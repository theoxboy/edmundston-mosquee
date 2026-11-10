
class Component extends DCLogic {
  // Logique du panneau Accueil (SA-Panneau). Remplace la logique d’origine (scripts/wire_homepage.py).
  // L'état « cur » est la seule source de vérité pour les interrupteurs, l'ordre des sections,
  // les cartes, les annonces et les heures de prière. Le script #sa-panneau-sync y accède par
  // window.__saHome (load, part, commit, revert) et gère les autres champs du formulaire.
  static defaults() {
    return {
      on: { chargement: true, bandeau: true, compte: true, mail: true, fb: true, don: true, langue: true,
        horaires: true, apropos: true, services: true, evenements: true, ressources: true, contact: true,
        hero: true, priere: true, hegirien: true, progression: true, puces: true, acces: true, campagne: true, barre: true,
        annonces: true, bienvenue: true, invitation: true, haut: true,
        pHor: true, pIti: true, pFb: true, pTcom: true, pCciq: true, pMail: true },
      ordre: ['acces', 'campagne', 'annonces', 'bienvenue', 'invitation'],
      cartes: [{ id: 'vendredi', on: true, lien: 'Page : Horaires du mois' }, { id: 'trouver', on: true, lien: 'Page : Contact' },
        { id: 'campagne', on: true, lien: 'Page : Faire un don' }],
      annonces: [],
      max: 3,
      priere: { fajr: '', lever: '', dohr: '', jumua: '', asr: '', maghreb: '', icha: '' }
    };
  }
  constructor(props) {
    super(props);
    this.base = Component.defaults();
    this.state = { cur: JSON.parse(JSON.stringify(this.base)), ext: false, loaded: false, saving: false,
      pages: [], more: false, device: 'PC', toast: '' };
    window.__saHome = this;
  }
  componentDidMount() {
    fetch('/api/admin/pages', { credentials: 'same-origin' })
      .then((r) => r.json().catch(() => ({ ok: false })))
      .then((d) => { if (d.ok) this.setState({ pages: d.pages.filter((p) => p.visibility !== 'draft') }); })
      .catch(() => {});
    window.dispatchEvent(new Event('sa-home-ready'));
  }
  componentWillUnmount() { clearTimeout(this.tt); if (window.__saHome === this) window.__saHome = null; }
  upd(fn) { const c = JSON.parse(JSON.stringify(this.state.cur)); fn(c); this.setState({ cur: c }); }
  flash(msg) { this.setState({ toast: msg }); clearTimeout(this.tt); this.tt = setTimeout(() => this.setState({ toast: '' }), 3200); }

  // ---------- passerelle avec #sa-panneau-sync
  fromSettings(s) {
    const d = Component.defaults();
    const c = d;
    if (s && s.on) Object.keys(d.on).forEach((k) => { if (typeof s.on[k] === 'boolean') c.on[k] = s.on[k]; });
    if (s && Array.isArray(s.ordre)) {
      const o = s.ordre.filter((x) => d.ordre.indexOf(x) > -1);
      d.ordre.forEach((x) => { if (o.indexOf(x) === -1) o.push(x); });
      c.ordre = o;
    }
    if (s && s.acces && Array.isArray(s.acces.cartes)) {
      const ids = ['vendredi', 'trouver', 'campagne'];
      const got = s.acces.cartes.filter((k) => k && ids.indexOf(k.id) > -1);
      ids.forEach((id) => { if (!got.some((k) => k.id === id)) got.push(d.cartes.find((k) => k.id === id)); });
      c.cartes = got.map((k) => ({ id: k.id, on: k.on !== false, lien: k.lien || d.cartes.find((x) => x.id === k.id).lien }));
    }
    if (s && s.annonces) {
      if ([1, 2, 3].indexOf(s.annonces.max) > -1) c.max = s.annonces.max;
      if (Array.isArray(s.annonces.items)) {
        c.annonces = s.annonces.items.map((a) => ({ date: a.date || '', titre: a.titre || '', resume: a.resume || '',
          lien: a.lien || 'Page : Événements', on: a.on !== false }));
      }
    }
    if (s && s.priere) Object.keys(d.priere).forEach((k) => { if (typeof s.priere[k] === 'string') c.priere[k] = s.priere[k]; });
    return c;
  }
  load(s) { const c = this.fromSettings(s); this.base = JSON.parse(JSON.stringify(c)); this.setState({ cur: c, ext: false, loaded: true }); }
  apply(s) { this.setState({ cur: this.fromSettings(s), ext: true }); }
  part() {
    const c = this.state.cur;
    return { on: c.on, ordre: c.ordre, cartes: c.cartes, max: c.max, priere: c.priere,
      items: c.annonces.map((a, i) => ({ id: i, date: a.date.trim(), titre: a.titre.trim(), resume: a.resume.trim(), lien: a.lien, on: a.on })) };
  }
  commit() { this.base = JSON.parse(JSON.stringify(this.state.cur)); this.setState({ ext: false, saving: false }); }
  revert() { this.setState({ cur: JSON.parse(JSON.stringify(this.base)), ext: false }); }
  markExt() { if (!this.state.ext) this.setState({ ext: true }); }

  // ---------- liens : pages du site, pages créées, lien externe
  linkOpts(current) {
    const SITE = ['Page : Horaires du mois', 'Page : Rappel de prière', 'Page : Langue de la khutba', 'Page : Faire un don',
      'Page : Campagne en direct', 'Page : Événements', 'Page : Calendrier du mois', 'Page : Contact', 'Page : Ressources',
      'Page : À propos', 'Page : Services'];
    const opts = SITE.map((t) => ({ v: t, t }));
    this.state.pages.forEach((p) => opts.push({ v: p.url, t: 'Ma page : ' + p.title }));
    if (current && !opts.some((o) => o.v === current)) {
      opts.push({ v: current, t: current.indexOf('/p/') === 0 ? 'Ma page : ' + current + ' (non publiée ou supprimée)'
        : /^https?:\/\//i.test(current) ? 'Lien externe : ' + current : current });
    }
    opts.push({ v: '__ext', t: 'Lien externe…' });
    return opts;
  }
  pickLink(e, write) {
    const v = e && e.target ? e.target.value : '';
    if (v !== '__ext') { this.upd((x) => write(x, v)); return; }
    const url = (window.prompt('Adresse du lien externe (doit commencer par https://)', 'https://') || '').trim();
    if (/^https?:\/\/[^\s<>"]{3,}$/i.test(url)) this.upd((x) => write(x, url));
    else { this.forceUpdate(); if (url && url !== 'https://') this.flash('Adresse non valide : elle doit commencer par https://. Le lien précédent est conservé.'); }
  }

  renderVals() {
    const c = this.state.cur, on = c.on;
    const dirty = this.state.ext || JSON.stringify(c) !== JSON.stringify(this.base);
    const tog = (k) => () => this.upd((x) => { x.on[k] = !x.on[k]; });
    const s = {};
    Object.keys(on).forEach((k) => { s[k] = { c: String(!!on[k]), t: tog(k) }; });
    const rows = (list) => list.map((r) => ({ l: r[1], h: r[2] || '', c: String(!!on[r[0]]), t: tog(r[0]) }));
    const SEC = { acces: 'Accès rapides', campagne: 'Campagne nouveau lieu', annonces: 'Dernières annonces', bienvenue: 'Bienvenue aux visiteurs', invitation: 'Invitation' };
    const move = (key, i, d) => () => this.upd((x) => { const a = x[key]; const j = i + d; const t = a[i]; a[i] = a[j]; a[j] = t; });
    const ordreItems = c.ordre.map((id, i) => ({ pos: i + 1, name: SEC[id], off: !on[id], col: on[id] ? '#1E2B26' : '#4F5E57',
      first: i === 0, last: i === c.ordre.length - 1, up: move('ordre', i, -1), down: move('ordre', i, 1) }));
    const CART = { vendredi: ['Prière du vendredi', 'Heure de Jumu’a reprise de « Prochaine prière ».'],
      trouver: ['Nous trouver', 'Adresse reprise des coordonnées générales.'],
      campagne: ['Nouveau lieu — campagne en cours', 'Mène à la page des dons.'] };
    const cartes = c.cartes.map((k, i) => ({ pos: i + 1, n: CART[k.id][0], h: CART[k.id][1], c: String(k.on), op: k.on ? 1 : 0.5,
      col: k.on ? '#0E4D3C' : '#4F5E57', first: i === 0, last: i === c.cartes.length - 1, up: move('cartes', i, -1), down: move('cartes', i, 1),
      t: () => this.upd((x) => { x.cartes[i].on = !x.cartes[i].on; }),
      lien: k.lien, opts: this.linkOpts(k.lien), setLien: (e) => this.pickLink(e, (x, v) => { x.cartes[i].lien = v; }) }));
    let shown = 0;
    const na = c.annonces.length;
    const annonces = c.annonces.map((a, i) => {
      const vis = a.on && shown < c.max; if (a.on) shown++;
      const etat = vis ? 'Affichée' : (a.on ? 'Au-delà du nombre affiché' : 'Masquée');
      const lbl = a.titre.trim() || ('Annonce ' + (i + 1));
      const field = (k) => (e) => { const v = e && e.target ? e.target.value : ''; this.upd((x) => { x.annonces[i][k] = v; }); };
      return { pos: i + 1, lbl, date: a.date, titre: a.titre, resume: a.resume, etat,
        tagBg: vis ? '#F6E7C4' : '#F3EAD8', tagFg: vis ? '#0E4D3C' : '#4F5E57',
        c: String(a.on), op: a.on ? 1 : 0.5, first: i === 0, last: i === na - 1,
        up: move('annonces', i, -1), down: move('annonces', i, 1),
        t: () => this.upd((x) => { x.annonces[i].on = !x.annonces[i].on; }),
        setDate: field('date'), setTitre: field('titre'), setResume: field('resume'),
        lien: a.lien, opts: this.linkOpts(a.lien), setLien: (e) => this.pickLink(e, (x, v) => { x.annonces[i].lien = v; }),
        del: () => { if (window.confirm('Supprimer l’annonce « ' + lbl + ' » ? Elle disparaîtra de l’accueil après « Enregistrer ».')) this.upd((x) => { x.annonces.splice(i, 1); }); } };
    });
    const HEURES = [['fajr', 'Fajr'], ['lever', 'Lever du soleil'], ['dohr', 'Dohr'], ['jumua', 'Jumu’a (vendredi)'], ['asr', 'Asr'], ['maghreb', 'Maghreb'], ['icha', 'Icha']];
    const heures = HEURES.map((h) => {
      const v = c.priere[h[0]] || '';
      return { n: h[1], v, note: v ? 'Affichée' : 'Vide → « — »', col: v ? '#0E4D3C' : '#7A5A1E',
        set: (e) => { const val = e && e.target ? e.target.value : ''; this.upd((x) => { x.priere[h[0]] = val; }); } };
    });
    const CARDS = [['w-general', 'Coordonnées générales', null], ['w-ordre', 'Ordre des sections', null], ['w-chargement', 'Écran de chargement', 'chargement'],
      ['w-bandeau', 'Bandeau du haut', 'bandeau'], ['w-entete', 'En-tête et menu', null], ['w-hero', 'Héros', 'hero'], ['w-priere', 'Prochaine prière', 'priere'],
      ['w-acces', 'Accès rapides', 'acces'], ['w-campagne', 'Campagne nouveau lieu', 'campagne'], ['w-annonces', 'Dernières annonces', 'annonces'],
      ['w-bienvenue', 'Bienvenue aux visiteurs', 'bienvenue'], ['w-invitation', 'Invitation', 'invitation'], ['w-haut', 'Bouton « Revenir en haut »', 'haut'], ['w-pied', 'Pied de page', null]];
    const offCls = {}; ['chargement', 'bandeau', 'hero', 'priere', 'acces', 'campagne', 'annonces', 'bienvenue', 'invitation'].forEach((k) => { offCls[k] = on[k] ? '' : 'off'; });
    const W = { PC: '300px', Tablette: '210px', Mobile: '120px' };
    const PVN = { acces: 'Accès rapides', campagne: 'Campagne', annonces: 'Annonces', bienvenue: 'Bienvenue', invitation: 'Invitation' };
    const pvBlocks = c.ordre.filter((id) => on[id]).map((id) => ({ n: PVN[id], bg: id === 'campagne' || id === 'bienvenue' ? '#F3EAD8' : '#fff', bd: '#E4D9C0' }));
    const call = (name) => () => { this.setState({ more: false }); if (typeof window[name] === 'function') window[name](); };
    const label = !this.state.loaded ? 'Chargement…' : this.state.saving ? 'Enregistrement…' : dirty ? 'Changements non enregistrés' : 'Tout est enregistré';
    return {
      s, on, offCls, ordreItems, cartes, annonces, heures, pvBlocks,
      navItems: CARDS.map((x) => ({ id: x[0], t: x[1], off: !!x[2] && !on[x[2]] })),
      rowsBandeau: rows([['compte', 'Compte à rebours', '« · dans 3 h 50 » après l’heure (PC et tablette).'], ['mail', 'Courriel', 'Sur PC seulement.'], ['fb', 'Lien Facebook', 'Sur PC seulement.']]),
      rowsEntete: rows([['don', 'Bouton « Faire un don »', 'En-tête et menu mobile.'], ['langue', 'Sélecteur de langue', 'FR · العربية · EN']]),
      rowsMenu: rows([['horaires', 'Horaires', 'Rappel de prière, khutba'], ['apropos', 'À propos', 'Campagne en direct'], ['services', 'Services', 'Cours, mariages, funérailles…'],
        ['evenements', 'Événements', 'Calendrier, inscription'], ['ressources', 'Ressources', 'Dua et annonces'], ['contact', 'Contact', '']]),
      rowsPriere: rows([['hegirien', 'Date hégirienne', 'À côté de la date du jour.'], ['progression', 'Barre de progression', 'Temps écoulé depuis la prière précédente.'], ['puces', 'Puces des prières', 'Les cinq boutons cliquables.']]),
      rowsPied: rows([['pHor', 'Horaires résumés', 'Repris de « Prochaine prière ».'], ['pIti', 'Bouton « Itinéraire »', 'Lien des coordonnées générales.'],
        ['pFb', 'Page Facebook', ''], ['pTcom', 'TCOM — annonces Ramadan et Aïd', ''], ['pCciq', 'CCIQ — annonces Ramadan et Aïd', ''], ['pMail', 'Courriel du pied de page', '']]),
      maxOpts: [1, 2, 3].map((n) => ({ n, p: String(c.max === n), pick: () => this.upd((x) => { x.max = n; }) })),
      addAnn: () => {
        if (c.annonces.length >= 10) { this.flash('L’accueil compte au plus 10 annonces. Supprimez-en une avant d’en ajouter.'); return; }
        this.upd((x) => { x.annonces.push({ date: '', titre: '', resume: '', lien: 'Page : Événements', on: true }); });
        this.flash('Annonce ajoutée en bas de la liste. Remplissez-la puis cliquez sur « Enregistrer ».');
      },
      annFull: c.annonces.length >= 10,
      devices: ['PC', 'Tablette', 'Mobile'].map((n) => ({ n, p: String(this.state.device === n), pick: () => this.setState({ device: n }) })),
      pvW: W[this.state.device], pvDesk: this.state.device === 'PC', pvDir: this.state.device === 'Mobile' ? 'column' : 'row',
      clean: !this.state.loaded || this.state.saving || !dirty, dot: dirty ? '#C49A4A' : '#7FB89F', statusTxt: label,
      save: () => { if (typeof window.saHomeSave === 'function') window.saHomeSave(); },
      undo: () => { if (typeof window.saHomeUndo === 'function') window.saHomeUndo(); },
      doExport: call('saHomeExport'), doImport: call('saHomeImport'), doReset: call('saHomeReset'),
      more: this.state.more, moreStr: String(this.state.more), toggleMore: () => this.setState({ more: !this.state.more }),
      toast: this.state.toast
    };
  }
}
