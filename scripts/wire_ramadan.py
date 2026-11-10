"""Étape R1 : thème saisonnier Ramadan (maquettes « event templates », Ramadan · Accueil et Page de l'événement).

Deux pages, reconstruites à chaque passage depuis les maquettes d'origine gardées dans scripts/maquettes/ :
  - TH-Ramadan-Accueil.dc.html : l'Accueil pendant le Ramadan. Quand « Site entier → Mode du site » est sur
    Ramadan (et dans ses dates si l'activation automatique est cochée), le serveur (functions/_middleware.js)
    la sert à la place de l'Accueil normal, à la même adresse ;
  - TH-Ramadan-Page.dc.html : la page du mois (calendrier des jours, nuits du Qadr).
L'enveloppe de chaque page (polices et images de la maquette) reste celle du fichier ; seul le modèle change.

Vraies données uniquement :
  - dates du Ramadan, numéro du jour, lunes, année de l'hégire : clé season (dates saisies dans le panneau) ;
  - heures : /api/prayer-times (tableau du mois, défauts de l'Accueil, calcul local pour Dohr, Asr, Maghreb) ;
    l'iftar est l'heure du Maghreb ;
  - campagne et annonces : réglages de l'Accueil (clé home).
Les blocs de la maquette sans vraie donnée (Imsak, Tarawih, iftar du samedi, zakat, halaqa, programme,
questions fréquentes, PDF) ne sont pas publiés à cette étape : ils reviendront avec la rubrique Ramadan du
panneau (étape R2), remplis par l'association.
Ordre : PREMIÈRE étape des branchements (les suivantes ajoutent leurs scripts communs à ces pages). Idempotent.
"""
import json, re, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
OPEN = '<script type="__bundler/template">'
SRC = ROOT / 'scripts' / 'maquettes'
ACC = ROOT / 'TH-Ramadan-Accueil.dc.html'
PAGE = ROOT / 'TH-Ramadan-Page.dc.html'

NAV = {'Horaires': '/Horaires.dc.html', 'À propos': '/APropos.dc.html', 'Services': '/Services.dc.html',
       'Événements': '/Evenements.dc.html', 'Contact': '/Contact.dc.html'}


def rep(tpl, old, new, count=1):
    n = tpl.count(old)
    assert n == count, f'{n} occurrence(s) au lieu de {count} : {old[:90]!r}'
    return tpl.replace(old, new)


def resub(tpl, pat, new, count=1):
    out, n = re.subn(pat, new, tpl, flags=re.S)
    assert n == count, f'{n} remplacement(s) au lieu de {count} : {pat[:90]!r}'
    return out


def sc_if(name, inner, default='true'):
    return f'<sc-if value="{{{{{name}}}}}" hint-placeholder-val="{{{{ {default} }}}}">{inner}</sc-if>'


# ---------------------------------------------------------------------------
# Logique commune (données réelles), insérée dans le composant de chaque page.
# ---------------------------------------------------------------------------
LOAD_JS = r"""
  componentDidMount() {
    this.t = setInterval(() => this.setState({ now: Date.now() }), 1000);
    const get = (u) => fetch(u).then((r) => (r.ok ? r.json() : null)).catch(() => null);
    Promise.all([get('/api/settings/season'), get('/api/settings/home'), get('/api/prayer-times')]).then(([se, ho, pt]) => {
      const S = (se && se.ok && se.settings) || {};
      const H = (ho && ho.ok && ho.settings) || {};
      const months = [];
      if (S.from && S.to) {
        let m = S.from.slice(0, 7);
        while (m <= S.to.slice(0, 7) && months.length < 3) {
          months.push(m);
          const y = +m.slice(0, 4), mo = +m.slice(5, 7);
          m = mo === 12 ? (y + 1) + '-01' : y + '-' + String(mo + 1).padStart(2, '0');
        }
      }
      const cur = pt && pt.ok ? pt.month : '';
      return Promise.all(months.map((m) => (m === cur ? Promise.resolve(pt) : get('/api/prayer-times?month=' + m)))).then((list) => {
        const byDate = {};
        list.concat([pt]).forEach((x) => { if (x && x.ok && Array.isArray(x.resolved)) x.resolved.forEach((d) => { byDate[d.date] = d; }); });
        const today = pt && pt.ok ? (pt.today || pt.day) : null;
        if (today && today.date) byDate[today.date] = today;
        this.setState({ S, H, byDate, today, ready: true });
      });
    });
  }
  componentWillUnmount() { clearInterval(this.t); }
  ramadan() {
    const st = this.state, S = st.S || {}, p2 = (n) => String(n).padStart(2, '0');
    const dayStr = (ms) => {
      try {
        const p = {};
        new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Moncton', year: 'numeric', month: '2-digit', day: '2-digit' }).formatToParts(new Date(ms)).forEach((x) => { p[x.type] = x.value; });
        return p.year + '-' + p.month + '-' + p.day;
      } catch (e) { return new Date(ms).toISOString().slice(0, 10); }
    };
    const utc = (d) => Date.UTC(+d.slice(0, 4), +d.slice(5, 7) - 1, +d.slice(8, 10));
    const addDays = (d, n) => new Date(utc(d) + n * 86400000).toISOString().slice(0, 10);
    const fmt = (d, o) => { try { return new Intl.DateTimeFormat('fr-CA', Object.assign({ timeZone: 'UTC' }, o)).format(new Date(utc(d))); } catch (e) { return d; } };
    const today = dayStr(st.now);
    const ok = /^\d{4}-\d\d-\d\d$/;
    const has = ok.test(S.from || '') && ok.test(S.to || '') && S.to >= S.from;
    const total = has ? Math.round((utc(S.to) - utc(S.from)) / 86400000) + 1 : 0;
    const n = has ? Math.round((utc(today) - utc(S.from)) / 86400000) + 1 : 0;
    const inside = has && n >= 1 && n <= total;
    let hy = '';
    if (has) {
      try {
        const yp = new Intl.DateTimeFormat('fr-CA-u-ca-islamic-umalqura', { year: 'numeric', timeZone: 'UTC' }).formatToParts(new Date(utc(S.from) + 86400000 * 2)).find((x) => x.type === 'year');
        hy = yp ? String(yp.value).replace(/\D/g, '') : '';
      } catch (e) { hy = ''; }
    }
    const T = /^\d\d:\d\d$/;
    const td = st.today || {};
    const toS = (h) => +h.slice(0, 2) * 3600 + +h.slice(3, 5) * 60;
    let secs = 0;
    try {
      const pp = new Intl.DateTimeFormat('en-US', { timeZone: 'America/Moncton', hour: '2-digit', minute: '2-digit', second: '2-digit', hourCycle: 'h23' }).formatToParts(new Date(st.now));
      const g = (k) => { const x = pp.find((q) => q.type === k); return x ? parseInt(x.value, 10) % 24 : 0; };
      secs = g('hour') * 3600 + g('minute') * 60 + (pp.find((q) => q.type === 'second') ? parseInt(pp.find((q) => q.type === 'second').value, 10) : 0);
    } catch (e) {}
    const iftar = T.test(td.maghreb || '') ? td.maghreb : '';
    const tom = (st.byDate || {})[addDays(today, 1)] || {};
    let left = -1, cdWhen = 'ce soir', cdTime = iftar;
    if (iftar) {
      left = toS(iftar) - secs;
      if (left <= 0) {
        if (T.test(tom.maghreb || '')) { left = toS(tom.maghreb) + 86400 - secs; cdWhen = 'demain'; cdTime = tom.maghreb; } else { left = -1; }
      }
    }
    return { S, has, total, n, inside, hy, today, fmt, addDays, iftar, left, cdWhen, cdTime, td, p2,
      before: has && n < 1 };
  }
"""

ACC_VALS = r"""
  renderVals() {
    const st = this.state, R = this.ramadan(), H = st.H || {}, T = /^\d\d:\d\d$/;
    const nf = (v) => { try { return Math.round(v).toLocaleString('fr-CA').replace(/\u202f|\u00a0/g, ' '); } catch (e) { return String(Math.round(v)); } };
    const isFri = (() => { try { return new Date(Date.UTC(+R.today.slice(0, 4), +R.today.slice(5, 7) - 1, +R.today.slice(8, 10))).getUTCDay() === 5; } catch (e) { return false; } })();
    const cells = [['Fajr', R.td.fajr], isFri ? ['Jumu’a', R.td.jumuha] : ['Dohr', R.td.dohr], ['Asr', R.td.asr], ['Icha', R.td.isha]]
      .filter((c) => T.test(c[1] || '')).map((c) => ({ n: c[0], v: c[1] }));
    const moons = [];
    for (let d = 1; d <= R.total; d++) {
      moons.push({ cls: 'mph' + (R.inside && d === R.n ? ' today' : '') + (d > R.total - 10 ? ' q' : ''), t: 'Jour ' + d,
        st: 'transform:translateX(' + Math.round(100 - d * 200 / R.total) + '%);opacity:' + (R.inside && d <= R.n ? 1 : 0.35) });
    }
    const done = R.inside ? R.n : (R.has && R.n > R.total ? R.total : 0);
    const C = H.campagne || {}, on = H.on || {};
    const obj = Math.max(0, +C.objectif || 0), rec = Math.max(0, +C.recolte || 0);
    const pct = obj ? Math.min(100, Math.round(rec / obj * 100)) : 0;
    const A = H.annonces || {};
    const ann = (Array.isArray(A.items) ? A.items : []).filter((x) => x && x.on !== false && x.titre).slice(0, A.max || 3)
      .map((x) => ({ date: x.date || '', hasDate: !!x.date, titre: x.titre, resume: x.resume || '', hasResume: !!x.resume }));
    return {
      menu: st.menu, menuStr: String(st.menu), toggleMenu: () => this.setState({ menu: !st.menu }),
      topDay: R.inside ? ' · Jour ' + R.n : '', hasIftar: !!R.iftar, iftar: R.iftar,
      eyebrow: 'Ramadan' + (R.hy ? ' ' + R.hy : '') + (R.inside ? ' · Jour ' + R.n + ' sur ' + R.total : (R.before ? ' · à partir du ' + R.fmt(R.S.from, { weekday: 'long', day: 'numeric', month: 'long' }) : '')),
      hasCd: R.left > 0, cdWhen: R.cdWhen, cdTime: R.cdTime,
      cdH: R.p2(Math.floor(Math.max(0, R.left) / 3600)), cdM: R.p2(Math.floor(Math.max(0, R.left) / 60) % 60), cdS: R.p2(Math.max(0, R.left) % 60),
      cells, hasCells: cells.length > 0, hasGlass: !!R.iftar || cells.length > 0,
      hasMonth: R.has, moons, moonsLabel: R.inside ? 'Jour ' + R.n + ' sur ' + R.total + ' du Ramadan' : R.total + ' jours de Ramadan',
      monthTitle: R.inside ? (R.n >= R.total ? 'Dernier jour de jeûne' : R.n + (R.n > 1 ? ' jours de jeûne, ' : ' jour de jeûne, ') + (R.total - R.n) + ' à venir') : R.total + ' jours de jeûne',
      barW: 'width:' + (R.total ? Math.round(done / R.total * 100) : 0) + '%',
      firstDay: R.has ? '1er Ramadan · ' + R.fmt(R.S.from, { weekday: 'short', day: 'numeric', month: 'short' }) : '',
      lastDay: R.has ? 'Dernier jour prévu · ' + R.fmt(R.S.to, { weekday: 'short', day: 'numeric', month: 'short' }) + ' (selon la TCOM)' : '',
      hasCamp: obj > 0 && on.campagne !== false, campRec: nf(rec) + ' $', campObj: 'sur ' + nf(obj) + ' $', campBar: 'width:' + pct + '%',
      campPct: pct + ' % de l’objectif',
      ann, hasAnn: ann.length > 0
    };
  }
"""

PAGE_VALS = r"""
  renderVals() {
    const st = this.state, R = this.ramadan();
    const long = { weekday: 'long', day: 'numeric', month: 'long' };
    const nights = [];
    if (R.has) {
      for (let k = 21; k <= Math.min(29, R.total); k++) {
        nights.push({ n: k, cls: 'night-card rv' + (k % 2 ? ' odd' : ''), soir: 'soir du ' + R.fmt(R.addDays(R.S.from, k - 2), { day: 'numeric', month: 'short' }) });
      }
    }
    const yr = R.has ? R.S.to.slice(0, 4) : '';
    return {
      menu: st.menu, menuStr: String(st.menu), toggleMenu: () => this.setState({ menu: !st.menu }),
      topDay: R.inside ? ' · Jour ' + R.n : '', hasIftar: !!R.iftar, iftar: R.iftar,
      eyebrow: 'Ramadan' + (R.hy ? ' ' + R.hy : ''),
      lead: R.has ? 'Du ' + R.fmt(R.S.from, long) + ' au ' + R.fmt(R.S.to, long) + ' ' + yr + ', selon l’annonce de la TCOM. Horaires du mois et nuits du Qadr : tout est ici.'
        : 'Horaires du mois et nuits du Qadr : tout est ici.',
      hasNights: nights.length > 0, nights
    };
  }
"""

# Calendrier des jours : construit en HTML par un petit script (tableau + choix de la semaine).
CAL_SCRIPT = r"""<script id="th-ramadan-cal">
(function () {
  var box = null, data = null, wk = -1;
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function today() {
    try { var p = {}; new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Moncton', year: 'numeric', month: '2-digit', day: '2-digit' }).formatToParts(new Date()).forEach(function (x) { p[x.type] = x.value; }); return p.year + '-' + p.month + '-' + p.day; } catch (e) { return new Date().toISOString().slice(0, 10); }
  }
  function utc(d) { return Date.UTC(+d.slice(0, 4), +d.slice(5, 7) - 1, +d.slice(8, 10)); }
  function add(d, n) { return new Date(utc(d) + n * 86400000).toISOString().slice(0, 10); }
  function label(d) { try { return new Intl.DateTimeFormat('fr-CA', { timeZone: 'UTC', weekday: 'short', day: 'numeric', month: 'short' }).format(new Date(utc(d))); } catch (e) { return d; } }
  function t(v) { return /^\d\d:\d\d$/.test(v || '') ? v : '—'; }
  function weeks(total) { var b = [0, 8, 15, 23, total], out = []; for (var i = 0; i < 4; i++) { var a = Math.min(b[i], total), z = Math.min(b[i + 1], total); if (i === 3) z = total; if (z > a) out.push([a, z]); } return out; }
  function render() {
    box = document.getElementById('th-cal');
    if (!box || !data) return;
    if (box.getAttribute('data-sig') === data.sig + ':' + wk) return;
    var W = weeks(data.days.length);
    var h = '<div class="seg" role="group" aria-label="Semaine" style="margin-bottom:18px">';
    W.forEach(function (w, i) { h += '<button type="button" data-wk="' + i + '" aria-pressed="' + (i === wk) + '">Jours ' + (w[0] + 1) + '–' + w[1] + '</button>'; });
    h += '</div><div style="overflow-x:auto"><table class="tbl tnum"><caption style="position:absolute;left:-9999px">Horaires du Ramadan, jours ' + (W[wk][0] + 1) + ' à ' + W[wk][1] + '</caption><thead><tr>'
      + '<th scope="col">Jour</th><th scope="col">Date</th><th scope="col">Fajr</th><th scope="col" class="hide-m">Dohr</th><th scope="col" class="hide-m">Asr</th><th scope="col">Iftar</th><th scope="col" class="hide-m">Icha</th></tr></thead><tbody>';
    for (var k = W[wk][0]; k < W[wk][1]; k++) {
      var d = data.days[k], cur = d.date === data.today;
      h += '<tr' + (cur ? ' class="now" aria-current="date"' : '') + '><td><b>' + (k + 1) + '</b></td><td>' + esc(label(d.date)) + '</td><td>' + esc(t(d.fajr)) + '</td><td class="hide-m">' + esc(t(d.jumuha && new Date(utc(d.date)).getUTCDay() === 5 ? d.jumuha : d.dohr)) + '</td><td class="hide-m">' + esc(t(d.asr)) + '</td><td class="if">' + esc(t(d.maghreb)) + '</td><td class="hide-m">' + esc(t(d.isha)) + '</td></tr>';
    }
    h += '</tbody></table></div><p class="muted" style="margin:14px 0 0;font-size:14px">La ligne dorée est aujourd’hui. Iftar = Maghreb. Horaires officiels de l’ASCIL (page Horaires).</p>';
    box.innerHTML = h;
    box.setAttribute('data-sig', data.sig + ':' + wk);
    Array.prototype.forEach.call(box.querySelectorAll('[data-wk]'), function (b) { b.addEventListener('click', function () { wk = +b.getAttribute('data-wk'); render(); var x = box.querySelector('[data-wk="' + wk + '"]'); if (x) x.focus(); }); });
  }
  function get(u) { return fetch(u).then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; }); }
  get('/api/settings/season').then(function (se) {
    var S = se && se.ok ? se.settings : null;
    if (!S || !/^\d{4}-\d\d-\d\d$/.test(S.from || '') || !/^\d{4}-\d\d-\d\d$/.test(S.to || '') || S.to < S.from) return;
    var months = [], m = S.from.slice(0, 7);
    while (m <= S.to.slice(0, 7) && months.length < 3) { months.push(m); var y = +m.slice(0, 4), mo = +m.slice(5, 7); m = mo === 12 ? (y + 1) + '-01' : y + '-' + String(mo + 1).padStart(2, '0'); }
    return Promise.all(months.map(function (x) { return get('/api/prayer-times?month=' + x); })).then(function (list) {
      var by = {};
      list.forEach(function (x) { if (x && x.ok && Array.isArray(x.resolved)) x.resolved.forEach(function (d) { by[d.date] = d; }); });
      var days = [], d = S.from;
      for (var i = 0; d <= S.to && i < 31; i++, d = add(d, 1)) days.push(by[d] || { date: d });
      var td = today(), idx = -1;
      days.forEach(function (x, i) { if (x.date === td) idx = i; });
      data = { days: days, today: td, sig: S.from + S.to + days.length };
      var W = weeks(days.length);
      wk = 0;
      W.forEach(function (w, i) { if (idx >= w[0] && idx < w[1]) wk = i; });
      render();
      new MutationObserver(function () { if (box && !box.isConnected) box = null; if (!document.getElementById('th-cal') || !document.getElementById('th-cal').getAttribute('data-sig')) render(); })
        .observe(document.documentElement, { childList: true, subtree: true });
    });
  });
})();
</script>
"""

EMAIL = ''


def footer(tpl):
    a = tpl.index('<footer class="ftr">')
    b = tpl.index('</footer>', a) + len('</footer>')
    f = tpl[a:b]
    logo = f[f.index('<div><div style="display:flex;align-items:center;gap:12px">'):f.index('\n    <p style="margin:14px 0 0">34, 37e Avenue')]
    lk = 'color:inherit;text-decoration:underline;text-underline-offset:3px'
    new = ('<footer class="ftr">\n <div class="wrap">\n  <div class="g4" style="gap:36px">\n   '
           + logo + '\n    <p style="margin:14px 0 0">34, 37e Avenue<br>Edmundston, NB E3V 3S2</p></div>\n'
           '   <div><p style="margin:0 0 10px;font-weight:700;color:#F5D896">Ramadan</p><p style="margin:0;line-height:2">'
           + sc_if('hasIftar', 'Iftar ce soir {{iftar}}<br>', 'false')
           + f'<a href="/TH-Ramadan-Page.dc.html" style="{lk}">Le mois du Ramadan</a><br><a href="/Horaires.dc.html" style="{lk}">Horaires du mois</a></p></div>\n'
           '   <div><p style="margin:0 0 10px;font-weight:700;color:#F5D896">Le site</p><p style="margin:0;line-height:2">'
           f'<a href="/" style="{lk}">Accueil</a> · <a href="/Horaires.dc.html" style="{lk}">Horaires</a> · <a href="/Services.dc.html" style="{lk}">Services</a><br>'
           f'<a href="/Evenements.dc.html" style="{lk}">Événements</a> · <a href="/Contact.dc.html" style="{lk}">Contact</a></p></div>\n'
           '   <div><p style="margin:0 0 10px;font-weight:700;color:#F5D896">Nous écrire</p><p style="margin:0;word-break:break-all">'
           f'<a href="mailto:{EMAIL}" style="{lk};overflow-wrap:anywhere">{EMAIL}</a></p><p class="ar" style="margin:14px 0 0;font-size:26px;color:#F5D896">رمضان كريم</p></div>\n'
           '  </div>\n'
           '  <p style="margin:44px 0 0;padding-top:22px;border-top:1px solid rgba(255,255,255,.18);font-size:14px">© 2026 Association Socio-Culturelle '
           'Islamique Louperivoise — Edmundston, Québec<a href="superadmin.html" rel="nofollow" style="float:right;color:#F3EAD8;opacity:.75;'
           'text-decoration:underline;text-underline-offset:3px;display:inline-block;padding:4px 0;margin-left:16px">Espace administration</a></p>\n'
           ' </div>\n</footer>')
    return tpl[:a] + new + tpl[b:]


def header(tpl, current):
    """Menu : vraies pages du site, adresses absolues (la page d'accueil Ramadan est servie à « / »)."""
    tpl = tpl.replace('href="TH-Ramadan-Accueil.dc.html"', 'href="/"')
    tpl = tpl.replace('href="TH-Ramadan-Page.dc.html', 'href="/TH-Ramadan-Page.dc.html')
    for label, href in NAV.items():
        tpl = rep(tpl, f'<a href="#">{label}</a>', f'<a href="{href}">{label}</a>', 2)
    tpl = rep(tpl, '<a class="btn btn-pri hide-m" href="#"', '<a class="btn btn-pri hide-m" href="/Dons.dc.html"')
    tpl = rep(tpl, '<a href="#" style="border:0;color:#7FA9E0">Faire un don</a>', '<a href="/Dons.dc.html" style="border:0;color:#7FA9E0">Faire un don</a>')
    # Bandeau du haut : jour et iftar réels, plus de Tarawih (heure non fournie).
    tpl = resub(tpl, r'Ramadan Moubarak · Jour 12 · Iftar à <strong style="color:#F5D896">&nbsp;17:19&nbsp;</strong> · Tarawih 19:04',
                'Ramadan Moubarak{{topDay}}' + sc_if('hasIftar', ' · Iftar à <strong style="color:#F5D896">&nbsp;{{iftar}}&nbsp;</strong>', 'false'))
    return tpl


def set_logic(tpl, vals):
    a = tpl.index('<script type="text/x-dc"')
    b = tpl.index('</script>', a)
    code = tpl[a:b]
    head = code[:code.index('class Component extends DCLogic {')]
    code = (head + 'class Component extends DCLogic {\n  constructor(props) {\n    super(props);\n'
            '    this.state = { now: Date.now(), menu: false, ready: false, S: {}, H: {}, byDate: {}, today: null };\n  }'
            + LOAD_JS + vals + '}\n')
    return tpl[:a] + code + tpl[b:]


def titles(s, tpl, title):
    tpl = re.sub(r'<title>[^<]*</title>', f'<title>{title}</title>', tpl, count=1)
    s = re.sub(r'<title>[^<]*</title>', f'<title>{title}</title>', s, count=1)
    s = re.sub(r'Loading [^<]*\.\.\.', f'Loading {title}...', s, count=1)
    return s, tpl


def build(path, src, fn, title):
    s = path.read_text(encoding='utf-8')
    i = s.index(OPEN) + len(OPEN)
    j = s.index('</script>', i)
    tpl = fn((SRC / src).read_text(encoding='utf-8'))
    s, tpl = titles(s, tpl, title)
    i = s.index(OPEN) + len(OPEN)
    j = s.index('</script>', i)
    enc = json.dumps(tpl).replace('</', '<\\u002F')
    assert json.loads(enc) == tpl
    path.write_text(s[:i] + enc + s[j:], encoding='utf-8')


def accueil(tpl):
    tpl = header(tpl, 'accueil')
    tpl = rep(tpl, '<p class="eyebrow rise">Ramadan 1448 · Jour 12 sur 30</p>', '<p class="eyebrow rise">{{eyebrow}}</p>')
    tpl = rep(tpl, 'Un mois de jeûne, de prière et de partage. La mosquée vous accueille chaque soir pour l’iftar et les Tarawih.',
              'Un mois de jeûne, de prière et de partage.')
    tpl = resub(tpl, r'\n     <a class="btn btn-line bm" href="/TH-Ramadan-Page\.dc\.html#iftar".*?Iftar communautaire</a>', '')
    # Carte de l'iftar : heure réelle, compte à rebours, heures du jour.
    tpl = rep(tpl, '>Rupture du jeûne ce soir</p>', '>Rupture du jeûne {{cdWhen}}</p>')
    tpl = rep(tpl, '<span style="font-size:40px;font-weight:800;color:#F5D896">17:19</span>', '<span style="font-size:40px;font-weight:800;color:#F5D896">{{cdTime}}</span>')
    tpl = resub(tpl, r'(<div class="cd tnum" role="timer".*?</div></div>)', lambda m: sc_if('hasCd', m.group(1), 'true'))
    tpl = resub(tpl, r'<div class="g4 tnum" style="margin-top:18px;gap:10px;font-size:14px">.*?</div>\n     </div>',
                sc_if('hasCells', '<div class="g4 tnum" style="margin-top:18px;gap:10px;font-size:14px">'
                      '<sc-for list="{{cells}}" as="c" hint-placeholder-count="4"><div><span style="color:#BAC3DC">{{c.n}}</span><br><b style="font-size:20px">{{c.v}}</b></div></sc-for></div>'))
    tpl = resub(tpl, r'(<div class="glass" style="position:relative;padding:28px">.*?</sc-if>\n    </div>)', lambda m: sc_if('hasGlass', m.group(1)))
    # Les lunes : jours réels du Ramadan.
    tpl = rep(tpl, '<h2 id="r-m" class="h2" style="margin-top:12px">12 jours de jeûne, 18 à venir</h2>', '<h2 id="r-m" class="h2" style="margin-top:12px">{{monthTitle}}</h2>')
    tpl = resub(tpl, r'<div class="moons rv" style="margin-top:36px" role="img" aria-label="Jour 12 sur 30 du Ramadan">.*?</div></div>\n',
                '<div class="moons rv" style="margin-top:36px" role="img" aria-label="{{moonsLabel}}"><sc-for list="{{moons}}" as="m" hint-placeholder-count="30">'
                '<div class="{{m.cls}}" title="{{m.t}}"><i style="{{m.st}}"></i></div></sc-for></div>\n')
    tpl = rep(tpl, '<div class="bar" style="margin-top:28px"><i style="width:40%"></i></div>', '<div class="bar" style="margin-top:28px"><i style="{{barW}}"></i></div>')
    tpl = rep(tpl, '<span>1er Ramadan · lun. 8 févr.</span><span>Aïd al-Fitr · mer. 10 mars (selon la TCOM)</span>', '<span>{{firstDay}}</span><span>{{lastDay}}</span>')
    tpl = resub(tpl, r'(<section class="sec arab" aria-labelledby="r-m">.*?</section>)', lambda m: sc_if('hasMonth', m.group(1)))
    # « Vivre le Ramadan ensemble » : exemples sans vraie donnée, retiré jusqu'à la rubrique Ramadan du panneau.
    tpl = resub(tpl, r'<section class="sec" style="padding-top:20px" aria-labelledby="r-c">.*?</section>', '')
    # Campagne : vrais chiffres de l'Accueil.
    tpl = rep(tpl, '<span class="serif" style="font-size:40px;font-weight:700;color:#F5D896">0 $</span>',
              '<span class="serif" style="font-size:40px;font-weight:700;color:#F5D896">{{campRec}}</span><span class="muted">{{campObj}}</span>')
    tpl = rep(tpl, '<div class="bar" style="margin-top:14px"><i style="width:41%"></i></div>', '<div class="bar" style="margin-top:14px"><i style="{{campBar}}"></i></div>')
    tpl = rep(tpl, '41 % · 38 dons depuis le début du Ramadan', '{{campPct}}')
    tpl = resub(tpl, r'<a class="btn btn-pri bm" href="#">(<svg[^>]*>(?:(?!</svg>).)*</svg>Donner par Interac)</a>', r'<a class="btn btn-pri bm" href="/Dons.dc.html">\1</a>')
    tpl = resub(tpl, r'(<section class="sec"[^>]*aria-labelledby="r-g">.*?</section>)', lambda m: sc_if('hasCamp', m.group(1)))
    # Annonces : celles du panneau Accueil.
    a = tpl.index('aria-labelledby="r-a"')
    g = tpl.index('<div class="g3"', a)
    e = tpl.index('</div>\n </div>\n</section>', g)
    card0 = tpl[tpl.index('<a class="card rv"', g):tpl.index('</a>', tpl.index('<a class="card rv"', g)) + 4]
    gopen = tpl[g:tpl.index('>', g) + 1]
    card = re.sub(r'href="#"', 'href="/Evenements.dc.html"', card0, count=1)
    card = re.sub(r'(<span class="chip"[^>]*>)Samedi 20 février(</span>)', lambda m: sc_if('x.hasDate', m.group(1) + '{{x.date}}' + m.group(2)), card)
    card = card.replace('>Grand iftar familial<', '>{{x.titre}}<')
    card = re.sub(r'(<p class="muted"[^>]*>)Repas offert, inscription conseillée pour prévoir les plats\.(</p>)', lambda m: sc_if('x.hasResume', m.group(1) + '{{x.resume}}' + m.group(2)), card)
    assert '{{x.titre}}' in card and '{{x.date}}' in card and '{{x.resume}}' in card, 'carte d’annonce inattendue'
    tpl = tpl[:g] + gopen + '<sc-for list="{{ann}}" as="x" hint-placeholder-count="3">' + card + '</sc-for>\n  ' + tpl[e:]
    tpl = rep(tpl, '<p class="eyebrow">Annonces du Ramadan</p>', '<p class="eyebrow">Annonces</p>')
    tpl = resub(tpl, r'<a class="link" href="/TH-Ramadan-Page\.dc\.html#programme"([^>]*)>Tout le programme ', r'<a class="link" href="/Evenements.dc.html"\1>Toutes les annonces ')
    tpl = resub(tpl, r'(<section class="sec"[^>]*aria-labelledby="r-a">.*?</section>)', lambda m: sc_if('hasAnn', m.group(1)))
    tpl = footer(tpl)
    tpl = set_logic(tpl, ACC_VALS)
    assert '17:19' not in tpl and '142 500' not in tpl and 'Jour 12' not in tpl and 'href="#"' not in tpl.split('<script type="text/x-dc"')[0], 'reste de la maquette'
    return tpl


def page(tpl):
    tpl = header(tpl, 'page')
    tpl = rep(tpl, '<p class="eyebrow rise">Ramadan 1448</p>', '<p class="eyebrow rise">{{eyebrow}}</p>')
    tpl = resub(tpl, r'Du lundi 8 février au mardi 9 mars 2027, selon l’annonce de la TCOM\. Horaires, nuits du Qadr, iftars et zakat al-Fitr : tout est ici\.', '{{lead}}')
    # Boutons : plus de PDF (pas de fichier) ; le rappel mène à la page Rappel de prière.
    tpl = resub(tpl, r'<a class="btn btn-pri bm" href="#">(?:(?!</a>).)*Télécharger le calendrier \(PDF\)</a>', '')
    tpl = resub(tpl, r'<a class="btn btn-line bm" href="#"([^>]*)>((?:(?!</a>).)*)Activer un rappel d’iftar</a>',
                r'<a class="btn btn-line bm" href="/N3-Rappel.dc.html"\1>\2Recevoir un rappel de prière</a>')
    # Calendrier : tableau construit d'après les vrais horaires (script #th-ramadan-cal).
    tpl = rep(tpl, '<h2 id="re-t" class="h2"', '<h2 id="re-t" class="h2"')
    a = tpl.index('aria-labelledby="re-t"')
    sa = tpl.rindex('<section', 0, a)
    se = tpl.index('</section>', a) + len('</section>')
    sec = tpl[sa:se]
    sec = resub(sec, r'<div class="seg" role="group" aria-label="Semaine">.*?</div>', '')
    gl = sec.index('<div class="glass rv"')
    gl_open = sec[gl:sec.index('>', gl) + 1]
    sec = sec[:gl] + gl_open + '<div id="th-cal"><p class="muted" style="margin:0">Le calendrier s’affiche dès que les dates du Ramadan sont fixées.</p></div></div>\n </div>\n</section>'
    sec = sec.replace('Les 30 jours, semaine par semaine', 'Les jours du Ramadan, semaine par semaine')
    tpl = tpl[:sa] + sec + tpl[se:]
    # Nuits du Qadr : dates réelles ; la phrase sur l'ouverture de la mosquée attend la rubrique du panneau.
    tpl = resub(tpl, r'<p class="lead"[^>]*>La mosquée reste ouverte pour le qiyam al-layl.*?</p>\n    ', '')
    n0 = tpl.index('<div class="night-card rv odd">')
    ne = tpl.index('</div></div>\n  </div>', n0)
    first = tpl[n0:tpl.index('</p></div>', n0) + len('</p></div>')]
    card = first.replace('class="night-card rv odd"', 'class="{{w.cls}}"')
    card = re.sub(r'(<p class="serif"[^>]*>)21(</p>)', r'\1{{w.n}}\2', card)
    card = re.sub(r'(<p class="tnum"[^>]*>)soir du 27 févr\.(</p>)', r'\1{{w.soir}}\2', card)
    assert '{{w.n}}' in card and '{{w.soir}}' in card, 'carte de nuit inattendue'
    tpl = tpl[:n0] + '<sc-for list="{{nights}}" as="w" hint-placeholder-count="9">' + card + '</sc-for>' + tpl[ne:]
    tpl = resub(tpl, r'(<section class="sec arab" style="padding-top:20px" aria-labelledby="re-q">.*?</section>)', lambda m: sc_if('hasNights', m.group(1)))
    # Programme, zakat, questions : exemples, retirés jusqu'à la rubrique Ramadan du panneau.
    tpl = resub(tpl, r'<section id="programme".*?</section>', '')
    tpl = resub(tpl, r'<section id="zakat".*?</section>', '')
    tpl = resub(tpl, r'<section class="sec"[^>]*aria-labelledby="re-f">.*?</section>', '')
    tpl = footer(tpl)
    tpl = set_logic(tpl, PAGE_VALS)
    k = tpl.rindex('</body>')
    tpl = tpl[:k] + CAL_SCRIPT + tpl[k:]
    body = tpl.split('<script type="text/x-dc"')[0]
    assert '17:19' not in body and '8 févr' not in body and 'href="#"' not in body, 'reste de la maquette'
    return tpl


# Lien de la saison dans le menu des pages publiques (Ramadan, Aïd al-Fitr, Aïd al-Adha), seulement pendant
# la saison choisie dans « Mode du site » (mêmes règles que le serveur). Le nom du script reste #ascil-ramadan-menu.
MENU_SCRIPT = r"""<script id="ascil-ramadan-menu">
(function () {
  var LINKS = { ramadan: ['/TH-Ramadan-Page.dc.html', 'Ramadan'], aid_fitr: ['/TH-Fitr-Page.dc.html', 'Aïd al-Fitr'], aid_adha: ['/TH-Adha-Page.dc.html', 'Aïd al-Adha'] };
  var HREF = '', LABEL = '';
  function today() {
    try { var p = {}; new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Moncton', year: 'numeric', month: '2-digit', day: '2-digit' }).formatToParts(new Date()).forEach(function (x) { p[x.type] = x.value; }); return p.year + '-' + p.month + '-' + p.day; } catch (e) { return new Date().toISOString().slice(0, 10); }
  }
  function active(s) {
    if (!s || !LINKS[s.mode]) return false;
    if (!s.auto) return true;
    var d = today();
    return !!s.from && !!s.to && d >= s.from && d <= s.to;
  }
  function horaires(nav) {
    var links = nav.querySelectorAll('a');
    for (var i = 0; i < links.length; i++) { if (/(^|\/)(?:M-|T-)?Horaires\.dc\.html$/.test(links[i].getAttribute('href') || '')) return links[i]; }
    return null;
  }
  function add() {
    var desk = document.querySelector('nav.nav-desk');
    if (desk && !desk.querySelector('[data-ascil-ramadan]')) {
      var h = horaires(desk), after = h && h.closest('.dd') ? h.closest('.dd') : h;
      if (after) {
        var a = document.createElement('a');
        a.className = 'navlink'; a.href = HREF; a.textContent = LABEL; a.setAttribute('data-ascil-ramadan', '');
        after.parentNode.insertBefore(a, after.nextSibling);
      }
    }
    var mob = document.querySelector('nav[aria-label="Menu mobile"]');
    if (mob && !mob.querySelector('[data-ascil-ramadan]')) {
      var hm = horaires(mob);
      if (hm && hm.parentNode === mob) {
        var c = hm.cloneNode(true);
        c.href = HREF; c.setAttribute('data-ascil-ramadan', ''); c.removeAttribute('aria-current');
        for (var k = 0; k < c.childNodes.length; k++) { if (c.childNodes[k].nodeType === 3 && c.childNodes[k].nodeValue.trim()) { c.childNodes[k].nodeValue = LABEL; break; } }
        mob.insertBefore(c, hm.nextSibling);
      }
    }
  }
  fetch('/api/settings/season').then(function (r) { return r.ok ? r.json() : null; }).then(function (j) {
    if (!j || !j.ok || !active(j.settings)) return;
    HREF = LINKS[j.settings.mode][0]; LABEL = LINKS[j.settings.mode][1];
    add();
    new MutationObserver(add).observe(document.documentElement, { childList: true, subtree: true });
  }).catch(function () {});
})();
</script>
"""
MENU_RE = re.compile(r'<script id="ascil-ramadan-menu">.*?</script>\n?', re.S)


def menu_pages():
    pages = [p for p in sorted(ROOT.glob('*.dc.html')) if not p.name.startswith(('SA-', 'TH-'))] + [ROOT / 'index.html', ROOT / '404.html']
    n = 0
    for path in pages:
        s = path.read_text(encoding='utf-8')
        i = s.index(OPEN) + len(OPEN)
        j = s.index('</script>', i)
        tpl = json.loads(s[i:j])
        if 'aria-label="Menu mobile"' not in tpl:
            continue
        new = MENU_RE.sub('', tpl)
        k = new.rindex('</body>')
        new = new[:k] + MENU_SCRIPT + new[k:]
        if new != tpl:
            enc = json.dumps(new).replace('</', '<\\u002F')
            path.write_text(s[:i] + enc + s[j:], encoding='utf-8')
        n += 1
    print(f'lien de la saison (Ramadan, Aïd) dans le menu de {n} pages publiques')


if __name__ == '__main__':
    build(ACC, 'ramadan-accueil.tpl.html', accueil, 'Ramadan — ASCIL')
    build(PAGE, 'ramadan-page.tpl.html', page, 'Le mois du Ramadan — ASCIL')
    menu_pages()
    print('thème Ramadan : TH-Ramadan-Accueil et TH-Ramadan-Page reconstruites depuis les maquettes, branchées sur les vraies données')
