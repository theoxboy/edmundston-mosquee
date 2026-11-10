"""Événements (étape E).

- Panneau SA-Evenements :
  - onglet « Annonces » : liste des événements (clé evenements) construite par le moteur commun des
    pages de services (copié depuis wire_service_pages.py), événement à la une, filtres, événements
    passés, rendez-vous fixes, bloc « Aller plus loin », partage ;
  - onglet « Détail d'un événement » retiré : la fiche de chaque événement se règle dans la liste et se
    déplie sur la page Événements ;
  - onglet « Calendrier du mois » (clé calendrier) ;
  - onglet « Inscription aux événements » : l'événement ouvert est choisi dans la liste ; titre, date,
    lieu et description suivent la liste ; places, dates et options (event_registration) ; inscrits,
    export, courriel groupé et annulation (repris de l'ancien script de wire_events.py) ;
  - publication des pages Événements, Calendrier et Inscription (clé pages).
- Pages publiques Evenements (PC, M-, T-) et N3-Calendrier (PC, M-, T-) tirées de ces réglages.
- Panneau Accueil : la liste « Dernières annonces » est remplacée par un renvoi vers Événements
  (l'accueil reçoit les annonces calculées par GET /api/settings/home).

Ordre : après wire_dons.py, avant wire_inbox.py et fix_inputs.py. Idempotent.
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


def section_span(tpl, start_marker):
    a = tpl.index(start_marker)
    b = tpl.index('</section>', a) + len('</section>')
    return a, b


# ---------- Moteur commun : copié depuis wire_service_pages.py ----------
def engine_source():
    tree = ast.parse((ROOT / 'scripts' / 'wire_service_pages.py').read_text(encoding='utf-8'))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, 'id', '') == 'ENGINE' for t in node.targets):
            src = node.value.value
            break
    else:
        raise AssertionError('moteur introuvable dans wire_service_pages.py')
    src = rep(src, '<script id="sa-services-x">', '<script id="sa-ev-x">')
    src = rep(src, "aria-hidden=\"true\">' + (n + 1) + '</span>'", "aria-hidden=\"true\">' + (n + 1 + (tab.n0 || 0)) + '</span>'")
    # Étiquette de date dans l'en-tête de chaque événement.
    src = rep(src, "    niveau: function (x) {", "    date: function (x) { return x.date ? x.date.split('-').reverse().join('/') : 'En cours'; },\n    niveau: function (x) {")
    # Un nouvel événement reçoit tout de suite un identifiant (fiche, à la une, inscriptions).
    src = rep(src, "      list.push(clone(f.d));\n",
              "      list.push(clone(f.d));\n      if (f.gid) list[list.length - 1].id = 'ev-' + Date.now().toString(36);\n")
    # Choix de l'événement à la une : options construites depuis la liste.
    src = rep(src, "        return lab('<select class=\"in\" id=\"' + id + '\"' + at(k, p) + FULL + '>' + f.o.map(function (o) {",
              "        return lab('<select class=\"in\" id=\"' + id + '\"' + at(k, p) + FULL + '>' + (f.o === '__EV__' ? evOpts(k) : f.o).map(function (o) {")
    src = rep(src, "  function grid(fields, k, pre) {",
              "  function evOpts(k) {\n"
              "    return [['auto', 'Le prochain événement (automatique)']].concat((data[k].items || []).filter(function (x) { return x.id && x.titre; })\n"
              "      .map(function (x) { return [x.id, x.titre + (x.date ? ' (' + x.date.split('-').reverse().join('/') + ')' : '')]; }));\n"
              "  }\n  function grid(fields, k, pre) {")
    # Le titre d'un événement change aussi la liste « à la une » : on reconstruit à la sortie du champ.
    src = rep(src, "    document.addEventListener('change', onInput);\n",
              "    document.addEventListener('change', onInput);\n"
              "    document.addEventListener('focusout', function (e) {\n"
              "      var t = e.target;\n"
              "      if (t && t.getAttribute && /^items\\.\\d+\\.(titre|date)$/.test(t.getAttribute('data-xp') || '') && t.getAttribute('data-xk') === 'evenements') renderTab(tabOf('evenements'));\n"
              "    });\n")
    assert '__saServices' in src
    return src.replace('__saServices', '__saEv')


def T(p, l, **k): return dict(t='text', p=p, l=l, **k)
def A(p, l, **k): return dict(t='area', p=p, l=l, wide=True, **k)
def SW(p, l, **k): return dict(t='sw', p=p, l=l, **k)
def SEL(p, l, o, **k): return dict(t='select', p=p, l=l, o=o, **k)
def NUM(p, l, **k): return dict(t='num', p=p, l=l, **k)
def NOTE(h): return dict(t='note', h=h)


LIENS = [['', 'Aucun lien'], ['dons', 'Page : Faire un don'], ['campagne', 'Page : Campagne en direct'], ['horaires', 'Page : Horaires'],
         ['services', 'Page : Services'], ['cours', 'Page : Cours de Coran et d’arabe'], ['inscription', 'Page : S’inscrire'],
         ['calendrier', 'Page : Calendrier du mois'], ['contact', 'Page : Contact'], ['ressources', 'Page : Ressources']]

EV_ITEM = [
    T('titre', 'Titre', max=120, wide=True),
    dict(t='date', p='date', l='Date', hint='Vide : affiché « En cours », ne passe jamais.'),
    dict(t='time', p='debut', l='Début'), dict(t='time', p='fin', l='Fin'),
    SEL('lieu', 'Lieu (filtre)', [['mosquee', 'À la mosquée'], ['salle', 'Salle de l’Aïd'], ['campagne', 'Campagne'], ['autre', 'Autre']]),
    T('lieuTexte', 'Adresse affichée', max=120, ph='Mosquée — 34, 37e Avenue'),
    SEL('categorie', 'Catégorie (calendrier)', [['comm', 'Communauté'], ['priere', 'Prière et spiritualité'], ['cours', 'Cours'], ['collecte', 'Collectes']]),
    A('resume', 'Résumé', max=400),
    SEL('lien', 'Lien', LIENS), T('lienTexte', 'Texte du lien', max=40, ph='En savoir plus'),
    SEL('inscription', 'Inscription', [['non', 'Pas d’inscription'], ['formulaire', 'Formulaire de la page « S’inscrire »'], ['contact', 'Par message (page Contact)']]),
    NUM('places', 'Places', hint='0 = illimitées.'),
    T('partenaire', 'Partenaire', max=120), T('public', 'Public concerné', max=160),
    A('description', 'Description de la fiche (5 à 10 lignes)', max=2000),
    SW('itineraire', 'Lien « Itinéraire »'),
]
EV_NEW = {'id': '', 'titre': '', 'date': '', 'debut': '', 'fin': '', 'lieu': 'mosquee', 'lieuTexte': '', 'categorie': 'comm', 'resume': '',
          'lien': '', 'lienTexte': '', 'inscription': 'non', 'partenaire': '', 'description': '', 'public': '', 'places': 0,
          'itineraire': True, 'on': True}

TABS = [
    dict(key='evenements', sections=[
        dict(title='Événement à la une', sw='une.on', desc='Le grand bloc en haut de la page Événements.', f=[
            SEL('une.choix', 'Événement mis en avant', '__EV__', hint='Un nouvel événement apparaît ici une fois son titre écrit.'),
            SEL('une.bouton', 'Bouton', [['details', 'Voir les détails'], ['inscrire', 'S’inscrire (si l’événement a une inscription)'], ['aucun', 'Aucun bouton']]),
        ]),
        dict(title='Liste des événements', desc='Triés par date sur le site. Un événement passe dans « Événements passés » le lendemain de sa date. '
             'Les « Dernières annonces » de l’accueil et le calendrier du mois reprennent cette liste.', f=[
            dict(t='list', p='items', add='+ Ajouter un événement', title='titre', empty='Nouvel événement', max=40, tag='date', gid=True,
                 none='Aucun événement : la page indique qu’aucun événement n’est annoncé.', item=EV_ITEM, d=EV_NEW),
        ]),
        dict(title='Filtres et événements passés', f=[
            SW('filtres', 'Filtres « Tous · À la mosquée · Salle de l’Aïd »'),
            SW('passes.on', 'Section « Événements passés »'),
            NUM('passes.nombre', 'Événements passés affichés', hint='0 = tous.'),
            SW('partage', 'Bouton « Partager » dans les fiches'),
        ]),
        dict(title='Les rendez-vous fixes', sw='fixes.on', f=[
            dict(t='list', p='fixes.items', add='+ Ajouter un rendez-vous', title='titre', empty='Nouveau rendez-vous', max=8,
                 none='Aucun rendez-vous : la section n’est pas affichée.',
                 item=[T('titre', 'Titre', max=60, wide=True), A('texte', 'Texte', max=300)], d={'titre': '', 'texte': '', 'on': True}),
        ]),
        dict(title='Bloc « Aller plus loin »', sw='outils.on', desc='Cartes vers les petites apps. Une carte vers une page masquée n’apparaît pas.', f=[
            SW('outils.calendrier', 'Calendrier du mois'), SW('outils.inscription', 'S’inscrire à un événement'), SW('outils.dua', 'Dua et annonces'),
        ]),
    ]),
    dict(key='calendrier', sections=[
        dict(title='Catégories', desc='Pastilles de couleur et filtres. Une catégorie décochée disparaît du calendrier.', f=[
            SW('categories.cours', 'Cours'), SW('categories.priere', 'Prière et spiritualité'),
            SW('categories.comm', 'Communauté'), SW('categories.collecte', 'Collectes'),
        ]),
        dict(title='Contenu', f=[
            SW('evenements', 'Reprendre automatiquement les événements', hint='Depuis la liste de l’onglet Annonces (événements datés).'),
            SW('cours', 'Ajouter les cours de la semaine', hint='Depuis Services → Cours : chaque cours affiché revient chaque semaine.'),
            SW('agenda', 'Bouton « Ajouter à mon agenda »'),
            SEL('vue', 'Vue par défaut', [['mois', 'Mois'], ['liste', 'Liste']]),
        ]),
    ]),
]

PUB = {'pub_evenements': 'pg_evenements', 'pub_calendrier': 'pg_calendrier', 'pub_inscription': 'pg_inscription'}
INS_SW = {'in_ouvert': 'is_open', 'in_vege': 'opt_vege', 'in_code': 'opt_code', 'in_agenda': 'opt_agenda'}

COMPONENT_SCRIPT = r"""class Component extends DCLogic {
  constructor(props) {
    super(props);
    this.base = __BASE__;
    this.pubKeys = ['pub_evenements', 'pub_calendrier', 'pub_inscription'];
    this.state = { on: Object.assign({}, this.base), extDirty: false, toast: '' };
    window.__saEv = this;
  }
  componentDidMount() {
    window.dispatchEvent(new Event('sa-ev-ready'));
  }
  componentWillUnmount() {
    clearTimeout(this.tt);
    if (window.__saEv === this) window.__saEv = null;
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
      save: () => { if (window.__saEvSave) window.__saEvSave(); },
      undo: () => { if (window.__saEvUndo) window.__saEvUndo(); },
      toast: this.state.toast
    };
  }
}"""

SYNC_SCRIPT = r'''<script id="sa-ev-sync">
(function () {
  var PUB = __PUB__;
  var INS_SW = __INS_SW__;
  var JOURS = ['Dimanche', 'Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi'];
  var MOIS = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'];
  var LIEUX = { mosquee: 'Mosquée — 34, 37e Avenue', salle: 'Salle de l’Aïd', campagne: 'Campagne de l’ASCIL', autre: '' };
  var pagesBase = null, ins = null, insBase = '', events = [], regs = [], restricted = '', role = '', saving = false, started = false;

  function comp() { return window.__saEv; }
  function flash(m) { var c = comp(); if (c) c.flash(m); }
  function el(id) { return document.getElementById(id); }
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; });
  }
  function api(url, method, body) {
    var o = { credentials: 'same-origin', method: method || 'GET' };
    if (body) { o.headers = { 'Content-Type': 'application/json' }; o.body = JSON.stringify(body); }
    return fetch(url, o).then(function (r) { return r.json().catch(function () { return { ok: false }; }); });
  }
  function swOn() { var c = comp(); return (c && c.state && c.state.on) || {}; }
  function canIns() { return role === 'superadmin' || role === 'events'; }

  // ---------- Inscription : événement choisi dans la liste ----------
  function hm(t) { return t ? t.replace(':', ' h ').replace(/ h 00$/, ' h') : ''; }
  function dateStr(x) {
    if (!x.date) return 'Date à venir';
    var d = new Date(x.date + 'T12:00:00Z');
    var s = JOURS[d.getUTCDay()] + ' ' + d.getUTCDate() + ' ' + MOIS[d.getUTCMonth()] + ' ' + d.getUTCFullYear();
    return s + (x.debut ? ' · ' + hm(x.debut) + (x.fin ? ' à ' + hm(x.fin) : '') : '');
  }
  function fromEvent(x, base) {
    return Object.assign({}, base, {
      event_slug: x.id, event_title: x.titre, date_str: dateStr(x),
      location: x.lieuTexte || LIEUX[x.lieu] || base.location, description: (x.resume || x.description || '').slice(0, 500)
    });
  }
  function eligible() { return events.filter(function (x) { return x.on && x.titre && x.inscription === 'formulaire'; }); }
  function renderSelect() {
    var f = el('f19');
    if (!f || !ins) return;
    var list = eligible(), cur = ins.event_slug;
    var opts = list.map(function (x) { return [x.id, x.titre + (x.date ? ' (' + x.date.split('-').reverse().join('/') + ')' : '')]; });
    if (!list.some(function (x) { return x.id === cur; })) opts.unshift([cur, ins.event_title + ' (réglage actuel)']);
    f.innerHTML = opts.map(function (o) { return '<option value="' + esc(o[0]) + '"' + (o[0] === cur ? ' selected' : '') + '>' + esc(o[1]) + '</option>'; }).join('');
    f.value = cur;
    var hint = el('f19-hint');
    if (!hint) {
      hint = document.createElement('p');
      hint.id = 'f19-hint'; hint.className = 'hint'; hint.style.margin = '2px 0 0';
      f.parentNode.appendChild(hint);
    }
    hint.textContent = list.length
      ? 'Titre, date, lieu et description viennent de la liste des événements (onglet Annonces).'
      : 'Aucun événement de la liste n’a l’inscription « Formulaire de la page S’inscrire ». Choisissez-la dans l’onglet Annonces.';
  }
  function setNum(id, v) { var e = el(id); if (e) e.value = v == null ? '' : v; }
  function applyIns(s, asBase) {
    ins = JSON.parse(JSON.stringify(s));
    if (asBase) insBase = JSON.stringify(s);
    setNum('f20', s.total_seats); setNum('f21', s.max_per_reg); setNum('f22', s.deadline);
    var sw = {};
    Object.keys(INS_SW).forEach(function (k) { sw[k] = !!s[INS_SW[k]]; });
    var c = comp();
    if (c) c.setSwitches(sw, asBase);
    renderSelect();
  }
  function collectIns() {
    if (!ins) return null;
    var on = swOn(), out = JSON.parse(JSON.stringify(ins));
    var f = el('f19'), slug = f ? f.value : ins.event_slug;
    var x = events.filter(function (e) { return e.id === slug; })[0];
    if (x) out = fromEvent(x, out);
    var num = function (id, d) { var e = el(id), n = e ? parseInt(String(e.value).replace(/\s/g, ''), 10) : NaN; return isFinite(n) ? n : d; };
    out.total_seats = num('f20', ins.total_seats);
    out.max_per_reg = num('f21', ins.max_per_reg);
    var dl = el('f22');
    out.deadline = dl ? dl.value : ins.deadline;
    Object.keys(INS_SW).forEach(function (k) { out[INS_SW[k]] = !!on[k]; });
    return out;
  }
  function insDirty() { var v = collectIns(); return !!v && canIns() && JSON.stringify(v) !== insBase; }

  // ---------- Inscrits ----------
  function summary(sm) {
    var p = document.querySelector('#sp-3 section[aria-label="Inscrits"] p.info');
    if (!p) return;
    var total = ins ? ins.total_seats : 0;
    p.textContent = (sm.total_attendees || 0) + ' places réservées sur ' + total + ' · ' + (sm.total_registrations || 0) +
      ' inscription(s) confirmée(s) · ' + (sm.vegetarian_count || 0) + ' repas végétarien(s)';
  }
  function renderRegs() {
    var cardB = document.querySelector('#sp-3 section[aria-label="Inscrits"] .card-b');
    if (!cardB) return;
    var w = el('sa-reg-list-wrap');
    if (!w) { w = document.createElement('div'); w.id = 'sa-reg-list-wrap'; w.style.marginTop = '18px'; cardB.appendChild(w); }
    if (restricted) { w.innerHTML = '<p style="color:#4F5E57;margin-top:12px">' + esc(restricted) + '</p>'; return; }
    if (!regs.length) { w.innerHTML = '<p class="hint" style="margin-top:12px">Aucune inscription enregistrée pour le moment.</p>'; return; }
    var th = 'padding:10px 12px';
    var h = ['<div style="overflow-x:auto;border:1px solid #E4D9C0;border-radius:12px;margin-top:14px;background:#fff" tabindex="0" aria-label="Liste des inscrits">',
      '<table style="width:100%;border-collapse:collapse;font-size:13px;text-align:left"><thead><tr style="background:#F6EEDF;color:#0E4D3C;font-weight:700;border-bottom:1px solid #E4D9C0">',
      '<th style="' + th + '">Code</th><th style="' + th + '">Nom</th><th style="' + th + '">Contact</th><th style="' + th + ';text-align:center">Places</th>',
      '<th style="' + th + ';text-align:center">Végé</th><th style="' + th + '">Date</th><th style="' + th + ';text-align:center">Statut</th><th style="' + th + ';text-align:right">Action</th></tr></thead><tbody>'];
    regs.forEach(function (r) {
      var ok = r.status === 'confirmed', mail = r.contact && r.contact.indexOf('@') > -1;
      h.push('<tr style="border-bottom:1px solid #F1E9DB;' + (ok ? '' : 'opacity:.6') + '">',
        '<td style="' + th + ';font-family:monospace;font-weight:700;color:#0E4D3C">' + esc(r.code) + '</td>',
        '<td style="' + th + ';font-weight:600">' + esc(r.name) + '</td>',
        '<td style="' + th + '"><a href="' + (mail ? 'mailto:' : 'tel:') + esc(r.contact) + '" style="color:#0E4D3C;text-decoration:underline">' + esc(r.contact) + '</a></td>',
        '<td style="' + th + ';text-align:center;font-weight:700" class="tnum">' + (r.attendees_count || 1) + '</td>',
        '<td style="' + th + ';text-align:center">' + (r.is_vegetarian ? 'Oui' : 'Non') + '</td>',
        '<td style="' + th + ';color:#4F5E57;font-size:12px" class="tnum">' + esc((r.created_at || '').slice(0, 16).replace('T', ' ')) + '</td>',
        '<td style="' + th + ';text-align:center"><span class="tag" style="background:' + (ok ? '#DCEFE6;color:#0E4D3C' : '#FDEBEB;color:#B3261E') + '">' + (ok ? 'Confirmé' : 'Annulé') + '</span></td>',
        '<td style="' + th + ';text-align:right">' + (ok ? '<button type="button" class="btn" data-ev-cancel="' + r.id + '" data-code="' + esc(r.code) +
          '" style="min-height:32px;padding:0 12px;font-size:12px;background:#fff;border-color:#B3261E;color:#B3261E">Annuler</button>' : '<span class="hint">Annulée</span>') + '</td></tr>');
    });
    h.push('</tbody></table></div>');
    w.innerHTML = h.join('');
  }
  function loadRegs() {
    return api('/api/admin/events/registrations').then(function (d) {
      if (!d || !d.ok) return;
      regs = d.registrations || [];
      restricted = d.restricted ? (d.message || 'La liste nominative est réservée au superadmin et au responsable des événements.') : '';
      document.querySelectorAll('#sp-3 button').forEach(function (b) {
        var t = (b.textContent || '').trim();
        if (d.restricted && (t === 'Exporter la liste (.csv)' || t === 'Écrire aux inscrits')) b.style.display = 'none';
      });
      summary(d.summary || {});
      renderRegs();
    }, function () {});
  }
  function onClick(e) {
    var b = e.target.closest && e.target.closest('#sp-3 button');
    if (!b) return;
    var t = (b.textContent || '').trim();
    if (t === 'Exporter la liste (.csv)') { location.href = '/api/admin/events/export'; return; }
    if (t === 'Écrire aux inscrits') {
      var mails = Array.from(new Set(regs.filter(function (r) { return r.status === 'confirmed' && r.contact && r.contact.indexOf('@') > -1; })
        .map(function (r) { return r.contact.trim(); })));
      if (!mails.length) { flash('Aucune adresse courriel parmi les inscrits confirmés.'); return; }
      location.href = 'mailto:?bcc=' + encodeURIComponent(mails.join(',')) + '&subject=' + encodeURIComponent('Information — ' + (ins ? ins.event_title : 'Événement ASCIL'));
      return;
    }
    if (b.hasAttribute('data-ev-cancel')) {
      var id = b.getAttribute('data-ev-cancel'), code = b.getAttribute('data-code');
      if (!window.confirm('Annuler l’inscription ' + code + ' ? Les places sont libérées tout de suite.')) return;
      b.disabled = true; b.setAttribute('aria-busy', 'true'); b.textContent = 'Annulation…';
      api('/api/admin/events/registrations?id=' + encodeURIComponent(id), 'DELETE').then(function (d) {
        if (d && d.ok) { flash('Inscription ' + code + ' annulée.'); loadRegs(); }
        else { b.disabled = false; b.removeAttribute('aria-busy'); b.textContent = 'Annuler'; flash((d && d.message) || 'L’inscription n’a pas pu être annulée. Réessayez.'); }
      }, function () { b.disabled = false; b.removeAttribute('aria-busy'); b.textContent = 'Annuler'; flash('Impossible de joindre le serveur. Réessayez.'); });
    }
  }

  // ---------- Enregistrer / annuler ----------
  function pagesNext() {
    if (!pagesBase) return null;
    var on = swOn(), next = Object.assign({}, pagesBase);
    Object.keys(PUB).forEach(function (k) { next[PUB[k]] = !!on[k]; });
    return JSON.stringify(next) !== JSON.stringify(pagesBase) ? next : null;
  }
  function pubChanged() {
    var c = comp();
    return !!c && Object.keys(PUB).some(function (k) { return c.state.on[k] !== c.base[k]; });
  }
  function checkDirty() {
    var c = comp();
    if (c) c.setExtDirty(!!(window.__svx && window.__svx.dirty()) || insDirty());
  }
  window.__svCheckDirty = checkDirty;

  function saveAll() {
    if (saving) return;
    if (pubChanged() && !pagesBase) { flash('Seuls l’administrateur et l’éditeur peuvent publier ou masquer une page.'); return; }
    var tasks = [];
    if (window.__svx) {
      var xs = window.__svx.save();
      if (xs === false) return;
      tasks = tasks.concat(xs);
    }
    var next = pagesNext();
    if (next) tasks.push(api('/api/admin/settings/pages', 'PUT', next).then(function (r) { if (r && r.ok && r.settings) pagesBase = r.settings; return r; }));
    var wantIns = insDirty();
    if (!tasks.length && !wantIns) { flash('Aucun changement à enregistrer.'); return; }
    saving = true;
    flash('Enregistrement…');
    Promise.all(tasks).then(function (res) {
      var failed = res.filter(function (r) { return !r || !r.ok; })[0];
      if (failed) throw failed;
      // La liste a pu changer (titre, date, lieu) : l'événement ouvert aux inscriptions suit.
      return api('/api/admin/settings/evenements').then(function (r) {
        if (r && r.ok && r.settings) events = r.settings.items || [];
        var v = collectIns();
        if (!v || !canIns() || JSON.stringify(v) === insBase) return null;
        return api('/api/admin/events/settings', 'PUT', v).then(function (d) {
          if (!d || !d.ok) throw d || { ok: false };
          applyIns(d.settings || v, true);
          return d;
        });
      });
    }).then(function () {
      saving = false;
      if (window.__svx) window.__svx.after();
      var c = comp();
      if (c) c.commitKeys(Object.keys(PUB).concat(Object.keys(INS_SW)));
      renderSelect();
      setTimeout(checkDirty, 0);
      loadRegs();
      flash('Événements enregistrés. Le site est à jour.');
    }).catch(function (r) {
      saving = false;
      if (window.__svx) window.__svx.after();
      setTimeout(checkDirty, 0);
      flash((r && r.message) || 'L’enregistrement a échoué. Vérifiez vos valeurs et réessayez.');
    });
  }
  function undoAll() {
    var c = comp();
    if (c) c.revertBase();
    if (window.__svx) window.__svx.undo();
    if (insBase) applyIns(JSON.parse(insBase), false);
    setTimeout(checkDirty, 0);
    flash('Changements annulés.');
  }
  window.__saEvSave = saveAll;
  window.__saEvUndo = undoAll;

  function start() {
    if (started) return;
    started = true;
    document.addEventListener('click', onClick);
    document.addEventListener('input', function (e) { if (e.target && e.target.closest && e.target.closest('#sp-3')) checkDirty(); });
    document.addEventListener('change', function (e) { if (e.target && e.target.closest && e.target.closest('#sp-3')) checkDirty(); });
    document.addEventListener('click', function (e) { if (e.target && e.target.closest && e.target.closest('#sp-3 button.sw')) setTimeout(checkDirty, 0); });
    Promise.all([api('/api/auth/me'), api('/api/admin/settings/pages'), api('/api/admin/events/settings'), api('/api/admin/settings/evenements')]).then(function (r) {
      role = r[0] && r[0].ok && r[0].admin ? r[0].admin.role : '';
      if (r[1] && r[1].ok && r[1].settings) {
        pagesBase = r[1].settings;
        var sw = {};
        Object.keys(PUB).forEach(function (k) { sw[k] = pagesBase[PUB[k]] !== false; });
        var c = comp();
        if (c) c.setSwitches(sw, true);
      }
      if (r[3] && r[3].ok && r[3].settings) events = r[3].settings.items || [];
      if (r[2] && r[2].ok && r[2].settings) applyIns(r[2].settings, true);
      if (!canIns()) {
        document.querySelectorAll('#sp-3 section[aria-label="Événement ouvert aux inscriptions"] input, #sp-3 section[aria-label="Événement ouvert aux inscriptions"] select, #sp-3 section[aria-label="Événement ouvert aux inscriptions"] button')
          .forEach(function (x) { x.disabled = true; });
        var h = el('f19-hint');
        if (h) h.textContent = 'Lecture seule : seuls l’administrateur et le responsable des événements règlent les inscriptions.';
      }
      setTimeout(checkDirty, 0);
      loadRegs();
    }, function () { flash('Impossible de joindre le serveur. Rechargez la page.'); });
  }
  if (comp()) start();
  else window.addEventListener('sa-ev-ready', start, { once: true });
})();
</script>
'''

BOX = '<div id="svx-{k}" style="display:flex;flex-direction:column;gap:18px"><p class="hint" style="margin:0">Chargement des réglages…</p></div>'


def replace_sections(tpl, sp, nxt_marker, box):
    a = tpl.index(f'<div id="{sp}" class="sp">')
    b = tpl.index(nxt_marker, a)
    body = tpl[a:b]
    h = body.index('<section')
    tail = body[body.rindex('</section>') + len('</section>'):]
    return tpl[:a] + body[:h] + box + tail + tpl[b:]


def wire_panel():
    path = ROOT / 'SA-Evenements.dc.html'
    s, i, j, tpl = load(path)
    if 'id="svx-evenements"' not in tpl:
        tpl = replace_sections(tpl, 'sp-0', '<div id="sp-1" class="sp">', BOX.format(k='evenements'))
        # Onglet « Détail d'un événement » retiré : la fiche se règle dans chaque événement.
        a = tpl.index('<div id="sp-1" class="sp">')
        b = tpl.index('<div id="sp-2" class="sp">', a)
        tpl = tpl[:a] + tpl[b:]
        tpl = rep(tpl, '<a href="#sp-1">Détail d’un événement</a>', '', 2)
        tpl = tpl.replace('<option>Détail d’un événement</option>', '')
        tpl = replace_sections(tpl, 'sp-2', '<div id="sp-3" class="sp">', BOX.format(k='calendrier'))
        tpl = rep(tpl, '<sc-raw-select class="in" id="f19"><option>Iftar communautaire</option><option>Journée de parrainage d’orphelins</option></sc-raw-select>',
                  '<sc-raw-select class="in" id="f19"><option>Chargement…</option></sc-raw-select>')
        tpl = tpl.replace('<p class="warn">Petite app : elle fonctionne dans le navigateur des visiteurs, sans compte. Publiez-la seulement quand les données sont prêtes.</p>', '')
    assert 'Détail d’un événement' not in tpl.split('class Component')[0] and 'pub_evdetail' not in tpl.split('class Component')[0]
    assert 'Inscriptions Ramadan 2027' not in tpl.split('class Component')[0], 'fausse page restante'

    m = re.search(r'this\.base = (\{.*?\});', tpl)
    assert m, 'base du composant introuvable'
    old = json.loads(m.group(1))
    base = {k: v for k, v in old.items() if k in PUB or k in INS_SW}
    assert set(base) == set(PUB) | set(INS_SW), base
    comp = COMPONENT_SCRIPT.replace('__BASE__', json.dumps(base))
    tpl, n = re.subn(r'class Component extends DCLogic \{.*?\n\}', lambda _: comp, tpl, count=1, flags=re.S)
    assert n == 1
    # L'ancien script des inscriptions (wire_events.py) est remplacé par celui-ci.
    tpl = re.sub(r'<script id="(?:sa-evenements-sync|sa-ev-x|sa-ev-sync)">.*?</script>\s*', '', tpl, flags=re.S)
    engine = engine_source().replace('__TABS__', json.dumps(TABS, ensure_ascii=False))
    sync = SYNC_SCRIPT.replace('__PUB__', json.dumps(PUB)).replace('__INS_SW__', json.dumps(INS_SW))
    k = tpl.rindex('</body>')
    tpl = tpl[:k] + engine + sync + tpl[k:]
    save(path, s, i, j, tpl)
    print('SA-Evenements.dc.html : Annonces, Calendrier et Inscription reliés (clés evenements, calendrier, event_registration, pages)')


def matching_end(tpl, start):
    """Fin de la boucle <sc-for> qui commence à start, en tenant compte des boucles imbriquées
    (la carte d'une annonce contient elle-même une boucle d'options)."""
    depth, k = 0, start
    while True:
        o = tpl.find('<sc-for', k)
        c = tpl.find('</sc-for>', k)
        assert c != -1, 'fin de la boucle des annonces introuvable'
        if o != -1 and o < c:
            depth += 1
            k = o + len('<sc-for')
        else:
            depth -= 1
            k = c + len('</sc-for>')
            if depth == 0:
                return k


def wire_panneau_accueil():
    """La liste « Dernières annonces » du panneau Accueil renvoie vers Événements."""
    path = ROOT / 'SA-Panneau.dc.html'
    s, i, j, tpl = load(path)
    if 'id="ann-from-ev"' not in tpl:
        a = tpl.index('<button type="button" class="btn btn-line" style="align-self:flex-start" disabled="{{annFull}}" sc-camel-on-click="{{addAnn}}">+ Ajouter une annonce</button>')
        b = matching_end(tpl, tpl.index('<sc-for list="{{annonces}}"', a))
        note = ('<p id="ann-from-ev" class="hint" style="margin:0">Les annonces affichées sont les prochains événements de la page Événements '
                '(à venir, puis en cours, puis les plus récents). '
                '<a href="SA-Evenements.dc.html" style="color:#0E4D3C;font-weight:700">Gérer les événements</a></p>')
        tpl = tpl[:a] + note + tpl[b:]
        tpl = rep(tpl, '<p class="dsc">Les cartes « La vie de la communauté ».</p>',
                  '<p class="dsc">Les cartes « La vie de la communauté », tirées des événements.</p>')
    save(path, s, i, j, tpl)
    print('SA-Panneau.dc.html : Dernières annonces tirées de la liste des événements')


# =====================================================================================
# Page Événements publique
# =====================================================================================

PIN = ('<svg class="icon" aria-hidden="true" width="{n}" height="{n}" sc-camel-view-box="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
       'stroke-linecap="round" stroke-linejoin="round" style="width:{n}px;height:{n}px"><path d="M12 21s-7-6.2-7-11a7 7 0 0 1 14 0c0 4.8-7 11-7 11z"></path><circle cx="12" cy="10" r="2.5"></circle></svg>')
CLOCK = ('<svg class="icon" aria-hidden="true" width="16" height="16" sc-camel-view-box="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
         'stroke-linecap="round" stroke-linejoin="round" style="width:16px;height:16px"><circle cx="12" cy="12" r="9"></circle><path d="M12 7v5l3 2"></path></svg>')
ARROW = ('<svg class="icon" aria-hidden="true" width="16" height="16" sc-camel-view-box="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
         'stroke-linecap="round" stroke-linejoin="round" style="width:16px;height:16px"><path d="M5 12h14M13 6l6 6-6 6"></path></svg>')


def fiche(x):
    """Fiche dépliable d'un événement (x = nom de la variable de boucle ou de l'objet)."""
    return sc_if(f'{x}.open',
        '<div class="pop" style="margin-top:16px;padding-top:16px;border-top:1px solid #E9E3D3;display:flex;flex-direction:column;gap:10px">'
        + sc_if(f'{x}.hasDesc', f'<p style="margin:0;white-space:pre-line">{{{{{x}.description}}}}</p>', 'true')
        + sc_if(f'{x}.hasPart', f'<p style="margin:0"><strong>Partenaire :</strong> {{{{{x}.partenaire}}}}</p>', 'false')
        + sc_if(f'{x}.hasPublic', f'<p style="margin:0"><strong>Public :</strong> {{{{{x}.public}}}}</p>', 'false')
        + sc_if(f'{x}.hasPlaces', f'<p style="margin:0"><strong>Places :</strong> {{{{{x}.placesTxt}}}}</p>', 'false')
        + '<div style="display:flex;gap:10px;flex-wrap:wrap">'
        + sc_if(f'{x}.hasIns', f'<a class="btn btn-green" href="{{{{{x}.insHref}}}}">{{{{{x}.insLabel}}}}</a>', 'false')
        + sc_if(f'{x}.showMap', f'<a class="btn btn-ghost" href="{{{{{x}.map}}}}" target="_blank" rel="noopener">{PIN.format(n=18)}Itinéraire</a>', 'false')
        + sc_if(f'{x}.canShare', f'<button type="button" class="btn btn-ghost" sc-camel-on-click="{{{{{x}.share}}}}" aria-live="polite">{{{{{x}.shareLbl}}}}</button>', 'false')
        + '</div></div>', 'false')


def ev_card(x):
    return (f'<div class="card" id="{{{{{x}.anchor}}}}" style="display:flex;gap:20px;align-items:flex-start;scroll-margin-top:96px">'
            '<span class="tnum" style="flex:none;width:76px;border-radius:14px;background:#F4EBD6;text-align:center;padding:10px 0;color:#0B0F1A">'
            f'<span style="display:block;font-size:28px;font-weight:700;line-height:1">{{{{{x}.day}}}}</span>'
            f'<span style="display:block;font-size:13px;font-weight:700;text-transform:uppercase">{{{{{x}.mon}}}}</span>'
            f'<span style="display:block;font-size:12px">{{{{{x}.year}}}}</span></span>'
            '<div style="flex:1;min-width:0">'
            f'<span class="h3" style="display:block;font-size:20px;overflow-wrap:anywhere">{{{{{x}.titre}}}}</span>'
            + sc_if(f'{x}.hasLieu', f'<span style="display:flex;gap:6px;align-items:center;margin-top:6px;font-weight:600;color:#0B0F1A;font-size:15px">{PIN.format(n=16)}{{{{{x}.lieuTxt}}}}</span>', 'true')
            + sc_if(f'{x}.hasHeure', f'<span class="tnum" style="display:flex;gap:6px;align-items:center;margin-top:4px;font-size:15px;color:#515B66">{CLOCK}{{{{{x}.heure}}}}</span>', 'false')
            + sc_if(f'{x}.hasResume', f'<span class="muted" style="display:block;margin-top:6px">{{{{{x}.resume}}}}</span>', 'true')
            + sc_if(f'{x}.hasPill', f'<span class="pill" style="margin-top:10px;background:#F4EBD6;color:#7A5A1E">{{{{{x}.pill}}}}</span>', 'false')
            + '<div style="display:flex;gap:18px;flex-wrap:wrap;margin-top:10px;align-items:center">'
            + sc_if(f'{x}.hasLien', f'<a class="link" href="{{{{{x}.lienHref}}}}">{{{{{x}.lienTexte}}}} {ARROW}</a>', 'false')
            + sc_if(f'{x}.hasFiche', f'<button type="button" class="link" sc-camel-on-click="{{{{{x}.toggle}}}}" aria-expanded="{{{{{x}.exp}}}}" '
                    f'style="background:none;border:0;padding:0;min-height:44px;cursor:pointer;font:inherit;font-weight:700">{{{{{x}.ficheLbl}}}}</button>', 'false')
            + '</div>' + fiche(x) + '</div></div>')


EV_JS = r"""
    /*ascil-evenements*/
    const PT = (typeof window !== 'undefined' && window.__ascilPrayer) || {};
    const EV = PT.evenements || __EV__;
    const pre = (typeof location !== 'undefined' && /\/(M-|T-)[^\/]*$/.exec(location.pathname)) ? /\/(M-|T-)[^\/]*$/.exec(location.pathname)[1] : '';
    let today = PT.date || '';
    if (!today) { try { today = new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Moncton', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date()); } catch (e) { today = ''; } }
    const MOIS = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'];
    const MC = ['janv.', 'févr.', 'mars', 'avr.', 'mai', 'juin', 'juil.', 'août', 'sept.', 'oct.', 'nov.', 'déc.'];
    const LIEUX = { mosquee: 'Mosquée — 106, rue de l’Église', salle: 'Salle de l’Aïd', campagne: 'Campagne de l’ASCIL', autre: '' };
    const PAGES = { dons: 'Dons', campagne: 'N3-Campagne', horaires: 'Horaires', services: 'Services', cours: 'N2-Cours', inscription: 'N3-Inscription',
      calendrier: 'N3-Calendrier', contact: 'Contact', ressources: 'Ressources' };
    const page = (k) => (PAGES[k] ? pre + PAGES[k] + '.dc.html' : '');
    const hm = (t) => (t ? t.replace(':', ' h ').replace(/ h 00$/, ' h') : '');
    const url = typeof location !== 'undefined' ? location.origin + location.pathname : '';
    const items = (EV.items || []).filter((x) => x.on && x.titre);
    const pastOf = (x) => !!x.date && !!today && x.date < today;
    const mk = (x) => {
      const open = this.state.evo === x.id;
      const lieuTxt = x.lieuTexte || LIEUX[x.lieu] || '';
      const heure = x.debut ? hm(x.debut) + (x.fin ? ' à ' + hm(x.fin) : '') : '';
      const insHref = x.inscription === 'formulaire' ? pre + 'N3-Inscription.dc.html' : x.inscription === 'contact' ? pre + 'Contact.dc.html' : '';
      const hasFiche = !!(x.description || x.partenaire || x.public || x.places > 0 || insHref || (x.itineraire && lieuTxt) || EV.partage);
      const shared = this.state.evShared === x.id;
      return {
        id: x.id, anchor: 'ev-' + x.id, titre: x.titre, resume: x.resume || '', hasResume: !!x.resume,
        day: x.date ? String(parseInt(x.date.slice(8, 10), 10)) : '—',
        mon: x.date ? MC[parseInt(x.date.slice(5, 7), 10) - 1] : 'En',
        year: x.date ? x.date.slice(0, 4) : 'cours',
        monthYear: x.date ? MOIS[parseInt(x.date.slice(5, 7), 10) - 1] + ' ' + x.date.slice(0, 4) : 'En cours',
        lieuTxt, hasLieu: !!lieuTxt, heure, hasHeure: !!heure,
        pill: x.inscription === 'formulaire' ? 'Inscription requise' : x.inscription === 'contact' ? 'Sur inscription, par message' : '',
        hasPill: x.inscription !== 'non',
        lienHref: page(x.lien), lienTexte: x.lienTexte || 'En savoir plus', hasLien: !!page(x.lien),
        hasFiche, open, exp: String(open), ficheLbl: open ? 'Masquer les détails' : 'Voir les détails',
        toggle: () => this.setState({ evo: open ? '' : x.id }),
        description: x.description || '', hasDesc: !!x.description, partenaire: x.partenaire || '', hasPart: !!x.partenaire,
        public: x.public || '', hasPublic: !!x.public,
        placesTxt: x.places > 0 ? x.places + ' places' : 'Illimitées', hasPlaces: x.inscription !== 'non' || x.places > 0,
        insHref, hasIns: !!insHref, insLabel: x.inscription === 'contact' ? 'S’inscrire par message' : 'S’inscrire',
        map: 'https://maps.google.com/?q=' + encodeURIComponent((lieuTxt.split('—').pop() || lieuTxt).trim() + ' Edmundston'),
        showMap: !!x.itineraire && !!lieuTxt && x.lieu !== 'campagne',
        canShare: !!EV.partage, shareLbl: shared ? 'Lien copié' : 'Partager',
        share: () => {
          const u = url + '#ev-' + x.id;
          try { if (navigator.share) { navigator.share({ title: x.titre, url: u }).catch(() => {}); return; } } catch (e) {}
          try { navigator.clipboard && navigator.clipboard.writeText(u); } catch (e) {}
          this.setState({ evShared: x.id }); clearTimeout(this.evst); this.evst = setTimeout(() => this.setState({ evShared: '' }), 2000);
        },
        _date: x.date, _debut: x.debut, _lieu: x.lieu,
      };
    };
    const byDate = (a, b) => (a.date + a.debut).localeCompare(b.date + b.debut);
    const upAll = items.filter((x) => x.date && !pastOf(x)).sort(byDate);
    const ongoing = items.filter((x) => !x.date);
    const pastAll = items.filter(pastOf).sort((a, b) => byDate(b, a));
    // À la une : l'événement choisi, sinon le prochain événement daté.
    const U = EV.une || {};
    let uneX = null;
    if (U.on !== false) {
      if (U.choix && U.choix !== 'auto') uneX = items.filter((x) => x.id === U.choix)[0] || null;
      if (!uneX) uneX = upAll[0] || null;
    }
    const une = uneX ? mk(uneX) : {};
    const uneBtnKind = U.bouton === 'inscrire' && une.hasIns ? 'inscrire' : U.bouton === 'aucun' ? '' : 'details';
    const evf = this.state.evf || 'tous';
    const keep = (x) => evf === 'tous' || x.lieu === evf;
    const listX = upAll.concat(ongoing).filter((x) => !uneX || x.id !== uneX.id).filter(keep);
    const P = EV.passes || {};
    const pastX = pastAll.filter((x) => !uneX || x.id !== uneX.id).filter(keep);
    const pastShown = P.nombre > 0 ? pastX.slice(0, P.nombre) : pastX;
    const fixes = ((EV.fixes && EV.fixes.items) || []).filter((f) => f.on && f.titre).map((f) => ({ titre: f.titre, texte: f.texte || '', hasTexte: !!f.texte }));
    const O = EV.outils || {};
    return {
      showUne: !!uneX, une, uneEyebrow: uneX && pastOf(uneX) ? 'Événement passé' : uneX && !uneX.date ? 'En ce moment' : 'Prochain événement',
      uneHasBtn: !!uneBtnKind && (uneBtnKind === 'inscrire' || une.hasFiche),
      uneBtnLabel: uneBtnKind === 'inscrire' ? une.insLabel : une.ficheLbl,
      uneBtnIsLink: uneBtnKind === 'inscrire', uneBtnIsToggle: uneBtnKind === 'details', uneHref: une.insHref || '#',
      uneShowMap: !!une.showMap && !une.open,
      showFiltres: EV.filtres !== false,
      evUp: listX.map(mk), evEmpty: listX.length === 0,
      evEmptyTxt: evf === 'tous' ? 'Aucun événement annoncé pour l’instant. Les prochaines annonces paraîtront ici.' : 'Aucun événement à venir à cet endroit. Essayez « Tous ».',
      showPast: P.on !== false && pastShown.length > 0, evPast: pastShown.map(mk),
      showFixes: !!(EV.fixes && EV.fixes.on) && fixes.length > 0, fixes,
      showOutils: O.on !== false && (O.calendrier || O.inscription || O.dua), oCal: !!O.calendrier, oIns: !!O.inscription, oDua: !!O.dua,
    };"""


def set_xvals(tpl, body, marker):
    la = tpl.index('<script type="text/x-dc"')
    lb = tpl.index('</script>', la)
    code = tpl[la:lb]
    new = '  xvals() {' + body + '\n  }\n'
    if marker in code or '  xvals() {' in code:
        a = code.index('  xvals() {')
        b = code.index('\n  }\n', a) + len('\n  }\n')
        code = code[:a] + new + code[b:]
    else:
        a = code.index('  renderVals() {')
        code = code[:a] + new + '\n' + code[a:]
    return tpl[:la] + code + tpl[lb:]


def patch_evenements(tpl):
    a = tpl.index('<main'); b = tpl.index('</main>')
    m = tpl[a:b]
    # ---------- À la une ----------
    sa, sb = section_span(m, '<section class="sec" aria-labelledby="pe-t">')
    sec = m[sa:sb]
    sec = rep(sec, '<p class="eyebrow">Prochain événement</p>', '<p class="eyebrow">{{uneEyebrow}}</p>')
    sec = rep(sec, 'line-height:1;color:#D9B46C">25</p>', 'line-height:1;color:#D9B46C">{{une.day}}</p>')
    sec = rep(sec, 'font-weight:700">avril 2026</p>', 'font-weight:700">{{une.monthYear}}</p>')
    sec = resub(sec, r'(<p class="tnum" style="[^"]*">)13 h 45 à 15 h 45</p>', lambda x: sc_if('une.hasHeure', x.group(1) + '{{une.heure}}</p>', 'false'))
    sec = resub(sec, r'<span class="pill"([^>]*)>Inscription requise</span>', lambda x: sc_if('une.hasPill', '<span class="pill"' + x.group(1) + '>{{une.pill}}</span>', 'false'))
    sec = rep(sec, ' style="margin-top:14px">Journée de parrainage d’orphelins</h2>', ' style="margin-top:14px;overflow-wrap:anywhere">{{une.titre}}</h2>')
    sec = resub(sec, r'(<p style="margin:12px 0 0">)Avec l’organisme Soleil des Orphelins\.</p>', lambda x: sc_if('une.hasResume', x.group(1) + '{{une.resume}}</p>'))
    sec = resub(sec, r'(<p style="margin:12px 0 0;display:flex[^"]*">)(<svg.*?</svg>)Mosquée — 106, rue de l’Église</p>',
                lambda x: sc_if('une.hasLieu', x.group(1) + x.group(2) + '{{une.lieuTxt}}</p>'))
    sec = resub(sec, r'<a class="btn btn-green" href="(?:[MT]-)?EvenementDetail\.dc\.html">S’inscrire</a>',
                sc_if('uneHasBtn', sc_if('uneBtnIsLink', '<a class="btn btn-green" href="{{uneHref}}">{{uneBtnLabel}}</a>', 'false')
                      + sc_if('uneBtnIsToggle', '<button type="button" class="btn btn-green" sc-camel-on-click="{{une.toggle}}" aria-expanded="{{une.exp}}">{{uneBtnLabel}}</button>'), 'true'))
    sec = resub(sec, r'<a class="btn btn-ghost" href="https://maps\.google\.com/\?q=174\+rue\+Lafontaine\+Edmundston">(<svg.*?</svg>)Itinéraire</a>',
                lambda x: sc_if('uneShowMap', '<a class="btn btn-ghost" href="{{une.map}}" target="_blank" rel="noopener">' + x.group(1) + 'Itinéraire</a>'))
    k = sec.rindex('</div>\n   </div>\n  </div>\n </div>\n</section>')
    sec = sec[:k] + fiche('une') + sec[k:]
    m = m[:sa] + sc_if('showUne', sec) + m[sb:]
    # ---------- Liste ----------
    sa, sb = section_span(m, '<section style="padding-bottom:80px" aria-labelledby="ls-t">')
    sec = m[sa:sb]
    sec = resub(sec, r'(<div class="seg" role="group" aria-label="Filtrer par lieu">.*?</div>)', lambda x: sc_if('showFiltres', x.group(1)))
    la = sec.index('<div class="g2 ev-list evl ev-{{evf}}" style="margin-top:24px">')
    lb = sec.index('<details class="past"', la)
    lb = sec.rindex('</div>', la, lb) + len('</div>')
    sec = (sec[:la] + '<div class="g2 ev-list" style="margin-top:24px">'
           + '<sc-for list="{{evUp}}" as="e" hint-placeholder-count="2">' + ev_card('e') + '</sc-for></div>'
           + sc_if('evEmpty', '<div class="card sand" style="margin-top:24px;text-align:center"><p style="margin:0;font-weight:700">{{evEmptyTxt}}</p></div>', 'false')
           + sec[lb:])
    da = sec.index('<details class="past"')
    db = sec.index('</details>', da) + len('</details>')
    det = sec[da:db]
    ia = det.index('<div style="padding:8px 0 16px;opacity:.75">')
    det = (det[:ia] + '<div style="padding:8px 0 16px;opacity:.75;display:flex;flex-direction:column;gap:12px">'
           + '<sc-for list="{{evPast}}" as="p" hint-placeholder-count="1">' + ev_card('p') + '</sc-for></div>\n  </details>')
    sec = sec[:da] + sc_if('showPast', det) + sec[db:]
    m = m[:sa] + sec + m[sb:]
    # ---------- Rendez-vous fixes ----------
    sa, sb = section_span(m, '<section class="sand" aria-labelledby="rv-t"')
    sec = m[sa:sb]
    ga = sec.index('<div class="g4" style="margin-top:28px">') + len('<div class="g4" style="margin-top:28px">')
    ge = sec.rindex('</div>\n </div>\n</section>')
    icon = re.search(r'<span style="color:#0B0F1A">(<svg.*?</svg>)</span>', sec[ga:ge], re.S).group(1)
    sec = (sec[:ga] + '\n   <sc-for list="{{fixes}}" as="f" hint-placeholder-count="4"><div class="card"><span style="color:#0B0F1A">' + icon + '</span>'
           '<p class="h3" style="margin-top:12px;font-size:19px">{{f.titre}}</p>'
           + sc_if('f.hasTexte', '<p class="muted" style="margin:6px 0 0;font-size:15px">{{f.texte}}</p>') + '</div></sc-for>\n  ' + sec[ge:])
    m = m[:sa] + sc_if('showFixes', sec) + m[sb:]
    # ---------- Aller plus loin ----------
    sa = m.index('<section class="" style=""><div class="wrap sec"><p class="eyebrow">Outils</p>')
    sb = m.index('</section>', sa) + len('</section>')
    sec = m[sa:sb]
    for name, page in (('oCal', 'N3-Calendrier'), ('oIns', 'N3-Inscription'), ('oDua', 'N3-Dua')):
        sec = resub(sec, r'(<a class="card" href="(?:[MT]-)?' + page + r'\.dc\.html".*?</a>)', lambda x, n=name: sc_if(n, x.group(1)))
    m = m[:sa] + sc_if('showOutils', sec) + m[sb:]
    # ---------- Rester informé : l'emplacement réservé disparaît ----------
    m = resub(m, r'\s*<div class="card" style="border-style:dashed[^"]*">\s*<p class="h3"[^>]*>Alertes par courriel</p>.*?</div>', '')
    m = rep(m, '<section class="sec" aria-labelledby="ri-t">\n <div class="wrap g2">', '<section class="sec" aria-labelledby="ri-t">\n <div class="wrap">')
    m = rep(m, '<div class="card" style="background:#0B0F1A;color:#fff;border-color:#0B0F1A">', '<div class="card" style="background:#0B0F1A;color:#fff;border-color:#0B0F1A;max-width:720px">')
    assert 'EvenementDetail' not in m and 'Emplacement réservé' not in m and '25</p>' not in m
    return tpl[:a] + m + tpl[b:]


# =====================================================================================
# Calendrier du mois
# =====================================================================================

CAL_JS = r"""
    /*ascil-calendrier*/
    const PT = (typeof window !== 'undefined' && window.__ascilPrayer) || {};
    const EV = PT.evenements || __EV__, CAL = PT.calendrier || __CAL__, CO = PT.cours || null;
    const st = this.state;
    const pre = (typeof location !== 'undefined' && /\/(M-|T-)[^\/]*$/.exec(location.pathname)) ? /\/(M-|T-)[^\/]*$/.exec(location.pathname)[1] : '';
    let today = PT.date || '';
    if (!today) { try { today = new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Moncton', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date()); } catch (e) { today = '2026-01-01'; } }
    const MOIS = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'];
    const T = {"cours": ["Cours", "#0B0F1A", "#fff", "#0B0F1A"], "priere": ["Prière et spiritualité", "#D9B46C", "#141B2C", "#D9B46C"], "comm": ["Communauté", "#141B2C", "#fff", "#141B2C"], "collecte": ["Collectes", "#fff", "#0B0F1A", "#0B0F1A"]};
    const CATS = Object.keys(T).filter((k) => !CAL.categories || CAL.categories[k] !== false);
    const off = st.cm || 0;
    let y = parseInt(today.slice(0, 4), 10), mo = parseInt(today.slice(5, 7), 10) - 1 + off;
    y += Math.floor(mo / 12); mo = ((mo % 12) + 12) % 12;
    const ym = y + '-' + String(mo + 1).padStart(2, '0');
    const dim = new Date(Date.UTC(y, mo + 1, 0)).getUTCDate();
    const lead = (new Date(Date.UTC(y, mo, 1)).getUTCDay() + 6) % 7;
    const hm = (t) => (t ? t.replace(':', ' h ').replace(/ h 00$/, ' h') : '');
    const span = (a, b) => (a ? hm(a) + (b ? ' – ' + hm(b) : '') : 'Toute la journée');
    const LIEUX = { mosquee: 'Mosquée — 106, rue de l’Église', salle: 'Salle de l’Aïd', campagne: 'Campagne de l’ASCIL', autre: '' };
    const E = [];
    if (CAL.evenements !== false) {
      (EV.items || []).filter((x) => x.on && x.titre && x.date && x.date.slice(0, 7) === ym).forEach((x) => {
        const href = x.inscription === 'formulaire' ? pre + 'N3-Inscription.dc.html' : x.inscription === 'contact' ? pre + 'Contact.dc.html' : '';
        E.push({ d: parseInt(x.date.slice(8, 10), 10), t: x.titre, type: x.categorie || 'comm', h: span(x.debut, x.fin), l: x.lieuTexte || LIEUX[x.lieu] || '',
          desc: x.resume || x.description || '', reg: !!href, href, regLbl: x.inscription === 'contact' ? 'S’inscrire par message' : 'S’inscrire',
          date: x.date, debut: x.debut, fin: x.fin });
      });
    }
    if (CAL.cours !== false && CO && Array.isArray(CO.items)) {
      const WD = { Dimanche: 0, Lundi: 1, Mardi: 2, Mercredi: 3, Jeudi: 4, Vendredi: 5, Samedi: 6 };
      const lieu = (CO.infos && CO.infos.lieu) || '106, rue de l’Église';
      CO.items.filter((c) => c.on && c.titre && WD[c.jour] !== undefined).forEach((c) => {
        for (let n = 1; n <= dim; n++) {
          if (new Date(Date.UTC(y, mo, n)).getUTCDay() !== WD[c.jour]) continue;
          E.push({ d: n, t: c.titre, type: 'cours', h: span(c.debut, c.fin), l: lieu, desc: c.prof || '', reg: CO.inscriptions !== false, href: pre + 'N2-Cours.dc.html',
            regLbl: 'Voir le cours', date: ym + '-' + String(n).padStart(2, '0'), debut: c.debut, fin: c.fin });
        }
      });
    }
    E.sort((a, b) => a.d - b.d || String(a.debut).localeCompare(String(b.debut)));
    const cf = st.cf || {};
    const vis = E.map((e, i) => Object.assign({ i }, e)).filter((e) => CATS.indexOf(e.type) > -1 && cf[e.type] !== false);
    const view = st.cviewPicked ? st.cview : (CAL.vue || 'mois');
    const todayN = today.slice(0, 7) === ym ? parseInt(today.slice(8, 10), 10) : 0;
    const cells = [];
    const nCells = Math.ceil((lead + dim) / 7) * 7;
    for (let k = 0; k < nCells; k++) {
      const n = k - lead + 1, ok = n >= 1 && n <= dim, evs = ok ? vis.filter((e) => e.d === n) : [];
      const has = (t) => evs.some((e) => e.type === t), sel = ok && st.cday === n, isT = n === todayN;
      cells.push({ n: ok ? n : '', aria: ok ? n + ' ' + MOIS[mo] + ', ' + evs.length + ' événement(s)' + (isT ? ', aujourd’hui' : '') : 'Hors du mois', pressed: String(sel), op: ok ? 1 : 0.25,
        bg: sel ? '#0B0F1A' : (isT ? '#F6E7C4' : '#fff'), fg: sel ? '#fff' : '#141B2C', bd: sel ? '#0B0F1A' : '#E9E3D3',
        d1: has('cours'), d2: has('priere'), d3: has('comm'), d4: has('collecte'), pick: () => ok && this.setState({ cday: sel ? 0 : n, cev: -1 }) });
    }
    const listSrc = (st.cday && view === 'mois') ? vis.filter((e) => e.d === st.cday) : vis;
    const deco = (e) => ({ tl: T[e.type][0], tbg: T[e.type][1], tfg: T[e.type][2], tbd: T[e.type][3] });
    const fe0 = vis.filter((e) => e.i === st.cev)[0];
    const moC = ['JANV.', 'FÉVR.', 'MARS', 'AVR.', 'MAI', 'JUIN', 'JUIL.', 'AOÛT', 'SEPT.', 'OCT.', 'NOV.', 'DÉC.'][mo];
    const go = (d) => this.setState({ cm: off + d, cday: 0, cev: -1 });
    const ics = (e) => {
      const pad = (s) => String(s).padStart(2, '0');
      const dt = (d, t) => d.replace(/-/g, '') + (t ? 'T' + t.replace(':', '') + '00' : '');
      const next = (d) => { const x = new Date(d + 'T12:00:00Z'); x.setUTCDate(x.getUTCDate() + 1); return x.getUTCFullYear() + '-' + pad(x.getUTCMonth() + 1) + '-' + pad(x.getUTCDate()); };
      const clean = (s) => String(s || '').replace(/[\\;,]/g, (c) => '\\' + c).replace(/\n/g, '\\n');
      const lines = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//ASCIL//Calendrier//FR', 'BEGIN:VEVENT',
        'UID:' + e.date + '-' + e.i + '@ascil', 'DTSTAMP:' + new Date().toISOString().replace(/[-:]/g, '').slice(0, 15) + 'Z',
        e.debut ? 'DTSTART;TZID=America/Moncton:' + dt(e.date, e.debut) : 'DTSTART;VALUE=DATE:' + dt(e.date),
        e.debut ? 'DTEND;TZID=America/Moncton:' + dt(e.date, e.fin || e.debut) : 'DTEND;VALUE=DATE:' + dt(next(e.date)),
        'SUMMARY:' + clean(e.t), 'LOCATION:' + clean(e.l), 'DESCRIPTION:' + clean(e.desc), 'END:VEVENT', 'END:VCALENDAR'];
      try {
        const blob = new Blob([lines.join('\r\n')], { type: 'text/calendar;charset=utf-8' });
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob); a.download = 'ascil-' + e.date + '.ics';
        document.body.appendChild(a); a.click(); a.remove();
        setTimeout(() => URL.revokeObjectURL(a.href), 1000);
      } catch (err) {}
      this.setState({ agd: true });
    };
    const monthTitle = MOIS[mo].charAt(0).toUpperCase() + MOIS[mo].slice(1) + ' ' + y;
    return {
      monthTitle, leadMonth: MOIS[mo] + ' ' + y, cPrev: () => go(-1), cNext: () => go(1), cToday: () => go(-off), notThisMonth: off !== 0,
      vMonthP: String(view === 'mois'), vListP: String(view === 'liste'),
      vMonth: () => this.setState({ cview: 'mois', cviewPicked: true }), vList: () => this.setState({ cview: 'liste', cviewPicked: true, cday: 0 }),
      isMonth: view === 'mois', cells,
      cTypes: CATS.map((k) => { const on = cf[k] !== false; return { label: T[k][0], pressed: String(on), dot: T[k][1], dotb: T[k][3], bg: on ? '#fff' : '#F7F2E4', bd: on ? T[k][3] : '#E9E3D3', op: on ? 1 : 0.6,
        toggle: () => this.setState({ cf: Object.assign({}, cf, { [k]: !on }) }) }; }),
      listTitle: (st.cday && view === 'mois') ? st.cday + ' ' + MOIS[mo] : 'Tous les événements de ' + MOIS[mo],
      listEmpty: listSrc.length === 0,
      evList: listSrc.map((e) => Object.assign({}, e, deco(e), { mo: moC, pressed: String(st.cev === e.i), bd: st.cev === e.i ? '#D9B46C' : '#E9E3D3', pick: () => this.setState({ cev: e.i, agd: false }) })),
      hasFiche: !!fe0, noFiche: !fe0,
      fe: fe0 ? Object.assign({}, fe0, deco(fe0), { date: fe0.d + ' ' + MOIS[mo] + ' ' + y, hasDesc: !!fe0.desc, hasLieu: !!fe0.l }) : {},
      showAgenda: CAL.agenda !== false, addAgenda: () => { if (fe0) ics(fe0); }, agendaLabel: st.agd ? 'Fichier agenda téléchargé' : 'Ajouter à mon agenda',
    };"""

CHEV = ('<svg class="icon" aria-hidden="true" width="18" height="18" sc-camel-view-box="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
        'stroke-linecap="round" stroke-linejoin="round" style="width:18px;height:18px"><path d="{d}"></path></svg>')


def patch_calendrier(tpl):
    a = tpl.index('<main'); b = tpl.index('</main>')
    m = tpl[a:b]
    m = resub(m, r'<div class="flag" role="note".*?</p></div>', '')
    m = rep(m, 'Tout ce qui se passe en novembre, d’un coup d’œil', 'Tout ce qui se passe en {{leadMonth}}, d’un coup d’œil')
    nav = ('<div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">'
           '<button type="button" class="btn btn-line" sc-camel-on-click="{{cPrev}}" aria-label="Mois précédent" style="min-width:44px;padding:0 12px">' + CHEV.format(d='M15 18l-6-6 6-6') + '</button>'
           '<button type="button" class="btn btn-line" sc-camel-on-click="{{cNext}}" aria-label="Mois suivant" style="min-width:44px;padding:0 12px">' + CHEV.format(d='M9 18l6-6-6-6') + '</button>'
           + sc_if('notThisMonth', '<button type="button" class="btn btn-line" sc-camel-on-click="{{cToday}}">Ce mois-ci</button>', 'false') + '</div>')
    m = rep(m, '<h2 id="cal-t" class="h2">Novembre 2026 <span class="ex">[EXEMPLE À MODIFIER]</span></h2>',
            '<h2 id="cal-t" class="h2" aria-live="polite">{{monthTitle}}</h2>' + nav)
    m = rep(m, '<span style="font-size:11px;font-weight:700">NOV.</span>', '<span style="font-size:11px;font-weight:700">{{e.mo}}</span>')
    m = resub(m, r'(<p style="margin:6px 0 0;display:flex;gap:8px;align-items:center">)(<svg.*?</svg>)\{\{fe\.l\}\}</p>',
              lambda x: sc_if('fe.hasLieu', x.group(1) + x.group(2) + '{{fe.l}}</p>'))
    m = rep(m, '<p style="margin:14px 0 0">{{fe.desc}} <span class="ex">[EXEMPLE À MODIFIER]</span></p>',
            sc_if('fe.hasDesc', '<p style="margin:14px 0 0">{{fe.desc}}</p>'))
    m = resub(m, r'<a class="btn btn-gold" href="(?:[MT]-)?N3-Inscription\.dc\.html">S’inscrire</a>', '<a class="btn btn-gold" href="{{fe.href}}">{{fe.regLbl}}</a>')
    m = rep(m, '<button type="button" class="btn btn-ghost" sc-camel-on-click="{{addAgenda}}">{{agendaLabel}}</button>',
            sc_if('showAgenda', '<button type="button" class="btn btn-ghost" sc-camel-on-click="{{addAgenda}}" aria-live="polite">{{agendaLabel}}</button>'))
    assert 'EXEMPLE À MODIFIER' not in m and 'prototype' not in m
    return tpl[:a] + m + tpl[b:]


def defaults():
    js = ("import('./functions/_lib/settings.js').then((m) => { const d = m.DEFAULT_SETTINGS; "
          "process.stdout.write(JSON.stringify({ evenements: d.evenements, calendrier: d.calendrier })); })")
    out = subprocess.run(['node', '--input-type=module', '-e', js], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def wire_public():
    d = defaults()
    ev = json.dumps(d['evenements'], ensure_ascii=False)
    for pre in ('', 'M-', 'T-'):
        path = ROOT / f'{pre}Evenements.dc.html'
        s, i, j, tpl = load(path)
        if '{{uneEyebrow}}' not in tpl:
            tpl = patch_evenements(tpl)
        tpl = set_xvals(tpl, EV_JS.replace('__EV__', ev), '/*ascil-evenements*/')
        save(path, s, i, j, tpl)
        path = ROOT / f'{pre}N3-Calendrier.dc.html'
        s, i, j, tpl = load(path)
        if '{{monthTitle}}' not in tpl:
            tpl = patch_calendrier(tpl)
        tpl = set_xvals(tpl, CAL_JS.replace('__EV__', ev).replace('__CAL__', json.dumps(d['calendrier'])), '/*ascil-calendrier*/')
        save(path, s, i, j, tpl)
    print('Evenements et N3-Calendrier (PC, M-, T-) : liste, à la une, fiches, filtres, passés, rendez-vous, calendrier reliés')


if __name__ == '__main__':
    wire_panel()
    wire_panneau_accueil()
    wire_public()
