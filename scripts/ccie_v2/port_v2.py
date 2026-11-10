"""Portage du design CCIE v2 sur les pages publiques câblées (pages intérieures).

Usage: python3 -I port_v2.py <scratchpad> <v2-frame-css-source> <page.html> [<page.html> ...] [--out DIR]
On garde le balisage, les textes, la logique et les scripts : on ajoute la feuille v2 (.cc),
on active la couche .cc sur la racine, et on restyle l'en-tête et le pied comme sur les planches.
Idempotent : une page déjà portée (marqueur ccie-v2) est ignorée.
"""
import sys, re, pathlib
sys.path.insert(0, sys.argv[1])
from bundle import split, join, add_assets

MARK = '<style id="ccie-v2">'
EXTRA = r"""
/* ---- en-tête et pied v2 sur le balisage du site ---- */
.root>.cc,.root .cc[style*="display:contents"]{container-type:normal !important}
.cc .hdr .tb strong{color:#141A2B}
.cc .hdr .tb a{color:#5B6272}
.cc .hdr .tb a:hover{color:#8E6524}
.cc .navlink{color:#3A4050;font-weight:400;font-size:15px;letter-spacing:.01em}
.cc .brand{min-width:0;flex:0 1 auto !important}
@media (min-width:1181px){.cc .brand{flex:none !important}.cc .brand .lg-t1{white-space:nowrap}}
.cc .nav-desk{gap:12px !important;min-width:0}
@media (max-width:1400px){.cc .navlink{font-size:14px}.cc .nav-desk{gap:2px !important}}
@media (max-width:1400px){.cc .brand .lg-t1{font-size:18px !important}.cc .brand .logo-sub{font-size:12px !important}}
@media (max-width:1260px){.cc .navlink{font-size:13px}.cc .brand .lg-t1{font-size:16px !important}.cc .brand .logo-sub{font-size:11px !important}}
@media (max-width:640px){.cc .brand .lg-t1{font-size:17px !important;line-height:1.1}.cc .brand .logo-sub{font-size:11px !important}.cc .don-btn{padding:0 !important;min-width:44px;justify-content:center}.cc .don-btn .don-ic{display:inline-flex !important}.cc .don-btn>span:last-child{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}}
.cc .navlink:hover,.cc .navlink.on{color:#8E6524}
.cc .brand .lg-t1{font-family:'Cormorant Garamond',Georgia,serif;font-weight:600;letter-spacing:0}
.cc .ftr{padding:0}
.cc .ftr .eyebrow{color:#8E6524}
.cc .ftr a:not(.btn){color:#3A4050}
.cc .ftr a.btn{color:#FFFFFF}
.cc .ftr a:not(.btn):hover{color:#8E6524}
"""


def region(tpl, tag):
    s = tpl.index('<' + tag)
    e = tpl.index('</' + tag + '>') + len(tag) + 3
    return s, e


def sub1(s, a, b, name):
    if a not in s:
        raise SystemExit('motif introuvable (%s): %s' % (name, a[:80]))
    return s.replace(a, b, 1)


def header(h):
    h = sub1(h, '<div style="background:#141A2B;color:#F3ECDD;font-size:14px">', '<div class="tb">', 'barre du haut')
    h = h.replace('<strong style="color:#fff">', '<strong>', 1)
    tb_s, tb_e = h.index('<div class="tb">'), h.index('<div style="position:relative;')
    h = h[:tb_s] + h[tb_s:tb_e].replace('color:#F3ECDD;', '') + h[tb_e:]
    h = sub1(h, '<div style="position:relative;background:rgba(251,248,241,.97);border-bottom:1px solid #E7DCC6;backdrop-filter:blur(6px)">',
             '<div class="nv" style="position:relative">', 'barre de navigation')
    h = sub1(h, 'class="btn btn-gold don-btn"', 'class="btn b-cu don-btn"', 'bouton don')
    return h


def footer(f):
    f = sub1(f, '<footer style="background:#141A2B;color:#F3ECDD">', '<footer class="ftr">', 'pied')
    f = f.replace('color:#F3ECDD', 'color:#5B6272').replace('color:#fff', 'color:#141A2B')
    f = f.replace('color:#A8813C', 'color:#8E6524')
    f = f.replace('rgba(243,236,221,', 'rgba(20,26,43,')
    f = f.replace('fill="#FFFFFF"', 'fill="#141A2B"')  # logo blanc sur fond sombre -> lisible sur fond clair
    return f


def port(tpl, css):
    if MARK in tpl:
        return None
    k = tpl.rindex('</head>')
    tpl = tpl[:k] + MARK + css + EXTRA + '</style>' + tpl[k:]
    # comme sur les planches, seuls l'en-tête et le pied sont dans la couche .cc ;
    # display:contents garde la mise en page (et l'en-tête collant) intacte
    W = '<div class="cc" style="display:contents">'
    s, e = region(tpl, 'header')
    tpl = tpl[:s] + W + header(tpl[s:e]) + '</div>' + tpl[e:]
    s, e = region(tpl, 'footer')
    tpl = tpl[:s] + W + footer(tpl[s:e]) + '</div>' + tpl[e:]
    return tpl


args = sys.argv[2:]
out = None
if '--out' in args:
    out = pathlib.Path(args[args.index('--out') + 1])
    args = args[:args.index('--out')]
src, pages = pathlib.Path(args[0]), [pathlib.Path(p) for p in args[1:]]
vtext = src.read_text(encoding='utf-8')
vt = split(vtext)[2]
css = [s for s in re.findall(r'<style[^>]*>(.*?)</style>', vt, re.S) if '@font-face' not in s[:300]][0]
ASSETS = sorted(set(re.findall(r'url\("?([0-9a-f]{8}-[0-9a-f-]{27})', css)))
for p in pages:
    t = p.read_text(encoding='utf-8')
    i, j, tpl = split(t)
    new = port(tpl, css)
    text = t if new is None else join(t, i, j, new)
    text, added = add_assets(text, vtext, ASSETS)
    if text == t:
        print('déjà porté', p.name)
        continue
    dst = (out / p.name) if out else p
    dst.write_text(text, encoding='utf-8')
    print('porté' if new is not None else 'assets', p.name, '+%d assets' % len(added))
