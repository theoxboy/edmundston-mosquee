"""Portage CCIE v2 du superadmin SA-* (planche 3.html) : ajoute les règles de style propres à la v2.

Usage: python3 -I port_sa.py <dossier-bundle> <planche v2> <page.html> [...]
Règles reprises : celles de la planche absentes de la page (typographie .sa, boutons or en dégradé,
bordures et survol des cartes, ornements des sur-titres). Exclues : l'animation du logo (cc-mk,
livrable à part) et la règle racine .sa. Les ornements SVG référencés sont copiés dans le manifest.
Balisage, textes, données et scripts inchangés. Idempotent.
"""
import sys, re, pathlib
sys.path.insert(0, sys.argv[1])
from bundle import split, join, add_assets

MARK = '<style id="ccie-v2-thx">'
norm = lambda r: re.sub(r'\s+', '', r)
BLOCK = re.compile(r'(?:@media[^{]+\{(?:[^{}]+\{[^{}]*\})+\s*\}|@keyframes[^{]+\{(?:[^{}]+\{[^{}]*\})+\s*\}|[^{}@]+\{[^{}]*\})')


def css_of(tpl):
    css = ''.join(s for s in re.findall(r'<style[^>]*>(.*?)</style>', tpl, re.S) if '@font-face' not in s[:300])
    return re.sub(r'/\*.*?\*/', '', css, flags=re.S)


frame = pathlib.Path(sys.argv[2])
vtext = frame.read_text(encoding='utf-8')
vcss = css_of(split(vtext)[2])
for p in map(pathlib.Path, sys.argv[3:]):
    t = p.read_text(encoding='utf-8')
    i, j, tpl = split(t)
    if MARK in tpl:
        print('déjà porté', p.name)
        continue
    have = set(norm(m) for m in re.findall(r'[^{}]+\{[^{}]*\}', css_of(tpl)))
    new = []
    for r in BLOCK.findall(vcss):
        if norm(r) in have or all(norm(x) in have for x in re.findall(r'[^{}]+\{[^{}]*\}', r)):
            continue
        if 'cc-mk' in r or 'ccmk' in r or re.match(r'\s*\.(?:sa|th)\{container-type', r):
            continue
        new.append(r.strip())
    k = tpl.rindex('</head>')
    tpl = tpl[:k] + MARK + '\n' + '\n'.join(new) + '\n</style>' + tpl[k:]
    text = join(t, i, j, tpl)
    uu = sorted(set(re.findall(r'url\("?([0-9a-f]{8}-[0-9a-f-]{27})', '\n'.join(new))))
    text, added = add_assets(text, vtext, uu)
    p.write_text(text, encoding='utf-8')
    print('porté', p.name, len(new), 'règles', '+%d assets' % len(added))
