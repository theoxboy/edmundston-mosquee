"""Logo CCIE : remplace l'ancien logo (dôme + croissant) par le logo A (la coupole et la rivière) de « effets 1 ».

Usage: python3 -I port_logo.py <scratchpad> <planche v2> <page.html> [...]
Chaque <svg> qui contient l'ancien croissant devient la marque v2 (class="mk"), à la même
taille d'affichage (carré de la plus grande dimension). Textes et scripts inchangés. Idempotent.
"""
import sys, re, pathlib
sys.path.insert(0, sys.argv[1])
from bundle import split, join

CRES = '127.83 20.67 Z'
# logo A de la maquette « effets 1 » (la coupole et la rivière), couleurs du site ; classes s1 s2 cr w1 w2
MARK = ('<svg class="mk mkc" aria-hidden="true" width="50" height="50" sc-camel-view-box="0 0 120 120" style="flex:none;overflow:visible">'
        '<path class="s1" sc-camel-path-length="1" d="M24 86V62C24 44 44 38 60 24C76 38 96 44 96 62V86" fill="none" stroke="#A8813C" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"></path>'
        '<path class="s2" sc-camel-path-length="1" d="M47 86V68a13 13 0 0 1 26 0v18" fill="none" stroke="#A8813C" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round" opacity=".75"></path>'
        '<path class="cr" d="M60.0 4.0A7.0 7.0 0 1 0 67.0 11.0A5.5 5.5 0 1 1 60.0 4.0Z" fill="#8E6524"></path>'
        '<path class="w1" sc-camel-path-length="1" d="M14 99q11.5-7 23 0t23 0 23 0 23 0" fill="none" stroke="#8E6524" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"></path>'
        '<path class="w2" sc-camel-path-length="1" d="M30 111q7.5-5 15 0t15 0 15 0 15 0" fill="none" stroke="#8E6524" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" opacity=".6"></path></svg>')
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
            m = m.replace('class="mk mkc"', 'class="mk mkc %s"' % cls.group(1), 1)
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
