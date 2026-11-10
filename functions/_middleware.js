// Garde d'entrée : ne s'exécute que sur les chemins listés dans _routes.json
// (API, pages superadmin, fichiers du dépôt qui ne doivent pas être servis).
import { currentAdmin } from './_lib/auth.js';
import { error, sameOrigin } from './_lib/http.js';
import { canOpenPage, homeFor, pageKey } from './_lib/roles.js';
import { todayToronto } from './_lib/prayer-times.js';
import { activeSeasonMode, activeVendredi, pageSettingForPath, readPagesSettings, readSeasonSettings } from './_lib/settings.js';

const PRIVATE = [/^\/functions(\/|$)/, /^\/migrations(\/|$)/, /^\/scripts(\/|$)/, /^\/wrangler\.toml$/, /^\/_routes\.json$/, /^\/\.git/];
// Adresses de l'Accueil : pendant le Ramadan (« Site entier → Mode du site »), elles affichent l'Accueil Ramadan.
const HOME_PAGES = [/^\/$/, /^\/index(\.html)?$/, /^\/Main\.dc(\.html)?$/, /^\/(?:M|T)-Accueil\.dc(\.html)?$/];
const SEASON_HOME = { ramadan: '/TH-Ramadan-Accueil.dc', aid_fitr: '/TH-Fitr-Accueil.dc', aid_adha: '/TH-Adha-Accueil.dc' };
const SEASON_HOME_RE = /^\/TH-(Ramadan|Fitr|Adha)-Accueil\.dc(\.html)?$/;
const SEASON_OF = { Ramadan: 'ramadan', Fitr: 'aid_fitr', Adha: 'aid_adha' };
// Thème du vendredi (« Mode du site → Thème du vendredi ») : Accueil du vendredi à l'adresse de l'Accueil,
// pages Horaires et Khutba du vendredi à leur propre adresse. Thème éteint : chaque page mène à la page normale.
const VENDREDI_HOME = '/TH-Vendredi-Accueil.dc';
const VENDREDI_RE = /^\/TH-Vendredi-(Accueil|Horaires|Khutba)\.dc(\.html)?$/;
const VENDREDI_OFF = { Accueil: '/', Horaires: '/Horaires.dc.html', Khutba: '/N2-Khutba.dc.html' };
const LOGIN_PAGES = [/^\/superadmin(\.html)?$/, /^\/SA-Connexion\.dc(\.html)?$/];

const PAGE_HEADERS = {
  'Cache-Control': 'no-store',
  'X-Robots-Tag': 'noindex, nofollow',
  'X-Frame-Options': 'DENY',
  'Referrer-Policy': 'same-origin',
  'X-Content-Type-Options': 'nosniff',
};

function withHeaders(response, headers) {
  const r = new Response(response.body, response);
  for (const [k, v] of Object.entries(headers)) r.headers.set(k, v);
  return r;
}

function redirect(location) {
  return new Response(null, { status: 302, headers: { Location: location, 'Cache-Control': 'no-store' } });
}

export async function onRequest(context) {
  const { request, env, next } = context;
  const url = new URL(request.url);
  const path = url.pathname;

  if (PRIVATE.some((re) => re.test(path))) return new Response('Not found', { status: 404 });

  if (path.startsWith('/api/')) {
    if (!['GET', 'HEAD', 'OPTIONS'].includes(request.method) && !sameOrigin(request)) {
      return error(403, 'origin', 'Requête refusée : elle ne vient pas du site du Centre Islamique d’Edmundston.');
    }
    if (!env.DB) return error(503, 'no_db', 'La base de données n’est pas reliée au site. Ajoutez la liaison D1 « DB » dans Cloudflare Pages.');
    try {
      return withHeaders(await next(), { 'X-Content-Type-Options': 'nosniff' });
    } catch (e) {
      console.error('api error', path, e && e.stack || e);
      return error(500, 'server', 'Une erreur interne est survenue. Réessayez dans un instant.');
    }
  }

  const isLogin = LOGIN_PAGES.some((re) => re.test(path));
  const key = isLogin ? null : pageKey(path);
  if (isLogin || key) {
    const admin = env.DB ? await currentAdmin(env.DB, request).catch(() => null) : null;
    if (isLogin) {
      // Connecté : on file vers sa page d'accueil, sauf s'il doit d'abord changer son mot de passe.
      if (admin && !admin.mustChangePassword) return redirect(homeFor(admin.role));
    } else if (!admin) {
      return redirect('/superadmin.html?next=' + encodeURIComponent(path + url.search));
    } else if (admin.mustChangePassword) {
      return redirect('/superadmin.html');
    } else if (!canOpenPage(admin.role, key)) {
      return redirect(homeFor(admin.role));
    }
    return withHeaders(await next(), PAGE_HEADERS);
  }

  // Accueil de saison : servi à la place de l'Accueil, à la même adresse (pas de redirection, pas de clignotement).
  // Hors de sa saison, l'adresse directe d'un Accueil saisonnier mène à l'Accueil.
  const isHome = HOME_PAGES.some((re) => re.test(path));
  const fri = VENDREDI_RE.exec(path);
  if ((isHome || SEASON_HOME_RE.test(path) || fri) && env.DB && request.method === 'GET') {
    const season = await readSeasonSettings(env.DB).catch(() => null);
    const today = todayToronto();
    const mode = season ? activeSeasonMode(season, today) : 'normal';
    // Une saison (Ramadan, Aïd) passe avant le thème du vendredi.
    const friday = mode === 'normal' && !!season && activeVendredi(season, today);
    const home = SEASON_HOME[mode] || (friday ? VENDREDI_HOME : '');
    if (isHome && home) {
      try {
        const r = await env.ASSETS.fetch(new Request(new URL(home, url), { method: 'GET' }));
        if (r.ok) return withHeaders(r, { 'Cache-Control': 'no-cache' });
      } catch (e) {
        console.warn('season home error', e && e.message);
      }
    } else if (fri) {
      if (!friday) return redirect(VENDREDI_OFF[fri[1]]);
      if (fri[1] === 'Accueil') return redirect('/');
    } else if (!isHome && SEASON_OF[SEASON_HOME_RE.exec(path)[1]] !== mode) {
      // Accueil d'une autre saison que celle en cours : on mène à l'Accueil du moment.
      return redirect('/');
    }
  }

  // Page publique masquée dans « Site entier → Pages publiées » : son adresse mène à l'accueil.
  const pageSetting = pageSettingForPath(path);
  if (pageSetting && env.DB) {
    const pages = await readPagesSettings(env.DB).catch(() => null);
    if (pages && pages[pageSetting] === false) return redirect('/');
  }

  return next();
}
