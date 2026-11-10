"""Remap CCIE v1 / ASCIL -> CCIE v2 colours, by string replacement in each page template.

Usage: python3 -I remap_v2.py <scratchpad> <repo> [--dry]
Only the __bundler/template JSON string is touched (SA-Comptes.html has none: whole file).
One regex pass per page, so maps never chain. #B3261E and the logo crescent are protected.
"""
import sys, re, pathlib, collections
sys.path.insert(0, sys.argv[1])
from bundle import split, join

ROOT = pathlib.Path(sys.argv[2])
DRY = '--dry' in sys.argv

# --- palette principale (pages publiques) : CCIE v1 + restes ASCIL -> v2 -----------------
MAIN = {
    '#0B0F1A': '#141A2B', '#07090F': '#0B0F1A', '#D9B46C': '#A8813C', '#F4EBD6': '#F3ECDD',
    '#E9E3D3': '#E7DCC6', '#141B2C': '#141A2B', '#515B66': '#5B6272', '#7A5A1E': '#8E6524',
    '#3A4842': '#4B5262', '#FFFEF9': '#FBF8F1', '#F7F2E4': '#F7F1E4', '#E9DCBF': '#E7DCC6',
    '#CDBF9C': '#D5C6A6', '#BBA672': '#C2A874', '#FBF7EC': '#FBF6EB', '#AE8436': '#8E6524',
    '#E3C27E': '#D4AE62', '#FBF3E0': '#FBF6EB',
    # restes ASCIL encore présents sur certaines pages publiques
    '#0E4D3C': '#141A2B', '#08362A': '#0B0F1A', '#F3EAD8': '#F3ECDD', '#4F5E57': '#5B6272',
    '#1E2B26': '#141A2B', '#E4D9C0': '#E7DCC6',
    'rgba(14,77,60': 'rgba(20,26,43', 'rgba(196,154,74': 'rgba(168,129,60',
    'rgba(243,234,216': 'rgba(243,236,221', 'rgba(255,254,249': 'rgba(251,248,241',
}
MAIN_PRE = [  # rôles précis repris des planches v2, appliqués avant la table
    ('.btn-gold{background:#D9B46C', '.btn-gold{background:#B88A3E'),
    ('linear-gradient(90deg,#D9B46C,#E3C27E)', 'linear-gradient(90deg,#6B4C1A,#D4AE62)'),
]

# --- superadmin SA-* : ASCIL -> v2 (planche 3.html) ---------------------------------------
SA = {
    '#0E4D3C': '#141A2B', '#08362A': '#0B0F1A', '#F3EAD8': '#F3ECDD', '#C49A4A': '#B88A3E',
    '#4F5E57': '#5B6272', '#E4D9C0': '#E7DCC6', '#1E2B26': '#141A2B', '#7A5A1E': '#8E6524',
    '#FAF8F1': '#FBF8F1', '#F7F2E4': '#F7F1E4', '#CDBF9C': '#D5C6A6', '#CFC6B1': '#D5C9B0',
    '#FFFEF9': '#FBF8F1', '#FBF3E0': '#FBF6EB', '#AE8436': '#A8813C', '#FAF6EC': '#FBF6EB',
    '#3D4A44': '#4B5262',
    'rgba(14,77,60': 'rgba(20,26,43', 'rgba(196,154,74': 'rgba(168,129,60',
    'rgba(243,234,216': 'rgba(243,236,221', 'rgba(30,43,38': 'rgba(20,26,43',
}

# --- thèmes saisonniers TH-* : ancienne palette -> palette v2 de 4.html --------------------
# Restes de l'habillage commun (bannière d'alerte, langues, pied) : vers la palette de la saison.
CHROME = {'#C49A4A': '#A8813C', '#F3EAD8': '#F0D9A4'}
TH = {
    'Ramadan': dict(CHROME, **{
        '#7FA9E0': '#C9A0DC', '#BAC3DC': '#CDBFD8', '#0A1430': '#1A0F2E', '#141B33': '#211634',
        '#1B2B5C': '#3A2160', '#13224F': '#2D1A4D', '#070F26': '#120A22',
        '#0E4D3C': '#1A0F2E', '#1E2B26': '#211634', 'rgba(10,20,48': 'rgba(26,15,46'}),
    'Fitr': dict(CHROME, **{
        '#0E6B4F': '#1D3F8F', '#7CC6A6': '#8FB2EA', '#16865F': '#2E5FC4', '#E07A68': '#D96C8A',
        '#BFE3D6': '#C6D6F2', '#E5F4EC': '#E8EFFB', '#D8F0E4': '#DCE6F8', '#0B523C': '#142F6E',
        '#4F5E57': '#5B6272', '#0E4D3C': '#141A2B', '#1E2B26': '#141A2B',
        'rgba(14,77,60': 'rgba(20,26,43'}),
    'Adha': dict(CHROME, **{
        '#1B4D3A': '#40182A', '#B5573A': '#C4874A', '#2E2117': '#2A1520', '#5E4D3C': '#5E4652',
        '#23634B': '#5C2338', '#7A3A22': '#7A4A1F', '#0E4D3C': '#40182A', '#1E2B26': '#2A1520'}),
    'Vendredi': dict(CHROME, **{
        '#0F5F55': '#141A2B', '#DCE3DA': '#E7DCC6', '#E3F0EB': '#F3ECDD', '#CFE3DC': '#E6DAC0',
        '#0B3F38': '#0B0F1A', '#157A6D': '#26304A', '#46605A': '#5B6272', '#12302A': '#0E1322',
        '#F7F4EC': '#F7F1E4', '#F4F1E6': '#FBF8F1', '#D8E8E2': '#EFE5D2', '#13705F': '#1E2742',
        '#1C8A79': '#2E3A5C', '#0E4D3C': '#141A2B', '#1E2B26': '#0E1322',
        'rgba(15,95,85': 'rgba(20,26,43', 'rgba(6,38,33': 'rgba(8,10,20'}),
}

PROTECT = ['#B3261E']
LOGO = re.compile(r'(A9\.33 9\.33 0 0 1 127\.83 20\.67 Z" fill=")(#[0-9A-Fa-f]{6})')  # croissant du logo


def remap(s, table, pre=()):
    for a, b in pre:
        s = s.replace(a, b)
    logos = []
    s = LOGO.sub(lambda m: (logos.append(m.group(2)), m.group(1) + '\x00LOGO%d\x00' % (len(logos) - 1))[1], s)
    hexes = {k.upper(): v for k, v in table.items() if k.startswith('#')}
    rgbas = {k: v for k, v in table.items() if k.startswith('rgb')}
    for p in PROTECT:
        assert p not in hexes
    hit = collections.Counter()
    def h(m):
        k = m.group(0).upper()
        if k in hexes:
            hit[k] += 1
            return hexes[k]
        return m.group(0)
    s = re.sub(r'#[0-9A-Fa-f]{6}(?![0-9A-Fa-f])', h, s)
    if rgbas:
        def r(m):
            k = re.sub(r'\s', '', m.group(0))
            if k in rgbas:
                hit[k] += 1
                return rgbas[k]
            return m.group(0)
        s = re.sub(r'rgba?\(\s*\d+\s*,\s*\d+\s*,\s*\d+', r, s)
    for n, v in enumerate(logos):
        s = s.replace('\x00LOGO%d\x00' % n, v)
    return s, hit


def group(name):
    if name.startswith('TH-'):
        return 'TH', TH[name.split('-')[1]], ()
    if name.startswith('SA-') or name == 'superadmin.html':
        return 'SA', SA, ()
    return 'MAIN', MAIN, MAIN_PRE


PUBLIC_EXTRA = {'404.html', 'index.html', 'site-gratuit-mosquee.html', 'superadmin.html', 'SA-Comptes.html'}
files = sorted(p for p in ROOT.glob('*.html') if p.name.endswith('.dc.html') or p.name in PUBLIC_EXTRA)
tot = collections.Counter()
for p in files:
    g, table, pre = group(p.name)
    text = p.read_text(encoding='utf-8')
    if p.name == 'SA-Comptes.html':
        new, hit = remap(text, table)
    else:
        i, j, tpl = split(text)
        ntpl, hit = remap(tpl, table, pre)
        new = join(text, i, j, ntpl)
    tot[g] += sum(hit.values())
    print(f'{p.name:34} {g:5} {sum(hit.values()):5} remplacements')
    if not DRY and new != text:
        p.write_text(new, encoding='utf-8')
print(dict(tot), 'DRY' if DRY else 'ÉCRIT')
