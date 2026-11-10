"""Ressources (étape R).

- Panneau SA-Ressources :
  - onglet « Nouveaux arrivants » (clé ressources) : phrase d'accueil, Manger halal, Mosquées et centres
    voisins, Services publics, Repères personnels, Pour bien s'installer, Étudier et scolariser. Champs
    construits par le moteur commun des pages de services (copié depuis wire_service_pages.py) ;
  - onglet « Dua et annonces » : modération réelle (table dua_messages, migration 0010 : à valider,
    signalés, publiés ; publier, modifier, refuser, retirer, supprimer) et règles du mur (clé dua) ;
  - publication des pages Ressources et Dua (clé pages).
- Pages publiques Ressources et N3-Dua (PC, M-, T-) tirées de ces réglages ; le mur lit GET /api/dua
  et envoie à POST /api/dua (champ piège, délai minimal, limite d'envois).

Ordre : après wire_evenements.py, avant wire_inbox.py et fix_inputs.py. Idempotent.
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


def engine_source():
    tree = ast.parse((ROOT / 'scripts' / 'wire_service_pages.py').read_text(encoding='utf-8'))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, 'id', '') == 'ENGINE' for t in node.targets):
            src = node.value.value
            break
    else:
        raise AssertionError('moteur introuvable dans wire_service_pages.py')
    src = rep(src, '<script id="sa-services-x">', '<script id="sa-res-x">')
    src = rep(src, "aria-hidden=\"true\">' + (n + 1) + '</span>'", "aria-hidden=\"true\">' + (n + 1 + (tab.n0 || 0)) + '</span>'")
    assert '__saServices' in src
    return src.replace('__saServices', '__saRes')


def T(p, l, **k): return dict(t='text', p=p, l=l, **k)
def A(p, l, **k): return dict(t='area', p=p, l=l, wide=True, **k)
def SW(p, l, **k): return dict(t='sw', p=p, l=l, **k)
def SEL(p, l, o, **k): return dict(t='select', p=p, l=l, o=o, **k)
def NUM(p, l, **k): return dict(t='num', p=p, l=l, **k)


LINK_ITEM = [T('titre', 'Titre', max=100, wide=True), T('texte', 'Description', max=200, wide=True),
             T('lien', 'Lien (adresse complète)', max=300, wide=True, ph='https://', hint='Vide : la carte s’affiche sans lien.')]
LINK_NEW = {'titre': '', 'texte': '', 'lien': '', 'on': True}

TABS = [
    dict(key='ressources', sections=[
        dict(title='En-tête de la page', f=[A('intro', 'Phrase d’accueil', max=300)]),
        dict(title='Manger halal', sw='halal.on', f=[
            T('halal.titre', 'Titre', max=80), A('halal.texte', 'Texte', max=400),
            dict(t='list', p='halal.items', add='+ Ajouter un commerce', title='nom', empty='Nouveau commerce', max=12,
                 none='Aucun commerce : la section n’est pas affichée.',
                 item=[T('nom', 'Nom', max=80, wide=True), T('adresse', 'Adresse', max=160), T('telephone', 'Téléphone', max=30),
                       SEL('certif', 'Certification', [['confirmer', 'À vérifier auprès du restaurant'], ['certifie', 'Certifié (organisme indiqué)'], ['non', 'Non certifié']]),
                       T('organisme', 'Organisme de certification', max=80, hint='Affiché quand le commerce est certifié.')],
                 d={'nom': '', 'adresse': '', 'telephone': '', 'certif': 'confirmer', 'organisme': '', 'on': True}),
            SW('halal.avert', 'Avertissement « horaires approximatifs, à vérifier »'),
        ]),
        dict(title='Mosquées et centres voisins', sw='mosquees.on', f=[
            dict(t='list', p='mosquees.items', add='+ Ajouter un lieu', title='nom', empty='Nouveau lieu', max=12,
                 none='Aucun lieu : la section n’est pas affichée.',
                 item=[T('nom', 'Nom', max=100, wide=True), T('adresse', 'Adresse', max=160),
                       T('distance', 'Distance routière', max=30, ph='ex. 60 km', hint='Vide : la ligne n’est pas affichée.')],
                 d={'nom': '', 'adresse': '', 'distance': '', 'on': True}),
            SW('mosquees.copier', 'Bouton « Copier l’adresse »'), SW('mosquees.itineraire', 'Bouton « Itinéraire »'),
        ]),
        dict(title='Services publics', sw='publics.on', f=[
            dict(t='list', p='publics.items', add='+ Ajouter un service', title='titre', empty='Nouveau service', max=12,
                 none='Aucun service : la colonne n’est pas affichée.', item=LINK_ITEM, d=LINK_NEW),
        ]),
        dict(title='Repères personnels', sw='reperes.on', f=[
            dict(t='list', p='reperes.items', add='+ Ajouter un repère', title='titre', empty='Nouveau repère', max=8,
                 none='Aucun repère : la colonne n’est pas affichée.', item=LINK_ITEM, d=LINK_NEW),
        ]),
        dict(title='Pour bien s’installer', sw='installer.on', desc='Cartes vers les pages de la communauté. Une carte vers une page masquée n’apparaît pas.', f=[
            SW('installer.aide', 'Aide alimentaire'), SW('installer.cours', 'Cours pour les enfants'), SW('installer.dua', 'Dua et annonces'),
        ]),
        dict(title='Étudier et scolariser', sw='etudier.on', f=[T('etudier.titre', 'Titre', max=80), A('etudier.texte', 'Texte', max=600)]),
    ]),
    dict(key='dua', n0=2, sections=[
        dict(title='Règles du mur', f=[
            NUM('max', 'Longueur max. d’un message', hint='Entre 80 et 1000 caractères.'),
            SEL('delai', 'Délai de relecture annoncé', [['12 h', '12 h'], ['24 h', '24 h'], ['48 h', '48 h']]),
            dict(t='list', p='categories', add='+ Ajouter une catégorie', title='titre', empty='Nouvelle catégorie', max=10,
                 none='Aucune catégorie : les annonces sont envoyées sans catégorie.', item=[T('titre', 'Catégorie', max=30, wide=True)], d={'titre': '', 'on': True}),
            SW('ongletDua', 'Onglet « Demandes de dua »'), SW('ongletAnn', 'Onglet « Annonces »'),
            SW('compteur', 'Compteur « J’ai fait une dua »'), SW('anonyme', 'Signature « Anonyme » permise'),
            SW('pause', 'Mettre le mur en pause', hint='Plus aucun envoi possible. Les messages publiés restent visibles.'),
        ]),
        dict(title='Règles affichées aux visiteurs', desc='Sous le formulaire. La première ligne (délai de relecture) est ajoutée automatiquement.', f=[
            dict(t='list', p='regles', add='+ Ajouter une règle', title='titre', empty='Nouvelle règle', max=8,
                 none='Aucune règle en plus du délai de relecture.', item=[T('titre', 'Règle', max=160, wide=True)], d={'titre': '', 'on': True}),
        ]),
    ]),
]

PUB = {'pub_ressources': 'pg_ressources', 'pub_dua': 'pg_dua'}

COMPONENT_SCRIPT = r"""class Component extends DCLogic {
  constructor(props) {
    super(props);
    this.base = __BASE__;
    this.pubKeys = ['pub_ressources', 'pub_dua'];
    this.state = { on: Object.assign({}, this.base), extDirty: false, toast: '' };
    window.__saRes = this;
  }
  componentDidMount() {
    window.dispatchEvent(new Event('sa-res-ready'));
  }
  componentWillUnmount() {
    clearTimeout(this.tt);
    if (window.__saRes === this) window.__saRes = null;
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
      save: () => { if (window.__saResSave) window.__saResSave(); },
      undo: () => { if (window.__saResUndo) window.__saResUndo(); },
      toast: this.state.toast
    };
  }
}"""

SYNC_SCRIPT = r'''<script id="sa-res-sync">
(function () {
  var PUB = __PUB__;
  var pagesBase = null, saving = false, started = false, msgs = { pending: [], published: [] }, editing = 0, cats = [];

  function comp() { return window.__saRes; }
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

  // ---------- Modération du mur ----------
  function ago(iso) {
    var t = Date.parse(iso || '');
    if (!isFinite(t)) return '';
    var m = Math.round((Date.now() - t) / 60000);
    if (m < 2) return 'à l’instant';
    if (m < 60) return 'il y a ' + m + ' min';
    var h = Math.round(m / 60);
    if (h < 24) return 'il y a ' + h + ' h';
    var d = Math.round(h / 24);
    return d === 1 ? 'hier' : 'il y a ' + d + ' jours';
  }
  var BTN = 'min-height:40px';
  function item(m, pending) {
    var type = m.type === 'ann' ? 'Annonce' + (m.categorie ? ' · ' + m.categorie : '') : 'Dua';
    var h = ['<li data-dua="' + m.id + '" style="border:1px solid ' + (m.signale ? '#B3261E' : '#E4D9C0') + ';border-radius:14px;background:#fff;padding:14px;display:flex;flex-direction:column;gap:10px">',
      '<div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap"><span class="tag" style="background:#F6E7C4;color:#0E4D3C">' + esc(type) + '</span>',
      m.signale ? '<span class="tag" style="background:#FDEBEB;color:#B3261E">Signalé par un visiteur</span>' : '',
      '<span style="font-size:13px;color:#4F5E57">Signé « ' + esc(m.signature) + ' » · ' + esc(ago(pending ? m.created_at : m.published_at)) + '</span>',
      !pending && m.type === 'dua' ? '<span style="font-size:13px;color:#4F5E57" class="tnum">· ' + (m.amin || 0) + ' dua faite(s)</span>' : '', '</div>'];
    if (editing === m.id) {
      h.push('<div class="fld"><label class="lbl" for="dua-e-t-' + m.id + '">Message</label><textarea class="in" rows="3" id="dua-e-t-' + m.id + '" maxlength="1000">' + esc(m.texte) + '</textarea></div>',
        '<div class="g2"><div class="fld"><label class="lbl" for="dua-e-s-' + m.id + '">Signature</label><input class="in" type="text" id="dua-e-s-' + m.id + '" maxlength="60" value="' + esc(m.signature) + '"></div>');
      if (m.type === 'ann') {
        var opts = cats.indexOf(m.categorie || '') < 0 && m.categorie ? [m.categorie].concat(cats) : cats;
        h.push('<div class="fld"><label class="lbl" for="dua-e-c-' + m.id + '">Catégorie</label><select class="in" id="dua-e-c-' + m.id + '"><option value="">Sans catégorie</option>' +
          opts.map(function (c) { return '<option' + (c === m.categorie ? ' selected' : '') + '>' + esc(c) + '</option>'; }).join('') + '</select></div>');
      }
      h.push('</div><div style="display:flex;gap:8px;flex-wrap:wrap"><button type="button" class="btn btn-green" data-dua-act="enregistrer" style="' + BTN + '">Enregistrer la correction</button>',
        '<button type="button" class="btn btn-line" data-dua-act="fermer" style="' + BTN + '">Annuler</button></div></li>');
      return h.join('');
    }
    h.push('<p style="margin:0;white-space:pre-line;overflow-wrap:anywhere">' + esc(m.texte) + '</p><div style="display:flex;gap:8px;flex-wrap:wrap">');
    if (pending) {
      h.push('<button type="button" class="btn btn-green" data-dua-act="publier" style="' + BTN + '">' + (m.signale ? 'Remettre sur le mur' : 'Publier') + '</button>',
        '<button type="button" class="btn btn-line" data-dua-act="modifier" style="' + BTN + '">Modifier</button>',
        '<button type="button" class="btn btn-line" data-dua-act="refuser" style="' + BTN + ';color:#B3261E;border-color:#B3261E">' + (m.signale ? 'Retirer du mur' : 'Refuser') + '</button>');
    } else {
      h.push('<button type="button" class="btn btn-line" data-dua-act="modifier" style="' + BTN + '">Modifier</button>',
        '<button type="button" class="btn btn-line" data-dua-act="retirer" style="' + BTN + ';color:#B3261E;border-color:#B3261E">Retirer du mur</button>');
    }
    h.push('<button type="button" class="btn btn-line" data-dua-act="supprimer" style="' + BTN + ';color:#B3261E;border-color:#B3261E">Supprimer</button></div></li>');
    return h.join('');
  }
  function list(id, arr, pending, none) {
    var w = el(id);
    if (!w) return;
    w.innerHTML = arr.length ? '<ul style="list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:10px">' + arr.map(function (m) { return item(m, pending); }).join('') + '</ul>'
      : '<p class="hint" style="margin:0">' + none + '</p>';
  }
  function renderMod() {
    list('dua-wait', msgs.pending, true, 'Aucun message à valider. Les nouveaux messages du mur et les messages signalés arrivent ici.');
    list('dua-pub', msgs.published, false, 'Aucun message publié pour le moment.');
    var n = el('dua-wait-n');
    if (n) n.textContent = msgs.pending.length ? msgs.pending.length + ' message(s) en attente.' : '';
  }
  function modError(text) {
    ['dua-wait', 'dua-pub'].forEach(function (id) { var w = el(id); if (w) w.innerHTML = '<p style="margin:0;color:#4F5E57">' + esc(text) + '</p>'; });
  }
  function loadMod() {
    return api('/api/admin/dua').then(function (d) {
      if (!d || !d.ok) { modError((d && d.message) || 'Impossible de charger les messages du mur. Rechargez la page.'); return; }
      msgs = { pending: d.pending || [], published: d.published || [] };
      renderMod();
    }, function () { modError('Impossible de joindre le serveur. Rechargez la page.'); });
  }
  function find(id) { return msgs.pending.concat(msgs.published).filter(function (m) { return m.id === id; })[0]; }
  function onModClick(e) {
    var b = e.target.closest && e.target.closest('button[data-dua-act]');
    if (!b) return;
    var li = b.closest('li[data-dua]'), id = parseInt(li.getAttribute('data-dua'), 10), act = b.getAttribute('data-dua-act'), m = find(id);
    if (!m) return;
    if (act === 'modifier') { editing = id; renderMod(); var t = el('dua-e-t-' + id); if (t) t.focus(); return; }
    if (act === 'fermer') { editing = 0; renderMod(); return; }
    var req;
    if (act === 'supprimer') {
      if (!window.confirm('Supprimer définitivement ce message ? Il ne pourra pas être récupéré.')) return;
      req = api('/api/admin/dua?id=' + id, 'DELETE');
    } else if (act === 'enregistrer') {
      var g = function (p) { var x = el('dua-e-' + p + '-' + id); return x ? x.value : ''; };
      req = api('/api/admin/dua', 'PATCH', { id: id, action: 'modifier', texte: g('t'), signature: g('s'), categorie: g('c') });
    } else {
      if ((act === 'refuser' || act === 'retirer') && !window.confirm(act === 'refuser' && !m.signale ? 'Refuser ce message ? Il n’apparaîtra pas sur le mur.' : 'Retirer ce message du mur ?')) return;
      req = api('/api/admin/dua', 'PATCH', { id: id, action: act === 'refuser' && m.signale ? 'retirer' : act });
    }
    b.disabled = true; b.setAttribute('aria-busy', 'true');
    req.then(function (d) {
      if (!d || !d.ok) { b.disabled = false; b.removeAttribute('aria-busy'); flash((d && d.message) || 'L’action n’a pas pu être faite. Réessayez.'); return; }
      editing = 0;
      flash({ publier: 'Message publié sur le mur.', refuser: 'Message refusé.', retirer: 'Message retiré du mur.', supprimer: 'Message supprimé.', enregistrer: 'Correction enregistrée.' }[act]);
      loadMod();
    }, function () { b.disabled = false; b.removeAttribute('aria-busy'); flash('Impossible de joindre le serveur. Réessayez.'); });
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
    if (c) c.setExtDirty(!!(window.__svx && window.__svx.dirty()));
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
    if (!tasks.length) { flash('Aucun changement à enregistrer.'); return; }
    saving = true;
    flash('Enregistrement…');
    Promise.all(tasks).then(function (res) {
      saving = false;
      var failed = res.filter(function (r) { return !r || !r.ok; })[0];
      if (window.__svx) window.__svx.after();
      if (failed) { flash((failed && failed.message) || 'L’enregistrement a échoué. Vérifiez vos valeurs et réessayez.'); return; }
      var c = comp();
      if (c) c.commitKeys(Object.keys(PUB));
      setTimeout(checkDirty, 0);
      loadCats();
      flash('Ressources enregistrées. Le site est à jour.');
    }).catch(function () {
      saving = false;
      if (window.__svx) window.__svx.after();
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
  window.__saResSave = saveAll;
  window.__saResUndo = undoAll;

  function loadCats() {
    return api('/api/admin/settings/dua').then(function (r) {
      if (r && r.ok && r.settings) cats = (r.settings.categories || []).filter(function (c) { return c.on && c.titre; }).map(function (c) { return c.titre; });
    }, function () {});
  }
  function start() {
    if (started) return;
    started = true;
    document.addEventListener('click', onModClick);
    api('/api/admin/settings/pages').then(function (r) {
      if (!(r && r.ok && r.settings)) return;
      pagesBase = r.settings;
      var sw = {};
      Object.keys(PUB).forEach(function (k) { sw[k] = pagesBase[PUB[k]] !== false; });
      var c = comp();
      if (c) c.setSwitches(sw, true);
    }, function () {});
    loadCats().then(loadMod);
  }
  if (comp()) start();
  else window.addEventListener('sa-res-ready', start, { once: true });
})();
</script>
'''

BOX = '<div id="svx-{k}" style="display:flex;flex-direction:column;gap:18px"><p class="hint" style="margin:0">Chargement des réglages…</p></div>'

MOD = ('<section class="card" aria-label="À valider"><div class="card-h"><span class="num" aria-hidden="true">1</span><div><h3 class="ttl">À valider</h3>'
       '<p class="dsc">Chaque message est relu avant d’apparaître sur le mur. Un message signalé par un visiteur quitte le mur et revient ici. '
       '<span id="dua-wait-n" aria-live="polite"></span></p></div></div>'
       '<div class="card-b"><div id="dua-wait"><p class="hint" style="margin:0">Chargement des messages…</p></div></div></section>'
       '<section class="card" aria-label="Publiés sur le mur"><div class="card-h"><span class="num" aria-hidden="true">2</span><div><h3 class="ttl">Publiés sur le mur</h3>'
       '<p class="dsc">Les messages visibles sur la page Dua et annonces, du plus récent au plus ancien.</p></div></div>'
       '<div class="card-b"><div id="dua-pub"><p class="hint" style="margin:0">Chargement des messages…</p></div></div></section>')


def replace_sections(tpl, sp, end_marker, box):
    a = tpl.index(f'<div id="{sp}" class="sp">')
    b = tpl.index(end_marker, a) if end_marker else None
    body = tpl[a:b] if b else tpl[a:]
    h = body.index('<section')
    last = body.rindex('</section>') + len('</section>')
    return tpl[:a] + body[:h] + box + body[last:] + (tpl[b:] if b else '')


def wire_panel():
    path = ROOT / 'SA-Ressources.dc.html'
    s, i, j, tpl = load(path)
    if 'id="svx-ressources"' not in tpl:
        tpl = replace_sections(tpl, 'sp-0', '<div id="sp-1" class="sp">', BOX.format(k='ressources'))
        # Fin de l'onglet Dua : dernière section avant la fermeture du conteneur des onglets.
        a = tpl.index('<div id="sp-1" class="sp">')
        b = tpl.index('</section></div>', tpl.rindex('aria-label="Règles du mur"') if 'aria-label="Règles du mur"' in tpl else a) + len('</section>')
        body = tpl[a:b]
        h = body.index('<section')
        tpl = tpl[:a] + body[:h] + MOD + BOX.format(k='dua') + tpl[b:]
        tpl = rep(tpl, '<p class="warn">Petite app : elle fonctionne dans le navigateur des visiteurs, sans compte. Publiez-la seulement quand les données sont prêtes.</p>', '')
    pre = tpl.split('class Component')[0]
    assert 'Fatima' not in pre and 'Méditerranéen' not in pre, 'contenu de maquette restant'

    m = re.search(r'this\.base = (\{.*?\});', tpl)
    assert m, 'base du composant introuvable'
    old = json.loads(m.group(1))
    base = {k: v for k, v in old.items() if k in PUB}
    assert set(base) == set(PUB), base
    comp = COMPONENT_SCRIPT.replace('__BASE__', json.dumps(base))
    tpl, n = re.subn(r'class Component extends DCLogic \{.*?\n\}', lambda _: comp, tpl, count=1, flags=re.S)
    assert n == 1
    tpl = re.sub(r'<script id="(?:sa-res-x|sa-res-sync)">.*?</script>\s*', '', tpl, flags=re.S)
    engine = engine_source().replace('__TABS__', json.dumps(TABS, ensure_ascii=False))
    sync = SYNC_SCRIPT.replace('__PUB__', json.dumps(PUB))
    k = tpl.rindex('</body>')
    tpl = tpl[:k] + engine + sync + tpl[k:]
    save(path, s, i, j, tpl)
    print('SA-Ressources.dc.html : Nouveaux arrivants et Dua et annonces reliés (clés ressources, dua, pages ; table dua_messages)')


# =====================================================================================
# Page Ressources publique
# =====================================================================================

RES_JS = r"""
    /*ascil-ressources*/
    const PT = (typeof window !== 'undefined' && window.__ascilPrayer) || {};
    const R = PT.ressources || __RES__;
    const on = (x) => x && x.on;
    const H = R.halal || {}, M = R.mosquees || {}, P = R.publics || {}, Q = R.reperes || {}, I = R.installer || {}, E = R.etudier || {};
    const CERT = { confirmer: 'Certification halal : à vérifier auprès du restaurant', certifie: 'Certifié halal', non: 'Non certifié halal' };
    const halal = (H.items || []).filter((x) => x.on && x.nom).map((x) => ({
      nom: x.nom, adresse: x.adresse || '', hasAdr: !!x.adresse, tel: x.telephone || '', hasTel: !!x.telephone,
      telHref: 'tel:' + String(x.telephone || '').replace(/[^\d+]/g, ''),
      certif: x.certif === 'certifie' && x.organisme ? 'Certifié halal par ' + x.organisme : CERT[x.certif] || CERT.confirmer,
    }));
    const cpk = this.state.cpk;
    const mosq = (M.items || []).filter((x) => x.on && x.nom).map((x, i) => ({
      nom: x.nom, adresse: x.adresse || '', hasAdr: !!x.adresse, distance: x.distance || '', hasDist: !!x.distance,
      map: 'https://maps.google.com/?q=' + encodeURIComponent(x.adresse || x.nom),
      ncp: cpk !== 'm' + i, cpd: cpk === 'm' + i,
      copy: () => {
        try { navigator.clipboard && navigator.clipboard.writeText(x.adresse || x.nom); } catch (e) {}
        this.setState({ cpk: 'm' + i }); clearTimeout(this.cpt); this.cpt = setTimeout(() => this.setState({ cpk: '' }), 2000);
      },
    }));
    const links = (L) => (L.items || []).filter((x) => x.on && x.titre).map((x) => ({ titre: x.titre, texte: x.texte || '', hasTexte: !!x.texte, lien: x.lien || '', hasLien: !!x.lien, noLien: !x.lien }));
    const pubs = links(P), reps = links(Q);
    const showPub = on(P) && pubs.length > 0, showRep = on(Q) && reps.length > 0;
    return {
      resIntro: R.intro || '', hasIntro: !!R.intro,
      showHalal: on(H) && halal.length > 0, halTitre: H.titre || 'À Edmundston', halTexte: H.texte || '', hasHalTexte: !!H.texte, halal, halAvert: !!H.avert,
      showMosq: on(M) && mosq.length > 0, mosq, showCopy: !!M.copier, showIti: !!M.itineraire,
      showIn: showPub || showRep, showPub, showRep, pubs, reps, inCols: showPub && showRep ? 'g2' : '',
      showInst: on(I) && (I.aide || I.cours || I.dua), iAide: !!I.aide, iCours: !!I.cours, iDua: !!I.dua,
      showEt: on(E) && !!(E.titre || E.texte), etTitre: E.titre || '', etTexte: E.texte || '', hasEtTexte: !!E.texte,
    };"""

# Pas de str.format() ici : il transformait {{x.texte}} en {x.texte}, affiché tel quel sur la page.
LINK_CARD_IN = ('<span style="color:#0E4D3C">@ICON@</span><span style="min-width:0"><span style="display:block;font-weight:700;overflow-wrap:anywhere">{{x.titre}}</span>'
                + sc_if('x.hasTexte', '<span class="muted" style="display:block;margin-top:4px;font-size:15px">{{x.texte}}</span>')
                + '@PILL@</span>')


def link_cards(var, icon):
    pill = '<span class="pill" style="background:#F3EAD8;color:#7A5A1E;margin-top:10px">Lien externe</span>'
    inner_a = LINK_CARD_IN.replace('@ICON@', icon).replace('@PILL@', pill)
    inner_d = LINK_CARD_IN.replace('@ICON@', icon).replace('@PILL@', '')
    return (f'<sc-for list="{{{{{var}}}}}" as="x" hint-placeholder-count="2">'
            + sc_if('x.hasLien', '<a class="card" href="{{x.lien}}" target="_blank" rel="noopener" style="display:flex;gap:14px;align-items:flex-start">' + inner_a + '</a>')
            + sc_if('x.noLien', '<div class="card" style="display:flex;gap:14px;align-items:flex-start">' + inner_d + '</div>', 'false')
            + '</sc-for>')


def patch_ressources(tpl):
    a = tpl.index('<main'); b = tpl.index('</main>')
    m = tpl[a:b]
    m = resub(m, r'(<p class="lead"[^>]*>)Pour la première semaine d’une famille, d’un étudiant ou d’un travailleur qui s’installe dans la région\.</p>',
              lambda x: sc_if('hasIntro', x.group(1) + '{{resIntro}}</p>'))
    # ---------- Manger halal ----------
    sa, sb = section_span(m, '<section class="sec" aria-labelledby="hal-t">')
    sec = m[sa:sb]
    sec = rep(sec, '>À Edmundston</h2>', '>{{halTitre}}</h2>')
    sec = resub(sec, r'(<p class="muted"[^>]*>)Un seul établissement est indiqué.*?</p>', lambda x: sc_if('hasHalTexte', x.group(1) + '{{halTexte}}</p>'))
    ca = sec.index('<div class="card">')
    cb = sec.index('</div>', ca) + len('</div>')
    card = sec[ca:cb]
    pin = re.search(r'(<svg(?:(?!</svg>).)*</svg>)298 boul', card, re.S).group(1)
    new = ('<div style="display:flex;flex-direction:column;gap:16px;min-width:0"><sc-for list="{{halal}}" as="h" hint-placeholder-count="1"><div class="card">'
           '<p class="h3" style="overflow-wrap:anywhere">{{h.nom}}</p>'
           + sc_if('h.hasAdr', '<p style="margin:10px 0 0;display:flex;gap:8px">' + pin + '<span>{{h.adresse}}</span></p>')
           + sc_if('h.hasTel', '<p style="margin:6px 0 0"><a class="link" href="{{h.telHref}}">{{h.tel}}</a></p>', 'false')
           + sc_if('halAvert', '<p class="muted" style="margin:14px 0 0;font-size:15px">Horaires approximatifs : vérifiez avant de vous déplacer.</p>')
           + '<p class="muted" style="margin:8px 0 0;font-size:15px">{{h.certif}}</p></div></sc-for></div>')
    sec = sec[:ca] + new + sec[cb:]
    m = m[:sa] + sc_if('showHalal', sec) + m[sb:]
    # ---------- Mosquées ----------
    sa, sb = section_span(m, '<section class="sand" aria-labelledby="mq-t"')
    sec = m[sa:sb]
    ga = sec.index('<div class="g2" style="margin-top:28px">') + len('<div class="g2" style="margin-top:28px">')
    ge = sec.rindex('</div>\n </div>\n</section>')
    g = sec[ga:ge]
    pin = re.search(r'(<svg(?:(?!</svg>).)*</svg>)<span>502-A', g, re.S).group(1)
    icon_copy = re.search(r'<sc-if value="\{\{nc\.poc\}\}"[^>]*>(<svg(?:(?!</svg>).)*</svg>)Copier', g, re.S).group(1)
    icon_ok = re.search(r'<span class="pop" style="display:inline-flex">(<svg(?:(?!</svg>).)*</svg>)</span>Copiée', g, re.S).group(1)
    icon_map = re.search(r'Painchaud,\+La\+Pocatière"[^>]*>(<svg(?:(?!</svg>).)*</svg>)Itinéraire', g, re.S).group(1)
    st = 'min-height:44px;padding:0 14px;font-size:14px'
    card = ('<sc-for list="{{mosq}}" as="q" hint-placeholder-count="4"><div class="card"><p class="h3" style="font-size:19px;overflow-wrap:anywhere">{{q.nom}}</p>'
            + sc_if('q.hasAdr', '<p style="margin:8px 0 0;display:flex;gap:8px">' + pin + '<span>{{q.adresse}}</span></p>')
            + '<div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:14px">'
            + sc_if('showCopy', f'<button type="button" class="btn btn-ghost" sc-camel-on-click="{{{{q.copy}}}}" style="{st}" aria-live="polite">'
                    + sc_if('q.ncp', icon_copy + 'Copier l’adresse') + sc_if('q.cpd', '<span class="pop" style="display:inline-flex">' + icon_ok + '</span>Copiée', 'false') + '</button>')
            + sc_if('showIti', f'<a class="btn btn-ghost" href="{{{{q.map}}}}" target="_blank" rel="noopener" style="{st}">' + icon_map + 'Itinéraire</a>')
            + '</div>' + sc_if('q.hasDist', '<p class="muted" style="margin:12px 0 0;font-size:14px">Distance routière : {{q.distance}}</p>', 'false')
            + '</div></sc-for>')
    sec = sec[:ga] + card + sec[ge:]
    m = m[:sa] + sc_if('showMosq', sec) + m[sb:]
    # ---------- Services publics et repères ----------
    sa, sb = section_span(m, '<section class="sec" aria-labelledby="in-t">')
    sec = m[sa:sb]
    icon_pub = re.search(r'<a class="card" href="#"[^>]*><span style="color:#0E4D3C">(<svg(?:(?!</svg>).)*</svg>)</span><span><span[^>]*>Accueil et Intégration', sec, re.S).group(1)
    icon_rep = re.search(r'<a class="card" href="#"[^>]*><span style="color:#0E4D3C">(<svg(?:(?!</svg>).)*</svg>)</span><span><span[^>]*>Horaires astronomiques', sec, re.S).group(1)
    sec = rep(sec, '<div class="g2">', '<div class="{{inCols}}">')
    cols = re.findall(r'<div style="display:flex;flex-direction:column;gap:16px;margin-top:20px">.*?</a></div>', sec, re.S)
    assert len(cols) == 2, len(cols)
    sec = sec.replace(cols[0], '<div style="display:flex;flex-direction:column;gap:16px;margin-top:20px">' + link_cards('pubs', icon_pub) + '</div>', 1)
    sec = sec.replace(cols[1], '<div style="display:flex;flex-direction:column;gap:16px;margin-top:20px">' + link_cards('reps', icon_rep) + '</div>', 1)
    sec = resub(sec, r'(   <div>\n    <p class="eyebrow">S’installer et s’intégrer</p>.*?</div>\n   </div>)\n(   <div>\n    <p class="eyebrow">Outils du fidèle</p>.*?</div>\n   </div>)\n',
                lambda x: sc_if('showPub', x.group(1)) + '\n' + sc_if('showRep', x.group(2)) + '\n')
    m = m[:sa] + sc_if('showIn', sec) + m[sb:]
    # ---------- Pour bien s'installer ----------
    sa = m.index('<section class="" style=""><div class="wrap sec"><p class="eyebrow">Communauté</p>')
    sb = m.index('</section>', sa) + len('</section>')
    sec = m[sa:sb]
    for name, page in (('iAide', 'N2-AideAlimentaire'), ('iCours', 'N2-Cours'), ('iDua', 'N3-Dua')):
        sec = resub(sec, r'(<a class="card" href="(?:[MT]-)?' + page + r'\.dc\.html".*?</a>)', lambda x, n=name: sc_if(n, x.group(1)))
    m = m[:sa] + sc_if('showInst', sec) + m[sb:]
    # ---------- Étudier ----------
    sa, sb = section_span(m, '<section style="padding-bottom:80px" aria-labelledby="et-t">')
    sec = m[sa:sb]
    sec = rep(sec, '>Étudier et scolariser</h2>', '>{{etTitre}}</h2>')
    sec = resub(sec, r'(<p style="margin:8px 0 0">)Aucune école islamique.*?</p>', lambda x: sc_if('hasEtTexte', x.group(1) + '{{etTexte}}</p>'))
    m = m[:sa] + sc_if('showEt', sec) + m[sb:]
    assert 'href="#" style' not in m and 'validation locale' not in m and 'Méditerranéen' not in m
    return tpl[:a] + m + tpl[b:]


# =====================================================================================
# Mur Dua et annonces
# =====================================================================================

DUA_JS = r"""
    /*ascil-dua*/
    const PT = (typeof window !== 'undefined' && window.__ascilPrayer) || {};
    const W = PT.dua || {};
    const RU = W.rules || __DUA__;
    const st = this.state, v = this.v;
    if (!this.dt0) this.dt0 = Date.now();
    if (!this.amSeen) { this.amSeen = {}; try { this.amSeen = JSON.parse(localStorage.getItem('ascil-dua-amin') || '{}') || {}; } catch (e) {} }
    const tabs = [RU.ongletDua !== false ? 'dua' : '', RU.ongletAnn !== false ? 'ann' : ''].filter(Boolean);
    const wall = tabs.indexOf(st.wall) > -1 ? st.wall : tabs[0] || 'dua';
    const ftype = tabs.indexOf(st.ftype) > -1 ? st.ftype : tabs[0] || 'dua';
    const cats = (RU.categories || []).filter((c) => c.on && c.titre).map((c) => ({ t: c.titre }));
    const max = RU.max || 280;
    const ago = (iso) => {
      const t = Date.parse(iso || ''); if (!isFinite(t)) return '';
      const m = Math.round((Date.now() - t) / 60000);
      if (m < 60) return m < 2 ? 'à l’instant' : 'il y a ' + m + ' min';
      const h = Math.round(m / 60); if (h < 24) return 'il y a ' + h + ' h';
      const d = Math.round(h / 24); return d === 1 ? 'hier' : 'il y a ' + d + ' jours';
    };
    const post = (body) => fetch('/api/dua', { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
      .then((r) => r.json().catch(() => ({ ok: false })), () => ({ ok: false, message: 'Impossible de joindre le site. Vérifiez votre connexion et réessayez.' }));
    const rl = (id) => (st.rep[id] ? 'Signalé, merci' : 'Signaler');
    const report = (id) => () => {
      if (st.rep[id]) return;
      post({ action: 'report', id }).then((d) => { if (d && d.ok) this.setState({ rep: Object.assign({}, this.state.rep, { [id]: true }) }); });
    };
    const amc = st.amc || {};
    const duas = (W.duas || []).map((d) => {
      const done = !!this.amSeen[d.id];
      return { text: d.texte, by: d.signature, when: ago(d.published_at), count: amc[d.id] !== undefined ? amc[d.id] : d.amin, pressed: String(done),
        bg: done ? '#0E4D3C' : '#fff', fg: done ? '#fff' : '#0E4D3C',
        amin: () => {
          if (this.amSeen[d.id]) return;
          this.amSeen[d.id] = 1;
          try { localStorage.setItem('ascil-dua-amin', JSON.stringify(this.amSeen)); } catch (e) {}
          this.setState({ amc: Object.assign({}, this.state.amc, { [d.id]: (d.amin || 0) + 1 }) });
          post({ action: 'amin', id: d.id }).then((r) => { if (r && r.ok) this.setState({ amc: Object.assign({}, this.state.amc, { [d.id]: r.amin }) }); });
        },
        report: report(d.id), repLab: rl(d.id) };
    }).filter((d, i) => !st.rep[(W.duas || [])[i].id]);
    const anns = (W.anns || []).filter((a) => !st.rep[a.id]).map((a) => ({ cat: a.categorie || 'Annonce', text: a.texte, by: a.signature, when: ago(a.published_at),
      mail: 'mailto:?subject=' + encodeURIComponent('Réponse à une annonce du mur : ' + String(a.texte).slice(0, 60)),
      report: report(a.id), repLab: rl(a.id) }));
    const send = () => {
      if (st.dBusy) return;
      const g = (id) => { const e = document.getElementById(id); return e ? String(e.value) : ''; };
      const texte = (v.dt || '').trim(), by = (v.db || '').trim();
      if (texte.length < 5) return this.setState({ dErr: 'Écrivez votre message (5 caractères minimum).', dSent: false });
      if (!by && RU.anonyme === false) return this.setState({ dErr: 'Signez votre message avec votre prénom ou vos initiales.', dSent: false });
      if (ftype === 'ann' && cats.length && !v.dc) return this.setState({ dErr: 'Choisissez une catégorie pour votre annonce.', dSent: false });
      if (!v.dok) return this.setState({ dErr: 'Cochez la case de relecture.', dSent: false });
      this.setState({ dErr: '', dBusy: true });
      post({ action: 'send', type: ftype, categorie: v.dc || '', texte, signature: by, ok: true, hp: g('d-site'), t: Date.now() - this.dt0 }).then((d) => {
        if (d && d.ok) {
          this.setState({ dBusy: false, dSent: true, dOkMsg: d.message || 'Merci. Votre message apparaîtra sur le mur après relecture.', wall: ftype,
            mineL: [{ type: ftype, text: texte, by: by || 'Anonyme' }].concat(this.state.mineL) });
          ['d1', 'd2'].forEach((id) => { const e = document.getElementById(id); if (e) e.value = ''; });
          v.dt = ''; v.db = ''; this.setState({ dLen: 0 });
        } else this.setState({ dBusy: false, dSent: false, dErr: (d && d.message) || 'Votre message n’a pas pu être envoyé. Réessayez dans un instant.' });
      });
    };
    const loaded = !!PT.dua;
    return {
      bothTabs: tabs.length > 1,
      isDua: wall === 'dua', isAnn: wall === 'ann', tDuaP: String(wall === 'dua'), tAnnP: String(wall === 'ann'),
      tDua: () => this.setState({ wall: 'dua' }), tAnn: () => this.setState({ wall: 'ann' }),
      duas, anns, showCount: RU.compteur !== false,
      duaEmpty: loaded && wall === 'dua' && duas.length === 0, annEmpty: loaded && wall === 'ann' && anns.length === 0, wallLoading: !loaded,
      mine: st.mineL.filter((m) => m.type === wall),
      paused: !!RU.pause, open: !RU.pause,
      fDuaP: String(ftype === 'dua'), fAnnP: String(ftype === 'ann'), fDua: () => this.setState({ ftype: 'dua', dErr: '' }), fAnn: () => this.setState({ ftype: 'ann', dErr: '' }),
      isFAnn: ftype === 'ann' && cats.length > 0, cats, dCat: (e) => { v.dc = e.target.value; },
      dText: (e) => { v.dt = e.target.value; this.setState({ dLen: e.target.value.length }); }, dBy: (e) => { v.db = e.target.value; },
      dOk: (e) => { v.dok = e.target.checked; }, dLen: st.dLen, dMax: max, dErr: !!st.dErr, dErrTxt: st.dErr, dBd: st.dErr ? '#B3261E' : '#CDBF9C', dSent: st.dSent,
      dOkMsg: st.dOkMsg || '', dSend: send, dSendLbl: st.dBusy ? 'Envoi en cours…' : 'Envoyer pour validation', dBusy: String(!!st.dBusy),
      sigHint: RU.anonyme === false ? '(prénom ou initiales)' : '(prénom, initiales ou « Anonyme »)',
      delai: RU.delai || '24 h', regles: (RU.regles || []).filter((r) => r.on && r.titre).map((r) => ({ t: r.titre })),
    };"""

HONEYPOT = ('<div style="position:relative"><div aria-hidden="true" style="position:absolute;left:-10000px;top:auto;width:1px;height:1px;overflow:hidden">'
            '<label for="d-site">Site web (laisser vide)</label><input id="d-site" type="text" tabindex="-1" autocomplete="off"></div></div>')


def patch_dua(tpl):
    a = tpl.index('<main'); b = tpl.index('</main>')
    m = tpl[a:b]
    m = resub(m, r'<div class="flag" role="note".*?</p></div>', '')
    m = resub(m, r'(<div class="seg" role="group" aria-label="Choisir le mur">.*?</div>)', lambda x: sc_if('bothTabs', x.group(1)))
    m = rep(m, '<span class="muted">— {{d.by}} <span class="ex">[EXEMPLE À MODIFIER]</span></span>', '<span class="muted">— {{d.by}} · {{d.when}}</span>')
    m = rep(m, '<span class="muted">— {{a.by}} <span class="ex">[EXEMPLE À MODIFIER]</span></span>', '<span class="muted">— {{a.by}} · {{a.when}}</span>')
    m = resub(m, r'(<button type="button" class="chip" sc-camel-on-click="\{\{d\.amin\}\}".*?</button>)', lambda x: sc_if('showCount', x.group(1)))
    m = rep(m, '<p style="margin:0;font-size:18px">{{d.text}}</p>', '<p style="margin:0;font-size:18px;white-space:pre-line;overflow-wrap:anywhere">{{d.text}}</p>')
    m = rep(m, '<p style="margin:10px 0 0;font-size:18px">{{a.text}}</p>', '<p style="margin:10px 0 0;font-size:18px;white-space:pre-line;overflow-wrap:anywhere">{{a.text}}</p>')
    m = rep(m, '<a class="btn btn-ghost" href="mailto:"', '<a class="btn btn-ghost" href="{{a.mail}}"')
    empty = ('<div class="card sand" style="text-align:center"><p style="margin:0;font-weight:700">{t}</p></div>')
    m = rep(m, '    <sc-if value="{{isDua}}" hint-placeholder-val="{{ true }}">',
            '    ' + sc_if('wallLoading', '<p class="muted" style="margin:0">Chargement du mur…</p>', 'false')
            + sc_if('duaEmpty', empty.format(t='Aucune demande de dua publiée pour le moment. Écrivez la vôtre avec le formulaire.'), 'false')
            + sc_if('annEmpty', empty.format(t='Aucune annonce publiée pour le moment. Partagez la vôtre avec le formulaire.'), 'false')
            + '\n    <sc-if value="{{isDua}}" hint-placeholder-val="{{ true }}">')
    # ---------- Formulaire ----------
    fa = m.index('<div class="card" style="padding:28px;border:2px solid #0E4D3C">')
    fb = m.index('<div class="card sand"><p class="eyebrow">Modération', fa)
    form = m[fa:fb]
    form = resub(form, r'(<div style="margin-top:14px"><div class="seg" role="group" aria-label="Type de message">.*?</div></div>)', lambda x: sc_if('bothTabs', x.group(1)))
    form = rep(form, 'maxlength="280"', 'maxlength="{{dMax}}"')
    form = rep(form, '{{dLen}} / 280', '{{dLen}} / {{dMax}}')
    form = rep(form, '(prénom, initiales ou « Anonyme »)', '{{sigHint}}')
    form = rep(form, '<input id="d2" type="text" sc-camel-on-input="{{dBy}}">', '<input id="d2" type="text" maxlength="60" sc-camel-on-input="{{dBy}}">' )
    form = rep(form, '<div class="field"><label for="d1">Votre message</label>',
               sc_if('isFAnn', '<div class="field"><label for="d3">Catégorie</label><select id="d3" sc-camel-on-change="{{dCat}}"><option value="">Choisir une catégorie</option>'
                     '<sc-for list="{{cats}}" as="c" hint-placeholder-count="4"><option value="{{c.t}}">{{c.t}}</option></sc-for></select></div>', 'false')
               + '<div class="field"><label for="d1">Votre message</label>')
    form = rep(form, '<button type="button" class="btn btn-green" sc-camel-on-click="{{dSend}}">Envoyer pour validation</button>',
               HONEYPOT + '<button type="button" class="btn btn-green" sc-camel-on-click="{{dSend}}" aria-busy="{{dBusy}}">{{dSendLbl}}</button>')
    form = rep(form, '<p class="pop" style="margin:0;font-weight:700;color:#0E4D3C">Merci ! Votre message apparaît sur le mur après validation.</p>',
               '<p class="pop" role="status" style="margin:0;font-weight:700;color:#0E4D3C">{{dOkMsg}}</p>')
    # Mur en pause : le formulaire laisse place à un avis.
    ia = form.index('<div style="display:flex;flex-direction:column;gap:14px;margin-top:16px">')
    ib = form.rindex('</div>\n   </div>')
    form = (form[:ia] + sc_if('paused', '<p style="margin:14px 0 0">Le mur est en pause : aucun nouveau message pour le moment. Revenez bientôt.</p>', 'false')
            + sc_if('open', form[ia:ib]) + form[ib:])
    m = m[:fa] + form + m[fb:]
    m = resub(m, r'<div class="card sand"><p class="eyebrow">Modération <span class="ex">\[EXEMPLE À MODIFIER\]</span></p><ul([^>]*)>.*?</ul></div>',
              lambda x: '<div class="card sand"><p class="eyebrow">Modération</p><ul' + x.group(1) + '><li>Chaque message est relu sous {{delai}} par l’association.</li>'
              '<sc-for list="{{regles}}" as="r" hint-placeholder-count="3"><li>{{r.t}}</li></sc-for></ul></div>')
    assert 'EXEMPLE' not in m and 'prototype' not in m
    return tpl[:a] + m + tpl[b:]


def set_xvals(tpl, body):
    la = tpl.index('<script type="text/x-dc"')
    lb = tpl.index('</script>', la)
    code = tpl[la:lb]
    new = '  xvals() {' + body + '\n  }\n'
    if '  xvals() {' in code:
        a = code.index('  xvals() {')
        b = code.index('\n  }\n', a) + len('\n  }\n')
        code = code[:a] + new + code[b:]
    else:
        a = code.index('  renderVals() {')
        code = code[:a] + new + '\n' + code[a:]
    return tpl[:la] + code + tpl[lb:]


def defaults():
    js = ("import('./functions/_lib/settings.js').then((m) => { const d = m.DEFAULT_SETTINGS; "
          "process.stdout.write(JSON.stringify({ ressources: d.ressources, dua: d.dua })); })")
    out = subprocess.run(['node', '--input-type=module', '-e', js], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def wire_public():
    d = defaults()
    for pre in ('', 'M-', 'T-'):
        path = ROOT / f'{pre}Ressources.dc.html'
        s, i, j, tpl = load(path)
        if '{{resIntro}}' not in tpl:
            tpl = patch_ressources(tpl)
        # Pages déjà branchées avec l'ancien gabarit : accolades simples affichées telles quelles.
        tpl = tpl.replace('{x.hasTexte}', '{{x.hasTexte}}').replace('{x.texte}', '{{x.texte}}').replace('{x.titre}', '{{x.titre}}')
        tpl = tpl.replace('{{{x.', '{{x.').replace('}}}', '}}')
        assert '{x.' not in tpl.replace('{{x.', ''), path.name
        tpl = set_xvals(tpl, RES_JS.replace('__RES__', json.dumps(d['ressources'], ensure_ascii=False)))
        save(path, s, i, j, tpl)
        path = ROOT / f'{pre}N3-Dua.dc.html'
        s, i, j, tpl = load(path)
        if '{{dMax}}' not in tpl:
            tpl = patch_dua(tpl)
        tpl = set_xvals(tpl, DUA_JS.replace('__DUA__', json.dumps(d['dua'], ensure_ascii=False)))
        save(path, s, i, j, tpl)
    print('Ressources et N3-Dua (PC, M-, T-) : nouveaux arrivants et mur Dua et annonces reliés')


if __name__ == '__main__':
    wire_panel()
    wire_public()
