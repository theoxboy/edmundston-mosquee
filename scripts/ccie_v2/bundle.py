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
