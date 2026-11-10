"""Branche « Services » (étape S) : panneau SA-Services et pages publiques des services.

S1 — onglet « Tous les services » (clé services) et page publique Services (PC, M-, T-) :
- Cartes de services : ordre, affichage, ajout et suppression des cartes libres. Trois cartes ont
  un rôle propre : prières (heures de Fajr et d'Icha du tableau du mois), Jumu'a (heure de Jumu'a,
  lignes vers la khutba et l'espace femmes), Aïd (lieu commun avec Horaires → Prières de l'Aïd,
  horaires.aid.lieu ; Zakat al-Fitr).
- Cartes « Les autres services » (une carte vers une page masquée disparaît déjà du site),
  équipements sur place, bloc « Une question ? » et son lien.
- Interrupteurs « Page publiée » des 6 onglets reliés à la clé pages.

Ordre : après wire_prieres.py (script #ascil-prayer-live, écoute « ascil:prayer »), avant fix_inputs.py.
Idempotent.
"""
import json, pathlib, re

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


SITE_LINKS = [
    'Page : Horaires du mois', 'Page : Événements', 'Page : Contact', 'Page : Faire un don', 'Page : Campagne en direct',
    'Page : Inscription aux événements', 'Page : À propos', 'Page : Services', 'Page : Ressources',
]
URL_MAP = {
    'Page : Horaires du mois': 'Horaires.dc.html', 'Page : Rappel de prière': 'N3-Rappel.dc.html',
    'Page : Langue de la khutba': 'N2-Khutba.dc.html', 'Page : Faire un don': 'Dons.dc.html',
    'Page : Campagne en direct': 'N3-Campagne.dc.html', 'Page : Événements': 'Evenements.dc.html',
    'Page : Inscription aux événements': 'N3-Inscription.dc.html', 'Page : Calendrier du mois': 'N3-Calendrier.dc.html',
    'Page : Contact': 'Contact.dc.html', 'Page : Ressources': 'Ressources.dc.html', 'Page : À propos': 'APropos.dc.html',
    'Page : Services': 'Services.dc.html',
}
ICON_NAMES = ['Horloge', 'Calendrier', 'Croissant de lune', 'Étoile', 'Main tendue']

# Cartes « Les autres services » : clé de réglage, page, titre.
AUTRES = [('cours', 'N2-Cours', 'Cours de Coran et d’arabe', 'pg_cours'), ('mariages', 'N2-Mariages', 'Mariages', 'pg_mariages'),
          ('funerailles', 'N2-Funerailles', 'Funérailles et janaza', 'pg_funerailles'),
          ('aide', 'N2-AideAlimentaire', 'Aide alimentaire', 'pg_aide'), ('femmes', 'N2-EspaceFemmes', 'Espace femmes', 'pg_femmes'),
          ('khutba', 'N2-Khutba', 'Langue de la khutba', 'pg_khutba')]
EQUIP = [('fauteuil', 'Salle accessible en fauteuil roulant'), ('ablutions', 'Ablutions et toilettes'),
         ('parking', 'Stationnement dans les rues avoisinantes'), ('femmes', 'Espace réservé aux femmes')]


# =====================================================================================
# 1. Panneau SA-Services, onglet « Tous les services »
# =====================================================================================

def card(num, key, title, dsc, body):
    sw = ''
    if key:
        sw = ('<div class="hsw"><span aria-hidden="true">Afficher</span><button type="button" class="sw" role="switch" '
              f'aria-label="Afficher {title}" aria-checked="{{{{s.{key}.c}}}}" sc-camel-on-click="{{{{s.{key}.t}}}}"></button></div>')
    cls = f'card {{{{off.{key}}}}}' if key else 'card'
    d = f'<p class="dsc">{dsc}</p>' if dsc else ''
    return (f'<section class="{cls}" aria-label="{title}"><div class="card-h"><span class="num" aria-hidden="true">{num}</span>'
            f'<div><h3 class="ttl">{title}</h3>{d}</div>{sw}</div><div class="card-b">{body}</div></section>')


def switch_row(key, label, hint='', extra=''):
    h = f'<p class="hint">{hint}</p>' if hint else ''
    return (f'<div class="row"><div><div style="font-weight:600;font-size:14px">{label}</div>{h}{extra}</div>'
            f'<button type="button" class="sw" role="switch" aria-label="{label}" aria-checked="{{{{s.{key}.c}}}}" '
            f'sc-camel-on-click="{{{{s.{key}.t}}}}"></button></div>')


SP0_SECTIONS = (
    card(1, None, 'Services offerts', 'Les cartes de la page, dans cet ordre. Les heures viennent du tableau du mois (Horaires).',
         '<div id="sv-items"></div><button type="button" class="btn btn-line" id="sv-add" style="align-self:flex-start">+ Ajouter un service</button>')
    + card(2, 'sv_autres', 'Les autres services', 'Cartes vers les pages de niveau 2. Une page masquée retire aussi sa carte du site.',
           '<div>' + ''.join(switch_row(f'sc_{k}', t, extra=f'<p class="hint" id="sv-pg-{k}" style="margin:2px 0 0"></p>')
                             for k, _, t, _ in AUTRES) + '</div>')
    + card(3, 'sv_equip', 'Équipements sur place', '',
           '<div>' + ''.join(switch_row(f'eq_{k}', t) for k, t in EQUIP) + '</div>')
    + card(4, 'sv_question', 'Bloc « Une question sur un autre service ? »', '',
           '<div class="fld"><label class="lbl" for="f5">Bouton « Nous écrire »</label><sc-raw-select class="in" id="f5">'
           + ''.join(f'<option>{x}</option>' for x in SITE_LINKS) + '</sc-raw-select></div>')
)

SP0_KEYS = ['sv_autres'] + [f'sc_{k}' for k, _, _, _ in AUTRES] + ['sv_equip'] + [f'eq_{k}' for k, _ in EQUIP] + ['sv_question']
SP0_DEFAULTS = {k: True for k in SP0_KEYS}
SP0_DEFAULTS['eq_femmes'] = False
PUB_PAGES = {'pub_services': 'pg_services', 'pub_cours': 'pg_cours', 'pub_mariages': 'pg_mariages',
             'pub_funerailles': 'pg_funerailles', 'pub_aide': 'pg_aide', 'pub_femmes': 'pg_femmes'}

COMPONENT_SCRIPT = r"""class Component extends DCLogic {
  constructor(props) {
    super(props);
    this.base = __BASE__;
    this.pubKeys = ["pub_services", "pub_cours", "pub_mariages", "pub_funerailles", "pub_aide", "pub_femmes"];
    this.state = { on: Object.assign({}, this.base), extDirty: false, toast: '' };
    window.__saServices = this;
  }
  componentDidMount() {
    window.dispatchEvent(new Event('sa-services-ready'));
  }
  componentWillUnmount() {
    clearTimeout(this.tt);
    if (window.__saServices === this) window.__saServices = null;
  }
  setSwitches(sw, asBase) {
    const next = Object.assign({}, this.state.on, sw);
    if (asBase) this.base = Object.assign({}, this.base, sw);
    this.setState({ on: next });
  }
  setExtDirty(flag) {
    if (!!this.state.extDirty !== !!flag) this.setState({ extDirty: !!flag });
    else this.forceUpdate();
  }
  // Seuls les interrupteurs réellement enregistrés deviennent la nouvelle base.
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
    const swDirty = Object.keys(on).some((k) => on[k] !== this.base[k]);
    const dirty = swDirty || !!this.state.extDirty;
    const s = {}, off = {}, op = {}, pub = {};
    Object.keys(on).forEach((k) => {
      s[k] = {
        c: String(!!on[k]),
        t: () => {
          const next = Object.assign({}, this.state.on, { [k]: !this.state.on[k] });
          this.setState({ on: next }, () => {
            if (window.__saServicesOnSwitch) window.__saServicesOnSwitch(k, next[k]);
          });
        }
      };
      off[k] = on[k] ? '' : 'off';
      op[k] = on[k] ? 1 : 0.5;
    });
    this.pubKeys.forEach((k) => { pub[k] = on[k] ? { t: 'Publiée', bg: '#DCEFE6', fg: '#0E4D3C' } : { t: 'Masquée du site', bg: '#F3EAD8', fg: '#7A5A1E' }; });
    return {
      s, off, op, pub,
      clean: !dirty, dot: dirty ? '#C49A4A' : '#7FB89F', statusTxt: dirty ? 'Changements non enregistrés' : 'Tout est enregistré',
      save: () => { if (window.__saServicesSave) window.__saServicesSave(); },
      undo: () => { if (window.__saServicesUndo) window.__saServicesUndo(); },
      toast: this.state.toast
    };
  }
}"""

SYNC_SCRIPT = r'''<script id="sa-services-sync">
(function () {
  var SITE = __SITE__;
  var ICONS = __ICONS__;
  var AUTRES = __AUTRES__;
  var EQUIP = __EQUIP__;
  var PUB = __PUB__;
  var EXT = 'Lien externe…';
  var KIND_TAG = { prieres: 'Heures du tableau du mois', jumua: 'Heure de Jumu’a du tableau du mois', aid: 'Lieu commun avec Horaires' };
  var SVG = {
    up: '<svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 19V5M5 12l7-7 7 7"></path></svg>',
    down: '<svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5v14M19 12l-7 7-7-7"></path></svg>',
    del: '<svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3"></path></svg>'
  };
  var items = [], svBase = null, aidLieu = '', aidLieuBase = '', pagesBase = null, pages = [], baseSig = '', saving = false, started = false;
  var prevLink = {};

  function comp() { return window.__saServices; }
  function flash(m) { var c = comp(); if (c) c.flash(m); }
  function getEl(id) { return document.getElementById(id); }
  // Valeurs réelles des champs, gardées ici : un champ redessiné par la page reprend la valeur de la
  // maquette (ou se vide) ; on la remet dès qu'il réapparaît, et on la lit même s'il n'est pas affiché.
  var cur = {};
  function setVal(id, v) { cur[id] = v == null ? '' : String(v); var e = getEl(id); if (e) { e.value = cur[id]; e.setAttribute('data-sa-v', '1'); } }
  function getVal(id) {
    var e = getEl(id);
    if (e && (e.getAttribute('data-sa-v') === '1' || !Object.prototype.hasOwnProperty.call(cur, id))) return String(e.value).trim();
    return Object.prototype.hasOwnProperty.call(cur, id) ? String(cur[id]).trim() : '';
  }
  ['input', 'change'].forEach(function (ev) {
    document.addEventListener(ev, function (e) { var t = e.target; if (t && t.id && Object.prototype.hasOwnProperty.call(cur, t.id)) { cur[t.id] = t.value; t.setAttribute('data-sa-v', '1'); } }, true);
  });
  var refillT = null;
  new MutationObserver(function () {
    clearTimeout(refillT);
    refillT = setTimeout(function () {
      Object.keys(cur).forEach(function (id) { var e = getEl(id); if (e && e.getAttribute('data-sa-v') !== '1') { e.value = cur[id]; e.setAttribute('data-sa-v', '1'); } });
    }, 0);
  }).observe(document.documentElement, { childList: true, subtree: true });
  function clone(o) { return JSON.parse(JSON.stringify(o)); }
  function swOn() { var c = comp(); return (c && c.state && c.state.on) || {}; }
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; });
  }
  function parseAmount(v) {
    var t = String(v == null ? '' : v).replace(/[\s\u00a0\u202f$]/g, '').replace(',', '.');
    if (t === '') return null;
    var n = Number(t);
    return isFinite(n) && n >= 0 ? Math.round(n) : NaN;
  }

  // ---------- Liens ----------
  function linkLabel(v) {
    if (!v) return 'Aucun lien';
    if (v === EXT) return EXT;
    if (/^\/p\//.test(v)) {
      var p = pages.filter(function (x) { return x.url === v; })[0];
      return p ? 'Ma page : ' + p.title : 'Ma page : ' + v + ' (non publiée ou supprimée)';
    }
    if (/^https?:\/\//i.test(v)) return 'Lien externe : ' + v;
    return v;
  }
  function linkOptions(cur, allowNone) {
    var vals = (allowNone ? [''] : []).concat(SITE, pages.map(function (p) { return p.url; }));
    if (cur && vals.indexOf(cur) === -1) vals.push(cur);
    vals.push(EXT);
    return vals.map(function (v) { return '<option value="' + esc(v) + '"' + (v === cur ? ' selected' : '') + '>' + esc(linkLabel(v)) + '</option>'; }).join('');
  }
  function askExternal(sel, prev) {
    var url = (window.prompt('Adresse du lien externe (doit commencer par https://)', 'https://') || '').trim();
    if (/^https?:\/\/[^\s<>"]{3,}$/i.test(url) && url.length <= 500) {
      var o = document.createElement('option');
      o.value = url; o.textContent = 'Lien externe : ' + url;
      sel.insertBefore(o, sel.options[sel.options.length - 1]);
      sel.value = url;
      return url;
    }
    sel.value = prev;
    if (url && url !== 'https://') window.alert('Adresse non valide : elle doit commencer par https:// . Le lien précédent est conservé.');
    return prev;
  }

  // ---------- Cartes de services ----------
  function title(x) { return x.titre || 'Nouveau service'; }
  function fld(id, label, html) { return '<div class="fld"><label class="lbl" for="' + id + '">' + label + '</label>' + html + '</div>'; }
  function inp(i, f, v, extra) {
    return '<input class="in" type="text" id="sv-' + i + '-' + f + '" data-i="' + i + '" data-f="' + f + '" value="' + esc(v) + '"' + (extra || '') + '>';
  }
  function area(i, f, v, max) {
    return '<textarea class="in" rows="2" maxlength="' + max + '" id="sv-' + i + '-' + f + '" data-i="' + i + '" data-f="' + f + '">' + esc(v) + '</textarea>';
  }
  function flag(i, f, label, on) {
    return '<div class="row"><div><div style="font-weight:600;font-size:14px">' + label + '</div></div>' +
      '<button type="button" class="sw" role="switch" data-i="' + i + '" data-flag="' + f + '" aria-label="' + esc(label) + '" aria-checked="' + (on ? 'true' : 'false') + '"></button></div>';
  }
  function bodyHtml(x, i) {
    var icon = '<select class="in" id="sv-' + i + '-icone" data-i="' + i + '" data-f="icone">' + ICONS.map(function (n, k) {
      return '<option value="' + k + '"' + (k === x.icone ? ' selected' : '') + '>' + n + '</option>';
    }).join('') + '</select>';
    var h = '<div class="g2">' + fld('sv-' + i + '-titre', 'Titre', inp(i, 'titre', x.titre, ' maxlength="80"')) + fld('sv-' + i + '-icone', 'Icône', icon) + '</div>';
    if (x.kind === 'prieres') {
      h += fld('sv-' + i + '-texte', 'Texte (suivi de « Fajr à …, Icha à … »)', area(i, 'texte', x.texte, 400));
    } else if (x.kind === 'jumua') {
      h += fld('sv-' + i + '-texte', 'Texte (après « Chaque vendredi à … »)', area(i, 'texte', x.texte, 400));
      h += flag(i, 'khutba', 'Ligne « Langue de la khutba de ce vendredi »', x.khutba) + flag(i, 'femmes', 'Ligne « Espace pour les femmes »', x.femmes);
    } else if (x.kind === 'aid') {
      h += fld('sv-aid-lieu', 'Lieu des prières de l’Aïd', '<input class="in" type="text" id="sv-aid-lieu" maxlength="160" value="' + esc(aidLieu) + '">') +
        '<p class="hint" style="margin:-4px 0 0">Le même lieu s’affiche sur la page Horaires (Prières de l’Aïd).</p>' +
        '<div class="g2">' + fld('sv-' + i + '-zakat', 'Zakat al-Fitr par personne', '<div style="position:relative">' +
          inp(i, 'zakat', x.zakat == null ? '' : x.zakat, ' inputmode="numeric" style="padding-right:32px"') +
          '<span aria-hidden="true" style="position:absolute;right:12px;top:50%;transform:translateY(-50%);color:#4F5E57;font-weight:600">$</span></div>') +
        fld('sv-' + i + '-zakatAnnee', 'Année du montant', inp(i, 'zakatAnnee', x.zakatAnnee, ' maxlength="12" placeholder="2026"')) + '</div>' +
        '<p class="hint" style="margin:-4px 0 0">Sans montant, la ligne Zakat al-Fitr n’est pas affichée.</p>' +
        fld('sv-' + i + '-texte', 'Texte complémentaire (facultatif)', area(i, 'texte', x.texte, 400));
    } else {
      h += fld('sv-' + i + '-texte', 'Texte', area(i, 'texte', x.texte, 400));
      h += flag(i, 'saison', 'Étiquette « Saisonnier »', x.saison);
    }
    if (x.kind === 'prieres' || x.kind === 'libre') {
      h += '<div class="g2">' + fld('sv-' + i + '-lien', 'Lien', '<select class="in" id="sv-' + i + '-lien" data-i="' + i + '" data-f="lien">' + linkOptions(x.lien, x.kind === 'libre') + '</select>') +
        fld('sv-' + i + '-lienTexte', 'Texte du lien', inp(i, 'lienTexte', x.lienTexte, ' maxlength="60" placeholder="En savoir plus"')) + '</div>';
    }
    return h;
  }
  function render() {
    var wrap = getEl('sv-items');
    if (!wrap) return;
    if (!items.length) { wrap.innerHTML = '<p class="hint" style="margin:0">Aucun service.</p>'; return; }
    wrap.innerHTML = '<ol style="list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:10px">' + items.map(function (x, i) {
      var t = title(x), tag = x.kind === 'libre' ? (x.saison ? 'Saisonnier' : '') : KIND_TAG[x.kind];
      return '<li style="border:1px solid #E4D9C0;border-radius:14px;background:#fff">' +
        '<div style="display:flex;align-items:center;gap:10px;padding:10px 10px 10px 14px;flex-wrap:wrap;border-bottom:1px solid #F3EAD8">' +
        '<span class="pos">' + (i + 1) + '</span>' +
        '<span data-title style="flex:1;min-width:150px;font-weight:700;color:#0E4D3C;overflow-wrap:anywhere">' + esc(t) + '</span>' +
        (tag ? '<span class="tag" style="background:#F3EAD8;color:#7A5A1E">' + esc(tag) + '</span>' : '') +
        '<button type="button" class="ico" data-i="' + i + '" data-act="up" aria-label="Monter ' + esc(t) + '"' + (i === 0 ? ' disabled' : '') + '>' + SVG.up + '</button>' +
        '<button type="button" class="ico" data-i="' + i + '" data-act="down" aria-label="Descendre ' + esc(t) + '"' + (i === items.length - 1 ? ' disabled' : '') + '>' + SVG.down + '</button>' +
        (x.kind === 'libre' ? '<button type="button" class="ico" data-i="' + i + '" data-act="del" aria-label="Supprimer ' + esc(t) + '">' + SVG.del + '</button>' : '') +
        '<button type="button" class="sw" role="switch" data-i="' + i + '" data-act="on" aria-label="Afficher ' + esc(t) + '" aria-checked="' + (x.on ? 'true' : 'false') + '"></button>' +
        '</div><div class="li-b" style="opacity:' + (x.on ? 1 : 0.5) + '">' + bodyHtml(x, i) + '</div></li>';
    }).join('') + '</ol>';
    items.forEach(function (x, i) { prevLink['sv-' + i + '-lien'] = x.lien; });
  }

  function pageTags() {
    var on = swOn();
    AUTRES.forEach(function (a) {
      var el = getEl('sv-pg-' + a[0]);
      if (!el) return;
      var pub = a[3] in PUB_REV ? !!on[PUB_REV[a[3]]] : !(pagesBase && pagesBase[a[3]] === false);
      el.textContent = pub ? 'Page publiée.' : 'Page masquée : la carte n’apparaît pas sur le site.';
    });
  }
  var PUB_REV = {};
  Object.keys(PUB).forEach(function (k) { PUB_REV[PUB[k]] = k; });

  // ---------- Lecture / application ----------
  function cleanItem(x) {
    var z = parseAmount(x.zakat);
    return { kind: x.kind, titre: String(x.titre || '').trim(), texte: String(x.texte || '').trim(), icone: parseInt(x.icone, 10) || 0,
      saison: !!x.saison, lien: x.lien || '', lienTexte: String(x.lienTexte || '').trim(), khutba: !!x.khutba, femmes: !!x.femmes,
      zakat: z === null || isNaN(z) ? null : z, zakatAnnee: String(x.zakatAnnee || '').trim(), on: !!x.on };
  }
  function readSv(ignoreSw) {
    var on = ignoreSw ? {} : swOn();
    var b = function (k) { return ignoreSw ? true : !!on[k]; };
    var autres = { on: b('sv_autres') }, eq = { on: b('sv_equip') };
    AUTRES.forEach(function (a) { autres[a[0]] = b('sc_' + a[0]); });
    EQUIP.forEach(function (e) { eq[e[0]] = b('eq_' + e[0]); });
    return { items: items.map(cleanItem), autres: autres, equipements: eq, question: { on: b('sv_question'), lien: getVal('f5') } };
  }
  function sig() { return JSON.stringify([readSv(true), getVal('sv-aid-lieu') || aidLieu]); }
  function checkDirty() { var c = comp(); if (c && baseSig) c.setExtDirty(sig() !== baseSig || !!(window.__svx && window.__svx.dirty())); }
  window.__svCheckDirty = checkDirty;

  function applySv(v, asBase) {
    if (asBase) svBase = clone(v);
    items = clone(v.items);
    var sw = { sv_autres: v.autres.on, sv_equip: v.equipements.on, sv_question: v.question.on };
    AUTRES.forEach(function (a) { sw['sc_' + a[0]] = v.autres[a[0]] !== false; });
    EQUIP.forEach(function (e) { sw['eq_' + e[0]] = !!v.equipements[e[0]]; });
    var c = comp();
    if (c) c.setSwitches(sw, asBase);
    var f5 = getEl('f5');
    if (f5) { f5.innerHTML = linkOptions(v.question.lien, false); f5.value = v.question.lien; prevLink.f5 = f5.value; }
    render();
  }

  // ---------- Événements ----------
  function onClick(e) {
    var t = e.target;
    if (t.closest && t.closest('#sv-add')) {
      if (items.length >= 12) { flash('Au plus 12 cartes. Supprimez-en une pour en ajouter une autre.'); return; }
      items.push({ kind: 'libre', titre: '', texte: '', icone: 4, saison: false, lien: '', lienTexte: '', khutba: false, femmes: false, zakat: null, zakatAnnee: '', on: true });
      render();
      checkDirty();
      var last = document.querySelector('#sv-items li:last-child input');
      if (last) last.focus();
      return;
    }
    var b = t.closest && t.closest('#sv-items [data-i]');
    if (!b || b.tagName !== 'BUTTON') return;
    var i = parseInt(b.getAttribute('data-i'), 10), x = items[i], act = b.getAttribute('data-act'), fl = b.getAttribute('data-flag');
    if (!x) return;
    if (fl) { x[fl] = !x[fl]; }
    else if (act === 'up' && i > 0) { items.splice(i - 1, 0, items.splice(i, 1)[0]); }
    else if (act === 'down' && i < items.length - 1) { items.splice(i + 1, 0, items.splice(i, 1)[0]); }
    else if (act === 'del' && x.kind === 'libre') {
      if (!window.confirm('Supprimer la carte « ' + title(x) + ' » ? Le changement sera publié à l’enregistrement.')) return;
      items.splice(i, 1);
    }
    else if (act === 'on') { x.on = !x.on; }
    else return;
    render();
    checkDirty();
    var j = act === 'up' ? i - 1 : act === 'down' ? i + 1 : i;
    var again = document.querySelector('#sv-items [data-i="' + j + '"]' + (fl ? '[data-flag="' + fl + '"]' : '[data-act="' + act + '"]'));
    if (again && !again.disabled) again.focus();
  }
  function onInput(e) {
    var t = e.target;
    if (!t || !t.getAttribute) return;
    if (t.id === 'sv-aid-lieu') { aidLieu = t.value; checkDirty(); return; }
    if (t.id === 'f5') { checkDirty(); return; }
    var f = t.getAttribute('data-f');
    if (!f || !t.closest('#sv-items')) return;
    var x = items[parseInt(t.getAttribute('data-i'), 10)];
    if (!x) return;
    x[f] = f === 'icone' ? parseInt(t.value, 10) || 0 : t.value;
    if (f === 'titre') { var ti = t.closest('li').querySelector('[data-title]'); if (ti) ti.textContent = title(x); }
    checkDirty();
  }
  function onChange(e) {
    var sel = e.target;
    if (!sel || sel.tagName !== 'SELECT' || (sel.id !== 'f5' && sel.getAttribute('data-f') !== 'lien')) return;
    if (sel.value === EXT) {
      var v = askExternal(sel, prevLink[sel.id] || '');
      if (sel.id !== 'f5') { var x = items[parseInt(sel.getAttribute('data-i'), 10)]; if (x) x.lien = v; }
    }
    prevLink[sel.id] = sel.value;
    checkDirty();
  }

  // ---------- Enregistrer / annuler ----------
  function api(url, method, body) {
    var o = { credentials: 'same-origin', method: method || 'GET' };
    if (body) { o.headers = { 'Content-Type': 'application/json' }; o.body = JSON.stringify(body); }
    return fetch(url, o).then(function (r) { return r.json().catch(function () { return { ok: false }; }); });
  }
  function saveAll() {
    if (saving || !svBase) return;
    var bad = items.filter(function (x) { return x.kind === 'aid' && String(x.zakat).trim() !== '' && x.zakat != null && isNaN(parseAmount(x.zakat)); })[0];
    if (bad) { flash('Montant de la Zakat al-Fitr illisible. Écrivez un nombre, par exemple 15.'); return; }
    var noTitle = items.filter(function (x) { return x.on && !String(x.titre || '').trim(); })[0];
    if (noTitle) { flash('Une carte affichée n’a pas de titre. Écrivez-en un, ou masquez la carte.'); return; }
    var sv = readSv(false), on = swOn(), lieu = getVal('sv-aid-lieu');
    saving = true;
    flash('Enregistrement…');
    var tasks = [api('/api/admin/settings/services', 'PUT', sv)];
    if (lieu && lieu !== aidLieuBase) {
      tasks.push(api('/api/admin/settings/horaires').then(function (h) {
        if (!h || !h.ok || !h.settings) return h || { ok: false };
        var next = clone(h.settings);
        next.aid = Object.assign({}, next.aid, { lieu: lieu });
        return api('/api/admin/settings/horaires', 'PUT', next);
      }));
    }
    if (pagesBase) {
      var next = Object.assign({}, pagesBase);
      Object.keys(PUB).forEach(function (k) { next[PUB[k]] = !!on[k]; });
      if (JSON.stringify(next) !== JSON.stringify(pagesBase)) {
        tasks.push(api('/api/admin/settings/pages', 'PUT', next).then(function (r) { if (r && r.ok && r.settings) pagesBase = r.settings; return r; }));
      }
    }
    if (window.__svx) {
      var xs = window.__svx.save();
      if (xs === false) { saving = false; return; }
      tasks = tasks.concat(xs);
    }
    Promise.all(tasks).then(function (res) {
      saving = false;
      var failed = res.filter(function (r) { return !r || !r.ok; })[0];
      if (failed) { flash((failed && failed.message) || 'L’enregistrement a échoué. Vérifiez vos valeurs et réessayez.'); return; }
      if (lieu) { aidLieu = lieu; aidLieuBase = lieu; }
      applySv(res[0].settings, true);
      var c = comp();
      if (c) c.commitKeys(__SP0_KEYS__.concat(Object.keys(PUB)));
      if (window.__svx) window.__svx.after();
      setTimeout(function () { baseSig = sig(); checkDirty(); pageTags(); }, 0);
      flash('Services enregistrés. Le site est à jour.');
    }).catch(function () {
      saving = false;
      flash('Impossible de joindre le serveur. Vérifiez votre connexion et réessayez.');
    });
  }
  function undoAll() {
    if (!svBase) return;
    aidLieu = aidLieuBase;
    applySv(svBase, false);
    var c = comp();
    if (c) c.revertBase();
    if (window.__svx) window.__svx.undo();
    setTimeout(function () { checkDirty(); pageTags(); }, 0);
    flash('Changements annulés.');
  }

  window.__saServicesSave = saveAll;
  window.__saServicesUndo = undoAll;
  window.__saServicesOnSwitch = function () { pageTags(); checkDirty(); };

  function start() {
    if (started) return;
    started = true;
    document.addEventListener('click', onClick);
    document.addEventListener('input', onInput);
    document.addEventListener('change', onChange, true);
    document.addEventListener('change', onInput);
    Promise.all([
      api('/api/admin/settings/services'), api('/api/admin/settings/horaires'), api('/api/admin/settings/pages'), api('/api/admin/pages')
    ]).then(function (r) {
      pages = r[3] && r[3].ok ? (r[3].pages || []).filter(function (p) { return p.visibility !== 'draft'; }) : [];
      if (!(r[0] && r[0].ok && r[1] && r[1].ok)) {
        var w = getEl('sv-items');
        if (w) w.innerHTML = '<p class="hint" style="margin:0">Impossible de charger les réglages. Rechargez la page.</p>';
        flash('Impossible de charger les réglages. Rechargez la page.');
        return;
      }
      aidLieu = aidLieuBase = (r[1].settings.aid && r[1].settings.aid.lieu) || '';
      if (r[2] && r[2].ok && r[2].settings) {
        pagesBase = r[2].settings;
        var sw = {};
        Object.keys(PUB).forEach(function (k) { sw[k] = pagesBase[PUB[k]] !== false; });
        var c = comp();
        if (c) c.setSwitches(sw, true);
      }
      applySv(r[0].settings, true);
      setTimeout(function () { baseSig = sig(); checkDirty(); pageTags(); }, 0);
    }, function () { flash('Impossible de joindre le serveur. Rechargez la page.'); });
  }

  if (comp() && getEl('sv-items')) start();
  else window.addEventListener('sa-services-ready', start, { once: true });
})();
</script>
'''


def wire_panel():
    path = ROOT / 'SA-Services.dc.html'
    s, i, j, tpl = load(path)
    a0 = tpl.index('<div id="sp-0" class="sp">')
    h0 = tpl.index('<section', a0)
    a1 = tpl.index('<div id="sp-1" class="sp">')
    tpl = tpl[:h0] + SP0_SECTIONS + '</div>' + tpl[a1:]

    m = re.search(r'this\.base = (\{.*?\});', tpl)
    assert m, 'base du composant introuvable'
    old = json.loads(m.group(1))
    base = {}
    for k, v in old.items():
        if not k.startswith('pub_') or k in SP0_DEFAULTS:
            continue
        base[k] = v
        if k == 'pub_services':
            base.update(SP0_DEFAULTS)
    assert all(k in base for k in SP0_KEYS)
    comp = COMPONENT_SCRIPT.replace('__BASE__', json.dumps(base))
    tpl, n = re.subn(r'class Component extends DCLogic \{.*?\n\}', lambda _: comp, tpl, count=1, flags=re.S)
    assert n == 1, 'Component introuvable dans SA-Services.dc.html'

    sync = (SYNC_SCRIPT.replace('__SITE__', json.dumps(SITE_LINKS, ensure_ascii=False))
            .replace('__ICONS__', json.dumps(ICON_NAMES, ensure_ascii=False))
            .replace('__AUTRES__', json.dumps([list(x) for x in AUTRES], ensure_ascii=False))
            .replace('__EQUIP__', json.dumps([list(x) for x in EQUIP], ensure_ascii=False))
            .replace('__PUB__', json.dumps(PUB_PAGES))
            .replace('__SP0_KEYS__', json.dumps(SP0_KEYS)))
    tpl = re.sub(r'<script id="sa-services-sync">.*?</script>\s*', '', tpl, flags=re.S)
    k = tpl.rindex('</body>')
    tpl = tpl[:k] + sync + tpl[k:]
    save(path, s, i, j, tpl)
    print('SA-Services.dc.html : onglet Tous les services relié à la base')


# =====================================================================================
# 2. Page publique « Services »
# =====================================================================================

SERVICES_XVALS = r"""
  xvals() {
    /*ascil-services*/
    const PT = (typeof window !== 'undefined' && window.__ascilPrayer) || {};
    const V = PT.services || __DEFAULT__, H = PT.horaires || {};
    const pre = (typeof location !== 'undefined' && /\/(M-|T-)[^\/]*$/.exec(location.pathname)) ? /\/(M-|T-)[^\/]*$/.exec(location.pathname)[1] : '';
    const MAP = __URLMAP__;
    const href = (v) => (MAP[v] ? pre + MAP[v] : (/^(\/p\/|https?:\/\/)/i.test(v || '') ? v : ''));
    const PD = PT.today || {}, defs = PT.defaults || {};
    const hm = (v) => (typeof v === 'string' && /^\d\d:\d\d$/.test(v) ? v : '');
    const fajr = hm(PD.fajr) || hm(defs.fajr) || '06:30', icha = hm(PD.isha) || hm(defs.isha) || '19:00';
    let jum = hm(PD.jumuha) || '';
    const today = PT.date || '';
    if (Array.isArray(PT.days) && today) {
      const f = PT.days.find((d) => d.date >= today && new Date(d.date + 'T12:00:00Z').getUTCDay() === 5 && hm(d.jumuha));
      if (f) jum = f.jumuha;
    }
    jum = jum || hm(defs.jumuha) || '12:30';
    const lieu = (H.aid && H.aid.lieu) || 'Salle louée — 15 rue Frontenac';
    const cards = (V.items || []).filter((x) => x.on && x.titre).map((x) => {
      const lk = x.kind === 'prieres' || x.kind === 'libre' ? href(x.lien) : '';
      return { titre: x.titre, texte: x.texte || '', hasTexte: !!x.texte, saison: !!x.saison,
        i0: x.icone === 0, i1: x.icone === 1, i2: x.icone === 2, i3: x.icone === 3, i4: x.icone === 4,
        isPri: x.kind === 'prieres', isJum: x.kind === 'jumua', isAid: x.kind === 'aid', isLibre: x.kind === 'libre' && !!x.texte,
        fajr, icha, jumua: jum, lieu,
        hasZakat: x.kind === 'aid' && x.zakat != null && x.zakat > 0,
        zakat: (x.zakat || 0).toLocaleString('fr-CA') + ' $', zakatAnnee: x.zakatAnnee ? ' en ' + x.zakatAnnee : '',
        khutba: x.kind === 'jumua' && !!x.khutba, femmes: x.kind === 'jumua' && !!x.femmes,
        hasLines: x.kind === 'jumua' && (!!x.khutba || !!x.femmes),
        khHref: pre + 'N2-Khutba.dc.html', feHref: pre + 'N2-EspaceFemmes.dc.html',
        hasLien: !!lk, href: lk, lienTexte: x.lienTexte || 'En savoir plus' };
    });
    const A = V.autres || {}, E = V.equipements || {}, Q = V.question || {};
    const qHref = href(Q.lien) || pre + 'Contact.dc.html';
    return {
      svCards: cards, svMain: cards.length > 0 || Q.on !== false, svQuestion: Q.on !== false, svQHref: qHref,
      svAutres: A.on !== false,
      svA_cours: A.cours !== false, svA_mariages: A.mariages !== false, svA_funerailles: A.funerailles !== false,
      svA_aide: A.aide !== false, svA_femmes: A.femmes !== false, svA_khutba: A.khutba !== false,
      svEquip: E.on !== false && (E.fauteuil !== false || E.ablutions !== false || E.parking !== false || !!E.femmes),
      svE_fauteuil: E.fauteuil !== false, svE_ablutions: E.ablutions !== false, svE_parking: E.parking !== false, svE_femmes: !!E.femmes,
    };
  }
"""

SERVICES_DEFAULT = {
    'items': [
        {'kind': 'prieres', 'titre': 'Les cinq prières quotidiennes', 'texte': 'Au 34, 37e Avenue, tous les jours.', 'icone': 0, 'saison': False,
         'lien': 'Page : Horaires du mois', 'lienTexte': 'Tableau complet des horaires', 'khutba': False, 'femmes': False, 'zakat': None, 'zakatAnnee': '', 'on': True},
        {'kind': 'jumua', 'titre': 'La prière du vendredi (Jumu’a)', 'texte': 'Khutba suivie de la prière.', 'icone': 1, 'saison': False,
         'lien': '', 'lienTexte': '', 'khutba': True, 'femmes': True, 'zakat': None, 'zakatAnnee': '', 'on': True},
        {'kind': 'libre', 'titre': 'Ramadan : Iftar et Tarawih', 'texte': 'Proposés pendant le mois de Ramadan, avec des dates publiées chaque année dès l’annonce officielle.',
         'icone': 2, 'saison': True, 'lien': '', 'lienTexte': '', 'khutba': False, 'femmes': False, 'zakat': None, 'zakatAnnee': '', 'on': True},
        {'kind': 'aid', 'titre': 'Les prières de l’Aïd', 'texte': '', 'icone': 3, 'saison': True, 'lien': '', 'lienTexte': '',
         'khutba': False, 'femmes': False, 'zakat': 15, 'zakatAnnee': '2025', 'on': True},
        {'kind': 'libre', 'titre': 'Solidarité et événements caritatifs',
         'texte': 'Exemple : la journée de parrainage d’orphelins avec l’organisme Soleil des Orphelins, le 25 avril 2026 au 34, 37e Avenue.',
         'icone': 4, 'saison': False, 'lien': 'Page : Événements', 'lienTexte': 'Voir les événements', 'khutba': False, 'femmes': False,
         'zakat': None, 'zakatAnnee': '', 'on': True},
    ],
    'autres': {'on': True, 'cours': True, 'mariages': True, 'funerailles': True, 'aide': True, 'femmes': True, 'khutba': True},
    'equipements': {'on': True, 'fauteuil': True, 'ablutions': True, 'parking': True, 'femmes': False},
    'question': {'on': True, 'lien': 'Page : Contact'},
}

FEMMES_ICON = ('<svg class="icon" aria-hidden="true" width="30" height="30" sc-camel-view-box="0 0 24 24" fill="none" stroke="currentColor" '
               'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="width:30px;height:30px">'
               '<circle cx="12" cy="7" r="3.2"></circle><path d="M5.5 20a6.5 6.5 0 0 1 13 0"></path></svg>')


def patch_services(tpl):
    la = tpl.index('<script type="text/x-dc"')
    lb = tpl.index('</script>', la)
    code = tpl[la:lb]
    if '/*ascil-services*/' not in code:
        assert 'xvals() {' not in code
        xv = (SERVICES_XVALS.replace('__DEFAULT__', json.dumps(SERVICES_DEFAULT, ensure_ascii=False))
              .replace('__URLMAP__', json.dumps(URL_MAP, ensure_ascii=False)))
        code = resub(code, r'\n  renderVals\(\) \{', lambda x: xv.rstrip('\n') + x.group(0))
        tpl = tpl[:la] + code + tpl[lb:]
    if '{{svCards}}' in tpl:
        return tpl

    a = tpl.index('<main'); b = tpl.index('</main>')
    m = tpl[a:b]

    # 1. Cartes de services : une liste, icône choisie parmi les 5 d'origine.
    sa = m.index('<section class="sec" aria-label="Services confirmés">')
    ga = m.index('<div class="wrap g2">', sa) + len('<div class="wrap g2">')
    qa = m.index('<div class="card sand"', ga)
    first = m[ga:qa]
    icons = re.findall(r'<span style="display:flex;width:52px;height:52px;[^"]*">(<svg.*?</svg>)</span>', first, flags=re.S)
    assert len(icons) == 5, f'{len(icons)} icônes de services au lieu de 5'
    arrow = re.search(r'<a class="link" href="(?:[MT]-)?Horaires\.dc\.html"[^>]*>Tableau complet des horaires (<svg.*?</svg>)</a>', first, flags=re.S).group(1)
    pill = '<span class="pill" style="background:#F3EAD8;color:#7A5A1E">Saisonnier</span>'
    ic = ''.join(f'<sc-if value="{{{{c.i{k}}}}}" hint-placeholder-val="{{{{ {str(k == 0).lower()} }}}}">{svg}</sc-if>' for k, svg in enumerate(icons))
    cards = ('<sc-for list="{{svCards}}" as="c" hint-placeholder-count="5"><div class="card">'
             '<div style="display:flex;justify-content:space-between;align-items:flex-start;gap:12px">'
             f'<span style="display:flex;width:52px;height:52px;border-radius:14px;background:#F3EAD8;align-items:center;justify-content:center;color:#0E4D3C">{ic}</span>'
             + sc_if('c.saison', pill, 'false') + '</div>'
             '<p class="h3" style="margin-top:18px">{{c.titre}}</p>'
             + sc_if('c.isPri', '<p style="margin:10px 0 0">{{c.texte}} Fajr à <strong class="tnum">{{c.fajr}}</strong>, Icha à <strong class="tnum">{{c.icha}}</strong>.</p>')
             + sc_if('c.isJum', '<p style="margin:10px 0 0">Chaque vendredi à <strong class="tnum">{{c.jumua}}</strong>. {{c.texte}}</p>', 'false')
             + sc_if('c.isAid', '<p style="margin:10px 0 0">Aïd al-Fitr et Aïd al-Adha, lieu : <strong>{{c.lieu}}</strong>.'
                     + sc_if('c.hasZakat', ' Zakat al-Fitr rappelée : {{c.zakat}} par personne{{c.zakatAnnee}}.', 'false')
                     + ' {{c.texte}}</p>', 'false')
             + sc_if('c.isLibre', '<p style="margin:10px 0 0;white-space:pre-line">{{c.texte}}</p>', 'false')
             + sc_if('c.hasLines', '<div style="display:flex;flex-direction:column;gap:8px;margin-top:14px">'
                     + sc_if('c.khutba', f'<a class="link" href="{{{{c.khHref}}}}">Langue de la khutba de ce vendredi {arrow}</a>', 'false')
                     + sc_if('c.femmes', f'<a class="link" href="{{{{c.feHref}}}}">Espace pour les femmes {arrow}</a>', 'false')
                     + '</div>', 'false')
             + sc_if('c.hasLien', f'<a class="link" href="{{{{c.href}}}}" style="margin-top:14px">{{{{c.lienTexte}}}} {arrow}</a>', 'false')
             + '</div></sc-for>')
    m = m[:ga] + cards + m[qa:]

    # 2. Bloc « Une question ? »
    qa = m.index('<div class="card sand"', ga)
    qb = m.index('</div>', m.index('Nous écrire</a>', qa)) + len('</div>')
    q = resub(m[qa:qb], r'href="(?:[MT]-)?Contact\.dc\.html"', 'href="{{svQHref}}"')
    m = m[:qa] + sc_if('svQuestion', q) + m[qb:]
    sb = m.index('</section>', sa) + len('</section>')
    m = m[:sa] + sc_if('svMain', m[sa:sb]) + m[sb:]

    # 3. Les autres services : une carte par page, chacune avec son interrupteur.
    for key, page, _, _ in AUTRES:
        ca = re.search(r'<a class="card" href="(?:[MT]-)?' + re.escape(page) + r'\.dc\.html"', m).start()
        cb = m.index('</a>', m.index('<span class="link">', ca)) + len('</a>')
        m = m[:ca] + sc_if(f'svA_{key}', m[ca:cb]) + m[cb:]
    oa = m.index('<section class="sand" style="border-top:1px solid #E4D9C0"><div class="wrap sec"><p class="eyebrow">Services</p>')
    ob = m.index('</section>', oa) + len('</section>')
    m = m[:oa] + sc_if('svAutres', m[oa:ob]) + m[ob:]

    # 4. Équipements
    ea = m.index('<section class="sand" aria-labelledby="sp-t"')
    eb = m.index('</section>', ea) + len('</section>')
    e = m[ea:eb]
    lis = re.findall(r'<li class="card".*?</li>', e, flags=re.S)
    assert len(lis) == 3, 'équipements introuvables'
    for li, key in zip(lis, ['fauteuil', 'ablutions', 'parking']):
        e = e.replace(li, sc_if(f'svE_{key}', li))
    femmes = ('<li class="card" style="display:flex;gap:14px;align-items:center"><span style="color:#0E4D3C">' + FEMMES_ICON
              + '</span><span style="font-weight:600">Espace réservé aux femmes</span></li>')
    e = rep(e, '\n  </ul>', sc_if('svE_femmes', femmes, 'false') + '\n  </ul>')
    m = m[:ea] + sc_if('svEquip', e) + m[eb:]

    assert '06:30' not in m and '19:00' not in m and '12:30' not in m and 'à confirmer' not in m
    return tpl[:a] + m + tpl[b:]


def wire_public():
    for prefix in ('', 'M-', 'T-'):
        path = ROOT / f'{prefix}Services.dc.html'
        s, i, j, tpl = load(path)
        save(path, s, i, j, patch_services(tpl))
    print('3 pages publiques Services (PC, M-, T-) reliées aux réglages')


if __name__ == '__main__':
    wire_panel()
    wire_public()
