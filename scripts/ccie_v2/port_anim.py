"""Logo C animé (maquette « effets 1 ») : chargement « 1 · Tracé lumineux » et apparition « Vague ».

Usage: python3 -I port_anim.py <scratchpad> [--loader] <page.html> [...]
Toutes les pages : le logo de l'en-tête joue « Vague » (lignes d'eau tracées de gauche à droite,
logo qui monte, nom qui glisse ; 1 s) une fois à l'ouverture, puis à chaque survol.
Avec --loader : écran « Tracé lumineux » (logo tracé, croissant, barre d'or ; cycle 3,6 s)
dans l'enveloppe de la page. Il n'apparaît que si l'ouverture dépasse 0,3 s, reste jusqu'à ce
que la page soit affichée, puis s'efface en fondu. Réduire les animations : rien ne bouge,
pas d'écran de chargement. Décoratif (aria-hidden). Idempotent.
"""
import sys, re, pathlib
sys.path.insert(0, sys.argv[1])
from bundle import split, join

MARK = '<style id="ccie-anim">'
SHELL_MARK = 'id="ccie-ldr-shell"'

def logo(camel=False):
    s = ('<svg class="mk" aria-hidden="true" width="120" height="120" viewBox="0 0 120 120" style="overflow:visible;display:block">'
         '<path class="s1" pathLength="1" d="M24 86V62C24 44 44 38 60 24C76 38 96 44 96 62V86" fill="none" stroke="#D9B46C" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"></path>'
         '<path class="s2" pathLength="1" d="M47 86V68a13 13 0 0 1 26 0v18" fill="none" stroke="#D9B46C" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round" opacity=".75"></path>'
         '<path class="cr" d="M60.0 4.0A7.0 7.0 0 1 0 67.0 11.0A5.5 5.5 0 1 1 60.0 4.0Z" fill="#F0D9A4"></path>'
         '<path class="w1" pathLength="1" d="M14 99q11.5-7 23 0t23 0 23 0 23 0" fill="none" stroke="#F0D9A4" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"></path>'
         '<path class="w2" pathLength="1" d="M30 111q7.5-5 15 0t15 0 15 0 15 0" fill="none" stroke="#F0D9A4" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" opacity=".6"></path></svg>')
    if camel:  # dans le composant, les attributs SVG s'écrivent en sc-camel-*
        s = s.replace('viewBox=', 'sc-camel-view-box=').replace('pathLength=', 'sc-camel-path-length=')
    return s

LDR = ('<div class="ccie-ldr" aria-hidden="true"><div class="ccie-l1">' + logo() +
       '<div class="ccie-bar"><i></i></div><p class="ccie-cap">Chargement</p></div></div>')
# intro de la page (gérée par la logique du composant) : même scène, à la place de l'arche
INTRO = ('<div class="ccie-ldr ccie-intro" style="opacity:{{loaderOpacity}}"><div class="ccie-l1">' + logo(True) +
         '<div class="ccie-bar"><i></i></div><p class="ccie-cap">Chargement</p></div></div>')

LDR_CSS = r"""
.ccie-ldr{position:fixed;inset:0;z-index:2147483000;display:flex;align-items:center;justify-content:center;pointer-events:none;background:radial-gradient(420px 260px at 50% 45%,rgba(40,62,110,.35),transparent 70%),#0B0F1A;transition:opacity .4s ease,visibility .4s ease}
.ccie-ldr.out{opacity:0;visibility:hidden}
.ccie-intro{transition:opacity .4s ease}
.ccie-l1{display:flex;flex-direction:column;align-items:center;gap:22px}
.ccie-l1 .mk .cr{transform-box:fill-box;transform-origin:center}
.ccie-l1 .s1,.ccie-l1 .s2,.ccie-l1 .w1,.ccie-l1 .w2{stroke-dasharray:1;stroke-dashoffset:1;animation:ccl1d 3.6s cubic-bezier(.6,0,.2,1) infinite}
.ccie-l1 .s2{animation-name:ccl1d2}.ccie-l1 .w1{animation-name:ccl1d3}.ccie-l1 .w2{animation-name:ccl1d4}
@keyframes ccl1d2{0%,8%{stroke-dashoffset:1;opacity:1}46%,88%{stroke-dashoffset:0;opacity:1}100%{stroke-dashoffset:0;opacity:0}}
@keyframes ccl1d4{0%,28%{stroke-dashoffset:1;opacity:1}62%,88%{stroke-dashoffset:0;opacity:1}100%{stroke-dashoffset:0;opacity:0}}
@keyframes ccl1d{0%{stroke-dashoffset:1;opacity:1}40%,88%{stroke-dashoffset:0;opacity:1}100%{stroke-dashoffset:0;opacity:0}}
@keyframes ccl1d3{0%,20%{stroke-dashoffset:1;opacity:1}55%,88%{stroke-dashoffset:0;opacity:1}100%{stroke-dashoffset:0;opacity:0}}
.ccie-l1 .cr{animation:ccl1p 3.6s infinite}
@keyframes ccl1p{0%,42%{opacity:0;transform:scale(.3) rotate(-70deg)}56%{opacity:1;transform:scale(1.18)}64%,88%{opacity:1;transform:none}100%{opacity:0}}
.ccie-l1 .mk{animation:ccl1g 3.6s infinite}
@keyframes ccl1g{0%,60%{filter:none}72%{filter:drop-shadow(0 0 14px rgba(240,217,164,.75))}88%{filter:none}}
.ccie-bar{width:150px;height:2px;border-radius:2px;background:rgba(217,180,108,.18);overflow:hidden}
.ccie-bar i{display:block;height:100%;width:0;background:linear-gradient(90deg,#A9843F,#F6E2B0);animation:ccl1b 3.6s cubic-bezier(.4,0,.2,1) infinite}
@keyframes ccl1b{0%{width:0;opacity:1}80%{width:100%;opacity:1}100%{width:100%;opacity:0}}
.ccie-cap{margin:0;font:400 11px/1.6 'Jost',system-ui,sans-serif;letter-spacing:.34em;text-transform:uppercase;color:#8E94A3}
@media (prefers-reduced-motion: reduce){.ccie-ldr{display:none !important}}
"""
# enveloppe : apparaît après 0,3 s seulement ; masque les messages techniques du chargeur
SHELL_CSS = ('<style ' + SHELL_MARK + '>' + LDR_CSS +
             '#__bundler_placeholder,#__bundler_loading{display:none !important}'
             '.ccie-ldr{opacity:0;animation:cclin .3s ease .3s forwards}@keyframes cclin{to{opacity:1}}</style>')
SHELL_JS = '<script>window.__ccieLdr0 = Date.now();</script>'

QV_CSS = r"""
.mkc :is(.s1,.s2,.cr,.w1,.w2){transform-box:fill-box;transform-origin:center}
.ccq-a .mkc :is(.w1,.w2){stroke-dasharray:1;animation:ccq3w_a .6s cubic-bezier(.6,0,.2,1) both}
.ccq-a .mkc .w2{animation-delay:.12s}
.ccq-a .mkc :is(.s1,.s2,.cr){animation:ccq3u_a .6s .25s cubic-bezier(.2,1.3,.4,1) both}
.ccq-a .lg-t1{display:inline-block;animation:ccq3l_a .55s .4s cubic-bezier(.2,1,.3,1) both}
.ccq-a :is(.lg-t2,.logo-sub){animation:ccqs_a .6s .8s ease both}
.ccq-b .mkc :is(.w1,.w2){stroke-dasharray:1;animation:ccq3w_b .6s cubic-bezier(.6,0,.2,1) both}
.ccq-b .mkc .w2{animation-delay:.12s}
.ccq-b .mkc :is(.s1,.s2,.cr){animation:ccq3u_b .6s .25s cubic-bezier(.2,1.3,.4,1) both}
.ccq-b .lg-t1{display:inline-block;animation:ccq3l_b .55s .4s cubic-bezier(.2,1,.3,1) both}
.ccq-b :is(.lg-t2,.logo-sub){animation:ccqs_b .6s .8s ease both}
@keyframes ccq3w_a{from{stroke-dashoffset:1}to{stroke-dashoffset:0}}
@keyframes ccq3w_b{from{stroke-dashoffset:1}to{stroke-dashoffset:0}}
@keyframes ccq3u_a{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:none}}
@keyframes ccq3u_b{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:none}}
@keyframes ccq3l_a{from{opacity:0;transform:translateX(-22px)}to{opacity:1;transform:none}}
@keyframes ccq3l_b{from{opacity:0;transform:translateX(-22px)}to{opacity:1;transform:none}}
@keyframes ccqs_a{from{opacity:0;letter-spacing:.5em}to{opacity:1}}
@keyframes ccqs_b{from{opacity:0;letter-spacing:.5em}to{opacity:1}}
@media (prefers-reduced-motion: reduce){:is(.ccq-a,.ccq-b) *{animation:none !important}}
"""
# Vague à l'ouverture (après le chargement s'il est affiché) et au survol du logo de l'en-tête
TPL_JS = r"""<script id="ccie-anim-js">(function () {
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  function brands() {
    var out = [];
    document.querySelectorAll('header svg.mkc').forEach(function (s) { var a = s.closest('a'); if (a && out.indexOf(a) < 0) out.push(a); });
    return out;
  }
  function play(a) {
    if (reduce) return;
    var next = a.classList.contains('ccq-a') ? 'ccq-b' : 'ccq-a';
    a.classList.remove('ccq-a', 'ccq-b'); a.classList.add(next);
  }
  var tries = 0;
  (function ready() {
    var b = brands();
    var intro = document.querySelector('.ccie-intro');
    if ((!b.length || intro) && tries++ < 600) { return requestAnimationFrame(ready); }
    b.forEach(play);
  })();
  document.addEventListener('mouseover', function (e) {
    var a = e.target && e.target.closest && e.target.closest('header a');
    if (!a || !a.querySelector('svg.mkc') || (e.relatedTarget && a.contains(e.relatedTarget))) return;
    play(a);
  });
})();</script>"""

args = sys.argv[2:]
loader = '--loader' in args
for p in map(pathlib.Path, [a for a in args if a != '--loader']):
    t = p.read_text(encoding='utf-8')
    i, j, tpl = split(t)
    if MARK in tpl:
        print('déjà porté', p.name); continue
    k = tpl.rindex('</head>')
    tpl = tpl[:k] + MARK + QV_CSS + (LDR_CSS if loader else '') + '</style>' + tpl[k:]
    if loader and 'class="door door-l"' in tpl:
        s = tpl.index('<div class="door door-l"')
        e = tpl.index('</div>', tpl.index('<div class="ld-center"'))
        # fin du bloc ld-center : dernier </div> avant </sc-if>
        e = tpl.index('</sc-if>', s); e = tpl.rindex('</div>', s, e)  # ferme le conteneur role=status
        e = tpl.rindex('</div>', s, e) + 6                              # ferme ld-center
        tpl = tpl[:s] + INTRO + tpl[e:]
    e = tpl.rindex('</body>')
    tpl = tpl[:e] + TPL_JS + tpl[e:]
    t = join(t, i, j, tpl)
    if loader and SHELL_MARK not in t[:t.index('<script type="__bundler/template">')]:
        h = t.index('</head>')
        t = t[:h] + SHELL_CSS + t[h:]
        b = t.index('<body>') + len('<body>')
        t = t[:b] + SHELL_JS + LDR + t[b:]
    p.write_text(t, encoding='utf-8')
    print('porté', p.name, '+chargement' if loader else '')
