"""Étape V1 : thème du vendredi (Jumu'a), maquette « joumoaa » : Vendredi · Accueil, Horaires et Khutba.

Trois pages, reconstruites à chaque passage depuis les maquettes d'origine gardées dans scripts/maquettes/ :
  - TH-Vendredi-Accueil.dc.html : l'Accueil du vendredi. Quand « Site entier → Mode du site → Thème du vendredi »
    est sur « Automatique » (le vendredi seulement) ou « Activé », le serveur (functions/_middleware.js) la sert à
    la place de l'Accueil normal, à la même adresse. Un mode Ramadan ou Aïd en cours passe avant ;
  - TH-Vendredi-Horaires.dc.html et TH-Vendredi-Khutba.dc.html : pages du vendredi, liées depuis cet Accueil.
    Thème éteint : leurs adresses mènent aux pages normales (Horaires, Langue de la khutba).
Les versions mobiles de la maquette sont les mêmes pages (mise en page adaptative) : une seule page par écran.

Vraies données uniquement :
  - heure de Jumu'a, Fajr, Icha et autres prières : /api/prayer-times (tableau du mois, défauts de l'Accueil) ;
  - conseil d'arrivée (minutes d'avance, stationnement) : Horaires → Vendredi (clé horaires) ;
  - langue, traduction et imam de la khutba : Horaires → Langue de la khutba (clé khutba) ;
  - campagne : /api/campagne (même source que le reste du site).
Retirés car propres à la maquette : heures fixes (portes 11:45, adhan, prière 12:55, après 13:05), thème et résumé
d'exemple de la khutba, fiches PDF, durée, nom d'imam d'attente, espace femmes « à confirmer », faux rappels.
Rappels religieux généraux (sunnas, al-Kahf, salawat, duas, hadiths cités) : gardés ; rien n'est mémorisé.
Ordre : juste après wire_aid.py. Idempotent.
"""
import re, pathlib, importlib.util

HERE = pathlib.Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location('wire_aid', HERE / 'wire_aid.py')
A = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(A)
ROOT, rep, resub, sc_if, build, EMAIL, NAV = A.ROOT, A.rep, A.resub, A.sc_if, A.build, A.EMAIL, A.NAV
section, drop, check = A.section, A.drop, A.check

GOLD = '#E7C27A'

# ---------------------------------------------------------------------------
# Logique commune aux trois pages (données réelles).
# ---------------------------------------------------------------------------
LOGIC = r"""
  componentDidMount() {
    this.t = setInterval(() => this.setState({ now: Date.now() }), 1000);
    const get = (u) => fetch(u).then((r) => (r.ok ? r.json() : null)).catch(() => null);
    const F = this.fri().F;
    Promise.all([get('/api/settings/horaires'), get('/api/settings/khutba'), get('/api/campagne'),
      get('/api/prayer-times?month=' + F.slice(0, 7) + '&date=' + F)]).then(([ho, kh, ca, pt]) => {
      const byDate = {};
      if (pt && pt.ok && Array.isArray(pt.resolved)) pt.resolved.forEach((d) => { if (d && d.date) byDate[d.date] = d; });
      if (pt && pt.ok && pt.day) byDate[F] = Object.assign({}, pt.day, { date: F });
      this.setState({ H: (ho && ho.ok && ho.settings) || {}, K: (kh && kh.ok && kh.settings) || {}, C: ca && ca.ok ? ca : null,
        byDate, defs: (pt && pt.ok && pt.defaults) || {}, ready: true });
    });
  }
  componentWillUnmount() { clearInterval(this.t); }
  fri() {
    const st = this.state, p2 = (n) => String(n).padStart(2, '0'), T = /^\d\d:\d\d$/;
    const pp = {};
    try {
      new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Moncton', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit', hourCycle: 'h23' })
        .formatToParts(new Date(st.now)).forEach((x) => { pp[x.type] = x.value; });
    } catch (e) {}
    const today = pp.year ? pp.year + '-' + pp.month + '-' + pp.day : new Date(st.now).toISOString().slice(0, 10);
    const secs = ((parseInt(pp.hour, 10) || 0) % 24) * 3600 + (parseInt(pp.minute, 10) || 0) * 60 + (parseInt(pp.second, 10) || 0);
    const utc = (d) => Date.UTC(+d.slice(0, 4), +d.slice(5, 7) - 1, +d.slice(8, 10));
    const addDays = (d, n) => new Date(utc(d) + n * 86400000).toISOString().slice(0, 10);
    const fmt = (d, o, loc) => { try { return new Intl.DateTimeFormat(loc || 'fr-CA', Object.assign({ timeZone: 'UTC' }, o)).format(new Date(utc(d) + 43200000)); } catch (e) { return d; } };
    const cap = (s) => (s ? s.charAt(0).toUpperCase() + s.slice(1) : s);
    const dow = new Date(utc(today)).getUTCDay();
    const isFri = dow === 5;
    const F = addDays(today, (5 - dow + 7) % 7);
    const by = st.byDate || {}, defs = st.defs || {};
    const jOf = (d) => { const r = by[d] || {}; return T.test(r.jumuha || '') ? r.jumuha : (T.test(defs.jumuha || '') ? defs.jumuha : ''); };
    const toS = (h) => +h.slice(0, 2) * 3600 + +h.slice(3, 5) * 60;
    const J = jOf(F);
    // Khutba et prière : environ 45 minutes à partir de l'heure de Jumu'a du tableau.
    const during = isFri && !!J && secs >= toS(J) && secs < toS(J) + 2700;
    const over = isFri && !!J && secs >= toS(J) + 2700;
    let left = 0;
    if (J && !during) {
      const tgt = over ? addDays(F, 7) : F;
      left = Math.round((utc(tgt) - utc(today)) / 86400000) * 86400 + toS(jOf(tgt) || J) - secs;
    }
    left = Math.max(0, left);
    const V = (st.H || {}).vendredi || {};
    const av = V.on !== false && Number(V.avance) > 0 ? Number(V.avance) : 0;
    let arrive = '';
    if (J && av) { const m = Math.max(0, toS(J) / 60 - av); arrive = p2(Math.floor(m / 60)) + ':' + p2(m % 60); }
    const K = st.K || {};
    const all = (Array.isArray(K.vendredis) ? K.vendredis : []).filter((v) => v && v.on !== false);
    const list = all.filter((v) => v.date >= F);
    const kf = list.find((v) => v.date === F) || null;
    const L = (s) => String(s || '').toLowerCase();
    const trad = (v) => (v && v.traduction && v.traduction !== 'Aucune' ? L(v.traduction) : '');
    let hijri = '';
    try { hijri = new Intl.DateTimeFormat('ar-SA-u-ca-islamic-umalqura', { timeZone: 'UTC', day: 'numeric', month: 'long', year: 'numeric' }).format(new Date(utc(F) + 43200000)); } catch (e) {}
    return { today, isFri, F, J, during, over, left, arrive, av, conseil: V.conseil !== false, all, list, kf, L, trad, fmt, cap, addDays,
      hijri, by, defs, p2, T, nombre: [2, 4, 6, 8].indexOf(Number(K.nombre)) >= 0 ? Number(K.nombre) : 4, mode: K.mode || '' };
  }
  renderVals() {
    const st = this.state, R = this.fri(), p2 = R.p2, T = R.T;
    const SUN = [['Le ghusl', 'La grande ablution avant de venir.'], ['Le siwak et la propreté', 'Se brosser les dents, se préparer.'],
      ['Le parfum et les beaux habits', 'Ses vêtements les plus propres (parfum pour les hommes).'], ['Venir tôt, à pied si possible', 'Chaque pas vers la mosquée compte.'],
      ['Lire la sourate al-Kahf', 'Entre le coucher du soleil jeudi et celui de vendredi.'], ['Multiplier les salawat', 'Prier sur le Prophète ﷺ tout au long du jour.'],
      ['Écouter la khutba en silence', 'Téléphone éteint, on ne parle pas pendant le sermon.'], ['Faire des duas', 'Surtout dans la dernière heure, avant le Maghreb.']];
    const done = st.sunna.filter(Boolean).length, kd = st.kahf.filter(Boolean).length;
    const dShort = (d) => R.cap(R.fmt(d, { weekday: 'short', day: 'numeric', month: 'short' }));
    const dLong = (d) => R.cap(R.fmt(d, { weekday: 'long', day: 'numeric', month: 'long' }));
    const val = (d, k) => { const r = R.by[d] || {}; return T.test(r[k] || '') ? r[k] : (T.test(R.defs[k] || '') ? R.defs[k] : ''); };
    const lang = R.kf ? R.kf.langue : '', tr = R.trad(R.kf);
    // Vendredis du mois : heures du tableau (défauts de l'Accueil sinon), langue saisie dans Horaires.
    const ym = R.F.slice(0, 7), fris = [];
    const w0 = new Date(Date.UTC(+ym.slice(0, 4), +ym.slice(5, 7) - 1, 1)).getUTCDay();
    for (let d = R.addDays(ym + '-01', (5 - w0 + 7) % 7); d.slice(0, 7) === ym; d = R.addDays(d, 7)) {
      const k = R.all.find((v) => v.date === d) || null;
      fris.push({ d: dShort(d), isToday: d === R.today, bg: d === R.today ? '#E3F0EB' : 'transparent',
        fajr: val(d, 'fajr') || '—', jum: val(d, 'jumuha') || '—', isha: val(d, 'isha') || '—',
        lang: k ? 'Khutba en ' + R.L(k.langue) + (R.trad(k) ? ', traduction ' + R.trad(k) : '') : '' });
    }
    const steps = [];
    if (R.arrive) steps.push({ t: R.arrive, cls: '', n: 'Arriver', d: R.av + ' minutes avant la khutba' + (R.conseil ? ', le stationnement étant limité dans la rue.' : '.') });
    if (R.J) steps.push({ t: R.J, cls: 'key', n: 'Khutba', d: (lang ? 'En ' + R.L(lang) + (tr ? ', traduction : ' + tr : '') + '. ' : '') + 'Écoute en silence.' });
    steps.push({ t: '', cls: 'key', n: 'Prière de Jumu’a', d: 'Deux unités en congrégation, juste après la khutba.' });
    const weeks = R.list.slice(0, R.nombre);
    const kw = Math.min(st.kw, Math.max(0, weeks.length - 1));
    const w = weeks[kw] || null;
    const MODES = { 'Résumé imprimé à l’entrée': 'Quand une traduction est prévue, un résumé imprimé est disponible à l’entrée.',
      'Traduction orale': 'Quand une traduction est prévue, elle est faite à l’oral.', 'Écran': 'Quand une traduction est prévue, elle est affichée sur écran.' };
    const C = st.C, obj = C ? Number(C.objectif) || 0 : 0, rec = C ? Math.max(0, Number(C.recolte) || 0) : 0;
    const money = (n) => Math.round(n).toLocaleString('fr-CA') + ' $';
    const dl = R.left;
    return {
      menu: st.menu, menuStr: String(st.menu), toggleMenu: () => this.setState({ menu: !st.menu }),
      hasJ: !!R.J, J: R.J, hasArrive: !!R.arrive, arrive: R.arrive, hasLangue: !!lang, langue: lang,
      cdD: Math.floor(dl / 86400), cdH: p2(Math.floor(dl / 3600) % 24), cdM: p2(Math.floor(dl / 60) % 60), cdS: p2(dl % 60),
      cdLabel: R.during ? 'La khutba est en cours' : (R.isFri && !R.over ? 'Aujourd’hui, avant la khutba' : 'Prochain vendredi dans'),
      topLeft: R.isFri ? 'C’est vendredi aujourd’hui' : 'Prochain vendredi dans ' + Math.max(1, Math.ceil(dl / 86400)) + ' j',
      eyebrow: R.cap(R.fmt(R.F, { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })) + (R.hijri ? ' · ' + R.hijri : ''),
      hEyebrow: 'Horaires · ' + dLong(R.F), hDay: R.isFri ? 'Aujourd’hui, c’est' : 'Ce vendredi, c’est',
      hLead: (R.J ? 'La khutba commence à ' + R.J + ', suivie de la prière.' : 'La khutba est suivie de la prière.')
        + (R.av ? ' Arrivez ' + R.av + ' minutes à l’avance' + (R.conseil ? ' : le stationnement est limité.' : '.') : ''),
      tFajr: val(R.F, 'fajr') || '—', tLever: val(R.F, 'lever') || '—', tJum: R.J || '—', tAsr: val(R.F, 'asr') || '—',
      tMaghreb: val(R.F, 'maghreb') || '—', tIcha: val(R.F, 'isha') || '—',
      steps, hasAddr: R.conseil, mName: R.cap(R.fmt(R.F, { month: 'long', year: 'numeric' })), fris,
      sunna: SUN.map((s, i) => ({ n: s[0], d: s[1], p: String(!!st.sunna[i]), t: () => { const a = st.sunna.slice(); a[i] = !a[i]; this.setState({ sunna: a }); } })),
      sDone: done, sPct: Math.round(done / 8 * 100), sMsg: done === 8 ? 'Ma sha Allah, toutes les sunnas du jour !' : (8 - done) + ' gestes à faire encore aujourd’hui.',
      kahf: st.kahf.map((v, i) => ({ n: (i * 10 + 1) + '–' + Math.min(110, i * 10 + 10), p: String(v), t: () => { const a = st.kahf.slice(); a[i] = !a[i]; this.setState({ kahf: a }); } })),
      kPct: Math.round(kd / 11 * 100), kTxt: Math.min(110, kd * 10) + ' versets lus sur 110' + (kd === 11 ? ' · sourate terminée !' : ''),
      sal: st.sal, pingCls: 'ping' + (st.ping % 2), salaw: () => this.setState({ sal: st.sal + 1, ping: st.ping + 1 }),
      goals: [33, 100, 1000].map((n) => ({ n: 'Objectif ' + n, p: String(st.goal === n), pick: () => this.setState({ goal: n }) })),
      salGoalTxt: st.sal >= st.goal ? 'Objectif atteint, baraka Allahu fik !' : (st.goal - st.sal) + ' avant l’objectif de ' + st.goal,
      hasCamp: obj > 0, cRecolte: money(rec), cObjectif: money(obj), cPct: obj > 0 ? Math.min(100, Math.round(rec / obj * 100)) : 0,
      hasWeeks: weeks.length > 0, noWeeks: weeks.length === 0,
      kwLabel: w ? dLong(w.date) : '', kMain: w ? R.L(w.langue) : '', kTrad: w ? (R.trad(w) || 'aucune') : '',
      kPrev: () => this.setState({ kw: Math.max(0, kw - 1) }), kNext: () => this.setState({ kw: Math.min(weeks.length - 1, kw + 1) }),
      kWeeks: weeks.map((x, i) => ({ date: dLong(x.date), main: x.langue, trad: R.trad(x) || 'aucune', pressed: String(kw === i),
        bd: kw === i ? '#0F5F55' : '#DCE3DA', bg: kw === i ? '#E3F0EB' : '#FFFFFF', pick: () => this.setState({ kw: i }) })),
      kDate: dLong(R.F), hasKf: !!R.kf, noKf: !R.kf, kfMain: lang ? R.L(lang) : '', kfTrad: tr || 'aucune',
      hasImam: !!(R.kf && R.kf.imam), imam: R.kf ? R.kf.imam : '', hasMode: !!MODES[R.mode], kModeTxt: MODES[R.mode] || ''
    };
  }
"""


def set_logic(tpl):
    a = tpl.index('<script type="text/x-dc"')
    b = tpl.index('</script>', a)
    code = tpl[a:b]
    head = code[:code.index('class Component extends DCLogic {')]
    code = (head + 'class Component extends DCLogic {\n  constructor(props) {\n    super(props);\n'
            '    this.state = { now: Date.now(), menu: false, ready: false, H: {}, K: {}, C: null, byDate: {}, defs: {},\n'
            '      sunna: [false, false, false, false, false, false, false, false], kahf: [false, false, false, false, false, false, false, false, false, false, false],\n'
            '      sal: 0, goal: 100, ping: 0, kw: 0 };\n  }'
            + LOGIC + '}\n')
    return tpl[:a] + code + tpl[b:]


def header(tpl):
    tpl = tpl.replace('href="TH-Vendredi-Accueil.dc.html"', 'href="/"')
    tpl = tpl.replace('href="TH-Vendredi-Horaires.dc.html', 'href="/TH-Vendredi-Horaires.dc.html')
    tpl = tpl.replace('href="TH-Vendredi-Khutba.dc.html', 'href="/TH-Vendredi-Khutba.dc.html')
    for label in ('À propos', 'Services', 'Événements', 'Contact'):
        tpl = rep(tpl, f'<a href="#">{label}</a>', f'<a href="{NAV[label]}">{label}</a>', 2)
    tpl = rep(tpl, '<a class="btn btn-pri hide-m" href="#"', '<a class="btn btn-pri hide-m" href="/Dons.dc.html"')
    tpl = rep(tpl, '<a href="#" style="border:0;color:#8A6720">Sadaqa du vendredi</a>', '<a href="/Dons.dc.html" style="border:0;color:#8A6720">Sadaqa du vendredi</a>')
    tpl = rep(tpl, f'Jumu’a Moubarak · Khutba <strong style="color:{GOLD}">&nbsp;12:30&nbsp;</strong> · {{{{topLeft}}}}',
              'Jumu’a Moubarak' + sc_if('hasJ', f' · Khutba <strong style="color:{GOLD}">&nbsp;{{{{J}}}}&nbsp;</strong>', 'false') + ' · {{topLeft}}')
    return tpl


def glass(tpl):
    """Carte du compte à rebours (Accueil et Horaires) : heure, conseil d'arrivée et langue réels."""
    tpl = rep(tpl, f'<span style="font-size:40px;font-weight:800;color:{GOLD}">12:30</span>',
              sc_if('hasJ', f'<span style="font-size:40px;font-weight:800;color:{GOLD}">{{{{J}}}}</span>', 'false'))
    old = re.search(r'\n <div class="g3 tnum" style="margin-top:18px;gap:10px;font-size:14px">\n.*?\n </div>\n', tpl, re.S)
    assert old and '11:45' in old.group(0), 'détails de la carte introuvables'
    cell = '<div><span style="color:#CFE3DC">{0}</span><br><b style="font-size:20px{1}">{2}</b></div>'
    new = ('\n <div class="g3 tnum" style="margin-top:18px;gap:10px;font-size:14px">\n  '
           + sc_if('hasArrive', cell.format('Arriver avant', '', '{{arrive}}'), 'false')
           + sc_if('hasJ', cell.format('Khutba', ';color:' + GOLD, '{{J}}'), 'false')
           + sc_if('hasLangue', cell.format('Langue', '', '{{langue}}'), 'false')
           + '\n </div>\n')
    return tpl[:old.start()] + new + tpl[old.end():]


def footer(tpl):
    a = tpl.index('<footer class="ftr">')
    b = tpl.index('</footer>', a) + len('</footer>')
    f = tpl[a:b]
    logo = f[f.index('<div><div style="display:flex;align-items:center;gap:12px">'):f.index('\n    <p style="margin:14px 0 0">34, 37e Avenue')]
    lk = 'color:inherit;text-decoration:underline;text-underline-offset:3px'
    new = ('<footer class="ftr">\n <div class="wrap">\n  <div class="g4" style="gap:36px">\n   '
           + logo + '\n    <p style="margin:14px 0 0">34, 37e Avenue<br>Edmundston, NB E3V 3S2</p></div>\n'
           f'   <div><p style="margin:0 0 10px;font-weight:700;color:{GOLD}">Vendredi</p><p style="margin:0;line-height:2">'
           + sc_if('hasJ', 'Khutba et prière {{J}}<br>', 'false') + sc_if('hasArrive', 'Arriver avant {{arrive}}<br>', 'false')
           + f'<a href="/TH-Vendredi-Horaires.dc.html" style="{lk}">Horaires du vendredi</a><br>'
           f'<a href="/TH-Vendredi-Khutba.dc.html" style="{lk}">Langue de la khutba</a></p></div>\n'
           f'   <div><p style="margin:0 0 10px;font-weight:700;color:{GOLD}">Le site</p><p style="margin:0;line-height:2">'
           f'<a href="/" style="{lk}">Accueil</a> · <a href="/Horaires.dc.html" style="{lk}">Horaires</a> · <a href="/Services.dc.html" style="{lk}">Services</a><br>'
           f'<a href="/Evenements.dc.html" style="{lk}">Événements</a> · <a href="/Contact.dc.html" style="{lk}">Contact</a></p></div>\n'
           f'   <div><p style="margin:0 0 10px;font-weight:700;color:{GOLD}">Nous écrire</p><p style="margin:0;word-break:break-all">'
           f'<a href="mailto:{EMAIL}" style="{lk};overflow-wrap:anywhere">{EMAIL}</a></p><p class="ar" style="margin:14px 0 0;font-size:26px;color:{GOLD}">جمعة مباركة</p></div>\n'
           '  </div>\n'
           '  <p style="margin:44px 0 0;padding-top:22px;border-top:1px solid rgba(255,255,255,.18);font-size:14px">© 2026 Association Socio-Culturelle '
           'Islamique Louperivoise — Edmundston, Québec<a href="superadmin.html" rel="nofollow" style="float:right;color:#F3EAD8;opacity:.75;'
           'text-decoration:underline;text-underline-offset:3px;display:inline-block;padding:4px 0;margin-left:16px">Espace administration</a></p>\n'
           ' </div>\n</footer>')
    return tpl[:a] + new + tpl[b:]


def rappel_card(title, text):
    return ('<div class="card rv" style="background:#0F5F55;color:#fff;border-color:#0F5F55">'
            f'<p class="h3" style="color:{GOLD}">{title}</p><p style="margin:6px 0 16px;color:#D8E8E2">{text}</p>'
            f'<a class="btn" href="/N3-Rappel.dc.html" style="background:{GOLD};color:#0B3F38">Choisir mes rappels</a></div>')


BANNED = ['11:45', '12:20', '12:55', '13:05', '12:30', '06:30', '19:00', '142 500', 'href="#"', 'nom à confirmer', 'exemple',
          'Novembre 2026', '13 novembre', '1448', 'Thème saisonnier', 'Durée', 'PDF', 'à confirmer', 'remLabel', 'toggleRemind',
          'boîte à l’entrée', 'Résumé en', '{{delays}}']


def common(tpl):
    tpl = header(tpl)
    tpl = tpl.replace('Cochez au fil de la journée. La liste revient vide chaque vendredi.', 'Cochez au fil de la journée.')
    tpl = footer(tpl)
    return set_logic(tpl)


# ---------------------------------------------------------------- Accueil
def accueil(tpl):
    tpl = rep(tpl, f'<p class="eyebrow rise" style="color:{GOLD}">Vendredi 13 novembre 2026 · ٣ جمادى الآخرة ١٤٤٨</p>',
              f'<p class="eyebrow rise" style="color:{GOLD}">{{{{eyebrow}}}}</p>')
    tpl = glass(tpl)
    # Rappel : la vraie application Rappel de prière, au lieu d'un bouton qui ne faisait rien.
    tpl = resub(tpl, r'<div style="flex:1 1 320px"><p class="h3" style="color:#E7C27A">Rappel de la dernière heure</p>.*?</button>',
                '<div style="flex:1 1 320px"><p class="h3" style="color:#E7C27A">Rappels de prière</p><p style="margin:4px 0 0;color:#D8E8E2">'
                'Recevez une alerte sur ce téléphone avant la prière, dont Jumu’a.</p></div>\n'
                f'   <a class="btn" href="/N3-Rappel.dc.html" style="background:{GOLD};color:#0B3F38">Choisir mes rappels</a>')
    # Sadaqa : montants réels de la campagne, bouton vers la page des dons.
    tpl = rep(tpl, 'Chaque vendredi, la collecte va au projet de nouveau lieu. Par Interac ou dans la boîte à l’entrée.',
              'Votre don du vendredi soutient le projet de nouveau lieu de l’ASCIL.')
    tpl = resub(tpl, r'<p class="tnum" style="margin:0;display:flex;justify-content:space-between;align-items:baseline">.*?<div class="bar" style="margin-top:12px"><i style="width:41%"></i></div>',
                lambda m: sc_if('hasCamp', '<p class="tnum" style="margin:0;display:flex;justify-content:space-between;align-items:baseline;gap:12px;flex-wrap:wrap">'
                                '<span class="serif" style="font-size:38px;font-weight:700;color:#0F5F55">{{cRecolte}}</span><span class="muted">sur {{cObjectif}}</span></p>'
                                '<div class="bar" style="margin-top:12px"><i style="width:{{cPct}}%"></i></div>', 'false'))
    tpl = rep(tpl, '<a class="btn btn-pri bm" href="#" style="margin-top:20px">', '<a class="btn btn-pri bm" href="/Dons.dc.html" style="margin-top:20px">')
    tpl = common(tpl)
    check(tpl, BANNED)
    return tpl


# ---------------------------------------------------------------- Horaires
def horaires(tpl):
    tpl = rep(tpl, f'<p class="eyebrow rise" style="color:{GOLD}">Horaires · Vendredi 13 novembre</p>', f'<p class="eyebrow rise" style="color:{GOLD}">{{{{hEyebrow}}}}</p>')
    tpl = rep(tpl, 'style="margin-top:16px;color:#FFFBEF">Aujourd’hui, c’est <span', 'style="margin-top:16px;color:#FFFBEF">{{hDay}} <span')
    tpl = rep(tpl, 'La khutba commence à 12:30, suivie de la prière. Le stationnement est limité : arrivez 15 minutes à l’avance.', '{{hLead}}')
    tpl = glass(tpl)
    # Prières du jour : heures du tableau (défauts de l'Accueil, calcul local pour Lever, Asr, Maghreb).
    a = tpl.index('<div class="today-big tnum">')
    b = tpl.index('\n  </div>', a)
    vals = iter(['{{tFajr}}', '{{tLever}}', '{{tJum}}', '{{tAsr}}', '{{tMaghreb}}', '{{tIcha}}'])
    blk, n = re.subn(r'>(?:\d\d:\d\d|—)</p></div>', lambda m: '>' + next(vals) + '</p></div>', tpl[a:b])
    assert n == 6, n
    tpl = tpl[:a] + blk + tpl[b:]
    # Déroulé : seulement ce que l'association a saisi (arrivée conseillée, khutba, prière).
    tpl = resub(tpl, r'<ol class="tl2">.*?</ol>',
                '<ol class="tl2"><sc-for list="{{steps}}" as="x" hint-placeholder-count="3"><li class="rv {{x.cls}}">'
                '<span class="tnum" style="font-weight:800;color:#0F5F55">{{x.t}}</span><span class="dot" aria-hidden="true"></span>'
                '<span><b style="display:block;font-size:18px;color:#12302A">{{x.n}}</b><span class="muted">{{x.d}}</span></span></li></sc-for></ol>')
    tpl = rep(tpl, '<p class="muted" style="margin:8px 0 0">Stationnement limité dans la rue : covoiturez ou venez à pied. Espace pour les femmes : à confirmer.</p>',
              sc_if('hasAddr', '<p class="muted" style="margin:8px 0 0">Stationnement limité dans la rue : covoiturez ou venez à pied.</p>', 'true'))
    tpl = resub(tpl, r'<div class="card rv" style="background:#0F5F55;color:#fff;border-color:#0F5F55"><p class="h3" style="color:#E7C27A">Me rappeler chaque vendredi</p>.*?</button></div>',
                lambda m: rappel_card('Me rappeler chaque vendredi', 'Une alerte avant la prière de Jumu’a, sur ce téléphone.'))
    # Vendredis du mois : liste (heures et langue réelles), pas de PDF.
    tpl = rep(tpl, '<p class="eyebrow">Novembre 2026</p>', '<p class="eyebrow">{{mName}}</p>')
    tpl = resub(tpl, r'<a class="btn btn-line" href="#">(?:(?!</a>).)*Tableau du mois \(PDF\)</a>', '')
    row = ('<div class="tnum" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(min(150px,100%),1fr));gap:6px 18px;align-items:center;'
           'padding:14px 18px;border-bottom:1px solid #DCE3DA;background:{{f.bg}}">'
           '<span><b>{{f.d}}</b>' + sc_if('f.isToday', ' <span class="chip" style="background:#0F5F55;color:#fff;padding:2px 10px;font-size:12px;margin-left:6px">Aujourd’hui</span>', 'false')
           + '</span><span>Fajr {{f.fajr}}</span><span style="font-weight:800;color:#0F5F55">Jumu’a {{f.jum}}</span><span>Icha {{f.isha}}</span>'
           '<span class="muted">{{f.lang}}</span></div>')
    tpl = resub(tpl, r'<div class="card rv" style="padding:6px 12px;overflow-x:auto"><sc-raw-table.*?</sc-raw-table></div>',
                lambda m: '<div class="card rv" style="padding:0;overflow:hidden"><sc-for list="{{fris}}" as="f" hint-placeholder-count="4">' + row + '</sc-for></div>')
    tpl = resub(tpl, r'<p class="muted" style="margin:12px 0 0;font-size:13px">Langues de la khutba : exemple.*?<a href="/?TH-Vendredi-Khutba\.dc\.html">Voir la page Khutba</a></p>',
                '<p class="muted" style="margin:12px 0 0;font-size:14px">Heures du tableau du mois de l’ASCIL. <a href="/TH-Vendredi-Khutba.dc.html">Langue de la khutba</a></p>')
    tpl = common(tpl)
    check(tpl, BANNED)
    return tpl


# ---------------------------------------------------------------- Khutba
def khutba(tpl):
    # Sélecteur de vendredi : seulement les vendredis saisis dans Horaires → Langue de la khutba.
    tpl = resub(tpl, r'(<div class="wk rise d2".*?\n  </div>\n)', lambda m: sc_if('hasWeeks', m.group(1), 'false')
                + sc_if('noWeeks', '<p class="lead rise d2" style="margin:24px auto 0;color:#D8E8E2;max-width:560px">La langue de la khutba sera indiquée ici dès qu’elle est fixée par l’association.</p>', 'true'))
    # Carte « Ce vendredi » (au lieu du thème et du résumé d'exemple).
    tpl = resub(tpl, r'<div class="card rv" style="padding:36px"><p class="eyebrow">Thème du jour · exemple</p>.*?</a></div></div>',
                '<div class="card rv" style="padding:36px"><p class="eyebrow">Ce vendredi</p><h2 id="k-t" class="h2" style="margin-top:12px;color:#0F5F55">{{kDate}}</h2>'
                + sc_if('hasKf', '<p class="lead" style="margin-top:12px">Khutba en {{kfMain}}. Traduction : {{kfTrad}}.</p>', 'false')
                + sc_if('noKf', '<p class="lead" style="margin-top:12px">La langue de ce vendredi n’est pas encore indiquée.</p>', 'true')
                + sc_if('hasJ', '<p class="muted" style="margin:16px 0 0">Khutba et prière à {{J}}' + sc_if('hasArrive', ' · arriver avant {{arrive}}', 'false') + '</p>', 'false')
                + sc_if('hasImam', '<p class="muted" style="margin:6px 0 0">Imam : {{imam}}</p>', 'false')
                + '<div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:22px"><a class="btn btn-pri" href="/TH-Vendredi-Horaires.dc.html">Horaires du vendredi</a></div></div>')
    tpl = rep(tpl, '<p class="eyebrow">Les prochains vendredis · exemple</p>', '<p class="eyebrow">Langue de la khutba</p>')
    tpl = rep(tpl, '>La langue alterne chaque semaine</h2>', '>Les prochains vendredis</h2>')
    tpl = resub(tpl, r'(<div class="g4">\n   <sc-for list="\{\{kWeeks\}\}".*?</sc-for>\n  </div>)', lambda m: sc_if('hasWeeks', m.group(1), 'false')
                + sc_if('noWeeks', '<p class="muted" style="margin:0">Aucun vendredi n’est encore indiqué.</p>', 'true'))
    tpl = rep(tpl, '<p class="muted" style="margin:18px 0 0">Une feuille résumé en français, en arabe et en anglais est disponible à l’entrée.</p>',
              sc_if('hasMode', '<p class="muted" style="margin:18px 0 0">{{kModeTxt}}</p>', 'false'))
    tpl = common(tpl)
    check(tpl, BANNED)
    return tpl


if __name__ == '__main__':
    build(ROOT / 'TH-Vendredi-Accueil.dc.html', 'vendredi-accueil.tpl.html', accueil, 'Jumu’a Moubarak — ASCIL')
    build(ROOT / 'TH-Vendredi-Horaires.dc.html', 'vendredi-horaires.tpl.html', horaires, 'Horaires du vendredi — ASCIL')
    build(ROOT / 'TH-Vendredi-Khutba.dc.html', 'vendredi-khutba.tpl.html', khutba, 'Khutba du vendredi — ASCIL')
    print('thème du vendredi : TH-Vendredi-Accueil, Horaires et Khutba reconstruites depuis la maquette, branchées sur les vraies données')
