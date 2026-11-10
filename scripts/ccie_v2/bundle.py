import base64, gzip, json, re, zlib, pathlib, collections
OPEN = '<script type="__bundler/template">'
def split(text):
    i = text.index(OPEN) + len(OPEN); j = text.index('</script>', i)
    return i, j, json.loads(text[i:j])
def join(text, i, j, tpl):
    enc = json.dumps(tpl).replace('</', '<\\u002F'); assert json.loads(enc) == tpl
    return text[:i] + enc + text[j:]
def manifest(text):
    m = re.search(r'<script type="__bundler/manifest"[^>]*>(.*?)</script>', text, re.S)
    return json.loads(m.group(1)) if m else {}
def dec(entry):
    raw = base64.b64decode(entry['data'])
    if entry.get('compressed', True):
        try: raw = gzip.decompress(raw)
        except OSError:
            try: raw = zlib.decompress(raw, -15)
            except Exception: pass
    return raw
HEX = re.compile(r'#[0-9A-Fa-f]{6}\b|#[0-9A-Fa-f]{3}\b')
def colors(s):
    return collections.Counter(h.upper() for h in HEX.findall(s))

MAN = re.compile(r'(<script type="__bundler/manifest"[^>]*>\s*)(.*?)(\s*</script>)', re.S)


def add_assets(text, src_text, uuids):
    """Copie dans le manifest de `text` les assets `uuids` présents dans celui de `src_text`."""
    m = MAN.search(text)
    man = json.loads(m.group(2))
    src = manifest(src_text)
    added = [u for u in uuids if u not in man and u in src]
    if not added:
        return text, []
    for u in added:
        man[u] = src[u]
    enc = json.dumps(man, separators=(',', ':'))
    return text[:m.start(2)] + enc + text[m.end(2):], added
