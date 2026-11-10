"""Étape V : réglages communs du site (panneau Accueil → Coordonnées et Pied de page) sur TOUTES
les pages publiques, et plus seulement sur l'accueil.

Un même petit script (#ascil-pied-live) lit /api/settings/home et applique, dans le pied de page et
le bandeau du haut uniquement (jamais dans le contenu propre d'une page) :
  - courriel (lien et texte), lien Facebook, lien de carte, adresse du pied de page ;
  - liens TCOM et CCIQ ; la ligne CCIQ est masquée tant qu'elle n'a pas de lien (dans la page
    elle-même : <li hidden>, sans lien « # » ; le script l'affiche dès qu'un lien https est enregistré) ;
  - lignes du pied de page affichées ou masquées (Facebook, TCOM, CCIQ, courriel, heures) et bouton Itinéraire.
Les valeurs sont relues à chaque nouveau rendu de la page (React), sans boucle : rien n'est écrit
si la valeur est déjà la bonne.
Aussi : la page Inscription aux événements (PC, M-, T-) perd la note « Petite app future — prototype »
et l'étiquette [EXEMPLE À MODIFIER] ; l'aide du champ CCIQ du panneau Accueil dit que la ligne est masquée
tant qu'elle est vide.
Ordre : après wire_formulaires.py, avant fix_inputs.py. Idempotent.
"""
import json, re, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
OPEN = '<script type="__bundler/template">'

SCRIPT = r"""<script id="ascil-pied-live">
(function () {
  var s = null, busy = false;
  var https = function (u) { return typeof u === 'string' && /^https:\/\/[^\s<>"]{3,}$/i.test(u.trim()); };
  function zones() { return Array.prototype.slice.call(document.querySelectorAll('footer, header.hdr > div:first-child')); }
  function each(sel, fn) { zones().forEach(function (z) { z.querySelectorAll(sel).forEach(fn); }); }
  function show(el, on) { if (el && el.style.display !== (on ? '' : 'none')) el.style.display = on ? '' : 'none'; }
  function setHref(a, u) { if (a.getAttribute('href') !== u) a.setAttribute('href', u); }
  function followList() {
    var lists = document.querySelectorAll('footer ul');
    for (var i = 0; i < lists.length; i++) if (/CCIQ|TCOM/.test(lists[i].textContent)) return lists[i];
    return null;
  }
  function apply() {
    if (!s || busy) return;
    busy = true;
    try {
      var g = s.general || {}, pied = s.pied || {}, on = s.on || {};
      if (g.email && /@/.test(g.email)) {
        each('a[href^="mailto:"]', function (a) {
          setHref(a, 'mailto:' + g.email.trim());
          Array.prototype.forEach.call(a.childNodes, function (n) {
            if (n.nodeType === 3 && /@/.test(n.nodeValue) && n.nodeValue.trim() !== g.email.trim()) n.nodeValue = g.email.trim();
          });
        });
      }
      if (https(g.facebook)) {
        each('a[href*="facebook.com"]', function (a) { setHref(a, g.facebook.trim()); });
        // Ailleurs dans la page : seuls les liens vers l'accueil de Facebook (jamais partage ou vidéo).
        document.querySelectorAll('a[href="https://www.facebook.com/"]').forEach(function (a) { setHref(a, g.facebook.trim()); });
      }
      if (https(g.mapUrl)) each('a[href*="maps.google."]', function (a) { setHref(a, g.mapUrl.trim()); });
      if (g.address || g.city) {
        var adr = document.querySelector('footer .g4 > div:first-child > p');
        var want = (g.address || '34, 37e Avenue') + '\n' + (g.city || 'Edmundston, NB E3V 3S2');
        if (adr && adr.innerText.replace(/\r/g, '').trim() !== want) {
          adr.textContent = '';
          adr.appendChild(document.createTextNode(g.address || '34, 37e Avenue'));
          adr.appendChild(document.createElement('br'));
          adr.appendChild(document.createTextNode(g.city || 'Edmundston, NB E3V 3S2'));
        }
      }
      var ul = followList();
      if (ul) {
        Array.prototype.forEach.call(ul.children, function (li) {
          var a = li.querySelector('a'); if (!a) return;
          var t = li.textContent;
          if (/CCIQ/.test(t)) {
            if (https(pied.cciq)) setHref(a, pied.cciq.trim());
            var vis = https(pied.cciq) && on.pCciq !== false;
            if (li.hidden === vis) li.hidden = !vis;
            show(li, vis);
          } else if (/TCOM/.test(t)) {
            if (https(pied.tcom)) setHref(a, pied.tcom.trim());
            show(li, on.pTcom !== false);
          } else if (/facebook\.com/.test(a.getAttribute('href') || '')) {
            show(li, on.pFb !== false);
          } else if (/^mailto:/.test(a.getAttribute('href') || '')) {
            show(li, on.pMail !== false);
          }
        });
      }
      show(document.querySelector('footer a.btn-gold'), on.pIti !== false);
      show(document.querySelector('footer .g4 > div:first-child > p.tnum'), on.pHor !== false);
    } catch (e) { /* une page sans pied de page : rien à faire */ }
    busy = false;
  }
  var timer = null;
  function later() { clearTimeout(timer); timer = setTimeout(apply, 60); }
  fetch('/api/settings/home').then(function (r) { return r.ok ? r.json() : null; }).then(function (d) {
    if (!d || !d.ok || !d.settings) return;
    s = d.settings;
    apply();
    new MutationObserver(later).observe(document.documentElement, { childList: true, subtree: true });
  }, function () {});
})();
</script>
"""


def load(path):
    s = path.read_text(encoding='utf-8')
    i = s.index(OPEN) + len(OPEN)
    j = s.index('</script>', i)
    return s, i, j, json.loads(s[i:j])


def main():
    n = 0
    pages = [p for p in sorted(ROOT.glob('*.dc.html')) if not p.name.startswith('SA-')] + [ROOT / 'index.html', ROOT / '404.html']
    for path in pages:
        if not path.exists():
            continue
        s, i, j, tpl = load(path)
        if '<footer' not in tpl:
            continue
        tpl = re.sub(r'<script id="ascil-pied-live">.*?</script>\s*', '', tpl, flags=re.S)
        # Ligne CCIQ : masquée tant qu'elle n'a pas de lien (plus de lien « # » dans la page).
        tpl = re.sub(r'<li><a href="#"( style="[^"]*">(?:(?!</a>).)*CCIQ)', r'<li hidden><a\1', tpl, flags=re.S)
        assert not re.search(r'<a href="#"[^>]*>(?:(?!</a>).)*CCIQ', tpl), path.name
        k = tpl.rindex('</body>')
        tpl = tpl[:k] + SCRIPT + tpl[k:]
        enc = json.dumps(tpl).replace('</', '<\\u002F')
        assert json.loads(enc) == tpl
        path.write_text(s[:i] + enc + s[j:], encoding='utf-8')
        n += 1
    print(f'réglages communs (pied de page, coordonnées, CCIQ) appliqués sur {n} pages publiques')


def save(path, s, i, j, tpl):
    enc = json.dumps(tpl).replace('</', '<\\u002F')
    assert json.loads(enc) == tpl
    path.write_text(s[:i] + enc + s[j:], encoding='utf-8')


def clean_inscription():
    for name in ('N3-Inscription.dc.html', 'M-N3-Inscription.dc.html', 'T-N3-Inscription.dc.html'):
        path = ROOT / name
        s, i, j, tpl = load(path)
        tpl = re.sub(r'<div class="flag" role="note"[^>]*>(?:(?!</div>).)*?Petite app future(?:(?!</div>).)*</div>', '', tpl, count=1, flags=re.S)
        tpl = tpl.replace('Événement <span class="ex" style="background:#FFF8E8">[EXEMPLE À MODIFIER]</span>', 'Événement')
        assert 'EXEMPLE À MODIFIER' not in tpl and 'Petite app future' not in tpl, name
        save(path, s, i, j, tpl)
    print('Inscription aux événements (PC, M-, T-) : note de prototype et étiquette d’exemple retirées')


def cciq_hint():
    path = ROOT / 'SA-Panneau.dc.html'
    s, i, j, tpl = load(path)
    old = 'id="f-cciq" type="url" placeholder="https://…"><p class="hint">Vide = pas encore de lien.</p>'
    new = 'id="f-cciq" type="url" placeholder="https://…"><p class="hint">Vide = la ligne CCIQ est masquée dans le pied de page de toutes les pages.</p>'
    if old in tpl:
        tpl = tpl.replace(old, new, 1)
    assert new in tpl, 'aide du champ CCIQ introuvable'
    save(path, s, i, j, tpl)


if __name__ == '__main__':
    main()
    clean_inscription()
    cciq_hint()
