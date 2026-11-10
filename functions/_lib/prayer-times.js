// Tableau mensuel des heures de prière (table prayer_times) : source unique des horaires du site.
// Une ligne par jour (date AAAA-MM-JJ). Pour les heures du jour, toute case vide ou absente se
// replie sur les défauts de l'Accueil (home.priere : Fajr 06:30, Jumu'a 12:30, Icha 19:00).
// Lever, Dohr, Asr et Maghreb encore vides sont alors calculés (ISNA, Edmundston) ; la liste
// `calc` du jour nomme les colonnes calculées. Rien n'est écrit dans la table.
import { DEFAULT_SETTINGS, cleanHomeSettings } from './settings.js';
import { CALC_COLUMNS, calcDay } from './prayer-calc.js';

export const ROLES = ['superadmin', 'editor'];
export const PRAYER_COLUMNS = ['fajr', 'lever', 'dohr', 'asr', 'maghreb', 'isha', 'jumuha'];

export const MONTH_RE = /^\d{4}-(0[1-9]|1[0-2])$/;
export const DAY_RE = /^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$/;
const HHMM_RE = /^([01]\d|2[0-3]):[0-5]\d$/;

export function cleanTime(v) {
  if (v === null || v === undefined) return '';
  if (typeof v !== 'string') return null;
  const t = v.trim();
  if (!t || t === '—' || t === '-' || t === '–') return '';
  if (HHMM_RE.test(t)) return t;
  const m = /^(\d{1,2})\s*[:hH]\s*([0-5]\d)(?::[0-5]\d)?$/.exec(t);
  if (!m) return null;
  const hh = Number(m[1]);
  if (hh < 0 || hh > 23) return null;
  return `${String(hh).padStart(2, '0')}:${m[2]}`;
}

export function isValidMonth(m) {
  if (typeof m !== 'string' || !MONTH_RE.test(m)) return false;
  const year = Number(m.slice(0, 4));
  return year >= 2020 && year <= 2100;
}

export function daysInMonthCount(ym) {
  const [y, m] = ym.split('-').map(Number);
  return new Date(Date.UTC(y, m, 0)).getUTCDate();
}

export function isValidDate(d) {
  if (typeof d !== 'string' || !DAY_RE.test(d)) return false;
  const ym = d.slice(0, 7);
  if (!isValidMonth(ym)) return false;
  const day = Number(d.slice(8, 10));
  return day >= 1 && day <= daysInMonthCount(ym);
}

export function monthDates(ym) {
  const total = daysInMonthCount(ym);
  const out = [];
  for (let d = 1; d <= total; d++) {
    out.push(`${ym}-${String(d).padStart(2, '0')}`);
  }
  return out;
}

export function todayMoncton() {
  try {
    return new Intl.DateTimeFormat('en-CA', {
      timeZone: 'America/Moncton',
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    }).format(new Date());
  } catch {
    return new Date().toISOString().slice(0, 10);
  }
}

export function currentMonthMoncton() {
  return todayMoncton().slice(0, 7);
}

// Défauts issus de la carte « Prochaine prière » de l'Accueil (site_settings.home.priere),
// avec repli sur Fajr 06:30, Jumu'a 12:30, Icha 19:00.
export async function readHomeDefaults(db) {
  const base = DEFAULT_SETTINGS.home.priere;
  let p = base;
  if (db) {
    try {
      const row = await db.prepare('SELECT value FROM site_settings WHERE key = ?').bind('home').first();
      if (row && row.value) {
        p = cleanHomeSettings(JSON.parse(row.value)).priere || base;
      }
    } catch {
      p = base;
    }
  }
  const fajr = cleanTime(p.fajr) || '';
  const lever = cleanTime(p.lever) || '';
  const dohr = cleanTime(p.dohr) || '';
  const asr = cleanTime(p.asr) || '';
  const maghreb = cleanTime(p.maghreb) || '';
  const isha = cleanTime(p.icha ?? p.isha) || '';
  const jumuha = cleanTime(p.jumua ?? p.jumuha) || '';

  return {
    fajr,
    lever,
    dohr,
    asr,
    maghreb,
    isha,
    icha: isha,
    jumuha,
    jumua: jumuha,
  };
}

export function resolveDayWithDefaults(row, defaults, date) {
  const r = row || {};
  const d = defaults || {
    fajr: '', lever: '', dohr: '', asr: '', maghreb: '', isha: '', jumuha: '',
  };
  const fajr = cleanTime(r.fajr) || d.fajr || '';
  // Lever, Dohr, Asr, Maghreb : ligne du tableau, puis défaut de l'Accueil, et seulement en dernier
  // recours le calcul local ISNA (prayer-calc.js). Fajr, Icha et Jumu'a ne sont jamais calculés.
  const manual = {};
  for (const col of CALC_COLUMNS) manual[col] = cleanTime(r[col]) || d[col] || '';
  const calc = [];
  let computed = null;
  if (date && CALC_COLUMNS.some((col) => !manual[col])) computed = calcDay(date);
  for (const col of CALC_COLUMNS) {
    if (!manual[col] && computed && computed[col]) { manual[col] = computed[col]; calc.push(col); }
  }
  const { lever, dohr, asr, maghreb } = manual;
  const isha = cleanTime(r.isha ?? r.icha) || d.isha || '';
  const jumuha = cleanTime(r.jumuha ?? r.jumua) || d.jumuha || '';

  const hasRow = Boolean(
    row && PRAYER_COLUMNS.some((col) => Boolean(cleanTime(row[col])))
  );

  return {
    date,
    fajr,
    lever,
    dohr,
    asr,
    maghreb,
    isha,
    icha: isha,
    jumuha,
    jumua: jumuha,
    source: r.source || (hasRow ? 'table' : 'defaults'),
    fromTable: hasRow,
    calc,
  };
}

export async function readDay(db, date = todayMoncton()) {
  const defaults = await readHomeDefaults(db);
  let row = null;
  if (db) {
    try {
      row = await db
        .prepare('SELECT date, fajr, lever, dohr, asr, maghreb, isha, jumuha, source FROM prayer_times WHERE date = ?')
        .bind(date)
        .first();
    } catch {
      row = null;
    }
  }
  return {
    day: resolveDayWithDefaults(row, defaults, date),
    raw: row ? {
      date: row.date,
      fajr: cleanTime(row.fajr) || '',
      lever: cleanTime(row.lever) || '',
      dohr: cleanTime(row.dohr) || '',
      asr: cleanTime(row.asr) || '',
      maghreb: cleanTime(row.maghreb) || '',
      isha: cleanTime(row.isha) || '',
      jumuha: cleanTime(row.jumuha) || '',
      source: row.source || '',
    } : null,
    defaults,
  };
}

export async function readMonth(db, month) {
  const dates = monthDates(month);
  const firstDay = dates[0];
  const lastDay = dates[dates.length - 1];

  const byDate = new Map();
  if (db) {
    const { results } = await db
      .prepare(
        `SELECT date, fajr, lever, dohr, asr, maghreb, isha, jumuha, source
         FROM prayer_times
         WHERE date >= ? AND date <= ?
         ORDER BY date ASC`
      )
      .bind(firstDay, lastDay)
      .all();

    for (const r of results || []) {
      if (r && r.date) byDate.set(r.date, r);
    }
  }

  const days = dates.map((date) => {
    const r = byDate.get(date);
    return {
      date,
      fajr: cleanTime(r?.fajr) || '',
      lever: cleanTime(r?.lever) || '',
      dohr: cleanTime(r?.dohr) || '',
      asr: cleanTime(r?.asr) || '',
      maghreb: cleanTime(r?.maghreb) || '',
      isha: cleanTime(r?.isha) || '',
      jumuha: cleanTime(r?.jumuha) || '',
      source: r?.source || '',
    };
  });

  return { month, days, savedCount: byDate.size };
}

export function cleanMonthPayload(month, body) {
  if (!isValidMonth(month)) {
    return { error: 'Mois invalide. Utilisez le format AAAA-MM (ex. 2026-11).' };
  }
  const rawList = Array.isArray(body)
    ? body
    : Array.isArray(body?.days)
      ? body.days
      : Array.isArray(body?.rows)
        ? body.rows
        : (body?.days && typeof body.days === 'object' ? Object.entries(body.days).map(([k, v]) => ({ date: k, ...v })) : null);

  if (!rawList) {
    return { error: 'Données du mois manquantes (tableau « days » attendu).' };
  }

  const defaultSource = typeof body?.source === 'string' && body.source.trim()
    ? body.source.trim().slice(0, 40)
    : 'manuel';

  const maxDay = daysInMonthCount(month);
  const byDate = new Map();

  for (const item of rawList) {
    if (!item || typeof item !== 'object') continue;
    let date = typeof item.date === 'string' ? item.date.trim() : '';
    if (!date && (typeof item.day === 'number' || typeof item.day === 'string')) {
      const dNum = Number(item.day);
      if (Number.isInteger(dNum) && dNum >= 1 && dNum <= maxDay) {
        date = `${month}-${String(dNum).padStart(2, '0')}`;
      }
    } else if (/^\d{1,2}$/.test(date)) {
      const dNum = Number(date);
      if (dNum >= 1 && dNum <= maxDay) {
        date = `${month}-${String(dNum).padStart(2, '0')}`;
      }
    }

    if (!isValidDate(date) || !date.startsWith(`${month}-`)) {
      return { error: `Date invalide pour le mois ${month} : « ${item.date ?? item.day ?? ''} ».` };
    }

    const cleanedRow = { date };
    for (const col of PRAYER_COLUMNS) {
      const rawVal = col === 'isha'
        ? (item.isha !== undefined ? item.isha : item.icha)
        : col === 'jumuha'
          ? (item.jumuha !== undefined ? item.jumuha : item.jumua)
          : item[col];
      const c = cleanTime(rawVal);
      if (c === null) {
        return { error: `Heure invalide le ${date} (${col}) : utilisez le format HH:MM (ex. 06:30).` };
      }
      cleanedRow[col] = c;
    }
    cleanedRow.source = typeof item.source === 'string' && item.source.trim()
      ? item.source.trim().slice(0, 40)
      : defaultSource;

    byDate.set(date, cleanedRow);
  }

  return { month, days: Array.from(byDate.values()) };
}

export async function writeMonth(db, month, cleanedDays) {
  const stmts = [];
  let upserted = 0;
  let cleared = 0;

  for (const row of cleanedDays) {
    const hasAny = PRAYER_COLUMNS.some((col) => Boolean(row[col]));
    if (hasAny) {
      upserted++;
      stmts.push(
        db.prepare(
          `INSERT INTO prayer_times (date, fajr, lever, dohr, asr, maghreb, isha, jumuha, source)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(date) DO UPDATE SET
             fajr = excluded.fajr,
             lever = excluded.lever,
             dohr = excluded.dohr,
             asr = excluded.asr,
             maghreb = excluded.maghreb,
             isha = excluded.isha,
             jumuha = excluded.jumuha,
             source = excluded.source`
        ).bind(
          row.date,
          row.fajr,
          row.lever,
          row.dohr,
          row.asr,
          row.maghreb,
          row.isha,
          row.jumuha,
          row.source || 'manuel'
        )
      );
    } else {
      cleared++;
      stmts.push(db.prepare('DELETE FROM prayer_times WHERE date = ?').bind(row.date));
    }
  }

  if (stmts.length > 0) {
    await db.batch(stmts);
  }

  return { upserted, cleared };
}

export const todayToronto = todayMoncton;
export const currentMonthToronto = currentMonthMoncton;
