// GET /p/<lien> : page créée dans le superadmin, rendue côté serveur.
//  - publiée : visible par tous, indexable ;
//  - lien privé : visible à qui a le lien, jamais indexée ;
//  - brouillon : visible seulement par un compte connecté (bandeau « Brouillon »), sinon introuvable ;
//  - ancienne adresse : redirection 301 vers l'adresse actuelle.
import { currentAdmin } from '../_lib/auth.js';
import { SLUG_RE, rowToPage } from '../_lib/custom-pages.js';
import { renderNotFound, renderPage } from '../_lib/render-page.js';
import { cleanAlertSettings } from '../_lib/settings.js';
import { VIDEO_HOSTS } from '../_lib/video.js';
import { rowToForm } from '../_lib/custom-forms.js';

const SECURITY = {
  'Content-Type': 'text/html; charset=utf-8',
  'X-Content-Type-Options': 'nosniff',
  'Referrer-Policy': 'strict-origin-when-cross-origin',
  // Aucune exécution de script dans la page. Les vidéos viennent de YouTube (sans cookie), Vimeo ou
  // Facebook ; les widgets de /w/<id> (même site, isolés par sandbox) ; les formulaires repartent vers le site.
  'Content-Security-Policy': "default-src 'none'; style-src 'unsafe-inline' https://fonts.googleapis.com; "
    + "font-src https://fonts.gstatic.com; img-src 'self' data:; "
    + `frame-src 'self' ${VIDEO_HOSTS.join(' ')}; `
    + "base-uri 'none'; form-action 'self'; frame-ancestors 'none'",
};

function html(body, status, extra = {}) {
  return new Response(body, { status, headers: { ...SECURITY, ...extra } });
}
const notFound = () => html(renderNotFound(), 404, { 'Cache-Control': 'no-store', 'X-Robots-Tag': 'noindex' });

// Bannière d'alerte active aujourd'hui (heure du Québec), comme sur le reste du site.
async function activeAlert(db) {
  try {
    const row = await db.prepare("SELECT value FROM site_settings WHERE key = 'alert'").first();
    const a = cleanAlertSettings(row ? JSON.parse(row.value) : null);
    if (!a.on || !a.message) return null;
    const today = new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Moncton' }).format(new Date());
    if ((a.from && today < a.from) || (a.to && today > a.to)) return null;
    return a;
  } catch {
    return null;
  }
}


// Photos, widgets et formulaires utilisés par la page, lus en une fois. Une table encore absente
// (migration 0011 pas appliquée) donne simplement un bloc vide.
async function loadRefs(db, blocks) {
  const ids = (type, key) => Array.from(new Set(blocks.filter((b) => b && b.type === type && Number.isInteger(b[key])).map((b) => b[key]))).slice(0, 50);
  const read = async (table, list) => {
    if (!list.length) return [];
    try {
      const { results } = await db.prepare(`SELECT * FROM ${table} WHERE id IN (${list.map(() => '?').join(',')})`).bind(...list).all();
      return results;
    } catch {
      return [];
    }
  };
  const [media, widgets, forms] = await Promise.all([
    read('media', ids('photo', 'media')),
    read('page_widgets', ids('widget', 'widget')),
    read('custom_forms', ids('formulaire', 'form')),
  ]);
  return {
    media: new Map(media.map((r) => [r.id, r])),
    widgets: new Map(widgets.map((r) => [r.id, r])),
    forms: new Map(forms.map((r) => [r.id, rowToForm(r)])),
  };
}

const RESULT_CODES = ['ok', 'missing', 'invalid', 'too_fast', 'too_many', 'closed', 'server'];

export async function onRequestGet({ request, env, params }) {
  const db = env.DB;
  const slug = String(params.slug || '').toLowerCase();
  if (!db || !SLUG_RE.test(slug) || slug.length > 60) return notFound();

  let row = await db.prepare('SELECT * FROM custom_pages WHERE slug = ?').bind(slug).first();
  if (!row) {
    const r = await db.prepare(
      'SELECT p.slug FROM page_redirects r JOIN custom_pages p ON p.id = r.page_id WHERE r.old_slug = ?'
    ).bind(slug).first();
    if (r) return new Response(null, { status: 301, headers: { Location: `/p/${r.slug}`, 'Cache-Control': 'public, max-age=300' } });
    return notFound();
  }
  const page = rowToPage(row);

  let draft = false;
  if (page.visibility === 'draft') {
    const admin = await currentAdmin(db, request).catch(() => null);
    if (!admin) return notFound();
    draft = true;
  }

  const url = new URL(request.url);
  const code = url.searchParams.get('r');
  const fid = Number(url.searchParams.get('f'));
  const result = RESULT_CODES.includes(code) && Number.isInteger(fid) && fid > 0 ? { form: fid, code } : null;
  const [alert, refs] = await Promise.all([activeAlert(db), loadRefs(db, page.blocks || [])]);
  const body = renderPage(page, { alert, draft, origin: url.origin, refs, result });
  if (result) {
    return html(body, 200, { 'Cache-Control': 'private, no-store', 'X-Robots-Tag': 'noindex, nofollow' });
  }
  if (page.visibility === 'published') {
    return html(body, 200, { 'Cache-Control': 'public, max-age=60' });
  }
  return html(body, 200, { 'Cache-Control': 'private, no-store', 'X-Robots-Tag': 'noindex, nofollow' });
}
