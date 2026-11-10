// GET /api/admin/stats
// Renvoie les statistiques agrégées selon le rôle du compte connecté.
import { requireRole } from '../../_lib/guard.js';
import { json, error } from '../../_lib/http.js';
import { DEFAULT_SETTINGS, cleanHomeSettings, cleanEvenementsSettings, readEventRegistrationSettings } from '../../_lib/settings.js';
import { autoTotals } from '../../_lib/campagne.js';

export async function onRequestGet({ request, env }) {
  const { admin, response } = await requireRole(env, request, ['superadmin', 'editor', 'events']);
  if (response) return response;

  const db = env.DB;
  if (!db) return error(503, 'no_db', 'Base de données non disponible.');

  // 1. Événements (accessible à tous les rôles admin)
  let eventsCount = 0;
  let registrationsCount = 0;
  // Les événements sont ceux saisis dans « Événements » du panneau (réglage evenements),
  // pas l'ancienne table events, restée vide : le tableau de bord affichait 0.
  try {
    const evSet = await db.prepare('SELECT value FROM site_settings WHERE key = ?').bind('evenements').first();
    if (evSet && evSet.value) {
      const items = cleanEvenementsSettings(JSON.parse(evSet.value)).items || [];
      eventsCount = items.filter((x) => x && x.titre).length;
    }
  } catch {}

  try {
    // Comme les autres résumés : uniquement l'événement en cours.
    const { event_slug: slug } = await readEventRegistrationSettings(db);
    const regRow = await db.prepare("SELECT COUNT(*) as count FROM event_registrations WHERE status = 'confirmed' AND event_slug = ?").bind(slug).first();
    if (regRow) registrationsCount = Number(regRow.count) || 0;
  } catch {}

  // Si rôle "events", on renvoie uniquement les métriques d'événements
  if (admin.role === 'events') {
    return json({
      ok: true,
      role: 'events',
      events: {
        count: eventsCount,
        registrations: registrationsCount,
      },
    });
  }

  // 2. Campagne et Dons (accessible à superadmin et editor)
  let campagne = {
    objectif: 0,
    recolte: 0,
    pct: 0,
    donationsCount: 0,
    donationsSum: 0,
  };

  try {
    const setRow = await db.prepare('SELECT value FROM site_settings WHERE key = ?').bind('home').first();
    if (setRow && setRow.value) {
      const s = cleanHomeSettings(JSON.parse(setRow.value));
      campagne.objectif = s.campagne.objectif;
      campagne.recolte = s.campagne.recolte;
    }
  } catch {}
  const auto = await autoTotals(db);
  if (auto) campagne.recolte = auto.recolte;
  campagne.pct = Math.min(100, Math.round((campagne.recolte / (campagne.objectif || 1)) * 100));

  try {
    const donRow = await db.prepare('SELECT COUNT(*) as count, COALESCE(SUM(amount), 0) as total FROM donations').first();
    if (donRow) {
      campagne.donationsCount = Number(donRow.count) || 0;
      campagne.donationsSum = Number(donRow.total) || 0;
    }
  } catch {}

  // 3. Fréquentation / Visites anonymisées (accessible à superadmin et editor)
  const visits = {
    total: 0,
    today: 0,
    week: 0,
    topPages: [],
  };

  try {
    const totRow = await db.prepare('SELECT COALESCE(SUM(count), 0) as total FROM page_views').first();
    const todRow = await db.prepare("SELECT COALESCE(SUM(count), 0) as today FROM page_views WHERE viewed_date = strftime('%Y-%m-%d', 'now')").first();
    const wkRow = await db.prepare("SELECT COALESCE(SUM(count), 0) as week FROM page_views WHERE viewed_date >= date('now', '-7 days')").first();
    const topRows = await db.prepare('SELECT path, SUM(count) as count FROM page_views GROUP BY path ORDER BY count DESC LIMIT 5').all();

    visits.total = Number(totRow?.total) || 0;
    visits.today = Number(todRow?.today) || 0;
    visits.week = Number(wkRow?.week) || 0;
    visits.topPages = topRows?.results || [];
  } catch {}

  // 4. Sécurité et Comptes (réservé EXCLUSIVEMENT au superadmin)
  let security = null;
  if (admin.role === 'superadmin') {
    let admRow = null;
    let sessRow = null;
    let failRow = null;
    const now = Date.now();
    const fifteenMinAgo = now - 15 * 60 * 1000;

    try {
      admRow = await db.prepare(`
        SELECT COUNT(*) as total,
               COALESCE(SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END), 0) as active,
               COALESCE(SUM(CASE WHEN must_change_password = 1 THEN 1 ELSE 0 END), 0) as pending
        FROM admins
      `).first();
    } catch {}

    try {
      sessRow = await db.prepare('SELECT COUNT(*) as active_sessions FROM admin_sessions WHERE expires_at > ?').bind(now).first();
    } catch {}

    try {
      failRow = await db.prepare('SELECT COUNT(*) as failed FROM login_attempts WHERE success = 0 AND attempted_at > ?').bind(fifteenMinAgo).first();
    } catch {}

    security = {
      totalAdmins: Number(admRow?.total) || 0,
      activeAdmins: Number(admRow?.active) || 0,
      pendingAdmins: Number(admRow?.pending) || 0,
      activeSessions: Number(sessRow?.active_sessions) || 0,
      recentFailures: Number(failRow?.failed) || 0,
    };
  }

  return json({
    ok: true,
    role: admin.role,
    campagne,
    events: {
      count: eventsCount,
      registrations: registrationsCount,
    },
    visits,
    ...(security ? { security } : {}),
  });
}
