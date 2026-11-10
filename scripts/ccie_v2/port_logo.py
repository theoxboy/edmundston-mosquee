"""Logo CCIE v2 : remplace l'ancien logo (dôme + croissant) par la marque des planches.

Usage: python3 -I port_logo.py <scratchpad> <planche v2> <page.html> [...]
Chaque <svg> qui contient l'ancien croissant devient la marque v2 (class="mk"), à la même
taille d'affichage (carré de la plus grande dimension). Textes et scripts inchangés. Idempotent.
"""
import sys, re, pathlib
sys.path.insert(0, sys.argv[1])
from bundle import split, join

CRES = '127.83 20.67 Z'
vt = split(pathlib.Path(sys.argv[2]).read_text(encoding='utf-8'))[2]
i = vt.index('<svg class="mk" aria-hidden="true" width="50"')
MARK = vt[i:vt.index('</svg>', i) + 6]
assert MARK.count('<svg') == 1

for p in map(pathlib.Path, sys.argv[3:]):
    t = p.read_text(encoding='utf-8')
    a, b, tpl = split(t)
    out, pos, n = [], 0, 0
    while True:
        c = tpl.find(CRES, pos)
        if c < 0:
            break
        s = tpl.rfind('<svg', 0, c)
        e = tpl.index('</svg>', c) + 6
        old = tpl[s:e]
        if old.count('<svg') != 1:
            raise SystemExit('svg imbriqué inattendu : ' + p.name)
        head = old[:old.index('>')]
        w = re.search(r'\swidth="(\d+(?:\.\d+)?)"', head)
        h = re.search(r'\sheight="(\d+(?:\.\d+)?)"', head)
        size = max(float(w.group(1)) if w else 44, float(h.group(1)) if h else 44)
        size = ('%g' % size)
        m = MARK.replace('width="50" height="50"', 'width="%s" height="%s"' % (size, size), 1)
        cls = re.search(r'\sclass="([^"]+)"', head)  # garde les classes de mise en page (ex. lg-ic)
        if cls:
            m = m.replace('class="mk"', 'class="mk %s"' % cls.group(1), 1)
        sty = re.search(r'\sstyle="([^"]*)"', head)
        if sty and 'display:none' in sty.group(1):
            m = m.replace('style="flex:none;overflow:visible"', 'style="%s"' % sty.group(1), 1)
        out.append(tpl[pos:s] + m)
        pos, n = e, n + 1
    if not n:
        print('rien', p.name)
        continue
    tpl = ''.join(out) + tpl[pos:]
    p.write_text(join(t, a, b, tpl), encoding='utf-8')
    print('logo', p.name, n)
