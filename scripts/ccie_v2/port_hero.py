"""Bandeau d'ouverture de l'Accueil, style de la planche main.html.

Usage: python3 -I port_hero.py <scratchpad> <page Accueil> [...]
Classes seulement (sur-titre en « kick », boutons or et filet, section .hero) et cadre doré
autour de la photo, qui reste gérée depuis le superadmin (data-ascil-photo). Textes inchangés.
Idempotent.
"""
import sys, re, pathlib
sys.path.insert(0, sys.argv[1])
from bundle import split, join

MARK = '<style id="ccie-v2-hero">'
CSS = r"""
.root .hero{position:relative;overflow:hidden;padding:72px 0 40px !important;background:radial-gradient(900px 520px at 78% 30%,rgba(212,174,98,.16),transparent 62%)}
.root .hero .kick{margin:0;font-size:12px;font-weight:500;letter-spacing:.32em;text-transform:uppercase;color:#8E6524;display:flex;align-items:center;gap:14px}
.root .hero .kick::before{content:"";width:46px;height:1px;background:linear-gradient(90deg,transparent,#A8813C)}
.root .hero .h1{margin-top:24px !important}
.root .b-nv{background:linear-gradient(135deg,#C49A4A,#8E6524);color:#FFFFFF}
.root .b-nv:hover{color:#FFFFFF;box-shadow:0 14px 34px -12px rgba(168,129,60,.8)}
.root .b-ln{background:transparent;color:#141A2B;box-shadow:inset 0 0 0 1px rgba(168,129,60,.55)}
.root .b-ln:hover{background:rgba(168,129,60,.1);color:#5E4316;box-shadow:inset 0 0 0 1px #A8813C}
.root .b-nv:focus-visible,.root .b-ln:focus-visible{outline:2px solid #8E6524;outline-offset:3px}
.root .hero .heroimg{border:1px solid rgba(168,129,60,.45) !important;border-radius:28px !important;box-shadow:0 0 0 8px rgba(251,248,241,.9),0 0 0 9px rgba(168,129,60,.28),0 40px 80px -40px rgba(20,26,43,.45)}
@media (max-width:640px){.root .hero{padding:40px 0 16px !important}.root .hero .kick{letter-spacing:.22em}}
"""

for p in map(pathlib.Path, sys.argv[2:]):
    t = p.read_text(encoding='utf-8')
    i, j, tpl = split(t)
    if MARK in tpl:
        print('déjà porté', p.name); continue
    s = tpl.index('<section aria-labelledby="hero-t"')
    e = tpl.index('</section>', s)
    sec = tpl[s:e]
    sec = re.sub(r'^<section aria-labelledby="hero-t" style="[^"]*"', '<section class="hero" aria-labelledby="hero-t"', sec)
    sec = sec.replace('class="eyebrow"', 'class="kick"', 1)
    sec = sec.replace('class="btn btn-gold"', 'class="btn b-nv"', 1).replace('class="btn btn-ghost"', 'class="btn b-ln"', 1)
    if 'class="hero"' not in sec or 'class="kick"' not in sec:
        raise SystemExit('bandeau inattendu : ' + p.name)
    tpl = tpl[:s] + sec + tpl[e:]
    k = tpl.rindex('</head>')
    tpl = tpl[:k] + MARK + CSS + '</style>' + tpl[k:]
    p.write_text(join(t, i, j, tpl), encoding='utf-8')
    print('porté', p.name)
