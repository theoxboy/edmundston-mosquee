"""Menu mobile CCIE v2 : le menu du site prend l'allure des tuiles de la planche (mm2).

Usage: python3 -I port_mm.py <scratchpad> <page.html> [...]
Style seulement : le menu garde ses liens, son ordre et le crochet nav[aria-label="Menu mobile"]
utilisé par les scripts (traduction, pages ajoutées). Idempotent.
"""
import sys, pathlib
sys.path.insert(0, sys.argv[1])
from bundle import split, join

MARK = '<style id="ccie-v2-mm">'
N = 'nav[aria-label="Menu mobile"]'
CSS = """
:is(.root,.th) {n}{{display:grid !important;grid-template-columns:minmax(0,1fr);gap:8px;margin-top:12px !important}}
:is(.root,.th) {n}>a{{flex-direction:row !important;align-items:center !important;justify-content:space-between !important;gap:12px;min-height:60px !important;padding:0 16px 0 18px !important;border:1px solid rgba(168,129,60,.2) !important;border-radius:18px;font-size:16px !important;font-weight:500 !important;line-height:1.25;overflow-wrap:anywhere;transition:border-color .2s ease,transform .2s ease}}
.root {n}>a{{background:rgba(20,26,43,.024)}}
.th {n}>a{{background:rgba(255,255,255,.04)}}
:is(.root,.th) {n}>a svg{{flex:none;color:#A8813C}}
:is(.root,.th) {n}>a:hover{{border-color:rgba(168,129,60,.5) !important}}
:is(.root,.th) {n}>a:active{{transform:scale(.97)}}
:is(.root,.th) {n}>a:focus-visible{{outline:2px solid #A8813C;outline-offset:2px}}
.root {n}>a:is([aria-current="page"],.on){{background:linear-gradient(160deg,rgba(168,129,60,.24),rgba(168,129,60,.05)) !important;border-color:rgba(168,129,60,.55) !important;color:#8E6524 !important}}
.th {n}>a:is([aria-current="page"],.on){{background:linear-gradient(160deg,rgba(226,184,101,.22),rgba(226,184,101,.04)) !important;border-color:rgba(226,184,101,.6) !important}}
:is(.root,.th) {n}>div{{grid-column:1/-1;flex-direction:row !important;flex-wrap:wrap;gap:6px 8px;padding:0 !important;margin:0 0 6px !important;padding-inline-start:6px !important;border:0 !important}}
:is(.root,.th) {n}>div>a{{min-height:36px !important;padding:0 12px;border-radius:999px;border:1px solid rgba(168,129,60,.25);font-size:14px !important;font-weight:500 !important}}
@media (prefers-reduced-motion: reduce){{:is(.root,.th) {n}>a{{transition:none}}}}
""".format(n=N)

for p in map(pathlib.Path, sys.argv[2:]):
    t = p.read_text(encoding='utf-8')
    i, j, tpl = split(t)
    if MARK in tpl or N not in tpl:
        print('ignoré', p.name)
        continue
    k = tpl.rindex('</head>')
    tpl = tpl[:k] + MARK + CSS + '</style>' + tpl[k:]
    p.write_text(join(t, i, j, tpl), encoding='utf-8')
    print('porté', p.name)
