"""Logo v2 sur SA-Comptes.html (HTML simple : attributs viewBox/pathLength en clair). Idempotent."""
import sys, re, pathlib
sys.path.insert(0, sys.argv[1])
from bundle import split
import importlib.util
spec = importlib.util.spec_from_file_location('pl', pathlib.Path(sys.argv[1]) / 'port_logo_mark.py'); pl = importlib.util.module_from_spec(spec); spec.loader.exec_module(pl)
m = pl.MARK
m = re.sub(r'sc-camel-(view-box|path-length)=', lambda x: {'view-box': 'viewBox=', 'path-length': 'pathLength='}[x.group(1)], m)
m = m.replace('width="50" height="50"', 'width="34" height="34"')
p = pathlib.Path(sys.argv[3]); t = p.read_text(encoding='utf-8')
c = t.find('127.83 20.67 Z')
if c < 0:
    sys.exit(print('déjà porté', p.name))
s = t.rfind('<svg', 0, c); e = t.index('</svg>', c) + 6
assert t[s:e].count('<svg') == 1
p.write_text(t[:s] + m + t[e:], encoding='utf-8'); print('logo', p.name)
