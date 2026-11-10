"""Étape A1 : thèmes saisonniers Aïd al-Fitr et Aïd al-Adha (maquettes « event templates »), sur le modèle du Ramadan.

Quatre pages, reconstruites à chaque passage depuis les maquettes d'origine gardées dans scripts/maquettes/ :
  - TH-Fitr-Accueil.dc.html / TH-Adha-Accueil.dc.html : l'Accueil pendant l'Aïd. Quand « Site entier → Mode du
    site » est sur Aïd al-Fitr ou Aïd al-Adha (dans ses dates si le changement automatique est coché), le serveur
    (functions/_middleware.js) la sert à la place de l'Accueil normal, à la même adresse ;
  - TH-Fitr-Page.dc.html / TH-Adha-Page.dc.html : la page de la fête (lien « Aïd al-… » du menu pendant la saison).

Vraies données uniquement :
  - date et heure de la prière, lieu et itinéraire : Horaires → Aïd (clé horaires, champs aid.*). Sans date
    saisie, la date vient du Mode du site : Aïd al-Fitr = premier jour de la période ; Aïd al-Adha = premier jour,
    ou dixième jour si la période couvre les dix jours de Dhou al-Hijja (9 jours ou plus) ;
  - montant de la zakat al-Fitr : carte « Les prières de l'Aïd » de Services (clé services) ;
  - année de l'hégire, jour d'Arafat, jours de Tachriq : calculés depuis la date de l'Aïd.
Les blocs de la maquette sans vraie donnée (programme heure par heure, takbirat à heure fixe, café, coin des
enfants, photo, bénévoles, udhiya et ses prix, iftar d'Arafat, pèlerins, questions fréquentes, agenda) ne sont
pas publiés : ils pourront revenir avec une rubrique du panneau, remplis par l'association.
Rappels religieux généraux (gestes de la Sunna, takbirat, vœux « Taqabbal Allahu minna wa minkum ») : gardés.
Ordre : juste après wire_ramadan.py (même fonctionnement). Idempotent.
"""
import re, pathlib, importlib.util

HERE = pathlib.Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location('wire_ramadan', HERE / 'wire_ramadan.py')
W = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(W)
ROOT, rep, resub, sc_if, build, EMAIL, NAV = W.ROOT, W.rep, W.resub, W.sc_if, W.build, W.EMAIL, W.NAV

# ---------------------------------------------------------------------------
# Logique commune (données réelles). __KIND__ = 'fitr' ou 'adha'.
# ---------------------------------------------------------------------------
LOAD_JS = r"""
  componentDidMount() {
    this.t = setInterval(() => this.setState({ now: Date.now() }), 1000);
    const get = (u) => fetch(u).then((r) => (r.ok ? r.json() : null)).catch(() => null);
    Promise.all([get('/api/settings/season'), get('/api/settings/horaires'), get('/api/settings/services')]).then(([se, ho, sv]) => {
      const S = (se && se.ok && se.settings) || {};
      const A = (ho && ho.ok && ho.settings && ho.settings.aid) || {};
      const items = (sv && sv.ok && sv.settings && Array.isArray(sv.settings.items)) ? sv.settings.items : [];
      const card = items.find((x) => x && x.kind === 'aid' && x.on !== false);
      this.setState({ S, A, zakat: card && Number(card.zakat) > 0 ? Number(card.zakat) : 0, ready: true });
    });
  }
  componentWillUnmount() { clearInterval(this.t); }
  aid() {
    const KIND = '__KIND__';
    const st = this.state, S = st.S || {}, A = st.A || {}, p2 = (n) => String(n).padStart(2, '0');
    const ok = /^\d{4}-\d\d-\d\d$/, T = /^\d\d:\d\d$/;
    const utc = (d) => Date.UTC(+d.slice(0, 4), +d.slice(5, 7) - 1, +d.slice(8, 10));
    const addDays = (d, n) => new Date(utc(d) + n * 86400000).toISOString().slice(0, 10);
    const fmt = (d, o) => { try { return new Intl.DateTimeFormat('fr-CA', Object.assign({ timeZone: 'UTC' }, o)).format(new Date(utc(d))); } catch (e) { return d; } };
    const cap = (s) => s ? s.charAt(0).toUpperCase() + s.slice(1) : s;
    const mode = KIND === 'fitr' ? 'aid_fitr' : 'aid_adha';
    let date = KIND === 'fitr' ? A.fitrDate : A.adhaDate;
    if (!ok.test(date || '') && S.mode === mode && ok.test(S.from || '')) {
      date = S.from;
      if (KIND === 'adha' && ok.test(S.to || '') && Math.round((utc(S.to) - utc(S.from)) / 86400000) >= 8) date = addDays(S.from, 9);
    }
    const has = ok.test(date || '');
    const heure = T.test((KIND === 'fitr' ? A.fitrHeure : A.adhaHeure) || '') ? (KIND === 'fitr' ? A.fitrHeure : A.adhaHeure) : '';
    const lieu = A.on !== false && A.lieu ? String(A.lieu) : '';
    const itin = A.on !== false && /^https?:\/\//i.test(A.itineraire || '') ? A.itineraire : '';
    let hy = '';
    if (has) {
      try {
        const yp = new Intl.DateTimeFormat('fr-CA-u-ca-islamic-umalqura', { year: 'numeric', timeZone: 'UTC' }).formatToParts(new Date(utc(date))).find((x) => x.type === 'year');
        hy = yp ? String(yp.value).replace(/\D/g, '') : '';
      } catch (e) { hy = ''; }
    }
    // Compte à rebours jusqu'à la prière (date + heure, heure de Edmundston).
    let left = -1;
    if (has && heure) {
      const guess = Date.UTC(+date.slice(0, 4), +date.slice(5, 7) - 1, +date.slice(8, 10), +heure.slice(0, 2), +heure.slice(3, 5));
      let off = 0;
      try {
        const pp = {};
        new Intl.DateTimeFormat('en-US', { timeZone: 'America/Moncton', hourCycle: 'h23', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
          .formatToParts(new Date(guess)).forEach((x) => { pp[x.type] = x.value; });
        off = Date.UTC(+pp.year, +pp.month - 1, +pp.day, +pp.hour % 24, +pp.minute) - guess;
      } catch (e) { off = 0; }
      left = Math.floor((guess - off - st.now) / 1000);
    }
    const dl = Math.max(0, left);
    const dateLong = has ? cap(fmt(date, { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })) : '';
    return { has, date, heure, lieu, itin, hy, dateLong, fmt, cap, addDays, p2,
      hasCd: left > 0, dD: Math.floor(dl / 86400), dH: p2(Math.floor(dl / 3600) % 24), dM: p2(Math.floor(dl / 60) % 60), dS: p2(dl % 60),
      topPrayer: heure ? ' · Prière de l’Aïd' : '', topLieu: lieu ? ' · ' + lieu : '' };
  }
"""

COMMON_VALS = """      menu: st.menu, menuStr: String(st.menu), toggleMenu: () => this.setState({ menu: !st.menu }),
      hasTime: !!R.heure, heure: R.heure, hasLieu: !!R.lieu, lieu: R.lieu, hasItin: !!R.itin, itin: R.itin,
      hasCd: R.hasCd, dD: R.dD, dH: R.dH, dM: R.dM, dS: R.dS, hasDate: R.has,
"""

FITR_VALS = r"""
  renderVals() {
    const st = this.state, R = this.aid();
    const SUN = [['Le ghusl', 'Grande ablution avant de sortir.'], ['Les beaux habits', 'Ses vêtements les plus propres, un parfum pour les hommes.'],
      ['Quelques dattes', 'En nombre impair, avant de partir.'], ['La zakat al-Fitr', 'Versée avant la prière.'],
      ['Les takbirat en chemin', 'À voix basse, jusqu’à l’arrivée.'], ['Un autre chemin au retour', 'Pour saluer plus de monde.']];
    const sun = st.sunna || [];
    const done = sun.filter(Boolean).length;
    const zN = st.zN || 1;
    return {
""" + COMMON_VALS + r"""      eyebrow: 'Aïd al-Fitr' + (R.hy ? ' ' + R.hy : '') + (R.has ? ' · ' + R.dateLong : ''),
      lead: R.has ? R.dateLong + ', selon l’annonce de la TCOM.' + (R.lieu ? ' Prière de l’Aïd : ' + R.lieu + '.' : '') : 'La date de l’Aïd sera annoncée ici dès qu’elle est confirmée.',
      hasZakat: st.zakat > 0, zakat: st.zakat, zN, zTotal: (zN * st.zakat) + ' $',
      zMinus: () => this.setState({ zN: Math.max(1, zN - 1) }), zPlus: () => this.setState({ zN: Math.min(20, zN + 1) }),
      sunna: SUN.map((s, i) => ({ n: s[0], d: s[1], p: String(!!sun[i]), t: () => { const a = sun.slice(); a[i] = !a[i]; this.setState({ sunna: a }); } })),
      sDone: done, sPct: Math.round(done / 6 * 100)
    };
  }
"""

ADHA_VALS = r"""
  renderVals() {
    const st = this.state, R = this.aid();
    const d0 = R.has ? R.addDays(R.date, -9) : '';
    const short = (d) => R.fmt(d, { day: 'numeric', month: 'short' });
    const days = [];
    if (R.has) {
      for (let k = 1; k <= 13; k++) {
        const d = R.addDays(d0, k - 1);
        days.push({ n: k, cls: 'day' + (k === 9 ? ' arf' : k === 10 ? ' eid' : k > 10 ? ' tq' : ''),
          t: k === 9 ? 'Arafat' : k === 10 ? 'Aïd' : k > 10 ? 'Tachriq' : short(d), title: R.cap(R.fmt(d, { weekday: 'long', day: 'numeric', month: 'long' })) });
      }
    }
    const arafat = R.has ? R.fmt(R.addDays(R.date, -1), { weekday: 'long', day: 'numeric', month: 'long' }) : '';
    const prog = R.has ? [
      { when: short(d0) + ' – ' + short(R.addDays(d0, 7)), c: '#5E4D3C', t: 'Les premiers jours', d: 'Dhikr, jeûne volontaire, bonnes actions.' },
      { when: R.cap(R.fmt(R.addDays(R.date, -1), { weekday: 'short', day: 'numeric', month: 'short' })), c: '#B5573A', t: 'Jour d’Arafat', d: 'Jeûne recommandé pour ceux qui ne sont pas en pèlerinage.' },
      { when: R.cap(R.fmt(R.date, { weekday: 'short', day: 'numeric', month: 'short' })), c: '#1B4D3A', t: 'Aïd al-Adha',
        d: (R.heure ? 'Prière de l’Aïd à ' + R.heure : 'Prière de l’Aïd') + (R.lieu ? ' · ' + R.lieu : '') + '.' },
      { when: short(R.addDays(R.date, 1)) + ' – ' + short(R.addDays(R.date, 3)), c: '#5E4D3C', t: 'Jours de Tachriq', d: 'Takbirat après chaque prière.' }
    ] : [];
    return {
""" + COMMON_VALS + r"""      eyebrow: 'Aïd al-Adha' + (R.hy ? ' ' + R.hy : '') + (R.has ? ' · ' + R.dateLong : ''),
      hijja: 'Dhou al-Hijja' + (R.hy ? ' ' + R.hy : ''),
      days, arafat, arafatCap: R.cap(arafat), prog,
      lead: R.has ? 'Du ' + R.fmt(d0, { weekday: 'long', day: 'numeric', month: 'long' }) + ' au ' + R.fmt(R.date, { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })
        + ', selon l’annonce de la TCOM.' + (R.lieu ? ' Prière de l’Aïd : ' + R.lieu + '.' : '') : 'Les dates de l’Aïd seront annoncées ici dès qu’elles sont confirmées.'
    };
  }
"""


def set_logic(tpl, kind, vals):
    a = tpl.index('<script type="text/x-dc"')
    b = tpl.index('</script>', a)
    code = tpl[a:b]
    head = code[:code.index('class Component extends DCLogic {')]
    code = (head + 'class Component extends DCLogic {\n  constructor(props) {\n    super(props);\n'
            '    this.state = { now: Date.now(), menu: false, ready: false, S: {}, A: {}, zakat: 0, zN: 1, sunna: [false, false, false, false, false, false] };\n  }'
            + LOAD_JS.replace('__KIND__', kind) + vals + '}\n')
    return tpl[:a] + code + tpl[b:]


def header(tpl, slug, name):
    tpl = tpl.replace(f'href="TH-{slug}-Accueil.dc.html"', 'href="/"')
    tpl = tpl.replace(f'href="TH-{slug}-Page.dc.html', f'href="/TH-{slug}-Page.dc.html')
    for label, href in NAV.items():
        tpl = rep(tpl, f'<a href="#">{label}</a>', f'<a href="{href}">{label}</a>', 2)
    tpl = rep(tpl, '<a class="btn btn-pri hide-m" href="#"', '<a class="btn btn-pri hide-m" href="/Dons.dc.html"')
    tpl = resub(tpl, r'<a href="#" (style="border:0;color:#[0-9A-Fa-f]{6}")>Faire un don</a>', r'<a href="/Dons.dc.html" \1>Faire un don</a>')
    # Bandeau du haut : heure et lieu réels, ou rien.
    tpl = resub(tpl, r'(<span class="live" aria-hidden="true"></span>)(Aïd(?: al-Adha)? Moubarak) · Prière(?: de l’Aïd)? <strong style="color:(#[0-9A-Fa-f]{6})">&nbsp;\d+:\d\d&nbsp;</strong> · 15 rue Frontenac',
                lambda m: m.group(1) + m.group(2) + sc_if('hasTime', f' · Prière de l’Aïd <strong style="color:{m.group(3)}">&nbsp;{{{{heure}}}}&nbsp;</strong>', 'false')
                + sc_if('hasLieu', ' · {{lieu}}', 'false'))
    return tpl


def footer(tpl, slug, name, ar):
    a = tpl.index('<footer class="ftr">')
    b = tpl.index('</footer>', a) + len('</footer>')
    f = tpl[a:b]
    color = re.search(r'<p style="margin:0 0 10px;font-weight:700;color:(#[0-9A-Fa-f]{6})">', f).group(1)
    logo = f[f.index('<div><div style="display:flex;align-items:center;gap:12px">'):f.index('\n    <p style="margin:14px 0 0">34, 37e Avenue')]
    lk = 'color:inherit;text-decoration:underline;text-underline-offset:3px'
    new = ('<footer class="ftr">\n <div class="wrap">\n  <div class="g4" style="gap:36px">\n   '
           + logo + '\n    <p style="margin:14px 0 0">34, 37e Avenue<br>Edmundston, NB E3V 3S2</p></div>\n'
           f'   <div><p style="margin:0 0 10px;font-weight:700;color:{color}">{name}</p><p style="margin:0;line-height:2">'
           + sc_if('hasTime', 'Prière de l’Aïd {{heure}}<br>', 'false') + sc_if('hasLieu', '{{lieu}}<br>', 'false')
           + f'<a href="/TH-{slug}-Page.dc.html" style="{lk}">La journée de l’Aïd</a><br><a href="/Horaires.dc.html" style="{lk}">Horaires du mois</a></p></div>\n'
           f'   <div><p style="margin:0 0 10px;font-weight:700;color:{color}">Le site</p><p style="margin:0;line-height:2">'
           f'<a href="/" style="{lk}">Accueil</a> · <a href="/Horaires.dc.html" style="{lk}">Horaires</a> · <a href="/Services.dc.html" style="{lk}">Services</a><br>'
           f'<a href="/Evenements.dc.html" style="{lk}">Événements</a> · <a href="/Contact.dc.html" style="{lk}">Contact</a></p></div>\n'
           f'   <div><p style="margin:0 0 10px;font-weight:700;color:{color}">Nous écrire</p><p style="margin:0;word-break:break-all">'
           f'<a href="mailto:{EMAIL}" style="{lk};overflow-wrap:anywhere">{EMAIL}</a></p><p class="ar" style="margin:14px 0 0;font-size:26px;color:{color}">{ar}</p></div>\n'
           '  </div>\n'
           '  <p style="margin:44px 0 0;padding-top:22px;border-top:1px solid rgba(255,255,255,.18);font-size:14px">© 2026 Association Socio-Culturelle '
           'Islamique Louperivoise — Edmundston, Québec<a href="superadmin.html" rel="nofollow" style="float:right;color:#F3EAD8;opacity:.75;'
           'text-decoration:underline;text-underline-offset:3px;display:inline-block;padding:4px 0;margin-left:16px">Espace administration</a></p>\n'
           ' </div>\n</footer>')
    return tpl[:a] + new + tpl[b:]


def section(tpl, label):
    """(début, fin) de la section dont aria-labelledby vaut label."""
    k = tpl.index(f'aria-labelledby="{label}"')
    a = tpl.rindex('<section', 0, k)
    return a, tpl.index('</section>', k) + len('</section>')


def drop(tpl, label):
    a, b = section(tpl, label)
    return tpl[:a] + tpl[b:]


def wrap(tpl, label, cond):
    a, b = section(tpl, label)
    return tpl[:a] + sc_if(cond, tpl[a:b]) + tpl[b:]


def svg_after(tpl, marker):
    """Premier <svg>…</svg> qui suit marker (icônes reprises de la maquette)."""
    k = tpl.index(marker)
    a = tpl.index('<svg', k)
    return tpl[a:tpl.index('</svg>', a) + len('</svg>')]


def check(tpl, words):
    body = tpl.split('<script type="text/x-dc"')[0]
    for w in words:
        assert w not in body, f'reste de la maquette : {w!r}'


BANNED = ['8:00', '8:30', '7 h 30', '1448', '2027', 'mars', ' mai', '15 $', '15 rue Frontenac', 'href="#"', 'Mouton', 'bovin',
          'Thème saisonnier', 'Café et douceurs', 'Coin des enfants', 'Bénévoles', 'Nos pèlerins', 'Iftar partagé', 'Halaqa']


# ---------------------------------------------------------------- Aïd al-Fitr
def fitr_accueil(tpl):
    tpl = header(tpl, 'Fitr', 'Aïd al-Fitr')
    tpl = rep(tpl, '<p class="eyebrow rise" style="color:#B5832A">Aïd al-Fitr 1448 · Mercredi 10 mars 2027</p>', '<p class="eyebrow rise" style="color:#B5832A">{{eyebrow}}</p>')
    tpl = rep(tpl, 'Après un mois de jeûne, place à la joie. Rejoignez la communauté pour la prière de l’Aïd, puis pour le café et les douceurs.',
              'Après un mois de jeûne, place à la joie. Rejoignez la communauté pour la prière de l’Aïd.')
    tpl = resub(tpl, r'(<a class="btn btn-pri bm" href="/TH-Fitr-Page\.dc\.html">(?:(?!</a>).)*?)Programme de l’Aïd</a>', r'\1La journée de l’Aïd</a>')
    tpl = resub(tpl, r'<a class="btn btn-line bm" href="#">((?:(?!</a>).)*?)Itinéraire vers la salle</a>',
                lambda m: sc_if('hasItin', f'<a class="btn btn-line bm" href="{{{{itin}}}}" target="_blank" rel="noopener">{m.group(1)}Itinéraire vers la salle</a>', 'false'))
    # Carte de la prière : heure et lieu réels, compte à rebours seulement si date et heure sont fixées.
    tpl = rep(tpl, '<p class="serif tnum" style="margin:6px 0 0;text-align:center;font-size:76px;font-weight:700;line-height:1;color:#F2C66D">8:00</p>',
              sc_if('hasTime', '<p class="serif tnum" style="margin:6px 0 0;text-align:center;font-size:76px;font-weight:700;line-height:1;color:#F2C66D">{{heure}}</p>', 'false')
              + sc_if('noTime', '<p style="margin:12px 0 0;text-align:center;font-size:18px;font-weight:700">L’heure sera annoncée ici dès qu’elle est fixée.</p>', 'true'))
    tpl = rep(tpl, '<p style="margin:8px 0 22px;text-align:center">Takbirat dès 7 h 30 · Salle louée, 15 rue Frontenac</p>',
              sc_if('hasLieu', '<p style="margin:8px 0 22px;text-align:center">{{lieu}}</p>', 'false'))
    tpl = resub(tpl, r'(<div class="tnum" style="display:grid;grid-template-columns:repeat\(4,minmax\(0,1fr\)\);gap:8px;text-align:center" role="timer".*?</div>\n     </div>)',
                lambda m: sc_if('hasCd', m.group(1), 'false'))
    # Zakat al-Fitr : montant de la carte Aïd (Services). Pas de bouton « Verser » (aucune page de versement dédiée).
    tpl = rep(tpl, '15 $ par personne du foyer, enfants compris.', '{{zakat}} $ par personne du foyer, enfants compris.')
    tpl = resub(tpl, r'\n  <a class="btn" href="#" style="background:#F2C66D;color:#1E2B26">Verser</a>', '')
    tpl = wrap(tpl, 'f-z', 'hasZakat')
    # Gestes de la Sunna : rappel général, la liste n'est pas gardée (aucune promesse de mémoire).
    tpl = rep(tpl, 'Cochez au fur et à mesure : la liste reste sur votre téléphone.', 'Cochez au fur et à mesure.')
    tpl = drop(tpl, 'f-f')                     # « On fête ensemble » : exemples
    tpl = resub(tpl, r'\n\s*<a class="btn" href="#" style="background:#fff;color:#0E4D3C;position:relative">(?:(?!</a>).)*Partager les vœux</a>', '')
    tpl = footer(tpl, 'Fitr', 'Aïd al-Fitr', 'عيد مبارك')
    tpl = set_logic(tpl, 'fitr', FITR_VALS.replace("hasTime: !!R.heure,", "hasTime: !!R.heure, noTime: !R.heure,"))
    check(tpl, BANNED)
    return tpl


def fitr_page(tpl):
    tpl = header(tpl, 'Fitr', 'Aïd al-Fitr')
    tpl = rep(tpl, '>Programme · Aïd al-Fitr 1448</p>', '>{{eyebrow}}</p>')
    tpl = rep(tpl, 'Mercredi 10 mars 2027, selon l’annonce de la TCOM. Prière à la salle louée du 15 rue Frontenac, plus grande que la mosquée.', '{{lead}}')
    tpl = resub(tpl, r'<a class="btn btn-pri bm" href="#">((?:(?!</a>).)*?)Itinéraire</a>',
                lambda m: sc_if('hasItin', f'<a class="btn btn-pri bm" href="{{{{itin}}}}" target="_blank" rel="noopener">{m.group(1)}Itinéraire</a>', 'false'))
    tpl = resub(tpl, r'<a class="btn btn-line bm" href="#">(?:(?!</a>).)*Ajouter à mon agenda</a>', '')
    # Le jour de l'Aïd : prière (heure, lieu, itinéraire) et zakat al-Fitr. Le « heure par heure » de la maquette est retiré.
    a, b = section(tpl, 'fe-p')
    sec = tpl[a:b]
    pin = svg_after(sec, '<div class="card rv"><span class="ib">')
    arrow = svg_after(sec, 'Ouvrir dans Google Maps')
    zak = sec[sec.index('<div class="card rv" style="background:#0E6B4F'):sec.index('{{zTotal}}</p></div></div>') + len('{{zTotal}}</p></div></div>')]
    zak = zak.replace('15 $ par personne, avant la prière.', '{{zakat}} $ par personne du foyer, avant la prière.')
    new = ('<section class="sec" aria-labelledby="fe-p">\n <div class="wrap">\n'
           '  <p class="eyebrow" style="color:#B5832A">Le jour de l’Aïd</p><h2 id="fe-p" class="h2" style="margin-top:12px;margin-bottom:30px;color:#0E4D3C">La prière de l’Aïd</h2>\n'
           '  <div class="g2" style="align-items:start">\n'
           f'   <div class="card rv"><span class="ib">{pin}</span>'
           '<p class="h3" style="margin-top:14px;color:#0E4D3C">Prière de l’Aïd</p>'
           + sc_if('hasTime', '<p class="serif tnum" style="margin:6px 0 0;font-size:56px;font-weight:700;line-height:1;color:#D9A441">{{heure}}</p>', 'false')
           + sc_if('noTime', '<p class="muted" style="margin:8px 0 0">L’heure sera annoncée ici dès qu’elle est fixée.</p>', 'true')
           + sc_if('hasLieu', '<p style="margin:12px 0 0;font-weight:700">{{lieu}}</p>', 'false')
           + sc_if('hasCd', '<p class="tnum muted" style="margin:10px 0 0" role="timer">Dans {{dD}} j {{dH}} h {{dM}} min</p>', 'false')
           + sc_if('hasItin', f'<a class="link" href="{{{{itin}}}}" target="_blank" rel="noopener" style="margin-top:14px;color:#0E6B4F">Ouvrir l’itinéraire {arrow}</a>', 'false')
           + '</div>\n   ' + sc_if('hasZakat', zak) + '\n  </div>\n </div>\n</section>')
    tpl = tpl[:a] + new + tpl[b:]
    tpl = drop(tpl, 'fe-b')                    # bénévoles : exemple
    tpl = drop(tpl, 'fe-f')                    # questions : propres à la maquette
    tpl = footer(tpl, 'Fitr', 'Aïd al-Fitr', 'عيد مبارك')
    tpl = set_logic(tpl, 'fitr', FITR_VALS.replace("hasTime: !!R.heure,", "hasTime: !!R.heure, noTime: !R.heure,"))
    check(tpl, BANNED)
    return tpl


# ---------------------------------------------------------------- Aïd al-Adha
def adha_accueil(tpl):
    tpl = header(tpl, 'Adha', 'Aïd al-Adha')
    # Séparateurs de la bande des takbirat : petit losange dessiné en CSS (pas de pictogramme).
    tpl = re.sub(r'<span aria-hidden="true" style="color:#C9973F">\u2726</span>',
                 '<span aria-hidden="true" style="display:inline-block;inline-size:8px;block-size:8px;background:#C9973F;transform:rotate(45deg)"></span>', tpl)
    tpl = rep(tpl, '<p class="eyebrow rise" style="color:#7A3A22">Aïd al-Adha 1448 · Dimanche 16 mai 2027</p>', '<p class="eyebrow rise" style="color:#7A3A22">{{eyebrow}}</p>')
    tpl = resub(tpl, r'\n\s*<a class="btn btn-line bm" href="/TH-Adha-Page\.dc\.html#udhiya".*?Réserver une udhiya</a>', '')
    # Les dix jours : dates calculées depuis la date de l'Aïd (10 Dhou al-Hijja).
    tpl = rep(tpl, '<p class="eyebrow" style="color:#B5573A">Dhou al-Hijja 1448</p>', '<p class="eyebrow" style="color:#B5573A">{{hijja}}</p>')
    tpl = rep(tpl, ' (samedi 15 mai), takbirat', ' ({{arafat}}), takbirat')
    tpl = resub(tpl, r'<div class="days rv tnum">.*?</div></div>\n',
                '<div class="days rv tnum"><sc-for list="{{days}}" as="d" hint-placeholder-count="13"><div class="{{d.cls}}" title="{{d.title}}"><b>{{d.n}}</b><span>{{d.t}}</span></div></sc-for></div>\n')
    tpl = wrap(tpl, 'a-t', 'hasDate')
    # Cartes : prière (heure, lieu, compte à rebours) et jour d'Arafat ; « Nos pèlerins » retiré (pas de donnée).
    tpl = rep(tpl, '<p class="serif tnum" style="margin:8px 0 0;font-size:64px;font-weight:700;line-height:1;color:#E9C98B">8:30</p><p id="a-p" style="margin:10px 0 18px">Takbirat dès 8 h · Salle louée, 15 rue Frontenac</p>',
              sc_if('hasTime', '<p class="serif tnum" style="margin:8px 0 0;font-size:64px;font-weight:700;line-height:1;color:#E9C98B">{{heure}}</p>', 'false')
              + sc_if('noTime', '<p style="margin:10px 0 0;font-weight:700">L’heure sera annoncée ici dès qu’elle est fixée.</p>', 'true')
              + '<p id="a-p" style="margin:10px 0 18px">{{lieu}}</p>')
    tpl = rep(tpl, '<p class="tnum" style="margin:0;font-weight:700" role="timer">Dans {{dD}} j {{dH}} h {{dM}} min</p>',
              sc_if('hasCd', '<p class="tnum" style="margin:0;font-weight:700" role="timer">Dans {{dD}} j {{dH}} h {{dM}} min</p>', 'false'))
    tpl = rep(tpl, 'Samedi 15 mai : jeûne recommandé pour ceux qui ne sont pas en pèlerinage. Iftar partagé à la mosquée.',
              '{{arafatCap}} : jeûne recommandé pour ceux qui ne sont pas en pèlerinage.')
    tpl = resub(tpl, r'(<div class="card rv"><span class="ib" style="background:#F3E2C4;color:#B5573A">(?:(?!</div>).)*?Jour d’Arafat</p>.*?</p></div>)',
                lambda m: sc_if('hasDate', m.group(1)))
    tpl = resub(tpl, r'\n\s*<div class="card rv"><span class="ib" style="background:#F3E2C4;color:#B5573A">(?:(?!</div>).)*?Nos pèlerins</p>.*?</p></div>', '')
    a, b = section(tpl, 'a-p')
    tpl = tpl[:a] + tpl[a:b].replace('<div class="g3">', '<div class="g2" style="align-items:start">', 1) + tpl[b:]
    tpl = drop(tpl, 'a-s')                     # udhiya : pas encore proposée par l'association
    tpl = footer(tpl, 'Adha', 'Aïd al-Adha', 'عيد الأضحى مبارك')
    tpl = set_logic(tpl, 'adha', ADHA_VALS.replace("hasTime: !!R.heure,", "hasTime: !!R.heure, noTime: !R.heure,"))
    check(tpl, BANNED + ['udhiya', '\u2726'])
    return tpl


def adha_page(tpl):
    tpl = header(tpl, 'Adha', 'Aïd al-Adha')
    tpl = rep(tpl, '<p class="eyebrow rise" style="color:#7A3A22">Dhou al-Hijja 1448</p>', '<p class="eyebrow rise" style="color:#7A3A22">{{hijja}}</p>')
    tpl = rep(tpl, 'Du vendredi 7 au dimanche 16 mai 2027, selon l’annonce de la TCOM. Réservez votre udhiya et retrouvez le programme de la fête.', '{{lead}}')
    # Programme : dates calculées, textes sans exemple (pas de halaqa, d'iftar ni de distribution annoncés).
    k = tpl.index('aria-labelledby="ae-p"')
    o = tpl.index('<ol style="list-style:none;margin:20px 0 0;padding:0">', k)
    e = tpl.index('</ol>', o) + len('</ol>')
    li = ('<li class="rv" style="display:grid;grid-template-columns:120px minmax(0,1fr);gap:20px;padding:22px 0;border-bottom:1px solid #E2C9A2">'
          '<p class="tnum" style="margin:0;font-weight:800;color:{{p.c}}">{{p.when}}</p><div><p class="h3" style="color:#1B4D3A">{{p.t}}</p>'
          '<p class="muted" style="margin:4px 0 0">{{p.d}}</p></div></li>')
    tpl = tpl[:o] + '<ol style="list-style:none;margin:20px 0 0;padding:0"><sc-for list="{{prog}}" as="p" hint-placeholder-count="4">' + li + '</sc-for></ol>' + tpl[e:]
    tpl = wrap(tpl, 'ae-p', 'hasDate')
    tpl = drop(tpl, 'ae-u')                    # udhiya et prix d'exemple
    tpl = drop(tpl, 'ae-f')                    # questions : propres à la maquette
    tpl = footer(tpl, 'Adha', 'Aïd al-Adha', 'عيد الأضحى مبارك')
    tpl = set_logic(tpl, 'adha', ADHA_VALS)
    check(tpl, BANNED + ['udhiya'])
    return tpl


if __name__ == '__main__':
    build(ROOT / 'TH-Fitr-Accueil.dc.html', 'fitr-accueil.tpl.html', fitr_accueil, 'Aïd al-Fitr — ASCIL')
    build(ROOT / 'TH-Fitr-Page.dc.html', 'fitr-page.tpl.html', fitr_page, 'La journée de l’Aïd al-Fitr — ASCIL')
    build(ROOT / 'TH-Adha-Accueil.dc.html', 'adha-accueil.tpl.html', adha_accueil, 'Aïd al-Adha — ASCIL')
    build(ROOT / 'TH-Adha-Page.dc.html', 'adha-page.tpl.html', adha_page, 'Aïd al-Adha et les dix jours — ASCIL')
    print('thèmes Aïd : TH-Fitr-* et TH-Adha-* reconstruites depuis les maquettes, branchées sur les vraies données')
