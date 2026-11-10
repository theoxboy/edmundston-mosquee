"""Accueil CCIE v2 : bloc « Prochaine prière » en carte claire, comme la planche main.html.

Usage: python3 -I port_home.py <dossier-bundle> <page Accueil déjà passée par port_v2.py> [...]
Seules des valeurs de couleur changent (balisage du bloc, et couleurs des pastilles dans la
logique) ; textes, données, liaisons et scripts inchangés. Idempotent.
"""
import sys, re, pathlib
sys.path.insert(0, sys.argv[1])
from bundle import split, join

MARK = '<style id="ccie-v2-home">'
CSS = r"""
.cc .m-first .big-m{font-family:'Cormorant Garamond',Georgia,serif;font-weight:500 !important;color:#141A2B !important;letter-spacing:.02em}
.cc .m-first .serif{font-weight:600 !important}
.cc .m-first .prog{background:rgba(20,26,43,.08)}
.cc .m-first .chip:hover{border-color:rgba(168,129,60,.8)}
"""
XDC = [  # pastilles des prières : fond sombre -> carte claire, prière choisie en or
    ("chipBg: selected ? '#A8813C' : 'rgba(255,255,255,.08)'", "chipBg: selected ? 'linear-gradient(135deg,#C49A4A,#8E6524)' : '#FBF8F1'"),
    ("chipFg: selected ? '#141A2B' : '#fff'", "chipFg: selected ? '#FFFFFF' : '#141A2B'"),
    ("chipSub: selected ? '#141A2B' : '#F3ECDD'", "chipSub: selected ? '#FFFFFF' : '#5B6272'"),
    ("chipBorder: (isNext && !selected) ? 'rgba(168,129,60,.9)' : 'transparent'", "chipBorder: (isNext && !selected) ? 'rgba(168,129,60,.9)' : 'rgba(168,129,60,.22)'"),
]


def band(b):
    a = '<div class="pad-m" style="background:#141A2B;color:#fff;'
    if a not in b:
        raise SystemExit('bloc des prières introuvable')
    b = b.replace(a, '<div class="pad-m" style="background:#FFFFFF;color:#141A2B;border:1px solid rgba(168,129,60,.22);box-shadow:0 30px 60px -40px rgba(20,26,43,.35);', 1)
    b = b.replace('class="eyebrow" style="color:#A8813C"', 'class="eyebrow" style="color:#8E6524"')
    b = b.replace('color:#F3ECDD', 'color:#5B6272').replace('color:#fff', 'color:#141A2B')
    b = b.replace('background:rgba(255,255,255,.1)', 'background:rgba(20,26,43,.06)')
    return b


for p in map(pathlib.Path, sys.argv[2:]):
    t = p.read_text(encoding='utf-8')
    i, j, tpl = split(t)
    if MARK in tpl:
        print('déjà porté', p.name)
        continue
    if 'id="ccie-v2"' not in tpl:
        raise SystemExit('passer port_v2.py avant : ' + p.name)
    k = tpl.rindex('</head>')
    tpl = tpl[:k] + MARK + CSS + '</style>' + tpl[k:]
    s = tpl.index('<section class="m-first"')
    e = tpl.index('</section>', s)
    tpl = tpl[:s] + band(tpl[s:e]) + tpl[e:]
    for a, b in XDC:
        if a not in tpl:
            raise SystemExit('logique des pastilles introuvable (%s) : %s' % (p.name, a[:40]))
        tpl = tpl.replace(a, b, 1)
    p.write_text(join(t, i, j, tpl), encoding='utf-8')
    print('porté', p.name)
