"""Accueil CCIE : le gabarit de la planche main.html remplace le contenu de l'Accueil.

Usage: python3 -I port_accueil.py <scratchpad> <planche PC.tpl.html> <page Accueil> [...]
- <main> : sections de la planche, branchées sur les clés de la logique actuelle (inchangée)
  et portant les crochets attendus par les scripts de câblage (#ascil-home-sync, etc.).
- En-tête et pied de page : ceux du site (menu commun, langues, câblage), avec le nom CCIE,
  « Le centre » et « Soutenir le CCIE ».
- CSS de la planche limitée à main.ccb ; animations renommées (b-*) pour ne rien écraser.
Idempotent (marqueur ccie-accueil).
"""
import sys, re, pathlib
sys.path.insert(0, sys.argv[1])
from bundle import split, join, add_assets

MARK = '<style id="ccie-accueil">'
board = pathlib.Path(sys.argv[2]).read_text(encoding='utf-8')
# document de la planche (son manifest porte les fichiers des polices)
board_doc = pathlib.Path(sys.argv[2].replace('.tpl.html', '.html')).read_text(encoding='utf-8')
FAM = {'Cormorant Garamond': 'CCIE Cormorant', 'Jost': 'CCIE Jost', 'Amiri': 'CCIE Amiri'}
FONTS, FONT_IDS = '', []
for ff in re.findall(r"@font-face\s*\{[^}]*\}", board):
    fam = re.search(r"font-family:\s*'([^']+)'", ff).group(1)
    FONTS += ff.replace("'%s'" % fam, "'%s'" % FAM[fam])
    FONT_IDS += re.findall(r'url\("([0-9a-f-]{36})"\)', ff)


def once(s, a, b, cnt=1):
    n = s.count(a)
    if n != cnt:
        raise SystemExit('motif %r : %d au lieu de %d' % (a[:80], n, cnt))
    return s.replace(a, b)


# ---------- CSS de la planche, limitée à main.ccb ----------
css_all = board[board.index('<style>\nbody{margin:0;background:#FBF8F1}'):]
css_all = css_all[len('<style>'):css_all.index('</style>')]
css_all = re.sub(r'/\*.*?\*/', '', css_all, flags=re.S)
DROP = ('.hdr', '.tb', '.nv', '.nl', '.mb', '.mm', '.mk-', '.ldr', '.qv', '.lang', '.ftr', '.fg', '.hide-t')
KF = set(re.findall(r'@keyframes\s+([\w-]+)', css_all))


def blocks(s):
    out, i = [], 0
    while i < len(s):
        j = s.find('{', i)
        if j < 0:
            break
        head = s[i:j].strip()
        d, k = 1, j + 1
        while d:
            d += {'{': 1, '}': -1}.get(s[k], 0)
            k += 1
        out.append((head, s[j + 1:k - 1]))
        i = k
    return out


def scope_sel(sel):
    sel = sel.strip()
    if any(re.search(re.escape(t) + r'(?![\w-])', sel) or (t.endswith('-') and t in sel) for t in DROP):
        return None
    if sel in ('body',):
        return None
    if sel == '.cc':
        return 'main.ccb'
    if sel == '.cc::before':
        return 'main.ccb::before'
    if sel.startswith('.cc '):
        return 'main.ccb ' + sel[4:]
    return 'main.ccb ' + sel


def ren(body):
    return re.sub(r'(?<![\w-])(' + '|'.join(map(re.escape, sorted(KF, key=len, reverse=True))) + r')(?![\w-])',
                  lambda m: 'b-' + m.group(1), body) if 'animation' in body else body


def conv(s):
    res = []
    for head, body in blocks(s):
        if head.startswith('@keyframes'):
            res.append('@keyframes b-%s{%s}' % (head.split()[1], body))
        elif head.startswith('@'):
            inner = conv(body)
            if inner:
                res.append('%s{%s}' % (head, inner))
        else:
            sels = [x for x in (scope_sel(p) for p in head.split(',')) if x]
            if not sels:
                continue
            if head.strip() == '.cc':
                body = body.replace('container-type:inline-size;', '')
            # reprise de la page après l'écran de chargement : délais calés sur --pd du site
            if re.fullmatch(r'\.rise\{animation-delay:2\.45s\}\.d1', head + '{' + body + '}.d1'):
                pass
            res.append('%s{%s}' % (','.join(sels), ren(body)))
    return ''.join(res)


CSS = conv(css_all)
for a, b in FAM.items():
    CSS = CSS.replace("'%s'" % a, "'%s','%s'" % (b, a))
# les délais « après chargement » de la planche (2,45 s…) suivent le délai réel du site (--pd)
CSS = once(CSS, 'main.ccb .rise{animation-delay:2.45s}', 'main.ccb .rise{animation-delay:calc(var(--pd,0s) + .1s)}')
CSS = once(CSS, 'main.ccb .d1{animation-delay:2.65s}', 'main.ccb .d1{animation-delay:calc(var(--pd,0s) + .3s)}')
CSS = once(CSS, 'main.ccb .d2{animation-delay:2.85s}', 'main.ccb .d2{animation-delay:calc(var(--pd,0s) + .5s)}')
CSS = once(CSS, 'main.ccb .d3{animation-delay:3.05s}', 'main.ccb .d3{animation-delay:calc(var(--pd,0s) + .7s)}')
# barre de campagne : classe .cprog (la classe .prog sert de crochet à la barre de prière)
CSS = CSS.replace('main.ccb .prog', 'main.ccb .cprog')
CSS = FONTS + CSS + (
    'html:not([dir="rtl"]) main.ccb,html:not([dir="rtl"]) main.ccb *{font-size-adjust:none !important}'
    'main.ccb .hero{padding:0 !important;background:none !important}'
    'main.ccb .link{display:inline-flex !important;min-height:0 !important}'
    'main.ccb .h1,main.ccb .h2,main.ccb .h3{letter-spacing:normal}'
    'main.ccb .h1{letter-spacing:-.01em}'
)
CSS += (
    'main.ccb .cprog .bar{height:100%;margin:0;border-radius:999px;background:linear-gradient(90deg,#6B4C1A,#D4AE62);box-shadow:0 0 12px rgba(168,129,60,.7);transition:width .6s ease}'
    'main.ccb .cslot{display:grid}'
    'main.ccb .btn.link{font-size:16px;letter-spacing:.04em;text-transform:none;color:#FFFFFF;min-height:54px !important;padding:0 30px;display:inline-flex !important}'
    'main.ccb .ph{border:0 !important;background:none !important;padding:0 !important;font-size:15px !important;color:#5B6272 !important}'
    'main.ccb section[aria-labelledby="ann-t"] .pill{background:rgba(168,129,60,.12) !important;color:#8E6524 !important}'
    'main.ccb section[aria-labelledby="ann-t"] .card .h3{font-size:24px !important}'
    'main.ccb .amts{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin-top:26px}'
    'main.ccb .amts .pt{text-align:center;border-color:rgba(168,129,60,.22)}'
    'main.ccb .amts .pt b{font-size:24px}'
    'main.ccb .times{grid-template-columns:repeat(6,minmax(0,1fr)) !important}'
    '@container (max-width: 980px){main.ccb .times{grid-template-columns:repeat(3,minmax(0,1fr)) !important}}'
    '@container (max-width: 640px){main.ccb .amts{grid-template-columns:repeat(2,minmax(0,1fr))}main.ccb .times{grid-template-columns:repeat(2,minmax(0,1fr)) !important}main.ccb .btn{white-space:normal;text-align:center}}'
    'html[dir="rtl"] main.ccb .stamp{left:auto;right:0}'
)

# ---------- <main> de la planche, branché ----------
M = board[board.index('<main>'):board.index('</main>')]
ARROW = re.search(r'<span class="link">Horaires (<svg.*?</svg>)</span>', M, re.S).group(1)
R = [
    ('<main>', ''),
    # héros
    ('aria-labelledby="c-h"', 'aria-labelledby="hero-t"'),
    ('<h1 id="c-h"', '<h1 id="hero-t"'),
    ('<a class="btn b-nv bm" href="#horaires">', '<a class="btn b-nv bm btn-gold" href="Horaires.dc.html">'),
    ('Edmundston · adresse à confirmer', 'Edmundston (Nouveau-Brunswick)'),
    # prochaine prière
    ('aria-labelledby="c-p"', 'aria-labelledby="pp-title"'),
    ('<div class="wrap"><div class="pcard rv">', '<div class="wrap"><div class="pcard pad-m rv">'),
    ('<div><p style="margin:0;font-size:13px', '<div><p id="pp-title" style="margin:0;font-size:13px'),
    ('<p id="c-p" class="disp"', '<p class="disp"'),
    ('<div class="bar" role="progressbar"', '<div class="bar prog" role="progressbar"'),
    ('aria-valuenow="{{prog}}"><i style="width:{{prog}}%">', 'aria-valuenow="{{progPct}}"><i style="width:{{progPct}}%">'),
    ('<div class="times tnum">', '<div class="times g5 tnum">'),
    ('aria-pressed="{{r.p}}"', 'aria-pressed="{{r.pressed}}"'),
    ('<b>{{r.t}}</b>', '<b>{{r.time}}</b>'),
    ('<p style="margin:0;font-size:15px;color:#5B6272"><strong', '<p aria-live="polite" style="margin:0;font-size:15px;color:#5B6272"><strong'),
    # accès rapides : la grille garde le crochet .wrap.g3 > a.card (vendredi, trouver)
    ('<div class="wrap"><div class="g3">\n  <a class="card rv" href="#"><span class="ib">', '<div class="wrap g3">\n  <a class="card rv" href="Horaires.dc.html"><span class="ib">'),
    ('Khutba et Jumu’a : heure <span class="ex">à confirmer</span>. Arrivez un peu avant.', 'Khutba et Jumu’a à <span class="tnum">{{jumuaTime}}</span>. Arrivez un peu avant.'),
    ('<a class="card rv" href="#visite"><span class="ib">', '<a class="card rv" href="Contact.dc.html"><span class="ib">'),
    ('106, rue de l’Église, local 1, Edmundston <span class="ex">à confirmer</span>', '106, rue de l’Église, Edmundston'),
    ('  <a class="card rv" href="#"><span class="ib">', '  <div class="cslot"><a class="card rv" href="Contact.dc.html"><span class="ib">'),
    ('<span class="link">Nous écrire ', '<span class="link">Nous écrire '),
    # soutenir le centre (crochets de la campagne)
    ('aria-labelledby="c-s"', 'aria-labelledby="camp-t"'),
    ('<h2 id="c-s" class="h2" style="font-size:34px">Objectif de l’année <span class="ex">exemple</span></h2>',
     '<h2 id="camp-t" class="h2" style="font-size:34px">Objectif de l’année</h2>'),
    ('<a class="btn b-cu" href="#" style="margin-top:20px;width:100%">', '<a class="btn b-cu btn-green" href="Dons.dc.html" style="margin-top:20px;width:100%">'),
    ('Donner {{amtTxt}} par Interac', '<span>Donner {{amtText}} par Interac</span>'),
    ('<div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin-top:26px">', '<div class="amts">'),
    ('<sc-for list="{{amts}}" as="a" hint-placeholder-count="3"><button type="button" class="pt" aria-pressed="{{a.p}}" sc-camel-on-click="{{a.pick}}" style="background:{{a.bg}};color:{{a.fg}};border-color:rgba(168,129,60,.22);text-align:center"><b>{{a.n}}</b></button></sc-for>',
     '<sc-for list="{{amts}}" as="a" hint-placeholder-count="4"><button type="button" class="pt" aria-pressed="{{a.pressed}}" sc-camel-on-click="{{a.pick}}"><b>{{a.label}}</b></button></sc-for>'),
    ('<p class="muted" style="margin:12px 0 0;font-size:14px">Adresse Interac du CCIE : <span class="ex">à fournir</span></p>',
     '<p style="margin:16px 0 0"><a class="link" href="N3-Campagne.dc.html">Suivre la campagne en direct ' + ARROW + '</a></p>'),
    # annonces
    ('aria-labelledby="c-n"', 'aria-labelledby="ann-t"'),
    ('<h2 id="c-n"', '<h2 id="ann-t"'),
    ('<a class="link" href="#">Tous les événements', '<a class="link" href="Evenements.dc.html">Tous les événements'),
    # première visite (crochets « bienvenue »)
    ('aria-labelledby="c-v"', 'aria-labelledby="bv-t"'),
    ('<h2 id="c-v"', '<h2 id="bv-t"'),
    ('<a class="btn b-nv bm" href="#" style="margin-top:26px">', '<a class="btn b-nv bm link" href="Contact.dc.html" style="margin-top:26px">'),
    # invitation
    ('<a class="btn b-cu" href="#soutenir" style="position:relative;margin-top:26px">', '<a class="btn b-cu btn-green" href="#soutenir" style="position:relative;margin-top:26px">'),
]
for a, b in R:
    M = once(M, a, b)
M = once(M, '<p style="margin:0;font-size:14px;color:#A8813C"><span class="ex" style="background:rgba(20,26,43,0.096);color:#8E6524">Exemple</span> Horaires officiels du CCIE sur Mawaqit, branchés à l’étape suivante</p>',
         '<a class="link" href="Horaires.dc.html">Tous les horaires du mois ' + ARROW + '</a>')
M = once(M, 'aria-label="Accès rapides">\n <div class="wrap g3">', 'aria-label="Accès rapides">\n <div class="wrap g3">')
# fermeture de la carte « Étudiantes et étudiants » dans son emplacement
M = once(M, 'on vous aide à vous installer.</p><span class="link">Nous écrire ' + ARROW + '</span></a>',
         'on vous aide à vous installer.</p><span class="link">Nous écrire ' + ARROW + '</span></a></div>')
M = once(M, '<div class="wrap g3">', '<div class="wrap g3">')
M = M.replace('</div></div>\n</section><section id="soutenir"', '</div>\n</section><section id="soutenir"', 1)

# montant récolté / objectif : les éléments que le panneau met à jour
OBJ_OLD = ('<p class="tnum" style="margin:16px 0 0;display:flex;justify-content:space-between;align-items:baseline"><span class="disp" style="font-size:44px;color:#8E6524">[montant récolté]</span><span class="muted">sur [objectif]</span></p>\n'
           '   <div class="prog" style="margin-top:14px"><i style="--w:46%"></i></div>')
OBJ_NEW = ('<div style="margin:16px 0 0;display:flex;justify-content:space-between;align-items:baseline;gap:8px 16px;flex-wrap:wrap">'
           '<sc-if value="{{hasRaised}}" hint-placeholder-val="{{ false }}"><p class="tnum disp" style="margin:0;font-size:40px;line-height:1.1;color:#8E6524">{{raisedFmt}} récoltés · {{pct}} %</p></sc-if>'
           '<sc-if value="{{noRaised}}" hint-placeholder-val="{{ true }}"><p class="ph" style="margin:0;color:#5B6272">Montant récolté : mis à jour par l’association</p></sc-if>'
           '<div style="display:inline-flex;align-items:baseline;gap:8px"><span class="muted">Objectif</span><p class="serif tnum disp" style="margin:0;font-size:28px;color:#141A2B">0 $</p></div></div>\n'
           '   <sc-if value="{{hasRaised}}" hint-placeholder-val="{{ false }}"><div class="cprog" role="progressbar" aria-valuemin="0" aria-valuemax="0" aria-label="Montant récolté" style="margin-top:14px"><div class="bar" style="width:{{pct}}%"></div></div></sc-if>')
M = once(M, OBJ_OLD, OBJ_NEW)

# annonces : les cartes par défaut actuelles (le panneau les remplace par les siennes)
ANN = re.search(r'<div class="g3">\n   <a class="card rv" href="#"><span class="pill".*?</a>\n  </div>', M, re.S)
CARDS = [('Oct. 2026', 'Campagne nouveau lieu', 'Objectif à définir.'),
         ('27 mai 2026', 'Aïd al-Adha 1447', 'Prière célébrée à la salle louée du 106, rue de l’Église, Edmundston, NB E3V 1V5.'),
         ('25 avr. 2026', 'Journée de parrainage d’orphelins', 'Avec l’organisme Activités d’entraide, au 106, rue de l’Église.')]
M = M[:ANN.start()] + '<div class="g3">' + ''.join(
    '<a class="card rv" href="Evenements.dc.html"><span class="pill tnum">%s</span><p class="h3" style="margin-top:16px">%s</p><p class="muted" style="margin:8px 0 0">%s</p></a>' % c
    for c in CARDS) + '</div>' + M[ANN.end():]
assert '{{prog}}' not in M and '{{amtTxt}}' not in M and 'href="#"' not in M, 'liaison ou lien de planche restant'
import re as _r; print([M[x.start()-200:x.end()+50] for x in _r.finditer("Exemple|exemple|à confirmer|à fournir",M)])
assert "Exemple" not in M and 'exemple' not in M and 'à confirmer' not in M and 'à fournir' not in M, 'texte de maquette restant'
SECTIONS = M

# ---------- en-tête et pied de page : nom CCIE, « Le centre », « Soutenir le CCIE » ----------
HF = [  # (motif regex, remplacement, nombre attendu)
    (r"<title>Accueil — Centre Islamique d[’']Edmundston", '<title>Accueil — Centre communautaire islamique d’Edmundston', 1),
    (r'aria-label="[^"]*Edmundston Islamic Centre, accueil"', 'aria-label="CCIE, accueil"', 1),
    (r"(<span class=\"logo-sub lg-t2\"[^>]*>)Centre Islamique d'Edmundston</span>", r'\1Centre communautaire islamique d’Edmundston</span>', 1),
    (r'(<a class="navlink" href="(?:[MT]-)?APropos\.dc\.html" aria-haspopup="true"[^>]*>)À propos<', r'\1Le centre<', 1),
    (r'role="menu" aria-label="À propos"', 'role="menu" aria-label="Le centre"', 1),
    (r"Tableau officiel du Centre Islamique d[’']Edmundston", 'Tableau officiel du CCIE', 1),
    (r'<span>Faire un don</span></a>', '<span>Soutenir le CCIE</span></a>', 1),
    (r'(<a href="(?:[MT]-)?APropos\.dc\.html"[^>]*>)À propos(<svg|</a>)', r'\1Le centre\2', 2),
    (r'(<a href="(?:[MT]-)?Dons\.dc\.html"[^>]*>)Faire un don</a></li>', r'\1Soutenir le CCIE</a></li>', 1),
    (r"(<p [^>]*>)Centre Islamique d[’']Edmundston</p>", r'\1Centre communautaire islamique d’Edmundston</p>', 1),
    (r"Page Facebook du Centre Islamique d[’']Edmundston", 'Page Facebook du CCIE', 1),
    (r'© 2026 Edmundston Islamic Centre — Edmundston', '© 2026 Centre communautaire islamique d’Edmundston — Edmundston', 1),
]
MENU_DON = re.compile(r'(<a class="btn btn-gold" href="(?:[MT]-)?Dons\.dc\.html"[^>]*><svg(?:(?!</a>).)*?</svg>)Faire un don</a>', re.S)

for p in map(pathlib.Path, sys.argv[3:]):
    t = p.read_text(encoding='utf-8')
    i, j, tpl = split(t)
    if MARK in tpl:
        print('déjà', p.name)
        continue
    for a, b, c in HF:
        tpl, n = re.subn(a, b, tpl)
        assert n == c, (p.name, a, n)
    tpl, n = MENU_DON.subn(r'\1Soutenir le CCIE</a>', tpl)
    assert n == 1, 'bouton don du menu mobile'
    m = re.search(r'<main class="pagein"( style="[^"]*")>', tpl)
    e = tpl.index('</main>', m.end())
    old = tpl[m.end():e]
    tail = old[old.index('<div class="totop">'):]
    pre = 'M-' if 'href="M-Horaires.dc.html"' in tpl else 'T-' if 'href="T-Horaires.dc.html"' in tpl else ''
    sec = re.sub(r'href="((?:N\d-)?[A-Z][\w-]*\.dc\.html)"',
                 lambda x: 'href="%s"' % ((pre + x.group(1)) if pre and (p.parent / (pre + x.group(1))).exists() else x.group(1)), SECTIONS)
    tpl = tpl[:m.start()] + '<main class="pagein ccb"%s>\n' % m.group(1) + sec + tail + tpl[e:]
    k = tpl.rindex('</head>')
    tpl = tpl[:k] + MARK + CSS + '</style>' + tpl[k:]
    out, added = add_assets(join(t, i, j, tpl), board_doc, FONT_IDS)
    assert all(u in out for u in FONT_IDS), 'police absente du manifest'
    p.write_text(out, encoding='utf-8')
    print('accueil', p.name, 'polices ajoutées', len(added))
