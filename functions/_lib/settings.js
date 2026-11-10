// Configuration et valeurs par défaut des réglages du site.

export const DEFAULT_SETTINGS = {
  home: {
    general: {
      email: '',
      facebook: '',
      address: '34, 37e Avenue',
      city: 'Edmundston, NB E3V 3S2',
      mapUrl: 'https://maps.google.com/?q=34+37e+Avenue+Edmundston+NB+E3V+3S2',
    },
    ordre: ['acces', 'campagne', 'annonces', 'bienvenue', 'invitation'],
    on: {
      chargement: true, bandeau: true, compte: true, mail: true, fb: true,
      don: true, langue: true, horaires: true, apropos: true, services: true,
      evenements: true, ressources: true, contact: true, hero: true, priere: true,
      hegirien: true, progression: true, puces: true, acces: true, campagne: true,
      barre: true, annonces: true, bienvenue: true, invitation: true, haut: true,
      pHor: true, pIti: true, pFb: true, pTcom: true, pCciq: true, pMail: true,
    },
    chargement: {
      duration: 'normale',
    },
    hero: {
      h1: 'Page : Horaires du mois',
      h2: 'Page : Faire un don',
    },
    priere: {
      fajr: '',
      lever: '',
      dohr: '',
      jumua: '',
      asr: '',
      maghreb: '',
      icha: '',
    },
    acces: {
      cartes: [
        { id: 'vendredi', on: true, lien: 'Page : Horaires du mois' },
        { id: 'trouver', on: true, lien: 'Page : Contact' },
        { id: 'campagne', on: true, lien: 'Page : Faire un don' },
      ],
    },
    campagne: {
      objectif: 0,
      recolte: 0,
      btnInterac: '',
      btnSuivre: '',
    },
    annonces: {
      max: 3,
      btnTous: 'Page : Événements',
      items: [],
    },
    charge: { on: ['b'], texte: ['t', 600] },
  },
  aide: {
    form: { on: ['b'], besoins: ['list', 8, { titre: ['s', 40], on: ['b'] }], recup: ['b'], livraison: ['b'], delai: ['e', ['24 h', '48 h', '72 h']] },
    manque: { on: ['b'], items: ['list', 15, { titre: ['s', 60], niveau: ['e', ['tres', 'demande', 'suffisant']], on: ['b'] }] },
    depot: { on: ['b'], adresse: ['s', 120], quand: ['s', 120], note: ['t', 300] },
    argent: { on: ['b'], courriel: ['s', 120], note: ['t', 300] },
  },
  femmes: {
    jours: ['fixed', 7, { on: ['b'], de1: ['hm'], a1: ['hm'], de2: ['hm'], a2: ['hm'] }],
    fermeture: ['date'], plan: ['img', 200000],
    pratique: { on: ['b'], entree: ['s', 160], acces: ['s', 160], ablutions: ['s', 160], jumua: ['s', 160], enfants: ['s', 160], responsable: ['s', 160] },
    regles: { on: ['b'], items: ['list', 15, LIST_ITEM] },
  },
};

const docs = (...t) => t.map((titre) => ({ titre, on: true }));
const fjour = (de1, a1, de2 = '', a2 = '') => ({ on: true, de1, a1, de2, a2 });
DEFAULT_SETTINGS.cours = {
  annee: '2026–2027', delai: '48 h', essai: true, attente: true, inscriptions: true,
  items: [],
};
const TR_MAX_ITEMS = 3000;
const TR_MAX_LEN = 2000;
const trText = (v) => (typeof v === 'string'
  ? v.replace(/[\u0000-\u001f\u007f]/g, ' ').replace(/\u00a0/g, ' ').replace(/\s+/g, ' ').trim().slice(0, TR_MAX_LEN)
  : '');
export function cleanTraductionsSettings(input) {
  const list = input && Array.isArray(input.items) ? input.items : [];
  const items = [];
  const seen = new Set();
  for (const x of list) {
    if (items.length >= TR_MAX_ITEMS) break;
    if (!x || typeof x !== 'object') continue;
    const fr = trText(x.fr), ar = trText(x.ar), en = trText(x.en);
    if (!fr || (!ar && !en) || seen.has(fr)) continue;
    seen.add(fr);
    items.push({ fr, ar, en });
  }
  return { items };
}

// Photos de l'Accueil (PC, index, mobile, tablette), choisies dans le panneau Accueil :
// « hero » = grande photo du haut, « bienvenue » = photo de « Vous venez pour la première fois ? ».
// La photo est envoyée par /api/admin/media (stockage MEDIA) ; seul son chemin /media/<nom> est gardé ici.
// Chemin vide = la photo d'origine du site reste affichée.
const PHOTO_SLOTS = ['hero', 'bienvenue'];
const MEDIA_PATH_RE = /^\/media\/[0-9a-f]{32}\.(?:jpg|png|webp|gif)$/;
DEFAULT_SETTINGS.photos = { hero: { src: '', alt: '' }, bienvenue: { src: '', alt: '' } };
export function cleanPhotosSettings(input) {
  const out = {};
  for (const k of PHOTO_SLOTS) {
    const x = input && typeof input[k] === 'object' && input[k] ? input[k] : {};
    const src = typeof x.src === 'string' && MEDIA_PATH_RE.test(x.src.trim()) ? x.src.trim() : '';
    const alt = typeof x.alt === 'string' ? x.alt.replace(/[\u0000-\u001f\u007f<>]/g, ' ').replace(/\s+/g, ' ').trim().slice(0, 200) : '';
    out[k] = { src, alt: src ? alt : '' };
  }
  return out;
}

// Clés modifiables par la route générique /api/admin/settings/:key, et par qui.
// « event_registration » n'y figure pas : elle passe par /api/admin/events/settings
// (superadmin et responsable événements), qui la valide.
export const GENERIC_KEYS = {
  home: { roles: ['superadmin', 'editor'], clean: cleanHomeSettings },
  pages: { roles: ['superadmin', 'editor'], clean: cleanPagesSettings },
  alert: { roles: ['superadmin', 'editor'], clean: cleanAlertSettings },
  season: { roles: ['superadmin', 'editor'], clean: cleanSeasonSettings },
  languages: { roles: ['superadmin', 'editor'], clean: cleanLanguagesSettings },
  horaires: { roles: ['superadmin', 'editor'], clean: cleanHorairesSettings },
  khutba: { roles: ['superadmin', 'editor'], clean: cleanKhutbaSettings },
  rappel: { roles: ['superadmin', 'editor'], clean: cleanRappelSettings },
  // Photos de l’équipe incluses (réduites dans le panneau) : corps de requête plus grand.
  apropos: { roles: ['superadmin', 'editor'], clean: cleanAproposSettings, maxBytes: 1000000 },
  campagne: { roles: ['superadmin', 'editor'], clean: cleanCampagneSettings },
  services: { roles: ['superadmin', 'editor'], clean: cleanServicesSettings },
  cours: { roles: ['superadmin', 'editor'], clean: cleanCoursSettings },
  mariages: { roles: ['superadmin', 'editor'], clean: cleanMariagesSettings },
  funerailles: { roles: ['superadmin', 'editor'], clean: cleanFuneraillesSettings },
  aide: { roles: ['superadmin', 'editor'], clean: cleanAideSettings },
  // Plan d'accès inclus (image réduite dans le panneau) : corps de requête plus grand.
  femmes: { roles: ['superadmin', 'editor'], clean: cleanFemmesSettings, maxBytes: 400000 },
  dons: { roles: ['superadmin', 'editor'], clean: cleanDonsSettings },
  merci: { roles: ['superadmin', 'editor'], clean: cleanMerciSettings },
  // Le responsable des événements gère aussi la liste et le calendrier.
  evenements: { roles: ['superadmin', 'editor', 'events'], clean: cleanEvenementsSettings, maxBytes: 200000 },
  calendrier: { roles: ['superadmin', 'editor', 'events'], clean: cleanCalendrierSettings },
  ressources: { roles: ['superadmin', 'editor'], clean: cleanRessourcesSettings },
  dua: { roles: ['superadmin', 'editor'], clean: cleanDuaSettings },
  contact: { roles: ['superadmin', 'editor'], clean: cleanContactSettings },
  p404: { roles: ['superadmin', 'editor'], clean: cleanP404Settings },
  // Jusqu'à 3000 textes de 2000 caractères au plus, dans les deux langues.
  traductions: { roles: ['superadmin', 'editor'], clean: cleanTraductionsSettings, maxBytes: 1500000 },
  photos: { roles: ['superadmin', 'editor'], clean: cleanPhotosSettings },
};

// Réglages lisibles publiquement par /api/settings/:key.
export const PUBLIC_KEYS = ['home', 'pages', 'alert', 'season', 'languages', 'horaires', 'khutba', 'rappel', 'apropos', 'services',
  'cours', 'mariages', 'funerailles', 'aide', 'femmes', 'dons', 'merci', 'evenements', 'calendrier', 'ressources', 'dua', 'contact', 'p404',
  'traductions', 'photos'];

// ---------------------------------------------------------------------------------------------
// Réglages restaurés depuis la version de référence (fonctions et valeurs par défaut manquantes).
// Valeurs propres à Edmundston : adresse et courriels vides, campagne à zéro, listes vides
// (cours, événements, ressources) et fuseau horaire d’Edmundston (America/Moncton).
// Compléments des valeurs par défaut de l’Accueil (la page publique attend ces trois clés).
DEFAULT_SETTINGS.home.bienvenue = { lien: 'Page : Contact' };
DEFAULT_SETTINGS.home.invitation = { lien: 'Page : Contact' };
DEFAULT_SETTINGS.home.pied = { tcom: '', cciq: '' };

// Aucun événement ouvert aux inscriptions pour l’instant.
DEFAULT_SETTINGS.event_registration = {
  event_slug: '', event_title: '', date_str: '', location: '', description: '',
  total_seats: 0, max_per_reg: 1, deadline: '', is_open: false,
  opt_vege: false, opt_code: false, opt_agenda: false,
};

// Traductions : aucun remplacement enregistré.
DEFAULT_SETTINGS.traductions = { items: [] };

// Cours : le panneau « infos » existe dans le schéma ; ses textes restent à saisir.
DEFAULT_SETTINGS.cours.infos = { on: true, tarifs: '', essai: '', lieu: '', lieuTexte: '' };

// Lien d'un bouton de l'accueil : « Page : … » (page du site), « /p/<lien> » (page créée) ou https://….
// Toute autre valeur (ancienne page d'exemple, « Lien externe… » enregistré tel quel, javascript:…)
// revient à la valeur par défaut.
function homeLink(v, def) {
  if (typeof v !== 'string') return def;
  const t = v.trim();
  if (/^Page : [^<>"]{1,60}$/.test(t)) return t;
  if (/^\/p\/[a-z0-9]+(?:-[a-z0-9]+)*$/.test(t) && t.length <= 63) return t;
  if (/^https?:\/\/[^\s<>"]{3,}$/i.test(t) && t.length <= 500) return t;
  return def;
}

export function cleanHomeSettings(input) {
  if (!input || typeof input !== 'object') return DEFAULT_SETTINGS.home;
  const def = DEFAULT_SETTINGS.home;

  const out = {
    general: {
      email: typeof input.general?.email === 'string' ? input.general.email.trim() : def.general.email,
      facebook: typeof input.general?.facebook === 'string' ? input.general.facebook.trim() : def.general.facebook,
      address: typeof input.general?.address === 'string' ? input.general.address.trim() : def.general.address,
      city: typeof input.general?.city === 'string' ? input.general.city.trim() : def.general.city,
      mapUrl: typeof input.general?.mapUrl === 'string' ? input.general.mapUrl.trim() : def.general.mapUrl,
    },
    ordre: Array.isArray(input.ordre) ? input.ordre.filter((x) => def.ordre.includes(x)) : def.ordre,
    on: {},
    chargement: {
      duration: input.chargement?.duration === 'rapide' ? 'rapide' : 'normale',
    },
    hero: {
      h1: homeLink(input.hero?.h1, def.hero.h1),
      h2: homeLink(input.hero?.h2, def.hero.h2),
    },
    priere: {
      fajr: typeof input.priere?.fajr === 'string' ? input.priere.fajr.trim() : def.priere.fajr,
      lever: typeof input.priere?.lever === 'string' ? input.priere.lever.trim() : def.priere.lever,
      dohr: typeof input.priere?.dohr === 'string' ? input.priere.dohr.trim() : def.priere.dohr,
      jumua: typeof input.priere?.jumua === 'string' ? input.priere.jumua.trim() : def.priere.jumua,
      asr: typeof input.priere?.asr === 'string' ? input.priere.asr.trim() : def.priere.asr,
      maghreb: typeof input.priere?.maghreb === 'string' ? input.priere.maghreb.trim() : def.priere.maghreb,
      icha: typeof input.priere?.icha === 'string' ? input.priere.icha.trim() : def.priere.icha,
    },
    acces: {
      cartes: Array.isArray(input.acces?.cartes)
        ? input.acces.cartes.slice(0, def.acces.cartes.length).map((c, i) => ({
          id: def.acces.cartes[i].id,
          on: typeof c?.on === 'boolean' ? c.on : true,
          lien: homeLink(c?.lien, def.acces.cartes[i].lien),
        }))
        : def.acces.cartes,
    },
    campagne: {
      objectif: typeof input.campagne?.objectif === 'number' ? Math.max(0, input.campagne.objectif) : (parseInt(input.campagne?.objectif, 10) || def.campagne.objectif),
      recolte: typeof input.campagne?.recolte === 'number' ? Math.max(0, input.campagne.recolte) : (parseInt(input.campagne?.recolte, 10) || 0),
      btnInterac: homeLink(input.campagne?.btnInterac, def.campagne.btnInterac),
      btnSuivre: homeLink(input.campagne?.btnSuivre, def.campagne.btnSuivre),
    },
    annonces: {
      max: [1, 2, 3].includes(input.annonces?.max) ? input.annonces.max : def.annonces.max,
      btnTous: homeLink(input.annonces?.btnTous, def.annonces.btnTous),
      items: Array.isArray(input.annonces?.items)
        ? input.annonces.items.slice(0, 10).map((it, i) => ({
          id: typeof it?.id === 'number' ? it.id : i,
          date: typeof it?.date === 'string' ? it.date.slice(0, 40) : '',
          titre: typeof it?.titre === 'string' ? it.titre.slice(0, 160) : '',
          resume: typeof it?.resume === 'string' ? it.resume.slice(0, 400) : '',
          lien: homeLink(it?.lien, 'Page : Événements'),
          on: typeof it?.on === 'boolean' ? it.on : true,
        }))
        : def.annonces.items,
    },
    bienvenue: {
      lien: homeLink(input.bienvenue?.lien, def.bienvenue.lien),
    },
    invitation: {
      lien: homeLink(input.invitation?.lien, def.invitation.lien),
    },
    pied: {
      tcom: typeof input.pied?.tcom === 'string' ? input.pied.tcom.trim() : def.pied.tcom,
      cciq: typeof input.pied?.cciq === 'string' ? input.pied.cciq.trim() : def.pied.cciq,
    },
  };

  // On/Off switches
  for (const k of Object.keys(def.on)) {
    out.on[k] = input.on && typeof input.on[k] === 'boolean' ? input.on[k] : def.on[k];
  }

  // Ensure all sections are in ordre
  for (const o of def.ordre) {
    if (!out.ordre.includes(o)) out.ordre.push(o);
  }

  return out;
}

export function cleanEventRegistrationSettings(input) {
  const def = DEFAULT_SETTINGS.event_registration;
  if (!input || typeof input !== 'object') return { ...def };

  return {
    event_slug: typeof input.event_slug === 'string' && input.event_slug.trim() ? input.event_slug.trim().slice(0, 64) : def.event_slug,
    event_title: typeof input.event_title === 'string' && input.event_title.trim() ? input.event_title.trim().slice(0, 120) : def.event_title,
    date_str: typeof input.date_str === 'string' && input.date_str.trim() ? input.date_str.trim().slice(0, 120) : def.date_str,
    location: typeof input.location === 'string' && input.location.trim() ? input.location.trim().slice(0, 160) : def.location,
    description: typeof input.description === 'string' ? input.description.trim().slice(0, 500) : def.description,
    total_seats: typeof input.total_seats === 'number' ? Math.max(1, Math.min(10000, Math.floor(input.total_seats))) : (parseInt(input.total_seats, 10) || def.total_seats),
    max_per_reg: typeof input.max_per_reg === 'number' ? Math.max(1, Math.min(20, Math.floor(input.max_per_reg))) : (parseInt(input.max_per_reg, 10) || def.max_per_reg),
    deadline: typeof input.deadline === 'string' ? input.deadline.trim().slice(0, 20) : def.deadline,
    is_open: typeof input.is_open === 'boolean' ? input.is_open : def.is_open,
    opt_vege: typeof input.opt_vege === 'boolean' ? input.opt_vege : def.opt_vege,
    opt_code: typeof input.opt_code === 'boolean' ? input.opt_code : def.opt_code,
    opt_agenda: typeof input.opt_agenda === 'boolean' ? input.opt_agenda : def.opt_agenda,
  };
}

// « Site entier → Pages publiées » : réglage -> page du site public (versions PC, M- et T-).
// Accueil n'y figure pas : elle ne peut pas être masquée.
export const PAGE_FILES = {
  pg_horaires: 'Horaires', pg_apropos: 'APropos', pg_services: 'Services', pg_dons: 'Dons',
  pg_evenements: 'Evenements', pg_ressources: 'Ressources', pg_contact: 'Contact',
  pg_cours: 'N2-Cours', pg_mariages: 'N2-Mariages', pg_funerailles: 'N2-Funerailles',
  pg_aide: 'N2-AideAlimentaire', pg_femmes: 'N2-EspaceFemmes', pg_khutba: 'N2-Khutba',
  pg_rappel: 'N3-Rappel', pg_campagne: 'N3-Campagne', pg_calendrier: 'N3-Calendrier',
  pg_inscription: 'N3-Inscription', pg_dua: 'N3-Dua',
};

// Tant que rien n'est enregistré, tout reste publié : le site ne change pas tout seul.
DEFAULT_SETTINGS.pages = Object.fromEntries(Object.keys(PAGE_FILES).map((k) => [k, true]));

export function cleanPagesSettings(input) {
  const out = { ...DEFAULT_SETTINGS.pages };
  if (input && typeof input === 'object') {
    for (const k of Object.keys(out)) if (typeof input[k] === 'boolean') out[k] = input[k];
  }
  return out;
}

export async function readPagesSettings(db) {
  const row = await db.prepare("SELECT value FROM site_settings WHERE key = 'pages'").first();
  let saved = null;
  try { saved = row ? JSON.parse(row.value) : null; } catch { saved = null; }
  return cleanPagesSettings(saved);
}

const PAGE_BY_FILE = Object.fromEntries(Object.entries(PAGE_FILES).map(([k, f]) => [f, k]));

// '/M-N2-Cours.dc.html' ou '/N2-Cours.dc' -> 'pg_cours' ; null pour toute autre adresse.
export function pageSettingForPath(path) {
  const m = /^\/(?:M-|T-)?([A-Za-z0-9-]+?)\.dc(?:\.html)?$/.exec(path);
  return m ? PAGE_BY_FILE[m[1]] || null : null;
}

// Date de mise à jour des réglages : toujours au format ISO, comme la migration 0003.
export const nowIso = () => new Date().toISOString();

// Réglages de l'événement ouvert aux inscriptions (une seule lecture, partagée par les routes).
export async function readEventRegistrationSettings(db) {
  try {
    const row = await db.prepare("SELECT value FROM site_settings WHERE key = 'event_registration'").first();
    if (row && row.value) return cleanEventRegistrationSettings(JSON.parse(row.value));
  } catch (err) {
    console.warn('read event_registration error:', err && err.message);
  }
  return { ...DEFAULT_SETTINGS.event_registration };
}

// « Site entier → Saison et langues → Bannière d'alerte » : bande en haut de toutes les pages publiques.
// Désactivée tant que rien n'est enregistré.
DEFAULT_SETTINGS.alert = { on: false, message: '', link: { type: 'none' }, from: '', to: '', tone: 'attention' };
const ALERT_TONES = ['info', 'attention', 'urgent'];
const ISO_DAY = /^\d{4}-\d{2}-\d{2}$/;

export function cleanAlertSettings(input) {
  const def = DEFAULT_SETTINGS.alert;
  const i = input && typeof input === 'object' ? input : {};
  const day = (v) => (typeof v === 'string' && ISO_DAY.test(v) ? v : '');
  const out = {
    on: typeof i.on === 'boolean' ? i.on : def.on,
    message: typeof i.message === 'string' ? i.message.replace(/\s+/g, ' ').trim().slice(0, 200) : '',
    link: { type: 'none' },
    from: day(i.from),
    to: day(i.to),
    tone: ALERT_TONES.includes(i.tone) ? i.tone : def.tone,
  };
  const l = i.link && typeof i.link === 'object' ? i.link : {};
  if (l.type === 'page' && Object.prototype.hasOwnProperty.call(PAGE_FILES, l.page)) {
    out.link = { type: 'page', page: l.page };
  } else if (l.type === 'custom' && typeof l.slug === 'string' && /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(l.slug) && l.slug.length <= 60) {
    out.link = { type: 'custom', slug: l.slug };
  } else if (l.type === 'url' && typeof l.url === 'string' && /^https?:\/\/[^\s]{3,}$/i.test(l.url.trim()) && l.url.length <= 500) {
    out.link = { type: 'url', url: l.url.trim() };
  }
  // Période à l'envers : on garde le début, on efface la fin plutôt que de ne jamais afficher.
  if (out.from && out.to && out.to < out.from) out.to = '';
  // Une bannière sans message ne peut pas être affichée : cohérence garantie entre message vide et « Afficher ».
  if (!out.message) out.on = false;
  return out;
}

// « Site entier → Saison et langues → Mode du site ».
// auto = true : le mode n'est actif qu'entre les dates (bornes incluses) ; auto = false : le mode
// choisi s'applique tout de suite, jusqu'à ce qu'on le change. « normal » = rien de particulier.
// vendredi : thème du vendredi (Jumu’a). 'off' = désactivé, 'on' = affiché tous les jours (jusqu’à ce qu’on le
// désactive), 'auto' = affiché chaque vendredi seulement (heure d’Edmundston). Une saison active passe avant.
DEFAULT_SETTINGS.season = { mode: 'normal', from: '', to: '', auto: true, vendredi: 'off' };
const SEASON_MODES = ['normal', 'ramadan', 'aid_fitr', 'aid_adha'];
export const VENDREDI_MODES = ['off', 'on', 'auto'];

export function cleanSeasonSettings(input) {
  const i = input && typeof input === 'object' ? input : {};
  const day = (v) => (typeof v === 'string' && ISO_DAY.test(v) ? v : '');
  const out = {
    mode: SEASON_MODES.includes(i.mode) ? i.mode : 'normal',
    from: day(i.from),
    to: day(i.to),
    auto: typeof i.auto === 'boolean' ? i.auto : true,
    vendredi: VENDREDI_MODES.includes(i.vendredi) ? i.vendredi : 'off',
  };
  if (out.from && out.to && out.to < out.from) out.to = '';
  return out;
}

// Thème du vendredi en vigueur aujourd’hui (date AAAA-MM-JJ, heure d’Edmundston).
export function activeVendredi(season, today) {
  const s = cleanSeasonSettings(season);
  if (s.vendredi === 'on') return true;
  if (s.vendredi !== 'auto' || !ISO_DAY.test(today || '')) return false;
  return new Date(`${today}T12:00:00Z`).getUTCDay() === 5;
}

// Mode de saison en vigueur aujourd'hui (date AAAA-MM-JJ, heure d’Edmundston) : 'normal' sinon.
export function activeSeasonMode(season, today) {
  const s = cleanSeasonSettings(season);
  if (s.mode === 'normal') return 'normal';
  if (!s.auto) return s.mode;
  return s.from && s.to && today >= s.from && today <= s.to ? s.mode : 'normal';
}

export async function readSeasonSettings(db) {
  try {
    const row = await db.prepare("SELECT value FROM site_settings WHERE key = 'season'").first();
    if (row && row.value) return cleanSeasonSettings(JSON.parse(row.value));
  } catch (err) {
    console.warn('read season error:', err && err.message);
  }
  return { ...DEFAULT_SETTINGS.season };
}

// « Site entier → Saison et langues → Langues » : langues proposées dans le sélecteur du site.
// Le français est toujours actif. Par défaut, les trois restent visibles (comme avant ce réglage).
DEFAULT_SETTINGS.languages = { fr: true, ar: true, en: true };

export function cleanLanguagesSettings(input) {
  const i = input && typeof input === 'object' ? input : {};
  return {
    fr: true,
    ar: typeof i.ar === 'boolean' ? i.ar : true,
    en: typeof i.en === 'boolean' ? i.en : true,
  };
}

// « Horaires » : réglages de la page publique Horaires (les heures elles-mêmes sont dans la table
// prayer_times, une ligne par jour). Les dates du Ramadan viennent de « Site entier → Mode du site »
// (clé season) ; l'heure de Jumu'a vient du tableau du mois. Valeurs par défaut = page actuelle.
// Pour Edmundston : le lieu de l’Aïd et son itinéraire restent à saisir, ainsi que la direction de la Qibla.
DEFAULT_SETTINGS.horaires = {
  aujourdhui: { on: true, compte: true, hijri: true, lienRappel: true, lienKhutba: true },
  mois: { vendredis: true },
  vendredi: { on: true, avance: 15, conseil: true },
  ramadan: { on: true, suhoor: true, iftar: true, tarawih: false, tarawihHeure: '' },
  aid: {
    on: true, lieu: '',
    itineraire: '',
    fitrDate: '', fitrHeure: '', adhaDate: '', adhaHeure: '',
  },
  qibla: { on: true, degres: '', repere: '' },
};
const HHMM = /^([01]\d|2[0-3]):[0-5]\d$/;

export function cleanHorairesSettings(input) {
  const def = DEFAULT_SETTINGS.horaires;
  const i = input && typeof input === 'object' ? input : {};
  const bool = (sec, k) => (typeof i[sec]?.[k] === 'boolean' ? i[sec][k] : def[sec][k]);
  const text = (sec, k, max) => (typeof i[sec]?.[k] === 'string' ? i[sec][k].replace(/\s+/g, ' ').trim().slice(0, max) : def[sec][k]);
  const day = (sec, k) => (typeof i[sec]?.[k] === 'string' && ISO_DAY.test(i[sec][k]) ? i[sec][k] : '');
  const time = (sec, k) => (typeof i[sec]?.[k] === 'string' && HHMM.test(i[sec][k]) ? i[sec][k] : '');
  const avance = Number(i.vendredi?.avance);
  const deg = typeof i.qibla?.degres === 'string' ? i.qibla.degres.trim().replace('.', ',') : def.qibla.degres;
  const degNum = Number(deg.replace(',', '.'));
  const url = typeof i.aid?.itineraire === 'string' ? i.aid.itineraire.trim() : def.aid.itineraire;
  return {
    aujourdhui: { on: bool('aujourdhui', 'on'), compte: bool('aujourdhui', 'compte'), hijri: bool('aujourdhui', 'hijri'),
      lienRappel: bool('aujourdhui', 'lienRappel'), lienKhutba: bool('aujourdhui', 'lienKhutba') },
    mois: { vendredis: bool('mois', 'vendredis') },
    vendredi: { on: bool('vendredi', 'on'),
      avance: Number.isInteger(avance) && avance >= 0 && avance <= 120 ? avance : def.vendredi.avance,
      conseil: bool('vendredi', 'conseil') },
    ramadan: { on: bool('ramadan', 'on'), suhoor: bool('ramadan', 'suhoor'), iftar: bool('ramadan', 'iftar'),
      tarawih: bool('ramadan', 'tarawih'), tarawihHeure: time('ramadan', 'tarawihHeure') },
    aid: {
      on: bool('aid', 'on'), lieu: text('aid', 'lieu', 120),
      itineraire: /^https?:\/\/[^\s<>"]{3,}$/i.test(url) && url.length <= 500 ? url : (url ? def.aid.itineraire : ''),
      fitrDate: day('aid', 'fitrDate'), fitrHeure: time('aid', 'fitrHeure'),
      adhaDate: day('aid', 'adhaDate'), adhaHeure: time('aid', 'adhaHeure'),
    },
    qibla: { on: bool('qibla', 'on'), degres: Number.isFinite(degNum) && degNum >= 0 && degNum < 360 ? deg : def.qibla.degres,
      repere: text('qibla', 'repere', 160) },
  };
}

// Horaires → Langue de la khutba (clé khutba). Une ligne par vendredi (date AAAA-MM-JJ, un vendredi),
// triées par date ; le site montre les vendredis à venir, dans la limite de « nombre ».
export const KHUTBA_LANGUES = ['Français', 'Arabe', 'Anglais', 'Arabe et français'];
export const KHUTBA_TRADUCTIONS = ['Aucune', 'Arabe', 'Français', 'Anglais'];
export const KHUTBA_MODES = ['Résumé imprimé à l’entrée', 'Traduction orale', 'Écran'];
DEFAULT_SETTINGS.khutba = {
  vendredis: [],
  nombre: 4,
  mode: 'Résumé imprimé à l’entrée',
};

export function cleanKhutbaSettings(input) {
  const def = DEFAULT_SETTINGS.khutba;
  const i = input && typeof input === 'object' ? input : {};
  const seen = new Set();
  const list = (Array.isArray(i.vendredis) ? i.vendredis : def.vendredis)
    .filter((v) => v && typeof v === 'object' && typeof v.date === 'string' && ISO_DAY.test(v.date)
      && new Date(`${v.date}T12:00:00Z`).getUTCDay() === 5)
    .filter((v) => (seen.has(v.date) ? false : (seen.add(v.date), true)))
    .slice(0, 60)
    .map((v) => ({
      date: v.date,
      langue: KHUTBA_LANGUES.includes(v.langue) ? v.langue : 'Arabe',
      traduction: KHUTBA_TRADUCTIONS.includes(v.traduction) ? v.traduction : 'Aucune',
      imam: typeof v.imam === 'string' ? v.imam.replace(/\s+/g, ' ').trim().slice(0, 80) : '',
      on: typeof v.on === 'boolean' ? v.on : true,
    }))
    .sort((a, b) => (a.date < b.date ? -1 : 1));
  const nombre = Number(i.nombre);
  return {
    vendredis: list,
    nombre: [2, 4, 6, 8].includes(nombre) ? nombre : def.nombre,
    mode: KHUTBA_MODES.includes(i.mode) ? i.mode : def.mode,
  };
}

// Horaires → Rappel de prière (clé rappel) : prières proposées aux visiteurs, délais, notification.
export const RAPPEL_DELAIS = [5, 10, 15, 30, 60];
DEFAULT_SETTINGS.rappel = {
  prieres: { fajr: true, dohr: false, jumua: true, asr: false, maghreb: false, icha: true },
  delais: [5, 10, 15, 30, 60],
  defaut: 15,
  titre: 'Prière dans {délai}',
  son: true,
  vibration: true,
};

export function cleanRappelSettings(input) {
  const def = DEFAULT_SETTINGS.rappel;
  const i = input && typeof input === 'object' ? input : {};
  const prieres = {};
  Object.keys(def.prieres).forEach((k) => {
    prieres[k] = typeof i.prieres?.[k] === 'boolean' ? i.prieres[k] : def.prieres[k];
  });
  let delais = Array.isArray(i.delais) ? RAPPEL_DELAIS.filter((d) => i.delais.map(Number).includes(d)) : def.delais.slice();
  if (!delais.length) delais = [15];
  const defaut = Number(i.defaut);
  const titre = typeof i.titre === 'string' ? i.titre.replace(/\s+/g, ' ').trim().slice(0, 80) : def.titre;
  return {
    prieres,
    delais,
    defaut: delais.includes(defaut) ? defaut : (delais.includes(def.defaut) ? def.defaut : delais[0]),
    titre: titre || def.titre,
    son: typeof i.son === 'boolean' ? i.son : def.son,
    vibration: typeof i.vibration === 'boolean' ? i.vibration : def.vibration,
  };
}

// À propos → L’association (clé apropos). Les blocs reprennent le contenu d’origine de la page publique.
// Une étape d’histoire sans date reste masquée ; l’équipe n’est publiée qu’avec l’accord écrit et un nom.
const PHOTO_RE = /^data:image\/(?:jpeg|png|webp);base64,[A-Za-z0-9+/]+={0,2}$/;
export const PHOTO_MAX = 100000;
DEFAULT_SETTINGS.apropos = {
  presentation: {
    on: true,
    texte: 'Le Centre Islamique d’Edmundston rassemble les musulmanes et les musulmans d’Edmundston et de la région. Il tient un lieu de prière, organise la prière du vendredi, les prières de l’Aïd et des activités de solidarité, et accueille les nouveaux arrivants.',
  },
  valeurs: {
    on: true,
    items: [
      { titre: 'Prier ensemble', texte: 'Les cinq prières quotidiennes et la prière du vendredi (Jumu’a).', on: true },
      { titre: 'Se soutenir', texte: 'Accueil, solidarité et événements caritatifs dans la communauté.', on: true },
      { titre: 'S’ancrer ici', texte: 'Une communauté du Nouveau-Brunswick, ouverte sur sa ville et ses voisins.', on: true },
    ],
  },
  histoire: {
    on: true,
    items: [
      { date: '', titre: 'Fondation de l’association', on: true },
    ],
  },
  projet: { on: true, btnSoutenir: 'Page : Faire un don', btnSuivre: 'Page : Campagne en direct' },
  equipe: {
    on: false,
    accord: false,
    items: [
      { nom: '', role: 'Président', photo: '', on: true },
      { nom: '', role: 'Imam', photo: '', on: true },
      { nom: '', role: 'Membre du conseil', photo: '', on: true },
    ],
  },
  chiffres: { on: true, items: [] },
};

const oneLine = (v, max) => (typeof v === 'string' ? v.replace(/\s+/g, ' ').trim().slice(0, max) : '');
const boolOr = (v, d) => (typeof v === 'boolean' ? v : d);
function listOf(v, def, max, fn) {
  return (Array.isArray(v) ? v : def).filter((x) => x && typeof x === 'object').slice(0, max).map(fn);
}

export function cleanAproposSettings(input) {
  const def = DEFAULT_SETTINGS.apropos;
  const i = input && typeof input === 'object' ? input : {};
  const part = (k) => (i[k] && typeof i[k] === 'object' ? i[k] : {});
  const pres = part('presentation'), val = part('valeurs'), hist = part('histoire');
  const proj = part('projet'), eq = part('equipe'), chif = part('chiffres');
  const texte = typeof pres.texte === 'string'
    ? pres.texte.replace(/\r/g, '').split('\n').map((l) => l.replace(/\s+/g, ' ').trim()).join('\n').replace(/\n{3,}/g, '\n\n').trim().slice(0, 1500)
    : def.presentation.texte;
  return {
    presentation: { on: boolOr(pres.on, def.presentation.on), texte },
    valeurs: {
      on: boolOr(val.on, def.valeurs.on),
      items: listOf(val.items, def.valeurs.items, 6, (x) => ({ titre: oneLine(x.titre, 80), texte: oneLine(x.texte, 300), on: boolOr(x.on, true) })),
    },
    histoire: {
      on: boolOr(hist.on, def.histoire.on),
      items: listOf(hist.items, def.histoire.items, 12, (x) => ({
        date: typeof x.date === 'string' && ISO_DAY.test(x.date) ? x.date : '',
        titre: oneLine(x.titre, 120),
        on: boolOr(x.on, true),
      })),
    },
    projet: {
      on: boolOr(proj.on, def.projet.on),
      btnSoutenir: homeLink(proj.btnSoutenir, def.projet.btnSoutenir),
      btnSuivre: homeLink(proj.btnSuivre, def.projet.btnSuivre),
    },
    equipe: {
      on: boolOr(eq.on, def.equipe.on),
      accord: boolOr(eq.accord, def.equipe.accord),
      items: listOf(eq.items, def.equipe.items, 8, (x) => ({
        nom: oneLine(x.nom, 80),
        role: oneLine(x.role, 80),
        photo: typeof x.photo === 'string' && x.photo.length <= PHOTO_MAX && PHOTO_RE.test(x.photo) ? x.photo : '',
        on: boolOr(x.on, true),
      })),
    },
    chiffres: {
      on: boolOr(chif.on, def.chiffres.on),
      items: listOf(chif.items, def.chiffres.items, 6, (x) => ({
        valeur: oneLine(x.valeur, 20), libelle: oneLine(x.libelle, 160), source: oneLine(x.source, 120), on: boolOr(x.on, true),
      })),
    },
  };
}

// À propos → Campagne en direct (clé campagne). L’objectif et le montant récolté restent dans
// home.campagne (communs à l’accueil) ; en mode automatique, récolté, donateurs, semaines et
// derniers dons sont calculés à partir de la table donations (functions/_lib/campagne.js).
export const CAMPAGNE_NOMS = ['prenom', 'initiales', 'anonyme'];
DEFAULT_SETTINGS.campagne = {
  donateurs: 0,
  auto: false,
  etapes: { on: true, items: [] },
  semaines: { on: true, nombre: 8, valeurs: [] },
  derniers: { on: true, nombre: 5, nom: 'prenom', montant: true },
};

// « 12 500 », « 12 500 $ » ou 12500 -> 12500 ; null si ce n'est pas un montant.
export function wholeAmount(v, max) {
  const n = typeof v === 'number' ? v : Number(String(v == null ? '' : v).replace(/[\s\u00A0\u202F$]/g, '').replace(',', '.'));
  if (!Number.isFinite(n) || n < 0) return null;
  return Math.min(Math.round(n), max);
}

export function cleanCampagneSettings(input) {
  const def = DEFAULT_SETTINGS.campagne;
  const i = input && typeof input === 'object' ? input : {};
  const et = i.etapes && typeof i.etapes === 'object' ? i.etapes : {};
  const se = i.semaines && typeof i.semaines === 'object' ? i.semaines : {};
  const de = i.derniers && typeof i.derniers === 'object' ? i.derniers : {};
  const nombre = Number(se.nombre), dn = Number(de.nombre);
  return {
    donateurs: wholeAmount(i.donateurs, 1000000) ?? def.donateurs,
    auto: boolOr(i.auto, def.auto),
    etapes: {
      on: boolOr(et.on, def.etapes.on),
      items: listOf(et.items, def.etapes.items, 8, (x) => ({
        seuil: Math.max(0, Math.min(100, wholeAmount(x.seuil, 100) ?? 0)), libelle: oneLine(x.libelle, 120), on: boolOr(x.on, true),
      })).sort((a, b) => a.seuil - b.seuil),
    },
    semaines: {
      on: boolOr(se.on, def.semaines.on),
      nombre: [4, 8, 12].includes(nombre) ? nombre : def.semaines.nombre,
      valeurs: (Array.isArray(se.valeurs) ? se.valeurs : def.semaines.valeurs).slice(0, 12).map((v) => wholeAmount(v, 100000000) ?? 0),
    },
    derniers: {
      on: boolOr(de.on, def.derniers.on),
      nombre: [3, 5, 10].includes(dn) ? dn : def.derniers.nombre,
      nom: CAMPAGNE_NOMS.includes(de.nom) ? de.nom : def.derniers.nom,
      montant: boolOr(de.montant, def.derniers.montant),
    },
  };
}

// Services → Tous les services (clé services). Cartes de la page Services, dans l'ordre.
// Trois cartes ont un rôle propre : prieres (heures de Fajr et d'Icha du tableau du mois),
// jumua (heure de Jumu'a, lignes khutba et espace femmes), aid (lieu repris de horaires.aid.lieu,
// Zakat al-Fitr). Les autres sont libres (kind 'libre') et peuvent être ajoutées ou supprimées.
export const SERVICE_KINDS = ['prieres', 'jumua', 'aid', 'libre'];
const SERVICE_BASE = { titre: '', texte: '', icone: 0, saison: false, lien: '', lienTexte: '', khutba: false, femmes: false, zakat: null, zakatAnnee: '', on: true };
DEFAULT_SETTINGS.services = {
  items: [
    { ...SERVICE_BASE, kind: 'prieres', titre: 'Les cinq prières quotidiennes', texte: 'À la mosquée, tous les jours.', icone: 0,
      lien: 'Page : Horaires du mois', lienTexte: 'Tableau complet des horaires' },
    { ...SERVICE_BASE, kind: 'jumua', titre: 'La prière du vendredi (Jumu’a)', texte: 'Khutba suivie de la prière.', icone: 1, khutba: true, femmes: true },
    { ...SERVICE_BASE, kind: 'libre', titre: 'Ramadan : Iftar et Tarawih', icone: 2, saison: true,
      texte: 'Proposés pendant le mois de Ramadan, avec des dates publiées chaque année dès l’annonce officielle.' },
    { ...SERVICE_BASE, kind: 'aid', titre: 'Les prières de l’Aïd', icone: 3, saison: true, zakat: 15, zakatAnnee: '2025' },
    { ...SERVICE_BASE, kind: 'libre', titre: 'Solidarité et événements caritatifs', icone: 4, lien: 'Page : Événements', lienTexte: 'Voir les événements',
      texte: 'Entraide et événements caritatifs dans la communauté.' },
  ],
  autres: { on: true, cours: true, mariages: true, funerailles: true, aide: true, femmes: true, khutba: true },
  equipements: { on: true, fauteuil: true, ablutions: true, parking: true, femmes: false },
  question: { on: true, lien: 'Page : Contact' },
};

export function cleanServicesSettings(input) {
  const def = DEFAULT_SETTINGS.services;
  const i = input && typeof input === 'object' ? input : {};
  const seen = new Set();
  const items = listOf(i.items, def.items, 12, (x) => {
    const kind = SERVICE_KINDS.includes(x.kind) ? x.kind : 'libre';
    const icone = Number(x.icone);
    const zak = x.zakat === null || x.zakat === '' || x.zakat === undefined ? null : wholeAmount(x.zakat, 10000);
    return {
      kind,
      titre: oneLine(x.titre, 80),
      texte: typeof x.texte === 'string' ? x.texte.replace(/\r/g, '').split('\n').map((l) => l.replace(/\s+/g, ' ').trim()).join('\n').trim().slice(0, 400) : '',
      icone: [0, 1, 2, 3, 4].includes(icone) ? icone : 0,
      saison: boolOr(x.saison, false),
      lien: x.lien === '' ? '' : homeLink(x.lien, ''),
      lienTexte: oneLine(x.lienTexte, 60),
      khutba: boolOr(x.khutba, false),
      femmes: boolOr(x.femmes, false),
      zakat: zak,
      zakatAnnee: oneLine(x.zakatAnnee, 12),
      on: boolOr(x.on, true),
    };
  }).filter((x) => (x.kind === 'libre' ? true : (seen.has(x.kind) ? false : (seen.add(x.kind), true))));
  // Les trois cartes à rôle propre existent toujours (masquées si elles avaient disparu).
  for (const k of ['prieres', 'jumua', 'aid']) {
    if (!seen.has(k)) items.push({ ...def.items.find((x) => x.kind === k), on: false });
  }
  const sec = (k) => (i[k] && typeof i[k] === 'object' ? i[k] : {});
  const flags = (k) => Object.fromEntries(Object.keys(def[k]).map((f) => [f, boolOr(sec(k)[f], def[k][f])]));
  return {
    items,
    autres: flags('autres'),
    equipements: flags('equipements'),
    question: { on: boolOr(sec('question').on, def.question.on), lien: homeLink(sec('question').lien, def.question.lien) },
  };
}

// ---------------------------------------------------------------------------------------------
// Pages des services (étapes S3 à S5) : Cours, Mariages, Funérailles, Aide alimentaire, Espace femmes.
// Chaque clé est nettoyée d'après un schéma : ['s', max] une ligne, ['t', max] texte sur plusieurs
// lignes, ['b'] oui/non, ['n', min, max] nombre entier, ['hm'] heure HH:MM, ['date'] AAAA-MM-JJ,
// ['e', [valeurs]] choix, ['set', [valeurs]] plusieurs choix, ['img', max] image réduite,
// ['list', max, {champs}] liste, ['fixed', n, {champs}] liste de longueur fixe, {…} objet.
const HM_RE = /^([01]\d|2[0-3]):[0-5]\d$/;
const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;
const multi = (v, max) => (typeof v === 'string'
  ? v.replace(/\r/g, '').split('\n').map((l) => l.replace(/\s+/g, ' ').trim()).join('\n').replace(/\n{3,}/g, '\n\n').trim().slice(0, max)
  : '');

function cleanWith(spec, v, d) {
  if (Array.isArray(spec)) {
    const [t, a, b] = spec;
    switch (t) {
      case 's': return typeof v === 'string' ? oneLine(v, a) : d;
      case 't': return typeof v === 'string' ? multi(v, a) : d;
      case 'b': return boolOr(v, d);
      case 'n': {
        if (v === '' || v === null) return d;
        const n = typeof v === 'number' ? v : Number(String(v).replace(',', '.'));
        return Number.isFinite(n) ? Math.min(b, Math.max(a, Math.round(n))) : d;
      }
      case 'hm': return typeof v === 'string' && (v === '' || HM_RE.test(v)) ? v : d;
      case 'date': return typeof v === 'string' && (v === '' || DATE_RE.test(v)) ? v : d;
      case 'e': return a.includes(v) ? v : d;
      case 'set': return Array.isArray(v) ? a.filter((x) => v.includes(x)) : d;
      case 'img': return typeof v === 'string' && (v === '' || (v.length <= a && PHOTO_RE.test(v))) ? v : d;
      case 'list': {
        const tmpl = Array.isArray(d) && d.length ? d[0] : {};
        const src = Array.isArray(v) ? v : d;
        return src.filter((x) => x && typeof x === 'object').slice(0, a).map((x) => cleanWith(b, x, Array.isArray(v) ? itemDefault(b, tmpl) : x));
      }
      case 'fixed': {
        const src = Array.isArray(v) ? v : [];
        return d.map((dx, k) => cleanWith(b, src[k] && typeof src[k] === 'object' ? src[k] : dx, dx));
      }
      default: return d;
    }
  }
  const o = v && typeof v === 'object' && !Array.isArray(v) ? v : {};
  const out = {};
  for (const k of Object.keys(spec)) out[k] = cleanWith(spec[k], o[k], d ? d[k] : undefined);
  return out;
}

// Valeur par défaut d'un nouvel élément de liste : champs vides, interrupteurs comme le modèle.
function itemDefault(spec, tmpl) {
  const out = {};
  for (const k of Object.keys(spec)) {
    const t = Array.isArray(spec[k]) ? spec[k][0] : 'obj';
    out[k] = t === 'b' ? (tmpl[k] !== undefined ? tmpl[k] : true) : t === 'set' ? [] : t === 'n' ? 0 : t === 'e' ? tmpl[k] : t === 'obj' ? itemDefault(spec[k], tmpl[k] || {}) : '';
  }
  return out;
}

const AGES = ['5-8', '9-12', '13-17', 'adulte'];
const NIVEAUX = ['deb', 'int', 'av'];
const JOURS = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche'];
const LIST_ITEM = { titre: ['s', 160], on: ['b'] };

export const SERVICE_PAGE_SCHEMAS = {
  cours: {
    annee: ['s', 20], delai: ['e', ['24 h', '48 h', '1 semaine']], essai: ['b'], attente: ['b'], inscriptions: ['b'],
    items: ['list', 30, {
      titre: ['s', 80], matiere: ['e', ['coran', 'arabe']], ages: ['set', AGES], niveaux: ['set', NIVEAUX], jour: ['e', JOURS],
      debut: ['hm'], fin: ['hm'], places: ['n', 0, 999], prix: ['n', 0, 10000], prof: ['s', 80], on: ['b'],
    }],
    infos: { on: ['b'], tarifs: ['t', 400], essai: ['t', 400], lieu: ['s', 80], lieuTexte: ['t', 400] },
  },
  mariages: {
    duree: ['s', 40], delai: ['s', 40],
    etapes: ['list', 10, { titre: ['s', 80], quand: ['s', 40], texte: ['t', 600], on: ['b'] }],
    docs: { on: ['b'], items: ['list', 15, LIST_ITEM] },
    form: { on: ['b'] },
  },
  funerailles: {
    responsable: ['s', 80], telephone: ['s', 30], courriel: ['s', 120], h24: ['b'], rappel911: ['b'],
    etapes: ['list', 10, { titre: ['s', 80], texte: ['t', 600], on: ['b'] }],
    docs: { on: ['b'], items: ['list', 15, LIST_ITEM] },
    charge: { on: ['b'], texte: ['t', 600] },
  },
  aide: {
    form: { on: ['b'], besoins: ['list', 8, { titre: ['s', 40], on: ['b'] }], recup: ['b'], livraison: ['b'], delai: ['e', ['24 h', '48 h', '72 h']] },
    manque: { on: ['b'], items: ['list', 15, { titre: ['s', 60], niveau: ['e', ['tres', 'demande', 'suffisant']], on: ['b'] }] },
    depot: { on: ['b'], adresse: ['s', 120], quand: ['s', 120], note: ['t', 300] },
    argent: { on: ['b'], courriel: ['s', 120], note: ['t', 300] },
  },
  femmes: {
    jours: ['fixed', 7, { on: ['b'], de1: ['hm'], a1: ['hm'], de2: ['hm'], a2: ['hm'] }],
    fermeture: ['date'], plan: ['img', 200000],
    pratique: { on: ['b'], entree: ['s', 160], acces: ['s', 160], ablutions: ['s', 160], jumua: ['s', 160], enfants: ['s', 160], responsable: ['s', 160] },
    regles: { on: ['b'], items: ['list', 15, LIST_ITEM] },
  },
};

// Nettoyeurs des pages de services : chaque clé est nettoyée d'après son schéma et ses valeurs par défaut.
// Déclarés comme fonctions (plutôt que const) pour que GENERIC_KEYS, défini plus haut dans le fichier,
// puisse les utiliser dès le chargement du module.
export function cleanCoursSettings(input) { return cleanWith(SERVICE_PAGE_SCHEMAS.cours, input, DEFAULT_SETTINGS.cours); }
export function cleanMariagesSettings(input) { return cleanWith(SERVICE_PAGE_SCHEMAS.mariages, input, DEFAULT_SETTINGS.mariages); }
export function cleanFuneraillesSettings(input) { return cleanWith(SERVICE_PAGE_SCHEMAS.funerailles, input, DEFAULT_SETTINGS.funerailles); }
export function cleanAideSettings(input) { return cleanWith(SERVICE_PAGE_SCHEMAS.aide, input, DEFAULT_SETTINGS.aide); }
export function cleanFemmesSettings(input) { return cleanWith(SERVICE_PAGE_SCHEMAS.femmes, input, DEFAULT_SETTINGS.femmes); }

DEFAULT_SETTINGS.mariages = {
  duree: 'environ 6 semaines', delai: '3 jours ouvrables',
  etapes: [
    { titre: 'Premier contact', quand: 'Jour 1', texte: 'Remplissez la demande de rendez-vous ci-dessous. L’association vous répond sous 3 jours ouvrables avec une date de rencontre.', on: true },
    { titre: 'Rencontre avec l’imam', quand: 'Semaine 1 à 2', texte: 'Un entretien de 45 minutes avec les deux futurs époux : intentions, conditions du contrat, mahr et questions pratiques.', on: true },
    { titre: 'Documents', quand: 'Semaine 2 à 4', texte: 'Rassemblez les documents de la liste. Cochez-les au fur et à mesure : votre progression s’affiche.', on: true },
    { titre: 'Cérémonie (nikah)', quand: 'Semaine 4 à 6', texte: 'Célébration à la mosquée, en présence du tuteur (wali) et de deux témoins. Prévoyez environ 45 minutes.', on: true },
    { titre: 'Démarches civiles', quand: 'À coordonner', texte: 'Le mariage religieux et le mariage civil sont deux démarches distinctes. L’association vous indique comment les coordonner au Québec.', on: true },
  ],
  docs: {
    on: true,
    items: docs('Pièce d’identité avec photo des deux époux', 'Coordonnées de deux témoins musulmans', 'Accord du tuteur (wali) de l’épouse',
      'Montant ou nature du mahr convenu', 'Certificat de divorce ou de décès du conjoint précédent, s’il y a lieu', 'Preuve des démarches civiles (si déjà faites)'),
  },
  form: { on: true },
};
DEFAULT_SETTINGS.funerailles = {
  responsable: '', telephone: '', courriel: '', h24: true, rappel911: true,
  etapes: [
    { titre: 'Appelez l’association', texte: 'À tout moment, jour et nuit. Un bénévole vous rappelle en moins de 30 minutes et vous accompagne pour la suite.', on: true },
    { titre: 'Obtenez le constat de décès', texte: 'Il est délivré par le médecin ou l’hôpital. Gardez-en une copie : il sera demandé pour toutes les démarches.', on: true },
    { titre: 'Contactez l’entreprise funéraire', texte: 'L’association vous oriente vers une entreprise qui connaît les rites musulmans (toilette mortuaire, linceul, transport).', on: true },
    { titre: 'Toilette mortuaire et prière de la janaza', texte: 'La toilette (ghusl) est faite par des bénévoles du même sexe. La prière de la janaza a lieu le plus tôt possible, idéalement dans les 24 à 48 heures.', on: true },
    { titre: 'Inhumation', texte: 'Dans la section musulmane d’un cimetière de la région, ou rapatriement si la famille le souhaite. L’association vous aide dans les démarches.', on: true },
  ],
  docs: { on: true, items: docs('Constat de décès', 'Pièce d’identité du défunt', 'Carte d’assurance maladie', 'Coordonnées d’un membre de la famille') },
  charge: { on: true, texte: 'Accompagnement de la famille, organisation de la toilette mortuaire et de la prière de la janaza, mise en relation avec l’entreprise funéraire.' },
};
DEFAULT_SETTINGS.aide = {
  form: { on: true, besoins: docs('Épicerie', 'Produits halal', 'Produits pour bébé', 'Repas du Ramadan'), recup: true, livraison: true, delai: '48 h' },
  manque: {
    on: true,
    items: [
      { titre: 'Riz, pâtes, semoule', niveau: 'tres', on: true }, { titre: 'Huile et conserves', niveau: 'demande', on: true },
      { titre: 'Lait et aliments pour bébé', niveau: 'demande', on: true }, { titre: 'Couches', niveau: 'demande', on: true },
      { titre: 'Produits d’hygiène', niveau: 'tres', on: true },
    ],
  },
  depot: { on: true, adresse: '', quand: '', note: 'Produits non périssables, non ouverts, non périmés.' },
  argent: { on: true, courriel: '', note: 'Indiquez « aide alimentaire » dans le message.' },
};
DEFAULT_SETTINGS.femmes = {
  jours: [
    { on: false, de1: '', a1: '', de2: '', a2: '' },
    { on: false, de1: '', a1: '', de2: '', a2: '' },
    { on: false, de1: '', a1: '', de2: '', a2: '' },
    { on: false, de1: '', a1: '', de2: '', a2: '' },
    { on: false, de1: '', a1: '', de2: '', a2: '' },
    { on: false, de1: '', a1: '', de2: '', a2: '' },
    { on: false, de1: '', a1: '', de2: '', a2: '' },
  ],
  fermeture: '', plan: '',
  pratique: { on: false, entree: '', acces: '', ablutions: '', jumua: '', enfants: '', responsable: '' },
  regles: {
    on: true,
    items: docs('Tenue couvrante ; des foulards sont prêtés à l’entrée.', 'Téléphones en silencieux pendant la prière.',
      'Les enfants restent accompagnés.', 'Merci de ranger tapis et chaises après les cours.'),
  },
};

// Faire un don (clés dons et merci). L’objectif et le montant récolté restent dans home.campagne ;
// le montant de la zakat al-Fitr reste dans services (carte Aïd) : une seule source par valeur.
const DON_LIENS = ['', 'contact', 'courriel'];
export const DONS_SCHEMA = {
  barre: ['b'], suivi: ['b'],
  interac: {
    on: ['b'], courriel: ['s', 120], m1: ['n', 0, 100000], m2: ['n', 0, 100000], m3: ['n', 0, 100000],
    defaut: ['e', ['m1', 'm2', 'm3', 'aucun']], autre: ['b'], etapes: ['b'],
  },
  desjardins: { on: ['b'], institution: ['s', 10], transit: ['s', 10], compte: ['s', 20] },
  autres: {
    on: ['b'],
    items: ['list', 8, { titre: ['s', 60], arabe: ['s', 40], texte: ['t', 400], fitr: ['b'], lien: ['e', DON_LIENS], lienTexte: ['s', 60], on: ['b'] }],
  },
  faq: { on: ['b'], items: ['list', 12, { titre: ['s', 160], texte: ['t', 1200], on: ['b'] }] },
  recus: { statut: ['b'], numero: ['s', 30] },
};
DEFAULT_SETTINGS.dons = {
  barre: true, suivi: true,
  interac: { on: true, courriel: '', m1: 20, m2: 50, m3: 100, defaut: 'm2', autre: true, etapes: true },
  desjardins: { on: true, institution: '', transit: '', compte: '' },
  autres: {
    on: true,
    items: [
      { titre: 'Sadaqa', arabe: 'صدقة', texte: 'Don libre, en tout temps, par Interac à la même adresse.', fitr: false, lien: '', lienTexte: '', on: true },
      { titre: 'Zakat al-mal', arabe: 'زكاة المال', texte: 'L’aumône obligatoire sur les biens. Pour la verser par l’association, écrivez-nous.', fitr: false, lien: 'contact', lienTexte: 'Écrire à l’association', on: true },
      { titre: 'Zakat al-Fitr', arabe: 'زكاة الفطر', texte: 'Montant mis à jour chaque Ramadan.', fitr: true, lien: '', lienTexte: '', on: true },
    ],
  },
  faq: {
    on: true,
    items: [
      { titre: 'Le don sert-il uniquement au bâtiment ?', texte: '', on: true },
      { titre: 'Puis-je donner chaque mois ?', texte: '', on: true },
      { titre: 'Puis-je donner anonymement ?', texte: '', on: true },
      { titre: 'À qui écrire pour un reçu ou une question ?', texte: 'Écrivez à l’association depuis la page Contact. Elle vous répond à l’adresse indiquée.', on: true },
    ],
  },
  recus: { statut: false, numero: '' },
};
export const MERCI_SCHEMA = {
  on: ['b'], titre: ['s', 80], texte: ['t', 300], facebook: ['b'], whatsapp: ['b'],
  suivre: ['b'], suivreLien: ['e', ['campagne', 'evenements', 'apropos', 'accueil']], suivreTexte: ['s', 40],
};
DEFAULT_SETTINGS.merci = {
  on: true, titre: 'Merci pour votre générosité', texte: 'Partagez la campagne autour de vous et suivez l’avancement du projet.',
  facebook: true, whatsapp: true, suivre: true, suivreLien: 'campagne', suivreTexte: 'Suivre le projet',
};
export function cleanDonsSettings(input) { return cleanWith(DONS_SCHEMA, input, DEFAULT_SETTINGS.dons); }
export function cleanMerciSettings(input) { return cleanWith(MERCI_SCHEMA, input, DEFAULT_SETTINGS.merci); }

// Événements (clé evenements) : une seule liste pour la page Événements, le calendrier du mois et
// les « Dernières annonces » de l’accueil. Un événement sans date est « en cours » et ne passe jamais.
export const EV_LIEUX = ['mosquee', 'salle', 'campagne', 'autre'];
export const EV_CATEGORIES = ['comm', 'priere', 'cours', 'collecte'];
export const EV_LIENS = ['', 'dons', 'campagne', 'horaires', 'services', 'cours', 'inscription', 'calendrier', 'contact', 'ressources'];
export const EVENEMENTS_SCHEMA = {
  une: { on: ['b'], choix: ['s', 40], bouton: ['e', ['details', 'inscrire', 'aucun']] },
  items: ['list', 40, {
    id: ['s', 40], titre: ['s', 120], date: ['date'], debut: ['hm'], fin: ['hm'],
    lieu: ['e', EV_LIEUX], lieuTexte: ['s', 120], categorie: ['e', EV_CATEGORIES], resume: ['t', 400],
    lien: ['e', EV_LIENS], lienTexte: ['s', 40], inscription: ['e', ['non', 'formulaire', 'contact']],
    partenaire: ['s', 120], description: ['t', 2000], public: ['s', 160], places: ['n', 0, 100000],
    itineraire: ['b'], on: ['b'],
  }],
  filtres: ['b'],
  passes: { on: ['b'], nombre: ['n', 0, 40] },
  fixes: { on: ['b'], items: ['list', 8, { titre: ['s', 60], texte: ['t', 300], on: ['b'] }] },
  outils: { on: ['b'], calendrier: ['b'], inscription: ['b'], dua: ['b'] },
  partage: ['b'],
};
const ev = (o) => ({
  id: '', titre: '', date: '', debut: '', fin: '', lieu: 'mosquee', lieuTexte: '', categorie: 'comm', resume: '', lien: '', lienTexte: '',
  inscription: 'non', partenaire: '', description: '', public: '', places: 0, itineraire: true, on: true, ...o,
});
DEFAULT_SETTINGS.evenements = {
  une: { on: true, choix: 'auto', bouton: 'details' },
  items: [],
  filtres: true,
  passes: { on: true, nombre: 3 },
  fixes: {
    on: true,
    items: [
      { titre: 'Ramadan', texte: 'Dates selon l’annonce officielle ; horaires du Suhoor et de l’Iftar sur la page Horaires.', on: true },
      { titre: 'Aïd al-Fitr', texte: 'Prière selon l’annonce ; zakat al-Fitr à verser avant.', on: true },
      { titre: 'Aïd al-Adha', texte: 'Prière selon l’annonce ; lieu et horaire selon l’annonce.', on: true },
      { titre: 'Vendredis', texte: 'Jumu’a à la mosquée, toute l’année. Heure du jour sur la page Horaires.', on: true },
    ],
  },
  outils: { on: true, calendrier: true, inscription: true, dua: true },
  partage: true,
};
// Calendrier du mois (clé calendrier).
export const CALENDRIER_SCHEMA = {
  categories: { comm: ['b'], priere: ['b'], cours: ['b'], collecte: ['b'] },
  evenements: ['b'], cours: ['b'], agenda: ['b'], vue: ['e', ['mois', 'liste']],
};
DEFAULT_SETTINGS.calendrier = {
  categories: { comm: true, priere: true, cours: true, collecte: true },
  evenements: true, cours: true, agenda: true, vue: 'mois',
};
export function cleanEvenementsSettings(input) {
  const out = cleanWith(EVENEMENTS_SCHEMA, input, DEFAULT_SETTINGS.evenements);
  // Identifiant stable et unique : sert à la fiche, à l’événement à la une et aux inscriptions.
  const seen = new Set();
  out.items.forEach((x, i) => {
    let id = String(x.id || '').toLowerCase().replace(/[^a-z0-9-]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 40) || 'ev-' + (i + 1);
    while (seen.has(id)) id = (id + '-' + (i + 1)).slice(-40);
    seen.add(id);
    x.id = id;
  });
  if (out.une.choix !== 'auto' && !seen.has(out.une.choix)) out.une.choix = 'auto';
  return out;
}
export function cleanCalendrierSettings(input) { return cleanWith(CALENDRIER_SCHEMA, input, DEFAULT_SETTINGS.calendrier); }

// « Dernières annonces » de l’accueil : les événements à venir, puis en cours, puis les plus récents passés.
const MOIS_COURTS = ['janv.', 'févr.', 'mars', 'avr.', 'mai', 'juin', 'juil.', 'août', 'sept.', 'oct.', 'nov.', 'déc.'];
export function evenementsAnnonces(evSettings, today) {
  const items = (evSettings.items || []).filter((x) => x.on && x.titre);
  const label = (d) => (d ? parseInt(d.slice(8, 10), 10) + ' ' + MOIS_COURTS[parseInt(d.slice(5, 7), 10) - 1] + ' ' + d.slice(0, 4) : 'En cours');
  const up = items.filter((x) => x.date && x.date >= today).sort((a, b) => (a.date + a.debut).localeCompare(b.date + b.debut));
  const ongoing = items.filter((x) => !x.date);
  const past = items.filter((x) => x.date && x.date < today).sort((a, b) => b.date.localeCompare(a.date));
  return up.concat(ongoing, past).slice(0, 10).map((x, i) => ({
    id: i, date: label(x.date), titre: x.titre, resume: x.resume, lien: 'Page : Événements', on: true,
  }));
}

// Date d’aujourd’hui dans le fuseau d’Edmundston (America/Moncton).
// Le nom historique torontoDate est conservé : les routes l’importent sous ce nom.
export function torontoDate(now = new Date()) {
  try {
    return new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Moncton', year: 'numeric', month: '2-digit', day: '2-digit' }).format(now);
  } catch {
    return now.toISOString().slice(0, 10);
  }
}

// Ressources (clé ressources) : page « Nouveaux arrivants ». Un lien externe doit commencer par http(s)://,
// sinon il est vidé et la carte s’affiche sans lien.
const RES_LINK = { titre: ['s', 100], texte: ['s', 200], lien: ['s', 300], on: ['b'] };
export const RESSOURCES_SCHEMA = {
  intro: ['t', 300],
  halal: {
    on: ['b'], titre: ['s', 80], texte: ['t', 400], avert: ['b'],
    items: ['list', 12, { nom: ['s', 80], adresse: ['s', 160], telephone: ['s', 30], certif: ['e', ['confirmer', 'certifie', 'non']], organisme: ['s', 80], on: ['b'] }],
  },
  mosquees: { on: ['b'], copier: ['b'], itineraire: ['b'], items: ['list', 12, { nom: ['s', 100], adresse: ['s', 160], distance: ['s', 30], on: ['b'] }] },
  publics: { on: ['b'], items: ['list', 12, RES_LINK] },
  reperes: { on: ['b'], items: ['list', 8, RES_LINK] },
  installer: { on: ['b'], aide: ['b'], cours: ['b'], dua: ['b'] },
  etudier: { on: ['b'], titre: ['s', 80], texte: ['t', 600] },
};
DEFAULT_SETTINGS.ressources = {
  intro: 'Pour la première semaine d’une famille, d’un étudiant ou d’un travailleur qui s’installe dans la région.',
  halal: {
    on: true, titre: 'À Edmundston', avert: true,
    texte: 'La certification se confirme directement auprès de chaque établissement.',
    items: [],
  },
  mosquees: {
    on: true, copier: true, itineraire: true,
    items: [],
  },
  publics: {
    on: true,
    items: [],
  },
  reperes: {
    on: true,
    items: [
      { titre: 'Horaires astronomiques de la ville', texte: 'Référence personnelle, distincte des horaires de la mosquée.', lien: '', on: true },
      { titre: 'Direction de la Qibla', texte: '', lien: '', on: true },
      { titre: 'Calendrier hégirien', texte: 'Dates du calendrier musulman.', lien: '', on: true },
    ],
  },
  installer: { on: true, aide: true, cours: true, dua: true },
  etudier: { on: true, titre: 'Étudier et scolariser', texte: 'Renseignez-vous auprès de l’association pour les écoles de la région.' },
};
const URL_RE = /^https?:\/\/[^\s<>"]+\.[^\s<>"]+$/i;
export function cleanRessourcesSettings(input) {
  const out = cleanWith(RESSOURCES_SCHEMA, input, DEFAULT_SETTINGS.ressources);
  for (const x of out.publics.items.concat(out.reperes.items)) if (!URL_RE.test(x.lien)) x.lien = '';
  return out;
}

// Mur « Dua et annonces » (clé dua) : règles du mur. Les messages sont dans la table dua_messages (migration 0010).
export const DUA_SCHEMA = {
  max: ['n', 80, 1000], delai: ['e', ['12 h', '24 h', '48 h']],
  categories: ['list', 10, { titre: ['s', 30], on: ['b'] }],
  ongletDua: ['b'], ongletAnn: ['b'], compteur: ['b'], anonyme: ['b'], pause: ['b'],
  regles: ['list', 8, { titre: ['s', 160], on: ['b'] }],
};
DEFAULT_SETTINGS.dua = {
  max: 280, delai: '24 h',
  categories: ['Covoiturage', 'Logement', 'Emploi', 'Objets perdus'].map((titre) => ({ titre, on: true })),
  ongletDua: true, ongletAnn: true, compteur: true, anonyme: true, pause: false,
  regles: [
    'Pas de publicité, pas de collecte d’argent privée.',
    'Pas de détails médicaux ou personnels sur d’autres personnes.',
    'Un message signalé est retiré le temps d’être relu.',
  ].map((titre) => ({ titre, on: true })),
};
export function cleanDuaSettings(input) {
  const out = cleanWith(DUA_SCHEMA, input, DEFAULT_SETTINGS.dua);
  if (!out.ongletDua && !out.ongletAnn) out.ongletDua = true;
  return out;
}

// Page Contact (clé contact). Adresse, ville, courriel et Facebook viennent des coordonnées générales (home.general).
export const CO_LIENS = ['', 'mariages', 'funerailles', 'dons', 'evenements', 'ressources', 'services', 'apropos'];
export const CO_PAGES = ['accueil', 'horaires', 'apropos', 'services', 'dons', 'evenements', 'ressources'];
const CO_LIGNE = { on: ['b'], texte: ['s', 120] };
export const CONTACT_SCHEMA = {
  carte: ['b'], lat: ['s', 20], lng: ['s', 20], codePostal: ['s', 10],
  lignes: { stationnement: CO_LIGNE, fauteuil: CO_LIGNE, ablutions: CO_LIGNE },
  etiquette: { on: ['b'], titre: ['s', 120], items: ['list', 8, { titre: ['s', 60], texte: ['t', 600], on: ['b'] }] },
  ecrire: {
    copier: ['b'], facebook: ['b'],
    demandes: { on: ['b'], note: ['s', 200], items: ['list', 8, { texte: ['s', 120], lien: ['e', CO_LIENS], lienTexte: ['s', 60], on: ['b'] }] },
  },
  form: {
    sujets: ['list', 10, { titre: ['s', 60], on: ['b'] }], max: ['n', 200, 3000],
    apres: ['e', ['message', 'page', 'mapage']], page: ['e', CO_PAGES], mapage: ['s', 63],
    merciTitre: ['s', 60], merciTexte: ['s', 300],
  },
};
DEFAULT_SETTINGS.contact = {
  carte: true, lat: '', lng: '', codePostal: 'E3V 3S2',
  lignes: {
    stationnement: { on: true, texte: 'Stationnement dans les rues avoisinantes' },
    fauteuil: { on: true, texte: 'Salle de prière accessible en fauteuil roulant' },
    ablutions: { on: true, texte: 'Ablutions et toilettes sur place' },
  },
  etiquette: {
    on: true, titre: 'Tous les visiteurs sont les bienvenus',
    items: [
      { titre: 'Tenue', texte: 'Une tenue couvrant les épaules et les genoux convient ; les femmes qui le souhaitent peuvent porter un foulard, sans obligation pour une simple visite.', on: true },
      { titre: 'Chaussures et téléphone', texte: 'On retire ses chaussures à l’entrée de la salle de prière, et on éteint la sonnerie de son téléphone.', on: true },
      { titre: 'Pendant la prière', texte: 'Pendant la prière, installez-vous simplement à l’arrière pour observer.', on: true },
    ],
  },
  ecrire: {
    copier: true, facebook: true,
    demandes: {
      on: true, note: 'À adresser par courriel à l’association.',
      items: [
        { texte: 'Visites de groupes et d’écoles', lien: '', lienTexte: '', on: true },
        { texte: 'Questions des médias', lien: '', lienTexte: '', on: true },
        { texte: 'Mariage', lien: 'mariages', lienTexte: 'voir le parcours', on: true },
        { texte: 'Funérailles', lien: 'funerailles', lienTexte: 'qui appeler, quoi faire', on: true },
      ],
    },
  },
  form: {
    sujets: ['Question générale', 'Dons', 'Événements', 'Nouveaux arrivants', 'Autre'].map((titre) => ({ titre, on: true })),
    max: 1000, apres: 'message', page: 'accueil', mapage: '',
    merciTitre: 'Message envoyé', merciTexte: 'Merci. L’association vous répondra à l’adresse indiquée.',
  },
};
const coord = (v, lim) => {
  const n = Number(String(v).replace(/\s/g, '').replace(',', '.').replace(/[\u2212\u2013]/g, '-'));
  return Number.isFinite(n) && Math.abs(n) <= lim ? String(Math.round(n * 1e6) / 1e6) : '';
};
export function cleanContactSettings(input) {
  const out = cleanWith(CONTACT_SCHEMA, input, DEFAULT_SETTINGS.contact);
  out.lat = coord(out.lat, 90) || DEFAULT_SETTINGS.contact.lat;
  out.lng = coord(out.lng, 180) || DEFAULT_SETTINGS.contact.lng;
  if (!/^\/p\/[a-z0-9]+(?:-[a-z0-9]+)*$/.test(out.form.mapage)) out.form.mapage = '';
  if (out.form.apres === 'mapage' && !out.form.mapage) out.form.apres = 'message';
  return out;
}

// Page 404 (clé p404) : affichée pour toute adresse qui n’existe pas.
export const P404_SCHEMA = { titre: ['s', 80], texte: ['t', 300], accueil: ['b'], horaires: ['b'], trouver: ['b'] };
DEFAULT_SETTINGS.p404 = {
  titre: 'Cette page n’existe pas',
  texte: 'L’adresse a peut-être changé, ou la page a été retirée. Ces raccourcis vous ramènent au bon endroit.',
  accueil: true, horaires: true, trouver: true,
};
export function cleanP404Settings(input) { return cleanWith(P404_SCHEMA, input, DEFAULT_SETTINGS.p404); }
