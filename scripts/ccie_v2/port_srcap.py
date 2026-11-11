"""Légendes masquées des tableaux d'horaires : plus de « left:-9999px ».

Usage: python3 -I port_srcap.py <scratchpad> <page.html> [...]
En arabe (de droite à gauche), une légende placée à -9999 px rendait la page
10 000 px plus large : on pouvait glisser sur le côté vers un grand vide.
Elle reste lue par les lecteurs d'écran, mais tient dans 1 px, à sa place.
Idempotent.
"""
import sys, pathlib
sys.path.insert(0, sys.argv[1])
from bundle import split, join

OLD = 'style="position:absolute;left:-9999px"'
NEW = 'style="position:absolute;width:1px;height:1px;margin:-1px;padding:0;border:0;overflow:hidden;clip:rect(0 0 0 0);clip-path:inset(50%);white-space:nowrap"'
TAGS = ('<caption ', '<sc-raw-caption ')

for p in map(pathlib.Path, sys.argv[2:]):
    t = p.read_text(encoding='utf-8')
    bundled = '__bundler/template' in t
    if bundled:
        i, j, tpl = split(t)
    else:
        tpl = t
    n = 0
    for tag in TAGS:
        n += tpl.count(tag + OLD)
        tpl = tpl.replace(tag + OLD, tag + NEW)
    if not n:
        continue
    p.write_text(join(t, i, j, tpl) if bundled else tpl, encoding='utf-8')
    print('légende', p.name, n)
