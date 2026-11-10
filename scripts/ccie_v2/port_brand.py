"""En-tête CCIE v2 (pages publiques) : marque « CCIE » + nom en petites capitales, menu en pilule.

Usage: python3 -I port_brand.py <scratchpad> <page.html> [...]
Dans le lien .brand de l'en-tête seulement : le titre devient « CCIE » et le sous-titre devient
« Centre Islamique d'Edmundston » (clé de traduction existante). Le pied de page ne change pas.
Idempotent.
"""
import sys, re, pathlib
sys.path.insert(0, sys.argv[1])
from bundle import split, join

MARK = '<style id="ccie-v2-brand">'
CSS = r"""
.cc .brand .lg-t1{font-size:27px !important;font-weight:600 !important;line-height:1;letter-spacing:.02em}
.cc .brand .logo-sub{font-size:10px !important;font-weight:500 !important;letter-spacing:.16em;text-transform:uppercase;line-height:1.45;margin-top:3px;max-inline-size:200px;white-space:normal !important;color:#5B6272}
.cc .nav-desk{flex:0 1 auto;margin:0 auto;gap:2px !important;padding:5px;border-radius:999px;border:1px solid rgba(168,129,60,.18);background:rgba(20,26,43,.024)}
.cc .nav-desk .navlink{padding:9px 13px !important;border-radius:999px;font-size:14px !important;letter-spacing:.03em;white-space:nowrap;transition:color .25s ease,background .25s ease,box-shadow .25s ease}
.cc .nav-desk .navlink:hover{color:#141A2B;background:rgba(20,26,43,.04)}
.cc .nav-desk .navlink.on,.cc .nav-desk .navlink[aria-current="page"]{color:#8E6524;background:rgba(168,129,60,.13);box-shadow:inset 0 0 0 1px rgba(168,129,60,.38)}
.cc .nav-desk .navlink:focus-visible{outline:2px solid #8E6524;outline-offset:2px}
@media (max-width:1400px){.cc .nav-desk .navlink{padding:9px 10px !important;font-size:13.5px !important}.cc .brand .logo-sub{max-inline-size:170px}}
@media (max-width:1280px){.cc .nav-desk .navlink{padding:8px 8px !important;font-size:13px !important;letter-spacing:0}.cc .brand .logo-sub{display:none}}
@media (max-width:640px){.cc .brand .lg-t1{font-size:24px !important}.cc .brand .logo-sub{display:block;max-inline-size:150px;font-size:9px !important}}
@media (prefers-reduced-motion: reduce){.cc .nav-desk .navlink{transition:none}}
"""

for p in map(pathlib.Path, sys.argv[2:]):
    t = p.read_text(encoding='utf-8')
    i, j, tpl = split(t)
    if MARK in tpl or 'class="brand"' not in tpl:
        print('ignoré', p.name)
        continue
    s = tpl.index('class="brand"')
    e = tpl.index('</a>', s)
    a = tpl[s:e]
    a2, n1 = re.subn(r'(class="lg-t1"[^>]*>)[^<]+<', r'\1CCIE<', a, count=1)
    a2, n2 = re.subn(r'(class="logo-sub[^"]*"[^>]*>)[^<]+<', r"\1Centre Islamique d'Edmundston<", a2, count=1)
    if not (n1 and n2):
        raise SystemExit('marque introuvable : ' + p.name)
    tpl = tpl[:s] + a2 + tpl[e:]
    k = tpl.rindex('</head>')
    tpl = tpl[:k] + MARK + CSS + '</style>' + tpl[k:]
    p.write_text(join(t, i, j, tpl), encoding='utf-8')
    print('porté', p.name)
