"""Contact et page 404 (étape C).

- Panneau SA-Contact :
  - onglet « Page Contact » (clé contact) : carte et coordonnées GPS, code postal, lignes pratiques,
    étiquette de visite, bloc « Écrire à l'association », formulaire (sujets, longueur, page après envoi) ;
  - onglet « Page 404 » (clé p404) : titre, texte et raccourcis ; la page 404 est toujours en ligne ;
  - publication de la page Contact (clé pages). L'onglet « Demandes reçues » (wire_inbox.py) reste tel quel.
- Pages publiques Contact (PC, M-, T-) tirées de ces réglages et des coordonnées générales (home.general).
- Nouvelle page 404.html construite depuis la page Contact (même en-tête, menu et pied de page) :
  Cloudflare Pages la sert pour toute adresse inconnue.

Ordre : après wire_inbox.py (qui relie le formulaire Contact), avant fix_inputs.py. Idempotent.
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


SVG = r'(<svg(?:(?!</svg>).)*</svg>)'


def engine_source():
    tree = ast.parse((ROOT / 'scripts' / 'wire_service_pages.py').read_text(encoding='utf-8'))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, 'id', '') == 'ENGINE' for t in node.targets):
            src = node.value.value
            break
    else:
        raise AssertionError('moteur introuvable dans wire_service_pages.py')
    src = rep(src, '<script id="sa-services-x">', '<script id="sa-co-x">')
    assert '__saServices' in src
    return src.replace('__saServices', '__saCo')


def T(p, l, **k): return dict(t='text', p=p, l=l, **k)
def A(p, l, **k): return dict(t='area', p=p, l=l, wide=True, **k)
def SW(p, l, **k): return dict(t='sw', p=p, l=l, **k)
def SEL(p, l, o, **k): return dict(t='select', p=p, l=l, o=o, **k)
def NUM(p, l, **k): return dict(t='num', p=p, l=l, **k)
def NOTE(h): return dict(t='note', h=h)


PAGES = [['accueil', 'Accueil'], ['horaires', 'Horaires'], ['apropos', 'À propos'], ['services', 'Services'], ['dons', 'Faire un don'],
         ['evenements', 'Événements'], ['ressources', 'Ressources']]

TABS = [
    dict(key='contact', sections=[
        dict(title='Adresse et carte', desc='Adresse, ville, courriel et page Facebook viennent des coordonnées générales (Accueil).', f=[
            SW('carte', 'Carte et bouton « Ouvrir dans Google Maps »'),
            T('lat', 'Latitude', max=20, ph='47.3726047'), T('lng', 'Longitude', max=20, ph='-68.3247465'),
            T('codePostal', 'Code postal', max=10, ph='G5R 0A0', hint='Vide : la ligne n’est pas affichée.'),
            SW('lignes.stationnement.on', 'Ligne « Stationnement »'), T('lignes.stationnement.texte', 'Texte', max=120, wide=True),
            SW('lignes.fauteuil.on', 'Ligne « Accessible en fauteuil roulant »'), T('lignes.fauteuil.texte', 'Texte', max=120, wide=True),
            SW('lignes.ablutions.on', 'Ligne « Ablutions et toilettes »'), T('lignes.ablutions.texte', 'Texte', max=120, wide=True),
        ]),
        dict(title='Étiquette de visite', sw='etiquette.on', f=[
            T('etiquette.titre', 'Titre', max=120, wide=True),
            dict(t='list', p='etiquette.items', add='+ Ajouter un conseil', title='titre', empty='Nouveau conseil', max=8,
                 none='Aucun conseil : la section n’est pas affichée.',
                 item=[T('titre', 'Titre', max=60, wide=True), A('texte', 'Conseil', max=600)], d={'titre': '', 'texte': '', 'on': True}),
        ]),
        dict(title='Écrire à l’association', f=[
            SW('ecrire.copier', 'Bouton « Copier » le courriel'),
            SW('ecrire.facebook', 'Lien « Message rapide sur Facebook »', hint='Vers la page Facebook des coordonnées générales.'),
            SW('ecrire.demandes.on', 'Bloc « Demandes particulières »'),
            dict(t='list', p='ecrire.demandes.items', add='+ Ajouter une demande', title='texte', empty='Nouvelle demande', max=8,
                 none='Aucune demande : le bloc n’est pas affiché.',
                 item=[T('texte', 'Demande', max=120, wide=True),
                       SEL('lien', 'Lien', [['', 'Aucun lien'], ['mariages', 'Page : Mariages'], ['funerailles', 'Page : Funérailles'], ['dons', 'Page : Faire un don'],
                                            ['evenements', 'Page : Événements'], ['ressources', 'Page : Ressources'], ['services', 'Page : Services'], ['apropos', 'Page : À propos']]),
                       T('lienTexte', 'Texte du lien', max=60, ph='voir le parcours')],
                 d={'texte': '', 'lien': '', 'lienTexte': '', 'on': True}),
            T('ecrire.demandes.note', 'Phrase sous les demandes', max=200, wide=True),
        ]),
        dict(title='Formulaire', f=[
            dict(t='list', p='form.sujets', add='+ Ajouter un sujet', title='titre', empty='Nouveau sujet', max=10,
                 none='Aucun sujet : le menu « Sujet » n’est pas affiché.', item=[T('titre', 'Sujet', max=60, wide=True)], d={'titre': '', 'on': True}),
            NUM('form.max', 'Longueur max. du message', hint='Entre 200 et 3000 caractères. Vérifiée aussi à l’envoi.'),
            SEL('form.apres', 'Après l’envoi', [['message', 'Afficher le message de remerciement'], ['page', 'Aller vers une page du site'], ['mapage', 'Aller vers une de mes pages']]),
            SEL('form.page', 'Page du site', PAGES, hint='Utilisée avec « Aller vers une page du site ».'),
            T('form.mapage', 'Adresse d’une de mes pages', max=63, ph='/p/inscriptions-ramadan', hint='Visible dans Créer une page → Mes pages. Utilisée avec « Aller vers une de mes pages ».'),
            T('form.merciTitre', 'Titre du remerciement', max=60), T('form.merciTexte', 'Texte du remerciement', max=300, wide=True),
        ]),
    ]),
    dict(key='p404', sections=[
        dict(title='Texte de la page', desc='La page 404 s’affiche pour toute adresse qui n’existe pas. Elle reste toujours en ligne.', f=[
            T('titre', 'Titre', max=80, wide=True), A('texte', 'Texte', max=300),
        ]),
        dict(title='Raccourcis proposés', f=[
            SW('accueil', 'Retour à l’accueil'), SW('horaires', 'Horaires'), SW('trouver', 'Nous trouver (page Contact)'),
        ]),
    ]),
]

PUB = {'pub_contact': 'pg_contact'}

COMPONENT_SCRIPT = r"""class Component extends DCLogic {
  constructor(props) {
    super(props);
    this.base = __BASE__;
    this.pubKeys = ['pub_contact'];
    this.state = { on: Object.assign({}, this.base), extDirty: false, toast: '' };
    window.__saCo = this;
  }
  componentDidMount() {
    window.__saContactToast = (m) => this.flash(m);
    window.dispatchEvent(new Event('sa-co-ready'));
  }
  componentWillUnmount() {
    clearTimeout(this.tt);
    if (window.__saContactToast) window.__saContactToast = null;
    if (window.__saCo === this) window.__saCo = null;
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
      save: () => { if (window.__saCoSave) window.__saCoSave(); },
      undo: () => { if (window.__saCoUndo) window.__saCoUndo(); },
      toast: this.state.toast
    };
  }
}"""

SYNC_SCRIPT = r'''<script id="sa-co-sync">
(function () {
  var PUB = __PUB__;
  var pagesBase = null, saving = false, started = false;
  function comp() { return window.__saCo; }
  function flash(m) { var c = comp(); if (c) c.flash(m); }
  function api(url, method, body) {
    var o = { credentials: 'same-origin', method: method || 'GET' };
    if (body) { o.headers = { 'Content-Type': 'application/json' }; o.body = JSON.stringify(body); }
    return fetch(url, o).then(function (r) { return r.json().catch(function () { return { ok: false }; }); });
  }
  function swOn() { var c = comp(); return (c && c.state && c.state.on) || {}; }
  function pagesNext() {
    if (!pagesBase) return null;
    var on = swOn(), next = Object.assign({}, pagesBase);
    Object.keys(PUB).forEach(function (k) { next[PUB[k]] = !!on[k]; });
    return JSON.stringify(next) !== JSON.stringify(pagesBase) ? next : null;
  }
  function checkDirty() {
    var c = comp();
    if (c) c.setExtDirty(!!(window.__svx && window.__svx.dirty()));
  }
  window.__svCheckDirty = checkDirty;
  function val(id) { var e = document.getElementById(id); return e ? String(e.value).trim() : ''; }
  function saveAll() {
    if (saving) return;
    var coord = function (v, lim) { var n = Number(v.replace(/\s/g, '').replace(',', '.').replace(/[−–]/g, '-')); return v === '' || (isFinite(n) && Math.abs(n) <= lim); };
    if (!coord(val('x-contact-lat'), 90) || !coord(val('x-contact-lng'), 180)) {
      flash('Coordonnées illisibles. Écrivez par exemple 47.3726047 pour la latitude et -68.3247465 pour la longitude.');
      return;
    }
    var mp = val('x-contact-form-mapage');
    if (mp && !/^\/p\/[a-z0-9]+(?:-[a-z0-9]+)*$/.test(mp)) {
      flash('Adresse de page illisible. Copiez-la depuis Créer une page → Mes pages, par exemple /p/inscriptions-ramadan.');
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
      if (c) c.commitKeys(Object.keys(PUB));
      setTimeout(checkDirty, 0);
      flash('Contact enregistré. Le site est à jour.');
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
  window.__saCoSave = saveAll;
  window.__saCoUndo = undoAll;
  function start() {
    if (started) return;
    started = true;
    api('/api/admin/settings/pages').then(function (r) {
      if (!(r && r.ok && r.settings)) return;
      pagesBase = r.settings;
      var sw = {};
      Object.keys(PUB).forEach(function (k) { sw[k] = pagesBase[PUB[k]] !== false; });
      var c = comp();
      if (c) c.setSwitches(sw, true);
    }, function () {});
  }
  if (comp()) start();
  else window.addEventListener('sa-co-ready', start, { once: true });
})();
</script>
'''

BOX = '<div id="svx-{k}" style="display:flex;flex-direction:column;gap:18px"><p class="hint" style="margin:0">Chargement des réglages…</p></div>'


def replace_sections(tpl, sp, end_marker, box):
    a = tpl.index(f'<div id="{sp}" class="sp">')
    b = tpl.index(end_marker, a) if end_marker else tpl.index('</main>', a)
    body = tpl[a:b]
    h = body.index('<section')
    last = body.rindex('</section>') + len('</section>')
    return tpl[:a] + body[:h] + box + body[last:] + tpl[b:]


def wire_panel():
    path = ROOT / 'SA-Contact.dc.html'
    s, i, j, tpl = load(path)
    assert 'id="sp-in"' in tpl, 'lancer wire_inbox.py avant wire_contact.py'
    if 'id="svx-contact"' not in tpl:
        tpl = replace_sections(tpl, 'sp-0', '<div id="sp-1" class="sp">', BOX.format(k='contact'))
        tpl = replace_sections(tpl, 'sp-1', None, BOX.format(k='p404'))
        tpl = resub(tpl, r'<div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap"><span class="tag" style="background:\{\{pub\.pub_404\.bg\}\}.*?</button></div>',
                    '<span class="hint" style="margin:0">Toujours en ligne : une adresse inconnue mène ici.</span>')
        tpl = resub(tpl, r'<span class="btn btn-line" aria-disabled="true" title="Cette page n’existe pas encore sur le site public" style="[^"]*">' + SVG + r'Voir la page</span>',
                    lambda x: '<a class="btn btn-line" href="/404.html" target="_blank" rel="noopener" style="min-height:40px">' + x.group(1) + 'Voir la page</a>')
    pre = tpl.split('class Component')[0]
    assert 'Inscriptions Ramadan 2027' not in pre and 'pub_404' not in pre

    m = re.search(r'this\.base = (\{.*?\});', tpl)
    assert m, 'base du composant introuvable'
    old = json.loads(m.group(1))
    base = {k: v for k, v in old.items() if k in PUB}
    assert set(base) == set(PUB), base
    comp = COMPONENT_SCRIPT.replace('__BASE__', json.dumps(base))
    tpl, n = re.subn(r'class Component extends DCLogic \{.*?\n\}', lambda _: comp, tpl, count=1, flags=re.S)
    assert n == 1
    tpl = re.sub(r'<script id="(?:sa-co-x|sa-co-sync)">.*?</script>\s*', '', tpl, flags=re.S)
    engine = engine_source().replace('__TABS__', json.dumps(TABS, ensure_ascii=False))
    sync = SYNC_SCRIPT.replace('__PUB__', json.dumps(PUB))
    k = tpl.rindex('</body>')
    tpl = tpl[:k] + engine + sync + tpl[k:]
    save(path, s, i, j, tpl)
    print('SA-Contact.dc.html : Page Contact et Page 404 reliées (clés contact, p404, pages)')


# =====================================================================================
# Page Contact publique
# =====================================================================================

CO_JS = r"""
    /*ascil-contact*/
    const PT = (typeof window !== 'undefined' && window.__ascilPrayer) || {};
    const C = PT.contact || __CO__;
    const G = (PT.home && PT.home.general) || __GEN__;
    const pre = (typeof location !== 'undefined' && /\/(M-|T-)[^\/]*$/.exec(location.pathname)) ? /\/(M-|T-)[^\/]*$/.exec(location.pathname)[1] : '';
    const PAGES = { accueil: 'Main', horaires: 'Horaires', apropos: 'APropos', services: 'Services', dons: 'Dons', evenements: 'Evenements', ressources: 'Ressources',
      mariages: 'N2-Mariages', funerailles: 'N2-Funerailles' };
    const page = (k) => (PAGES[k] ? pre + PAGES[k] + '.dc.html' : '');
    const mail = G.email || '';
    const at = mail.indexOf('@');
    const L = C.lignes || {};
    const ligne = (k) => !!(L[k] && L[k].on && L[k].texte);
    const F = C.form || {};
    const E = C.etiquette || {}, W = C.ecrire || {}, D = W.demandes || {};
    const etis = (E.items || []).filter((x) => x.on && (x.titre || x.texte)).map((x) => ({ titre: x.titre || '', hasTitre: !!x.titre, texte: x.texte || '' }));
    const dems = (D.items || []).filter((x) => x.on && x.texte).map((x) => ({ texte: x.texte, href: page(x.lien), hasLien: !!page(x.lien), lienTexte: x.lienTexte || 'en savoir plus' }));
    const sujets = (F.sujets || []).filter((x) => x.on && x.titre).map((x) => ({ t: x.titre }));
    this.coGo = F.apres === 'page' ? page(F.page) || '' : F.apres === 'mapage' && F.mapage ? F.mapage : '';
    const copied = this.state.cpk === 'mail';
    const fb = /^https?:\/\//.test(G.facebook || '') ? G.facebook : '';
    return {
      coCarte: C.carte !== false, coMap: 'https://maps.google.com/?q=' + C.lat + ',' + C.lng,
      coCoords: String(C.lat).replace('.', ',') + ' · ' + String(C.lng).replace('.', ',').replace('-', '−'),
      coAdr: G.address || '', coVille: G.city || '', hasCP: !!C.codePostal, coCP: C.codePostal || '',
      liStat: ligne('stationnement'), liFaut: ligne('fauteuil'), liAblu: ligne('ablutions'),
      txStat: (L.stationnement || {}).texte || '', txFaut: (L.fauteuil || {}).texte || '', txAblu: (L.ablutions || {}).texte || '',
      showLignes: ligne('stationnement') || ligne('fauteuil') || ligne('ablutions'),
      showEti: E.on !== false && etis.length > 0, etiTitre: E.titre || '', etis,
      coMail: mail, coMail1: at > 0 ? mail.slice(0, at + 1) : mail, coMail2: at > 0 ? mail.slice(at + 1) : '',
      coCopier: W.copier !== false,
      cp: { mail: () => { try { navigator.clipboard && navigator.clipboard.writeText(mail); } catch (e) {} this.setState({ cpk: 'mail' }); clearTimeout(this.ct); this.ct = setTimeout(() => this.setState({ cpk: '' }), 2000); } },
      nc: { mail: !copied }, cpd: { mail: copied },
      coFb: W.facebook !== false && !!fb, coFbUrl: fb,
      showDem: D.on !== false && dems.length > 0, dems, hasDemNote: !!D.note, demNote: D.note || '',
      hasSujets: sujets.length > 0, sujets, coMax: F.max || 1000,
      coMerciT: F.merciTitre || 'Message envoyé', coMerciX: F.merciTexte || '',
    };"""

GO_OLD = "if (d && d.ok) this.setState({ sending: false, sent: true });"
GO_NEW = "if (d && d.ok) { if (this.coGo) { location.href = this.coGo; return; } this.setState({ sending: false, sent: true }); }"


def patch_contact(tpl):
    a = tpl.index('<main'); b = tpl.index('</main>')
    m = tpl[a:b]
    # ---------- Adresse et carte ----------
    sa, sb = section_span(m, '<section class="sec" aria-labelledby="map-t">')
    sec = m[sa:sb]
    ca = sec.index('<div class="card" style="padding:0;overflow:hidden;min-height:360px')
    cb = sec.index('</div>\n  </div>\n', ca) + len('</div>\n  </div>')
    card = sec[ca:cb]
    card = resub(card, r'<a class="btn btn-gold" href="https://maps\.google\.com/\?q=47\.836047,-69\.537465">', '<a class="btn btn-gold" href="{{coMap}}" target="_blank" rel="noopener">')
    card = rep(card, '>47,836047 · −69,537465</span>', '>{{coCoords}}</span>')
    sec = sec[:ca] + sc_if('coCarte', card) + sec[cb:]
    sec = rep(sec, '>106, rue de l’Église<br>Edmundston (Québec)</h2>', '>{{coAdr}}<br>{{coVille}}</h2>')
    sec = rep(sec, '<p class="ph" style="margin:12px 0 0">Code postal : affiché une fois confirmé par l’association</p>',
              sc_if('hasCP', '<p class="muted" style="margin:12px 0 0">Code postal : {{coCP}}</p>', 'false'))
    for txt, on, var in (('Stationnement dans les rues avoisinantes', 'liStat', 'txStat'), ('Salle de prière accessible en fauteuil roulant', 'liFaut', 'txFaut'),
                         ('Ablutions et toilettes sur place', 'liAblu', 'txAblu')):
        sec = resub(sec, r'(<li style="display:flex;gap:14px;align-items:center"><span style="color:#0B0F1A">' + SVG + r'</span>)' + re.escape(txt) + '</li>',
                    lambda x, on=on, var=var: sc_if(on, x.group(1) + '{{' + var + '}}</li>'))
    sec = resub(sec, r'(<ul style="list-style:none;margin:28px 0 0.*?</ul>)', lambda x: sc_if('showLignes', x.group(1)))
    m = m[:sa] + sec + m[sb:]
    # ---------- Étiquette ----------
    sa, sb = section_span(m, '<section class="sand" aria-labelledby="eti-t"')
    sec = m[sa:sb]
    sec = rep(sec, '>Tous les visiteurs sont les bienvenus</h2>', '>{{etiTitre}}</h2>')
    sec = resub(sec, r'<p class="lead" style="margin-top:16px;color:#141B2C">Une tenue.*?</p>',
                '<div style="display:flex;flex-direction:column;gap:16px;margin-top:20px"><sc-for list="{{etis}}" as="e" hint-placeholder-count="3"><div>'
                + sc_if('e.hasTitre', '<p class="h3" style="font-size:19px">{{e.titre}}</p>')
                + '<p class="lead" style="margin:6px 0 0;color:#141B2C">{{e.texte}}</p></div></sc-for></div>')
    m = m[:sa] + sc_if('showEti', sec) + m[sb:]
    # ---------- Écrire ----------
    sa, sb = section_span(m, '<section class="sec" aria-labelledby="ec-t">')
    sec = m[sa:sb]
    sec = rep(sec, '>associationrdl.ascil@<wbr>gmail.com</p>', '>{{coMail1}}<wbr>{{coMail2}}</p>')
    sec = resub(sec, r'(<button type="button" class="btn btn-ghost" sc-camel-on-click="\{\{cp\.mail\}\}".*?</button>)', lambda x: sc_if('coCopier', x.group(1)))
    sec = resub(sec, r'<a class="link" href="https://www\.facebook\.com/" style="margin-top:16px">' + SVG + 'Message rapide sur Facebook</a>',
                lambda x: sc_if('coFb', '<a class="link" href="{{coFbUrl}}" target="_blank" rel="noopener" style="margin-top:16px">' + x.group(1) + 'Message rapide sur Facebook</a>'))
    da = sec.index('<h3 class="h3" style="margin-top:36px">Demandes particulières</h3>')
    db = sec.index('</p>', sec.index('À adresser par courriel à l’association.', da)) + len('</p>')
    dem = ('<h3 class="h3" style="margin-top:36px">Demandes particulières</h3><ul style="margin:12px 0 0;padding-left:20px;display:flex;flex-direction:column;gap:8px">'
           '<sc-for list="{{dems}}" as="d" hint-placeholder-count="4"><li>{{d.texte}}'
           + sc_if('d.hasLien', ' : <a href="{{d.href}}" class="link">{{d.lienTexte}}</a>', 'false') + '</li></sc-for></ul>'
           + sc_if('hasDemNote', '<p class="muted" style="margin:10px 0 0;font-size:15px">{{demNote}}</p>'))
    sec = sec[:da] + sc_if('showDem', dem) + sec[db:]
    # ---------- Formulaire ----------
    sec = resub(sec, r'<div class="field"><label for="f-suj">Sujet</label><sc-raw-select id="f-suj">.*?</sc-raw-select></div>',
                sc_if('hasSujets', '<div class="field"><label for="f-suj">Sujet</label><select id="f-suj"><sc-for list="{{sujets}}" as="j" hint-placeholder-count="5">'
                      '<option value="{{j.t}}">{{j.t}}</option></sc-for></select></div>'))
    sec = rep(sec, 'maxlength="1000"', 'maxlength="{{coMax}}"')
    sec = rep(sec, '{{msgLen}} / 1000', '{{msgLen}} / {{coMax}}')
    sec = rep(sec, '<p class="h3" style="margin-top:16px">Message envoyé</p>', '<p class="h3" style="margin-top:16px">{{coMerciT}}</p>')
    sec = rep(sec, '<p class="muted" style="margin:8px 0 0">Merci. L’association vous répondra à l’adresse indiquée.</p>', '<p class="muted" style="margin:8px 0 0">{{coMerciX}}</p>')
    m = m[:sa] + sec + m[sb:]
    assert 'facebook.com/"' not in m and 'maxlength="1000"' not in m and '/ 1000' not in m and 'affiché une fois confirmé' not in m
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
    if GO_NEW not in code:
        assert code.count(GO_OLD) == 1, 'envoi du formulaire introuvable (wire_inbox.py doit passer avant)'
        code = code.replace(GO_OLD, GO_NEW)
    return tpl[:la] + code + tpl[lb:]


# =====================================================================================
# Page 404
# =====================================================================================

P404_JS = r"""
    /*ascil-404*/
    const PT = (typeof window !== 'undefined' && window.__ascilPrayer) || {};
    const P = PT.p404 || __P404__;
    return {
      p4Titre: P.titre || 'Cette page n’existe pas', p4Texte: P.texte || '', p4HasTexte: !!P.texte,
      p4Acc: P.accueil !== false, p4Hor: P.horaires !== false, p4Tro: P.trouver !== false,
      p4Any: P.accueil !== false || P.horaires !== false || P.trouver !== false,
    };"""

P404_LOAD = '''<script id="ascil-404-load">
(function () {
  fetch('/api/settings/p404', { credentials: 'same-origin' }).then(function (r) { return r.json(); }).then(function (d) {
    if (!d || !d.ok || !d.settings) return;
    var P = window.__ascilPrayer = window.__ascilPrayer || {};
    P.p404 = d.settings;
    try { window.dispatchEvent(new Event('ascil:prayer')); } catch (e) {}
  }, function () {});
})();
</script>
'''


def build_404(contact_path):
    s, i, j, tpl = load(contact_path)
    a = tpl.index('<main'); b = tpl.index('</main>')
    m = tpl[a:b]
    head = m[:m.index('>') + 1]
    tail = m[m.rindex('<div style="padding:24px 0 8px">'):]
    btn = 'min-height:48px'
    main = (head + '\n<section class="sand" aria-labelledby="nf-t" style="border-bottom:1px solid #E4D9C0;position:relative;overflow:hidden;min-height:62vh;display:flex;align-items:center">'
            '<div class="frise" aria-hidden="true" style="opacity:.8"></div><div class="wrap" style="padding-top:72px;padding-bottom:72px;position:relative;inline-size:100%">'
            '<p class="eyebrow">Erreur 404 · Page introuvable</p><h1 id="nf-t" class="h1 rv" style="margin-top:12px;max-width:760px">{{p4Titre}}</h1>'
            + sc_if('p4HasTexte', '<p class="lead" style="margin-top:16px;max-width:640px">{{p4Texte}}</p>')
            + sc_if('p4Any', '<nav aria-label="Raccourcis" style="display:flex;gap:12px;flex-wrap:wrap;margin-top:32px">'
                    + sc_if('p4Acc', f'<a class="btn btn-green" href="/" style="{btn}">Retour à l’accueil</a>')
                    + sc_if('p4Hor', f'<a class="btn btn-ghost" href="/Horaires.dc.html" style="{btn}">Horaires de prière</a>')
                    + sc_if('p4Tro', f'<a class="btn btn-ghost" href="/Contact.dc.html" style="{btn}">Nous trouver</a>') + '</nav>')
            + '</div></section>\n' + tail)
    tpl = tpl[:a] + main + tpl[b:]
    tpl = rep(tpl, '<title>Contact — ASCIL</title>', '<title>Page introuvable — ASCIL</title>')
    tpl = rep(tpl, '<head>\n<meta charset="utf-8">', '<head>\n<meta charset="utf-8">\n<meta name="robots" content="noindex">')
    # Liens et menu absolus (/Horaires.dc.html) : ils marchent quelle que soit l'adresse demandée (/a/b/c).
    # Pas de <base> : il enverrait aussi les ancres « # » (Revenir en haut) vers l'accueil.
    tpl = re.sub(r'(<a\b[^>]*?\shref=")(?![a-zA-Z][a-zA-Z0-9+.-]*:|/|#|\{\{)([^"]+")', r'\1/\2', tpl)
    tpl = tpl.replace(' aria-current="page"', '')
    la = tpl.index('<script type="text/x-dc"')
    lb = tpl.index('</script>', la)
    code = tpl[la:lb]
    xa = code.index('  xvals() {')
    xb = code.index('\n  }\n', xa) + len('\n  }\n')
    code = code[:xa] + '  xvals() {' + P404_JS.replace('__P404__', json.dumps(defaults()['p404'], ensure_ascii=False)) + '\n  }\n' + code[xb:]
    tpl = tpl[:la] + code + tpl[lb:]
    k = tpl.rindex('</body>')
    tpl = tpl[:k] + P404_LOAD + tpl[k:]
    out = s[:i] + json.dumps(tpl).replace('</', '<\\u002F') + s[j:]
    out = out.replace('Contact — ASCIL', 'Page introuvable — ASCIL')
    (ROOT / '404.html').write_text(out, encoding='utf-8')
    print('404.html : page introuvable construite depuis Contact (clé p404)')


_DEF = None


def defaults():
    global _DEF
    if _DEF is None:
        js = ("import('./functions/_lib/settings.js').then((m) => { const d = m.DEFAULT_SETTINGS; "
              "process.stdout.write(JSON.stringify({ contact: d.contact, p404: d.p404, general: d.home.general })); })")
        _DEF = json.loads(subprocess.run(['node', '--input-type=module', '-e', js], cwd=ROOT, capture_output=True, text=True, check=True).stdout)
    return _DEF


def wire_public():
    d = defaults()
    for pre in ('', 'M-', 'T-'):
        path = ROOT / f'{pre}Contact.dc.html'
        s, i, j, tpl = load(path)
        if '{{coMap}}' not in tpl:
            tpl = patch_contact(tpl)
        tpl = set_xvals(tpl, CO_JS.replace('__CO__', json.dumps(d['contact'], ensure_ascii=False)).replace('__GEN__', json.dumps(d['general'], ensure_ascii=False)))
        save(path, s, i, j, tpl)
    print('Contact (PC, M-, T-) : adresse, carte, étiquette, écrire, formulaire reliés')
    build_404(ROOT / 'Contact.dc.html')


if __name__ == '__main__':
    wire_panel()
    wire_public()
