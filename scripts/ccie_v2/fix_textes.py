"""Corrige les restes de texte ASCIL (marque, association, province, article « de le »).

Usage: python3 -I fix_textes.py <scratchpad> <repo>
Pages : remplacements exacts dans le template (forme échappée JSON). Traductions : mêmes
clés renommées dans i18n/en.json et ar.json pour que la recherche par texte français marche.
"""
import sys, re, json, pathlib, collections
sys.path.insert(0, sys.argv[1])
from bundle import split, join
R = pathlib.Path(sys.argv[2])

PAGE = [  # forme décodée du template
    ('Islamique Louperivoise<', "Islamique d'Edmundston<"),
    ('Edmundston, Qu\u00e9bec<', 'Edmundston, Nouveau-Brunswick<'),
    ('#fff">ASCIL</p>', '#fff">CCIE</p>'),
    ('font-weight:800">ASCIL</span>', 'font-weight:800">CCIE</span>'),
    ('color:#141A2B">ASCIL</span>', 'color:#141A2B">CCIE</span>'),
    ('aria-label="ASCIL \u2014 Edmundston Islamic Centre, accueil', 'aria-label="Centre Islamique d\'Edmundston \u2014 Edmundston Islamic Centre, accueil'),
    ('aria-label="ASCIL, accueil', 'aria-label="Centre Islamique d\'Edmundston, accueil'),
    ('de le Centre Islamique', 'du Centre Islamique'),
]
KEYS = [  # clés de traduction : même texte français que les pages
    ('Islamique Louperivoise', "Islamique d'Edmundston"),
    ('de l’Centre Islamique', 'du Centre Islamique'),
    ('L’Centre Islamique', 'Le Centre Islamique'),
    ('l’Centre Islamique', 'le Centre Islamique'),
]
COPY = {'en': 'Edmundston, New Brunswick', 'ar': None}

hit = collections.Counter()
for p in sorted(R.glob('*.html')):
    t = p.read_text(encoding='utf-8')
    if '<script type="__bundler/template">' not in t:
        continue
    i, j, tpl = split(t)
    n = tpl
    for a, b in PAGE:
        hit[a] += n.count(a)
        n = n.replace(a, b)
    n, k = re.subn(r'(class="lg-t1"[^>]*>)ASCIL<', r'\1CCIE<', n)
    hit['lg-t1 ASCIL'] += k
    if n != tpl:
        p.write_text(join(t, i, j, n), encoding='utf-8')
        hit['pages'] += 1

for lang in ('en', 'ar'):
    f = R / 'i18n' / (lang + '.json')
    d = json.loads(f.read_text(encoding='utf-8'))
    s = {}
    for k, v in d['strings'].items():
        nk = k
        for a, b in KEYS:
            nk = nk.replace(a, b)
        if nk != k:
            hit['clé ' + lang] += 1
        s.setdefault(nk, v)
    d['strings'] = s
    for pat in d['patterns']:
        if 'Edmundston, Québec$' in pat[0]:
            pat[0] = pat[0].replace('Edmundston, Québec$', 'Edmundston, Nouveau-Brunswick$')
            if lang == 'en':
                pat[1] = pat[1].replace('Edmundston, Quebec', COPY['en'])
            else:
                pat[1] = pat[1].replace('إدموندستون، كيبيك', 'إدموندستون، نيو برونزويك')
            hit['motif ' + lang] += 1
    old = f.read_text(encoding='utf-8')
    f.write_text(json.dumps(d, ensure_ascii=False, indent=0) + ('\n' if old.endswith('\n') else ''), encoding='utf-8')
for k, v in hit.items():
    print(v, k)
