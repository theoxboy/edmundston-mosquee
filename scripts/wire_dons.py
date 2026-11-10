"""Faire un don (étape D).

- Panneau SA-Dons : onglet « Page Dons » (campagne, Virement Interac, Desjardins, autres formes de don,
  questions fréquentes, reçus fiscaux) et onglet « Bloc Merci » (bandeau en bas de la page Dons).
  Les champs sont construits par le moteur commun des pages de services (copié depuis
  wire_service_pages.py) ; Enregistrer écrit les clés dons et merci, l'objectif et le montant récolté
  dans home.campagne (communs à l'accueil et à la campagne en direct), et la publication dans pages.
- Page Dons publique (PC, M-, T-) : tout ce qui est affiché vient de ces réglages ; la zakat al-Fitr
  reprend le montant de la carte Aïd des Services.

Ordre : après wire_service_pages.py, avant fix_inputs.py. Idempotent.
"""
import ast, json, pathlib, re, subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
OPEN = '<script type="__bundler/template">'


def load(path):
    s = path.read_text(encoding='utf-8')
    i = s.index(OPEN) + len(OPEN)
    j = s.index('</script>', i)
    return s, i, j, json.loads(s[i:j])


def save(path, s, i, j, tpl):
    enc = json.dumps(tpl).replace('</', '<\\u002F')
    assert json.loads(enc) == tpl
    path.write_text(s[:i] + enc + s[j:], encoding='utf-8')


def rep(tpl, old, new, count=1):
    n = tpl.count(old)
    assert n == count, f'{n} occurrence(s) au lieu de {count} : {old[:90]!r}'
    return tpl.replace(old, new)


def resub(tpl, pattern, repl, flags=re.S):
    out, n = re.subn(pattern, repl, tpl, count=1, flags=flags)
    assert n == 1, f'motif introuvable : {pattern[:90]!r}'
    return out


def sc_if(name, inner, default='true'):
    return f'<sc-if value="{{{{{name}}}}}" hint-placeholder-val="{{{{ {default} }}}}">{inner}</sc-if>'


# ---------- Moteur commun : copié depuis wire_service_pages.py (une seule écriture du moteur) ----------
def engine_source():
    tree = ast.parse((ROOT / 'scripts' / 'wire_service_pages.py').read_text(encoding='utf-8'))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, 'id', '') == 'ENGINE' for t in node.targets):
            src = node.value.value
            break
    else:
        raise AssertionError('moteur introuvable dans wire_service_pages.py')
    src = rep(src, '<script id="sa-services-x">', '<script id="sa-dons-x">')
    # Numérotation continue des cartes quand un onglet a plusieurs blocs.
    src = rep(src, "aria-hidden=\"true\">' + (n + 1) + '</span>'", "aria-hidden=\"true\">' + (n + 1 + (tab.n0 || 0)) + '</span>'")
    assert '__saServices' in src
    return src.replace('__saServices', '__saDons')


def T(p, l, **k): return dict(t='text', p=p, l=l, **k)
def A(p, l, **k): return dict(t='area', p=p, l=l, wide=True, **k)
def SW(p, l, **k): return dict(t='sw', p=p, l=l, **k)
def SEL(p, l, o, **k): return dict(t='select', p=p, l=l, o=o, **k)
def NUM(p, l, **k): return dict(t='num', p=p, l=l, **k)
def NOTE(h): return dict(t='note', h=h)


TABS = [
    dict(key='home', sections=[
        dict(title='Campagne', desc='Mêmes valeurs que l’accueil et la campagne en direct. Si la campagne est en mise à jour '
             'automatique (À propos → Campagne en direct), le montant récolté vient des dons enregistrés.', f=[
            NUM('campagne.objectif', 'Objectif', suf='$'),
            NUM('campagne.recolte', 'Montant récolté', suf='$', hint='0 = « mis à jour par l’association ».'),
        ]),
    ]),
    dict(key='dons', n0=1, sections=[
        dict(title='Affichage de la campagne', f=[
            SW('barre', 'Barre de progression'),
            SW('suivi', 'Lien « Suivre la campagne en direct »'),
        ]),
        dict(title='Virement Interac', sw='interac.on', desc='Voie principale. Sans adresse, le bloc n’est pas affiché.', f=[
            T('interac.courriel', 'Adresse de virement', max=120, type='email', wide=True),
            NUM('interac.m1', 'Montant 1', suf='$'), NUM('interac.m2', 'Montant 2', suf='$'), NUM('interac.m3', 'Montant 3', suf='$'),
            SEL('interac.defaut', 'Sélectionné par défaut', [['m1', 'Montant 1'], ['m2', 'Montant 2'], ['m3', 'Montant 3'], ['aucun', 'Aucun']]),
            NOTE('Un montant à 0 n’est pas proposé.'),
            SW('interac.autre', 'Bouton « Autre montant »'),
            SW('interac.etapes', 'Les 3 étapes « Ouvrez votre application bancaire… »'),
        ]),
        dict(title='Transfert Desjardins', sw='desjardins.on',
             desc='À remplir depuis l’affiche officielle validée. La carte reste masquée tant que les trois numéros ne sont pas remplis.', f=[
            T('desjardins.institution', 'Institution', max=10, ph='815'),
            T('desjardins.transit', 'Transit', max=10, ph='5 chiffres'),
            T('desjardins.compte', 'Compte', max=20, ph='7 chiffres'),
        ]),
        dict(title='Autres formes de don', sw='autres.on', f=[
            dict(t='list', p='autres.items', add='+ Ajouter une forme de don', title='titre', empty='Nouvelle forme de don', max=8,
                 none='Aucune forme de don : la section n’est pas affichée.', item=[
                     T('titre', 'Nom', max=60), T('arabe', 'Nom en arabe (facultatif)', max=40),
                     A('texte', 'Texte', max=400),
                     SEL('lien', 'Bouton', [['', 'Aucun bouton'], ['contact', 'Page Contact'], ['courriel', 'Écrire par courriel (adresse Interac)']]),
                     T('lienTexte', 'Texte du bouton', max=60, ph='Écrire à l’association'),
                     SW('fitr', 'Afficher le montant de la zakat al-Fitr',
                        hint='Montant et année : réglés dans <a href="SA-Services.dc.html" style="color:#0E4D3C;font-weight:700">Services</a> → carte des prières de l’Aïd.'),
                 ], d={'titre': '', 'arabe': '', 'texte': '', 'fitr': False, 'lien': '', 'lienTexte': '', 'on': True}),
        ]),
        dict(title='Questions fréquentes', sw='faq.on', f=[
            dict(t='list', p='faq.items', add='+ Ajouter une question', title='titre', empty='Nouvelle question', max=12,
                 none='Aucune question : la section n’est pas affichée.', item=[
                     T('titre', 'Question', max=160, wide=True),
                     A('texte', 'Réponse', max=1200, hint='Réponse vide : la question est masquée.'),
                 ], d={'titre': '', 'texte': '', 'on': True}),
        ]),
        dict(title='Reçus fiscaux', f=[
            SW('recus.statut', 'Statut d’organisme de bienfaisance confirmé',
               hint='Tant que c’est non, le site dit qu’aucun reçu fiscal n’est promis.'),
            T('recus.numero', 'Numéro d’enregistrement ARC', max=30, ph='123456789 RR0001'),
        ]),
    ]),
    dict(key='merci', sections=[
        dict(title='Bandeau « Merci »', sw='on', f=[
            T('titre', 'Titre', max=80, wide=True),
            A('texte', 'Texte', max=300),
            SW('facebook', 'Bouton « Partager sur Facebook »'),
            SW('whatsapp', 'Bouton « Partager sur WhatsApp »'),
            SW('suivre', 'Bouton de suivi'),
            SEL('suivreLien', 'Le bouton de suivi mène à', [['campagne', 'Page : Campagne en direct'], ['evenements', 'Page : Événements'],
                                                            ['apropos', 'Page : À propos'], ['accueil', 'Page : Accueil']]),
            T('suivreTexte', 'Texte du bouton de suivi', max=40, ph='Suivre le projet'),
        ]),
    ]),
]

COMPONENT_SCRIPT = r"""class Component extends DCLogic {
  constructor(props) {
    super(props);
    this.base = { pub_dons: true };
    this.pubKeys = ['pub_dons'];
    this.state = { on: Object.assign({}, this.base), extDirty: false, toast: '' };
    window.__saDons = this;
  }
  componentDidMount() {
    window.dispatchEvent(new Event('sa-dons-ready'));
  }
  componentWillUnmount() {
    clearTimeout(this.tt);
    if (window.__saDons === this) window.__saDons = null;
  }
  setSwitches(sw, asBase) {
    if (asBase) this.base = Object.assign({}, this.base, sw);
    this.setState({ on: Object.assign({}, this.state.on, sw) });
  }
  setExtDirty(flag) {
    if (!!this.state.extDirty !== !!flag) this.setState({ extDirty: !!flag });
    else this.forceUpdate();
  }
  commitKeys(keys) {
    const b = Object.assign({}, this.base);
    keys.forEach((k) => { b[k] = this.state.on[k]; });
    this.base = b;
    this.setState({ extDirty: false });
  }
  revertBase() {
    this.setState({ on: Object.assign({}, this.base), extDirty: false });
  }
  flash(m) {
    this.setState({ toast: m });
    clearTimeout(this.tt);
    this.tt = setTimeout(() => this.setState({ toast: '' }), 3600);
  }
  renderVals() {
    const on = this.state.on;
    const dirty = Object.keys(on).some((k) => on[k] !== this.base[k]) || !!this.state.extDirty;
    const s = {}, off = {}, op = {}, pub = {};
    Object.keys(on).forEach((k) => {
      s[k] = { c: String(!!on[k]), t: () => this.setState({ on: Object.assign({}, this.state.on, { [k]: !this.state.on[k] }) }) };
      off[k] = on[k] ? '' : 'off';
      op[k] = on[k] ? 1 : 0.5;
    });
    this.pubKeys.forEach((k) => { pub[k] = on[k] ? { t: 'Publiée', bg: '#DCEFE6', fg: '#0E4D3C' } : { t: 'Masquée du site', bg: '#F3EAD8', fg: '#7A5A1E' }; });
    return {
      s, off, op, pub,
      clean: !dirty, dot: dirty ? '#C49A4A' : '#7FB89F', statusTxt: dirty ? 'Changements non enregistrés' : 'Tout est enregistré',
      save: () => { if (window.__saDonsSave) window.__saDonsSave(); },
      undo: () => { if (window.__saDonsUndo) window.__saDonsUndo(); },
      toast: this.state.toast
    };
  }
}"""

SYNC_SCRIPT = r'''<script id="sa-dons-sync">
(function () {
  var MAIL_RE = /^[^@\s<>"]+@[^@\s<>"]+\.[^@\s<>"]{2,}$/;
  var pagesBase = null, saving = false, started = false;
  function comp() { return window.__saDons; }
  function flash(m) { var c = comp(); if (c) c.flash(m); }
  function api(url, method, body) {
    var o = { credentials: 'same-origin', method: method || 'GET' };
    if (body) { o.headers = { 'Content-Type': 'application/json' }; o.body = JSON.stringify(body); }
    return fetch(url, o).then(function (r) { return r.json().catch(function () { return { ok: false }; }); });
  }
  function swOn() { var c = comp(); return (c && c.state && c.state.on) || {}; }
  function pagesNext() {
    if (!pagesBase) return null;
    var next = Object.assign({}, pagesBase);
    next.pg_dons = !!swOn().pub_dons;
    return JSON.stringify(next) !== JSON.stringify(pagesBase) ? next : null;
  }
  function checkDirty() {
    var c = comp();
    if (c) c.setExtDirty(!!(window.__svx && window.__svx.dirty()));
  }
  window.__svCheckDirty = checkDirty;

  function saveAll() {
    if (saving) return;
    var mail = document.getElementById('x-dons-interac-courriel');
    if (mail && String(mail.value).trim() && !MAIL_RE.test(String(mail.value).trim())) {
      flash('Adresse de virement illisible. Écrivez une adresse complète, par exemple nom@exemple.com.');
      mail.focus();
      return;
    }
    var tasks = [];
    if (window.__svx) {
      var xs = window.__svx.save();
      if (xs === false) return;
      tasks = tasks.concat(xs);
    }
    var next = pagesNext();
    if (next) tasks.push(api('/api/admin/settings/pages', 'PUT', next).then(function (r) { if (r && r.ok && r.settings) pagesBase = r.settings; return r; }));
    if (!tasks.length) { flash('Aucun changement à enregistrer.'); return; }
    saving = true;
    flash('Enregistrement…');
    Promise.all(tasks).then(function (res) {
      saving = false;
      var failed = res.filter(function (r) { return !r || !r.ok; })[0];
      if (window.__svx) window.__svx.after();
      if (failed) { flash((failed && failed.message) || 'L’enregistrement a échoué. Vérifiez vos valeurs et réessayez.'); return; }
      var c = comp();
      if (c) c.commitKeys(['pub_dons']);
      setTimeout(checkDirty, 0);
      flash('Faire un don enregistré. Le site est à jour.');
    }).catch(function () {
      saving = false;
      flash('Impossible de joindre le serveur. Vérifiez votre connexion et réessayez.');
    });
  }
  function undoAll() {
    var c = comp();
    if (c) c.revertBase();
    if (window.__svx) window.__svx.undo();
    setTimeout(checkDirty, 0);
    flash('Changements annulés.');
  }
  window.__saDonsSave = saveAll;
  window.__saDonsUndo = undoAll;

  function start() {
    if (started) return;
    started = true;
    api('/api/admin/settings/pages').then(function (r) {
      if (!(r && r.ok && r.settings)) return;
      pagesBase = r.settings;
      var c = comp();
      if (c) c.setSwitches({ pub_dons: pagesBase.pg_dons !== false }, true);
    }, function () {});
  }
  if (comp()) start();
  else window.addEventListener('sa-dons-ready', start, { once: true });
})();
</script>
'''

BOX = '<div id="svx-{k}" style="display:flex;flex-direction:column;gap:18px"><p class="hint" style="margin:0">Chargement des réglages…</p></div>'


def wire_panel():
    path = ROOT / 'SA-Dons.dc.html'
    s, i, j, tpl = load(path)
    if 'id="svx-dons"' not in tpl:
        # Onglet Page Dons : en-tête conservé, sections remplacées par les blocs du moteur.
        a = tpl.index('<div id="sp-0" class="sp">')
        b = tpl.index('<div id="sp-1" class="sp">', a)
        body = tpl[a:b]
        h = body.index('<section')
        tail = body[body.rindex('</section>') + len('</section>'):]
        tpl = tpl[:a] + body[:h] + BOX.format(k='home') + BOX.format(k='dons') + tail + tpl[b:]
        # Onglet Merci : devient « Bloc Merci », sans interrupteur de publication (c'est un bandeau de la page Dons).
        a = tpl.index('<div id="sp-1" class="sp">')
        b = tpl.index('</main>', a)
        body = tpl[a:b]
        h = body.index('<section')
        head, tail = body[:h], body[body.rindex('</section>') + len('</section>'):]
        head = rep(head, '>Page Merci</h2>', '>Bloc Merci</h2>')
        head = resub(head, r'(<p class="eyebrow"[^>]*>)Page</p>', r'\1Bandeau</p>')
        head = resub(head, r'(<p class="dsc"[^>]*>)Affichée après l’envoi du formulaire de contact\.</p>',
                     r'\1Le bandeau « Merci pour votre générosité » en bas de la page Dons.</p>')
        head = resub(head, r'<div[^>]*><span class="tag"[^>]*>\{\{pub\.pub_merci\.t\}\}</span>.*?</button></div>', '')
        head = resub(head, r'<span class="btn btn-line" aria-disabled="true" title="[^"]*" style="[^"]*">(<svg.*?</svg>)Voir la page</span>',
                     r'<a class="btn btn-line" href="Dons.dc.html#mp-t" style="min-height:40px">\1Voir le bandeau</a>')
        tpl = tpl[:a] + head + BOX.format(k='merci') + tail + tpl[b:]
        tpl = tpl.replace('>Page Merci<', '>Bloc Merci<')
    assert 'pub_merci' not in tpl.split('class Component')[0], 'interrupteur Merci restant'
    assert 'Inscriptions Ramadan 2027' not in tpl.split('class Component')[0], 'fausse page restante'

    tpl, n = re.subn(r'class Component extends DCLogic \{.*?\n\}', lambda _: COMPONENT_SCRIPT, tpl, count=1, flags=re.S)
    assert n == 1, 'Component introuvable dans SA-Dons.dc.html'
    tpl = re.sub(r'<script id="sa-dons-(?:x|sync)">.*?</script>\s*', '', tpl, flags=re.S)
    engine = engine_source().replace('__TABS__', json.dumps(TABS, ensure_ascii=False))
    k = tpl.rindex('</body>')
    tpl = tpl[:k] + engine + SYNC_SCRIPT + tpl[k:]
    save(path, s, i, j, tpl)
    print('SA-Dons.dc.html : Page Dons et Bloc Merci reliés (clés dons, merci, home.campagne, pages)')


# =====================================================================================
# Page Dons publique
# =====================================================================================

DONS_JS = r"""
    /*ascil-dons*/
    const PT = (typeof window !== 'undefined' && window.__ascilPrayer) || {};
    const D = PT.dons || __DONS__, M = PT.merci || __MERCI__, C = PT.campagne || null;
    const pre = (typeof location !== 'undefined' && /\/(M-|T-)[^\/]*$/.exec(location.pathname)) ? /\/(M-|T-)[^\/]*$/.exec(location.pathname)[1] : '';
    const nf = (n) => Math.round(n).toLocaleString('fr-CA') + ' $';
    // Campagne : objectif et montant récolté de l'accueil (calculé depuis les dons en mode automatique).
    const objectif = C && Number(C.objectif) > 0 ? Math.round(Number(C.objectif)) : __OBJECTIF__;
    const raised = C ? Math.max(0, Math.round(Number(C.recolte) || 0)) : 0;
    const pct = objectif > 0 ? Math.min(100, Math.round(raised / objectif * 100)) : 0;
    // Virement Interac.
    const I = D.interac || {};
    const mail = String(I.courriel || '').trim();
    const at = mail.indexOf('@');
    const amtList = ['m1', 'm2', 'm3'].map((k) => Number(I[k]) || 0).filter((v) => v > 0);
    const defV = I.defaut && I.defaut !== 'aucun' ? Number(I[I.defaut]) || null : null;
    const cur = this.state.amtPicked ? this.state.amt : defV;
    const amtOpts = amtList.map((v) => [v, v + ' $']).concat(I.autre ? [[0, 'Autre']] : []);
    const pick = (v) => () => this.setState({ amt: v, amtPicked: true });
    const showInterac = !!I.on && !!mail;
    // Desjardins : affiché seulement avec les trois numéros.
    const J = D.desjardins || {};
    const showDesj = !!J.on && !!J.institution && !!J.transit && !!J.compte;
    // Reçus fiscaux.
    const R = D.recus || {};
    const recuTxt = R.statut
      ? 'L’ASCIL est un organisme de bienfaisance enregistré' + (R.numero ? ' (numéro d’enregistrement : ' + R.numero + ')' : '') + '. Pour un reçu fiscal, écrivez à l’association.'
      : 'Aucun reçu fiscal n’est promis tant que le statut d’organisme de bienfaisance de l’ASCIL n’est pas confirmé.';
    // Autres formes de don ; la zakat al-Fitr reprend la carte Aïd des Services.
    const aid = ((PT.services && PT.services.items) || []).filter((x) => x && x.kind === 'aid')[0] || __AID__;
    const fitrOk = aid && aid.zakat !== null && aid.zakat !== undefined && aid.zakat !== '';
    const AU = D.autres || {};
    const autres = (AU.items || []).filter((x) => x.on && x.titre).map((x) => {
      const href = x.lien === 'contact' ? pre + 'Contact.dc.html' : x.lien === 'courriel' && mail ? 'mailto:' + mail : '';
      return { titre: x.titre, arabe: x.arabe || '', hasAr: !!x.arabe, texte: x.texte || '', hasTexte: !!x.texte,
        hasFitr: !!x.fitr && fitrOk, fitrAmt: fitrOk ? aid.zakat + ' $' : '', fitrYear: fitrOk && aid.zakatAnnee ? ' en ' + aid.zakatAnnee : '',
        href, hasLien: !!href && !!x.lienTexte, lienTexte: x.lienTexte || '' };
    });
    const afTitle = autres.map((x, k) => (k ? x.titre.charAt(0).toLowerCase() + x.titre.slice(1) : x.titre)).join(', ');
    // Questions fréquentes : une réponse vide masque la question.
    const fq = ((D.faq && D.faq.items) || []).filter((x) => x.on && x.titre && x.texte);
    const faqs = fq.map((q, k) => ({ q: q.titre, a: q.texte, open: this.state.faq === k, rot: this.state.faq === k ? 45 : 0, rows: this.state.faq === k ? '1fr' : '0fr',
      exp: this.state.faq === k ? 'true' : 'false', toggle: () => this.setState({ faq: this.state.faq === k ? -1 : k }) }));
    // Bandeau Merci : partage de cette page.
    const url = typeof location !== 'undefined' ? location.origin + location.pathname : '';
    const shareTxt = 'Soutenez le nouveau lieu de la mosquée de Edmundston : ';
    const SUIVRE = { campagne: 'N3-Campagne.dc.html', evenements: 'Evenements.dc.html', apropos: 'APropos.dc.html', accueil: pre ? 'Accueil.dc.html' : 'Main.dc.html' };
    return {
      objFmt: nf(objectif), objMax: String(objectif), leadObj: objectif > 0 ? nf(objectif) : 'les fonds nécessaires',
      hasRaised: raised > 0 && objectif > 0, noRaised: !!C && !(raised > 0 && objectif > 0), showBar: raised > 0 && objectif > 0 && D.barre !== false,
      pct, raisedFmt: nf(raised), raisedNum: String(raised), showSuivi: D.suivi !== false,
      showPay: showInterac || showDesj, payCls: showInterac && showDesj ? 'split' : '', showInterac, showDesj,
      iMailA: at > -1 ? mail.slice(0, at + 1) : mail, iMailB: at > -1 ? mail.slice(at + 1) : '',
      iCopy: () => { try { navigator.clipboard && navigator.clipboard.writeText(mail); } catch (e) {} this.setState({ cpk: 'imail' }); clearTimeout(this.ct); this.ct = setTimeout(() => this.setState({ cpk: '' }), 2000); },
      iCpd: this.state.cpk === 'imail', iNc: this.state.cpk !== 'imail',
      hasAmts: amtOpts.length > 0,
      amts: amtOpts.map((a) => ({ label: a[1], pressed: String(cur === a[0]), pick: pick(a[0]) })),
      amtText: cur ? cur + ' $' : 'le montant de votre choix', showEtapes: I.etapes !== false, recuTxt,
      dj: { institution: J.institution || '', transit: J.transit || '', compte: J.compte || '' },
      showAutres: !!AU.on && autres.length > 0, autres, afTitle,
      showFaq: !!(D.faq && D.faq.on) && faqs.length > 0, faqs,
      showMerci: M.on !== false, mTitre: M.titre || 'Merci pour votre générosité', mTexte: M.texte || '', hasMTexte: !!M.texte,
      showFb: !!M.facebook, fbHref: 'https://www.facebook.com/sharer/sharer.php?u=' + encodeURIComponent(url),
      showWa: !!M.whatsapp, waHref: 'https://wa.me/?text=' + encodeURIComponent(shareTxt + url),
      showSuivre: !!M.suivre && !!M.suivreTexte, suivreHref: pre + (SUIVRE[M.suivreLien] || SUIVRE.campagne), suivreTexte: M.suivreTexte || '',
      showMerciBtns: !!M.facebook || !!M.whatsapp || (!!M.suivre && !!M.suivreTexte),
    };"""


def set_xvals(tpl, body):
    la = tpl.index('<script type="text/x-dc"')
    lb = tpl.index('</script>', la)
    code = tpl[la:lb]
    new = '  xvals() {' + body + '\n  }\n'
    if '/*ascil-dons*/' in code:
        a = code.index('  xvals() {')
        b = code.index('\n  }\n', a) + len('\n  }\n')
        code = code[:a] + new + code[b:]
    else:
        assert '  xvals() {' not in code, 'xvals déjà présent sur la page Dons'
        a = code.index('  renderVals() {')
        code = code[:a] + new + '\n' + code[a:]
    return tpl[:la] + code + tpl[lb:]


def patch_dons(tpl):
    a = tpl.index('<main'); b = tpl.index('</main>')
    m = tpl[a:b]
    # ---------- Campagne ----------
    m = rep(m, 'Le Centre rassemble des dons pour', 'L’ASCIL rassemble {{leadObj}} pour')
    m = resub(m, r'(<a class="btn btn-light" href="(?:[MT]-)?N3-Campagne\.dc\.html"[^>]*>.*?Suivre la campagne en direct</a>)',
              lambda x: sc_if('showSuivi', x.group(1)))
    m = rep(m, 'line-height:1.1">0 $</p>', 'line-height:1.1">{{objFmt}}</p>')
    m = resub(m, r'(<div style="[^"]*" role="progressbar" aria-valuemin="0" aria-valuemax=")0(" aria-label="Montant récolté">\s*<div class="bar".*?</div>\s*</div>)',
              lambda x: sc_if('showBar', x.group(1) + '{{objMax}}" aria-valuenow="{{raisedNum}}' + x.group(2)))
    # ---------- Interac et Desjardins ----------
    sa = m.index('<section class="sec" aria-labelledby="int-t">')
    sb = m.index('</section>', sa) + len('</section>')
    sec = m[sa:sb]
    sec = rep(sec, '<div class="split" style="align-items:stretch">', '<div class="{{payCls}}" style="align-items:stretch">')
    ia = sec.index('<div style="background:#fff;border:2px solid #D9B46C')
    da = sec.index('<div class="card" style="display:flex;flex-direction:column">')
    de = sec.index('</dl>', da) + len('</dl>')
    de = sec.index('</div>', de) + len('</div>')
    inter, desj = sec[ia:da], sec[da:de]
    inter = rep(inter, '>associationrdl.ascil@<wbr>gmail.com</p>', '>{{iMailA}}<wbr>{{iMailB}}</p>')
    inter = rep(inter, '{{cp.mail}}', '{{iCopy}}')
    inter = rep(inter, '{{nc.mail}}', '{{iNc}}')
    inter = rep(inter, '{{cpd.mail}}', '{{iCpd}}')
    ma = inter.index('<p style="margin:22px 0 8px;font-weight:700">Montant (facultatif)</p>')
    me = inter.index('</sc-for>', ma)
    me = inter.index('</div>', me) + len('</div>')
    inter = inter[:ma] + sc_if('hasAmts', inter[ma:me]) + inter[me:]
    oa = inter.index('<ol style="list-style:none;margin:22px 0 0')
    oe = inter.index('</ol>', oa) + len('</ol>')
    inter = (inter[:oa] + sc_if('showEtapes', inter[oa:oe]) +
             '\n    <p class="muted" style="margin:18px 0 0;font-size:15px">{{recuTxt}}</p>' + inter[oe:])
    k = inter.rindex('</div>')
    inter = sc_if('showInterac', inter[:k + len('</div>')]) + inter[k + len('</div>'):]
    for key, lbl in (('institution', 'Institution'), ('transit', 'Transit'), ('compte', 'Compte')):
        desj = rep(desj, f'<dt style="font-weight:700">{lbl}</dt><dd style="margin:0"><span class="ph">À remplir depuis l’affiche validée</span></dd>',
                   f'<dt style="font-weight:700">{lbl}</dt><dd class="tnum" style="margin:0;font-weight:600;overflow-wrap:anywhere">{{{{dj.{key}}}}}</dd>')
    desj = sc_if('showDesj', desj)
    sec = sec[:ia] + inter + sec[da:da] + desj + sec[de:]
    m = m[:sa] + sc_if('showPay', sec) + m[sb:]
    # ---------- Autres formes de don ----------
    sa = m.index('<section class="sand" aria-labelledby="af-t"')
    sb = m.index('</section>', sa) + len('</section>')
    sec = m[sa:sb]
    sec = rep(sec, '>Sadaqa, zakat al-mal, zakat al-fitr</h2>', '>{{afTitle}}</h2>')
    ga = sec.index('<div class="g3" style="margin-top:28px">') + len('<div class="g3" style="margin-top:28px">')
    ge = sec.rindex('</div>\n </div>\n</section>')
    cards = sec[ga:ge]
    arrow = re.search(r'Écrire à l’association (<svg.*?</svg>)</a>', cards, re.S).group(1)
    card = ('\n   <sc-for list="{{autres}}" as="z" hint-placeholder-count="3"><div class="card">'
            '<p class="h3">{{z.titre}}' + sc_if('z.hasAr', ' <span class="ar" lang="ar" dir="rtl" style="font-weight:400;font-size:18px;color:#515B66">{{z.arabe}}</span>', 'true') + '</p>'
            + sc_if('z.hasFitr', '<p style="margin:8px 0 0"><strong class="tnum" style="font-size:22px;color:#0B0F1A">{{z.fitrAmt}}</strong> par personne{{z.fitrYear}}</p>', 'false')
            + sc_if('z.hasTexte', '<p class="muted" style="margin:8px 0 0">{{z.texte}}</p>', 'true')
            + sc_if('z.hasLien', '<a class="link" href="{{z.href}}" style="margin-top:12px">{{z.lienTexte}} ' + arrow + '</a>', 'false')
            + '</div></sc-for>\n  ')
    sec = sec[:ga] + card + sec[ge:]
    m = m[:sa] + sc_if('showAutres', sec) + m[sb:]
    # ---------- Questions fréquentes ----------
    sa = m.index('<section class="sec" aria-labelledby="faq-t">')
    sb = m.index('</section>', sa) + len('</section>')
    m = m[:sa] + sc_if('showFaq', m[sa:sb]) + m[sb:]
    # ---------- Bandeau Merci ----------
    sa = m.index('<section class="sand2" aria-labelledby="mp-t">')
    sb = m.index('</section>', sa) + len('</section>')
    sec = m[sa:sb]
    sec = rep(sec, '>Merci pour votre générosité</h2>', '>{{mTitre}}</h2>')
    sec = resub(sec, r'(<p style="[^"]*">)Partagez la campagne autour de vous et suivez l’avancement du projet\.</p>',
                lambda x: sc_if('hasMTexte', x.group(1) + '{{mTexte}}</p>'))
    sec = resub(sec, r'<a class="btn btn-ghost" href="#">(<svg.*?</svg>)Partager sur Facebook</a>',
                lambda x: sc_if('showFb', '<a class="btn btn-ghost" href="{{fbHref}}" target="_blank" rel="noopener">' + x.group(1) + 'Partager sur Facebook</a>'))
    sec = resub(sec, r'<a class="btn btn-ghost" href="#">(<svg.*?</svg>)Partager sur WhatsApp</a>',
                lambda x: sc_if('showWa', '<a class="btn btn-ghost" href="{{waHref}}" target="_blank" rel="noopener">' + x.group(1) + 'Partager sur WhatsApp</a>'))
    sec = resub(sec, r'<a class="btn btn-ghost" href="(?:[MT]-)?Evenements\.dc\.html">(<svg.*?</svg>)Suivre le projet</a>',
                lambda x: sc_if('showSuivre', '<a class="btn btn-ghost" href="{{suivreHref}}">' + x.group(1) + '{{suivreTexte}}</a>'))
    ba = sec.index('<div class="stack-m"')
    be = sec.index('</div>', sec.rindex('</sc-if>')) + len('</div>')
    sec = sec[:ba] + sc_if('showMerciBtns', sec[ba:be]) + sec[be:]
    m = m[:sa] + sc_if('showMerci', sec) + m[sb:]
    assert 'À remplir depuis' not in m and '50 000' not in m and 'href="#"' not in m.split('class="totop"')[0]
    return tpl[:a] + m + tpl[b:]


def defaults():
    js = ("import('./functions/_lib/settings.js').then((m) => { const d = m.DEFAULT_SETTINGS; "
          "process.stdout.write(JSON.stringify({ dons: d.dons, merci: d.merci, objectif: d.home.campagne.objectif, "
          "aid: d.services.items.filter((x) => x.kind === 'aid')[0] || null })); })")
    out = subprocess.run(['node', '--input-type=module', '-e', js], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def wire_public():
    d = defaults()
    body = (DONS_JS.replace('__DONS__', json.dumps(d['dons'], ensure_ascii=False))
            .replace('__MERCI__', json.dumps(d['merci'], ensure_ascii=False))
            .replace('__OBJECTIF__', json.dumps(d['objectif']))
            .replace('__AID__', json.dumps(d['aid'], ensure_ascii=False)))
    for pre in ('', 'M-', 'T-'):
        path = ROOT / f'{pre}Dons.dc.html'
        s, i, j, tpl = load(path)
        if '{{leadObj}}' not in tpl:
            tpl = patch_dons(tpl)
        tpl = set_xvals(tpl, body)
        save(path, s, i, j, tpl)
        print(f'{pre}Dons.dc.html : campagne, Interac, Desjardins, autres formes de don, FAQ, reçus et bandeau Merci reliés')


if __name__ == '__main__':
    wire_panel()
    wire_public()
