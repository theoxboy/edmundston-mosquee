"""Branche « À propos » (étape A) : panneau SA-APropos et pages publiques À propos et Campagne en direct.

Panneau SA-APropos.dc.html :
- Onglet « L’association » (clé apropos) : présentation, valeurs, histoire, projet (liens des 2 boutons),
  équipe (photos réduites dans le navigateur, accord écrit), chiffres. Listes : ajouter, monter,
  descendre, supprimer, afficher ou masquer chaque ligne.
- Onglet « Campagne en direct » (clé campagne + objectif et récolté de home.campagne, communs à
  l’accueil) : donateurs, mise à jour automatique depuis la table donations, étapes, dons par
  semaine, derniers dons.
- Interrupteurs « Page publiée » reliés à la clé pages (pg_apropos, pg_campagne).

Pages publiques (versions PC, M- et T-) :
- APropos : chaque bloc suit les réglages ; l’objectif du projet vient de la campagne.
- N3-Campagne : montants, étapes, semaines et derniers dons lus sur /api/campagne
  (rafraîchis chaque minute par le script #ascil-prayer-live), simulation et mentions
  « [EXEMPLE À MODIFIER] » retirées.

Ordre : après wire_prieres.py (qui pose le script #ascil-prayer-live et l’écoute « ascil:prayer »),
avant fix_inputs.py. Idempotent.
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


# Liens « Page : … » proposés dans le panneau, et fichier public de chacun.
SITE_LINKS = [
    'Page : Faire un don', 'Page : Campagne en direct', 'Page : Horaires du mois', 'Page : Événements',
    'Page : Inscription aux événements', 'Page : Contact', 'Page : À propos', 'Page : Services', 'Page : Ressources',
]
URL_MAP = {
    'Page : Horaires du mois': 'Horaires.dc.html', 'Page : Rappel de prière': 'N3-Rappel.dc.html',
    'Page : Langue de la khutba': 'N2-Khutba.dc.html', 'Page : Faire un don': 'Dons.dc.html',
    'Page : Campagne en direct': 'N3-Campagne.dc.html', 'Page : Événements': 'Evenements.dc.html',
    'Page : Inscription aux événements': 'N3-Inscription.dc.html', 'Page : Calendrier du mois': 'N3-Calendrier.dc.html',
    'Page : Contact': 'Contact.dc.html', 'Page : Ressources': 'Ressources.dc.html', 'Page : À propos': 'APropos.dc.html',
    'Page : Services': 'Services.dc.html',
}

# Contenu d’origine de la page publique : affiché tant que les réglages ne sont pas arrivés
# (et si le serveur ne répond pas). Identique à DEFAULT_SETTINGS.apropos (functions/_lib/settings.js).
APROPOS_DEFAULT = {
    'presentation': {'on': True, 'texte': 'L’ASCIL rassemble les musulmanes et les musulmans de Edmundston et des environs. Elle tient un lieu de prière au 34, 37e Avenue, organise la prière du vendredi, les prières de l’Aïd et des activités de solidarité, et accueille les nouveaux arrivants dans la région.'},
    'valeurs': {'on': True, 'items': [
        {'titre': 'Prier ensemble', 'texte': 'Les cinq prières quotidiennes et la prière du vendredi (Jumu’a).', 'on': True},
        {'titre': 'Se soutenir', 'texte': 'Accueil, solidarité et événements caritatifs, comme l’activité avec Soleil des Orphelins d’avril 2026.', 'on': True},
        {'titre': 'S’ancrer ici', 'texte': 'Une communauté du Bas-Saint-Laurent, membre de la Table de concertation des organisations musulmanes du Québec (TCOM).', 'on': True},
    ]},
    'histoire': {'on': True, 'items': [
        {'date': '', 'titre': 'Fondation de l’association', 'on': True},
        {'date': '', 'titre': 'Installation au 34, 37e Avenue', 'on': True},
        {'date': '2026-10-01', 'titre': 'Lancement du projet de nouveau lieu', 'on': True},
    ]},
    'projet': {'on': True, 'btnSoutenir': 'Page : Faire un don', 'btnSuivre': 'Page : Campagne en direct'},
    'equipe': {'on': False, 'accord': False, 'items': []},
    'chiffres': {'on': True, 'items': [
        {'valeur': '≈ 1 100', 'libelle': 'abonnés à la page Facebook de l’ASCIL', 'source': 'page Facebook de l’ASCIL', 'on': True},
        {'valeur': '≈ 45', 'libelle': 'pays d’origine des personnes immigrantes de la région', 'source': 'données de la MRC de Edmundston', 'on': True},
        {'valeur': '2e', 'libelle': 'le Maghreb, région d’origine la mieux représentée après la France', 'source': 'données de la MRC de Edmundston', 'on': True},
    ]},
}


# =====================================================================================
# 1. Panneau SA-APropos
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


def add_btn(lst, label):
    return f'<button type="button" class="btn btn-line" data-ap-add="{lst}" style="align-self:flex-start">+ {label}</button>'


def money_input(fid, label, extra=''):
    return (f'<div class="fld"><label class="lbl" for="{fid}">{label}</label><div style="position:relative">'
            f'<input class="in tnum" id="{fid}" type="text" inputmode="numeric" autocomplete="off" style="padding-right:32px"{extra}>'
            '<span aria-hidden="true" style="position:absolute;right:12px;top:50%;transform:translateY(-50%);color:#4F5E57;font-weight:600">$</span>'
            '</div></div>')


def switch_row(key, label, hint=''):
    h = f'<p class="hint">{hint}</p>' if hint else ''
    return (f'<div><div class="row"><div><div style="font-weight:600;font-size:14px">{label}</div>{h}</div>'
            f'<button type="button" class="sw" role="switch" aria-label="{label}" aria-checked="{{{{s.{key}.c}}}}" '
            f'sc-camel-on-click="{{{{s.{key}.t}}}}"></button></div></div>')


def link_select(fid, label):
    opts = ''.join(f'<option>{x}</option>' for x in SITE_LINKS)
    return f'<div class="fld"><label class="lbl" for="{fid}">{label}</label><sc-raw-select class="in" id="{fid}">{opts}</sc-raw-select></div>'


SP0_SECTIONS = (
    card(1, 'ap_pres', 'Présentation', '',
         '<div class="fld"><label class="lbl" for="ap-pres">Texte de présentation</label>'
         '<textarea class="in" id="ap-pres" rows="5" maxlength="1500"></textarea>'
         '<p class="hint">Une ligne vide sépare deux paragraphes.</p></div>')
    + card(2, 'ap_valeurs', 'Mission et valeurs', 'Les engagements de l’association, 6 au plus.',
           '<div id="ap-valeurs"></div>' + add_btn('valeurs', 'Ajouter une valeur'))
    + card(3, 'ap_hist', 'Notre histoire', 'Une étape sans date reste masquée. Le site les range par date et montre le mois et l’année.',
           '<div id="ap-histoire"></div>' + add_btn('histoire', 'Ajouter une étape'))
    + card(4, 'ap_projet', 'Le projet de nouveau lieu', 'Le montant affiché est l’objectif de l’onglet Campagne en direct.',
           '<div class="g2">' + link_select('f8', 'Bouton « Soutenir le projet »') + link_select('f9', 'Lien « Suivre en direct »') + '</div>')
    + card(5, 'ap_equipe', 'L’équipe', 'Publiée seulement avec l’accord écrit. Une personne sans nom n’est pas affichée.',
           '<div id="ap-equipe"></div>' + add_btn('equipe', 'Ajouter une personne')
           + switch_row('ap_accord', 'Accord écrit reçu', 'Obligatoire avant de publier ce bloc.'))
    + card(6, 'ap_chiffres', 'La communauté en chiffres', 'Des faits publics, avec leur source.',
           '<div id="ap-chiffres"></div>' + add_btn('chiffres', 'Ajouter un chiffre'))
)

SP1_SECTIONS = (
    card(1, None, 'Montants', 'Objectif et montant récolté sont communs à l’accueil, à la page À propos et à cette page.',
         '<div class="g3">' + money_input('f23', 'Objectif') + money_input('f24', 'Montant récolté')
         + '<div class="fld"><label class="lbl" for="f25">Nombre de donateurs</label>'
           '<input class="in tnum" id="f25" type="text" inputmode="numeric" autocomplete="off"></div></div>'
         + switch_row('cp_auto', 'Mise à jour automatique',
                      'Le montant récolté, le nombre de donateurs, les semaines et les derniers dons sont alors calculés à partir des dons enregistrés.')
         + '<p class="hint" id="cp-auto-info" aria-live="polite" style="margin:0"></p>')
    + card(2, 'cp_etapes', 'Étapes du projet', 'Une étape est cochée sur le site quand le montant récolté atteint son seuil. Elles sont rangées par seuil.',
           '<div id="cp-etapes"></div>' + add_btn('etapes', 'Ajouter une étape'))
    + card(3, 'cp_semaines', 'Dons par semaine', 'Graphique en barres. Semaine 1 = la plus ancienne. Sans montant, le graphique reste masqué.',
           '<div class="g4" id="cp-semaines"></div>'
           '<div class="g2"><div class="fld"><label class="lbl" for="f32">Nombre de semaines affichées</label>'
           '<sc-raw-select class="in" id="f32"><option value="4">4</option><option value="8">8</option><option value="12">12</option></sc-raw-select></div></div>')
    + card(4, 'cp_feed', 'Derniers dons', 'Seulement en mise à jour automatique : la liste vient des dons enregistrés.',
           '<div class="g2"><div class="fld"><label class="lbl" for="f33">Nombre affiché</label>'
           '<sc-raw-select class="in" id="f33"><option value="3">3</option><option value="5">5</option><option value="10">10</option></sc-raw-select></div>'
           '<div class="fld"><label class="lbl" for="f34">Nom affiché</label><sc-raw-select class="in" id="f34">'
           '<option value="prenom">Prénom seulement</option><option value="initiales">Initiales</option>'
           '<option value="anonyme">Toujours « Anonyme »</option></sc-raw-select></div></div>'
           + switch_row('cp_montant', 'Afficher le montant de chaque don'))
)

WARN_OLD = 'Petite app : elle fonctionne dans le navigateur des visiteurs, sans compte. Publiez-la seulement quand les données sont prêtes.'
WARN_NEW = 'Les montants de cet onglet s’affichent sur l’accueil, la page À propos et la page Campagne en direct. Publiez la page quand les chiffres sont prêts.'

COMPONENT_SCRIPT = r"""class Component extends DCLogic {
  constructor(props) {
    super(props);
    this.base = {"pub_apropos": true, "ap_pres": true, "ap_valeurs": true, "ap_hist": true, "ap_projet": true, "ap_equipe": false, "ap_accord": false, "ap_chiffres": true, "pub_campagne": false, "cp_auto": false, "cp_etapes": true, "cp_semaines": true, "cp_feed": true, "cp_montant": true};
    this.pubKeys = ["pub_apropos", "pub_campagne"];
    this.state = { on: Object.assign({}, this.base), extDirty: false, toast: '' };
    window.__saApropos = this;
  }
  componentDidMount() {
    window.dispatchEvent(new Event('sa-apropos-ready'));
  }
  componentWillUnmount() {
    clearTimeout(this.tt);
    if (window.__saApropos === this) window.__saApropos = null;
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
  commitBase() {
    this.base = Object.assign({}, this.state.on);
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
            if (window.__saAproposOnSwitch) window.__saAproposOnSwitch(k, next[k]);
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
      save: () => { if (window.__saAproposSave) window.__saAproposSave(); },
      undo: () => { if (window.__saAproposUndo) window.__saAproposUndo(); },
      toast: this.state.toast
    };
  }
}"""

SYNC_SCRIPT = r'''<script id="sa-apropos-sync">
(function () {
  var SITE = __SITE__;
  var EXT = 'Lien externe…';
  var PHOTO_MAX = 100000;
  var ICON = {
    up: '<svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 19V5M5 12l7-7 7 7"></path></svg>',
    down: '<svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5v14M19 12l-7 7-7-7"></path></svg>',
    del: '<svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3"></path></svg>'
  };
  // Listes éditables : champs, ligne vide, titre affiché dans l'en-tête de la ligne, étiquette d'alerte.
  var LISTS = {
    valeurs: { max: 6, grid: '', noun: 'valeur',
      blank: function () { return { titre: '', texte: '', on: true }; },
      title: function (x) { return x.titre || 'Nouvelle valeur'; },
      tag: function (x) { return x.titre ? '' : 'Titre à écrire'; },
      fields: [['titre', 'Titre', 'text', 80], ['texte', 'Texte', 'area', 300]] },
    histoire: { max: 12, grid: 'g2', noun: 'étape', fixed: true,
      blank: function () { return { date: '', titre: '', on: true }; },
      title: function (x) { return x.titre || 'Nouvelle étape'; },
      tag: function (x) { return x.date ? '' : 'Date à fournir, masquée'; },
      fields: [['date', 'Date', 'date'], ['titre', 'Titre', 'text', 120]] },
    equipe: { max: 8, grid: 'g2', noun: 'personne',
      blank: function () { return { nom: '', role: '', photo: '', on: true }; },
      title: function (x) { return x.nom || x.role || 'Nouvelle personne'; },
      tag: function (x) { return x.nom ? '' : 'Nom à fournir, masquée'; },
      fields: [['nom', 'Nom', 'text', 80], ['role', 'Rôle', 'text', 80]], photo: true },
    chiffres: { max: 6, grid: 'g3', noun: 'chiffre',
      blank: function () { return { valeur: '', libelle: '', source: '', on: true }; },
      title: function (x) { return ((x.valeur || '') + ' ' + (x.libelle || '')).trim() || 'Nouveau chiffre'; },
      tag: function () { return ''; },
      fields: [['valeur', 'Valeur', 'text', 20], ['libelle', 'Libellé', 'text', 160], ['source', 'Source', 'text', 120]] },
    etapes: { max: 8, grid: 'g2', noun: 'étape', fixed: true,
      blank: function () { return { seuil: 100, libelle: '', on: true }; },
      title: function (x) { return (x.seuil === '' ? '…' : x.seuil) + ' % — ' + (x.libelle || 'Nouvelle étape'); },
      tag: function () { return ''; },
      fields: [['seuil', 'Seuil atteint (%)', 'pct'], ['libelle', 'Libellé', 'text', 120]] }
  };
  var WRAP = { valeurs: 'ap-valeurs', histoire: 'ap-histoire', equipe: 'ap-equipe', chiffres: 'ap-chiffres', etapes: 'cp-etapes' };
  var AP_SW = { ap_pres: 'presentation', ap_valeurs: 'valeurs', ap_hist: 'histoire', ap_projet: 'projet', ap_equipe: 'equipe', ap_chiffres: 'chiffres' };

  var D = { valeurs: [], histoire: [], equipe: [], chiffres: [], etapes: [] };
  var weeks = [];
  var apBase = null, cpBase = null, homeMoney = null, pagesBase = null, baseSig = '';
  var pages = [], prevLink = {}, stats = null;
  var saving = false, started = false;

  function comp() { return window.__saApropos; }
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
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; });
  }
  function parseAmount(v) {
    var t = String(v == null ? '' : v).replace(/[\s  $]/g, '').replace(',', '.');
    if (t === '') return null;
    var n = Number(t);
    return isFinite(n) && n >= 0 ? Math.round(n) : null;
  }
  function fmt(n) { return Number(n || 0).toLocaleString('fr-CA'); }
  function swOn() { var c = comp(); return (c && c.state && c.state.on) || {}; }

  // ---------- Listes ----------
  function fieldHtml(l, i, f, x) {
    var id = 'ap-' + l + '-' + i + '-' + f[0], v = x[f[0]];
    var attrs = ' id="' + id + '" data-l="' + l + '" data-i="' + i + '" data-f="' + f[0] + '"';
    var lab = '<label class="lbl" for="' + id + '">' + f[1] + '</label>';
    if (f[2] === 'area') return '<div class="fld">' + lab + '<textarea class="in" rows="2" maxlength="' + f[3] + '"' + attrs + '>' + esc(v) + '</textarea></div>';
    if (f[2] === 'date') return '<div class="fld">' + lab + '<input class="in tnum" type="date"' + attrs + ' value="' + esc(v) + '"></div>';
    if (f[2] === 'pct') return '<div class="fld">' + lab + '<input class="in tnum" type="number" min="0" max="100" step="1" inputmode="numeric"' + attrs + ' value="' + esc(v) + '"></div>';
    return '<div class="fld">' + lab + '<input class="in" type="text" maxlength="' + f[3] + '"' + attrs + ' value="' + esc(v) + '"></div>';
  }
  function photoHtml(i, x) {
    var has = !!x.photo;
    return '<div class="fld"><span class="lbl">Photo (facultative)</span>' +
      '<div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;min-height:44px;padding:6px 6px 6px 12px;border:1.5px dashed #CDBF9C;border-radius:10px;background:#fff">' +
      (has ? '<img src="' + x.photo + '" alt="" style="width:44px;height:44px;border-radius:50%;object-fit:cover;flex:none">' : '') +
      '<span style="flex:1;min-width:120px;font-size:14px;color:#4F5E57">' + (has ? 'Photo ajoutée, réduite pour le site' : 'Aucune photo') + '</span>' +
      '<button type="button" class="btn btn-line" data-l="equipe" data-i="' + i + '" data-act="photo" style="min-height:36px">' + (has ? 'Changer la photo' : 'Choisir une photo') + '</button>' +
      (has ? '<button type="button" class="btn btn-line" data-l="equipe" data-i="' + i + '" data-act="nophoto" style="min-height:36px">Retirer</button>' : '') +
      '</div></div>';
  }
  function renderList(l) {
    var wrap = getEl(WRAP[l]), L = LISTS[l], list = D[l];
    if (!wrap) return;
    if (!list.length) {
      wrap.innerHTML = '<p class="hint" style="margin:0">Aucune ' + L.noun + ' pour l’instant. Ce bloc reste masqué sur le site tant que la liste est vide.</p>';
      return;
    }
    wrap.innerHTML = '<ol style="list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:10px">' + list.map(function (x, i) {
      var t = L.title(x), tag = L.tag(x), n = list.length;
      var move = L.fixed ? '' :
        '<button type="button" class="ico" data-l="' + l + '" data-i="' + i + '" data-act="up" aria-label="Monter ' + esc(t) + '"' + (i === 0 ? ' disabled' : '') + '>' + ICON.up + '</button>' +
        '<button type="button" class="ico" data-l="' + l + '" data-i="' + i + '" data-act="down" aria-label="Descendre ' + esc(t) + '"' + (i === n - 1 ? ' disabled' : '') + '>' + ICON.down + '</button>';
      var fields = L.fields.map(function (f) { return fieldHtml(l, i, f, x); }).join('');
      return '<li style="border:1px solid #E4D9C0;border-radius:14px;background:#fff">' +
        '<div style="display:flex;align-items:center;gap:10px;padding:10px 10px 10px 14px;flex-wrap:wrap;border-bottom:1px solid #F3EAD8">' +
        '<span class="pos">' + (i + 1) + '</span>' +
        '<span data-title style="flex:1;min-width:150px;font-weight:700;color:#0E4D3C;overflow-wrap:anywhere">' + esc(t) + '</span>' +
        '<span class="tag" data-tag style="background:#F3EAD8;color:#7A5A1E' + (tag ? '' : ';display:none') + '">' + esc(tag) + '</span>' +
        move +
        '<button type="button" class="ico" data-l="' + l + '" data-i="' + i + '" data-act="del" aria-label="Supprimer ' + esc(t) + '">' + ICON.del + '</button>' +
        '<button type="button" class="sw" role="switch" data-l="' + l + '" data-i="' + i + '" data-act="on" aria-label="Afficher ' + esc(t) + '" aria-checked="' + (x.on ? 'true' : 'false') + '"></button>' +
        '</div><div class="li-b" style="opacity:' + (x.on ? 1 : 0.5) + '">' +
        (L.grid ? '<div class="' + L.grid + '">' + fields + '</div>' : fields) +
        (L.photo ? photoHtml(i, x) : '') +
        '</div></li>';
    }).join('') + '</ol>';
  }
  function renderAll() { Object.keys(WRAP).forEach(renderList); }

  function renderWeeks() {
    var wrap = getEl('cp-semaines');
    if (!wrap) return;
    var n = parseInt(getVal('f32'), 10) || 8, auto = !!swOn().cp_auto, h = '';
    while (weeks.length < 12) weeks.push('');
    for (var i = 0; i < n; i++) {
      h += '<div class="fld"><label class="lbl" for="cp-w-' + i + '">Semaine ' + (i + 1) + '</label><div style="position:relative">' +
        '<input class="in tnum" id="cp-w-' + i + '" type="text" inputmode="numeric" autocomplete="off" data-w="' + i + '" value="' + esc(weeks[i]) + '" style="padding-right:32px"' + (auto ? ' disabled' : '') + '>' +
        '<span aria-hidden="true" style="position:absolute;right:12px;top:50%;transform:translateY(-50%);color:#4F5E57;font-weight:600">$</span></div></div>';
    }
    wrap.innerHTML = h;
  }

  function applyAutoUi() {
    var auto = !!swOn().cp_auto;
    ['f24', 'f25'].forEach(function (id) { var e = getEl(id); if (e) e.disabled = auto; });
    var ws = document.querySelectorAll('#cp-semaines input');
    for (var i = 0; i < ws.length; i++) ws[i].disabled = auto;
    var info = getEl('cp-auto-info');
    if (info) {
      var n = stats ? stats.donationsCount : null, sum = stats ? stats.donationsSum : null;
      var base = n == null ? '' : 'Dons enregistrés dans la base : ' + fmt(n) + (n > 1 ? ' dons' : ' don') + ', ' + fmt(sum) + ' $.';
      info.textContent = auto
        ? (base ? base + ' Le site affiche ces montants à la place des champs Montant récolté, Donateurs et Semaines.' : 'Le site calcule les montants à partir des dons enregistrés.')
        : (base ? base + ' Mode manuel : le site affiche les montants saisis ici.' : '');
    }
  }

  // ---------- Liens des boutons du projet ----------
  function addOpt(sel, value, text) {
    for (var i = 0; i < sel.options.length; i++) if (sel.options[i].value === value) return;
    var o = document.createElement('option');
    o.value = value; o.textContent = text;
    var ext = null;
    for (var j = 0; j < sel.options.length; j++) if (sel.options[j].value === EXT) ext = sel.options[j];
    sel.insertBefore(o, ext);
  }
  function fillLinks(id) {
    var sel = getEl(id);
    if (!sel) return;
    sel.innerHTML = '';
    SITE.forEach(function (v) { addOpt(sel, v, v); });
    pages.forEach(function (p) { addOpt(sel, p.url, 'Ma page : ' + p.title); });
    addOpt(sel, EXT, EXT);
  }
  function setLink(id, v) {
    var sel = getEl(id);
    if (!sel) return;
    if (v && !Array.prototype.some.call(sel.options, function (o) { return o.value === v; })) {
      if (/^\/p\//.test(v)) addOpt(sel, v, 'Ma page : ' + v + ' (non publiée ou supprimée)');
      else if (/^https?:\/\//i.test(v)) addOpt(sel, v, 'Lien externe : ' + v);
      else addOpt(sel, v, v);
    }
    sel.value = v || SITE[0];
    prevLink[id] = sel.value;
  }

  // ---------- Lecture / application ----------
  function cleanItem(l, x) {
    if (l === 'etapes') {
      var s = parseInt(x.seuil, 10);
      return { seuil: isFinite(s) ? Math.max(0, Math.min(100, s)) : 0, libelle: String(x.libelle || '').trim(), on: !!x.on };
    }
    var o = {};
    Object.keys(LISTS[l].blank()).forEach(function (k) { o[k] = k === 'on' ? !!x.on : String(x[k] == null ? '' : x[k]).trim(); });
    return o;
  }
  // ignoreSw : signature des champs seulement (les interrupteurs sont suivis par le composant).
  function readAp(ignoreSw) {
    var on = ignoreSw ? {} : swOn();
    var b = function (k) { return ignoreSw ? true : !!on[k]; };
    return {
      presentation: { on: b('ap_pres'), texte: (getEl('ap-pres') ? getEl('ap-pres').value : '').trim() },
      valeurs: { on: b('ap_valeurs'), items: D.valeurs.map(function (x) { return cleanItem('valeurs', x); }) },
      histoire: { on: b('ap_hist'), items: D.histoire.map(function (x) { return cleanItem('histoire', x); }) },
      projet: { on: b('ap_projet'), btnSoutenir: getVal('f8'), btnSuivre: getVal('f9') },
      equipe: { on: b('ap_equipe'), accord: b('ap_accord'), items: D.equipe.map(function (x) { var o = cleanItem('equipe', x); o.photo = x.photo || ''; return o; }) },
      chiffres: { on: b('ap_chiffres'), items: D.chiffres.map(function (x) { return cleanItem('chiffres', x); }) }
    };
  }
  function readCp(ignoreSw) {
    var on = ignoreSw ? {} : swOn();
    var b = function (k) { return ignoreSw ? true : !!on[k]; };
    var vals = weeks.slice(0, 12).map(function (v) { return parseAmount(v) || 0; });
    while (vals.length && !vals[vals.length - 1]) vals.pop();
    return {
      donateurs: parseAmount(getVal('f25')) || 0,
      auto: b('cp_auto'),
      etapes: { on: b('cp_etapes'), items: D.etapes.map(function (x) { return cleanItem('etapes', x); }) },
      semaines: { on: b('cp_semaines'), nombre: parseInt(getVal('f32'), 10) || 8, valeurs: vals },
      derniers: { on: b('cp_feed'), nombre: parseInt(getVal('f33'), 10) || 5, nom: getVal('f34') || 'prenom', montant: b('cp_montant') }
    };
  }
  function sig() { return JSON.stringify([readAp(true), readCp(true), getVal('f23'), getVal('f24')]); }
  function checkDirty() { var c = comp(); if (c && baseSig) c.setExtDirty(sig() !== baseSig); }

  function applyAp(a, asBase) {
    if (asBase) apBase = clone(a);
    setVal('ap-pres', a.presentation.texte);
    ['valeurs', 'histoire', 'equipe', 'chiffres'].forEach(function (l) { D[l] = clone(a[l].items); });
    setLink('f8', a.projet.btnSoutenir);
    setLink('f9', a.projet.btnSuivre);
    var c = comp();
    if (c) c.setSwitches({ ap_pres: a.presentation.on, ap_valeurs: a.valeurs.on, ap_hist: a.histoire.on, ap_projet: a.projet.on,
      ap_equipe: a.equipe.on, ap_accord: a.equipe.accord, ap_chiffres: a.chiffres.on }, asBase);
    renderAll();
  }
  function applyCp(k, asBase) {
    if (asBase) cpBase = clone(k);
    setVal('f25', k.donateurs ? fmt(k.donateurs) : '');
    D.etapes = clone(k.etapes.items);
    weeks = k.semaines.valeurs.map(function (v) { return fmt(v); });
    setVal('f32', String(k.semaines.nombre));
    setVal('f33', String(k.derniers.nombre));
    setVal('f34', k.derniers.nom);
    var c = comp();
    if (c) c.setSwitches({ cp_auto: k.auto, cp_etapes: k.etapes.on, cp_semaines: k.semaines.on, cp_feed: k.derniers.on, cp_montant: k.derniers.montant }, asBase);
    renderList('etapes');
    renderWeeks();
    setTimeout(applyAutoUi, 0);
  }
  function applyMoney(m) {
    homeMoney = { objectif: m.objectif, recolte: m.recolte };
    setVal('f23', fmt(m.objectif));
    setVal('f24', fmt(m.recolte));
  }

  // ---------- Photos : réduites dans le navigateur avant l'envoi ----------
  var fileIn = document.createElement('input');
  fileIn.type = 'file';
  fileIn.accept = 'image/jpeg,image/png,image/webp';
  fileIn.style.display = 'none';
  fileIn.setAttribute('aria-hidden', 'true');
  fileIn.tabIndex = -1;
  function shrink(file, done) {
    if (!file || !/^image\//.test(file.type)) { flash('Choisissez une image JPEG, PNG ou WebP.'); return; }
    if (file.size > 15e6) { flash('Cette image dépasse 15 Mo. Choisissez une image plus légère.'); return; }
    var url = URL.createObjectURL(file), img = new Image();
    img.onload = function () {
      var out = '', steps = [[320, 0.82], [240, 0.75], [180, 0.7]];
      for (var k = 0; k < steps.length && (!out || out.length > PHOTO_MAX); k++) {
        var r = Math.min(1, steps[k][0] / Math.max(img.width, img.height));
        var cv = document.createElement('canvas');
        cv.width = Math.max(1, Math.round(img.width * r));
        cv.height = Math.max(1, Math.round(img.height * r));
        var g = cv.getContext('2d');
        g.fillStyle = '#fff';
        g.fillRect(0, 0, cv.width, cv.height);
        g.drawImage(img, 0, 0, cv.width, cv.height);
        out = cv.toDataURL('image/jpeg', steps[k][1]);
      }
      URL.revokeObjectURL(url);
      if (!/^data:image\/jpeg;base64,/.test(out) || out.length > PHOTO_MAX) { flash('Cette image reste trop lourde après réduction. Essayez une autre photo.'); return; }
      done(out);
    };
    img.onerror = function () { URL.revokeObjectURL(url); flash('Image illisible. Essayez un autre fichier JPEG, PNG ou WebP.'); };
    img.src = url;
  }
  fileIn.addEventListener('change', function () {
    var i = parseInt(fileIn.getAttribute('data-i'), 10), f = fileIn.files && fileIn.files[0];
    if (!f || !D.equipe[i]) return;
    shrink(f, function (data) {
      if (!D.equipe[i]) return;
      D.equipe[i].photo = data;
      renderList('equipe');
      checkDirty();
      flash('Photo ajoutée. Cliquez sur Enregistrer pour la publier.');
    });
  });

  // ---------- Événements ----------
  function onClick(e) {
    var add = e.target.closest && e.target.closest('[data-ap-add]');
    if (add) {
      var l = add.getAttribute('data-ap-add'), L = LISTS[l];
      if (D[l].length >= L.max) { flash('Au plus ' + L.max + ' lignes dans ce bloc. Supprimez-en une pour en ajouter une autre.'); return; }
      D[l].push(L.blank());
      renderList(l);
      checkDirty();
      var last = document.querySelector('#' + WRAP[l] + ' li:last-child input, #' + WRAP[l] + ' li:last-child textarea');
      if (last) last.focus();
      return;
    }
    var b = e.target.closest && e.target.closest('[data-act][data-l]');
    if (!b || !WRAP[b.getAttribute('data-l')]) return;
    var l2 = b.getAttribute('data-l'), i = parseInt(b.getAttribute('data-i'), 10), list = D[l2], act = b.getAttribute('data-act');
    if (!list[i]) return;
    if (act === 'up' && i > 0) { list.splice(i - 1, 0, list.splice(i, 1)[0]); }
    else if (act === 'down' && i < list.length - 1) { list.splice(i + 1, 0, list.splice(i, 1)[0]); }
    else if (act === 'del') {
      if (!window.confirm('Supprimer « ' + LISTS[l2].title(list[i]) + ' » ? Le changement sera publié à l’enregistrement.')) return;
      list.splice(i, 1);
    }
    else if (act === 'on') { list[i].on = !list[i].on; }
    else if (act === 'photo') { fileIn.setAttribute('data-i', String(i)); fileIn.value = ''; fileIn.click(); return; }
    else if (act === 'nophoto') { list[i].photo = ''; }
    else return;
    renderList(l2);
    checkDirty();
    var again = document.querySelector('#' + WRAP[l2] + ' [data-act="' + act + '"][data-i="' + (act === 'up' ? i - 1 : act === 'down' ? i + 1 : i) + '"]');
    if (again && !again.disabled) again.focus();
  }
  function onInput(e) {
    var t = e.target;
    if (!t || !t.getAttribute) return;
    var l = t.getAttribute('data-l'), f = t.getAttribute('data-f');
    if (l && f && WRAP[l]) {
      var x = D[l][parseInt(t.getAttribute('data-i'), 10)];
      if (!x) return;
      x[f] = t.value;
      var li = t.closest('li');
      if (li) {
        var ti = li.querySelector('[data-title]'), tg = li.querySelector('[data-tag]');
        if (ti) ti.textContent = LISTS[l].title(x);
        if (tg) { var tag = LISTS[l].tag(x); tg.textContent = tag; tg.style.display = tag ? '' : 'none'; }
      }
    } else if (t.hasAttribute('data-w')) {
      weeks[parseInt(t.getAttribute('data-w'), 10)] = t.value;
    } else if (['ap-pres', 'f23', 'f24', 'f25', 'f8', 'f9', 'f32', 'f33', 'f34'].indexOf(t.id) === -1) {
      return;
    }
    if (t.id === 'f32') renderWeeks();
    checkDirty();
  }
  // « Lien externe… » : on demande l'adresse au lieu d'enregistrer ce texte comme lien.
  function onLinkChange(e) {
    var sel = e.target;
    if (!sel || (sel.id !== 'f8' && sel.id !== 'f9')) return;
    if (sel.value === EXT) {
      var url = (window.prompt('Adresse du lien externe (doit commencer par https://)', 'https://') || '').trim();
      if (/^https?:\/\/[^\s<>"]{3,}$/i.test(url) && url.length <= 500) {
        addOpt(sel, url, 'Lien externe : ' + url);
        sel.value = url;
      } else {
        sel.value = prevLink[sel.id] || SITE[0];
        if (url && url !== 'https://') window.alert('Adresse non valide : elle doit commencer par https:// . Le lien précédent est conservé.');
      }
    }
    prevLink[sel.id] = sel.value;
    checkDirty();
  }
  function onBlur(e) {
    var t = e.target;
    if (!t || !t.id) return;
    if (['f23', 'f24', 'f25'].indexOf(t.id) > -1 || t.hasAttribute('data-w')) {
      var n = parseAmount(t.value);
      if (n !== null) {
        t.value = fmt(n);
        if (t.hasAttribute('data-w')) weeks[parseInt(t.getAttribute('data-w'), 10)] = t.value;
        t.style.borderColor = '';
      } else if (t.value.trim() !== '') {
        t.style.borderColor = '#B3261E';
      }
      checkDirty();
    }
  }

  // ---------- Enregistrer / annuler ----------
  function api(url, method, body) {
    var o = { credentials: 'same-origin', method: method || 'GET' };
    if (body) { o.headers = { 'Content-Type': 'application/json' }; o.body = JSON.stringify(body); }
    return fetch(url, o).then(function (r) { return r.json().catch(function () { return { ok: false }; }); });
  }

  function saveAll() {
    if (saving || !apBase || !cpBase) return;
    var obj = parseAmount(getVal('f23')), rec = parseAmount(getVal('f24'));
    if (!obj) { flash('Indiquez l’objectif de la campagne en dollars, par exemple 50 000.'); if (getEl('f23')) getEl('f23').focus(); return; }
    if (rec === null && getVal('f24') !== '') { flash('Montant récolté illisible. Écrivez un nombre, par exemple 20 000.'); if (getEl('f24')) getEl('f24').focus(); return; }
    if (getVal('f25') !== '' && parseAmount(getVal('f25')) === null) { flash('Nombre de donateurs illisible. Écrivez un nombre entier, par exemple 212.'); if (getEl('f25')) getEl('f25').focus(); return; }
    var badWeek = weeks.slice(0, parseInt(getVal('f32'), 10) || 8).some(function (v) { return String(v).trim() !== '' && parseAmount(v) === null; });
    if (badWeek) { flash('Un montant de semaine est illisible. Écrivez des nombres, par exemple 9 800.'); return; }
    var ap = readAp(false), cp = readCp(false);
    if (!ap.presentation.texte && ap.presentation.on) { flash('Écrivez le texte de présentation, ou masquez ce bloc.'); if (getEl('ap-pres')) getEl('ap-pres').focus(); return; }
    rec = rec || 0;
    saving = true;
    flash('Enregistrement…');

    var tasks = [api('/api/admin/settings/apropos', 'PUT', ap), api('/api/admin/settings/campagne', 'PUT', cp)];
    // Objectif et récolté : dans les réglages de l'accueil (relus juste avant, pour ne rien écraser).
    if (!homeMoney || homeMoney.objectif !== obj || homeMoney.recolte !== rec) {
      tasks.push(api('/api/admin/settings/home').then(function (h) {
        if (!h || !h.ok || !h.settings) return h || { ok: false };
        var next = clone(h.settings);
        next.campagne = Object.assign({}, next.campagne, { objectif: obj, recolte: rec });
        return api('/api/admin/settings/home', 'PUT', next);
      }));
    }
    var on = swOn();
    if (pagesBase) {
      var nextPages = Object.assign({}, pagesBase, { pg_apropos: !!on.pub_apropos, pg_campagne: !!on.pub_campagne });
      if (JSON.stringify(nextPages) !== JSON.stringify(pagesBase)) {
        tasks.push(api('/api/admin/settings/pages', 'PUT', nextPages).then(function (r) { if (r && r.ok && r.settings) pagesBase = r.settings; return r; }));
      }
    }
    Promise.all(tasks).then(function (res) {
      saving = false;
      var failed = res.filter(function (r) { return !r || !r.ok; })[0];
      if (failed) { flash((failed && failed.message) || 'L’enregistrement a échoué. Vérifiez vos valeurs et réessayez.'); return; }
      applyAp(res[0].settings, true);
      applyCp(res[1].settings, true);
      applyMoney({ objectif: obj, recolte: rec });
      var c = comp();
      if (c) c.commitBase();
      setTimeout(function () { baseSig = sig(); checkDirty(); }, 0);
      var msg = 'Réglages enregistrés. Le site est à jour.';
      if (ap.equipe.on && !ap.equipe.accord) msg += ' L’équipe reste masquée tant que « Accord écrit reçu » n’est pas activé.';
      flash(msg);
    }).catch(function () {
      saving = false;
      flash('Impossible de joindre le serveur. Vérifiez votre connexion et réessayez.');
    });
  }

  function undoAll() {
    if (!apBase || !cpBase) return;
    applyAp(apBase, false);
    applyCp(cpBase, false);
    if (homeMoney) applyMoney(homeMoney);
    var c = comp();
    if (c) c.revertBase();
    setTimeout(function () { applyAutoUi(); checkDirty(); }, 0);
    flash('Changements annulés.');
  }

  window.__saAproposSave = saveAll;
  window.__saAproposUndo = undoAll;
  window.__saAproposOnSwitch = function (k) {
    if (k === 'cp_auto') applyAutoUi();
    checkDirty();
  };

  function start() {
    if (started) return;
    started = true;
    document.body.appendChild(fileIn);
    document.addEventListener('click', onClick);
    document.addEventListener('input', onInput);
    document.addEventListener('change', onLinkChange, true);
    document.addEventListener('change', onInput);
    document.addEventListener('blur', onBlur, true);
    Promise.all([
      api('/api/admin/settings/apropos'), api('/api/admin/settings/campagne'), api('/api/admin/settings/home'),
      api('/api/admin/settings/pages'), api('/api/admin/pages'), api('/api/admin/stats')
    ]).then(function (r) {
      pages = r[4] && r[4].ok ? (r[4].pages || []).filter(function (p) { return p.visibility !== 'draft'; }) : [];
      fillLinks('f8');
      fillLinks('f9');
      stats = r[5] && r[5].ok && r[5].campagne ? r[5].campagne : null;
      if (!(r[0] && r[0].ok && r[1] && r[1].ok && r[2] && r[2].ok)) {
        ['ap-valeurs', 'ap-histoire', 'ap-equipe', 'ap-chiffres', 'cp-etapes'].forEach(function (id) {
          var w = getEl(id);
          if (w) w.innerHTML = '<p class="hint" style="margin:0">Impossible de charger les réglages. Rechargez la page.</p>';
        });
        flash('Impossible de charger les réglages. Rechargez la page.');
        return;
      }
      applyAp(r[0].settings, true);
      applyCp(r[1].settings, true);
      applyMoney(r[2].settings.campagne || { objectif: 0, recolte: 0 });
      if (r[3] && r[3].ok && r[3].settings) {
        pagesBase = r[3].settings;
        var c = comp();
        if (c) c.setSwitches({ pub_apropos: pagesBase.pg_apropos !== false, pub_campagne: pagesBase.pg_campagne !== false }, true);
      }
      setTimeout(function () { baseSig = sig(); applyAutoUi(); checkDirty(); }, 0);
    }, function () { flash('Impossible de joindre le serveur. Rechargez la page.'); });
  }

  if (comp() && getEl('ap-valeurs')) start();
  else window.addEventListener('sa-apropos-ready', start, { once: true });
})();
</script>
'''


def wire_panel():
    path = ROOT / 'SA-APropos.dc.html'
    s, i, j, tpl = load(path)
    a0 = tpl.index('<div id="sp-0" class="sp">')
    h0 = tpl.index('<section', a0)
    a1 = tpl.index('<div id="sp-1" class="sp">')
    h1 = tpl.index('<section', a1)
    end = tpl.index('</main>', a1)
    head0, head1 = tpl[a0:h0], tpl[a1:h1]
    if WARN_OLD in head1:
        head1 = head1.replace(WARN_OLD, WARN_NEW)
    assert WARN_NEW in head1, 'avertissement de l’onglet Campagne introuvable'
    tpl = tpl[:a0] + head0 + SP0_SECTIONS + '</div>' + head1 + SP1_SECTIONS + '</div>' + tpl[end:]

    tpl, n = re.subn(r'class Component extends DCLogic \{.*?\n\}', lambda _: COMPONENT_SCRIPT, tpl, count=1, flags=re.S)
    assert n == 1, 'Component introuvable dans SA-APropos.dc.html'
    tpl = re.sub(r'<script id="sa-apropos-sync">.*?</script>\s*', '', tpl, flags=re.S)
    k = tpl.rindex('</body>')
    tpl = tpl[:k] + SYNC_SCRIPT.replace('__SITE__', json.dumps(SITE_LINKS, ensure_ascii=False)) + tpl[k:]
    assert 'Inscriptions Ramadan 2027' not in tpl
    save(path, s, i, j, tpl)
    print('SA-APropos.dc.html : onglets L’association et Campagne en direct reliés à la base')


# =====================================================================================
# 2. Page publique « À propos »
# =====================================================================================

LINK_JS = r"""    const pre = (typeof location !== 'undefined' && /\/(M-|T-)[^\/]*$/.exec(location.pathname)) ? /\/(M-|T-)[^\/]*$/.exec(location.pathname)[1] : '';
    const MAP = __URLMAP__;
    const href = (v, d) => { v = v || d; if (MAP[v]) return pre + MAP[v]; return /^(\/p\/|https?:\/\/)/i.test(v) ? v : pre + MAP[d]; };
"""

APROPOS_XVALS = r"""
  xvals() {
    /*ascil-apropos*/
    const PT = (typeof window !== 'undefined' && window.__ascilPrayer) || {};
    const A = PT.apropos || __DEFAULT__, C = PT.campagne || null;
""" + LINK_JS + r"""    const on = (b) => !!(b && b.on);
    const MONTHS = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin', 'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'];
    const COUNT = ['', 'Un engagement', 'Deux engagements', 'Trois engagements', 'Quatre engagements', 'Cinq engagements', 'Six engagements'];
    const val = on(A.valeurs) ? A.valeurs.items.filter((x) => x.on && x.titre) : [];
    const hist = on(A.histoire) ? A.histoire.items.filter((x) => x.on && x.titre && x.date).slice().sort((a, b) => (a.date < b.date ? -1 : 1)) : [];
    const eq = on(A.equipe) && A.equipe.accord ? A.equipe.items.filter((x) => x.on && x.nom) : [];
    const chif = on(A.chiffres) ? A.chiffres.items.filter((x) => x.on && x.valeur) : [];
    const srcs = [];
    chif.forEach((x) => { if (x.source && srcs.indexOf(x.source) === -1) srcs.push(x.source); });
    const obj = C && C.objectif ? C.objectif : 0;
    const texte = A.presentation && A.presentation.texte ? A.presentation.texte : '';
    return {
      apPres: on(A.presentation) && !!texte, apTexte: texte,
      apVal: val.length > 0, apValTitre: COUNT[val.length] || 'Nos engagements',
      apValeurs: val.map((x, i) => ({ titre: x.titre, texte: x.texte, i0: i % 3 === 0, i1: i % 3 === 1, i2: i % 3 === 2 })),
      apHist: hist.length > 0,
      apHistoire: hist.map((x) => ({ titre: x.titre, date: MONTHS[parseInt(x.date.slice(5, 7), 10) - 1] + ' ' + x.date.slice(0, 4) })),
      apProjet: on(A.projet), apObjectif: obj.toLocaleString('fr-CA') + ' $',
      apSoutenir: href(A.projet && A.projet.btnSoutenir, 'Page : Faire un don'),
      apSuivre: href(A.projet && A.projet.btnSuivre, 'Page : Campagne en direct'),
      apEquipe: eq.length > 0,
      apMembres: eq.map((x) => ({ nom: x.nom, role: x.role, photo: x.photo || '', hasPhoto: !!x.photo, noPhoto: !x.photo,
        ini: x.nom.split(/\s+/).filter(Boolean).slice(0, 2).map((p) => p.charAt(0).toUpperCase()).join('') })),
      apChif: chif.length > 0,
      apChiffres: chif.map((x) => { const m = /^(.*\d)\s?(e|er|re|ème)$/.exec(x.valeur); return { v: m ? m[1] : x.valeur, sup: m ? m[2] : '', libelle: x.libelle }; }),
      apHasSources: srcs.length > 0, apSources: srcs.join(' ; '),
    };
  }
"""


def sc_if(name, inner, default='true'):
    return f'<sc-if value="{{{{{name}}}}}" hint-placeholder-val="{{{{ {default} }}}}">{inner}</sc-if>'


def wrap_section(tpl, start_pat, name):
    """Entoure la <section> qui commence par start_pat d'un sc-if."""
    a = tpl.index(start_pat)
    b = tpl.index('</section>', a) + len('</section>')
    return tpl[:a] + sc_if(name, tpl[a:b]) + tpl[b:]


def patch_apropos(tpl):
    if '{{apTexte}}' in tpl:
        return tpl
    a = tpl.index('<main'); b = tpl.index('</main>')
    m = tpl[a:b]

    # 1. Présentation
    m = rep(m, '<p class="lead" style="font-size:21px;color:#1E2B26">' + APROPOS_DEFAULT['presentation']['texte'] + '</p>',
            '<p class="lead" style="font-size:21px;color:#1E2B26;white-space:pre-line">{{apTexte}}</p>')
    m = wrap_section(m, '<section class="sec" aria-label="Présentation">', 'apPres')

    # 2. Valeurs : trois cartes -> liste, l'icône d'origine tourne (1, 2, 3, 1…)
    g = m.index('<div class="g3" style="margin-top:28px">', m.index('id="mv-t"'))
    ge = m.index('</div>\n </div>\n</section>', g)
    cards = re.findall(r'<div class="card"><span style="color:#0E4D3C">(<svg.*?</svg>)</span>', m[g:ge], flags=re.S)
    assert len(cards) == 3, 'icônes des valeurs introuvables'
    icons = ''.join(f'<sc-if value="{{{{v.i{k}}}}}" hint-placeholder-val="{{{{ {str(k == 0).lower()} }}}}">{svg}</sc-if>' for k, svg in enumerate(cards))
    m = m[:g] + ('<div class="g3" style="margin-top:28px"><sc-for list="{{apValeurs}}" as="v" hint-placeholder-count="3">'
                 f'<div class="card"><span style="color:#0E4D3C">{icons}</span>'
                 '<p class="h3" style="margin-top:14px">{{v.titre}}</p><p class="muted" style="margin:8px 0 0">{{v.texte}}</p></div>'
                 '</sc-for>') + m[ge:]
    m = rep(m, '>Trois engagements</h2>', '>{{apValTitre}}</h2>')
    m = wrap_section(m, '<section class="sand" aria-labelledby="mv-t"', 'apVal')

    # 3. Histoire : étapes datées seulement
    m = resub(m, r'(<ol class="g3" style="list-style:none;margin:32px 0 0;[^"]*">).*?(</ol>)',
              lambda x: x.group(1) + '<sc-for list="{{apHistoire}}" as="h" hint-placeholder-count="1">'
              '<li style="padding-top:20px;position:relative"><span style="position:absolute;top:-9px;left:0;width:16px;height:16px;border-radius:50%;background:#C49A4A"></span>'
              '<p class="pill tnum" style="background:#0E4D3C;color:#fff;margin:0">{{h.date}}</p>'
              '<p style="margin:12px 0 0;font-weight:700">{{h.titre}}</p></li></sc-for>' + x.group(2))
    m = wrap_section(m, '<section class="sec" aria-labelledby="hist-t">', 'apHist')

    # 4. Projet : objectif de la campagne et liens des boutons
    m = rep(m, 'Une campagne pour', 'Une campagne de {{apObjectif}} pour')
    m = resub(m, r'<a class="btn btn-gold" href="(?:[MT]-)?Dons\.dc\.html">Soutenir le projet', '<a class="btn btn-gold" href="{{apSoutenir}}">Soutenir le projet')
    m = resub(m, r'<a class="btn btn-light" href="(?:[MT]-)?N3-Campagne\.dc\.html">Suivre en direct', '<a class="btn btn-light" href="{{apSuivre}}">Suivre en direct')
    m = wrap_section(m, '<section style="padding-bottom:80px" aria-labelledby="nl-t">', 'apProjet')

    # 5. Équipe : seulement avec l'accord écrit et des noms
    m = resub(m, r'\s*<p class="ph">Publié seulement avec les noms[^<]*</p>', '')
    eqa = m.index('<div class="g3" style="margin-top:28px">', m.index('id="eq-t"'))
    eqb = m.index('</div>\n </div>\n</section>', eqa)
    m = m[:eqa] + ('<div class="g3" style="margin-top:28px"><sc-for list="{{apMembres}}" as="p" hint-placeholder-count="3">'
                   '<div class="card" style="display:flex;gap:16px;align-items:center">'
                   '<sc-if value="{{p.hasPhoto}}" hint-placeholder-val="{{ false }}"><img src="{{p.photo}}" alt="" style="width:72px;height:72px;border-radius:50%;object-fit:cover;flex:none"></sc-if>'
                   '<sc-if value="{{p.noPhoto}}" hint-placeholder-val="{{ true }}"><span aria-hidden="true" style="width:72px;height:72px;border-radius:50%;background:#FBF7EC;border:2px solid #E4D9C0;flex:none;display:inline-flex;align-items:center;justify-content:center;font-weight:700;font-size:24px;color:#0E4D3C">{{p.ini}}</span></sc-if>'
                   '<div style="min-width:0"><p style="margin:0;font-weight:700;overflow-wrap:anywhere">{{p.nom}}</p><p class="muted" style="margin:2px 0 0">{{p.role}}</p></div></div>'
                   '</sc-for>') + m[eqb:]
    m = wrap_section(m, '<section class="sand" aria-labelledby="eq-t"', 'apEquipe')

    # 6. Chiffres et sources
    cha = m.index('<div class="g3" style="margin-top:28px">', m.index('id="ch-t"'))
    chb = m.index('</div>\n  <p class="muted"', cha)
    m = m[:cha] + ('<div class="g3" style="margin-top:28px"><sc-for list="{{apChiffres}}" as="c" hint-placeholder-count="3">'
                   '<div class="card"><p class="serif tnum" style="margin:0;font-size:44px;font-weight:700;color:#0E4D3C;overflow-wrap:anywhere">{{c.v}}<sup style="font-size:22px">{{c.sup}}</sup></p>'
                   '<p style="margin:6px 0 0">{{c.libelle}}</p></div></sc-for>') + m[chb:]
    m = resub(m, r'>Sources : page Facebook de l’ASCIL ; données de la MRC de Edmundston\. ',
              '>' + sc_if('apHasSources', 'Sources : {{apSources}}. ') )
    m = wrap_section(m, '<section class="sec" aria-labelledby="ch-t">', 'apChif')

    tpl = tpl[:a] + m + tpl[b:]

    # Logique : xvals ajoutée avant renderVals (la page n'en avait pas).
    la = tpl.index('<script type="text/x-dc"')
    lb = tpl.index('</script>', la)
    code = tpl[la:lb]
    assert '/*ascil-apropos*/' not in code and 'xvals() {' not in code
    xv = (APROPOS_XVALS.replace('__DEFAULT__', json.dumps(APROPOS_DEFAULT, ensure_ascii=False))
          .replace('__URLMAP__', json.dumps(URL_MAP, ensure_ascii=False)))
    code = resub(code, r'\n  renderVals\(\) \{', lambda x: xv.rstrip('\n') + x.group(0))
    return tpl[:la] + code + tpl[lb:]


# =====================================================================================
# 3. Page publique « Campagne en direct »
# =====================================================================================

CAMPAGNE_XVALS = r"""
  xvals() {
    /*ascil-campagne*/
    const PT = (typeof window !== 'undefined' && window.__ascilPrayer) || {};
    const C = PT.campagne || null, st = this.state;
    const obj = C && C.objectif ? C.objectif : 0, g = Math.max(0, st.graw || 0), pct = obj > 0 ? Math.min(100, g / obj * 100) : 0;
    const fr = (n) => Math.round(n).toLocaleString('fr-CA');
    const kfmt = (n) => (n >= 1000 ? (Math.round(n / 100) / 10).toLocaleString('fr-CA') + ' k' : fr(n));
    const rec = C ? C.recolte : 0;
    const etapes = C && C.etapes && C.etapes.on ? C.etapes.items : [];
    const recPct = Math.min(100, rec / obj * 100);
    const wk = C && C.semaines && C.semaines.on ? C.semaines.items : [];
    const wmax = wk.reduce((m, w) => Math.max(m, w.montant), 0);
    const der = C && C.derniers && C.derniers.on ? C.derniers.items : [];
    const now = Date.now();
    const ago = (d) => {
      const t = Date.parse(String(d).replace(' ', 'T') + (/[zZ]|[+-]\d\d:?\d\d$/.test(String(d)) ? '' : 'Z'));
      if (!isFinite(t)) return '';
      const m = Math.max(0, Math.round((now - t) / 60000));
      if (m < 2) return 'à l’instant';
      if (m < 60) return 'il y a ' + m + ' min';
      const h = Math.round(m / 60);
      if (h < 24) return 'il y a ' + h + ' h';
      const j = Math.round(h / 24);
      return j < 2 ? 'hier' : 'il y a ' + j + ' jours';
    };
    return {
      gRaw: g, gAmount: C ? fr(g) + ' $' : '…', gPct: Math.round(pct), gRing: Math.round(100 - pct),
      gDonors: C ? fr(C.donateurs || 0) : '', showDonors: !!(C && C.donateurs > 0),
      gLeft: fr(Math.max(0, obj - g)) + ' $', gObjectif: fr(obj) + ' $', gObjRaw: obj,
      cHasEtapes: etapes.length > 0,
      cEtapes: etapes.map((e) => ({ seuil: e.seuil, libelle: e.libelle, bg: recPct >= e.seuil ? '#0E4D3C' : '#fff',
        etat: recPct >= e.seuil ? 'étape atteinte' : 'étape à venir' })),
      cHasWeeks: wk.length > 0 && wmax > 0,
      cWeeks: wk.map((w, i) => ({ label: w.label, val: kfmt(w.montant), h: Math.max(2, Math.round(w.montant / (wmax || 1) * 100)) + '%',
        bg: i === wk.length - 1 ? '#C49A4A' : '#0E4D3C' })),
      showFeed: der.length > 0,
      feed: der.map((d, i) => ({ who: d.nom, amt: d.montant == null ? '' : fr(d.montant) + ' $', when: ago(d.date), bg: i === 0 ? '#FFF8E8' : '#F7F2E4', cls: '' })),
    };
  }

  campAnim() {
    const C = (typeof window !== 'undefined' && window.__ascilPrayer && window.__ascilPrayer.campagne) || null;
    if (!C) return;
    const to = Math.max(0, C.recolte || 0), from = this.state.graw || 0;
    cancelAnimationFrame(this.raf2);
    let reduce = false;
    try { reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches; } catch (e) {}
    if (reduce || from === to) { this.setState({ graw: to }); return; }
    const t0 = performance.now() + (this.state.loading ? 1900 : 0);
    const step = (now) => { const k = Math.min(1, Math.max(0, (now - t0) / 1600)); this.setState({ graw: Math.round(from + (to - from) * (1 - Math.pow(1 - k, 3))) }); if (k < 1) this.raf2 = requestAnimationFrame(step); };
    this.raf2 = requestAnimationFrame(step);
    // Onglet en arrière-plan : le navigateur suspend l'animation. La vraie valeur est posée quand même.
    clearTimeout(this.campT);
    this.campT = setTimeout(() => { cancelAnimationFrame(this.raf2); if (this.state.graw !== to) this.setState({ graw: to }); }, (this.state.loading ? 1900 : 0) + 2200);
  }
"""

CHECK_RE = r'<svg class="icon" aria-hidden="true" width="16" height="16"[^>]*><path d="M5 12\.5l4\.5 4\.5L19 7\.5"></path></svg>'


def patch_campagne(tpl):
    la = tpl.index('<script type="text/x-dc"')
    lb = tpl.index('</script>', la)
    code = tpl[la:lb]
    if '/*ascil-campagne*/' not in code:
        # Simulation retirée : montant animé vers la vraie valeur dès que /api/campagne répond.
        code = resub(code, r' const tgt2 = 0, t0 = .*?\}, 7000\); \}',
                     lambda _: " this.onCamp = () => this.campAnim(); try { window.addEventListener('ascil:prayer', this.onCamp); } catch (e) {} this.campAnim(); }")
        code = rep(code, 'clearInterval(this.xt);',
                   "clearInterval(this.xt); cancelAnimationFrame(this.raf2); try { window.removeEventListener('ascil:prayer', this.onCamp); } catch (e) {}")
        code = rep(code, ', graw: 0, donors: 312, fi: 0, feedL: [] }', ', graw: 0 }')
        code, n = re.subn(r'\n  xvals\(\) \{.*?\n  \}\n', lambda _: CAMPAGNE_XVALS, code, count=1, flags=re.S)
        assert n == 1, 'xvals introuvable dans N3-Campagne'
        tpl = tpl[:la] + code + tpl[lb:]
    else:
        # Déjà branchée : on remet la dernière version de xvals() et campAnim().
        code, n = re.subn(r'\n  xvals\(\) \{\n    /\*ascil-campagne\*/.*?\n  campAnim\(\) \{.*?\n  \}\n', lambda _: CAMPAGNE_XVALS, code, count=1, flags=re.S)
        assert n == 1, 'bloc campagne introuvable dans N3-Campagne'
        tpl = tpl[:la] + code + tpl[lb:]

    if '{{gObjectif}}' in tpl:
        return tpl
    a = tpl.index('<main'); b = tpl.index('</main>')
    m = tpl[a:b]
    m = resub(m, r'<div class="flag" role="note".*?</p></div>', '')
    m = rep(m, 'Voici où nous en sommes, mis à jour en temps réel.', 'Voici où nous en sommes.')
    m = re.sub(r'\s*<span class="ex"[^>]*>\[EXEMPLE À MODIFIER\]</span>', '', m)
    assert 'EXEMPLE' not in m
    m = rep(m, 'collectés', 'collectés sur <strong>{{gObjectif}}</strong>')
    m = rep(m, 'aria-valuemax="0"', 'aria-valuemax="{{gObjRaw}}"')
    m = resub(m, r'(<div style="display:flex;gap:24px;margin-top:18px;flex-wrap:wrap" class="tnum">)(<div><p[^>]*>\{\{gDonors\}\}</p><p[^>]*>donateurs</p></div>)',
              lambda x: x.group(1) + sc_if('showDonors', x.group(2)))

    # Étapes
    ua = m.index('<div class="card"><p class="eyebrow">Étapes du projet')
    ub = m.index('</ul></div>', ua) + len('</ul></div>')
    chk = re.search(CHECK_RE, m[ua:ub]).group(0)
    etapes = ('<div class="card"><p class="eyebrow">Étapes du projet</p><ul style="list-style:none;margin:14px 0 0;padding:0;display:flex;flex-direction:column;gap:12px">'
              '<sc-for list="{{cEtapes}}" as="e" hint-placeholder-count="4"><li style="display:flex;gap:12px;align-items:center">'
              '<span style="flex:none;width:28px;height:28px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;background:{{e.bg}};color:#fff;border:2px solid #0E4D3C">'
              + chk + '</span><span><strong class="tnum">{{e.seuil}} %</strong> — {{e.libelle}}'
              '<span style="position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap"> ({{e.etat}})</span></span></li></sc-for></ul></div>')
    m = m[:ua] + sc_if('cHasEtapes', etapes) + m[ub:]

    # Dons par semaine
    wa = m.index('<div class="card"><p class="eyebrow">Dons par semaine')
    wb = m.index('</div>\n  </div>\n  <div style="position:sticky', wa) + len('</div>')
    weeks = ('<div class="card"><p class="eyebrow">Dons par semaine</p><div style="display:flex;gap:8px;align-items:flex-end;margin-top:16px">'
             '<sc-for list="{{cWeeks}}" as="w" hint-placeholder-count="8"><div style="display:flex;flex-direction:column;align-items:center;gap:6px;flex:1;min-width:0">'
             '<span class="tnum" style="font-size:12px;font-weight:700">{{w.val}}</span>'
             '<div style="width:100%;max-width:44px;height:140px;display:flex;align-items:flex-end"><div class="bar" style="width:100%;height:{{w.h}};background:{{w.bg}};border-radius:8px 8px 3px 3px;transform-origin:bottom;animation-name:growy"></div></div>'
             '<span class="muted" style="font-size:12px;text-align:center">{{w.label}}</span></div></sc-for></div></div>')
    m = m[:wa] + sc_if('cHasWeeks', weeks) + m[wb:]

    # Derniers dons
    fa = m.index('<div class="card" style="padding:22px"><p class="eyebrow" style="display:flex;gap:8px;align-items:center"><span class="live"')
    fb = m.index('</ul>\n   </div>', fa) + len('</ul>\n   </div>')
    m = m[:fa] + sc_if('showFeed', m[fa:fb], 'false') + m[fb:]

    m = rep(m, 'Faire un don maintenant · Objectif à définir', 'Faire un don maintenant · Objectif {{gObjectif}}')
    assert '50 000' not in m and '0' not in m, 'montant en dur restant'
    return tpl[:a] + m + tpl[b:]


def wire_public():
    for prefix in ('', 'M-', 'T-'):
        for name, fn in (('APropos', patch_apropos), ('N3-Campagne', patch_campagne)):
            path = ROOT / f'{prefix}{name}.dc.html'
            s, i, j, tpl = load(path)
            save(path, s, i, j, fn(tpl))
    print('6 pages publiques (APropos, N3-Campagne : PC, M-, T-) reliées aux réglages')


if __name__ == '__main__':
    wire_panel()
    wire_public()
