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
