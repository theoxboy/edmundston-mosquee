// Calcul local des heures de prière (méthode ISNA, Asr standard / chaféite), pour Edmundston.
// Utilisé UNIQUEMENT pour Lever, Dohr, Asr et Maghreb, et seulement quand ni le tableau du mois
// ni la carte « Prochaine prière » de l'Accueil n'en donnent une : une heure saisie à la main gagne toujours.
// Fajr, Icha et Jumu'a ne sont JAMAIS calculés (horaires fixes d'Edmundston (non définis par défaut)).
// Rien n'est enregistré : le calcul est refait à chaque lecture.
// Algorithme astronomique classique (position du soleil d'après l'U.S. Naval Observatory,
// le même que celui des calculateurs usuels, dont Aladhan) : lever et coucher à -0,833°,
// Dohr au passage du soleil au méridien, Asr quand l'ombre égale la hauteur de l'objet plus son ombre de midi.

export const LIEU = { lat: 47.372, lng: -68.324, tz: 'America/Moncton' };
export const CALC_COLUMNS = ['lever', 'dohr', 'asr', 'maghreb'];

const DEG = Math.PI / 180;
const sin = (d) => Math.sin(d * DEG);
const cos = (d) => Math.cos(d * DEG);
const tan = (d) => Math.tan(d * DEG);
const asin = (x) => Math.asin(x) / DEG;
const acos = (x) => Math.acos(x) / DEG;
const atan2 = (y, x) => Math.atan2(y, x) / DEG;
const acot = (x) => Math.atan(1 / x) / DEG;
const fix = (a, b) => { const r = a - b * Math.floor(a / b); return r < 0 ? r + b : r; };

function julian(y, m, d) {
  if (m <= 2) { y -= 1; m += 12; }
  const A = Math.floor(y / 100);
  const B = 2 - A + Math.floor(A / 4);
  return Math.floor(365.25 * (y + 4716)) + Math.floor(30.6001 * (m + 1)) + d + B - 1524.5;
}

function sun(jd) {
  const D = jd - 2451545.0;
  const g = fix(357.529 + 0.98560028 * D, 360);
  const q = fix(280.459 + 0.98564736 * D, 360);
  const L = fix(q + 1.915 * sin(g) + 0.020 * sin(2 * g), 360);
  const e = 23.439 - 0.00000036 * D;
  const RA = fix(atan2(cos(e) * sin(L), cos(L)) / 15, 24);
  return { decl: asin(sin(e) * sin(L)), eqt: q / 15 - RA };
}

// Décalage horaire (heures) du fuseau à une date donnée, heure d'été comprise.
export function tzOffset(dateStr, tz = LIEU.tz) {
  const [y, m, d] = dateStr.split('-').map(Number);
  const at = new Date(Date.UTC(y, m - 1, d, 12, 0, 0));
  const parts = {};
  new Intl.DateTimeFormat('en-US', { timeZone: tz, hourCycle: 'h23', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
    .formatToParts(at).forEach((p) => { parts[p.type] = p.value; });
  const local = Date.UTC(Number(parts.year), Number(parts.month) - 1, Number(parts.day), Number(parts.hour) % 24, Number(parts.minute));
  return (local - at.getTime()) / 3600000;
}

function hhmm(h) {
  if (!Number.isFinite(h)) return '';
  const t = fix(h + 0.5 / 60, 24); // arrondi à la minute la plus proche
  const H = Math.floor(t);
  const M = Math.floor((t - H) * 60);
  return `${String(H).padStart(2, '0')}:${String(M).padStart(2, '0')}`;
}

// Heures calculées (HH:MM, heure locale) pour une date AAAA-MM-JJ : { lever, dohr, asr, maghreb }.
export function calcDay(dateStr, lieu = LIEU) {
  try {
    const [y, m, d] = dateStr.split('-').map(Number);
    const { lat, lng } = lieu;
    const tz = tzOffset(dateStr, lieu.tz);
    const jd = julian(y, m, d) - lng / (15 * 24);
    const mid = (t) => fix(12 - sun(jd + t).eqt, 24);
    const angleTime = (angle, t, ccw) => {
      const decl = sun(jd + t).decl;
      const T = acos((-sin(angle) - sin(decl) * sin(lat)) / (cos(decl) * cos(lat))) / 15;
      return mid(t) + (ccw ? -T : T);
    };
    const asrTime = (factor, t) => {
      const decl = sun(jd + t).decl;
      return angleTime(-acot(factor + tan(Math.abs(lat - decl))), t);
    };
    // Deux passes : la première sur des heures approchées, la seconde affine (fraction de jour).
    let t = { lever: 6, dohr: 12, asr: 13, maghreb: 18 };
    for (let i = 0; i < 2; i++) {
      const p = { lever: t.lever / 24, dohr: t.dohr / 24, asr: t.asr / 24, maghreb: t.maghreb / 24 };
      t = {
        lever: angleTime(0.833, p.lever, true),
        dohr: mid(p.dohr),
        asr: asrTime(1, p.asr),
        maghreb: angleTime(0.833, p.maghreb),
      };
    }
    const local = (h) => h + tz - lng / 15;
    return { lever: hhmm(local(t.lever)), dohr: hhmm(local(t.dohr)), asr: hhmm(local(t.asr)), maghreb: hhmm(local(t.maghreb)) };
  } catch {
    return { lever: '', dohr: '', asr: '', maghreb: '' };
  }
}
