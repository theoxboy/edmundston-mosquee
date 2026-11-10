"""Versions arabe et anglaise du site public (étape L).

1. scripts/i18n/strings.json et scripts/i18n/*.tsv (sources, éditées à la main) -> i18n/ar.json et
   i18n/en.json (seuls fichiers publics, servis tels quels).
   Clé = texte français exact, espaces normalisés ; valeur = traduction. « __patterns » : motifs pour
   les textes calculés (heures, compte à rebours…), en expressions régulières.
2. Un même script (#ascil-i18n) dans les 59 pages publiques :
   - langue choisie : ?lang=fr|ar|en dans l'adresse, sinon le choix gardé dans le navigateur, sinon français ;
   - le sélecteur existant (liste « Français / العربية / English » sur PC, pastilles FR / العربية / EN
     dans le menu mobile) change vraiment de langue, à la souris comme au clavier ;
   - en arabe : <html lang="ar" dir="rtl">, police Cairo (/fonts/cairo) ; en anglais : <html lang="en"> ;
   - chaque texte et chaque attribut (aria-label, placeholder, title, alt) dont le français est dans le
     dictionnaire est remplacé, y compris après chaque nouveau rendu (MutationObserver, seulement sur
     les parties modifiées) ; un texte absent du dictionnaire reste en français ;
   - une langue désactivée dans le panneau (Site entier -> Langues) n'est jamais appliquée ;
   - les traductions saisies dans la rubrique Traductions du panneau (clé « traductions »,
     wire_traductions.py) passent avant le dictionnaire du site.
3. Rapport : textes fixes des pages encore sans traduction, listés dans scripts/i18n-a-traduire.txt
   (fichier de travail, non servi : /scripts/* passe par les Functions).
Ordre : après wire_nettoyage.py, avant fix_inputs.py. Idempotent.
"""
import json, re, html, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / 'scripts' / 'i18n'   # sources du dictionnaire (privées : /scripts/* n'est pas servi)
OPEN = '<script type="__bundler/template">'
LANGS = ('ar', 'en')

SCRIPT = r"""<script id="ascil-i18n">
(function () {
  var KEY = 'ascil-lang', OK = { fr: 1, ar: 1, en: 1 };
  var NAMES = { 'Français': 'fr', 'FR': 'fr', 'العربية': 'ar', 'English': 'en', 'EN': 'en' };
  var SHORT = { fr: 'FR', ar: 'ع', en: 'EN' };
  function store(l) { try { localStorage.setItem(KEY, l); } catch (e) {} }
  function pick() {
    var q = null;
    try { q = new URLSearchParams(location.search).get('lang'); } catch (e) {}
    if (q && OK[q]) { store(q); return q; }
    try { var v = localStorage.getItem(KEY); if (v && OK[v]) return v; } catch (e) {}
    return 'fr';
  }
  var lang = pick();
  function choose(l) {
    if (!OK[l] || l === lang) return;
    store(l);
    try {
      var u = new URL(location.href);
      if (u.searchParams.has('lang')) { u.searchParams.set('lang', l); location.replace(u.href); return; }
    } catch (e) {}
    location.reload();
  }
  function langOf(el) {
    var o = el.closest && el.closest('li[role="option"], span.pill');
    if (!o) return null;
    var l = NAMES[(o.textContent || '').trim()];
    return l ? { el: o, l: l } : null;
  }
  document.addEventListener('click', function (e) {
    var h = langOf(e.target);
    if (h) { e.preventDefault(); choose(h.l); }
  }, true);
  document.addEventListener('keydown', function (e) {
    if (e.key !== 'Enter' && e.key !== ' ') return;
    var h = langOf(e.target);
    if (h) { e.preventDefault(); choose(h.l); }
  }, true);

  // Sélecteur : options atteignables au clavier et langue active indiquée.
  function marks() {
    document.querySelectorAll('li[role="option"]').forEach(function (li) {
      var l = NAMES[(li.textContent || '').trim()];
      if (!l) return;
      if (!li.hasAttribute('tabindex')) li.setAttribute('tabindex', '0');
      li.style.cursor = 'pointer';
      var want = l === lang ? 'true' : 'false';
      if (li.getAttribute('aria-selected') !== want) li.setAttribute('aria-selected', want);
      li.style.fontWeight = l === lang ? '700' : '';
    });
    document.querySelectorAll('span.pill').forEach(function (p) {
      var l = NAMES[(p.textContent || '').trim()];
      if (!l) return;
      if (p.getAttribute('role') !== 'button') { p.setAttribute('role', 'button'); p.setAttribute('tabindex', '0'); p.style.cursor = 'pointer'; }
      var want = l === lang ? 'true' : 'false';
      if (p.getAttribute('aria-pressed') !== want) p.setAttribute('aria-pressed', want);
      var on = l === lang;
      var bg = on ? '#0E4D3C' : '#F3EAD8', fg = on ? '#fff' : '#1E2B26';
      if (p.style.background !== bg && p.dataset.i18nBg !== bg) { p.style.background = bg; p.style.color = fg; p.dataset.i18nBg = bg; }
    });
    document.querySelectorAll('.lang-desk > button').forEach(function (b) {
      for (var n = b.firstChild; n; n = n.nextSibling) {
        if (n.nodeType === 3 && n.nodeValue.trim()) {
          if (n.nodeValue.trim() !== SHORT[lang]) n.nodeValue = SHORT[lang] + ' ';
          break;
        }
      }
    });
  }

  var dict = null, pats = [];
  var SKIP = { SCRIPT: 1, STYLE: 1, TEXTAREA: 1, CODE: 1, PRE: 1, NOSCRIPT: 1 };
  var ATTRS = ['aria-label', 'placeholder', 'title', 'alt'];
  function norm(s) { return s.replace(/ /g, ' ').replace(/\s+/g, ' ').trim(); }
  // Garde-fou : sans dictionnaire (français, ou dictionnaire pas encore chargé), rien n'est traduit.
  var has = function (k) { return !!dict && Object.prototype.hasOwnProperty.call(dict, k); };
  // Dates écrites en français (« samedi 7 novembre 2026 », « 25 avr. 2026 », « Novembre 2026 »).
  var FR_M = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'];
  var FR_MS = ['janv', 'févr', 'mars', 'avr', 'mai', 'juin', 'juil', 'août', 'sept', 'oct', 'nov', 'déc'];
  var FR_D = ['dimanche', 'lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi'];
  var M = { ar: ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو', 'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر'],
    en: ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'] };
  var D = { ar: ['الأحد', 'الاثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت'],
    en: ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'] };
  function month(w) {
    w = w.toLowerCase().replace(/\.$/, '');
    var i = FR_M.indexOf(w); if (i < 0) i = FR_MS.indexOf(w); if (i < 0 && w === 'juill') i = 6;
    return i;
  }
  function date(k) {
    var m = k.match(/^(?:([a-zé]+)\.? )?(1er|\d{1,2}) ([a-zéû]+\.?)(?: (\d{4}))?$/i), mi, di = -1;
    if (m && (mi = month(m[3])) >= 0) {
      if (m[1]) { di = FR_D.indexOf(m[1].toLowerCase()); if (di < 0) return null; }
      var day = m[2] === '1er' ? '1' : m[2];
      if (lang === 'ar') return (di >= 0 ? D.ar[di] + ' ' : '') + day + ' ' + M.ar[mi] + (m[4] ? ' ' + m[4] : '');
      return (di >= 0 ? D.en[di] + ', ' : '') + M.en[mi] + ' ' + day + (m[4] ? ', ' + m[4] : '');
    }
    m = k.match(/^([a-zéû]+\.?) (\d{4})$/i);
    if (m && (mi = month(m[1])) >= 0) return M[lang][mi] + ' ' + m[2];
    m = k.match(/^([a-zéû]+)(\.?)$/i);
    if (m && !m[2] && (di = FR_D.indexOf(m[1].toLowerCase())) >= 0) return D[lang][di];
    if (m && (mi = month(m[1])) >= 0) {
      var w = lang === 'en' && m[2] ? M.en[mi].slice(0, 3) + '.' : M[lang][mi];
      return k === k.toUpperCase() && lang === 'en' ? w.toUpperCase() : w;
    }
    return null;
  }
  // Débuts de phrase suivis d'une valeur (« Iftar à 17:05 », « Enseignante : … », « Khutba en arabe »).
  var PREFIX_END = /(?:^|\s)(?:à|sous|par|en|le|sur|code|jusqu’à|Jusqu’à)$|[:«—]$/;
  var prefixes = null;
  function tr(s, depth) {
    if (!dict || lang === 'fr') return null;
    var k = norm(s);
    if (!k) return null;
    depth = depth || 0;
    if (has(k)) return dict[k];
    for (var i = 0; i < pats.length; i++) if (pats[i][0].test(k)) return k.replace(pats[i][0], pats[i][1]);
    var d = date(k); if (d) return d;
    // Titres de page : « Horaires — ASCIL », « Mariages — ASCIL (mobile) »…
    var m = k.match(/^(.+?) — ASCIL(?: \((?:mobile|tablette)\))?$/);
    if (m && has(m[1])) return dict[m[1]] + ' — ASCIL';
    if (depth > 2) return null;
    // Nombre suivi d'un texte connu : « 12 places restantes », « 50 000 $ récoltés · 50 % ».
    var n = k.match(/^([−+-]?\d[\d\s.,]*(?:\s?[$%])?) (.+)$/);
    if (n) { var r0 = tr(n[2], depth + 1); if (r0 != null) return n[1] + ' ' + r0; }
    if (!prefixes) prefixes = Object.keys(dict).filter(function (x) { return PREFIX_END.test(x); }).sort(function (a, b) { return b.length - a.length; });
    for (var j = 0; j < prefixes.length; j++) {
      var p = prefixes[j];
      if (k.length > p.length + 1 && k.slice(0, p.length + 1) === p + ' ') {
        var rest = k.slice(p.length + 1), rr = tr(rest, depth + 1);
        return dict[p] + ' ' + (rr != null ? rr : rest);
      }
    }
    return null;
  }
  function skip(el) {
    for (var e = el; e && e.nodeType === 1; e = e.parentElement) {
      if (SKIP[e.tagName] || e.isContentEditable || e.hasAttribute('data-no-i18n') || e.getAttribute('translate') === 'no') return true;
    }
    return false;
  }
  // En arabe (de droite à gauche), un nombre en plusieurs morceaux (« 50 000 $ », « 17 % », « 06:30 »)
  // serait lu bloc par bloc et inversé (« $ 000 350 ») : chaque nombre est tenu en un seul bloc
  // lu de gauche à droite, entre deux marques invisibles (isolement Unicode U+2066 … U+2069).
  var ISO = /[\u2066\u2069]/g;
  var NUM = /[\u2212+-]?\d(?:[\d.,:\/]|[-\u2010\u2013](?=\d)|[\s\u00a0\u202f](?=[\d$%\u20ac])|[$%\u20ac])*/g;
  var MULTI = /\d[\s\u00a0\u202f.,:\/\u2010\u2013-]+\d|\d[\s\u00a0\u202f]?[$%\u20ac]|^[\u2212+-]/;
  function bidi(s) {
    if (lang !== 'ar' || !/\d/.test(s)) return s;
    return s.replace(ISO, '').replace(NUM, function (m) { return MULTI.test(m) ? '\u2066' + m + '\u2069' : m; });
  }
  function text(n) {
    if (!n.parentElement || skip(n.parentElement)) return;
    var v = n.nodeValue, plain = v.replace(ISO, ''), t = tr(plain);
    var nv = plain;
    if (t != null) nv = plain.match(/^\s*/)[0] + t + plain.match(/\s*$/)[0];
    nv = bidi(nv);
    if (nv !== v) n.nodeValue = nv;
  }
  function attrs(el) {
    if (skip(el)) return;
    for (var i = 0; i < ATTRS.length; i++) {
      var a = ATTRS[i], v = el.getAttribute(a);
      if (!v) continue;
      var t = tr(v);
      if (t != null && t !== v) el.setAttribute(a, t);
    }
  }
  function walk(root) {
    if (!root) return;
    if (root.nodeType === 3) { text(root); return; }
    if (root.nodeType !== 1 && root.nodeType !== 9) return;
    var w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null), n;
    while ((n = w.nextNode())) text(n);
    if (root.nodeType === 1) attrs(root);
    if (root.querySelectorAll) root.querySelectorAll('[aria-label],[placeholder],[title],[alt]').forEach(attrs);
  }
  var queue = [], timer = null;
  // Une erreur ici ne doit jamais se répéter à chaque rendu : elle est arrêtée et la page reste en l'état.
  function flush() {
    timer = null;
    var q = queue; queue = [];
    try {
      if (dict && lang !== 'fr') {
        for (var i = 0; i < q.length; i++) if (q[i].isConnected !== false) walk(q[i]);
        var t = tr(document.title); if (t != null && t !== document.title) document.title = t;
      }
      marks();
    } catch (e) { /* page laissée telle quelle */ }
  }
  function later(n) { if (lang === 'fr' || !dict) return; queue.push(n); if (!timer) timer = setTimeout(flush, 0); }

  function start() {
    var root = document.documentElement;
    try {
      if (lang !== 'fr' && dict) {
        root.setAttribute('lang', lang);
        root.setAttribute('dir', lang === 'ar' ? 'rtl' : 'ltr');
        walk(document.body);
        var t = tr(document.title); if (t != null) document.title = t;
      }
      marks();
    } catch (e) { /* page laissée telle quelle */ }
    new MutationObserver(function (recs) {
      for (var i = 0; i < recs.length; i++) {
        var r = recs[i];
        if (r.type === 'characterData') { if (lang !== 'fr') later(r.target); }
        else if (r.type === 'attributes') { if (lang !== 'fr') later(r.target); }
        else if (lang !== 'fr') for (var j = 0; j < r.addedNodes.length; j++) later(r.addedNodes[j]);
      }
      if (lang === 'fr' && !timer) timer = setTimeout(function () { timer = null; queue = []; try { marks(); } catch (e) {} }, 0);
    }).observe(root, lang === 'fr' ? { childList: true, subtree: true }
      : { childList: true, subtree: true, characterData: true, attributes: true, attributeFilter: ATTRS });
    var w = document.getElementById('ascil-i18n-wait'); if (w) w.remove();
  }

  if (lang === 'fr') { start(); return; }
  // Pendant le chargement du dictionnaire, la page reste masquée (au plus 2,5 s) pour éviter un flash en français.
  var st = document.createElement('style');
  st.id = 'ascil-i18n-wait';
  st.textContent = 'body{visibility:hidden}';
  document.head.appendChild(st);
  var css = document.createElement('style');
  css.id = 'ascil-i18n-css';
  // La police arabe (Cairo) est posée par la feuille fixe #ascil-cairo de chaque page.
  css.textContent = 'html[dir="rtl"] .tnum, html[dir="rtl"] time{unicode-bidi:isolate}';
  document.head.appendChild(css);
  var giveUp = setTimeout(function () { var w = document.getElementById('ascil-i18n-wait'); if (w) w.remove(); }, 2500);
  Promise.all([
    fetch('/i18n/' + lang + '.json').then(function (r) { return r.ok ? r.json() : null; }),
    fetch('/api/settings/languages').then(function (r) { return r.ok ? r.json() : null; }, function () { return null; }),
    // Traductions saisies dans le panneau (rubrique Traductions) : prioritaires sur le dictionnaire du site.
    fetch('/api/settings/traductions').then(function (r) { return r.ok ? r.json() : null; }, function () { return null; })
  ]).then(function (res) {
    clearTimeout(giveUp);
    var d = res[0], l = res[1], own = res[2];
    if (l && l.ok && l.settings && l.settings[lang] === false) { lang = 'fr'; store('fr'); }
    if (!d || lang === 'fr') { lang = 'fr'; start(); return; }
    dict = d.strings || {};
    if (own && own.ok && own.settings && Array.isArray(own.settings.items)) {
      own.settings.items.forEach(function (x) {
        if (x && typeof x.fr === 'string' && typeof x[lang] === 'string' && x[lang]) dict[norm(x.fr)] = x[lang];
      });
    }
    pats = (d.patterns || []).map(function (p) { try { return [new RegExp(p[0]), p[1]]; } catch (e) { return null; } }).filter(Boolean);
    start();
  }, function () { clearTimeout(giveUp); lang = 'fr'; start(); });
})();
</script>
"""


# Textes identiques dans les trois langues (noms propres, adresses, sélecteur de langue).
KEEP = {'ASCIL', 'FR', 'EN', 'English', 'Français', 'Facebook', '', 'gmail.com', 'N', '{x.texte}', '9 619 km'}


def norm(s):
    return re.sub(r'\s+', ' ', s.replace(' ', ' ')).strip()


def build():
    src = json.loads((SRC / 'strings.json').read_text(encoding='utf-8'))
    pats = src.get('__patterns', [])
    # Lots supplémentaires : une ligne par texte, « français<TAB>arabe<TAB>anglais ».
    for tsv in sorted(SRC.glob('*.tsv')):
        for n, line in enumerate(tsv.read_text(encoding='utf-8').splitlines(), 1):
            if not line.strip() or line.startswith('#'):
                continue
            cols = [c.strip() for c in line.split('\t')]
            assert len(cols) >= 3 and all(cols[:3]), f'{tsv.name}:{n} : il faut français, arabe et anglais'
            k = norm(cols[0])
            assert k not in src or src[k] == {'ar': cols[1], 'en': cols[2]}, f'{tsv.name}:{n} : « {k} » déjà traduit autrement'
            src[k] = {'ar': cols[1], 'en': cols[2]}
    for lg in LANGS:
        strings = {}
        for k, v in src.items():
            if k.startswith('__'):
                continue
            assert norm(k) == k, f'clé non normalisée : {k!r}'
            assert isinstance(v, dict) and v.get(lg), f'traduction {lg} manquante : {k!r}'
            strings[k] = v[lg]
        out = {'lang': lg, 'strings': strings, 'patterns': [[p['re'], p[lg]] for p in pats]}
        for p in pats:
            re.compile(p['re'])
        (ROOT / 'i18n' / f'{lg}.json').write_text(json.dumps(out, ensure_ascii=False, indent=0, sort_keys=True) + '\n', encoding='utf-8')
    return {k for k in src if not k.startswith('__')}, [re.compile(p['re']) for p in pats]


def load(path):
    s = path.read_text(encoding='utf-8')
    i = s.index(OPEN) + len(OPEN)
    j = s.index('</script>', i)
    return s, i, j, json.loads(s[i:j])


def visible_texts(tpl):
    f = re.sub(r'<(script|style)\b.*?</\1>', '', tpl, flags=re.S)
    out = set()
    for m in re.finditer(r'>([^<>]+)<', f):
        t = norm(html.unescape(m.group(1)))
        if t and '{{' not in t and re.search(r'[A-Za-zÀ-ÿ]', t):
            out.add(t)
    for m in re.finditer(r'\b(?:aria-label|placeholder|title|alt)="([^"{}]+)"', f):
        t = norm(html.unescape(m.group(1)))
        if re.search(r'[A-Za-zÀ-ÿ]', t):
            out.add(t)
    return out


# Police arabe Cairo (fichier variable, toutes les graisses ; licence SIL OFL dans /fonts/cairo/OFL.txt).
# Feuille FIXE dans chaque page (pas ajoutée par script), placée après les polices de la page :
# 1. toute lettre arabe s'affiche en Cairo, dans les trois langues, même dans un élément qui impose
#    'Noto Sans', 'Noto Serif' ou 'Noto Sans Arabic' dans son propre style (ces noms reçoivent
#    Cairo pour la plage de caractères arabes uniquement ; le latin garde sa police) ;
# 2. en version arabe (html lang="ar"), toute la page passe en Cairo, latin et chiffres compris,
#    malgré les polices écrites sur les éléments eux-mêmes (d'où !important) ; les icônes SVG et le code
#    ne changent pas.
AR_RANGE = 'U+0600-06FF,U+0750-077F,U+0870-089F,U+08A0-08FF,U+FB50-FDFF,U+FE70-FEFF,U+200C-200F'
FONT_STYLE = ('<style id="ascil-cairo">'
    + ''.join("@font-face{font-family:'%s';src:url('/fonts/cairo/Cairo-Variable.ttf') format('truetype');"
              "font-weight:100 1000;font-style:normal;font-display:swap;unicode-range:%s}" % (f, AR_RANGE)
              for f in ('Noto Sans', 'Noto Serif', 'Noto Sans Arabic'))
    + "@font-face{font-family:'Cairo';src:url('/fonts/cairo/Cairo-Variable.ttf') format('truetype');"
      "font-weight:200 1000;font-style:normal;font-display:swap}"
    + 'html[lang="ar"] body,html[lang="ar"] body *:not(svg):not(svg *):not(code):not(pre):not(kbd)'
      "{font-family:'Cairo',system-ui,sans-serif!important}"
    + '</style>\n')


def main():
    keys, pats = build()
    pages = [p for p in sorted(ROOT.glob('*.dc.html')) if not p.name.startswith('SA-')] + [ROOT / 'index.html', ROOT / '404.html']
    n, missing = 0, set()
    for path in pages:
        if not path.exists():
            continue
        s, i, j, tpl = load(path)
        if '<footer' not in tpl:
            continue
        tpl = re.sub(r'<script id="ascil-i18n">.*?</script>\s*', '', tpl, flags=re.S)
        tpl = re.sub(r'<style id="ascil-cairo">.*?</style>\s*', '', tpl, flags=re.S)
        k = tpl.rindex('</body>')
        tpl = tpl[:k] + FONT_STYLE + SCRIPT + tpl[k:]
        enc = json.dumps(tpl).replace('</', '<\\u002F')
        assert json.loads(enc) == tpl
        path.write_text(s[:i] + enc + s[j:], encoding='utf-8')
        n += 1
        for t in visible_texts(tpl):
            m = re.match(r'^(.+?) — ASCIL(?: \((?:mobile|tablette)\))?$', t)
            if m and m.group(1) in keys:
                continue
            if t in KEEP:
                continue
            if t not in keys and not any(p.search(t) for p in pats):
                missing.add(t)
    print(f'langues : sélecteur et traduction (arabe, anglais) sur {n} pages ; {len(keys)} textes au dictionnaire, '
          f'{len(missing)} textes fixes encore en français seulement')
    (ROOT / 'scripts' / 'i18n-a-traduire.txt').write_text('\n'.join(sorted(missing)) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
