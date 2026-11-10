"""SA-Comptes.html (page HTML simple, sans bundle) : polices et règles v2 du superadmin.

Usage: python3 -I port_comptes.py <scratchpad> <planche 3__Panneau_PC.html> <SA-Comptes.html>
Polices Jost + Cormorant Garamond (comme la planche), règles v2 absentes de la page, sauf
l'animation du logo, la racine .sa et celles qui pointent vers des images du bundle. Idempotent.
"""
import sys, re, pathlib
sys.path.insert(0, sys.argv[1])
from bundle import split

MARK = '<style id="ccie-v2-sa">'
norm = lambda r: re.sub(r'\s+', '', r)
BLOCK = re.compile(r'(?:@media[^{]+\{(?:[^{}]+\{[^{}]*\})+\s*\}|@keyframes[^{]+\{(?:[^{}]+\{[^{}]*\})+\s*\}|[^{}@]+\{[^{}]*\})')
css_of = lambda t: re.sub(r'/\*.*?\*/', '', ''.join(s for s in re.findall(r'<style[^>]*>(.*?)</style>', t, re.S) if '@font-face' not in s[:300]), flags=re.S)

vcss = css_of(split(pathlib.Path(sys.argv[2]).read_text(encoding='utf-8'))[2])
p = pathlib.Path(sys.argv[3])
t = p.read_text(encoding='utf-8')
if MARK in t:
    sys.exit(print('déjà porté', p.name))
OLD = 'family=Noto+Sans:wght@400;500;600;700;800&family=Noto+Serif:wght@700'
assert OLD in t
t = t.replace(OLD, 'family=Jost:wght@400;500;600;700;800&family=Cormorant+Garamond:wght@500;600;700')
t = t.replace("'Noto Sans',system-ui", "'Jost',system-ui").replace("'Noto Serif',Georgia", "'Cormorant Garamond',Georgia")
have = set(norm(m) for m in re.findall(r'[^{}]+\{[^{}]*\}', css_of(t)))
new = [r.strip() for r in BLOCK.findall(vcss)
       if norm(r) not in have and not all(norm(x) in have for x in re.findall(r'[^{}]+\{[^{}]*\}', r))
       and 'cc-mk' not in r and 'ccmk' not in r and 'url(' not in r and not re.match(r'\s*\.sa\{container-type', r)]
k = t.rindex('</head>')
t = t[:k] + MARK + '\n' + '\n'.join(new) + '\n</style>\n' + t[k:]
p.write_text(t, encoding='utf-8')
print('porté', p.name, len(new), 'règles')
