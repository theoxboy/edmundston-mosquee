"""Pages des services (étapes S3 à S5) : Cours, Mariages, Funérailles, Aide alimentaire, Espace femmes.

- Panneau SA-Services, onglets 2 à 6 : chaque onglet est construit dans le navigateur à partir d'une
  description de ses champs (moteur commun « sa-services-x »), lit et enregistre sa clé
  (cours, mariages, funerailles, aide, femmes) avec le bouton Enregistrer de l'en-tête.
- Pages publiques N2-* (PC, M-, T-) : contenus tirés de ces clés, mentions [À CONFIRMER] et
  [EXEMPLE À MODIFIER] retirées, formulaires envoyés à la boîte de réception (POST /api/forms).

Ordre : après wire_services.py (enregistrement commun du panneau), avant fix_inputs.py. Idempotent.
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


def wrap_between(tpl, start, end_marker, name, default='true', include_end=True):
    """Enveloppe tpl[start : fin de end_marker] dans un sc-if."""
    e = tpl.index(end_marker, start) + (len(end_marker) if include_end else 0)
    return tpl[:start] + sc_if(name, tpl[start:e], default) + tpl[e:]


INBOX_NOTE = ('Les demandes envoyées par ce formulaire arrivent dans '
              '<a href="SA-Contact.dc.html#sp-in" style="color:#0E4D3C;font-weight:700">Contact → Demandes reçues</a>.')
JOURS = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']


def T(p, l, **k): return dict(t='text', p=p, l=l, **k)
def A(p, l, **k): return dict(t='area', p=p, l=l, wide=True, **k)
def SW(p, l, **k): return dict(t='sw', p=p, l=l, **k)
def SEL(p, l, o, **k): return dict(t='select', p=p, l=l, o=o, **k)
def NOTE(h): return dict(t='note', h=h)
def LIST(p, add, item, d, mx, **k): return dict(t='list', p=p, add=add, item=item, d=d, max=mx, title='titre', **k)


SIMPLE_ITEM = [T('titre', 'Texte', max=160, wide=True)]

TABS = [
    dict(key='cours', sp='sp-1', sections=[
        dict(title='Liste des cours', desc='Le chercheur « 3 questions, 1 cours » et la liste « Tous les cours » utilisent ces fiches. '
             'Prix à 0 : aucun prix affiché.', f=[
            LIST('items', '+ Ajouter un cours', [
                T('titre', 'Nom du cours', max=80),
                SEL('matiere', 'Matière', [['coran', 'Coran'], ['arabe', 'Arabe']]),
                SEL('jour', 'Jour', [[j, j] for j in JOURS]),
                dict(t='time', p='debut', l='Début'), dict(t='time', p='fin', l='Fin'),
                dict(t='num', p='places', l='Places restantes'), dict(t='num', p='prix', l='Prix par mois', suf='$'),
                T('prof', 'Enseignant·e', max=80, ph='Enseignante : Sœur Amina'),
                dict(t='multi', p='ages', l='Public', o=[['5-8', 'Enfant 5–8 ans'], ['9-12', 'Enfant 9–12 ans'], ['13-17', 'Ado 13–17 ans'], ['adulte', 'Adulte']]),
                dict(t='multi', p='niveaux', l='Niveaux', o=[['deb', 'Débutant'], ['int', 'Intermédiaire'], ['av', 'Avancé']]),
            ], {'titre': '', 'matiere': 'coran', 'ages': [], 'niveaux': [], 'jour': 'Samedi', 'debut': '', 'fin': '',
                'places': 0, 'prix': 0, 'prof': '', 'on': True}, 30, tag='places', empty='Nouveau cours',
                none='Aucun cours : la page indique qu’aucun cours ne correspond.'),
        ]),
        dict(title='Inscriptions', f=[
            T('annee', 'Année scolaire', max=20, ph='2026–2027'),
            SEL('delai', 'Délai de réponse annoncé', [['24 h', '24 h'], ['48 h', '48 h'], ['1 semaine', '1 semaine']]),
            SW('inscriptions', 'Inscriptions ouvertes', hint='Fermées : les cours restent visibles, sans bouton d’inscription.'),
            SW('attente', 'Liste d’attente quand un cours est complet'),
            SW('essai', 'Premier cours d’essai gratuit'),
            NOTE(INBOX_NOTE),
        ]),
        dict(title='Tarifs, premier cours et lieu', sw='infos.on', f=[
            NOTE('Le titre « Tarifs » se calcule avec les prix des cours (par exemple « 25 à 40 $ par mois »).'),
            A('infos.tarifs', 'Texte sous les tarifs', max=400),
            A('infos.essai', 'Texte « Premier cours » (affiché si le cours d’essai est offert)', max=400),
            T('infos.lieu', 'Lieu', max=80), A('infos.lieuTexte', 'Texte sous le lieu', max=400),
        ]),
    ]),
    dict(key='mariages', sp='sp-2', sections=[
        dict(title='Étapes du parcours', f=[
            T('duree', 'Durée totale annoncée', max=40, ph='environ 6 semaines'),
            T('delai', 'Délai de réponse', max=40, ph='3 jours ouvrables'),
            LIST('etapes', '+ Ajouter une étape', [T('titre', 'Titre', max=80), T('quand', 'Quand', max=40), A('texte', 'Explication', max=600)],
                 {'titre': '', 'quand': '', 'texte': '', 'on': True}, 10, empty='Nouvelle étape',
                 none='Aucune étape : le parcours n’est pas affiché.'),
        ]),
        dict(title='Liste de documents', sw='docs.on', f=[
            NOTE('Les visiteurs cochent les documents prêts sur leur appareil ; rien n’est enregistré.'),
            LIST('docs.items', '+ Ajouter un document', SIMPLE_ITEM, {'titre': '', 'on': True}, 15, empty='Nouveau document'),
        ]),
        dict(title='Formulaire de rendez-vous', sw='form.on', f=[NOTE(INBOX_NOTE)]),
    ]),
    dict(key='funerailles', sp='sp-3', sections=[
        dict(title='Numéro d’urgence', desc='Grand bouton en haut de la page : « Appeler maintenant » si un téléphone est indiqué, '
             'sinon « Écrire par courriel ».', f=[
            T('responsable', 'Responsable des funérailles', max=80, ph='Nom (facultatif)'),
            T('telephone', 'Téléphone', max=30, ph='418 555-0142', type='tel'),
            T('courriel', 'Courriel (utilisé s’il n’y a pas de téléphone)', max=120, type='email'),
            SW('h24', 'Joignable 24 h / 24'),
            SW('rappel911', 'Rappel « Urgence médicale ? Composez le 911 »'),
        ]),
        dict(title='Quoi faire maintenant', desc='Les étapes que la famille peut cocher sur son appareil.', f=[
            LIST('etapes', '+ Ajouter une étape', [T('titre', 'Titre', max=80, wide=True), A('texte', 'Explication', max=600)],
                 {'titre': '', 'texte': '', 'on': True}, 10, empty='Nouvelle étape', none='Aucune étape : le bloc n’est pas affiché.'),
        ]),
        dict(title='Documents utiles', sw='docs.on', f=[
            LIST('docs.items', '+ Ajouter un document', SIMPLE_ITEM, {'titre': '', 'on': True}, 15, empty='Nouveau document'),
        ]),
        dict(title='Ce que l’association prend en charge', sw='charge.on', f=[A('charge.texte', 'Texte', max=600)]),
    ]),
    dict(key='aide', sp='sp-4', sections=[
        dict(title='Formulaire « J’ai besoin d’aide »', sw='form.on',
             desc='Masqué : la page invite à écrire depuis la page Contact.', f=[
            NOTE(INBOX_NOTE),
            NOTE('<strong style="color:#1E2B26">Ce qui peut aider</strong> : les choix proposés dans le formulaire.'),
            LIST('form.besoins', '+ Ajouter un choix', [T('titre', 'Choix proposé', max=40, wide=True)], {'titre': '', 'on': True}, 8,
                 empty='Nouveau choix'),
            SW('form.recup', 'Option « Sur place, discrètement »'),
            SW('form.livraison', 'Option « Livraison »'),
            SEL('form.delai', 'Délai de réponse annoncé', [['24 h', '24 h'], ['48 h', '48 h'], ['72 h', '72 h']]),
        ]),
        dict(title='Ce qui manque ce mois-ci', sw='manque.on', f=[
            LIST('manque.items', '+ Ajouter une denrée', [
                T('titre', 'Denrée', max=60),
                SEL('niveau', 'Besoin', [['tres', 'Très demandé'], ['demande', 'Demandé'], ['suffisant', 'Suffisant']]),
            ], {'titre': '', 'niveau': 'demande', 'on': True}, 15, tag='niveau', empty='Nouvelle denrée'),
        ]),
        dict(title='Dépôt de denrées', sw='depot.on', f=[
            T('depot.adresse', 'Adresse', max=120), T('depot.quand', 'Jours et heures', max=120, ph='Samedi et dimanche, 10 h – 14 h'),
            A('depot.note', 'Précision', max=300),
        ]),
        dict(title='Don en argent', sw='argent.on', f=[
            T('argent.courriel', 'Courriel Interac', max=120, type='email'), A('argent.note', 'Message à indiquer', max=300),
        ]),
    ]),
    dict(key='femmes', sp='sp-5', sections=[
        dict(title='Horaires par jour', desc='Le badge « Ouvert / Fermé » de la page se calcule avec ces heures. La 2e plage est facultative.', f=[
            dict(t='week', p='jours'),
            dict(t='date', p='fermeture', l='Fermeture exceptionnelle le',
                 hint='Ce jour-là, la page affiche « Fermé aujourd’hui ». Laissez vide sinon.'),
        ]),
        dict(title='Plan d’accès', f=[dict(t='img', p='plan', l='Image du plan', max=200000, alt='Plan d’accès de l’espace femmes')]),
        dict(title='Infos pratiques', sw='pratique.on', desc='Laissez une ligne vide pour la masquer.', f=[
            T('pratique.entree', 'Entrée', max=160), T('pratique.acces', 'Accès', max=160),
            T('pratique.ablutions', 'Ablutions', max=160), T('pratique.jumua', 'Jumu’a', max=160),
            T('pratique.enfants', 'Enfants', max=160), T('pratique.responsable', 'Contact de la responsable', max=160),
        ]),
        dict(title='Règles de l’espace', sw='regles.on', f=[
            LIST('regles.items', '+ Ajouter une règle', SIMPLE_ITEM, {'titre': '', 'on': True}, 15, empty='Nouvelle règle'),
        ]),
    ]),
]

ENGINE = r'''<script id="sa-services-x">
(function () {
  var TABS = __TABS__;
  var JOURS = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche'];
  var TAGF = {
    places: function (x) { return Number(x.places) > 0 ? x.places + ' places' : 'Complet'; },
    niveau: function (x) { return { tres: 'Très demandé', demande: 'Demandé', suffisant: 'Suffisant' }[x.niveau] || ''; }
  };
  var SVG = {
    up: '<svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 19V5M5 12l7-7 7 7"></path></svg>',
    down: '<svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5v14M19 12l-7 7-7-7"></path></svg>',
    del: '<svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3"></path></svg>'
  };
  var data = {}, base = {}, loaded = false, started = false, LISTS = {};

  function el(id) { return document.getElementById(id); }
  function clone(o) { return JSON.parse(JSON.stringify(o)); }
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; });
  }
  function flash(m) { var c = window.__saServices; if (c) c.flash(m); }
  function notify() { if (window.__svCheckDirty) window.__svCheckDirty(); }
  function get(o, path) {
    var ps = String(path).split('.');
    for (var i = 0; i < ps.length; i++) { if (o == null) return undefined; o = o[ps[i]]; }
    return o;
  }
  function set(o, path, v) {
    var ps = String(path).split('.');
    for (var i = 0; i < ps.length - 1; i++) { if (o[ps[i]] == null) o[ps[i]] = {}; o = o[ps[i]]; }
    o[ps[ps.length - 1]] = v;
  }
  function dirtyKey(k) { return loaded && base[k] !== undefined && JSON.stringify(data[k]) !== base[k]; }
  function api(url, method, body) {
    var o = { credentials: 'same-origin', method: method || 'GET' };
    if (body) { o.headers = { 'Content-Type': 'application/json' }; o.body = JSON.stringify(body); }
    return fetch(url, o).then(function (r) { return r.json().catch(function () { return { ok: false }; }); });
  }
  function at(k, p) { return ' data-xk="' + k + '" data-xp="' + esc(p) + '"'; }
  function fid(k, p) { return 'x-' + k + '-' + String(p).replace(/\./g, '-'); }
  var FULL = ' style="inline-size:100%;min-inline-size:0"';

  // ---------- Champs ----------
  function field(f, k, pre) {
    var p = f.p ? pre + f.p : '', v = f.p ? get(data[k], p) : null, id = fid(k, p);
    var col = f.wide ? ' style="grid-column:1/-1;min-width:0"' : ' style="min-width:0"';
    function lab(inner) {
      return '<div class="fld"' + col + '><label class="lbl" for="' + id + '">' + esc(f.l) + '</label>' + inner +
        (f.hint ? '<p class="hint" style="margin:2px 0 0">' + f.hint + '</p>' : '') + '</div>';
    }
    switch (f.t) {
      case 'text':
        return lab('<input class="in" type="' + (f.type || 'text') + '" id="' + id + '"' + at(k, p) + ' maxlength="' + (f.max || 200) + '"' +
          (f.ph ? ' placeholder="' + esc(f.ph) + '"' : '') + ' value="' + esc(v) + '"' + FULL + '>');
      case 'area':
        return lab('<textarea class="in" rows="3" id="' + id + '"' + at(k, p) + ' maxlength="' + (f.max || 400) + '">' + esc(v) + '</textarea>');
      case 'num':
        return lab('<div style="position:relative"><input class="in" type="text" inputmode="numeric" data-xnum="1" id="' + id + '"' + at(k, p) +
          ' value="' + esc(v == null ? '' : v) + '" style="inline-size:100%;min-inline-size:0' + (f.suf ? ';padding-right:34px' : '') + '">' +
          (f.suf ? '<span aria-hidden="true" style="position:absolute;right:12px;top:50%;transform:translateY(-50%);color:#4F5E57;font-weight:600">' + esc(f.suf) + '</span>' : '') + '</div>');
      case 'time':
      case 'date':
        return lab('<input class="in" type="' + f.t + '" id="' + id + '"' + at(k, p) + ' value="' + esc(v) + '"' + FULL + '>');
      case 'select':
        return lab('<select class="in" id="' + id + '"' + at(k, p) + FULL + '>' + f.o.map(function (o) {
          return '<option value="' + esc(o[0]) + '"' + (o[0] === v ? ' selected' : '') + '>' + esc(o[1]) + '</option>';
        }).join('') + '</select>');
      case 'sw':
        return '<div class="row" style="grid-column:1/-1"><div><div style="font-weight:600;font-size:14px">' + esc(f.l) + '</div>' +
          (f.hint ? '<p class="hint" style="margin:2px 0 0">' + f.hint + '</p>' : '') + '</div>' +
          '<button type="button" class="sw" role="switch" data-xsw="1"' + at(k, p) + ' aria-label="' + esc(f.l) + '" aria-checked="' + (v ? 'true' : 'false') + '"></button></div>';
      case 'multi':
        var arr = Array.isArray(v) ? v : [];
        return '<div class="fld" style="grid-column:1/-1;min-width:0"><span class="lbl" id="' + id + '">' + esc(f.l) + '</span>' +
          '<div role="group" aria-labelledby="' + id + '" style="display:flex;flex-wrap:wrap;gap:8px">' + f.o.map(function (o) {
            var on = arr.indexOf(o[0]) > -1;
            return '<button type="button" class="btn ' + (on ? 'btn-green' : 'btn-line') + '" data-xv="' + esc(o[0]) + '"' + at(k, p) +
              ' aria-pressed="' + on + '" style="min-height:40px;padding:0 14px;font-size:14px">' + esc(o[1]) + '</button>';
          }).join('') + '</div></div>';
      case 'img':
        return '<div class="fld" style="grid-column:1/-1;min-width:0"><span class="lbl">' + esc(f.l) + '</span>' +
          (v ? '<img src="' + esc(v) + '" alt="' + esc(f.alt || '') + '" style="max-width:100%;max-height:260px;border-radius:12px;border:1px solid #E4D9C0;align-self:flex-start">'
             : '<p class="hint" style="margin:0">Aucune image : le bloc n’est pas affiché sur le site.</p>') +
          '<div style="display:flex;gap:8px;flex-wrap:wrap"><label class="btn btn-line" style="cursor:pointer;position:relative">' + (v ? 'Remplacer l’image' : 'Choisir une image') +
          '<input type="file" accept="image/*" data-ximg="' + (f.max || 200000) + '"' + at(k, p) + ' style="position:absolute;inset:0;opacity:0;cursor:pointer"></label>' +
          (v ? '<button type="button" class="btn" data-xclear="1"' + at(k, p) + ' style="background:#fff;border-color:#B3261E;color:#B3261E">Retirer l’image</button>' : '') +
          '</div><p class="hint" style="margin:2px 0 0">L’image est réduite avant l’enregistrement.</p></div>';
      case 'note':
        return '<p class="hint" style="grid-column:1/-1;margin:0">' + f.h + '</p>';
      case 'list':
        return list(f, k, pre);
      case 'week':
        return week(f, k, pre);
    }
    return '';
  }
  function grid(fields, k, pre) {
    return '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,210px),1fr));gap:12px 14px;align-items:start">' +
      fields.map(function (f) { return field(f, k, pre); }).join('') + '</div>';
  }
  function list(f, k, pre) {
    var p = pre + f.p, arr = get(data[k], p) || [];
    var rows = arr.map(function (x, i) {
      var t = (x[f.title] || '').trim() || f.empty || 'Sans titre', tag = f.tag && TAGF[f.tag] ? TAGF[f.tag](x) : '', ip = p + '.' + i + '.';
      var b = function (act, dis) {
        return '<button type="button" class="ico" data-xk="' + k + '" data-xl="' + esc(p) + '" data-xi="' + i + '" data-xact="' + act + '"' +
          ' aria-label="' + { up: 'Monter', down: 'Descendre', del: 'Supprimer' }[act] + ' ' + esc(t) + '"' + (dis ? ' disabled' : '') + '>' + SVG[act] + '</button>';
      };
      return '<li style="border:1px solid #E4D9C0;border-radius:14px;background:#fff">' +
        '<div style="display:flex;align-items:center;gap:10px;padding:10px 10px 10px 14px;flex-wrap:wrap;border-bottom:1px solid #F3EAD8">' +
        '<span class="pos">' + (i + 1) + '</span>' +
        '<span data-xtitle style="flex:1;min-width:150px;font-weight:700;color:#0E4D3C;overflow-wrap:anywhere">' + esc(t) + '</span>' +
        (tag ? '<span class="tag" style="background:#F3EAD8;color:#7A5A1E">' + esc(tag) + '</span>' : '') +
        b('up', i === 0) + b('down', i === arr.length - 1) + b('del', false) +
        '<button type="button" class="sw" role="switch" data-xsw="1"' + at(k, ip + 'on') + ' aria-label="Afficher ' + esc(t) + '" aria-checked="' + (x.on !== false ? 'true' : 'false') + '"></button>' +
        '</div><div style="padding:12px 14px;opacity:' + (x.on === false ? 0.5 : 1) + '">' + grid(f.item, k, ip) + '</div></li>';
    });
    return '<div style="grid-column:1/-1;display:flex;flex-direction:column;gap:10px;min-width:0">' +
      (arr.length ? '<ol style="list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:10px">' + rows.join('') + '</ol>'
        : '<p class="hint" style="margin:0">' + esc(f.none || 'Aucun élément pour l’instant.') + '</p>') +
      '<button type="button" class="btn btn-line" data-xk="' + k + '" data-xl="' + esc(p) + '" data-xact="add" style="align-self:flex-start"' +
      (arr.length >= f.max ? ' disabled' : '') + '>' + esc(f.add) + '</button></div>';
  }
  function week(f, k, pre) {
    var p = pre + f.p, arr = get(data[k], p) || [];
    return '<div style="grid-column:1/-1;display:flex;flex-direction:column;gap:8px;min-width:0">' + JOURS.map(function (d, i) {
      var x = arr[i] || {}, ip = p + '.' + i + '.';
      var t = function (q, l) {
        var id = fid(k, ip + q);
        return '<div class="fld" style="flex:1 1 112px;min-width:0"><label class="lbl" for="' + id + '">' + l + '</label>' +
          '<input class="in" type="time" id="' + id + '"' + at(k, ip + q) + ' value="' + esc(x[q] || '') + '"' + FULL + '></div>';
      };
      return '<div style="border:1px solid #E4D9C0;border-radius:14px;padding:10px 14px;display:flex;flex-wrap:wrap;gap:10px;align-items:flex-end;background:#fff">' +
        '<div style="flex:1 1 150px;display:flex;align-items:center;justify-content:space-between;gap:10px;min-height:44px">' +
        '<span style="font-weight:700;color:#0E4D3C">' + d + '</span><span style="display:flex;align-items:center;gap:8px"><span class="hint" aria-hidden="true">Ouvert</span>' +
        '<button type="button" class="sw" role="switch" data-xsw="1"' + at(k, ip + 'on') + ' aria-label="' + d + ' : ouvert" aria-checked="' + (x.on ? 'true' : 'false') + '"></button></span></div>' +
        '<div style="flex:3 1 300px;display:flex;flex-wrap:wrap;gap:10px;opacity:' + (x.on ? 1 : 0.5) + '">' +
        t('de1', 'Ouverture') + t('a1', 'Fermeture') + t('de2', '2e ouverture') + t('a2', '2e fermeture') + '</div></div>';
    }).join('') + '</div>';
  }

  // ---------- Onglets ----------
  function renderTab(tab) {
    var w = el('svx-' + tab.key);
    if (!w || !loaded || !data[tab.key]) return;
    var k = tab.key;
    w.innerHTML = tab.sections.map(function (s, n) {
      var on = s.sw ? !!get(data[k], s.sw) : true;
      return '<section class="card ' + (on ? '' : 'off') + '" aria-label="' + esc(s.title) + '"><div class="card-h"><span class="num" aria-hidden="true">' + (n + 1) + '</span>' +
        '<div><h3 class="ttl">' + esc(s.title) + '</h3>' + (s.desc ? '<p class="dsc">' + s.desc + '</p>' : '') + '</div>' +
        (s.sw ? '<div class="hsw"><span aria-hidden="true">Afficher</span><button type="button" class="sw" role="switch" data-xsw="1"' + at(k, s.sw) +
          ' aria-label="Afficher ' + esc(s.title) + '" aria-checked="' + on + '"></button></div>' : '') +
        '</div><div class="card-b">' + grid(s.f, k, '') + '</div></section>';
    }).join('');
  }
  function tabOf(k) { return TABS.filter(function (t) { return t.key === k; })[0]; }
  function rerender(k, sel) {
    renderTab(tabOf(k));
    if (sel) { var e = document.querySelector(sel); if (e && !e.disabled) e.focus(); }
    notify();
  }
  function q(s) { return String(s).replace(/"/g, '\\"'); }

  // ---------- Événements ----------
  function onClick(e) {
    var b = e.target.closest && e.target.closest('button[data-xk]');
    if (!b) return;
    var k = b.getAttribute('data-xk');
    if (!data[k]) return;
    var p = b.getAttribute('data-xp');
    if (b.hasAttribute('data-xsw')) {
      set(data[k], p, !get(data[k], p));
      rerender(k, 'button[data-xsw][data-xk="' + k + '"][data-xp="' + q(p) + '"]');
      return;
    }
    if (b.hasAttribute('data-xv')) {
      var v = b.getAttribute('data-xv'), arr = (get(data[k], p) || []).slice(), i0 = arr.indexOf(v);
      if (i0 > -1) arr.splice(i0, 1); else arr.push(v);
      set(data[k], p, arr);
      rerender(k, 'button[data-xk="' + k + '"][data-xp="' + q(p) + '"][data-xv="' + q(v) + '"]');
      return;
    }
    if (b.hasAttribute('data-xclear')) { set(data[k], p, ''); rerender(k); return; }
    var act = b.getAttribute('data-xact'), lp = b.getAttribute('data-xl'), f = LISTS[k + ':' + lp];
    if (!act || !f) return;
    var list = get(data[k], lp) || [], i = parseInt(b.getAttribute('data-xi'), 10), focus = '';
    if (act === 'add') {
      if (list.length >= f.max) { flash('Au plus ' + f.max + ' éléments. Supprimez-en un pour en ajouter un autre.'); return; }
      list.push(clone(f.d));
      set(data[k], lp, list);
      focus = '[data-xk="' + k + '"][data-xp^="' + q(lp + '.' + (list.length - 1) + '.') + '"]:not(button)';
    } else if (act === 'up' && i > 0) {
      list.splice(i - 1, 0, list.splice(i, 1)[0]);
      focus = 'button[data-xk="' + k + '"][data-xl="' + q(lp) + '"][data-xi="' + (i - 1) + '"][data-xact="up"]';
    } else if (act === 'down' && i < list.length - 1) {
      list.splice(i + 1, 0, list.splice(i, 1)[0]);
      focus = 'button[data-xk="' + k + '"][data-xl="' + q(lp) + '"][data-xi="' + (i + 1) + '"][data-xact="down"]';
    } else if (act === 'del') {
      var t = (list[i] && String(list[i][f.title] || '').trim()) || f.empty || 'cet élément';
      if (!window.confirm('Supprimer « ' + t + ' » ? Le changement sera publié à l’enregistrement.')) return;
      list.splice(i, 1);
      focus = 'button[data-xk="' + k + '"][data-xl="' + q(lp) + '"][data-xact="add"]';
    } else return;
    rerender(k, focus);
  }
  function onInput(e) {
    var t = e.target;
    if (!t || !t.getAttribute || !t.hasAttribute('data-xk') || t.type === 'file' || t.tagName === 'BUTTON') return;
    var k = t.getAttribute('data-xk'), p = t.getAttribute('data-xp');
    if (!data[k]) return;
    var v = t.value;
    if (t.hasAttribute('data-xnum')) { var s = String(v).replace(/[\s  $]/g, ''); v = /^\d+$/.test(s) ? Number(s) : v; }
    set(data[k], p, v);
    var li = t.closest('li');
    if (li && /\.titre$/.test(p)) { var ti = li.querySelector('[data-xtitle]'); if (ti) ti.textContent = String(v).trim() || 'Sans titre'; }
    notify();
  }
  function shrink(file, max, done) {
    var r = new FileReader();
    r.onload = function () {
      var im = new Image();
      im.onload = function () {
        var dim = 1600, qq = 0.85, out = '';
        for (var n = 0; n < 14; n++) {
          var sc = Math.min(1, dim / Math.max(im.width, im.height));
          var c = document.createElement('canvas');
          c.width = Math.max(1, Math.round(im.width * sc)); c.height = Math.max(1, Math.round(im.height * sc));
          var g = c.getContext('2d');
          g.fillStyle = '#fff'; g.fillRect(0, 0, c.width, c.height); g.drawImage(im, 0, 0, c.width, c.height);
          out = c.toDataURL('image/jpeg', qq);
          if (out.length <= max) { done(out); return; }
          if (qq > 0.55) qq -= 0.1; else dim = Math.round(dim * 0.8);
        }
        done('');
      };
      im.onerror = function () { done(''); };
      im.src = r.result;
    };
    r.onerror = function () { done(''); };
    r.readAsDataURL(file);
  }
  function onChange(e) {
    var t = e.target;
    if (!t || !t.hasAttribute || !t.hasAttribute('data-ximg')) return;
    var k = t.getAttribute('data-xk'), p = t.getAttribute('data-xp'), file = t.files && t.files[0];
    if (!file || !data[k]) return;
    flash('Réduction de l’image…');
    shrink(file, parseInt(t.getAttribute('data-ximg'), 10) || 200000, function (url) {
      if (!url) { flash('Cette image n’a pas pu être lue. Choisissez une photo JPEG ou PNG.'); return; }
      set(data[k], p, url);
      rerender(k);
      flash('Image prête. Cliquez sur Enregistrer pour la publier.');
    });
  }

  // ---------- Enregistrer / annuler (appelés par l'enregistrement commun) ----------
  function save() {
    if (!loaded) return [];
    var bad = Array.prototype.filter.call(document.querySelectorAll('input[data-xnum]'), function (i) {
      var s = String(i.value).replace(/[\s  $]/g, '');
      return s !== '' && !/^\d+$/.test(s);
    })[0];
    if (bad) {
      var l = bad.id && document.querySelector('label[for="' + bad.id + '"]');
      flash('Nombre illisible' + (l ? ' dans « ' + l.textContent + ' »' : '') + '. Écrivez un nombre entier, par exemple 25.');
      bad.focus();
      return false;
    }
    return TABS.filter(function (t) { return dirtyKey(t.key); }).map(function (t) {
      var k = t.key;
      return api('/api/admin/settings/' + k, 'PUT', data[k]).then(function (r) {
        if (r && r.ok && r.settings) { data[k] = clone(r.settings); base[k] = JSON.stringify(r.settings); }
        return r || { ok: false };
      });
    });
  }
  function after() { TABS.forEach(renderTab); notify(); }
  function undo() { TABS.forEach(function (t) { if (base[t.key] !== undefined) data[t.key] = JSON.parse(base[t.key]); }); after(); }
  window.__svx = { dirty: function () { return TABS.some(function (t) { return dirtyKey(t.key); }); }, save: save, after: after, undo: undo };

  function index(fields, k, pre) {
    fields.forEach(function (f) { if (f.t === 'list') LISTS[k + ':' + pre + f.p] = f; });
  }
  function start() {
    if (started || !el('svx-' + TABS[0].key)) return;
    started = true;
    TABS.forEach(function (t) { t.sections.forEach(function (s) { index(s.f, t.key, ''); }); });
    document.addEventListener('click', onClick);
    document.addEventListener('input', onInput);
    document.addEventListener('change', onInput);
    document.addEventListener('change', onChange);
    Promise.all(TABS.map(function (t) { return api('/api/admin/settings/' + t.key); })).then(function (res) {
      res.forEach(function (r, i) {
        var k = TABS[i].key;
        if (r && r.ok && r.settings) { data[k] = clone(r.settings); base[k] = JSON.stringify(r.settings); }
        else { var w = el('svx-' + k); if (w) w.innerHTML = '<p class="hint" style="margin:0;color:#B3261E">Impossible de charger ces réglages. Rechargez la page.</p>'; }
      });
      loaded = true;
      after();
    }, function () { flash('Impossible de joindre le serveur. Rechargez la page.'); });
  }
  if (el('svx-' + TABS[0].key)) start();
  else {
    var mo = new MutationObserver(function () { if (el('svx-' + TABS[0].key)) { mo.disconnect(); start(); } });
    mo.observe(document.documentElement, { childList: true, subtree: true });
  }
})();
</script>
'''


def wire_panel():
    path = ROOT / 'SA-Services.dc.html'
    s, i, j, tpl = load(path)
    for n, tab in enumerate(TABS, start=1):
        a = tpl.index(f'<div id="sp-{n}" class="sp">')
        nxt = tpl.find(f'<div id="sp-{n + 1}" class="sp">', a)
        if nxt == -1:
            nxt = tpl.index('</main>', a)
        body = tpl[a:nxt]
        h = body.find('<section')
        if f'id="svx-{tab["key"]}"' in body:
            continue
        assert h > 0, f'sp-{n} : sections introuvables'
        head = body[:h]
        head = head.replace('>Service à confirmer</p>', '>Service</p>')
        head = re.sub(r'<p[^>]*>Page de réserve.*?</p>', '', head, flags=re.S)
        tail = body[body.rindex('</section>') + len('</section>'):]
        tpl = tpl[:a] + head + f'<div id="svx-{tab["key"]}" style="display:flex;flex-direction:column;gap:18px">' \
            '<p class="hint" style="margin:0">Chargement des réglages…</p></div>' + tail + tpl[nxt:]
    assert 'Service à confirmer' not in tpl and 'Page de réserve' not in tpl
    tpl = re.sub(r'<script id="sa-services-x">.*?</script>\s*', '', tpl, flags=re.S)
    engine = ENGINE.replace('__TABS__', json.dumps(TABS, ensure_ascii=False))
    k = tpl.rindex('</body>')
    tpl = tpl[:k] + engine + tpl[k:]
    save(path, s, i, j, tpl)
    print('SA-Services.dc.html : onglets Cours, Mariages, Funérailles, Aide alimentaire et Espace femmes reliés')


# =====================================================================================
# Pages publiques
# =====================================================================================

URL_MAP_CONTACT = 'Contact.dc.html'

# Envoi commun vers la boîte de réception, utilisé par les formulaires des pages.
POST_JS = r"""
    if (!this.t0) this.t0 = Date.now();
    const gv = (id) => { const e = typeof document !== 'undefined' && document.getElementById(id); return e ? String(e.value || '').trim() : ''; };
    const post = (payload, ok) => {
      if (this.state.sending) return;
      this.setState({ sending: true, sendErr: '' });
      fetch('/api/forms', { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(Object.assign({ t: Date.now() - (this.t0 || 0) }, payload)) })
        .then((r) => r.json().catch(() => ({ ok: false })))
        .then((d) => { if (d && d.ok) this.setState(Object.assign({ sending: false, sendErr: '' }, ok)); else this.setState({ sending: false, sendErr: (d && d.message) || 'Votre demande n’a pas pu être envoyée. Réessayez dans un instant.' }); },
          () => this.setState({ sending: false, sendErr: 'Impossible de joindre le site. Vérifiez votre connexion et réessayez.' }));
    };
    const sendVals = (label) => ({ lbl: this.state.sending ? 'Envoi en cours…' : label, busy: String(!!this.state.sending) });
    const errVals = { sendErr: this.state.sendErr || '', hasSendErr: !!this.state.sendErr };
    const pre = (typeof location !== 'undefined' && /\/(M-|T-)[^\/]*$/.exec(location.pathname)) ? /\/(M-|T-)[^\/]*$/.exec(location.pathname)[1] : '';
"""

ERR_HTML = sc_if('hasSendErr', '<p role="alert" style="margin:10px 0 0;color:#B3261E;font-weight:600">{{sendErr}}</p>', 'false')


def strip_marks(tpl):
    """Retire le cadre [À CONFIRMER] et les mentions [EXEMPLE À MODIFIER]."""
    a = tpl.index('<main'); b = tpl.index('</main>')
    m = tpl[a:b]
    m = re.sub(r'<div class="flag" role="note".*?</p></div>', '', m, flags=re.S)
    m = re.sub(r'<div class="wrap" style="padding-top:20px"></div>', '', m)
    m = re.sub(r'<p[^>]*>\s*<span class="ex"[^>]*>\[EXEMPLE À MODIFIER\]</span>\s*</p>', '', m)
    m = re.sub(r'\s*<span class="ex"[^>]*>\[EXEMPLE À MODIFIER\]</span>', '', m)
    assert 'EXEMPLE À MODIFIER' not in m and 'À CONFIRMER' not in m, 'mention restante'
    return tpl[:a] + m + tpl[b:]


def set_xvals(tpl, body, default):
    la = tpl.index('<script type="text/x-dc"')
    lb = tpl.index('</script>', la)
    code = tpl[la:lb]
    a = code.index('  xvals() {')
    b = code.index('\n  }\n', a) + len('\n  }\n')
    new = ('  xvals() {\n    /*ascil-svx*/' + POST_JS + body.replace('__DEFAULT__', json.dumps(default, ensure_ascii=False)) + '\n  }\n')
    code = code[:a] + new + code[b:]
    return tpl[:la] + code + tpl[lb:]


def btn_send(tpl, click, label, name):
    """Bouton d'envoi : libellé « Envoi en cours… », aria-busy, message d'erreur dessous."""
    pat = r'sc-camel-on-click="\{\{' + re.escape(click) + r'\}\}"([^>]*)>' + re.escape(label) + '</button>'
    new = f'sc-camel-on-click="{{{{{click}}}}}"\\1 aria-busy="{{{{{name}.busy}}}}">{{{{{name}.lbl}}}}</button>' + ERR_HTML
    return resub(tpl, pat, new)


# ---------- Cours ----------
COURS_JS = r"""
    const PT = (typeof window !== 'undefined' && window.__ascilPrayer) || {};
    const V = PT.cours || __DEFAULT__, st = this.state, I = V.infos || {};
    const AGE = { '5-8': 'Enfant 5–8 ans', '9-12': 'Enfant 9–12 ans', '13-17': 'Ado 13–17 ans', adulte: 'Adulte' };
    const LVL = { deb: 'Débutant', int: 'Intermédiaire', av: 'Avancé' }, SUBJ = { coran: 'Coran', arabe: 'Arabe' };
    const hm = (v) => { const m = /^(\d\d):(\d\d)$/.exec(v || ''); return m ? (+m[1]) + ' h' + (m[2] !== '00' ? ' ' + m[2] : '') : ''; };
    const open = V.inscriptions !== false, wait = V.attente !== false;
    const C = (V.items || []).filter((c) => c.on !== false && c.titre).map((c, i) => ({
      id: i + 1, n: c.titre, subj: c.matiere, ages: c.ages || [], lvl: c.niveaux || [], jour: c.jour || '',
      h: [hm(c.debut), hm(c.fin)].filter(Boolean).join(' – '), prixN: Number(c.prix) || 0,
      prix: Number(c.prix) > 0 ? c.prix + ' $ / mois' : '', places: Number(c.places) || 0, prof: c.prof || '' }));
    const when = (c) => [c.jour, c.h].filter(Boolean).join(' · ');
    const info = (c) => [c.prix, c.prof].filter(Boolean).join(' · ');
    const opt = (pairs, key) => pairs.map((p) => ({ label: p[1], pressed: String(st[key] === p[0]), pick: () => this.setState({ [key]: st[key] === p[0] ? '' : p[0], course: 0, regDone: false, waitDone: false, sendErr: '' }) }));
    let res = [];
    if (st.age && st.subj) {
      const base = C.filter((c) => c.subj === st.subj && c.ages.indexOf(st.age) >= 0);
      const exact = st.lvl ? base.filter((c) => c.lvl.indexOf(st.lvl) >= 0) : base;
      res = (exact.length ? exact : base).map((c) => {
        const can = open && (c.places > 0 || wait);
        return { ...c, when: when(c), info: info(c), hasInfo: !!info(c), tag: exact.length && st.lvl ? 'Recommandé pour vous' : 'Cours proposé',
          placesTxt: c.places ? c.places + ' places restantes' : 'Complet', pBg: c.places ? '#EAF3EF' : '#FDF3F2', pFg: c.places ? '#0E4D3C' : '#B3261E',
          cta: c.places ? 'S’inscrire à ce cours' : 'Rejoindre la liste d’attente', border: c.places ? '#C49A4A' : '#E4D9C0',
          canReg: can, noReg: !can, noRegTxt: !open ? 'Les inscriptions sont fermées pour le moment.' : 'Ce cours est complet.',
          pick: () => this.setState({ course: c.id, regDone: false, sendErr: '' }) };
      });
    }
    const chosen = C.find((c) => c.id === st.course);
    const prices = C.map((c) => c.prixN).filter((x) => x > 0);
    const lo = prices.length ? Math.min.apply(null, prices) : 0, hi = prices.length ? Math.max.apply(null, prices) : 0;
    return {
      ageOpts: opt([['5-8', '5–8 ans'], ['9-12', '9–12 ans'], ['13-17', '13–17 ans'], ['adulte', 'Adulte']], 'age'),
      subjOpts: opt([['coran', 'Coran'], ['arabe', 'Arabe']], 'subj'),
      lvlOpts: opt([['deb', 'Débutant'], ['int', 'Intermédiaire'], ['av', 'Avancé']], 'lvl'),
      results: chosen ? [] : res, noAnswer: !(st.age && st.subj), noMatch: !!(st.age && st.subj) && res.length === 0,
      regOpen: !!chosen, regName: chosen ? chosen.n : '', regDone: st.regDone, regNotDone: !st.regDone,
      regSend: () => { if (!chosen) return; const tel = gv('r2'), mail = gv('r4');
        if (!tel && !mail) return this.setState({ sendErr: 'Indiquez un numéro de téléphone (de préférence) ou un courriel.' });
        post({ source: 'cours', nom: gv('r1'), contact: tel || mail, sujet: chosen.n,
        message: (chosen.places ? 'Demande d’inscription au cours « ' : 'Demande de place en liste d’attente pour le cours « ') + chosen.n + ' ».',
        details: { 'Cours': chosen.n, 'Horaire': when(chosen), 'Téléphone': tel, 'Courriel': mail, 'Prénom de l’enfant': gv('r3'), 'Liste d’attente': chosen.places ? 'Non' : 'Oui' } }, { regDone: true }); },
      regBtn: sendVals('Envoyer la demande'),
      regDoneTxt: 'L’enseignant vous répond sous ' + (V.delai || '48 h') + '.' + (V.essai ? ' Le premier cours est un cours d’essai gratuit.' : ''),
      resetFinder: () => this.setState({ age: '', subj: '', lvl: '', course: 0, regDone: false, waitDone: false, sendErr: '' }),
      showWait: open && wait, waitDone: st.waitDone, waitNot: !st.waitDone,
      joinWait: () => post({ source: 'cours', nom: 'Liste d’attente', contact: gv('wl'), sujet: 'Liste d’attente',
        message: 'Aucun cours ne correspond à cette recherche : ' + [AGE[st.age], SUBJ[st.subj], LVL[st.lvl]].filter(Boolean).join(', ') + '.' }, { waitDone: true }),
      waitBtn: sendVals('Rejoindre la liste d’attente'),
      ...errVals,
      hasCourses: C.length > 0, annee: V.annee || '',
      allCourses: C.map((c) => ({ subjL: SUBJ[c.subj] || '', n: c.n, when: when(c), info: info(c), hasInfo: !!info(c),
        pub: c.ages.map((a) => AGE[a]).filter(Boolean).join(', ') + (c.lvl.length ? ' · ' + c.lvl.map((l) => LVL[l]).filter(Boolean).join(', ') : ''),
        placesTxt: c.places ? c.places + ' places' : (wait && open ? 'Complet — liste d’attente' : 'Complet'),
        pBg: c.places ? '#EAF3EF' : '#FDF3F2', pFg: c.places ? '#0E4D3C' : '#B3261E' })),
      infosOn: I.on !== false, tarifTitre: !prices.length ? 'Sur demande' : lo === hi ? lo + ' $ par mois' : lo + ' à ' + hi + ' $ par mois',
      tarifTxt: I.tarifs || '', essaiOn: !!V.essai, essaiTxt: I.essai || '', lieuTitre: I.lieu || '', lieuTxt: I.lieuTexte || '',
    };"""


def patch_cours(tpl, default):
    tpl = strip_marks(tpl)
    tpl = set_xvals(tpl, COURS_JS, default)
    # Résultats du chercheur
    tpl = rep(tpl, '<p class="tnum" style="margin:8px 0 0;font-size:19px;font-weight:700;color:#0E4D3C">{{c.jour}} · {{c.h}}</p>',
              '<p class="tnum" style="margin:8px 0 0;font-size:19px;font-weight:700;color:#0E4D3C">{{c.when}}</p>')
    tpl = rep(tpl, '<p style="margin:6px 0 0">{{c.prix}} · {{c.prof}}</p>',
              sc_if('c.hasInfo', '<p style="margin:6px 0 0">{{c.info}}</p>'))
    old = '<button type="button" class="btn btn-gold" sc-camel-on-click="{{c.pick}}" style="margin-top:18px">{{c.cta}}</button>'
    tpl = rep(tpl, old, sc_if('c.canReg', old) + sc_if('c.noReg', '<p class="muted" style="margin:14px 0 0;font-weight:600">{{c.noRegTxt}}</p>', 'false'))
    # Liste d'attente
    a = tpl.index('<p class="muted" style="margin:8px 0 0">Laissez votre courriel')
    tpl = wrap_between(tpl, a, '<p class="pop" style="margin:12px 0 0;font-weight:700;color:#0E4D3C">C’est noté, merci.</p></sc-if>', 'showWait')
    tpl = btn_send(tpl, 'joinWait', 'Rejoindre la liste d’attente', 'waitBtn')
    tpl = rep(tpl, '<sc-if value="{{waitDone}}" hint-placeholder-val="{{ false }}"><p class="pop" style="margin:12px 0 0;font-weight:700;color:#0E4D3C">C’est noté, merci.</p></sc-if>',
              '<sc-if value="{{waitDone}}" hint-placeholder-val="{{ false }}"><p class="pop" role="status" style="margin:12px 0 0;font-weight:700;color:#0E4D3C">C’est noté, merci. Nous vous écrirons dès qu’un groupe ouvre.</p></sc-if>')
    # Inscription
    tpl = btn_send(tpl, 'regSend', 'Envoyer la demande', 'regBtn')
    tpl = rep(tpl, 'L’enseignant vous répond sous 48 h. Le premier cours est un cours d’essai gratuit.</p>', '{{regDoneTxt}}</p>')
    # Tous les cours
    tpl = rep(tpl, 'Horaires de l’année 2026–2027</h2>', 'Horaires de l’année {{annee}}</h2>')
    a = tpl.index('<div class="g3" style="margin-top:24px"><div class="card">')
    b = tpl.index('</div>\n </div>\n</section>', a)
    card = ('<sc-for list="{{allCourses}}" as="k" hint-placeholder-count="6"><div class="card"><div style="display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap">'
            '<span class="pill" style="background:#F3EAD8;color:#7A5A1E">{{k.subjL}}</span><span class="pill" style="background:{{k.pBg}};color:{{k.pFg}}">{{k.placesTxt}}</span></div>'
            '<p class="h3" style="margin-top:14px">{{k.n}}</p><p style="margin:8px 0 0">{{k.pub}}</p>'
            '<p class="tnum" style="margin:6px 0 0;font-weight:700;color:#0E4D3C">{{k.when}}</p>'
            + sc_if('k.hasInfo', '<p class="muted" style="margin:6px 0 0">{{k.info}}</p>') + '</div></sc-for>')
    tpl = tpl[:a] + '<div class="g3" style="margin-top:24px">' + card + tpl[b:]
    a = tpl.index('<section class="sand" aria-labelledby="all-t"')
    tpl = wrap_between(tpl, a, '</section>', 'hasCourses')
    # Tarifs, premier cours, lieu
    a = tpl.index('<section class="sec" aria-labelledby="tar-t">')
    b = tpl.index('</section>', a) + len('</section>')
    sec = tpl[a:b]
    sec = resub(sec, r'(id="tar-t" style="margin-top:10px">)25 à 40 \$ par mois(</p><p class="muted" style="margin:8px 0 0">).*?(</p>)', r'\1{{tarifTitre}}\2{{tarifTxt}}\3')
    sec = resub(sec, r'(<div class="card"><p class="eyebrow">Premier cours</p>.*?<p class="muted" style="margin:8px 0 0">).*?(</p></div>)', r'\1{{essaiTxt}}\2')
    sec = resub(sec, r'(<p class="eyebrow">Lieu</p><p class="h3" style="margin-top:10px">)34, 37e Avenue(</p><p class="muted" style="margin:8px 0 0">).*?(</p>)', r'\1{{lieuTitre}}\2{{lieuTxt}}\3')
    ea = sec.index('<div class="card"><p class="eyebrow">Premier cours</p>')
    sec = wrap_between(sec, ea, '</p></div>', 'essaiOn')
    tpl = tpl[:a] + sc_if('infosOn', sec) + tpl[b:]
    return tpl


# ---------- Mariages ----------
MARIAGES_JS = r"""
    const PT = (typeof window !== 'undefined' && window.__ascilPrayer) || {};
    const V = PT.mariages || __DEFAULT__, st = this.state;
    const S = (V.etapes || []).filter((s) => s.on !== false && s.titre), D = ((V.docs || {}).items || []).filter((d) => d.on !== false && d.titre);
    const n = S.length, cur = Math.min(st.mstep, Math.max(0, n - 1)), done = D.filter((t, i) => st.mdocs[i]).length;
    const docsOn = (V.docs || {}).on !== false && D.length > 0, formOn = (V.form || {}).on !== false;
    return {
      hasSteps: n > 0, nSteps: n, stepsTitle: n + (n > 1 ? ' étapes' : ' étape') + (V.duree ? ' · ' + V.duree : ''),
      mSteps: S.map((s, i) => ({ t: s.titre, d: s.quand || '', num: i + 1, cur: i === cur ? 'step' : 'false', pick: () => this.setState({ mstep: i }),
        bg: i === cur ? '#0E4D3C' : (i < cur ? '#EAF3EF' : '#fff'), fg: i === cur ? '#fff' : '#1E2B26', bd: i === cur ? '#0E4D3C' : '#E4D9C0',
        nbg: i <= cur ? '#C49A4A' : '#F3EAD8', nfg: '#1E2B26' })),
      stepNum: cur + 1, stepPct: n ? Math.round((cur + 1) / n * 100) : 0,
      curTitle: n ? S[cur].titre : '', curWhen: n ? S[cur].quand || '' : '', curText: n ? S[cur].texte || '' : '',
      prevStep: () => this.setState({ mstep: Math.max(0, cur - 1) }), nextStep: () => this.setState({ mstep: Math.min(n - 1, cur + 1) }),
      docSecOn: docsOn || formOn, docsOn, formOn, nDocs: D.length,
      docs: D.map((d, i) => ({ t: d.titre, pressed: String(!!st.mdocs[i]), bg: st.mdocs[i] ? '#0E4D3C' : '#fff', bd: st.mdocs[i] ? '#0E4D3C' : '#E4D9C0', deco: st.mdocs[i] ? 'line-through' : 'none',
        toggle: () => this.setState({ mdocs: Object.assign({}, st.mdocs, { [i]: !st.mdocs[i] }) }) })),
      docCount: done, docPct: D.length ? Math.round(done / D.length * 100) : 0,
      rdv: st.rdv, rdvNot: !st.rdv,
      rdvSend: () => post({ source: 'mariages', nom: gv('m1'), contact: gv('m2'), sujet: 'Premier rendez-vous (mariage)',
        message: 'Demande de premier rendez-vous pour un mariage.', details: { 'Date de mariage souhaitée': gv('m3') } }, { rdv: true }),
      rdvBtn: sendVals('Envoyer la demande'), ...errVals,
      delaiTxt: V.delai ? 'Réponse sous ' + V.delai + '.' : '', hasDelai: !!V.delai,
      rdvNext: n > 1 ? 'Prochaine étape : ' + S[1].titre.charAt(0).toLowerCase() + S[1].titre.slice(1) + '.' : 'L’association vous répond bientôt.',
    };"""


def patch_mariages(tpl, default):
    tpl = strip_marks(tpl)
    tpl = set_xvals(tpl, MARIAGES_JS, default)
    tpl = rep(tpl, '>5 étapes · environ 6 semaines</h2>', '>{{stepsTitle}}</h2>')
    tpl = rep(tpl, 'Étape {{stepNum}} sur 5</p>', 'Étape {{stepNum}} sur {{nSteps}}</p>')
    a = tpl.rindex('<section', 0, tpl.index('aria-labelledby="par-t"'))
    tpl = wrap_between(tpl, a, '</section>', 'hasSteps')
    tpl = rep(tpl, '{{docCount}} sur 6 prêts</h2>', '{{docCount}} sur {{nDocs}} prêts</h2>')
    a = tpl.index('<p class="eyebrow">Ma liste de documents')
    a = tpl.rindex('<div>', 0, a)
    tpl = wrap_between(tpl, a, '</ul>\n  </div>', 'docsOn')
    a = tpl.index('<div class="card" style="padding:30px">\n   <sc-if value="{{rdvNot}}"')
    tpl = wrap_between(tpl, a, '</sc-if>\n  </div>', 'formOn')
    tpl = btn_send(tpl, 'rdvSend', 'Envoyer la demande', 'rdvBtn')
    tpl = rep(tpl, '<p class="muted" style="margin:0;font-size:14px">Réponse sous 3 jours ouvrables.</p>',
              sc_if('hasDelai', '<p class="muted" style="margin:0;font-size:14px">{{delaiTxt}}</p>'))
    tpl = rep(tpl, 'Prochaine étape : la rencontre avec l’imam.</p>', '{{rdvNext}}</p>')
    a = tpl.rindex('<section', 0, tpl.index('aria-labelledby="doc-t"'))
    tpl = wrap_between(tpl, a, '</section>', 'docSecOn')
    return tpl


# ---------- Funérailles ----------
PHONE_SVG = ('<svg class="icon" aria-hidden="true" width="22" height="22" sc-camel-view-box="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
             'stroke-linecap="round" stroke-linejoin="round" style="width:22px;height:22px"><path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6 '
             '19.8 19.8 0 0 1-3.1-8.7A2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1.9.4 1.8.7 2.7a2 2 0 0 1-.5 2.1L8 9.8a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.8.6 2.7.7a2 2 0 0 1 1.7 2z"></path></svg>')

FUNERAILLES_JS = r"""
    const PT = (typeof window !== 'undefined' && window.__ascilPrayer) || {};
    const V = PT.funerailles || __DEFAULT__, st = this.state;
    const tel = String(V.telephone || '').trim(), mail = String(V.courriel || '').trim() || '';
    const S = (V.etapes || []).filter((s) => s.on !== false && s.titre), D = ((V.docs || {}).items || []).filter((d) => d.on !== false && d.titre);
    const W = ['Aucune', 'Une', 'Deux', 'Trois', 'Quatre', 'Cinq', 'Six', 'Sept', 'Huit', 'Neuf', 'Dix'];
    const main = tel || mail;
    return {
      fuLead: tel ? 'Appelez le responsable des funérailles' + (V.h24 ? ', à toute heure du jour ou de la nuit.' : '.') : 'Contactez les responsables par courriel à ' + mail + '.',
      fuWho: (String(V.responsable || '').trim() || 'Responsable des funérailles') + (V.h24 ? ' · 24 h / 24' : ''),
      fuMain: main, fuHref: tel ? 'tel:' + tel.replace(/[^\d+]/g, '') : 'mailto:' + mail, fuIsTel: !!tel, fuIsMail: !tel,
      fuCta: tel ? 'Appeler maintenant' : 'Écrire par courriel',
      fuCopyTxt: tel ? 'Copier le numéro' : 'Copier l’adresse', fuCopiedTxt: tel ? 'Numéro copié' : 'Adresse copiée',
      fu911: V.rappel911 !== false,
      hasFSteps: S.length > 0, fuStepsTitle: (W[S.length] || S.length) + (S.length > 1 ? ' étapes, une à la fois' : ' étape'),
      fSteps: S.map((s, i) => ({ t: s.titre, d: s.texte || '', num: i + 1, pressed: String(!!st.fdone[i]), lab: st.fdone[i] ? 'Fait' : 'Marquer comme fait',
        bbg: st.fdone[i] ? '#0E4D3C' : '#fff', bfg: st.fdone[i] ? '#fff' : '#0E4D3C', bd: st.fdone[i] ? '#0E4D3C' : '#E4D9C0', bgc: st.fdone[i] ? '#F3F8F5' : '#fff',
        toggle: () => this.setState({ fdone: Object.assign({}, st.fdone, { [i]: !st.fdone[i] }) }) })),
      fuDocsOn: (V.docs || {}).on !== false && D.length > 0, fuDocs: D.map((d) => ({ t: d.titre })),
      fuChargeOn: (V.charge || {}).on !== false && !!(V.charge || {}).texte, fuCharge: (V.charge || {}).texte || '',
      telCopied: st.telc, telNot: !st.telc,
      copyTel: () => { try { navigator.clipboard && navigator.clipboard.writeText(main); } catch (e) {} this.setState({ telc: true }); clearTimeout(this.xto); this.xto = setTimeout(() => this.setState({ telc: false }), 2000); },
    };"""


def patch_funerailles(tpl, default):
    tpl = strip_marks(tpl)
    tpl = set_xvals(tpl, FUNERAILLES_JS, default)
    tpl = rep(tpl, 'Contactez les responsables par courriel à .</p>', '{{fuLead}}</p>')
    tpl = rep(tpl, '>Responsable des funérailles · 24 h / 24</p>', '>{{fuWho}}</p>')
    tpl = rep(tpl, 'overflow-wrap:anywhere"></p>', 'overflow-wrap:anywhere">{{fuMain}}</p>')
    m = re.search(r'<a class="btn btn-green" href="mailto:associationrdl\.ascil@gmail\.com" style="font-size:18px;min-height:56px">(<svg.*?</svg>)Écrire par courriel</a>', tpl, flags=re.S)
    assert m, 'bouton courriel introuvable'
    tpl = tpl.replace(m.group(0), '<a class="btn btn-green" href="{{fuHref}}" style="font-size:18px;min-height:56px">'
                      + sc_if('fuIsTel', PHONE_SVG, 'false') + sc_if('fuIsMail', m.group(1)) + '{{fuCta}}</a>')
    tpl = rep(tpl, '</svg>Copier le numéro</sc-if>', '</svg>{{fuCopyTxt}}</sc-if>')
    tpl = rep(tpl, '</svg>Numéro copié</sc-if>', '</svg>{{fuCopiedTxt}}</sc-if>')
    a = tpl.index('<p style="margin:18px 0 0;padding-top:14px;border-top:1px solid #E4D9C0;font-size:15px"><strong>Urgence médicale ?</strong>')
    tpl = wrap_between(tpl, a, '</p>', 'fu911')
    tpl = rep(tpl, '>Cinq étapes, une à la fois</h2>', '>{{fuStepsTitle}}</h2>')
    a = tpl.index('<section class="sec" aria-labelledby="qf-t"')
    tpl = wrap_between(tpl, a, '</section>', 'hasFSteps')
    tpl = resub(tpl, r'(<div class="card"><p class="eyebrow">Documents utiles</p><ul [^>]*>).*?(</ul>)',
                r'\1<sc-for list="{{fuDocs}}" as="x" hint-placeholder-count="4"><li>{{x.t}}</li></sc-for>\2')
    a = tpl.index('<div class="card"><p class="eyebrow">Documents utiles</p>')
    tpl = wrap_between(tpl, a, '</ul></div>', 'fuDocsOn')
    tpl = resub(tpl, r'(<div class="card"><p class="eyebrow">Ce que l’association prend en charge</p><p style="margin:12px 0 0">).*?(</p></div>)',
                r'\1{{fuCharge}}\2')
    a = tpl.index('<div class="card"><p class="eyebrow">Ce que l’association prend en charge</p>')
    tpl = wrap_between(tpl, a, '</p></div>', 'fuChargeOn')
    return tpl


# ---------- Aide alimentaire ----------
AIDE_JS = r"""
    const PT = (typeof window !== 'undefined' && window.__ascilPrayer) || {};
    const V = PT.aide || __DEFAULT__, st = this.state, F = V.form || {}, M = V.manque || {}, Dp = V.depot || {}, Ar = V.argent || {};
    const N = (F.besoins || []).filter((b) => b.on !== false && b.titre).map((b) => b.titre);
    const formOn = F.on !== false, sur = F.recup !== false, liv = F.livraison !== false;
    const pu = st.pu === 'liv' && liv ? 'liv' : (sur ? 'sur' : (liv ? 'liv' : ''));
    const LV = { tres: ['très demandé', 85], demande: ['demandé', 50], suffisant: ['suffisant', 15] };
    const mail = String(Ar.courriel || '').trim();
    return {
      isNeed: st.path === 'need', isGive: st.path === 'give', needP: String(st.path === 'need'), giveP: String(st.path === 'give'),
      goNeed: () => this.setState({ path: 'need' }), goGive: () => this.setState({ path: 'give' }),
      aFormOff: !formOn, contactHref: pre + 'Contact.dc.html',
      hh: st.hh, hhMinus: () => this.setState({ hh: Math.max(1, st.hh - 1) }), hhPlus: () => this.setState({ hh: Math.min(12, st.hh + 1) }),
      hasNeeds: N.length > 0,
      needOpts: N.map((n) => ({ label: n, pressed: String(!!st.needs[n]), bg: st.needs[n] ? '#0E4D3C' : '#fff', fg: st.needs[n] ? '#fff' : '#0E4D3C',
        pick: () => this.setState({ needs: Object.assign({}, st.needs, { [n]: !st.needs[n] }) }) })),
      hasPu: sur || liv, puSurOn: sur, puLivOn: liv,
      puSurP: String(pu === 'sur'), puLivP: String(pu === 'liv'), puSur: () => this.setState({ pu: 'sur' }), puLiv: () => this.setState({ pu: 'liv' }),
      aDone: st.aDone, aNot: formOn && !st.aDone,
      aSend: () => post({ source: 'aide', nom: gv('a1') || 'Anonyme', contact: gv('a2'), sujet: 'Demande d’aide alimentaire',
        message: 'Demande d’aide alimentaire.', details: { 'Personnes dans le foyer': st.hh, 'Besoins': N.filter((n) => st.needs[n]).join(', ') || 'Non précisé',
          'Récupération': pu === 'liv' ? 'Livraison' : pu === 'sur' ? 'Sur place' : 'Non précisé' } }, { aDone: true }),
      aBtn: sendVals('Envoyer ma demande'), ...errVals,
      aDoneTxt: 'Une personne de l’équipe vous contacte sous ' + (F.delai || '48 h') + ', en toute discrétion.',
      manqueOn: M.on !== false && (M.items || []).some((x) => x.on !== false && x.titre),
      manque: (M.items || []).filter((x) => x.on !== false && x.titre).map((x) => ({ t: x.titre, lv: (LV[x.niveau] || LV.demande)[0], w: (LV[x.niveau] || LV.demande)[1] })),
      depotOn: Dp.on !== false && !!(Dp.adresse || Dp.quand), depotAdr: Dp.adresse || '', depotQuand: Dp.quand || '', depotNote: Dp.note || '', hasDepotNote: !!Dp.note,
      argentOn: Ar.on !== false && !!mail, argentMail: mail, argentNote: Ar.note || '', hasArgentNote: !!Ar.note,
      aCopy: () => { try { navigator.clipboard && navigator.clipboard.writeText(mail); } catch (e) {} this.setState({ acpd: true }); clearTimeout(this.xto); this.xto = setTimeout(() => this.setState({ acpd: false }), 2000); },
      aCpd: !!st.acpd, aNc: !st.acpd,
    };"""


def patch_aide(tpl, default):
    tpl = strip_marks(tpl)
    tpl = set_xvals(tpl, AIDE_JS, default)
    off = ('<sc-if value="{{aFormOff}}" hint-placeholder-val="{{ false }}"><h2 class="h3" style="font-size:24px">Faire une demande</h2>'
           '<p style="margin:8px 0 0">Écrivez-nous depuis la page <a class="link" href="{{contactHref}}">Contact</a> : votre demande reste confidentielle.</p></sc-if>')
    tpl = rep(tpl, '<sc-if value="{{aNot}}" hint-placeholder-val="{{ true }}">', off + '<sc-if value="{{aNot}}" hint-placeholder-val="{{ true }}">')
    a = tpl.index('<div class="field"><span style="font-weight:700;font-size:15px">Ce qui vous aiderait</span>')
    tpl = wrap_between(tpl, a, '</sc-for></div></div>', 'hasNeeds')
    tpl = rep(tpl, '<button type="button" sc-camel-on-click="{{puSur}}" aria-pressed="{{puSurP}}">Sur place, discrètement</button>',
              sc_if('puSurOn', '<button type="button" sc-camel-on-click="{{puSur}}" aria-pressed="{{puSurP}}">Sur place, discrètement</button>'))
    tpl = rep(tpl, '<button type="button" sc-camel-on-click="{{puLiv}}" aria-pressed="{{puLivP}}">Livraison</button>',
              sc_if('puLivOn', '<button type="button" sc-camel-on-click="{{puLiv}}" aria-pressed="{{puLivP}}">Livraison</button>'))
    a = tpl.index('<div class="field"><span style="font-weight:700;font-size:15px">Récupération</span>')
    tpl = wrap_between(tpl, a, '</sc-if></div></div>', 'hasPu')
    tpl = btn_send(tpl, 'aSend', 'Envoyer ma demande', 'aBtn')
    tpl = rep(tpl, 'Une personne de l’équipe vous contacte sous 48 h, en toute discrétion.</p>', '{{aDoneTxt}}</p>')
    # Je veux aider
    tpl = resub(tpl, r'(<div class="card"><p class="eyebrow">Ce qui manque ce mois-ci</p><ul [^>]*>).*?(</ul></div>)',
                r'\1<sc-for list="{{manque}}" as="x" hint-placeholder-count="5"><li><div style="display:flex;justify-content:space-between;gap:10px;font-weight:600">'
                r'<span>{{x.t}}</span><span class="muted" style="font-weight:400">{{x.lv}}</span></div>'
                r'<div class="prog" style="background:#F3EAD8;margin-top:6px;height:8px"><i style="width:{{x.w}}%"></i></div></li></sc-for>\2')
    a = tpl.index('<div class="card"><p class="eyebrow">Ce qui manque ce mois-ci</p>')
    tpl = wrap_between(tpl, a, '</ul></div>', 'manqueOn')
    tpl = resub(tpl, r'(<p class="eyebrow">Déposer des denrées</p><p class="h3" style="margin-top:10px">)34, 37e Avenue(</p><p class="tnum" style="margin:8px 0 0">)Samedi et dimanche, 10 h – 14 h(</p>)'
                r'(<p class="muted" style="margin:8px 0 0">)Produits non périssables, non ouverts, non périmés\.(</p>)',
                r'\1{{depotAdr}}\2{{depotQuand}}\3<sc-if value="{{hasDepotNote}}" hint-placeholder-val="{{ true }}">\4{{depotNote}}\5</sc-if>')
    a = tpl.index('<div class="card"><p class="eyebrow">Déposer des denrées</p>')
    tpl = wrap_between(tpl, a, '</sc-if></div>', 'depotOn')
    tpl = rep(tpl, 'overflow-wrap:anywhere">associationrdl.ascil@<wbr>gmail.com</p>', 'overflow-wrap:anywhere">{{argentMail}}</p>')
    tpl = resub(tpl, r'(<p class="muted" style="margin:6px 0 0">)Indiquez « aide alimentaire » dans le message\.(</p>)',
                r'<sc-if value="{{hasArgentNote}}" hint-placeholder-val="{{ true }}">\1{{argentNote}}\2</sc-if>')
    tpl = rep(tpl, 'sc-camel-on-click="{{cp.mail}}" style="margin-top:14px" aria-live="polite"><sc-if value="{{nc.mail}}"',
              'sc-camel-on-click="{{aCopy}}" style="margin-top:14px" aria-live="polite"><sc-if value="{{aNc}}"')
    tpl = rep(tpl, 'Copier l’adresse</sc-if><sc-if value="{{cpd.mail}}"', 'Copier l’adresse</sc-if><sc-if value="{{aCpd}}"')
    a = tpl.index('<div class="card"><p class="eyebrow">Donner de l’argent</p>')
    tpl = wrap_between(tpl, a, 'Adresse copiée</sc-if></button></div>', 'argentOn')
    return tpl


# ---------- Espace femmes ----------
FEMMES_JS = r"""
    const PT = (typeof window !== 'undefined' && window.__ascilPrayer) || {};
    const V = PT.femmes || __DEFAULT__, st = this.state, P = V.pratique || {}, R = V.regles || {};
    const NAMES = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche'], keys = ['lun', 'mar', 'mer', 'jeu', 'ven', 'sam', 'dim'];
    const mn = (v) => { const m = /^(\d\d):(\d\d)$/.exec(v || ''); return m ? (+m[1]) * 60 + (+m[2]) : null; };
    const fmt = (m) => Math.floor(m / 60) + ' h' + (m % 60 ? ' ' + String(m % 60).padStart(2, '0') : '');
    const HF = {};
    keys.forEach((k, i) => {
      const d = (V.jours || [])[i] || {}, slots = [];
      if (d.on) [[d.de1, d.a1], [d.de2, d.a2]].forEach((p) => { const a = mn(p[0]), b = mn(p[1]); if (a !== null && b !== null && b > a) slots.push([a, b]); });
      HF[k] = [NAMES[i], slots.length ? slots.map((s) => fmt(s[0]) + ' – ' + fmt(s[1])).join(' · ') : 'Fermé', slots];
    });
    let wd = 'lun', mins = 0, ymd = '';
    try { const p = new Intl.DateTimeFormat('en-US', { timeZone: 'America/Moncton', weekday: 'short', hour: '2-digit', minute: '2-digit', hourCycle: 'h23' }).formatToParts(new Date(this.state.now));
      const g = (t) => (p.find((x) => x.type === t) || {}).value; wd = { Mon: 'lun', Tue: 'mar', Wed: 'mer', Thu: 'jeu', Fri: 'ven', Sat: 'sam', Sun: 'dim' }[g('weekday')] || 'lun'; mins = (+g('hour')) * 60 + (+g('minute'));
      ymd = new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Moncton', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date(this.state.now)); } catch (e) {}
    const closedToday = !!V.fermeture && V.fermeture === ymd;
    const today = HF[wd], slot = closedToday ? null : today[2].find((s) => mins >= s[0] && mins < s[1]);
    const nextS = closedToday ? null : today[2].find((s) => s[0] > mins);
    let nextTxt = '';
    for (let n = 1; n <= 7 && !nextTxt; n++) { const k = keys[(keys.indexOf(wd) + n) % 7]; if (HF[k][2].length) nextTxt = 'Ouvre ' + (n === 1 ? 'demain' : HF[k][0].toLowerCase()) + ' à ' + fmt(HF[k][2][0][0]); }
    const sel = st.fday || wd;
    const PR = [['Entrée', P.entree], ['Accès', P.acces], ['Ablutions', P.ablutions], ['Jumu’a', P.jumua], ['Enfants', P.enfants], ['Responsable', P.responsable]];
    const pr = {};
    PR.forEach((x, i) => { pr['f' + i] = String(x[1] || '').trim(); });
    const RG = (R.items || []).filter((x) => x.on !== false && x.titre);
    return {
      openTxt: slot ? 'Ouvert' : 'Fermé', openDot: slot ? '#7BE0A6' : '#E8A39C',
      openSub: closedToday ? 'Fermeture exceptionnelle aujourd’hui' : slot ? 'Jusqu’à ' + fmt(slot[1]) + ' aujourd’hui' : (nextS ? 'Ouvre à ' + fmt(nextS[0]) + ' aujourd’hui' : (nextTxt || 'Horaires à venir')),
      fDays: keys.map((k) => ({ short: HF[k][0].slice(0, 3) + '.', pressed: String(k === sel), bg: k === sel ? '#C49A4A' : 'rgba(255,255,255,.1)', fg: k === sel ? '#1E2B26' : '#fff', pick: () => this.setState({ fday: k }) })),
      dayName: HF[sel][0], dayHours: closedToday && sel === wd ? 'Fermé aujourd’hui' : HF[sel][1],
      planOn: !!V.plan, planSrc: V.plan || '',
      pratOn: P.on !== false && PR.some((x) => String(x[1] || '').trim()), pr, prOn: Object.fromEntries(Object.keys(pr).map((k) => [k, !!pr[k]])),
      reglesOn: R.on !== false && RG.length > 0, regles: RG.map((x) => ({ t: x.titre })),
    };"""


def patch_femmes(tpl, default):
    tpl = strip_marks(tpl)
    tpl = set_xvals(tpl, FEMMES_JS, default)
    m = re.search(r'(<div class="card" style="padding:24px">\s*<p class="eyebrow">Plan d’accès</p>)\s*(<svg.*?</svg>)\s*(</div>)', tpl, flags=re.S)
    assert m, 'plan d’accès introuvable'
    tpl = tpl.replace(m.group(0), sc_if('planOn', m.group(1) + '<img src="{{planSrc}}" alt="Plan d’accès de l’espace femmes" '
                                         'style="display:block;width:100%;height:auto;margin-top:12px;border-radius:14px">' + m.group(3), 'false'))
    for i, label in enumerate(['Entrée', 'Accès', 'Ablutions', 'Jumu’a', 'Enfants', 'Responsable']):
        mm = re.search(r'<div class="card" style="display:flex;gap:14px;align-items:flex-start">(?:(?!<div class="card").)*?<p style="margin:0;font-weight:800">'
                       + re.escape(label) + r'</p><p style="margin:4px 0 0;overflow-wrap:anywhere">.*?</p></div></div>', tpl, flags=re.S)
        assert mm, f'carte {label} introuvable'
        card = re.sub(r'(<p style="margin:4px 0 0;overflow-wrap:anywhere">).*?(</p></div></div>)$', r'\1{{pr.f' + str(i) + r'}}\2', mm.group(0), flags=re.S)
        tpl = tpl.replace(mm.group(0), sc_if(f'prOn.f{i}', card))
    a = tpl.index('<section aria-label="Informations pratiques"')
    tpl = wrap_between(tpl, a, '</section>', 'pratOn')
    tpl = resub(tpl, r'(<h2 id="rg-t"[^>]*>Un lieu calme et respectueux</h2>\s*<ul [^>]*>).*?(</ul>)',
                r'\1<sc-for list="{{regles}}" as="x" hint-placeholder-count="4"><li>{{x.t}}</li></sc-for>\2')
    a = tpl.index('<section class="sand" aria-labelledby="rg-t"')
    tpl = wrap_between(tpl, a, '</section>', 'reglesOn')
    return tpl


PAGES = [('N2-Cours', 'cours', patch_cours), ('N2-Mariages', 'mariages', patch_mariages), ('N2-Funerailles', 'funerailles', patch_funerailles),
         ('N2-AideAlimentaire', 'aide', patch_aide), ('N2-EspaceFemmes', 'femmes', patch_femmes)]


def defaults():
    """Valeurs par défaut lues dans functions/_lib/settings.js (source unique) via Node."""
    import subprocess
    lib = ROOT / 'functions' / '_lib' / 'settings.js'
    code = ("import(process.argv[1]).then((S) => { const o = {}; for (const k of ['cours','mariages','funerailles','aide','femmes']) o[k] = S.DEFAULT_SETTINGS[k];"
            " process.stdout.write(JSON.stringify(o)); });")
    out = subprocess.run(['node', '-e', code, lib.as_uri()], capture_output=True, text=True, check=True).stdout
    return json.loads(out)


# Inscription aux cours : téléphone (préféré) ou courriel, l'un des deux suffit.
R2_OLD = '<div class="field"><label for="r2">Courriel</label><input id="r2" type="email" autocomplete="email"></div>'
R2_NEW = ('<p style="margin:0;font-weight:700;font-size:15px">Pour vous joindre : un téléphone (de préférence) ou un courriel</p>'
          '<div class="field"><label for="r2">Téléphone (de préférence)</label><input id="r2" type="tel" inputmode="tel" autocomplete="tel" maxlength="30"></div>'
          '<div class="field"><label for="r4">Courriel (si pas de téléphone)</label><input id="r4" type="email" autocomplete="email" maxlength="200"></div>')


def contact_cours(tpl, name):
    if R2_NEW in tpl:
        return tpl
    assert tpl.count(R2_OLD) == 1, 'champ Courriel du formulaire introuvable dans ' + name
    return tpl.replace(R2_OLD, R2_NEW, 1)


def wire_public():
    D = defaults()
    for name, key, fn in PAGES:
        for prefix in ('', 'M-', 'T-'):
            path = ROOT / f'{prefix}{name}.dc.html'
            s, i, j, tpl = load(path)
            if '/*ascil-svx*/' in tpl:
                tpl = set_xvals(tpl, {'cours': COURS_JS, 'mariages': MARIAGES_JS, 'funerailles': FUNERAILLES_JS, 'aide': AIDE_JS, 'femmes': FEMMES_JS}[key], D[key])
            else:
                tpl = fn(tpl, D[key])
            if key == 'cours':
                tpl = contact_cours(tpl, path.name)
            save(path, s, i, j, tpl)
    print('15 pages publiques des services (Cours, Mariages, Funérailles, Aide alimentaire, Espace femmes ; PC, M-, T-) reliées aux réglages')


if __name__ == '__main__':
    wire_panel()
    wire_public()
