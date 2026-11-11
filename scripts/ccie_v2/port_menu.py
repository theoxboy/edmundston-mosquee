"""Un seul menu principal partout.

Usage: python3 -I port_menu.py <scratchpad> <page.html> [...]

- Pages de thème (TH-*) : le menu réduit (sans Ressources, sans sous-menus) devient le menu du
  site (Accueil, Horaires, À propos, Services, Événements, Ressources, Contact, avec leurs
  sous-menus), l'entrée de saison restant juste après Horaires, comme sur les autres pages.
  Les couleurs du thème sont gardées ; seuls les sous-menus ajoutent une carte claire.
- SA-Panneau : menu latéral dans le même ordre que les autres pages du panneau
  (Site entier, Créer une page, Accueil + ses widgets, Horaires...).
- SA-Comptes.html : même ordre, mêmes entrées dans « Page à gérer », marque « CCIE ».
Idempotent (marqueur ccie-menu).
"""
import sys, re, pathlib
sys.path.insert(0, sys.argv[1])
from bundle import split, join

MARK = 'ccie-menu'
STD = ['Accueil', 'Horaires', 'À propos', 'Services', 'Événements', 'Ressources', 'Contact']
CHEV = ('<span class="ddc" aria-hidden="true"><svg class="icon" aria-hidden="true" width="14" height="14" '
        'sc-camel-view-box="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" '
        'stroke-linejoin="round" style="width:14px;height:14px"><path d="M7 10l5 5 5-5"></path></svg></span>')
# (libellé, lien, [(titre, sous-titre, lien), ...]) ; le premier sous-lien = la page du menu
SUB = {
    'Horaires': [('Horaires du mois', "Tableau officiel du Centre Islamique d'Edmundston", None),
                 ('Rappel de prière', 'Une alerte avant chaque prière', '/N3-Rappel.dc.html'),
                 ('Langue de la khutba', 'La langue de ce vendredi', '/N2-Khutba.dc.html')],
    'À propos': [('L’association', 'Mission, histoire, équipe', None),
                 ('Campagne en direct', 'Le nouveau lieu, pas à pas', '/N3-Campagne.dc.html')],
    'Services': [('Tous les services', 'Prières, Jumu’a, Aïd, solidarité', None),
                 ('Cours de Coran et d’arabe', 'Trouver le bon cours', '/N2-Cours.dc.html'),
                 ('Mariages', 'Le parcours étape par étape', '/N2-Mariages.dc.html'),
                 ('Funérailles et janaza', 'Qui appeler, quoi faire', '/N2-Funerailles.dc.html'),
                 ('Aide alimentaire', 'Demander ou donner', '/N2-AideAlimentaire.dc.html'),
                 ('Espace femmes', 'Horaires et accès', '/N2-EspaceFemmes.dc.html')],
    'Événements': [('Toutes les annonces', 'Ce qui s’en vient', None),
                   ('Calendrier du mois', 'Cours, prières, communauté', '/N3-Calendrier.dc.html'),
                   ('S’inscrire', 'Iftar, Aïd, activités', '/N3-Inscription.dc.html')],
    'Ressources': [('Nouveaux arrivants', 'Halal, mosquées voisines, démarches', None),
                   ('Dua et annonces', 'Le mur de la communauté', '/N3-Dua.dc.html')],
}
DEFAULT = {'Accueil': '/', 'Horaires': '/Horaires.dc.html', 'À propos': '/APropos.dc.html',
           'Services': '/Services.dc.html', 'Événements': '/Evenements.dc.html',
           'Ressources': '/Ressources.dc.html', 'Contact': '/Contact.dc.html'}

VP = '<meta name="viewport" content="width=device-width, initial-scale=1">'
TH_CSS = '''<style id="ccie-menu">
.th .navl{gap:14px}
.th .navl .dd{position:relative;display:flex;align-items:center}
.th .navl .dd>a{display:inline-flex;align-items:center;gap:2px}
.th .navl .ddc{display:inline-flex;margin-inline-start:2px;transition:transform .2s ease}
.th .navl .dd:hover .ddc,.th .navl .dd:focus-within .ddc{transform:rotate(180deg)}
.th .navl .ddp{position:absolute;top:100%;left:50%;translate:-50% 0;margin-top:8px;min-width:280px;background:#fff;border:1px solid #E7DCC6;border-radius:16px;box-shadow:0 18px 40px -20px rgba(20,26,43,.4);padding:8px;display:none;z-index:50}
.th .navl .ddp::before{content:"";position:absolute;left:0;right:0;top:-12px;height:12px}
.th .navl .dd:hover .ddp,.th .navl .dd:focus-within .ddp{display:block;animation:ccmdd .2s ease both}
@keyframes ccmdd{from{opacity:0;transform:translateY(-4px)}to{opacity:1;transform:none}}
@media (prefers-reduced-motion: reduce){.th .navl .ddp{animation:none !important}.th .navl .ddc{transition:none}}
.th .navl .ddp{text-align:start}
.th .navl .ddp a.ddi{display:flex;flex-direction:column;gap:2px;padding:10px 14px;border-radius:10px;background:none;color:#141A2B;font-size:15px;font-weight:400;min-height:44px;justify-content:center}
.th .navl .ddp a.ddi:hover,.th .navl .ddp a.ddi:focus-visible{background:#F7F1E4}
@container (max-width: 1320px){.th .navl{gap:10px}.th .navl a{font-size:14px}}
.th .navl a{white-space:nowrap}
.th .mmenu>div{display:flex;flex-wrap:wrap;gap:6px 8px;padding:6px 0 12px;padding-inline-start:12px;border-bottom:1px solid color-mix(in srgb,currentColor 22%,transparent)}
.th .mmenu>div>a{min-height:36px;padding:0 12px;border:1px solid color-mix(in srgb,currentColor 30%,transparent);border-radius:999px;font-size:14px;font-weight:500}
@container (max-width: 1180px){.th .navl{display:none !important}.th .mbtn{display:inline-flex}.th .nav .wrap>span.only-m{display:block !important}}
</style>'''


def anchors(nav):
    out = []
    for m in re.finditer(r'<a([^>]*)>(.*?)</a>', nav, re.S):
        attrs, label = m.group(1), re.sub(r'<[^>]+>', '', m.group(2)).strip()
        href = re.search(r'href="([^"]*)"', attrs).group(1)
        out.append((label, href, ' class="on"' in attrs or 'class="on"' in attrs, attrs))
    return out


def th_menu(tpl):
    m = re.search(r'<nav class="navl"[^>]*>(.*?)</nav>', tpl, re.S)
    mm = re.search(r'<nav class="mmenu"[^>]*>(.*?)</nav>', tpl, re.S)
    if not m or not mm:
        raise SystemExit('menu de thème introuvable')
    cur = anchors(m.group(1))
    href = {l: h for l, h, _, _ in cur}
    on = {l for l, _, o, _ in cur if o}
    theme = [(l, h) for l, h, _, _ in cur if l not in STD]
    H = lambda l: href.get(l, DEFAULT[l])
    oncls = lambda l: ' class="on"' if l in on else ''
    desk, mob = [], []
    for l in STD:
        if l in SUB:
            items = ''.join('<a class="ddi" href="%s"><span style="font-weight:700;color:#141A2B">%s</span>'
                            '<span style="font-size:13px;color:#5B6272">%s</span></a>' % (u or H(l), t, s)
                            for t, s, u in SUB[l])
            desk.append('<div class="dd"><a href="%s"%s aria-haspopup="true">%s%s</a>'
                        '<div class="ddp" role="menu" aria-label="%s">%s</div></div>' % (H(l), oncls(l), l, CHEV, l, items))
            mob.append('<a href="%s"%s>%s</a>' % (H(l), oncls(l), l))
            mob.append('<div>%s</div>' % ''.join('<a href="%s">%s</a>' % (u, t) for t, s, u in SUB[l] if u))
        else:
            desk.append('<a href="%s"%s>%s</a>' % (H(l), oncls(l), l))
            mob.append('<a href="%s"%s>%s</a>' % (H(l), oncls(l), l))
        if l == 'Horaires':
            for tl, th in theme:
                desk.append('<a href="%s"%s>%s</a>' % (th, oncls(tl), tl))
                mob.append('<a href="%s"%s>%s</a>' % (th, oncls(tl), tl))
    # le lien de don du menu mobile (dernier, stylé par le thème) est gardé tel quel
    don = [a for a in re.findall(r'<a [^>]*>.*?</a>', mm.group(1), re.S) if 'Dons.dc.html' in a]
    navl = m.group(0)[:m.group(0).index('>') + 1] + ''.join(desk) + '</nav>'
    mmenu = mm.group(0)[:mm.group(0).index('>') + 1] + ''.join(mob) + ''.join(don[-1:]) + '</nav>'
    tpl = tpl.replace(m.group(0), navl, 1).replace(mm.group(0), mmenu, 1)
    k = tpl.rindex('</head>')
    vp = '' if 'name="viewport"' in tpl else VP
    return tpl[:k] + vp + TH_CSS + tpl[k:]


def panneau(tpl):
    m = re.search(r'<nav class="side nav" aria-label="Widgets de l’accueil"([^>]*)>(.*?)</nav>', tpl, re.S)
    if not m:
        raise SystemExit('menu latéral du panneau introuvable')
    body = m.group(2)
    loop = re.search(r'<sc-for list="\{\{navItems\}\}".*?</sc-for>', body, re.S).group(0)
    rest = body[body.index('<a href="SA-Site.dc.html">'):]
    hor = rest.index('<a href="SA-Horaires.dc.html">')
    new = ('<nav class="side nav" aria-label="Pages du site"%s><!-- %s --><p class="side-t">Pages du site</p>' % (m.group(1), MARK)
           + rest[:hor] + '<a href="SA-Panneau.dc.html" aria-current="page" class="on">Accueil</a>'
           + '<div class="side-sub">' + loop + '</div>' + rest[hor:] + '</nav>')
    tpl = tpl.replace(m.group(0), new, 1)
    tpl = tpl.replace('<sc-raw-select class="in" id="jump-page"><option>Accueil</option><option>Site entier</option><option>Créer une page</option>',
                      '<sc-raw-select class="in" id="jump-page"><option>Site entier</option><option>Créer une page</option><option selected="">Accueil</option>', 1)
    return tpl


def comptes(t):
    if MARK in t:
        return None
    acc = '   <a href="SA-Panneau.dc.html">Accueil</a>\n'
    if acc not in t:
        raise SystemExit('Comptes : lien Accueil introuvable')
    t = t.replace(acc, '', 1)
    t = t.replace('   <a href="SA-Pages.dc.html">Créer une page</a>\n',
                  '   <a href="SA-Pages.dc.html">Créer une page</a>\n' + acc, 1)
    t = t.replace('<nav class="side nav" aria-label="Pages du site">', '<nav class="side nav" aria-label="Pages du site"><!-- %s -->' % MARK, 1)
    t = t.replace('     <option>Accueil</option>\n     <option>Site entier</option>\n     <option>Créer une page</option>\n',
                  '     <option>Site entier</option>\n     <option>Créer une page</option>\n     <option>Accueil</option>\n', 1)
    t = t.replace('     <option>Contact</option>\n     <option selected>Comptes</option>',
                  '     <option>Contact</option>\n     <option>Formulaires</option>\n     <option>Traductions</option>\n     <option selected>Comptes</option>', 1)
    t = t.replace("'Contact': 'SA-Contact.dc.html', 'Comptes': 'SA-Comptes.html'",
                  "'Contact': 'SA-Contact.dc.html', 'Formulaires': 'SA-Formulaires.dc.html', 'Traductions': 'SA-Traductions.dc.html', 'Comptes': 'SA-Comptes.html'", 1)
    t = t.replace("'Ressources': 'SA-Ressources', 'Contact': 'SA-Contact', 'Comptes': 'SA-Comptes' };",
                  "'Ressources': 'SA-Ressources', 'Contact': 'SA-Contact', 'Formulaires': 'SA-Formulaires', 'Traductions': 'SA-Traductions', 'Comptes': 'SA-Comptes' };", 1)
    t = t.replace('<span style="font-size:20px;font-weight:800">Centre Islamique d\'Edmundston</span>',
                  '<span class="lg-t1" style="font-size:20px;font-weight:800">CCIE</span>', 1)
    return t


for p in map(pathlib.Path, sys.argv[2:]):
    t = p.read_text(encoding='utf-8')
    if p.name == 'SA-Comptes.html':
        new = comptes(t)
        if new is None:
            print('déjà fait', p.name); continue
        p.write_text(new, encoding='utf-8'); print('menu', p.name); continue
    i, j, tpl = split(t)
    if MARK in tpl:
        print('déjà fait', p.name); continue
    if p.name.startswith('TH-'):
        tpl = th_menu(tpl)
    elif p.name == 'SA-Panneau.dc.html':
        tpl = panneau(tpl)
    else:
        print('ignoré', p.name); continue
    out = join(t, i, j, tpl)
    if p.name.startswith('TH-') and 'name="viewport"' not in out[:out.index('__bundler/template')]:
        k = out.index('<head>') + 6 if '<head>' in out else out.index('<head') 
        out = out[:k] + VP + out[k:]
    p.write_text(out, encoding='utf-8')
    print('menu', p.name)
