"""Branche les heures de prière du site public sur la base (étapes H4, H5 et H6).

Source unique : le tableau du mois (table prayer_times, API publique GET /api/prayer-times),
avec repli sur les heures de la carte « Prochaine prière » de l'Accueil quand une case est vide.

Toutes les pages publiques (*.dc.html hors SA-*, et index.html) - étape H5 :
- barre du haut « Prochaine prière », menu mobile « Aujourd'hui », pied de page, et sur l'accueil
  la carte « Prochaine prière » (heure, compte à rebours, progression, puces) : heures du jour
  tirées de la base, sur toutes les heures remplies (Fajr, Dohr ou Jumu'a, Asr, Maghreb, Icha).

Pages Horaires.dc.html, M-Horaires.dc.html, T-Horaires.dc.html - étape H4 :
1. Logique de la page : les heures du jour (barre du haut « Prochaine prière », tableau
   « Aujourd'hui », compte à rebours, menu mobile, pied de page) viennent de la base.
   Le script #ascil-prayer-live charge les données, les range dans window.__ascilPrayer et
   prévient la page (événement « ascil:prayer »), qui se redessine.
2. Tableau « Mois complet » : mois courant (fuseau America/Moncton) lu dans la base,
   « AUJOURD'HUI » sur le vrai jour, vendredis mis en évidence avec l'heure de Jumu'a,
   colonnes Suhoor / Iftar pendant le Ramadan (si activées). Bouton PDF retiré.
3. Réglages « horaires » (Superadmin → Horaires) : bloc Aujourd'hui (affichage, compte à
   rebours, date hégirienne, liens Rappel et Khutba), filtre Vendredis, carte du vendredi
   (affichage, heure du prochain vendredi, minutes d'avance, conseil de stationnement),
   Ramadan (dates du « Mode du site », Suhoor, Iftar, Tarawih), Aïd (dates, heures, lieu,
   itinéraire), Qibla (degrés, repère).

Pages N2-Khutba (et M-/T-) - étape H6 : vendredis à venir (clé khutba : langue, traduction,
imam, nombre affiché, mode de traduction) et heure de Jumu'a du tableau du mois.
Pages N3-Rappel (et M-/T-) - étape H6 : prières et délais proposés (clé rappel), heures du jour
tirées de la base, vraies notifications du navigateur (page ouverte), choix mémorisés sur
l'appareil du visiteur, fichier calendrier .ics des rappels du mois (page fermée).

Idempotent : la logique et le balisage ne sont modifiés qu'une fois (repère ascil-prayer),
le script #ascil-prayer-live est remplacé à chaque passage.
"""
import json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
OPEN = '<script type="__bundler/template">'
MARK = '/*ascil-prayer*/'
HORAIRES = {'Horaires.dc.html', 'M-Horaires.dc.html', 'T-Horaires.dc.html'}


def public_pages():
    return sorted(p.name for p in ROOT.glob('*.dc.html') if not p.name.startswith(('SA-', 'TH-'))) + ['index.html']


def load(path):
    s = path.read_text(encoding='utf-8')
    i = s.index(OPEN) + len(OPEN)
    j = s.index('</script>', i)
    return s, i, j, json.loads(s[i:j])


def save(path, s, i, j, tpl):
    enc = json.dumps(tpl).replace('</', '<\\u002F')
    assert json.loads(enc) == tpl
    path.write_text(s[:i] + enc + s[j:], encoding='utf-8')


def rep(tpl, old, new, count=1):
    n = tpl.count(old)
    assert n == count, f'{n} occurrence(s) au lieu de {count} : {old[:80]!r}'
    return tpl.replace(old, new)


def resub(tpl, pattern, repl, flags=re.S):
    out, n = re.subn(pattern, repl, tpl, count=1, flags=flags)
    assert n == 1, f'motif introuvable : {pattern[:80]!r}'
    return out


# ---------------------------------------------------------------------------
# 1. Logique de la page (classe Component)
# ---------------------------------------------------------------------------

HOR_VALS = r'''  /*ascil-prayer*/
  horVals(PT, k) {
    const HS = PT.horaires || {};
    const g = (sec, key, d) => (HS[sec] && HS[sec][key] !== undefined && HS[sec][key] !== null ? HS[sec][key] : d);
    const today = PT.date || '';
    const days = Array.isArray(PT.days) ? PT.days : [];
    const defs = PT.defaults || {};
    const fmtDay = (iso) => { try { return new Intl.DateTimeFormat('fr-CA', { timeZone: 'UTC', weekday: 'long', day: 'numeric', month: 'long' }).format(new Date(iso + 'T12:00:00Z')); } catch (e) { return iso; } };
    let friTime = k.tJ;
    if (!k.isFri && today) {
      const f = days.find((d) => d.date > today && new Date(d.date + 'T12:00:00Z').getUTCDay() === 5);
      if (f) friTime = f.jumuha || defs.jumuha || k.tJ;
    }
    const avance = Number(g('vendredi', 'avance', 15)) || 0;
    const conseil = g('vendredi', 'conseil', true) !== false;
    let friNote = 'Khutba suivie de la prière.';
    if (avance > 0) friNote += ' Conseil : arrivez ' + avance + ' minutes à l\u2019avance' + (conseil ? ', le stationnement étant limité dans la rue.' : '.');
    else if (conseil) friNote += ' Le stationnement est limité dans la rue.';
    const S = PT.season || {};
    const hasRam = S.mode === 'ramadan' && !!S.from && !!S.to;
    const inRam = hasRam && !!today && today >= S.from && today <= S.to;
    let ramIntro = 'Les horaires du Ramadan seront publiés ici dès l\u2019annonce officielle.';
    if (hasRam) ramIntro = today && today > S.to ? 'Le Ramadan s\u2019est terminé le ' + fmtDay(S.to) + '.' : 'Du ' + fmtDay(S.from) + ' au ' + fmtDay(S.to) + '.';
    const rp = [];
    if (inRam && g('ramadan', 'suhoor', true)) rp.push('Suhoor jusqu\u2019à ' + k.tF);
    if (inRam && g('ramadan', 'iftar', true) && k.tM) rp.push('Iftar à ' + k.tM);
    const ramToday = rp.length ? 'Aujourd\u2019hui : ' + rp.join(' · ') + '.' : '';
    const tarH = g('ramadan', 'tarawih', false) ? g('ramadan', 'tarawihHeure', '') : '';
    const ramTar = hasRam && !(today && today > S.to) && tarH ? 'Tarawih chaque soir à ' + tarH + '.' : '';
    const aidL = [];
    [['fitrDate', 'fitrHeure', 'Aïd al-Fitr'], ['adhaDate', 'adhaHeure', 'Aïd al-Adha']].forEach((a) => {
      const dd = g('aid', a[0], ''), hh = g('aid', a[1], '');
      if (dd && (!today || dd >= today)) aidL.push(a[2] + ' : ' + fmtDay(dd) + (hh ? ' à ' + hh : '') + '.');
    });
    const aidHref = String(g('aid', 'itineraire', 'https://maps.google.com/?q=15+rue+Frontenac+Edmundston') || '');
    const qDeg = String(g('qibla', 'degres', '61,6') || '61,6');
    const qNum = parseFloat(qDeg.replace(',', '.'));
    const qRepere = String(g('qibla', 'repere', '') || '');
    const MOIS = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'];
    const ym = PT.month || today.slice(0, 7);
    const mName = ym ? MOIS[parseInt(ym.slice(5, 7), 10) - 1] + ' ' + ym.slice(0, 4) : '';
    const showRam = g('ramadan', 'on', true) !== false, showAid = g('aid', 'on', true) !== false, showQibla = g('qibla', 'on', true) !== false;
    const showRappel = g('aujourdhui', 'lienRappel', true) !== false, showKhutba = g('aujourdhui', 'lienKhutba', true) !== false;
    return {
      showAuj: g('aujourdhui', 'on', true) !== false, showCompte: g('aujourdhui', 'compte', true) !== false,
      showHijri: g('aujourdhui', 'hijri', true) !== false, showRappel, showKhutba, showLinks: showRappel || showKhutba,
      showFri: g('vendredi', 'on', true) !== false, friTime, friNote,
      showFriFilter: g('mois', 'vendredis', true) !== false,
      monthTitle: mName ? mName.charAt(0).toUpperCase() + mName.slice(1) : 'Mois complet',
      showRam, ramIntro, ramToday, hasRamToday: !!ramToday, ramTar, hasRamTar: !!ramTar,
      showAid, aidDates: aidL.length ? aidL.join(' ') : 'Date selon l\u2019annonce TCOM.',
      aidLieu: String(g('aid', 'lieu', 'Salle louée — 15 rue Frontenac') || 'Lieu communiqué prochainement'), aidHref, hasAidHref: !!aidHref,
      showQibla, qDeg, qRot: Number.isFinite(qNum) ? qNum : 61.6, qRepere, hasQRepere: !!qRepere,
      showSand: showRam || showAid || showQibla,
    };
  }

  renderVals() {'''

LOGIC = [
    ('componentDidMount() { ',
     "componentDidMount() { this.onPrayer = () => this.setState({ now: Date.now() }); "
     "try { window.addEventListener('ascil:prayer', this.onPrayer); } catch (e) {} "),
    ('componentWillUnmount() { ',
     "componentWillUnmount() { try { window.removeEventListener('ascil:prayer', this.onPrayer); } catch (e) {} "),
    ('\n  renderVals() {', '\n' + HOR_VALS),
    (r"""    const known = [{ n: 'Fajr', t: 390 }].concat(isFri ? [{ n: 'Jumu\u2019a', t: 750 }] : []).concat([{ n: 'Icha', t: 1140 }]);
    let next = known.find((x) => x.t > mins); let tomorrow = false;
    if (!next) { next = { n: 'Fajr', t: 390 }; tomorrow = true; }""",
     r"""    const PT = (typeof window !== 'undefined' && window.__ascilPrayer) || {};
    const PD = PT.today || {};
    const pt = (k, d) => (typeof PD[k] === 'string' && /^\d\d:\d\d$/.test(PD[k]) ? PD[k] : d);
    const toM = (s) => parseInt(s.slice(0, 2), 10) * 60 + parseInt(s.slice(3), 10);
    const tF = pt('fajr', '06:30'), tL = pt('lever', ''), tD = pt('dohr', ''), tA = pt('asr', ''), tM = pt('maghreb', ''), tI = pt('isha', '19:00'), tJ = pt('jumuha', '12:30');
    const known = [['Fajr', tF], isFri ? ['Jumu\u2019a', tJ] : ['Dohr', tD], ['Asr', tA], ['Maghreb', tM], ['Icha', tI]].filter((x) => x[1]).map((x) => ({ n: x[0], t: toM(x[1]) })).sort((a, b) => a.t - b.t);
    let next = known.find((x) => x.t > mins); let tomorrow = false;
    if (!next) { next = known[0]; tomorrow = true; }"""),
    (r"""      mk('Fajr', 'Fajr', 'الفجر', '06:30'),
      mk('Lever', 'Lever du soleil', 'الشروق', ''),
      isFri ? mk('Jumu\u2019a', 'Jumu\u2019a', 'الجمعة', '12:30') : mk('Dohr', 'Dohr', 'الظهر', ''),
      mk('Asr', 'Asr', 'العصر', ''),
      mk('Maghreb', 'Maghreb', 'المغرب', ''),
      mk('Icha', 'Icha', 'العشاء', '19:00'),""",
     r"""      mk('Fajr', 'Fajr', 'الفجر', tF),
      mk('Lever', 'Lever du soleil', 'الشروق', tL),
      isFri ? mk('Jumu\u2019a', 'Jumu\u2019a', 'الجمعة', tJ) : mk('Dohr', 'Dohr', 'الظهر', tD),
      mk('Asr', 'Asr', 'العصر', tA),
      mk('Maghreb', 'Maghreb', 'المغرب', tM),
      mk('Icha', 'Icha', 'العشاء', tI),"""),
    ("const prevK = known.filter((x) => x.t <= mins).pop() || { n: 'Icha', t: 1140 - 1440 };",
     "const prevK = known.filter((x) => x.t <= mins).pop() || { n: known[known.length - 1].n, t: known[known.length - 1].t - 1440 };"),
    ("dohrTime: '12:30',",
     "dohrTime: tJ, fajrTime: tF, jumuaTime: tJ, ichaTime: tI, ...this.horVals(PT, { tF, tM, tJ, isFri }),"),
]


def patch_logic(tpl):
    a = tpl.index('<script type="text/x-dc"')
    b = tpl.index('</script>', a)
    code = tpl[a:b]
    if MARK in code:
        return tpl
    for old, new in LOGIC:
        code = rep(code, old, new)
    return tpl[:a] + code + tpl[b:]


# ---------------------------------------------------------------------------
# 2. Balisage de la page Horaires
# ---------------------------------------------------------------------------

def sc_if(name, inner, default='true'):
    return f'<sc-if value="{{{{{name}}}}}" hint-placeholder-val="{{{{ {default} }}}}">{inner}</sc-if>'


MONTH_PLACEHOLDER = ('<div id="ascil-month"><p class="muted" style="margin:0;padding:18px 16px">'
                     'Chargement des horaires du mois…</p></div>')


MENU_FAJR = '<div style="font-size:13px">Fajr</div><div style="font-size:22px;font-weight:700;color:#fff">06:30</div>'


def patch_common(tpl):
    """Menu mobile et pied de page : heures du jour (toutes les pages)."""
    if MENU_FAJR not in tpl and '{{fajrTime}}' in tpl:
        return tpl
    tpl = rep(tpl, '<div style="font-size:13px">Fajr</div><div style="font-size:22px;font-weight:700;color:#fff">06:30</div>',
              '<div style="font-size:13px">Fajr</div><div style="font-size:22px;font-weight:700;color:#fff">{{fajrTime}}</div>')
    tpl = rep(tpl, '<div style="font-size:13px">Icha</div><div style="font-size:22px;font-weight:700;color:#fff">19:00</div>',
              '<div style="font-size:13px">Icha</div><div style="font-size:22px;font-weight:700;color:#fff">{{ichaTime}}</div>')
    tpl = rep(tpl, 'Fajr 06:30 — Jumu’a 12:30 — Icha 19:00', 'Fajr {{fajrTime}} — Jumu’a {{jumuaTime}} — Icha {{ichaTime}}')
    return tpl


def patch_markup(tpl):
    """Page Horaires : bloc Aujourd'hui, vendredi, mois complet, Ramadan, Aïd, Qibla."""
    if 'id="ascil-month"' in tpl:
        return tpl

    # Bloc « Aujourd'hui » : date hégirienne, compte à rebours, liens, affichage du bloc.
    h = '<p class="muted" style="margin:4px 0 0">{{hijri}}</p>'
    tpl = rep(tpl, h, sc_if('showHijri', h))
    tpl = resub(tpl, r'(<p class="tnum" style="margin:0;display:inline-flex[^"]*">(?:(?!</p>).)*?\{\{nextName\}\} \{\{countdown\}\}</p>)',
                lambda m: sc_if('showCompte', m.group(1)))
    tpl = resub(tpl, r'(<a class="btn btn-ghost" href="(?:[MT]-)?N3-Rappel\.dc\.html"(?:(?!</a>).)*</a>)', lambda m: sc_if('showRappel', m.group(1)))
    tpl = resub(tpl, r'(<a class="btn btn-ghost" href="(?:[MT]-)?N2-Khutba\.dc\.html"(?:(?!</a>).)*</a>)', lambda m: sc_if('showKhutba', m.group(1)))
    tpl = resub(tpl, r'(<div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:16px"><sc-if value="\{\{showRappel\}\}".*?</sc-if></div>)',
                lambda m: sc_if('showLinks', m.group(1)))
    a = tpl.index('<div class="split" style="align-items:start">') + len('<div class="split" style="align-items:start">')
    b = tpl.index('\n   <div style="display:flex;flex-direction:column;gap:20px">', a)
    left = tpl[a:b]
    assert left.lstrip().startswith('<div>') and left.rstrip().endswith('</div>'), 'colonne Aujourd’hui inattendue'
    tpl = tpl[:a] + sc_if('showAuj', left) + tpl[b:]

    # Carte du vendredi : heure du prochain vendredi, conseil, affichage.
    fri_time = '<p class="tnum" style="margin:8px 0 0;font-size:56px;font-weight:700;color:#C49A4A;line-height:1">12:30</p>'
    tpl = rep(tpl, fri_time, fri_time.replace('>12:30<', '>{{friTime}}<'))
    tpl = resub(tpl, r'<p style="margin:12px 0 0;color:#F3EAD8">Khutba suivie[^<]*</p>',
                lambda m: '<p style="margin:12px 0 0;color:#F3EAD8">{{friNote}}</p>')
    tpl = resub(tpl, r'(<div style="background:#0E4D3C;color:#fff;border-radius:22px;padding:30px">.*?\{\{friNote\}\}</p>\s*</div>)',
                lambda m: sc_if('showFri', m.group(1)))

    # Mois complet : titre, filtre Vendredis, PDF retiré, tableau rendu depuis la base.
    tpl = rep(tpl, '<h2 id="mois-t" class="h2" style="margin-top:8px">Novembre 2026</h2>',
              '<h2 id="mois-t" class="h2" style="margin-top:8px">{{monthTitle}}</h2>')
    tpl = resub(tpl, r'(<div class="seg" role="group" aria-label="Affichage">.*?</div>)', lambda m: sc_if('showFriFilter', m.group(1)))
    tpl = resub(tpl, r'<a class="btn btn-ghost" href="#">(?:(?!</a>).)*Télécharger le mois en PDF</a>', lambda m: '')
    a = tpl.index('aria-labelledby="mois-t"')
    tpl = tpl[:a] + resub(tpl[a:], r'<sc-raw-table class="t tnum" style="min-width:680px">.*?</sc-raw-table>',
                          lambda m: MONTH_PLACEHOLDER)

    # Ramadan, Aïd, Qibla.
    tpl = resub(tpl, r'(<div class="card">\s*<span style="color:#0E4D3C">(?:(?!</span>).)*</span>\s*<p class="h3" style="margin-top:14px">Ramadan</p>)\s*'
                     r'<p class="muted" style="margin:8px 0 0">Les horaires du Ramadan[^<]*</p>\s*</div>',
                lambda m: sc_if('showRam', m.group(1)
                                + '<p class="muted" style="margin:8px 0 0">{{ramIntro}}</p>'
                                + sc_if('hasRamToday', '<p style="margin:8px 0 0;font-weight:600;color:#0E4D3C">{{ramToday}}</p>', 'false')
                                + sc_if('hasRamTar', '<p style="margin:6px 0 0">{{ramTar}}</p>', 'false')
                                + '</div>'))
    tpl = resub(tpl, r'(<div class="card">\s*<span style="color:#0E4D3C">(?:(?!</span>).)*</span>\s*<p class="h3" style="margin-top:14px">Prières de l’Aïd</p>)\s*'
                     r'<p class="muted" style="margin:8px 0 0">Date selon l’annonce TCOM\. Lieu :</p>\s*'
                     r'<p style="margin:6px 0 0;font-size:20px;font-weight:700;color:#0E4D3C">15 rue Frontenac</p>\s*'
                     r'<p class="muted" style="margin:2px 0 0;font-size:15px">[^<]*</p>\s*'
                     r'<a class="btn btn-ghost" href="https://maps\.google\.com/\?q=15\+rue\+Frontenac\+Edmundston"( style="margin-top:16px">(?:(?!</a>).)*</a>)\s*</div>',
                lambda m: sc_if('showAid', m.group(1)
                                + '<p class="muted" style="margin:8px 0 0">{{aidDates}} Lieu :</p>'
                                + '<p style="margin:6px 0 0;font-size:20px;font-weight:700;color:#0E4D3C;overflow-wrap:anywhere">{{aidLieu}}</p>'
                                + sc_if('hasAidHref', '<a class="btn btn-ghost" href="{{aidHref}}"' + m.group(2), 'true')
                                + '</div>'))
    tpl = resub(tpl, r'(<div class="card" style="display:flex;flex-direction:column">\s*<p class="h3">Qibla</p>.*?</svg>\s*<p style="margin:0">.*?</p>\s*</div>\s*</div>)',
                lambda m: sc_if('showQibla', m.group(1)))
    tpl = rep(tpl, 'aria-label="Boussole : la Qibla à 61,6 degrés du nord vrai"', 'aria-label="Boussole : la Qibla à {{qDeg}} degrés du nord vrai"')
    tpl = rep(tpl, '<g class="needle">', '<g transform="rotate({{qRot}} 60 60)"><g class="needle">')
    tpl = resub(tpl, r'(<g transform="rotate\(\{\{qRot\}\} 60 60\)"><g class="needle">.*?</g>)', lambda m: m.group(1) + '</g>')
    tpl = rep(tpl, '<strong>61,6°</strong> depuis le nord vrai ; la Kaaba est à <strong>9 619 km</strong>.</p>',
              '<strong>{{qDeg}}°</strong> depuis le nord vrai ; la Kaaba est à <strong>9 619 km</strong>.</p>'
              + sc_if('hasQRepere', '<p class="muted" style="margin:0;font-size:15px">Sur place : {{qRepere}}</p>', 'false'))
    # Aiguille : l'animation part de -90° et s'arrête sur 0°, le groupe parent porte l'angle réel.
    tpl = rep(tpl, '@keyframes needle{from{transform:rotate(-30deg)}to{transform:rotate(61.6deg)}}',
              '@keyframes needle{from{transform:rotate(-90deg)}to{transform:rotate(0deg)}}')
    tpl = rep(tpl, '.needle{transform:rotate(61.6deg) !important}', '.needle{transform:rotate(0deg) !important}')
    tpl = resub(tpl, r'(<section class="sand" style="border-top:1px solid #E4D9C0">\s*<div class="wrap sec g3">.*?</section>)',
                lambda m: sc_if('showSand', m.group(1)))
    return tpl


# ---------------------------------------------------------------------------
# 3. Chargement des données et tableau du mois
# ---------------------------------------------------------------------------

LIVE_SCRIPT = r'''<script id="ascil-prayer-live">
(function () {
  var P = window.__ascilPrayer = window.__ascilPrayer || {};
  var page = (location.pathname.split('/').pop() || '').replace(/^(M-|T-)/, '').replace(/\.dc(\.html)?$/, '');
  var isHoraires = page === 'Horaires';
  var EXTRA = { 'Horaires': ['horaires', 'season'], 'N2-Khutba': ['khutba'], 'N3-Rappel': ['rappel'],
    'APropos': ['apropos', 'campagne'], 'N3-Campagne': ['campagne'],
    'Services': ['services', 'horaires'], 'N2-Cours': ['cours'], 'N2-Mariages': ['mariages'],
    'N2-Funerailles': ['funerailles'], 'N2-AideAlimentaire': ['aide'], 'N2-EspaceFemmes': ['femmes'],
    'Dons': ['dons', 'merci', 'campagne', 'services'], 'Evenements': ['evenements'],
    'N3-Calendrier': ['calendrier', 'evenements', 'cours'], 'Ressources': ['ressources'], 'N3-Dua': ['dua'], 'Contact': ['contact', 'home'] }[page] || [];
  var URLS = { campagne: '/api/campagne', dua: '/api/dua' };
  function getJ(u) {
    return fetch(u, { cache: 'no-store' }).then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; });
  }
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; });
  }
  var DAYS = ['dim.', 'lun.', 'mar.', 'mer.', 'jeu.', 'ven.', 'sam.'];
  var MONTHS = ['janv.', 'févr.', 'mars', 'avr.', 'mai', 'juin', 'juill.', 'août', 'sept.', 'oct.', 'nov.', 'déc.'];
  var MONTHS_LONG = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'];
  function cell(v, muted) {
    return v ? '<td>' + esc(v) + '</td>' : '<td class="muted">—</td>';
  }
  function monthHtml() {
    if (P.failed || !P.days || !P.days.length) {
      return '<p class="muted" style="margin:0;padding:18px 16px">Les horaires du mois sont momentanément indisponibles. ' +
        'Réessayez dans quelques minutes, ou consultez l’affiche à la mosquée.</p>';
    }
    var D = P.defaults || {}, H = P.horaires || {}, S = P.season || {}, R = H.ramadan || {};
    var hasRam = R.on !== false && S.mode === 'ramadan' && S.from && S.to;
    var first = P.days[0].date, last = P.days[P.days.length - 1].date;
    var ramCols = hasRam && S.from <= last && S.to >= first;
    var suhoor = ramCols && R.suhoor !== false, iftar = ramCols && R.iftar !== false;
    var ym = P.month || first.slice(0, 7);
    var title = MONTHS_LONG[parseInt(ym.slice(5, 7), 10) - 1] + ' ' + ym.slice(0, 4);
    var h = ['<table class="t tnum" style="min-width:680px"><caption style="position:absolute;left:-9999px">Horaires de ' + esc(title) + '</caption>',
      '<thead style="position:sticky;top:0"><tr><th scope="col">Jour</th><th scope="col">Fajr</th><th scope="col">Lever</th>',
      '<th scope="col">Dohr</th><th scope="col">Asr</th><th scope="col">Maghreb</th><th scope="col">Icha</th>',
      suhoor ? '<th scope="col">Suhoor (fin)</th>' : '', iftar ? '<th scope="col">Iftar</th>' : '', '</tr></thead><tbody>'];
    P.days.forEach(function (d) {
      var dt = new Date(d.date + 'T12:00:00Z'), wd = dt.getUTCDay();
      var isFri = wd === 5, isToday = d.date === P.date;
      var label = DAYS[wd] + ' ' + dt.getUTCDate() + ' ' + MONTHS[dt.getUTCMonth()];
      var fajr = d.fajr || D.fajr || '', isha = d.isha || D.isha || D.icha || '', maghreb = d.maghreb || D.maghreb || '';
      var bg = isToday ? '#F6E7C4' : (isFri ? '#F7F2E4' : '#fff');
      var row = '<tr class="' + (isFri ? '' : 'nf') + '" style="background:' + bg + '"' + (isToday ? ' aria-current="date"' : '') + '>';
      row += '<td style="white-space:nowrap;font-weight:' + (isFri || isToday ? 700 : 400) + '">' + esc(label) +
        (isToday ? ' <span class="pill" style="background:#C49A4A;color:#1E2B26;padding:2px 8px;font-size:11px">AUJOURD’HUI</span>' : '') + '</td>';
      row += cell(fajr) + cell(d.lever || D.lever);
      if (isFri) {
        var j = d.jumuha || D.jumuha || D.jumua || '';
        row += j ? '<td><strong>' + esc(j) + '</strong> <span style="font-size:12px;font-weight:700;color:#7A5A1E">JUMU’A</span></td>' : cell(d.dohr || D.dohr);
      } else {
        row += cell(d.dohr || D.dohr);
      }
      row += cell(d.asr || D.asr) + cell(maghreb) + cell(isha);
      var inRam = ramCols && d.date >= S.from && d.date <= S.to;
      if (suhoor) row += inRam ? cell(fajr) : '<td class="muted">—</td>';
      if (iftar) row += inRam ? cell(maghreb) : '<td class="muted">—</td>';
      h.push(row + '</tr>');
    });
    h.push('</tbody></table>');
    return h.join('');
  }
  var html = null;
  function renderMonth() {
    if (!isHoraires || html === null) return;
    var el = document.getElementById('ascil-month');
    if (!el || el.getAttribute('data-done') === '1') return;
    el.innerHTML = html;
    el.setAttribute('data-done', '1');
  }
  Promise.all([getJ('/api/prayer-times')].concat(EXTRA.map(function (k) { return getJ(URLS[k] || '/api/settings/' + k); }))).then(function (r) {
    var pt = r[0];
    if (pt && pt.ok) {
      P.today = pt.today || pt.day;
      P.date = (P.today && P.today.date) || pt.date;
      P.month = pt.month;
      // Heures retenues de chaque jour (tableau, sinon défauts de l'Accueil, sinon calcul pour Lever, Dohr, Asr, Maghreb).
      P.days = (Array.isArray(pt.resolved) && pt.resolved.length ? pt.resolved : pt.days) || [];
      P.defaults = pt.defaults || {};
    } else {
      P.failed = true;
    }
    EXTRA.forEach(function (k, i) { if (r[i + 1] && r[i + 1].ok) P[k] = URLS[k] ? r[i + 1] : r[i + 1].settings; });
    try { window.dispatchEvent(new Event('ascil:prayer')); } catch (e) {}
    // Campagne en direct : montants relus chaque minute.
    if (page === 'N3-Campagne') {
      setInterval(function () {
        getJ('/api/campagne').then(function (c) {
          if (c && c.ok) { P.campagne = c; try { window.dispatchEvent(new Event('ascil:prayer')); } catch (e) {} }
        });
      }, 60000);
    }
    if (isHoraires) {
      html = monthHtml();
      renderMonth();
      new MutationObserver(renderMonth).observe(document.documentElement, { childList: true, subtree: true });
    }
  });
})();
</script>
'''


# ---------------------------------------------------------------------------
# 4. Pages « Langue de la khutba » et « Rappel de prière » (étape H6)
# ---------------------------------------------------------------------------

KHUTBA = {'N2-Khutba.dc.html', 'M-N2-Khutba.dc.html', 'T-N2-Khutba.dc.html'}
RAPPEL = {'N3-Rappel.dc.html', 'M-N3-Rappel.dc.html', 'T-N3-Rappel.dc.html'}

KHUTBA_XVALS = r"""
  xvals() {
    /*ascil-khutba*/
    const PT = (typeof window !== 'undefined' && window.__ascilPrayer) || {};
    const KS = PT.khutba || null, st = this.state;
    let today = PT.date || '';
    if (!today) { try { today = new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Moncton', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date()); } catch (e) {} }
    const fd = (iso) => { try { return new Intl.DateTimeFormat('fr-CA', { timeZone: 'UTC', weekday: 'long', day: 'numeric', month: 'long' }).format(new Date(iso + 'T12:00:00Z')); } catch (e) { return iso; } };
    const list = KS ? (KS.vendredis || []).filter((v) => v.on && v.date >= today).slice(0, KS.nombre || 4) : [];
    const kw = Math.min(st.kw || 0, Math.max(0, list.length - 1));
    const cur = list[kw] || null;
    const days = Array.isArray(PT.days) ? PT.days : [], defs = PT.defaults || {};
    const row = cur ? days.find((d) => d.date === cur.date) : null;
    const jum = (row && row.jumuha) || defs.jumuha || (PT.today && PT.today.jumuha) || '12:30';
    const add = cur && today ? Math.round((Date.parse(cur.date) - Date.parse(today)) / 864e5) : 0;
    const hasT = (v) => !!(v && v.traduction && v.traduction !== 'Aucune');
    const mode = KS && KS.mode ? KS.mode : '';
    const note = mode ? 'Traduction prévue : ' + mode.charAt(0).toLowerCase() + mode.slice(1) + '. Le programme peut changer : revenez voir cette page avant chaque vendredi.' : '';
    return {
      kwLabel: !cur ? 'Programme' : (add === 0 ? 'Aujourd\u2019hui' : (add <= 6 ? 'Ce vendredi' : (add <= 13 ? 'Vendredi prochain' : 'Dans ' + Math.round(add / 7) + ' semaines'))),
      kwDate: cur ? fd(cur.date) : (KS ? 'à venir' : 'chargement…'),
      kMain: cur ? cur.langue : (KS ? 'À venir' : '…'),
      kTrad: hasT(cur) ? cur.traduction : '', kHasTrad: hasT(cur),
      kMode: cur ? (hasT(cur) ? mode : 'Sans traduction') : (KS ? 'Le programme des prochains vendredis sera publié ici.' : ''),
      kHasCur: !!cur, kJum: jum, kImam: cur && cur.imam ? cur.imam : '', kHasImam: !!(cur && cur.imam),
      kPrev: () => this.setState({ kw: Math.max(0, kw - 1) }),
      kNext: () => this.setState({ kw: Math.min(Math.max(0, list.length - 1), kw + 1) }),
      kWeeks: list.map((v, o) => ({ date: fd(v.date), main: v.langue, trad: hasT(v) ? 'Traduction : ' + v.traduction : 'Sans traduction',
        pressed: String(o === kw), bd: o === kw ? '#C49A4A' : '#E4D9C0', pick: () => this.setState({ kw: o }) })),
      kHasWeeks: list.length > 0, kNote: note, kHasNote: !!note,
    };
  }
"""

RAPPEL_XVALS = r"""
  xvals() {
    /*ascil-rappel*/
    const st = this.state;
    const PT = (typeof window !== 'undefined' && window.__ascilPrayer) || {};
    const RS = PT.rappel || { prieres: { fajr: true, dohr: false, jumua: true, asr: false, maghreb: false, icha: true }, delais: [5, 10, 15, 30, 60], defaut: 15, titre: 'Prière dans {délai}', son: true, vibration: true };
    const PD = PT.today || {}, defs = PT.defaults || {};
    const N = typeof window !== 'undefined' ? window.Notification : null;
    const persist = (patch) => this.setState(patch, () => { try { localStorage.setItem('ascil-rappel', JSON.stringify({ rp: this.state.rp, rdl: this.state.rdl, ron: this.state.ron })); } catch (e) {} });
    if (!this.rLoaded && PT.rappel) {
      this.rLoaded = true;
      let sv = null;
      try { sv = JSON.parse(localStorage.getItem('ascil-rappel') || 'null'); } catch (e) {}
      const okD = (d) => d === 0 || RS.delais.indexOf(d) > -1;
      setTimeout(() => this.setState({
        rp: sv && sv.rp ? sv.rp : { Fajr: true, Dohr: true, 'Jumu\u2019a': true, Asr: true, Maghreb: true, Icha: true },
        rdl: sv && okD(sv.rdl) ? sv.rdl : RS.defaut,
        ron: !!(sv && sv.ron && N && N.permission === 'granted'),
      }), 0);
    }
    let secs = 0, isFri = false;
    try { const p = new Intl.DateTimeFormat('en-US', { timeZone: 'America/Moncton', weekday: 'short', hour: '2-digit', minute: '2-digit', second: '2-digit', hourCycle: 'h23' }).formatToParts(new Date(st.now2));
      const g = (t) => +((p.find((x) => x.type === t) || {}).value || 0); secs = (g('hour') % 24) * 3600 + g('minute') * 60 + g('second');
      isFri = (p.find((x) => x.type === 'weekday') || {}).value === 'Fri'; } catch (e) {}
    const okT = (v) => typeof v === 'string' && /^\d\d:\d\d$/.test(v);
    const toM = (v) => parseInt(v.slice(0, 2), 10) * 60 + parseInt(v.slice(3), 10);
    const ALL = [['Fajr', 'fajr', 'fajr'], ['Dohr', 'dohr', 'dohr'], ['Jumu\u2019a', 'jumua', 'jumuha'], ['Asr', 'asr', 'asr'], ['Maghreb', 'maghreb', 'maghreb'], ['Icha', 'icha', 'isha']];
    const offered = ALL.filter((p) => RS.prieres[p[1]]).map((p) => ({ n: p[0], col: p[2], time: okT(PD[p[2]]) ? PD[p[2]] : '' }));
    const valid = (p) => p.n === 'Jumu\u2019a' ? isFri : !(isFri && p.n === 'Dohr');
    const active = offered.filter((p) => st.rp[p.n] && p.time && valid(p));
    const list = active.map((p) => ({ n: p.n, time: p.time, at: (toM(p.time) - st.rdl) * 60 }));
    let nx = list.filter((x) => x.at > secs).sort((a, b) => a.at - b.at)[0], add = 0;
    if (!nx && list.length) { nx = list.slice().sort((a, b) => a.at - b.at)[0]; add = 86400; }
    const left = nx ? nx.at + add - secs : 0, hh = Math.floor(left / 3600), mm = Math.floor(left % 3600 / 60), ss = left % 60;
    const dLabel = (d) => d === 60 ? '1 h' : d + ' min';
    const title = (p) => st.rdl ? String(RS.titre || 'Prière dans {délai}').split('{délai}').join(dLabel(st.rdl)) : p.n + ' : c\u2019est l\u2019heure de la prière';
    if (st.ron && nx && N && N.permission === 'granted') {
      const key = nx.n + '|' + (nx.at + add) + '|' + Math.floor(st.now2 / 864e5);
      if (this.rKey !== key) {
        clearTimeout(this.rTimer); this.rKey = key;
        const target = nx, ms = left * 1000;
        if (ms > 0 && ms < 2147483647) this.rTimer = setTimeout(() => {
          const son = document.getElementById('rp-son'), vib = document.getElementById('rp-vib');
          const wantVib = RS.vibration && (!vib || vib.checked);
          try { new N(title(target), { body: target.n + ' à ' + target.time + ' · 34, 37e Avenue, Edmundston', tag: 'ascil-' + target.n, silent: !(RS.son && (!son || son.checked)) }); } catch (e) {}
          try { if (wantVib && navigator.vibrate) navigator.vibrate([200, 100, 200]); } catch (e) {}
          this.rKey = ''; this.setState({ now2: Date.now() });
        }, ms);
      }
    } else if (this.rTimer) { clearTimeout(this.rTimer); this.rTimer = null; this.rKey = ''; }
    const span = 6 * 3600;
    const perm = N ? N.permission : 'unsupported';
    const ics = () => {
      const days = (PT.days || []).filter((d) => d.date >= (PT.date || ''));
      const toUtc = (ds, hm) => { const y = +ds.slice(0, 4), mo = +ds.slice(5, 7), d = +ds.slice(8, 10), h = +hm.slice(0, 2), mi = +hm.slice(3, 5);
        const want = Date.UTC(y, mo - 1, d, h, mi); let guess = want;
        for (let k = 0; k < 2; k++) { const q = {}; new Intl.DateTimeFormat('en-US', { timeZone: 'America/Moncton', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hourCycle: 'h23' }).formatToParts(new Date(guess)).forEach((x) => { q[x.type] = x.value; });
          guess += want - Date.UTC(+q.year, +q.month - 1, +q.day, +q.hour % 24, +q.minute); }
        return new Date(guess); };
      const stamp = (dt) => dt.toISOString().replace(/[-:]/g, '').replace(/\.\d{3}/, '');
      const now = stamp(new Date()), L = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//ASCIL//Rappels de priere//FR', 'CALSCALE:GREGORIAN'];
      let n = 0;
      days.forEach((d) => {
        const fri = new Date(d.date + 'T12:00:00Z').getUTCDay() === 5;
        offered.forEach((p) => {
          if (!st.rp[p.n] || (p.n === 'Jumu\u2019a' ? !fri : (fri && p.n === 'Dohr'))) return;
          const t = d[p.col] || defs[p.col] || (p.col === 'isha' ? defs.icha : '') || '';
          if (!okT(t)) return;
          const st0 = toUtc(d.date, t);
          L.push('BEGIN:VEVENT', 'UID:' + d.date + '-' + p.col + '@ascil-mosquee', 'DTSTAMP:' + now, 'DTSTART:' + stamp(st0),
            'DTEND:' + stamp(new Date(st0.getTime() + 15 * 60000)), 'SUMMARY:' + p.n.replace('\u2019', "'") + ' - ASCIL',
            'LOCATION:34, 37e Avenue\\, Edmundston', 'BEGIN:VALARM', 'ACTION:DISPLAY', 'DESCRIPTION:' + p.n.replace('\u2019', "'"),
            'TRIGGER:-PT' + (st.rdl || 0) + 'M', 'END:VALARM', 'END:VEVENT');
          n++;
        });
      });
      L.push('END:VCALENDAR');
      if (!n) { this.setState({ rIcsMsg: 'Aucune heure à ajouter pour les prières choisies ce mois-ci.' }); return; }
      try {
        const url = URL.createObjectURL(new Blob([L.join('\r\n') + '\r\n'], { type: 'text/calendar;charset=utf-8' }));
        const a = document.createElement('a'); a.href = url; a.download = 'rappels-ascil-' + (PT.month || 'mois') + '.ics';
        document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(url), 4000);
        this.setState({ rIcsMsg: n + ' rappel' + (n > 1 ? 's' : '') + ' prêts : ouvrez le fichier téléchargé pour les ajouter à votre calendrier.' });
      } catch (e) { this.setState({ rIcsMsg: 'Le téléchargement a échoué. Réessayez.' }); }
    };
    return {
      rPrayers: offered.map((p) => ({ n: p.n, t: p.time || 'heure à venir', pressed: String(!!st.rp[p.n]), bg: st.rp[p.n] ? '#0E4D3C' : '#fff', fg: st.rp[p.n] ? '#fff' : '#0E4D3C',
        toggle: () => persist({ rp: Object.assign({}, st.rp, { [p.n]: !st.rp[p.n] }) }) })),
      rMissing: offered.some((p) => !p.time),
      rDelays: [[0, 'À l\u2019heure']].concat(RS.delais.map((d) => [d, dLabel(d) + ' avant'])).map((d) => ({ label: d[1], pressed: String(st.rdl === d[0]), pick: () => persist({ rdl: d[0] }) })),
      rSon: RS.son !== false, rVib: RS.vibration !== false,
      rOnStr: String(st.ron),
      rToggle: () => {
        if (st.ron) { persist({ ron: false }); return; }
        if (!N) { this.setState({ rErr: 'unsupported' }); return; }
        const go = (pm) => { if (pm === 'granted') { this.setState({ rErr: '' }); persist({ ron: true }); } else this.setState({ rErr: pm === 'denied' ? 'denied' : '' }); };
        try { if (N.permission === 'default') { const pr = N.requestPermission(go); if (pr && pr.then) pr.then(go); } else go(N.permission); } catch (e) { go(N.permission); }
      },
      rBtnLabel: st.ron ? 'Rappels activés — Désactiver' : 'Activer mes rappels', rBtnCls: st.ron ? 'btn-green' : 'btn-gold',
      rHead: !nx ? 'Choisissez au moins une prière' : (st.ron ? 'Prochain rappel' : 'Aperçu — rappels inactifs'),
      rCount: nx ? (hh ? hh + ':' : '') + String(mm).padStart(2, '0') + ':' + String(ss).padStart(2, '0') : '--:--',
      rRing: nx ? Math.round(Math.min(100, left / span * 100)) : 100, rNextName: nx ? nx.n + (st.rdl ? ' (−' + dLabel(st.rdl) + ')' : '') : 'la prochaine prière',
      rSummary: active.length + ' prière' + (active.length > 1 ? 's' : '') + ' · ' + (st.rdl ? dLabel(st.rdl) + ' avant' : 'à l\u2019heure'),
      rNotifTitle: nx ? title(nx) : String(RS.titre || '').split('{délai}').join(dLabel(st.rdl || 15)),
      rDenied: perm === 'denied' || st.rErr === 'denied', rUnsupported: perm === 'unsupported' || st.rErr === 'unsupported',
      rIcs: ics, rHasIcs: Array.isArray(PT.days) && PT.days.length > 0, rIcsMsg: st.rIcsMsg || '', rHasIcsMsg: !!st.rIcsMsg,
    };
  }
"""


def patch_xvals(tpl, code_new, mark):
    a = tpl.index('<script type="text/x-dc"')
    b = tpl.index('</script>', a)
    code = tpl[a:b]
    if mark in code:
        return tpl
    code, n = re.subn(r'\n  xvals\(\) \{.*?\n  \}\n', lambda _: code_new, code, count=1, flags=re.S)
    assert n == 1, 'xvals introuvable'
    return tpl[:a] + code + tpl[b:]


def patch_khutba(tpl):
    tpl = patch_xvals(tpl, KHUTBA_XVALS, '/*ascil-khutba*/')
    if '{{kJum}}' in tpl:
        return tpl
    tpl = resub(tpl, r'<div class="flag" role="note"[^>]*>(?:(?!</div>).)*</div>', lambda m: '')
    tpl = resub(tpl, r'<p style="margin:24px 0 0;color:#F3EAD8">Jumu’a à <strong style="color:#fff">12:30</strong>(?:(?!</p>).)*</p>',
                lambda m: sc_if('kHasCur', '<p style="margin:24px 0 0;color:#F3EAD8">Jumu’a à <strong style="color:#fff">{{kJum}}</strong>'
                                + sc_if('kHasImam', ' · Imam {{kImam}}', 'false') + '</p>', 'false'))
    tpl = rep(tpl, 'Les prochains vendredis <span class="ex">[EXEMPLE À MODIFIER]</span></h2>', 'Les prochains vendredis</h2>')
    tpl = resub(tpl, r'(<div class="g4" style="margin-top:20px">\s*<sc-for list="\{\{kWeeks\}\}".*?</sc-for>\s*</div>)', lambda m: sc_if('kHasWeeks', m.group(1), 'true'))
    tpl = resub(tpl, r'(<div class="card sand" style="margin-top:20px;display:flex;gap:14px;align-items:flex-start">.*?)<p style="margin:0">La langue alterne(?:(?!</p>).)*</p></div>',
                lambda m: sc_if('kHasNote', m.group(1) + '<p style="margin:0">{{kNote}}</p></div>', 'true'))
    return tpl


def patch_rappel(tpl):
    tpl = patch_xvals(tpl, RAPPEL_XVALS, '/*ascil-rappel*/')
    if 'id="rp-son"' in tpl:
        return tpl
    tpl = resub(tpl, r'<div class="flag" role="note"[^>]*>(?:(?!</div>).)*</div>', lambda m: '')
    tpl = resub(tpl, r'<p class="muted" style="margin:10px 0 0;font-size:14px">Dohr, Asr et Maghreb : heures d’exemple(?:(?!</p>).)*</p>',
                lambda m: sc_if('rMissing', '<p class="muted" style="margin:10px 0 0;font-size:14px">Certaines heures ne sont pas encore dans le tableau du mois : '
                                'ces prières seront rappelées dès qu’elles y figurent.</p>', 'false'))
    tpl = resub(tpl, r'<label style="display:flex;gap:10px;align-items:center;font-weight:600;min-height:44px"><input type="checkbox" sc-camel-default-checked="true"( style="[^"]*")>Son</label>',
                lambda m: sc_if('rSon', '<label style="display:flex;gap:10px;align-items:center;font-weight:600;min-height:44px"><input type="checkbox" id="rp-son" sc-camel-default-checked="true"' + m.group(1) + '>Son</label>'))
    tpl = resub(tpl, r'<label style="display:flex;gap:10px;align-items:center;font-weight:600;min-height:44px"><input type="checkbox" sc-camel-default-checked="true"( style="[^"]*")>Vibration</label>',
                lambda m: sc_if('rVib', '<label style="display:flex;gap:10px;align-items:center;font-weight:600;min-height:44px"><input type="checkbox" id="rp-vib" sc-camel-default-checked="true"' + m.group(1) + '>Vibration</label>'))
    tpl = rep(tpl, 'Votre navigateur vous demandera l’autorisation d’envoyer des notifications. Aucun compte, aucune donnée envoyée.</p>',
              'Votre navigateur vous demandera l’autorisation d’envoyer des notifications. Aucun compte, aucune donnée envoyée. '
              'Les rappels arrivent tant que cette page reste ouverte.</p>'
              + sc_if('rUnsupported', '<p style="margin:10px 0 0;font-size:14px;color:#B3261E;font-weight:600">Ce navigateur ne permet pas les notifications : '
                      'ajoutez plutôt les rappels à votre calendrier.</p>', 'false')
              + sc_if('rHasIcs', '<button type="button" class="btn btn-ghost" sc-camel-on-click="{{rIcs}}" style="width:100%;min-height:52px;margin-top:14px">'
                      'Ajouter les rappels du mois à mon calendrier</button>'
                      '<p class="muted" style="margin:8px 0 0;font-size:14px">Fichier .ics : vos rappels sonnent même page fermée.</p>', 'false')
              + sc_if('rHasIcsMsg', '<p role="status" style="margin:8px 0 0;font-size:14px;font-weight:600;color:#0E4D3C">{{rIcsMsg}}</p>', 'false'))
    tpl = resub(tpl, r'(<div class="flag" style="background:#FDF3F2;border:1.5px dashed #B3261E">.*?)\s*<span class="muted">\(état d’erreur\)</span>(</p></div>)',
                lambda m: sc_if('rDenied', m.group(1) + m.group(2), 'false'))
    return tpl


def wire(name):
    path = ROOT / name
    s, i, j, tpl = load(path)
    tpl = patch_logic(tpl)
    tpl = patch_common(tpl)
    if name in HORAIRES:
        tpl = patch_markup(tpl)
    if name in KHUTBA:
        tpl = patch_khutba(tpl)
    if name in RAPPEL:
        tpl = patch_rappel(tpl)
    tpl = re.sub(r'<script id="ascil-prayer-live">.*?</script>\s*', '', tpl, flags=re.S)
    k = tpl.rindex('</body>')
    tpl = tpl[:k] + LIVE_SCRIPT + tpl[k:]
    save(path, s, i, j, tpl)


if __name__ == '__main__':
    pages = public_pages()
    for p in pages:
        wire(p)
    print(len(pages), 'pages publiques : heures de prière reliées à la base (dont la page Horaires complète)')
