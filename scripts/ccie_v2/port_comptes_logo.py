"""Logo v2 sur SA-Comptes.html (HTML simple : attributs viewBox/pathLength en clair). Idempotent."""
import sys, re, pathlib
sys.path.insert(0, sys.argv[1])
from bundle import split
vt = split(pathlib.Path(sys.argv[2]).read_text(encoding='utf-8'))[2]
i = vt.index('<svg class="mk" aria-hidden="true" width="50"')
m = vt[i:vt.index('</svg>', i) + 6]
m = re.sub(r'sc-camel-(view-box|path-length)=', lambda x: {'view-box': 'viewBox=', 'path-length': 'pathLength='}[x.group(1)], m)
m = m.replace('width="50" height="50"', 'width="34" height="34"')
p = pathlib.Path(sys.argv[3]); t = p.read_text(encoding='utf-8')
c = t.find('127.83 20.67 Z')
if c < 0:
    sys.exit(print('déjà porté', p.name))
s = t.rfind('<svg', 0, c); e = t.index('</svg>', c) + 6
assert t[s:e].count('<svg') == 1
p.write_text(t[:s] + m + t[e:], encoding='utf-8'); print('logo', p.name)
