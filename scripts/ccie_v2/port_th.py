"""Portage CCIE v2 des thèmes saisonniers TH-* (planche 4.html).

Usage: python3 -I port_th.py <dossier-bundle> <page TH-*.dc.html> <planche v2 correspondante> [--out DIR]
Ajoute la typographie .th et l'étoile tournante du bandeau d'ouverture. Balisage, textes,
données et scripts inchangés. Le logo et le menu mobile restent ceux du site. Idempotent.
"""
import sys, re, pathlib
sys.path.insert(0, sys.argv[1])
from bundle import split, join

MARK = '<style id="ccie-v2-th">'
CSS = r"""
.th [style*="Cormorant"],.th .h1,.th .h2,.th .h3,.th .serif{font-family:'Cormorant Garamond',Georgia,serif;font-weight:600 !important;font-size-adjust:.47}
.th .btn{font-weight:500;letter-spacing:.03em}
.cc-star-host{position:relative;overflow:hidden}
.cc-star{position:absolute;right:-140px;top:-120px;width:560px;height:560px;pointer-events:none;opacity:.32;z-index:0;animation:ccstar 140s linear infinite}
.cc-star svg{width:100%;height:100%;display:block}
@keyframes ccstar{to{transform:rotate(360deg)}}
@media (max-width:640px){.cc-star{width:320px;height:320px;right:-110px;top:-90px;opacity:.25}}
@media (prefers-reduced-motion: reduce){.cc-star{animation:none}}
"""

args = sys.argv[2:]
out = None
if '--out' in args:
    out = pathlib.Path(args[args.index('--out') + 1])
    args = args[:args.index('--out')]
page, frame = pathlib.Path(args[0]), pathlib.Path(args[1])
vt = split(frame.read_text(encoding='utf-8'))[2]
star = re.search(r'<div class="cc-star" aria-hidden="true">.*?</svg></div>', vt, re.S).group(0)

t = page.read_text(encoding='utf-8')
i, j, tpl = split(t)
if MARK in tpl:
    print('déjà porté', page.name)
    sys.exit(0)
k = tpl.rindex('</head>')
tpl = tpl[:k] + MARK + CSS + '</style>' + tpl[k:]
h = tpl.index('</header>')
m = re.compile(r'<section class="([a-z]+)"').search(tpl, h)
if not m:
    raise SystemExit('bandeau introuvable: ' + page.name)
end = tpl.index('>', m.start()) + 1
open_tag = tpl[m.start():end].replace('class="%s"' % m.group(1), 'class="%s cc-star-host"' % m.group(1), 1)
tpl = tpl[:m.start()] + open_tag + star + tpl[end:]
dst = (out / page.name) if out else page
dst.write_text(join(t, i, j, tpl), encoding='utf-8')
print('porté', page.name)
