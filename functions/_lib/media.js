// Photos des pages créées (étape M1). Les fichiers vivent dans l'espace de stockage Cloudflare KV
// « edmundston-medias », relié sous le nom « MEDIA » (wrangler.toml) ; la clé de chaque fichier est la
// colonne file_key de la table media (migration 0011), qui garde sa fiche.
// KV est « finalement cohérent » : une photo qui vient d'être envoyée peut mettre jusqu'à une minute
// à être visible partout ; le panneau l'annonce comme « en cours de mise en ligne », pas comme une erreur.
// Sécurité :
//  - le format est reconnu d'après le contenu du fichier (ses premiers octets), jamais d'après son nom ;
//  - seuls JPEG, PNG, WebP et GIF sont acceptés : pas de SVG, qui peut contenir du script ;
//  - le nom rangé est aléatoire (impossible à deviner ou à écraser) ;
//  - le fichier est servi avec son vrai type, nosniff et une politique qui interdit tout script.

export const MAX_BYTES = 5 * 1024 * 1024;
export const NO_STORAGE = 'Le stockage des photos n’est pas relié au site : l’espace KV « edmundston-medias » (liaison MEDIA, déclarée dans wrangler.toml) est introuvable. Vérifiez-le dans Cloudflare, puis redéployez.';
export const NO_TABLE = 'La table des photos n’existe pas encore. Appliquez la migration 0011 dans la console D1, puis réessayez.';
export const KEY_RE = /^[0-9a-f]{32}\.(jpg|png|webp|gif)$/;

const EXT = { 'image/jpeg': 'jpg', 'image/png': 'png', 'image/webp': 'webp', 'image/gif': 'gif' };

// Type réel du fichier, d'après ses premiers octets. null si ce n'est pas une image acceptée.
export function sniff(b) {
  if (b.length < 12) return null;
  if (b[0] === 0xff && b[1] === 0xd8 && b[2] === 0xff) return 'image/jpeg';
  if (b[0] === 0x89 && b[1] === 0x50 && b[2] === 0x4e && b[3] === 0x47 && b[4] === 0x0d && b[5] === 0x0a && b[6] === 0x1a && b[7] === 0x0a) return 'image/png';
  if (b[0] === 0x47 && b[1] === 0x49 && b[2] === 0x46 && b[3] === 0x38) return 'image/gif';
  if (b[0] === 0x52 && b[1] === 0x49 && b[2] === 0x46 && b[3] === 0x46 && b[8] === 0x57 && b[9] === 0x45 && b[10] === 0x42 && b[11] === 0x50) return 'image/webp';
  return null;
}

const u16be = (b, i) => (b[i] << 8) | b[i + 1];
const u16le = (b, i) => b[i] | (b[i + 1] << 8);
const u24le = (b, i) => b[i] | (b[i + 1] << 8) | (b[i + 2] << 16);
const u32be = (b, i) => ((b[i] << 24) >>> 0) + (b[i + 1] << 16) + (b[i + 2] << 8) + b[i + 3];

// Largeur et hauteur, lues dans l'en-tête (pour réserver la place de l'image et éviter les sauts).
export function dimensions(b, mime) {
  try {
    if (mime === 'image/png') return { width: u32be(b, 16), height: u32be(b, 20) };
    if (mime === 'image/gif') return { width: u16le(b, 6), height: u16le(b, 8) };
    if (mime === 'image/webp') {
      const kind = String.fromCharCode(b[12], b[13], b[14], b[15]);
      if (kind === 'VP8X') return { width: u24le(b, 24) + 1, height: u24le(b, 27) + 1 };
      if (kind === 'VP8L') {
        const n = b[21] | (b[22] << 8) | (b[23] << 16) | (b[24] << 24);
        return { width: (n & 0x3fff) + 1, height: ((n >> 14) & 0x3fff) + 1 };
      }
      if (kind === 'VP8 ') return { width: u16le(b, 26) & 0x3fff, height: u16le(b, 28) & 0x3fff };
    }
    if (mime === 'image/jpeg') {
      let i = 2;
      while (i + 9 < b.length) {
        if (b[i] !== 0xff) { i += 1; continue; }
        const m = b[i + 1];
        if (m === 0xd8 || m === 0x01 || (m >= 0xd0 && m <= 0xd7)) { i += 2; continue; }
        const len = u16be(b, i + 2);
        if ((m >= 0xc0 && m <= 0xcf) && m !== 0xc4 && m !== 0xc8 && m !== 0xcc) {
          return { width: u16be(b, i + 7), height: u16be(b, i + 5) };
        }
        i += 2 + len;
      }
    }
  } catch { /* en-tête illisible : on garde null */ }
  return { width: null, height: null };
}

export function randomKey(mime) {
  const a = new Uint8Array(16);
  crypto.getRandomValues(a);
  return Array.from(a, (x) => x.toString(16).padStart(2, '0')).join('') + '.' + EXT[mime];
}

export const noTable = (e) => /no such table/i.test(String(e && e.message));

export function rowToMedia(r) {
  return {
    id: r.id, key: r.file_key, url: `/media/${r.file_key}`, mime: r.mime, size: r.size,
    width: r.width, height: r.height, name: r.name, createdAt: r.created_at,
  };
}
