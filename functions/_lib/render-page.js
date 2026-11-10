// Rendu HTML des pages créées dans le superadmin (/p/<lien>), côté serveur, sans aucun script.
// Les widgets (code du superadmin) ne sont jamais insérés ici : ils s'affichent dans un <iframe>
// isolé qui pointe vers /w/<id> (voir widgets.js). Les formulaires sont de vrais formulaires HTML.
// Tout texte venant de la base est échappé ; les liens sont recalculés à partir des blocs validés.
import { PAGE_FILES } from './settings.js';
import { parseVideo } from './video.js';
import { FIELD_TYPES, RESULT_MESSAGES } from './custom-forms.js';

const esc = (s) => String(s ?? '')
  .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');

const WIDTHS = { normal: '760px', large: '1120px', full: '100%' };
const ALERT_TONES = {
  info: { bg: 'var(--vert)', fg: '#FFFFFF', label: 'Information' },
  attention: { bg: 'var(--or)', fg: 'var(--encre)', label: 'Attention' },
  urgent: { bg: 'var(--rouge)', fg: '#FFFFFF', label: 'Urgent' },
};

function href(lien) {
  if (!lien) return null;
  if (lien.type === 'page' && PAGE_FILES[lien.page]) return { url: `/${PAGE_FILES[lien.page]}.dc.html`, ext: false };
  if (lien.type === 'custom' && lien.slug) return { url: `/p/${encodeURIComponent(lien.slug)}`, ext: false };
  if (lien.type === 'url' && /^https?:\/\//i.test(lien.url || '')) return { url: lien.url, ext: true };
  return null;
}

function renderBlock(b, ctx = {}) {
  if (b.type === 'texte') {
    const paras = String(b.texte || '').split(/\n\s*\n/).map((p) => p.trim()).filter(Boolean)
      .map((p) => `<p>${esc(p).replace(/\n/g, '<br>')}</p>`).join('');
    if (!b.titre && !paras) return '';
    return `<section class="blk blk-texte">${b.titre ? `<h2>${esc(b.titre)}</h2>` : ''}${paras}</section>`;
  }
  if (b.type === 'bouton') {
    const h = href(b.lien);
    if (!h || !b.texte) return '';
    const extra = h.ext ? ' target="_blank" rel="noopener"' : '';
    return `<p class="blk blk-bouton"><a class="btn btn-${esc(b.style || 'or')}" href="${esc(h.url)}"${extra}>${esc(b.texte)}`
      + `${h.ext ? '<span class="sr"> (ouvre un autre site)</span>' : ''}</a></p>`;
  }
  if (b.type === 'tableau') {
    const cols = Array.isArray(b.colonnes) ? b.colonnes : [];
    const rows = (Array.isArray(b.lignes) ? b.lignes : []).filter((r) => r.some((c) => String(c).trim()));
    if (!rows.length && !cols.some((c) => String(c).trim())) return '';
    const head = cols.some((c) => String(c).trim())
      ? `<thead><tr>${cols.map((c) => `<th scope="col">${esc(c)}</th>`).join('')}</tr></thead>` : '';
    const body = rows.map((r) => `<tr>${r.map((c) => `<td>${esc(c)}</td>`).join('')}</tr>`).join('');
    return `<div class="blk blk-tableau" role="region" aria-label="Tableau, défilable horizontalement si besoin" tabindex="0">`
      + `<table>${head}<tbody>${body}</tbody></table></div>`;
  }
  if (b.type === 'photo') {
    const m = ctx.media && ctx.media.get(b.media);
    if (!m) return '';
    const size = m.width && m.height ? ` width="${m.width}" height="${m.height}"` : '';
    return `<figure class="blk blk-photo blk-photo-${esc(b.taille || 'pleine')}">`
      + `<img src="/media/${esc(m.file_key)}" alt="${esc(b.alt)}"${size} loading="lazy" decoding="async">`
      + `${b.legende ? `<figcaption>${esc(b.legende)}</figcaption>` : ''}</figure>`;
  }
  if (b.type === 'video') {
    const v = parseVideo(b.url);
    if (!v) return '';
    const title = b.titre || `Vidéo ${v.provider}`;
    return `<figure class="blk blk-video"><div class="vid"><iframe src="${esc(v.embed)}" title="${esc(title)}" loading="lazy"`
      + ` allow="encrypted-media; picture-in-picture; fullscreen" allowfullscreen referrerpolicy="strict-origin-when-cross-origin"></iframe></div>`
      + `${b.titre ? `<figcaption>${esc(b.titre)}</figcaption>` : ''}</figure>`;
  }
  if (b.type === 'widget') {
    const w = ctx.widgets && ctx.widgets.get(b.widget);
    if (!w) return '';
    return `<div class="blk blk-widget"><iframe src="/w/${w.id}?v=${encodeURIComponent(w.updated_at || '')}" title="${esc(w.title || 'Widget')}"`
      + ` sandbox="allow-scripts" loading="lazy" referrerpolicy="no-referrer" style="height:${Number(w.height) || 400}px"></iframe></div>`;
  }
  if (b.type === 'formulaire') {
    const f = ctx.forms && ctx.forms.get(b.form);
    return f ? renderForm(f, ctx) : '';
  }
  return '';
}

function fieldHtml(f, fid) {
  const name = `c_${f.id}`;
  const id = `f${fid}-${f.id}`;
  const req = f.requis ? ' required' : '';
  const star = f.requis ? ' <span class="req" aria-hidden="true">*</span>' : '';
  const hintId = f.aide ? `${id}-aide` : '';
  const desc = hintId ? ` aria-describedby="${hintId}"` : '';
  const hint = f.aide ? `<p class="aide" id="${hintId}">${esc(f.aide)}</p>` : '';
  const label = `${esc(f.label)}${star}`;
  if (f.type === 'choix' || f.type === 'cases') {
    const type = f.type === 'choix' ? 'radio' : 'checkbox';
    const opts = (f.options || []).map((o, i) => `<label class="opt"><input type="${type}" name="${name}" value="${esc(o)}"`
      + `${type === 'radio' && f.requis && i === 0 ? ' required' : ''}> <span>${esc(o)}</span></label>`).join('');
    return `<fieldset class="fld"${desc}><legend>${label}</legend>${hint}${opts}</fieldset>`;
  }
  let control;
  if (f.type === 'paragraphe') {
    control = `<textarea id="${id}" name="${name}" rows="5" maxlength="5000"${req}${desc}></textarea>`;
  } else if (f.type === 'liste') {
    control = `<select id="${id}" name="${name}"${req}${desc}><option value="">Choisir…</option>`
      + (f.options || []).map((o) => `<option value="${esc(o)}">${esc(o)}</option>`).join('') + '</select>';
  } else {
    const t = { texte: 'text', courriel: 'email', telephone: 'tel', nombre: 'text', date: 'date' }[f.type] || 'text';
    const extra = { texte: ' maxlength="300"', courriel: ' maxlength="200" autocomplete="email"', telephone: ' maxlength="30" autocomplete="tel"',
      nombre: ' inputmode="decimal" maxlength="30" pattern="-?[0-9]+([.,][0-9]+)?"', date: '' }[f.type] || '';
    control = `<input id="${id}" name="${name}" type="${t}"${extra}${req}${desc}>`;
  }
  return `<div class="fld"><label for="${id}">${label}</label>${hint}${control}</div>`;
}

function renderForm(f, ctx) {
  const anchor = `form-${f.id}`;
  const res = ctx.result && ctx.result.form === f.id ? ctx.result.code : '';
  const head = `<h2 id="${anchor}-t">${esc(f.title)}</h2>${f.intro ? f.intro.split(/\n\s*\n/).map((p) => `<p>${esc(p).replace(/\n/g, '<br>')}</p>`).join('') : ''}`;
  if (res === 'ok') {
    const merci = f.merci || 'Merci ! Votre réponse est bien arrivée à l’association.';
    return `<section class="blk blk-form" id="${anchor}" aria-labelledby="${anchor}-t">${head}`
      + `<div class="ok" role="status">${esc(merci).replace(/\n/g, '<br>')}</div>`
      + `<p><a href="/p/${encodeURIComponent(ctx.slug)}#${anchor}">Envoyer une autre réponse</a></p></section>`;
  }
  if (!f.open) {
    return `<section class="blk blk-form" id="${anchor}" aria-labelledby="${anchor}-t">${head}`
      + `<p class="note" role="note">Ce formulaire est fermé : il n’accepte plus de réponses.</p></section>`;
  }
  const err = res && RESULT_MESSAGES[res] ? `<div class="err" role="alert">${esc(RESULT_MESSAGES[res])}</div>` : '';
  const fields = (f.fields || []).filter((x) => FIELD_TYPES[x.type]).map((x) => fieldHtml(x, f.id)).join('');
  const anyReq = (f.fields || []).some((x) => x.requis);
  return `<section class="blk blk-form" id="${anchor}" aria-labelledby="${anchor}-t">${head}${err}`
    + `<form method="post" action="/api/forms/custom/${f.id}" accept-charset="utf-8">`
    + `<input type="hidden" name="_p" value="${esc(ctx.slug)}"><input type="hidden" name="_t" value="${Date.now()}">`
    + `<div class="hp" aria-hidden="true"><label>Ne pas remplir ce champ <input type="text" name="_site" tabindex="-1" autocomplete="off"></label></div>`
    + (anyReq ? '<p class="aide">Les champs marqués d’un astérisque (*) sont obligatoires.</p>' : '')
    + fields
    + `<p><button class="btn btn-or" type="submit">${esc(f.bouton || 'Envoyer')}</button></p></form></section>`;
}

const STYLE = `
:root{--vert:#0E4D3C;--vert-fonce:#08362A;--or:#C49A4A;--sable:#F3EAD8;--sable-bord:#E4D9C0;--encre:#1E2B26;
--muted:#4F5E57;--fond:#FAF8F1;--blanc:#FFFFFF;--rouge:#B3261E;--focus:#C49A4A}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--fond);color:var(--encre);font:16px/1.6 'Noto Sans',system-ui,-apple-system,'Segoe UI',sans-serif;overflow-wrap:anywhere}
a{color:var(--vert)}
a:focus-visible,.blk-tableau:focus-visible{outline:3px solid var(--focus);outline-offset:3px;border-radius:6px}
.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
.skip{position:absolute;left:-9999px;top:8px;background:var(--blanc);color:var(--vert);padding:10px 14px;border-radius:10px;z-index:100}
.skip:focus{left:16px}
.alert{padding:10px 16px;text-align:center;font-weight:600}
.alert a{color:inherit;text-underline-offset:3px}
.hdr{background:var(--vert);color:var(--sable)}
.hdr-in,.ftr-in{max-width:1180px;margin:0 auto;padding:0 16px}
.hdr-in{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;min-height:64px}
.logo{color:var(--blanc);font-weight:800;font-size:20px;text-decoration:none;display:inline-flex;flex-direction:column;line-height:1.15;padding:6px 0}
.logo small{font-size:12px;font-weight:600;color:var(--sable)}
.nav{display:flex;flex-wrap:wrap;gap:4px 16px;margin:0;padding:0;list-style:none}
.nav a{color:var(--sable);text-decoration:none;display:inline-flex;align-items:center;min-height:44px;font-weight:600}
.nav a:hover{color:var(--blanc);text-decoration:underline}
.nav .don{background:var(--or);color:var(--encre);padding:0 16px;border-radius:999px}
.nav .don:hover{color:var(--encre);background:#D6AE60}
main{margin:0 auto;padding:40px 16px 64px}
h1{font-family:'Noto Serif',Georgia,serif;color:var(--vert);font-size:clamp(32px,6vw,48px);line-height:1.15;margin:0 0 24px}
.blk{margin:0 0 28px}
.blk h2{font-family:'Noto Serif',Georgia,serif;color:var(--vert);font-size:clamp(22px,3.4vw,28px);line-height:1.25;margin:0 0 10px}
.blk-texte p{margin:0 0 14px;max-width:70ch}
.btn{display:inline-flex;align-items:center;justify-content:center;min-height:48px;padding:0 24px;border-radius:999px;font-weight:700;text-decoration:none;border:2px solid transparent}
.btn-or{background:var(--or);color:var(--encre)}.btn-or:hover{background:#D6AE60}
.btn-vert{background:var(--vert);color:var(--blanc)}.btn-vert:hover{background:var(--vert-fonce)}
.btn-contour{background:transparent;color:var(--vert);border-color:var(--vert)}.btn-contour:hover{background:var(--sable)}
.blk-tableau{overflow-x:auto;border:1px solid var(--sable-bord);border-radius:14px;background:var(--blanc);
  background-image:linear-gradient(to right,var(--blanc),var(--blanc)),linear-gradient(to left,var(--blanc),var(--blanc)),
  linear-gradient(to right,rgba(0,0,0,.12),transparent),linear-gradient(to left,rgba(0,0,0,.12),transparent);
  background-position:left,right,left,right;background-repeat:no-repeat;background-size:24px 100%,24px 100%,12px 100%,12px 100%;
  background-attachment:local,local,scroll,scroll}
table{border-collapse:collapse;width:100%;min-width:480px}
th,td{padding:12px 14px;text-align:start;border-bottom:1px solid var(--sable);vertical-align:top}
th{background:var(--sable);color:var(--vert)}
tr:last-child td{border-bottom:0}
.blk-photo{margin-inline:0}
.blk-photo img{display:block;width:100%;height:auto;border-radius:14px;background:var(--sable)}
.blk-photo-moyenne{max-width:480px}.blk-photo-petite{max-width:280px}
figcaption{margin-top:8px;color:var(--muted);font-size:15px}
.blk-video{margin-inline:0}
.vid{position:relative;aspect-ratio:16/9;border-radius:14px;overflow:hidden;background:var(--encre)}
.vid iframe{position:absolute;inset:0;width:100%;height:100%;border:0}
.blk-widget iframe{display:block;width:100%;border:1px solid var(--sable-bord);border-radius:14px;background:var(--blanc)}
.blk-form{background:var(--blanc);border:1px solid var(--sable-bord);border-radius:16px;padding:24px}
.blk-form form{display:flex;flex-direction:column;gap:16px;margin-top:8px}
.blk-form .fld{display:flex;flex-direction:column;gap:6px;border:0;margin:0;padding:0;min-width:0}
.blk-form label,.blk-form legend{font-weight:700;color:var(--encre);padding:0}
.blk-form .opt{font-weight:400;display:flex;gap:10px;align-items:center;min-height:40px}
.blk-form .opt input{width:22px;height:22px;accent-color:var(--vert)}
.blk-form input[type=text],.blk-form input[type=email],.blk-form input[type=tel],.blk-form input[type=date],.blk-form select,.blk-form textarea{
  width:100%;min-width:0;min-height:48px;padding:10px 14px;border:1px solid #8A9A92;border-radius:12px;font:inherit;color:var(--encre);background:var(--blanc)}
.blk-form textarea{min-height:120px;resize:vertical}
.blk-form :is(input,select,textarea,button):focus-visible{outline:3px solid var(--focus);outline-offset:2px}
.blk-form .aide{margin:0;color:var(--muted);font-size:14px}
.blk-form .req{color:var(--rouge)}
.blk-form .btn{cursor:pointer;font:inherit;font-weight:700}
.blk-form .ok{padding:14px 16px;border-radius:12px;background:#DCEFE6;color:var(--vert);font-weight:600}
.blk-form .err{padding:14px 16px;border-radius:12px;background:#FBEAE8;color:#8C1D18;font-weight:600}
.blk-form .note{color:var(--muted)}
.hp{position:absolute;left:-10000px;width:1px;height:1px;overflow:hidden}
.draft{background:var(--sable);color:#7A5A1E;text-align:center;padding:10px 16px;font-weight:700;border-bottom:1px solid var(--sable-bord)}
.empty{color:var(--muted)}
.ftr{background:var(--vert);color:var(--sable);padding:32px 0;font-size:15px}
.ftr a{color:var(--sable)}
.ftr p{margin:0 0 6px}
@media (prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
`;

function alertHtml(alert) {
  if (!alert) return '';
  const t = ALERT_TONES[alert.tone] || ALERT_TONES.attention;
  const h = href(alert.link);
  const link = h ? ` <a href="${esc(h.url)}"${h.ext ? ' target="_blank" rel="noopener"' : ''}>En savoir plus</a>` : '';
  return `<div class="alert" role="region" aria-label="Information importante" style="background:${t.bg};color:${t.fg}">`
    + `<span class="sr">${t.label} : </span>${esc(alert.message)}${link}</div>`;
}

const HEADER = `<header class="hdr"><div class="hdr-in">
<a class="logo" href="/">Centre Islamique d'Edmundston<small>Edmundston Islamic Centre</small></a>
<nav aria-label="Navigation principale"><ul class="nav">
<li><a href="/Horaires.dc.html">Horaires</a></li><li><a href="/APropos.dc.html">À propos</a></li>
<li><a href="/Services.dc.html">Services</a></li><li><a href="/Evenements.dc.html">Événements</a></li><li><a href="/Contact.dc.html">Contact</a></li>
<li><a class="don" href="/Dons.dc.html">Faire un don</a></li></ul></nav></div></header>`;

const FOOTER = `<footer class="ftr"><div class="ftr-in">
<p><strong>Centre Islamique d'Edmundston</strong> (Edmundston Islamic Centre)</p>
<p>34, 37e Avenue, Edmundston, NB E3V 3S2</p>
<p><a href="/">Retour à l’accueil</a></p></div></footer>`;

// Les balises email_off empêchent Cloudflare de remplacer les adresses par « [email protected] » :
// son script de décodage est bloqué par la politique de sécurité de ces pages.
function shell({ title, description, body, noindex, canonical, layout, alert, draft }) {
  const site = layout !== 'blank';
  return `<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${esc(title)} — Centre Islamique d'Edmundston</title>
${description ? `<meta name="description" content="${esc(description)}">` : ''}
${noindex ? '<meta name="robots" content="noindex, nofollow">' : ''}
${canonical ? `<link rel="canonical" href="${esc(canonical)}">` : ''}
<meta property="og:title" content="${esc(title)}">
${description ? `<meta property="og:description" content="${esc(description)}">` : ''}
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans:wght@400;600;700;800&family=Noto+Serif:wght@700&display=swap">
<style>${STYLE}</style></head><body>
<a class="skip" href="#contenu">Aller au contenu</a>
${draft ? '<p class="draft" role="note">Brouillon : cette page n’est visible que par les comptes connectés au superadmin.</p>' : ''}
<!--email_off-->
${site ? alertHtml(alert) + HEADER : ''}
${body}
${site ? FOOTER : ''}
<!--/email_off-->
</body></html>`;
}

export function renderPage(page, { alert = null, draft = false, origin = '', refs = {}, result = null } = {}) {
  const ctx = { ...refs, result, slug: page.slug };
  const blocks = (page.blocks || []).map((b) => renderBlock(b, ctx)).join('');
  const body = `<main id="contenu" style="max-width:${WIDTHS[page.width] || WIDTHS.normal}">`
    + `<h1>${esc(page.title)}</h1>${blocks || '<p class="empty">Cette page est encore vide.</p>'}</main>`;
  return shell({
    title: page.title,
    description: page.description,
    body,
    noindex: page.visibility !== 'published',
    canonical: page.visibility === 'published' && origin ? `${origin}/p/${page.slug}` : '',
    layout: page.layout,
    alert,
    draft,
  });
}

export function renderNotFound() {
  return shell({
    title: 'Page introuvable',
    body: `<main id="contenu" style="max-width:760px"><h1>Page introuvable</h1>`
      + `<p>Cette page n’existe pas, a été retirée ou n’est pas encore publiée. Vérifiez l’adresse, ou revenez à l’accueil.</p>`
      + `<p><a class="btn btn-vert" href="/">Retour à l’accueil</a></p></main>`,
    noindex: true,
    layout: 'site',
  });
}
