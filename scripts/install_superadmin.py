"""Installe le frontend superadmin dans le site ASCIL.

Source : la planche /Users/mac/Documents/mosque/superadmin.html (15 maquettes).
Chaque maquette est une page bundlée complète, au même format que les pages du site.
On garde la version PC de chaque écran (les versions mobile et tablette sont le même code,
fluide grâce aux container queries), et on écrit :
  SA-Connexion, SA-Panneau, SA-Site, SA-Pages, SA-PageEditeur, SA-Horaires, SA-APropos,
  SA-Services, SA-Dons, SA-Evenements, SA-Ressources, SA-Contact (.dc.html)
  superadmin.html = point d'entrée (copie de SA-Connexion.dc.html)
Puis on ajoute un lien discret « Espace administration » dans le pied de page du site.

ATTENTION : régénérer les pages SA-* efface les branchements ajoutés ensuite par les scripts
wire_*.py. Ce script les relance donc automatiquement, dans cet ordre obligatoire :
  1. install_superadmin.py   (ce script : pages SA-* depuis la maquette)
  2. wire_ramadan.py         (thème Ramadan : Accueil et page du mois depuis les maquettes, lien du menu en saison)
  3. wire_aid.py             (thèmes Aïd al-Fitr et Aïd al-Adha : Accueil et page de la fête depuis les maquettes)
  4. wire_vendredi.py        (thème du vendredi : Accueil, Horaires et Khutba du vendredi depuis la maquette)
  5. wire_homepage.py        (accueil public + panneau Accueil + bandeau statistiques)
  6. wire_events.py          (inscriptions publiques)
  7. wire_site.py            (Site entier → Pages publiées, Compte et sécurité + liens du site public)
  8. wire_pages.py           (Créer une page : « Mes pages » et éditeur)
  9. wire_horaires.py        (panneau Horaires du mois : tableau mensuel, copie, collage Excel, réglages)
 10. wire_prieres.py         (site public : heures de prière tirées de la base, page Horaires)
 11. wire_apropos.py         (panneau À propos + pages publiques À propos et Campagne en direct)
 12. wire_services.py        (panneau Services + page publique Services)
 13. wire_service_pages.py   (onglets Cours, Mariages, Funérailles, Aide alimentaire, Espace femmes + leurs pages)
 14. wire_dons.py            (Faire un don : panneau Page Dons et Bloc Merci + page Dons publique)
 15. wire_evenements.py      (Événements : liste, à la une, calendrier du mois, inscriptions + pages publiques)
 16. wire_ressources.py      (Ressources : nouveaux arrivants, mur Dua et annonces avec modération + pages publiques)
 17. wire_inbox.py           (boîte de réception : Contact → Demandes reçues, formulaire Contact)
 18. wire_contact.py         (Contact : page Contact, page 404 et nouvelle page 404.html)
 19. wire_formulaires.py     (nouvelle rubrique Formulaires : formulaires créés et leurs réponses)
 20. wire_traductions.py     (nouvelle rubrique Traductions : textes du panneau en arabe et en anglais)
 21. wire_pied.py            (réglages communs : coordonnées et pied de page sur toutes les pages publiques)
 22. wire_nettoyage.py       (dernières mentions de brouillon retirées)
 23. wire_photos.py          (photos de l'Accueil choisies dans le panneau Accueil)
 24. wire_langues.py         (versions arabe et anglaise : sélecteur, dictionnaires i18n/ar.json et i18n/en.json)
 25. wire_gratuit.py         (page « Un site gratuit pour votre mosquée » et son lien du pied de page)
 26. fix_inputs.py           (libère les champs figés par la maquette : TOUJOURS en dernier)
Option --sans-branchements : ne relance pas les étapes 2 à 26 (déconseillé).

Usage : python3 scripts/install_superadmin.py /chemin/superadmin.html /chemin/ascil-mosquee
"""
import base64, gzip, json, re, subprocess, sys, zlib, pathlib

SRC = pathlib.Path(sys.argv[1])
ROOT = pathlib.Path(sys.argv[2])
OPEN = '<script type="__bundler/template">'
VIEWPORT = '<meta name="viewport" content="width=device-width, initial-scale=1">'
ROBOTS = '<meta name="robots" content="noindex, nofollow">'

SCREENS = {  # titre de la planche -> fichier
    'Connexion · PC': 'SA-Connexion.dc.html',
    'Panneau · PC': 'SA-Panneau.dc.html',
    'Superadmin · Site entier': 'SA-Site.dc.html',
    'Superadmin · Horaires': 'SA-Horaires.dc.html',
    'Superadmin · À propos': 'SA-APropos.dc.html',
    'Superadmin · Services': 'SA-Services.dc.html',
    'Superadmin · Faire un don': 'SA-Dons.dc.html',
    'Superadmin · Événements': 'SA-Evenements.dc.html',
    'Superadmin · Ressources': 'SA-Ressources.dc.html',
    'Superadmin · Contact': 'SA-Contact.dc.html',
    'Superadmin · Créer une page': 'SA-Pages.dc.html',
    'Superadmin · Éditeur de page': 'SA-PageEditeur.dc.html',
}
TITLES = {'SA-Panneau.dc.html': 'Superadmin · Accueil — ASCIL'}

# Boutons « Voir la page » vers des pages que le site n'a pas encore.
MISSING = ['Page404.dc.html', 'Merci.dc.html', 'EvenementDetail.dc.html']


def split(text):
    i = text.index(OPEN) + len(OPEN)
    j = text.index('</script>', i)
    return i, j, json.loads(text[i:j])


def join(text, i, j, tpl):
    enc = json.dumps(tpl).replace('</', '<\\u002F')
    assert json.loads(enc) == tpl
    return text[:i] + enc + text[j:]


def disable_missing(tpl):
    def repl(m):
        inner = m.group(2)
        return ('<span class="btn btn-line" aria-disabled="true" title="Cette page n’existe pas encore sur le site public"'
                ' style="min-height:40px;opacity:.5;cursor:not-allowed">' + inner + '</span>')
    for name in MISSING:
        pat = re.compile(r'<a class="btn btn-line" href="' + re.escape(name) + r'"( style="min-height:40px")>(.*?)</a>', re.S)
        tpl, n = pat.subn(repl, tpl)
        assert name not in tpl, name
    return tpl


# Sur tablette et mobile le menu latéral est masqué et remplacé par des listes
# « Page à gérer » / « Aller au widget » qui, dans la maquette, ne faisaient rien.
NAV_SCRIPT = r'''<script id="sa-nav">
(function () {
  var PAGES = {
    'Accueil': 'SA-Panneau.dc.html', 'Site entier': 'SA-Site.dc.html', 'Créer une page': 'SA-Pages.dc.html',
    'Horaires': 'SA-Horaires.dc.html', 'À propos': 'SA-APropos.dc.html', 'Services': 'SA-Services.dc.html',
    'Faire un don': 'SA-Dons.dc.html', 'Événements': 'SA-Evenements.dc.html', 'Ressources': 'SA-Ressources.dc.html',
    'Contact': 'SA-Contact.dc.html', 'Formulaires': 'SA-Formulaires.dc.html', 'Traductions': 'SA-Traductions.dc.html', 'Comptes': 'SA-Comptes.html'
  };
  function labelOf(el) {
    var l = el.id && document.querySelector('label[for="' + el.id + '"]');
    return l ? l.textContent.trim() : '';
  }
  document.addEventListener('change', function (e) {
    var t = e.target;
    if (!t || t.tagName !== 'SELECT' || (t.id !== 'jump' && t.id !== 'jump-page')) return;
    var v = t.value.trim();
    if (labelOf(t).indexOf('Page') === 0) {
      var href = PAGES[v];
      if (href && location.pathname.split('/').pop() !== href) location.href = href;
      return;
    }
    var links = document.querySelectorAll('nav.side a[href^="#"]');
    for (var i = 0; i < links.length; i++) {
      var first = links[i].firstChild ? links[i].firstChild.textContent.trim() : '';
      if (first === v) {
        var target = document.getElementById(links[i].getAttribute('href').slice(1));
        if (target) {
          var hdr = document.querySelector('header.top');
          var off = (hdr && getComputedStyle(hdr).position === 'sticky' ? hdr.offsetHeight : 0) + 12;
          window.scrollTo({ top: target.getBoundingClientRect().top + window.scrollY - off,
            behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
          var f = target.querySelector('h2, [tabindex]');
          if (f) { f.setAttribute('tabindex', '-1'); f.focus({ preventScroll: true }); }
        }
        return;
      }
    }
  });
})();
</script>
'''


# Déconnexion : les liens « Se déconnecter » ferment la session côté serveur.
LOGOUT_SCRIPT = r'''<script id="sa-logout">
document.addEventListener('click', function (e) {
  var a = e.target.closest && e.target.closest('a[href="SA-Connexion.dc.html"]');
  if (!a) return;
  e.preventDefault();
  a.setAttribute('aria-busy', 'true');
  fetch('/api/auth/logout', { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json' }, body: '{}' })
    .catch(function () {})
    .then(function () { location.href = 'superadmin.html'; });
});
</script>
'''

# Connexion : le formulaire de la maquette était un simple lien vers le panneau.
LOGIN_STYLE = '''<style id="sa-login-style">
.lg-in[aria-invalid="true"]{border-color:#B3261E}
.lg-err{margin:0;padding:10px 14px;border-radius:12px;background:#FBEAE8;color:#8C1D18;font-size:14px;line-height:1.45}
.lg-info{margin:0;padding:10px 14px;border-radius:12px;background:#F7F2E4;color:#4F5E57;font-size:14px;line-height:1.45}
.lg-btn[aria-busy="true"]{cursor:progress}
.lg-spin{width:18px;height:18px;border-radius:50%;border:2.5px solid rgba(255,255,255,.35);border-top-color:#fff;animation:lgspin .8s linear infinite}
@keyframes lgspin{to{transform:rotate(360deg)}}
@media (prefers-reduced-motion: reduce){.lg-spin{animation-duration:2.4s}}
</style>
'''
LOGIN_SCRIPT = r'''<script id="sa-login-js">
(function () {
  function nextUrl(home) {
    var n = new URLSearchParams(location.search).get('next') || '';
    return /^\/SA-[A-Za-z]+(\.dc)?(\.html)?(\?[^#]*)?$/.test(n) && !/SA-Connexion/.test(n) ? n : (home || 'SA-Panneau.dc.html');
  }
  // Compte créé ou réinitialisé par le superadmin : il choisit d'abord son propre mot de passe.
  function showChange(current) {
    var login = document.getElementById('sa-login'), change = document.getElementById('sa-change');
    if (!login || !change) return;
    login.style.display = 'none';
    change.style.display = 'flex';
    var cur = document.getElementById('sa-cur');
    if (current) { cur.value = current; document.getElementById('sa-cur-wrap').style.display = 'none'; }
    (current ? document.getElementById('sa-new') : cur).focus();
  }
  fetch('/api/auth/me', { credentials: 'same-origin' }).then(function (r) { return r.ok ? r.json() : null; })
    .then(function (d) { if (d && d.ok && d.admin.mustChangePassword) showChange(''); }, function () {});
  document.addEventListener('submit', function (e) {
    var f = e.target;
    if (!f || f.id !== 'sa-change') return;
    e.preventDefault();
    var cur = document.getElementById('sa-cur'), n1 = document.getElementById('sa-new'), n2 = document.getElementById('sa-new2');
    var btn = document.getElementById('sa-change-btn'), err = document.getElementById('sa-change-err');
    if (btn.getAttribute('aria-busy') === 'true') return;
    [cur, n1, n2].forEach(function (x) { x.removeAttribute('aria-invalid'); });
    show(err, '');
    var bad = !cur.value ? [cur, 'Entrez le mot de passe provisoire reçu.']
      : n1.value.length < 12 ? [n1, 'Le nouveau mot de passe doit contenir au moins 12 caractères. Une courte phrase fonctionne bien.']
      : n1.value !== n2.value ? [n2, 'Les deux mots de passe ne correspondent pas. Retapez-le.'] : null;
    if (bad) { bad[0].setAttribute('aria-invalid', 'true'); show(err, bad[1]); bad[0].focus(); return; }
    var label = btn.innerHTML;
    btn.setAttribute('aria-busy', 'true');
    btn.innerHTML = '<span class="lg-spin" aria-hidden="true"></span>Enregistrement…';
    fetch('/api/auth/password', {
      method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ current: cur.value, next: n1.value })
    }).then(function (r) {
      return r.json().catch(function () { return { ok: false, message: 'Le serveur ne répond pas correctement. Réessayez dans un instant.' }; });
    }).then(function (d) {
      if (d.ok) { location.href = nextUrl(d.home); return; }
      btn.removeAttribute('aria-busy'); btn.innerHTML = label;
      if (d.code === 'wrong_current') { document.getElementById('sa-cur-wrap').style.display = ''; cur.value = ''; cur.setAttribute('aria-invalid', 'true'); cur.focus(); }
      show(err, d.message || 'L’enregistrement a échoué. Réessayez.');
    }, function () {
      btn.removeAttribute('aria-busy'); btn.innerHTML = label;
      show(err, 'Impossible de joindre le serveur. Vérifiez votre connexion Internet et réessayez.');
    });
  });
  function show(el, msg) { if (!el) return; el.textContent = msg; el.hidden = !msg; }
  document.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('#sa-forgot');
    if (!a) return;
    e.preventDefault();
    show(document.getElementById('sa-login-info'),
      'Le mot de passe se réinitialise depuis l’ordinateur du responsable technique de l’ASCIL. Contactez-le pour en obtenir un nouveau.');
  });
  document.addEventListener('submit', function (e) {
    var f = e.target;
    if (!f || f.id !== 'sa-login') return;
    e.preventDefault();
    var id = document.getElementById('sa-id'), pw = document.getElementById('sa-pw');
    var rem = document.getElementById('sa-remember'), btn = document.getElementById('sa-login-btn');
    var err = document.getElementById('sa-login-err');
    if (btn.getAttribute('aria-busy') === 'true') return;
    id.removeAttribute('aria-invalid'); pw.removeAttribute('aria-invalid'); show(err, '');
    if (!id.value.trim() || !pw.value) {
      (!id.value.trim() ? id : pw).setAttribute('aria-invalid', 'true');
      show(err, 'Entrez votre identifiant et votre mot de passe.');
      (!id.value.trim() ? id : pw).focus();
      return;
    }
    var label = btn.innerHTML;
    btn.setAttribute('aria-busy', 'true');
    btn.innerHTML = '<span class="lg-spin" aria-hidden="true"></span>Connexion…';
    fetch('/api/auth/login', {
      method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: id.value.trim(), password: pw.value, remember: !!(rem && rem.checked) })
    }).then(function (r) {
      return r.json().catch(function () { return { ok: false, message: 'Le serveur ne répond pas correctement. Réessayez dans un instant.' }; });
    }).then(function (d) {
      if (d.ok && d.mustChangePassword) { btn.removeAttribute('aria-busy'); btn.innerHTML = label; showChange(pw.value); return; }
      if (d.ok) { location.href = nextUrl(d.home); return; }
      btn.removeAttribute('aria-busy'); btn.innerHTML = label;
      if (d.code === 'invalid') { pw.setAttribute('aria-invalid', 'true'); pw.value = ''; pw.focus(); }
      show(err, d.message || 'La connexion a échoué. Réessayez.');
    }, function () {
      btn.removeAttribute('aria-busy'); btn.innerHTML = label;
      show(err, 'Impossible de joindre le serveur. Vérifiez votre connexion Internet et réessayez.');
    });
  });
})();
</script>
'''


CHANGE_FORM = (
    '<form id="sa-change" novalidate style="display:none;flex-direction:column;gap:16px">'
    '<div><p style="margin:0;font-weight:700;font-size:18px;color:#0E4D3C">Choisissez votre mot de passe</p>'
    '<p style="margin:6px 0 0;font-size:14px;color:#4F5E57">Votre compte utilise un mot de passe provisoire. '
    'Choisissez-en un à vous : 12 caractères minimum. Une courte phrase fonctionne bien.</p></div>'
    '<div id="sa-cur-wrap" style="display:flex;flex-direction:column;gap:6px">'
    '<label for="sa-cur" style="font-weight:600;font-size:14px">Mot de passe provisoire</label>'
    '<input class="lg-in" id="sa-cur" type="password" autocomplete="current-password"></div>'
    '<div style="display:flex;flex-direction:column;gap:6px">'
    '<label for="sa-new" style="font-weight:600;font-size:14px">Nouveau mot de passe</label>'
    '<input class="lg-in" id="sa-new" type="password" autocomplete="new-password" aria-describedby="sa-change-err"></div>'
    '<div style="display:flex;flex-direction:column;gap:6px">'
    '<label for="sa-new2" style="font-weight:600;font-size:14px">Confirmez le nouveau mot de passe</label>'
    '<input class="lg-in" id="sa-new2" type="password" autocomplete="new-password"></div>'
    '<p id="sa-change-err" class="lg-err" role="alert" hidden></p>'
    '<button type="submit" class="lg-btn btn" id="sa-change-btn">Enregistrer mon mot de passe</button>'
    '</form>'
)


def fix_login(tpl):
    rep = [
        ('<form style="display:flex;flex-direction:column;gap:16px">',
         '<form id="sa-login" novalidate style="display:flex;flex-direction:column;gap:16px">'),
        (' type="password" autocomplete="current-password" value="motdepasse">',
         ' type="password" autocomplete="current-password" aria-describedby="sa-login-err">'),
        ('<a href="#" style="font-size:14px;font-weight:600">Mot de passe oublié ?</a>',
         '<a href="#sa-login-info" id="sa-forgot" style="font-size:14px;font-weight:600">Mot de passe oublié ?</a>'),
        ('<input type="checkbox" style="width:20px;height:20px;accent-color:#0E4D3C;margin:0">',
         '<input type="checkbox" id="sa-remember" style="width:20px;height:20px;accent-color:#0E4D3C;margin:0">'),
    ]
    for a, b in rep:
        assert tpl.count(a) == 1, a
        tpl = tpl.replace(a, b)
    tpl, n = re.subn(r'<a class="lg-btn btn" href="SA-Panneau\.dc\.html">(Se connecter.*?)</a>',
                     lambda m: '<p id="sa-login-err" class="lg-err" role="alert" hidden></p>'
                               '<p id="sa-login-info" class="lg-info" role="status" hidden></p>'
                               '<button type="submit" class="lg-btn btn" id="sa-login-btn">' + m.group(1) + '</button>',
                     tpl, count=1, flags=re.S)
    assert n == 1
    k = tpl.index('</form>', tpl.index('id="sa-login"')) + len('</form>')
    tpl = tpl[:k] + CHANGE_FORM + tpl[k:]
    k = tpl.index('</head>')
    tpl = tpl[:k] + LOGIN_STYLE + tpl[k:]
    k = tpl.rindex('</body>')
    return tpl[:k] + LOGIN_SCRIPT + tpl[k:]


# Rôle connecté : badge du haut, et menus limités aux pages que ce rôle peut ouvrir.
# Le serveur refuse de toute façon les autres pages (functions/_lib/roles.js) ; ceci évite
# d'afficher des liens qui ne mèneraient nulle part.
ROLE_SCRIPT = r'''<script id="sa-role">
(function () {
  var ALLOW = { superadmin: null, editor: { not: ['SA-Comptes'] }, events: { only: ['SA-Evenements'] } };
  var NAMES = { 'Accueil': 'SA-Panneau', 'Site entier': 'SA-Site', 'Créer une page': 'SA-Pages', 'Horaires': 'SA-Horaires',
    'À propos': 'SA-APropos', 'Services': 'SA-Services', 'Faire un don': 'SA-Dons', 'Événements': 'SA-Evenements',
    'Ressources': 'SA-Ressources', 'Contact': 'SA-Contact', 'Formulaires': 'SA-Formulaires', 'Traductions': 'SA-Traductions', 'Comptes': 'SA-Comptes' };
  var me = null;
  function ok(key) {
    var r = ALLOW[me.role];
    if (r === null) return true;
    if (!r) return false;
    return r.only ? r.only.indexOf(key) > -1 : r.not.indexOf(key) === -1;
  }
  function apply() {
    if (!me) return;
    document.querySelectorAll('.lg-tag').forEach(function (t) { if (t.textContent !== me.roleLabel) t.textContent = me.roleLabel; });
    document.querySelectorAll('a[href^="SA-"]').forEach(function (a) {
      var m = /^(SA-[A-Za-z]+)/.exec(a.getAttribute('href'));
      if (m && m[1] !== 'SA-Connexion' && !ok(m[1]) && !a.hidden) { a.hidden = true; a.style.display = 'none'; }
    });
    document.querySelectorAll('select#jump-page option, select#jump option').forEach(function (o) {
      var key = NAMES[o.textContent.trim()];
      var sel = o.parentElement, lbl = sel.id && document.querySelector('label[for="' + sel.id + '"]');
      if (key && lbl && lbl.textContent.trim().indexOf('Page') === 0 && !ok(key) && !o.hidden) { o.hidden = true; o.disabled = true; }
    });
  }
  fetch('/api/auth/me', { credentials: 'same-origin' }).then(function (r) { return r.ok ? r.json() : null; }).then(function (d) {
    if (!d || !d.ok) return;
    me = d.admin;
    apply();
    new MutationObserver(apply).observe(document.body, { childList: true, subtree: true });
  }, function () {});
})();
</script>
'''


def add_comptes(tpl):
    # Lien « Comptes » en fin de menu latéral, et option dans la liste « Page à gérer » (mobile, tablette).
    tpl, n = re.subn(r'(<nav class="side nav"[^>]*>.*?)(</nav>)', r'\1<a href="SA-Comptes.html">Comptes</a>\2', tpl, count=1, flags=re.S)
    assert n == 1
    sel = 'jump-page' if 'id="jump-page"' in tpl else 'jump'
    tpl, n = re.subn(r'(<sc-raw-select class="in" id="' + sel + r'">.*?)(</sc-raw-select>)', r'\1<option>Comptes</option>\2', tpl, count=1, flags=re.S)
    assert n == 1 or 'id="' + sel + '"' not in tpl, sel  # l'éditeur de page n'a pas de liste
    return tpl


def fix_sa(text, out_name):
    if 'name="viewport"' not in text.split(OPEN)[0]:
        text = text.replace('<meta charset="utf-8">', '<meta charset="utf-8">\n  ' + VIEWPORT + '\n  ' + ROBOTS, 1)
    i, j, tpl = split(text)
    if 'name="viewport"' not in tpl:
        tpl = tpl.replace('<meta charset="utf-8">', '<meta charset="utf-8">\n' + VIEWPORT + '\n' + ROBOTS, 1)
        assert 'name="viewport"' in tpl
    tpl = disable_missing(tpl)
    if 'id="sa-nav"' not in tpl:
        k = tpl.rindex('</body>')
        tpl = tpl[:k] + NAV_SCRIPT + tpl[k:]
    if out_name == 'SA-Connexion.dc.html':
        tpl = fix_login(tpl)
    elif 'id="sa-logout"' not in tpl:
        k = tpl.rindex('</body>')
        tpl = tpl[:k] + LOGOUT_SCRIPT + ROLE_SCRIPT + tpl[k:]
        if 'href="SA-Comptes.html"' not in tpl and '<nav class="side nav"' in tpl:
            tpl = add_comptes(tpl)
    if out_name in TITLES:
        tpl = re.sub(r'<title>.*?</title>', '<title>' + TITLES[out_name] + '</title>', tpl, count=1)
    return join(text, i, j, tpl)


# 1. Pages superadmin
board = SRC.read_text(encoding='utf-8')
bi, bj, btpl = split(board)
manifest = json.loads(re.search(r'<script type="__bundler/manifest"[^>]*>(.*?)</script>', board, re.S).group(1))
frames = dict(re.findall(r'<h2>(.*?)</h2><iframe src="about:blank#([0-9a-f-]+)"', btpl))
for title, out in SCREENS.items():
    raw = base64.b64decode(manifest[frames[title]]['data'])
    try:
        page = gzip.decompress(raw)
    except OSError:
        page = zlib.decompress(raw, -15)
    page = page.decode('utf-8')
    (ROOT / out).write_text(fix_sa(page, out), encoding='utf-8')
    print('écrit', out)

(ROOT / 'superadmin.html').write_text((ROOT / 'SA-Connexion.dc.html').read_text(encoding='utf-8'), encoding='utf-8')
print('superadmin.html = SA-Connexion.dc.html')

# 2. Lien depuis le site public (pied de page de toutes les pages)
ANCHOR = 'Islamique Louperivoise — Edmundston, Québec</p>'
LINK = ('Islamique Louperivoise — Edmundston, Québec'
        '<a href="superadmin.html" rel="nofollow" style="float:right;color:#F3EAD8;opacity:.75;'
        'text-decoration:underline;text-underline-offset:3px;display:inline-block;padding:4px 0;margin-left:16px">'
        'Espace administration</a></p>')
n = 0
for p in sorted(ROOT.glob('*.dc.html')) + [ROOT / 'index.html']:
    if p.name.startswith('SA-'):
        continue
    s = p.read_text(encoding='utf-8')
    i, j, tpl = split(s)
    if 'href="superadmin.html"' in tpl:
        continue
    assert tpl.count(ANCHOR) == 1, p.name
    tpl = tpl.replace(ANCHOR, LINK)
    p.write_text(join(s, i, j, tpl), encoding='utf-8')
    n += 1
print('pages du site reliées:', n)

# 3. Rebrancher : sans cette étape, les pages SA-* régénérées perdraient la base de données.
WIRE = ['wire_ramadan.py', 'wire_aid.py', 'wire_vendredi.py', 'wire_homepage.py', 'wire_events.py', 'wire_site.py', 'wire_pages.py', 'wire_horaires.py', 'wire_prieres.py', 'wire_apropos.py', 'wire_services.py', 'wire_service_pages.py', 'wire_dons.py', 'wire_evenements.py', 'wire_ressources.py', 'wire_inbox.py', 'wire_contact.py', 'wire_formulaires.py', 'wire_traductions.py', 'wire_pied.py', 'wire_nettoyage.py', 'wire_photos.py', 'wire_langues.py', 'wire_gratuit.py', 'fix_inputs.py']
HERE = pathlib.Path(__file__).resolve().parent
if '--sans-branchements' in sys.argv:
    print('ATTENTION : branchements non relancés. Lancez ensuite, dans l’ordre :', ', '.join(WIRE))
elif ROOT.resolve() != HERE.parent:
    print('ATTENTION : dossier cible différent du dépôt ; lancez vous-même, dans l’ordre :', ', '.join(WIRE))
else:
    for w in WIRE:
        subprocess.run([sys.executable, '-I', str(HERE / w)], check=True)
    print('Branchements relancés :', ', '.join(WIRE))
