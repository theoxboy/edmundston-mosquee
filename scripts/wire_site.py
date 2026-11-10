"""Branche « Site entier » (superadmin) sur la base, et l'applique au site public.

1. SA-Site.dc.html :
   - #sp-0 « Pages publiées » :
     * 8 pages principales (Accueil avec interrupteur réellement désactivé + badge, et 7 pages avec pastille d'état en direct Publiée / Masquée du site) ;
     * 6 « Services (niveau 2) » (pastille et mention explicite de l'état publié réel sur le site) ;
     * 5 « Applications (niveau 3) » (pastille et mention explicite de l'état publié réel sur le site).
   - #sp-1 « Saison et langues » :
     * « Mode du site » (Normal, Ramadan, Aïd al-Fitr, Aïd al-Adha, dates, changement auto + état en direct)
       et « Thème du vendredi » (Désactivé, Automatique chaque vendredi, Activé tous les jours ; champ season.vendredi) ;
     * « Langues » (Français avec interrupteur réellement désactivé, العربية, English + pastilles d'état) ;
     * « Bannière d'alerte » (interrupteur Afficher, message, lien dont pages créées et lien externe, dates, couleur + Aperçu visuel en direct et état de cohérence message vide / OFF).
   - #sp-2 « Compte et sécurité » :
     * Mon compte + Changer le mot de passe (12 caractères min.) ;
     * Appareils connectés ;
     * Journal des modifications (20 dernières actions : « Page modifiée » nomme la page, « Réglages modifiés » détaille la rubrique et les pages).

2. Toutes les pages publiques :
   - Masquage des pages décochées (#ascil-pages-sync) ;
   - Bannière d'alerte (#ascil-alert-banner) ;
   - Sélecteur de langues (#ascil-languages) ;
   - Bandeau de saison sur l'accueil (#ascil-season).

À relancer après scripts/install_superadmin.py (qui régénère les pages SA-*). Idempotent.
"""
import json, re, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
OPEN = '<script type="__bundler/template">'


def load(path):
    s = path.read_text(encoding='utf-8')
    i = s.index(OPEN) + len(OPEN)
    j = s.index('</script>', i)
    return s, i, j, json.loads(s[i:j])


def save(path, s, i, j, tpl):
    enc = json.dumps(tpl).replace('</', '<\\u002F')
    assert json.loads(enc) == tpl
    path.write_text(s[:i] + enc + s[j:], encoding='utf-8')


def find_div_end(tpl, start_idx):
    depth = 0
    for m in re.finditer(r'<div\b|</div>', tpl[start_idx:]):
        depth += 1 if m.group(0) != '</div>' else -1
        if depth == 0:
            return start_idx + m.end()
    raise AssertionError('div non fermée à partir de ' + str(start_idx))


def replace_div_by_id(tpl, div_id, new_html):
    marker = f'<div id="{div_id}" class="sp">'
    a = tpl.index(marker)
    b = find_div_end(tpl, a)
    return tpl[:a] + new_html + tpl[b:]


# ---------------------------------------------------------------- Styles du panneau Site entier
SITE_STYLE = '''<style id="sa-site-style">
.sw:disabled,.sw[aria-disabled="true"]{opacity:.55;cursor:not-allowed;box-shadow:none !important}
.sw-wrap{display:flex;align-items:center;gap:10px;flex-wrap:wrap;justify-content:flex-end}
.pub-pill{display:inline-flex;align-items:center;min-height:24px;padding:0 10px;border-radius:999px;font-size:12px;font-weight:700;white-space:nowrap}
section[aria-label="Bannière d’alerte"].off .card-b{opacity:1}
.alert-pv-wrap{margin-top:4px;padding:14px 16px;border:1px solid #E4D9C0;border-radius:14px;background:#FAF6EC;display:flex;flex-direction:column;gap:10px}
.alert-pv-head{display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap}
.alert-pv-bar{border-radius:10px;padding:10px 16px;font:600 15px/1.45 "Noto Sans",system-ui,sans-serif;transition:background .15s,color .15s}
.alert-pv-row{display:flex;align-items:center;justify-content:center;gap:10px;flex-wrap:wrap;text-align:center}
</style>
'''

# ---------------------------------------------------------------- #sp-0 : Pages publiées
MAIN_PAGES = [
    ('pg_horaires', 'Horaires du mois'),
    ('pg_apropos', 'À propos'),
    ('pg_services', 'Services'),
    ('pg_dons', 'Faire un don'),
    ('pg_evenements', 'Événements'),
    ('pg_ressources', 'Ressources'),
    ('pg_contact', 'Contact'),
]

N2_PAGES = [
    ('pg_cours', 'Cours de Coran et d’arabe'),
    ('pg_mariages', 'Mariages'),
    ('pg_funerailles', 'Funérailles et janaza'),
    ('pg_aide', 'Aide alimentaire'),
    ('pg_femmes', 'Espace femmes'),
    ('pg_khutba', 'Langue de la khutba'),
]

N3_PAGES = [
    ('pg_rappel', 'Rappel de prière'),
    ('pg_campagne', 'Campagne en direct'),
    ('pg_calendrier', 'Calendrier du mois'),
    ('pg_inscription', 'Inscription aux événements'),
    ('pg_dua', 'Dua et annonces'),
]


def build_sp0():
    rows_main = [
        '<div class="row"><div><div style="font-weight:600;font-size:14px">Accueil</div>'
        '<p class="hint">Ne peut pas être masquée.</p></div>'
        '<div class="sw-wrap"><span class="pub-pill" style="background:#DCEFE6;color:#0E4D3C">Toujours publiée</span>'
        '<button type="button" class="sw" role="switch" aria-label="Accueil" aria-checked="true" disabled="" aria-disabled="true" title="La page d’accueil ne peut pas être masquée"></button></div></div>'
    ]
    for key, label in MAIN_PAGES:
        rows_main.append(
            f'<div class="row"><div><div style="font-weight:600;font-size:14px">{label}</div></div>'
            f'<div class="sw-wrap"><span class="pub-pill" style="background:{{{{pub.{key}.bg}}}};color:{{{{pub.{key}.fg}}}}">{{{{pub.{key}.t}}}}</span>'
            f'<button type="button" class="sw" role="switch" aria-label="{label}" aria-checked="{{{{s.{key}.c}}}}" sc-camel-on-click="{{{{s.{key}.t}}}}"></button></div></div>'
        )

    rows_n2 = []
    for key, label in N2_PAGES:
        rows_n2.append(
            f'<div class="row"><div><div style="font-weight:600;font-size:14px">{label}</div>'
            f'<p class="hint">Service · <span style="font-weight:600;color:{{{{pub.{key}.fg}}}}">{{{{pub.{key}.sub}}}}</span></p></div>'
            f'<div class="sw-wrap"><span class="pub-pill" style="background:{{{{pub.{key}.bg}}}};color:{{{{pub.{key}.fg}}}}">{{{{pub.{key}.t}}}}</span>'
            f'<button type="button" class="sw" role="switch" aria-label="{label}" aria-checked="{{{{s.{key}.c}}}}" sc-camel-on-click="{{{{s.{key}.t}}}}"></button></div></div>'
        )

    rows_n3 = []
    for key, label in N3_PAGES:
        rows_n3.append(
            f'<div class="row"><div><div style="font-weight:600;font-size:14px">{label}</div>'
            f'<p class="hint">Application · <span style="font-weight:600;color:{{{{pub.{key}.fg}}}}">{{{{pub.{key}.sub}}}}</span></p></div>'
            f'<div class="sw-wrap"><span class="pub-pill" style="background:{{{{pub.{key}.bg}}}};color:{{{{pub.{key}.fg}}}}">{{{{pub.{key}.t}}}}</span>'
            f'<button type="button" class="sw" role="switch" aria-label="{label}" aria-checked="{{{{s.{key}.c}}}}" sc-camel-on-click="{{{{s.{key}.t}}}}"></button></div></div>'
        )

    return (
        '<div id="sp-0" class="sp">'
        '<div class="sp-h"><div style="flex:1;min-width:220px"><p class="eyebrow">Tout le site</p>'
        '<h2 class="serif" style="margin:4px 0 0;font-size:26px;color:#0E4D3C;font-weight:700">Pages publiées</h2>'
        '<p class="dsc" style="margin-top:4px">Une page masquée disparaît du menu, du pied de page et des liens qui y mènent.</p></div>'
        '<div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap"></div></div>'

        '<section class="card" aria-label="Pages principales"><div class="card-h"><span class="num" aria-hidden="true">1</span>'
        '<div><h3 class="ttl">Pages principales</h3><p class="dsc">Toujours visibles dans le menu.</p></div></div>'
        '<div class="card-b"><div>' + ''.join(rows_main) + '</div></div></section>'

        '<section class="card" aria-label="Services (niveau 2)"><div class="card-h"><span class="num" aria-hidden="true">2</span>'
        '<div><h3 class="ttl">Services (niveau 2)</h3>'
        '<p class="dsc">Pages des services de la mosquée. Une page masquée n’apparaît plus sur le site public.</p></div></div>'
        '<div class="card-b"><div>' + ''.join(rows_n2) + '</div>'
        '<p class="info" style="margin:4px 0 0">{{n2Summary}}</p></div></section>'

        '<section class="card" aria-label="Applications (niveau 3)"><div class="card-h"><span class="num" aria-hidden="true">3</span>'
        '<div><h3 class="ttl">Applications (niveau 3)</h3>'
        '<p class="dsc">Outils interactifs du site. Une page masquée n’apparaît plus sur le site public.</p></div></div>'
        '<div class="card-b"><div>' + ''.join(rows_n3) + '</div>'
        '<p class="info" style="margin:4px 0 0">{{n3Summary}}</p></div></section>'
        '</div>'
    )


# ---------------------------------------------------------------- #sp-1 : Saison et langues
ALERT_LINKS = [
    ('', 'Aucun lien'),
    ('pg_horaires', 'Page : Horaires du mois'), ('pg_evenements', 'Page : Événements'),
    ('pg_inscription', 'Page : Inscription aux événements'), ('pg_dons', 'Page : Faire un don'),
    ('pg_campagne', 'Page : Campagne en direct'), ('pg_contact', 'Page : Contact'),
    ('pg_apropos', 'Page : À propos'), ('pg_services', 'Page : Services'), ('pg_ressources', 'Page : Ressources'),
    ('__url', 'Lien externe…'),
]


def build_sp1():
    options = ''.join(f'<option>{label}</option>' for _, label in ALERT_LINKS)
    return (
        '<div id="sp-1" class="sp">'
        '<div class="sp-h"><div style="flex:1;min-width:220px"><p class="eyebrow">Tout le site</p>'
        '<h2 class="serif" style="margin:4px 0 0;font-size:26px;color:#0E4D3C;font-weight:700">Saison et langues</h2></div>'
        '<div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap"></div></div>'

        '<section class="card" aria-label="Mode du site"><div class="card-h"><span class="num" aria-hidden="true">1</span>'
        '<div><h3 class="ttl">Mode du site</h3>'
        '<p class="dsc">Affiche un bandeau de saison en haut de l’accueil (vœux, horaires Suhoor et Iftar pour le Ramadan) pendant la période choisie.</p></div></div>'
        '<div class="card-b">'
        '<div class="fld"><span class="lbl" id="f1">Mode actif</span>'
        '<div class="seg" role="group" aria-labelledby="f1" style="align-self:flex-start;flex-wrap:wrap">'
        '<button type="button" data-season-mode="normal" aria-pressed="true">Normal</button>'
        '<button type="button" data-season-mode="ramadan" aria-pressed="false">Ramadan</button>'
        '<button type="button" data-season-mode="aid_fitr" aria-pressed="false">Aïd al-Fitr</button>'
        '<button type="button" data-season-mode="aid_adha" aria-pressed="false">Aïd al-Adha</button>'
        '</div></div>'
        '<div class="g2"><div class="fld"><label class="lbl" for="f2">Début de la période</label>'
        '<input class="in tnum" id="f2" type="date" value=""></div>'
        '<div class="fld"><label class="lbl" for="f3">Fin de la période</label>'
        '<input class="in tnum" id="f3" type="date" value=""></div></div>'
        '<div><div class="row"><div><div style="font-weight:600;font-size:14px">Changer de mode automatiquement aux dates</div>'
        '<p class="hint">Activé : le mode ne s’affiche qu’entre les deux dates. Désactivé : il s’affiche tout de suite, jusqu’à ce que vous repassiez en Normal.</p></div>'
        '<button type="button" class="sw" role="switch" aria-label="Changer de mode automatiquement aux dates" aria-checked="{{s.mode_auto.c}}" sc-camel-on-click="{{s.mode_auto.t}}"></button></div></div>'
        '<p class="info" id="season-live-status">Les dates suivent l’annonce officielle de la TCOM. Hors période, le site revient au mode Normal.</p>'
        '<div class="fld" style="margin-top:8px;padding-top:18px;border-top:1px solid #E4D9C0"><span class="lbl" id="f1v">Thème du vendredi (Jumu’a)</span>'
        '<div class="seg" role="group" aria-labelledby="f1v" style="align-self:flex-start;flex-wrap:wrap">'
        '<button type="button" data-friday-mode="off" aria-pressed="true">Désactivé</button>'
        '<button type="button" data-friday-mode="auto" aria-pressed="false">Automatique, chaque vendredi</button>'
        '<button type="button" data-friday-mode="on" aria-pressed="false">Activé tous les jours</button>'
        '</div>'
        '<p class="hint">Accueil aux couleurs du vendredi : heure de la khutba, langue, sunnas du jour, sourate al-Kahf, salawat et duas. '
        'Automatique : seulement le vendredi, de minuit à minuit. Un mode Ramadan ou Aïd en cours passe avant.</p></div>'
        '<p class="info" id="friday-live-status">État sur le site : thème du vendredi désactivé.</p>'
        '</div></section>'

        '<section class="card" aria-label="Langues"><div class="card-h"><span class="num" aria-hidden="true">2</span>'
        '<div><h3 class="ttl">Langues</h3><p class="dsc">Le sélecteur FR · العربية · EN de l’en-tête.</p></div></div>'
        '<div class="card-b"><div>'
        '<div class="row"><div><div style="font-weight:600;font-size:14px">Français</div>'
        '<p class="hint">Langue principale, toujours active.</p></div>'
        '<div class="sw-wrap"><span class="pub-pill" style="background:#DCEFE6;color:#0E4D3C">Toujours active</span>'
        '<button type="button" class="sw" role="switch" aria-label="Français" aria-checked="true" disabled="" aria-disabled="true" title="Le français est la langue principale et ne peut pas être désactivé"></button></div></div>'
        '<div class="row"><div><div style="font-weight:600;font-size:14px">العربية</div>'
        '<p class="hint">Affichée de droite à gauche.</p></div>'
        '<div class="sw-wrap"><span class="pub-pill" style="background:{{pub.lang_ar.bg}};color:{{pub.lang_ar.fg}}">{{pub.lang_ar.t}}</span>'
        '<button type="button" class="sw" role="switch" aria-label="العربية" aria-checked="{{s.lang_ar.c}}" sc-camel-on-click="{{s.lang_ar.t}}"></button></div></div>'
        '<div class="row"><div><div style="font-weight:600;font-size:14px">English</div></div>'
        '<div class="sw-wrap"><span class="pub-pill" style="background:{{pub.lang_en.bg}};color:{{pub.lang_en.fg}}">{{pub.lang_en.t}}</span>'
        '<button type="button" class="sw" role="switch" aria-label="English" aria-checked="{{s.lang_en.c}}" sc-camel-on-click="{{s.lang_en.t}}"></button></div></div>'
        '</div>'
        '<p class="hint">Une langue masquée disparaît du sélecteur de toutes les pages. Les textes ne sont pas encore traduits : choisir العربية ou EN n’affiche pas encore de traduction.</p>'
        '</div></section>'

        '<section class="card {{off.alerte}}" aria-label="Bannière d’alerte"><div class="card-h"><span class="num" aria-hidden="true">3</span>'
        '<div><h3 class="ttl">Bannière d’alerte</h3>'
        '<p class="dsc">Bande en haut de toutes les pages pour une information urgente (fermeture, tempête, changement d’horaire).</p></div>'
        '<div class="hsw"><span aria-hidden="true">Afficher</span>'
        '<button type="button" class="sw" role="switch" aria-label="Afficher Bannière d’alerte" aria-checked="{{s.alerte.c}}" sc-camel-on-click="{{s.alerte.t}}"></button></div></div>'
        '<div class="card-b">'
        '<div class="g2"><div class="fld"><label class="lbl" for="f4">Message</label>'
        '<input class="in" id="f4" type="text" value="" maxlength="200" placeholder="Ex. La mosquée est fermée ce soir à cause de la tempête." aria-describedby="alert-msg-hint">'
        '<p class="hint" id="alert-msg-hint">200 caractères au plus. La bannière ne s’affiche que si un message est saisi.</p></div>'
        '<div class="fld"><label class="lbl" for="f5">Lien (facultatif)</label>'
        '<sc-raw-select class="in" id="f5">' + options + '</sc-raw-select>'
        '<div id="alert-url-wrap" style="display:none;flex-direction:column;gap:6px;margin-top:8px">'
        '<label class="lbl" for="alert-url">Adresse du lien externe</label>'
        '<input class="in" id="alert-url" type="url" value="" placeholder="https://…" maxlength="500"></div></div></div>'
        '<div class="g2"><div class="fld"><label class="lbl" for="f6">Afficher à partir du</label>'
        '<input class="in tnum" id="f6" type="date" value="" aria-describedby="alert-dates-hint"></div>'
        '<div class="fld"><label class="lbl" for="f7">Jusqu’au</label>'
        '<input class="in tnum" id="f7" type="date" value=""></div></div>'
        '<p class="hint" id="alert-dates-hint" style="margin:-4px 0 0">Laissez vide pour afficher dès maintenant, ou sans date de fin.</p>'
        '<div class="fld"><span class="lbl" id="f8">Couleur</span>'
        '<div class="seg" role="group" aria-labelledby="f8" style="align-self:flex-start;flex-wrap:wrap">'
        '<button type="button" data-alert-tone="info" aria-pressed="false">Information (vert)</button>'
        '<button type="button" data-alert-tone="attention" aria-pressed="true">Attention (or)</button>'
        '<button type="button" data-alert-tone="urgent" aria-pressed="false">Urgent (rouge)</button>'
        '</div></div>'

        '<div class="alert-pv-wrap" id="alert-pv-wrap" aria-live="polite">'
        '<div class="alert-pv-head">'
        '<div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">'
        '<span class="lbl" style="font-size:13px">Aperçu de la bannière</span>'
        '<span class="pub-pill" id="alert-pv-badge" style="background:#F3EAD8;color:#7A5A1E">Désactivée</span>'
        '</div>'
        '<button type="button" class="btn btn-line" id="alert-clear-btn" style="min-height:32px;padding:0 12px;font-size:12px;display:none">Effacer les réglages en réserve</button>'
        '</div>'
        '<p class="hint" id="alert-pv-note" style="margin:0">Aucune bannière n’est affichée sur le site.</p>'
        '<div class="alert-pv-bar" id="alert-pv-bar" style="background:#C49A4A;color:#1E2B26">'
        '<div class="alert-pv-row" id="alert-pv-row"></div>'
        '</div>'
        '</div>'
        '</div></section>'
        '</div>'
    )


# ---------------------------------------------------------------- #sp-2 : Compte et sécurité
ACCOUNT_HTML = (
    '<div id="sp-2" class="sp"><div class="sp-h"><div style="flex:1;min-width:220px"><p class="eyebrow">Votre accès</p>'
    '<h2 class="serif" style="margin:4px 0 0;font-size:26px;color:#0E4D3C;font-weight:700">Compte et sécurité</h2>'
    '<p class="dsc" style="margin-top:4px">Votre compte, vos appareils connectés et l’historique des changements.</p></div></div>'

    '<section class="card" aria-labelledby="acc-t1"><div class="card-h"><span class="num" aria-hidden="true">1</span>'
    '<div><h3 class="ttl" id="acc-t1">Mon compte</h3></div></div><div class="card-b">'
    '<dl id="acc-info" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px 24px;margin:10px 0 0">'
    '<div><dt class="lbl">Nom affiché</dt><dd id="acc-name" style="margin:4px 0 0;overflow-wrap:anywhere">Chargement…</dd></div>'
    '<div><dt class="lbl">Identifiant</dt><dd id="acc-user" style="margin:4px 0 0;overflow-wrap:anywhere">—</dd></div>'
    '<div><dt class="lbl">Rôle</dt><dd id="acc-role" style="margin:4px 0 0">—</dd></div>'
    '<div><dt class="lbl">Courriel</dt><dd id="acc-mail" style="margin:4px 0 0;overflow-wrap:anywhere">—</dd></div></dl>'
    '<form id="acc-pw" novalidate style="margin-top:18px;display:flex;flex-direction:column;gap:12px">'
    '<p class="lbl" style="margin:0">Changer le mot de passe</p>'
    '<div class="g2" style="align-items:start">'
    '<div class="fld"><label class="lbl" for="acc-cur">Mot de passe actuel</label><input class="in" id="acc-cur" type="password" autocomplete="current-password"></div>'
    '<div class="fld"><label class="lbl" for="acc-new">Nouveau mot de passe</label><input class="in" id="acc-new" type="password" autocomplete="new-password" aria-describedby="acc-pw-hint"><p class="hint" id="acc-pw-hint">12 caractères minimum. Une courte phrase fonctionne bien.</p></div>'
    '</div>'
    '<div class="g2" style="align-items:start"><div class="fld"><label class="lbl" for="acc-new2">Confirmez le nouveau mot de passe</label><input class="in" id="acc-new2" type="password" autocomplete="new-password"></div></div>'
    '<p id="acc-pw-msg" role="status" aria-live="polite" class="hint" style="margin:0"></p>'
    '<div><button type="submit" class="btn btn-line" id="acc-pw-btn">Changer le mot de passe</button></div>'
    '</form></div></section>'

    '<section class="card" aria-labelledby="acc-t2"><div class="card-h"><span class="num" aria-hidden="true">2</span>'
    '<div><h3 class="ttl" id="acc-t2">Appareils connectés</h3><p class="dsc">Les sessions ouvertes sur votre compte en ce moment.</p></div></div>'
    '<div class="card-b"><ul id="acc-sessions" style="list-style:none;margin:10px 0 0;padding:0;display:flex;flex-direction:column;gap:8px"><li class="hint">Chargement…</li></ul>'
    '<p id="acc-sess-msg" role="status" aria-live="polite" class="hint" style="margin:10px 0 0"></p>'
    '<div style="margin-top:10px"><button type="button" class="btn btn-line" id="acc-revoke">Déconnecter les autres appareils</button></div>'
    '</div></section>'

    '<section class="card" id="acc-journal" aria-labelledby="acc-t3" hidden><div class="card-h"><span class="num" aria-hidden="true">3</span>'
    '<div><h3 class="ttl" id="acc-t3">Journal des modifications</h3><p class="dsc">Les 20 dernières actions dans le panneau : qui, quoi, quand.</p></div></div>'
    '<div class="card-b"><div style="overflow-x:auto;margin-top:10px;border:1px solid #E4D9C0;border-radius:12px;background:#fff" tabindex="0" aria-label="Journal des modifications, défilable horizontalement">'
    '<table style="width:100%;border-collapse:collapse;font-size:14px;min-width:520px"><caption class="sr" style="position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)">Journal des modifications</caption>'
    '<thead><tr style="background:#F6EEDF;color:#0E4D3C;text-align:left">'
    '<th scope="col" style="padding:10px 12px">Quand</th><th scope="col" style="padding:10px 12px">Action</th><th scope="col" style="padding:10px 12px">Par</th></tr></thead>'
    '<tbody id="acc-journal-rows"><tr><td colspan="3" style="padding:10px 12px" class="hint">Chargement…</td></tr></tbody></table></div>'
    '</div></section>'
    '</div>'
)


# ---------------------------------------------------------------- Composant React (DCLogic) de SA-Site.dc.html
SITE_COMPONENT = r"""
class Component extends DCLogic {
  constructor(props) {
    super(props);
    this.base = {
      "pg_accueil": true, "pg_horaires": true, "pg_apropos": true, "pg_services": true,
      "pg_dons": true, "pg_evenements": true, "pg_ressources": true, "pg_contact": true,
      "pg_cours": true, "pg_mariages": true, "pg_funerailles": true, "pg_aide": true,
      "pg_femmes": true, "pg_khutba": true,
      "pg_rappel": true, "pg_campagne": true, "pg_calendrier": true, "pg_inscription": true, "pg_dua": true,
      "mode_auto": true, "lang_fr": true, "lang_ar": true, "lang_en": true,
      "alerte": false, "sec_2fa": false, "sec_auto": true
    };
    this.pubKeys = [
      "pg_horaires", "pg_apropos", "pg_services", "pg_dons", "pg_evenements", "pg_ressources", "pg_contact",
      "pg_cours", "pg_mariages", "pg_funerailles", "pg_aide", "pg_femmes", "pg_khutba",
      "pg_rappel", "pg_campagne", "pg_calendrier", "pg_inscription", "pg_dua"
    ];
    this.n2Keys = ["pg_cours", "pg_mariages", "pg_funerailles", "pg_aide", "pg_femmes", "pg_khutba"];
    this.n3Keys = ["pg_rappel", "pg_campagne", "pg_calendrier", "pg_inscription", "pg_dua"];
    this.state = { on: Object.assign({}, this.base), toast: '' };
  }
  componentWillUnmount() { clearTimeout(this.tt); }
  componentDidMount() {
    this.listenSeason();
    this.loadSeason();
    this.listenAlert();
    this.loadAlert();
    this.loadCustomPages();
    fetch('/api/admin/settings/pages', { credentials: 'same-origin' })
      .then((r) => r.json().catch(() => ({ ok: false })))
      .then((d) => {
        if (!d.ok) { this.flash(d.message || 'Impossible de charger l’état des pages. Rechargez la page.'); return; }
        const clean = Object.assign({}, d.settings, { pg_accueil: true });
        this.base = Object.assign({}, this.base, clean);
        this.setState({ on: Object.assign({}, this.state.on, clean) });
      })
      .catch(() => this.flash('Impossible de joindre le serveur. Vérifiez votre connexion et rechargez la page.'));
  }
  todayIso() {
    try {
      const p = {};
      new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Moncton', year: 'numeric', month: '2-digit', day: '2-digit' })
        .formatToParts(new Date()).forEach((x) => { p[x.type] = x.value; });
      if (p.year && p.month && p.day) return p.year + '-' + p.month + '-' + p.day;
    } catch (e) {}
    const d = new Date();
    return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
  }
  alertLinks() {
    return __ALERT_LINKS__;
  }
  readAlertForm() {
    const v = (id) => { const e = document.getElementById(id); return e ? e.value : ''; };
    const sel = document.getElementById('f5');
    const label = sel && sel.selectedIndex > -1 ? sel.options[sel.selectedIndex].text.trim() : '';
    const opt = sel && sel.selectedIndex > -1 ? sel.options[sel.selectedIndex] : null;
    const customSlug = opt ? opt.getAttribute('data-custom-slug') : null;
    const found = this.alertLinks().find((x) => x[1] === label);
    const key = customSlug ? '__custom' : found ? found[0] : '';
    const pressed = document.querySelector('[data-alert-tone][aria-pressed="true"]');
    return {
      on: !!this.state.on.alerte,
      message: v('f4').replace(/\s+/g, ' ').trim(),
      link: key === '__custom' ? { type: 'custom', slug: customSlug } : key === '__url' ? { type: 'url', url: v('alert-url').trim() } : key ? { type: 'page', page: key } : { type: 'none' },
      from: v('f6'), to: v('f7'),
      tone: pressed ? pressed.getAttribute('data-alert-tone') : 'attention'
    };
  }
  setAlertForm(a) {
    const set = (id, val) => { const e = document.getElementById(id); if (e) e.value = val || ''; };
    set('f4', a.message); set('f6', a.from); set('f7', a.to);
    const key = a.link && a.link.type === 'url' ? '__url' : a.link && a.link.type === 'page' ? a.link.page : '';
    const sel = document.getElementById('f5');
    if (sel && a.link && a.link.type === 'custom') {
      this.addCustomOption(sel, a.link.slug, 'Ma page : /p/' + a.link.slug + ' (non publiée ou supprimée)');
      for (let i = 0; i < sel.options.length; i++) if (sel.options[i].getAttribute('data-custom-slug') === a.link.slug) sel.selectedIndex = i;
    } else if (sel) {
      const label = (this.alertLinks().find((x) => x[0] === key) || this.alertLinks()[0])[1];
      for (let i = 0; i < sel.options.length; i++) if (sel.options[i].text.trim() === label) sel.selectedIndex = i;
    }
    set('alert-url', a.link && a.link.type === 'url' ? a.link.url : '');
    this.showAlertUrl();
    document.querySelectorAll('[data-alert-tone]').forEach((b) => b.setAttribute('aria-pressed', String(b.getAttribute('data-alert-tone') === a.tone)));
    this.updateAlertPreview();
  }
  addCustomOption(sel, slug, text) {
    for (let i = 0; i < sel.options.length; i++) if (sel.options[i].getAttribute('data-custom-slug') === slug) return;
    const o = document.createElement('option');
    o.textContent = text;
    o.setAttribute('data-custom-slug', slug);
    let ext = null;
    for (let i = 0; i < sel.options.length; i++) if (sel.options[i].text.trim() === 'Lien externe…') ext = sel.options[i];
    sel.insertBefore(o, ext);
  }
  loadCustomPages() {
    fetch('/api/admin/pages', { credentials: 'same-origin' })
      .then((r) => r.json().catch(() => ({ ok: false })))
      .then((d) => {
        const sel = document.getElementById('f5');
        if (!d.ok || !sel) return;
        d.pages.filter((p) => p.visibility !== 'draft').forEach((p) => this.addCustomOption(sel, p.slug, 'Ma page : ' + p.title));
        if (this.alertBase) this.setAlertForm(this.alertBase);
      })
      .catch(() => {});
  }
  showAlertUrl() {
    const w = document.getElementById('alert-url-wrap'), sel = document.getElementById('f5');
    if (w && sel) w.style.display = sel.selectedIndex > -1 && sel.options[sel.selectedIndex].text.trim() === 'Lien externe…' ? 'flex' : 'none';
  }
  updateAlertPreview() {
    const bar = document.getElementById('alert-pv-bar');
    const row = document.getElementById('alert-pv-row');
    const badge = document.getElementById('alert-pv-badge');
    const note = document.getElementById('alert-pv-note');
    const clearBtn = document.getElementById('alert-clear-btn');
    if (!bar || !row || !badge || !note) return;

    const a = this.readAlertForm();
    const TONES = {
      info: { bg: '#0E4D3C', fg: '#FFFFFF', label: 'Information (vert)' },
      attention: { bg: '#C49A4A', fg: '#1E2B26', label: 'Attention (or)' },
      urgent: { bg: '#B3261E', fg: '#FFFFFF', label: 'Urgent (rouge)' }
    };
    const FILES = {
      pg_horaires: 'Horaires.dc.html', pg_apropos: 'APropos.dc.html', pg_services: 'Services.dc.html',
      pg_dons: 'Dons.dc.html', pg_evenements: 'Evenements.dc.html', pg_ressources: 'Ressources.dc.html',
      pg_contact: 'Contact.dc.html', pg_cours: 'N2-Cours.dc.html', pg_mariages: 'N2-Mariages.dc.html',
      pg_funerailles: 'N2-Funerailles.dc.html', pg_aide: 'N2-AideAlimentaire.dc.html',
      pg_femmes: 'N2-EspaceFemmes.dc.html', pg_khutba: 'N2-Khutba.dc.html', pg_rappel: 'N3-Rappel.dc.html',
      pg_campagne: 'N3-Campagne.dc.html', pg_calendrier: 'N3-Calendrier.dc.html',
      pg_inscription: 'N3-Inscription.dc.html', pg_dua: 'N3-Dua.dc.html'
    };
    const t = TONES[a.tone] || TONES.attention;
    bar.style.background = t.bg;
    bar.style.color = t.fg;
    bar.style.opacity = (a.on && a.message) ? '1' : '0.82';

    const iconSvg = a.tone === 'info'
      ? '<circle cx="12" cy="12" r="10"></circle><path d="M12 16v-4"></path><path d="M12 8h.01"></path>'
      : '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"></path><path d="M12 9v4"></path><path d="M12 17h.01"></path>';
    row.innerHTML = '<svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex:none">' + iconSvg + '</svg>';

    const msgEl = document.createElement('p');
    msgEl.style.cssText = 'margin:0;min-width:0;overflow-wrap:anywhere' + (a.message ? '' : ';font-style:italic;opacity:.9');
    msgEl.textContent = a.message || '(Aucun message saisi — écrivez un message ci-dessus pour pouvoir afficher la bannière)';
    row.appendChild(msgEl);

    const href = a.link && a.link.type === 'page' && FILES[a.link.page] ? FILES[a.link.page]
      : a.link && a.link.type === 'custom' && a.link.slug ? '/p/' + a.link.slug
      : a.link && a.link.type === 'url' && a.link.url ? a.link.url : '';
    if (href) {
      const lnk = document.createElement('a');
      lnk.href = href;
      lnk.target = '_blank';
      lnk.rel = 'noopener';
      lnk.textContent = 'En savoir plus';
      lnk.style.cssText = 'color:inherit;text-decoration:underline;text-underline-offset:3px;display:inline-flex;align-items:center;min-height:24px;padding:2px 4px';
      row.appendChild(lnk);
    }

    const hasExtra = (a.link && a.link.type !== 'none') || !!a.from || !!a.to || a.tone !== 'attention';
    if (clearBtn) {
      clearBtn.style.display = (!a.on && !a.message && hasExtra) ? 'inline-flex' : 'none';
    }

    const now = this.todayIso();
    if (!a.on) {
      if (!a.message && hasExtra) {
        badge.textContent = 'Désactivée · Message vide';
        badge.style.background = '#F3EAD8';
        badge.style.color = '#7A5A1E';
        note.textContent = 'La bannière n’est pas affichée sur le site (« Afficher » est désactivé et le message est vide). Le lien, les dates et la couleur ci-dessus restent en réserve tant que vous ne l’activez pas avec un message.';
      } else if (a.message) {
        badge.textContent = 'Désactivée (brouillon)';
        badge.style.background = '#F3EAD8';
        badge.style.color = '#7A5A1E';
        note.textContent = 'La bannière est prête mais masquée sur le site. Activez « Afficher » puis cliquez sur « Enregistrer » pour la publier.';
      } else {
        badge.textContent = 'Désactivée';
        badge.style.background = '#F3EAD8';
        badge.style.color = '#7A5A1E';
        note.textContent = 'Aucune bannière d’alerte n’est affichée sur le site public.';
      }
    } else if (!a.message) {
      badge.textContent = 'Message requis';
      badge.style.background = '#FBEAE8';
      badge.style.color = '#8C1D18';
      note.textContent = 'Une bannière sans message ne peut pas être affichée sur le site. Saisissez un message ou désactivez « Afficher ».';
    } else if (a.from && now < a.from) {
      badge.textContent = 'Programmée';
      badge.style.background = '#E6EEF8';
      badge.style.color = '#1F4E86';
      note.textContent = 'La bannière s’affichera automatiquement sur le site à partir du ' + a.from + (a.to ? ' jusqu’au ' + a.to : '') + '.';
    } else if (a.to && now > a.to) {
      badge.textContent = 'Période terminée';
      badge.style.background = '#F3EAD8';
      badge.style.color = '#7A5A1E';
      note.textContent = 'La date de fin (' + a.to + ') est dépassée : la bannière n’est plus visible sur le site public.';
    } else {
      badge.textContent = 'Affichée sur le site';
      badge.style.background = '#DCEFE6';
      badge.style.color = '#0E4D3C';
      note.textContent = 'La bannière est visible en haut de toutes les pages publiques' + (a.to ? ' jusqu’au ' + a.to : '') + '.';
    }
  }
  alertDirty() {
    if (!this.alertBase) return false;
    return JSON.stringify(this.readAlertForm()) !== JSON.stringify(Object.assign({}, this.alertBase, { on: !!this.base.alerte }));
  }
  listenAlert() {
    const inCard = (t) => t && t.closest && t.closest('section[aria-label="Bannière d’alerte"]');
    const changed = (e) => {
      if (inCard(e.target)) {
        this.showAlertUrl();
        this.updateAlertPreview();
        this.forceUpdate();
      }
    };
    document.addEventListener('input', changed);
    document.addEventListener('change', changed);
    document.addEventListener('click', (e) => {
      const b = e.target.closest && e.target.closest('[data-alert-tone]');
      if (b) {
        document.querySelectorAll('[data-alert-tone]').forEach((x) => x.setAttribute('aria-pressed', String(x === b)));
        this.updateAlertPreview();
        this.forceUpdate();
        return;
      }
      const clr = e.target.closest && e.target.closest('#alert-clear-btn');
      if (clr) {
        this.setAlertForm({ on: false, message: '', link: { type: 'none' }, from: '', to: '', tone: 'attention' });
        this.setState({ on: Object.assign({}, this.state.on, { alerte: false }) });
        this.flash('Champs en réserve effacés. Cliquez sur « Enregistrer » pour confirmer.');
      }
    });
  }
  loadAlert() {
    fetch('/api/admin/settings/alert', { credentials: 'same-origin' })
      .then((r) => r.json().catch(() => ({ ok: false })))
      .then((d) => {
        if (!d.ok) { this.flash(d.message || 'Impossible de charger la bannière d’alerte. Rechargez la page.'); return; }
        this.alertBase = d.settings;
        this.base = Object.assign({}, this.base, { alerte: d.settings.on });
        this.setState({ on: Object.assign({}, this.state.on, { alerte: d.settings.on }) }, () => this.updateAlertPreview());
        this.setAlertForm(d.settings);
      })
      .catch(() => this.flash('Impossible de joindre le serveur. Vérifiez votre connexion et rechargez la page.'));
  }
  readSeasonForm() {
    const v = (id) => { const e = document.getElementById(id); return e ? e.value : ''; };
    const pressed = document.querySelector('[data-season-mode][aria-pressed="true"]');
    const fr = document.querySelector('[data-friday-mode][aria-pressed="true"]');
    return { mode: pressed ? pressed.getAttribute('data-season-mode') : 'normal', from: v('f2'), to: v('f3'), auto: !!this.state.on.mode_auto,
      vendredi: fr ? fr.getAttribute('data-friday-mode') : ((this.seasonBase && this.seasonBase.vendredi) || 'off') };
  }
  setSeasonForm(a) {
    const set = (id, val) => { const e = document.getElementById(id); if (e) e.value = val || ''; };
    set('f2', a.from); set('f3', a.to);
    document.querySelectorAll('[data-season-mode]').forEach((b) => b.setAttribute('aria-pressed', String(b.getAttribute('data-season-mode') === a.mode)));
    document.querySelectorAll('[data-friday-mode]').forEach((b) => b.setAttribute('aria-pressed', String(b.getAttribute('data-friday-mode') === (a.vendredi || 'off'))));
    this.updateSeasonStatus();
  }
  updateFridayStatus(s) {
    const el = document.getElementById('friday-live-status');
    if (!el) return;
    const v = s.vendredi || 'off';
    const now = this.todayIso();
    const isFri = /^\d{4}-\d\d-\d\d$/.test(now) && new Date(now + 'T12:00:00Z').getUTCDay() === 5;
    const season = s.mode !== 'normal' && (!s.auto || (s.from && s.to && now >= s.from && now <= s.to));
    if (v === 'off') el.textContent = 'État sur le site : thème du vendredi désactivé.';
    else if (season) el.textContent = 'État sur le site : le mode de saison en cours passe avant ; le thème du vendredi reviendra après la période.';
    else if (v === 'on') el.textContent = 'État sur le site : Accueil du vendredi affiché tous les jours, jusqu’à ce que vous le désactiviez.';
    else el.textContent = isFri ? 'État sur le site : c’est vendredi, l’Accueil du vendredi est affiché aujourd’hui.'
      : 'État sur le site : l’Accueil du vendredi s’affichera automatiquement vendredi prochain.';
  }
  updateSeasonStatus() {
    const el = document.getElementById('season-live-status');
    if (!el) return;
    const s = this.readSeasonForm();
    this.updateFridayStatus(s);
    const LABELS = { normal: 'Normal', ramadan: 'Ramadan', aid_fitr: 'Aïd al-Fitr', aid_adha: 'Aïd al-Adha' };
    const now = this.todayIso();
    if (s.mode === 'normal') {
      if (s.from || s.to) {
        el.textContent = 'État sur le site : Mode Normal actif (aucun bandeau de saison affiché sur l’accueil). Les dates ' +
          (s.from || '…') + ' → ' + (s.to || '…') + ' restent mémorisées (et servent de période Ramadan dans Horaires).';
      } else {
        el.textContent = 'État sur le site : Mode Normal actif. Les dates suivent l’annonce officielle de la TCOM.';
      }
      return;
    }
    const name = LABELS[s.mode] || s.mode;
    if (!s.auto) {
      el.textContent = 'État sur le site : Bandeau « ' + name + ' » affiché immédiatement en haut de l’accueil (changement automatique aux dates désactivé).';
    } else if (!s.from || !s.to) {
      el.textContent = 'Choisissez les dates de début et de fin pour activer automatiquement le mode « ' + name + ' ».';
    } else if (now < s.from) {
      el.textContent = 'État sur le site : Mode « ' + name + ' » programmé du ' + s.from + ' au ' + s.to + ' (en attente de la date de début).';
    } else if (now > s.to) {
      el.textContent = 'État sur le site : Période du ' + s.from + ' au ' + s.to + ' terminée — le site affiche le mode Normal.';
    } else {
      el.textContent = 'État sur le site : Bandeau « ' + name + ' » actif en direct sur l’accueil (du ' + s.from + ' au ' + s.to + ').';
    }
  }
  seasonDirty() {
    if (!this.seasonBase) return false;
    return JSON.stringify(this.readSeasonForm()) !== JSON.stringify(Object.assign({ mode: 'normal', from: '', to: '', auto: true, vendredi: 'off' }, this.seasonBase, { auto: !!this.base.mode_auto }));
  }
  listenSeason() {
    const inCard = (t) => t && t.closest && t.closest('section[aria-label="Mode du site"]');
    const changed = (e) => { if (inCard(e.target)) { this.updateSeasonStatus(); this.forceUpdate(); } };
    document.addEventListener('input', changed);
    document.addEventListener('change', changed);
    document.addEventListener('click', (e) => {
      const f = e.target.closest && e.target.closest('[data-friday-mode]');
      if (f) {
        document.querySelectorAll('[data-friday-mode]').forEach((x) => x.setAttribute('aria-pressed', String(x === f)));
        this.updateSeasonStatus();
        this.forceUpdate();
        return;
      }
      const b = e.target.closest && e.target.closest('[data-season-mode]');
      if (!b) return;
      document.querySelectorAll('[data-season-mode]').forEach((x) => x.setAttribute('aria-pressed', String(x === b)));
      this.updateSeasonStatus();
      this.forceUpdate();
    });
  }
  loadSeason() {
    const get = (key) => fetch('/api/admin/settings/' + key, { credentials: 'same-origin' }).then((r) => r.json().catch(() => ({ ok: false })));
    Promise.all([get('season'), get('languages')])
      .then(([s, l]) => {
        if (!s.ok || !l.ok) { this.flash((!s.ok ? s : l).message || 'Impossible de charger la saison et les langues. Rechargez la page.'); return; }
        this.seasonBase = s.settings;
        const sw = { mode_auto: s.settings.auto, lang_fr: true, lang_ar: l.settings.ar, lang_en: l.settings.en };
        this.base = Object.assign({}, this.base, sw);
        this.setState({ on: Object.assign({}, this.state.on, sw) }, () => this.updateSeasonStatus());
        this.setSeasonForm(s.settings);
      })
      .catch(() => this.flash('Impossible de joindre le serveur. Vérifiez votre connexion et rechargez la page.'));
  }
  saveAll() {
    if (this.saving) return;
    const alert = this.readAlertForm(), season = this.readSeasonForm();
    if (alert.on && !alert.message) { this.flash('Écrivez le message de la bannière, ou désactivez-la.'); document.getElementById('f4') && document.getElementById('f4').focus(); return; }
    if (alert.link.type === 'url' && !/^https?:\/\/\S{3,}$/i.test(alert.link.url)) { this.flash('L’adresse du lien externe doit commencer par https://'); return; }
    if (season.mode !== 'normal' && season.auto && (!season.from || !season.to)) {
      this.flash('Indiquez le début et la fin de la période, ou désactivez le changement automatique aux dates.');
      document.getElementById(season.from ? 'f3' : 'f2') && document.getElementById(season.from ? 'f3' : 'f2').focus();
      return;
    }
    this.saving = true;
    const on = this.state.on, pages = {};
    Object.keys(on).forEach((k) => { if (k.indexOf('pg_') === 0 && k !== 'pg_accueil') pages[k] = !!on[k]; });
    const languages = { fr: true, ar: !!on.lang_ar, en: !!on.lang_en };

    const pagesChanged = Object.keys(pages).some((k) => pages[k] !== !!this.base[k]);
    const alertChanged = this.alertDirty();
    const seasonChanged = this.seasonDirty();
    const langChanged = on.lang_ar !== this.base.lang_ar || on.lang_en !== this.base.lang_en;
    const anySpecific = pagesChanged || alertChanged || seasonChanged || langChanged;

    this.flash('Enregistrement…');
    const put = (key, body, shouldPut) => (!anySpecific || shouldPut)
      ? fetch('/api/admin/settings/' + key, {
          method: 'PUT', credentials: 'same-origin', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body)
        }).then((r) => r.json().catch(() => ({ ok: false })))
      : Promise.resolve({ ok: true, skipped: true });

    Promise.all([
      put('pages', pages, pagesChanged),
      put('alert', alert, alertChanged),
      put('season', season, seasonChanged),
      put('languages', languages, langChanged)
    ])
      .then(([p, a, se, la]) => {
        this.saving = false;
        const failed = [p, a, se, la].find((x) => !x.ok);
        if (failed) { this.flash(failed.message || 'L’enregistrement a échoué. Réessayez.'); return; }
        if (!a.skipped && a.settings) this.alertBase = a.settings;
        if (!se.skipped && se.settings) this.seasonBase = se.settings;
        const nextPages = (!p.skipped && p.settings) ? p.settings : pages;
        const nextAlert = this.alertBase || alert;
        const nextSeason = this.seasonBase || season;
        const nextLang = (!la.skipped && la.settings) ? la.settings : languages;
        this.base = Object.assign({}, this.base, nextPages, {
          pg_accueil: true,
          alerte: nextAlert.on, mode_auto: nextSeason.auto,
          lang_fr: true, lang_ar: nextLang.ar, lang_en: nextLang.en
        });
        this.setState({ on: Object.assign({}, this.state.on, { pg_accueil: true, alerte: nextAlert.on, mode_auto: nextSeason.auto, lang_fr: true }) });
        this.setAlertForm(nextAlert);
        this.setSeasonForm(nextSeason);
        this.forceUpdate();
        if (typeof window.__saReloadJournal === 'function') window.__saReloadJournal();
        this.flash('Réglages enregistrés. Le site est à jour.');
      })
      .catch(() => { this.saving = false; this.flash('Impossible de joindre le serveur. Vérifiez votre connexion et réessayez.'); });
  }
  flash(m) { this.setState({ toast: m }); clearTimeout(this.tt); this.tt = setTimeout(() => this.setState({ toast: '' }), 2400); }
  renderVals() {
    const on = this.state.on;
    const dirty = Object.keys(on).some((k) => on[k] !== this.base[k]) || this.alertDirty() || this.seasonDirty();
    const s = {}, off = {}, op = {}, pub = {};
    Object.keys(on).forEach((k) => {
      const locked = (k === 'pg_accueil' || k === 'lang_fr');
      s[k] = {
        c: String(locked ? true : !!on[k]),
        t: () => {
          if (locked) return null;
          const next = Object.assign({}, this.state.on, { [k]: !this.state.on[k] });
          this.setState({ on: next }, () => {
            if (k === 'alerte') this.updateAlertPreview();
            if (k === 'mode_auto') this.updateSeasonStatus();
          });
        }
      };
      off[k] = on[k] ? '' : 'off';
      op[k] = on[k] ? 1 : 0.5;
    });
    this.pubKeys.forEach((k) => {
      pub[k] = on[k]
        ? { t: 'Publiée sur le site', sub: 'Actuellement visible sur le site public', bg: '#DCEFE6', fg: '#0E4D3C' }
        : { t: 'Masquée du site', sub: 'Masquée du site public', bg: '#F3EAD8', fg: '#7A5A1E' };
    });
    ['lang_ar', 'lang_en'].forEach((k) => {
      pub[k] = on[k]
        ? { t: 'Active', bg: '#DCEFE6', fg: '#0E4D3C' }
        : { t: 'Masquée', bg: '#F3EAD8', fg: '#7A5A1E' };
    });
    const n2On = this.n2Keys.filter((k) => !!on[k]).length;
    const n3On = this.n3Keys.filter((k) => !!on[k]).length;
    const n2Summary = n2On === 0
      ? 'État actuel : les 6 services sont masqués du site public.'
      : 'État actuel : ' + n2On + ' sur 6 service(s) sont actuellement publiés et visibles sur le site public. Basculez un interrupteur puis cliquez sur « Enregistrer » pour masquer ou publier une page.';
    const n3Summary = n3On === 0
      ? 'État actuel : les 5 applications sont masquées du site public.'
      : 'État actuel : ' + n3On + ' sur 5 application(s) sont actuellement publiées et visibles sur le site public. Basculez un interrupteur puis cliquez sur « Enregistrer » pour masquer ou publier une page.';

    return {
      s, off, op, pub, n2Summary, n3Summary,
      clean: !dirty, dot: dirty ? '#C49A4A' : '#7FB89F', statusTxt: dirty ? 'Changements non enregistrés' : 'Tout est enregistré',
      save: () => this.saveAll(),
      undo: () => {
        this.setState({ on: Object.assign({}, this.base) }, () => {
          if (this.alertBase) this.setAlertForm(this.alertBase);
          if (this.seasonBase) this.setSeasonForm(this.seasonBase);
          this.updateAlertPreview();
          this.updateSeasonStatus();
        });
        this.flash('Changements annulés.');
      },
      toast: this.state.toast
    };
  }
}
"""


# ---------------------------------------------------------------- Script Compte et sécurité + Journal
ACCOUNT_SCRIPT = r"""<script id="sa-site-account">
(function () {
  var ROLE = { superadmin: 'Superadmin', editor: 'Éditeur', events: 'Responsable événements' };
  var ACTIONS = {
    'auth.login': 'Connexion', 'auth.logout': 'Déconnexion', 'auth.login_failed': 'Échec de connexion',
    'auth.password_changed': 'Mot de passe changé', 'auth.sessions_revoked': 'Autres appareils déconnectés',
    'account.create': 'Compte créé', 'account.update': 'Compte modifié', 'account.reset_password': 'Mot de passe réinitialisé',
    'events.settings_update': 'Réglages de l’événement modifiés', 'events.registration_cancel': 'Inscription annulée',
    'settings.update': 'Réglages modifiés', 'pages.create': 'Page créée', 'pages.update': 'Page modifiée',
    'pages.duplicate': 'Page dupliquée', 'pages.delete': 'Page supprimée',
    'prayer_times.update': 'Horaires du mois modifiés',
    'forms.status': 'Statut d’une demande reçue changé', 'forms.delete': 'Demande reçue supprimée',
    'dua.publier': 'Message du mur Dua publié', 'dua.refuser': 'Message du mur Dua refusé', 'dua.retirer': 'Message retiré du mur Dua',
    'dua.modifier': 'Message du mur Dua corrigé', 'dua.delete': 'Message du mur Dua supprimé',
    'media.upload': 'Photo envoyée', 'media.delete': 'Photo supprimée du stockage',
    'widgets.create': 'Widget créé', 'widgets.update': 'Widget modifié', 'widgets.delete': 'Widget supprimé',
    'cforms.create': 'Formulaire créé', 'cforms.update': 'Formulaire modifié', 'cforms.delete': 'Formulaire supprimé',
    'cforms.entries.status': 'Statut de réponses changé', 'cforms.entries.delete': 'Réponse à un formulaire supprimée'
  };
  var TARGETS = {
    'settings:home': 'Accueil', 'settings:pages': 'Pages publiées', 'settings:event_registration': 'Événement',
    'settings:alert': 'Bannière d’alerte', 'settings:season': 'Mode du site', 'settings:languages': 'Langues', 'settings:traductions': 'Traductions', 'settings:photos': 'Photos de l’Accueil',
    'settings:horaires': 'Horaires', 'settings:khutba': 'Langue de la khutba', 'settings:rappel': 'Rappel de prière',
    'settings:apropos': 'À propos', 'settings:campagne': 'Campagne en direct', 'settings:services': 'Services',
    'settings:cours': 'Cours', 'settings:mariages': 'Mariages', 'settings:funerailles': 'Funérailles', 'settings:aide': 'Aide alimentaire',
    'settings:femmes': 'Espace femmes', 'settings:dons': 'Faire un don', 'settings:merci': 'Bloc Merci (Faire un don)',
    'settings:evenements': 'Événements', 'settings:calendrier': 'Calendrier du mois',
    'settings:ressources': 'Ressources (nouveaux arrivants)', 'settings:dua': 'Règles du mur Dua et annonces',
    'settings:contact': 'Page Contact', 'settings:p404': 'Page 404'
  };
  var PAGE_NAMES = {
    pg_accueil: 'Accueil', pg_horaires: 'Horaires du mois', pg_apropos: 'À propos', pg_services: 'Services',
    pg_dons: 'Faire un don', pg_evenements: 'Événements', pg_ressources: 'Ressources', pg_contact: 'Contact',
    pg_cours: 'Cours de Coran et d’arabe', pg_mariages: 'Mariages', pg_funerailles: 'Funérailles et janaza',
    pg_aide: 'Aide alimentaire', pg_femmes: 'Espace femmes', pg_khutba: 'Langue de la khutba',
    pg_rappel: 'Rappel de prière', pg_campagne: 'Campagne en direct', pg_calendrier: 'Calendrier du mois',
    pg_inscription: 'Inscription aux événements', pg_dua: 'Dua et annonces'
  };
  function $(id) { return document.getElementById(id); }
  function text(id, v) { var e = $(id); if (e) e.textContent = v; }
  function when(iso) {
    var d = new Date(iso);
    return isNaN(d) ? '—' : d.toLocaleString('fr-CA', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' });
  }
  function device(ua) {
    var os = /iPhone/.test(ua) ? 'iPhone' : /iPad/.test(ua) ? 'iPad' : /Android/.test(ua) ? 'Android'
      : /Macintosh|Mac OS X/.test(ua) ? 'Mac' : /Windows/.test(ua) ? 'Windows' : /Linux/.test(ua) ? 'Linux' : 'Appareil inconnu';
    var br = /Edg\//.test(ua) ? 'Edge' : /Firefox\//.test(ua) ? 'Firefox' : /Chrome\//.test(ua) ? 'Chrome' : /Safari\//.test(ua) ? 'Safari' : '';
    return br ? os + ' · ' + br : os;
  }
  function getJson(url, opt) {
    return fetch(url, Object.assign({ credentials: 'same-origin' }, opt || {}))
      .then(function (r) { return r.json().catch(function () { return { ok: false }; }).then(function (d) { d.status = r.status; return d; }); });
  }
  function formatAuditAction(e, customById) {
    var base = ACTIONS[e.action] || e.action;
    var d = e.details && typeof e.details === 'object' ? e.details : null;

    if (e.target && e.target.indexOf('page:') === 0) {
      var pid = e.target.slice(5);
      var fromMap = customById && customById[pid] ? customById[pid] : null;
      var title = e.pageTitle || (d && d.title) || (fromMap && fromMap.title) || '';
      var slug = e.pageSlug || (d && (d.newSlug || d.slug)) || (fromMap && fromMap.slug) || '';
      if (title && slug) return base + ' : « ' + title + ' » (/p/' + slug + ')';
      if (title) return base + ' : « ' + title + ' »';
      if (slug) return base + ' : /p/' + slug;
      return base + ' (page #' + pid + ')';
    }

    if (e.target && TARGETS[e.target]) {
      var label = base + ' : ' + TARGETS[e.target];
      if (e.target === 'settings:pages' && d) {
        var pub = Array.isArray(d.published) ? d.published.map(function (k) { return PAGE_NAMES[k] || k; }) : [];
        var hid = Array.isArray(d.hidden) ? d.hidden.map(function (k) { return PAGE_NAMES[k] || k; }) : [];
        var parts = [];
        if (pub.length) parts.push('publiée(s) : ' + pub.join(', '));
        if (hid.length) parts.push('masquée(s) : ' + hid.join(', '));
        if (parts.length) label += ' (' + parts.join(' ; ') + ')';
      }
      return label;
    }

    if (e.target && /^(media|widget|form):/.test(e.target)) {
      var nm = d && (d.title || d.name) ? ' : « ' + (d.title || d.name) + ' »' : '';
      return base + nm + (d && Array.isArray(d.ids) ? ' (' + d.ids.length + ')' : '');
    }

    if (e.target && e.target.indexOf('prayer_times:') === 0) {
      return base + ' : ' + e.target.slice('prayer_times:'.length);
    }

    if (e.target && e.target.indexOf('admin:') === 0 && d && d.username) {
      return base + ' : ' + d.username;
    }

    if (e.action === 'events.registration_cancel' && d && d.fullName) {
      return base + ' : ' + d.fullName;
    }

    return base;
  }
  function loadMe() {
    getJson('/api/auth/me').then(function (d) {
      if (!d.ok) { text('acc-name', 'Impossible de charger votre compte. Rechargez la page.'); return; }
      var a = d.admin;
      text('acc-name', a.displayName || '—');
      text('acc-user', a.username);
      text('acc-role', a.roleLabel || ROLE[a.role] || a.role);
      text('acc-mail', a.email || 'Aucun courriel enregistré');
      if (a.role === 'superadmin') loadJournal();
    }, function () { text('acc-name', 'Impossible de joindre le serveur. Rechargez la page.'); });
  }
  function loadSessions() {
    getJson('/api/auth/sessions').then(function (d) {
      var ul = $('acc-sessions'); if (!ul) return;
      ul.innerHTML = '';
      if (!d.ok) { ul.innerHTML = '<li class="hint">Impossible de charger les appareils connectés.</li>'; return; }
      d.sessions.forEach(function (s) {
        var li = document.createElement('li');
        li.style.cssText = 'display:flex;flex-wrap:wrap;gap:4px 12px;align-items:baseline;padding:10px 12px;border:1px solid #E4D9C0;border-radius:12px;background:#fff';
        var b = document.createElement('strong'); b.textContent = device(s.userAgent) + (s.current ? ' (cet appareil)' : '');
        var span = document.createElement('span'); span.className = 'hint'; span.style.margin = '0';
        span.textContent = 'Dernière activité : ' + when(s.lastSeenAt) + ' · connecté le ' + when(s.createdAt);
        li.appendChild(b); li.appendChild(span); ul.appendChild(li);
      });
      var others = d.sessions.filter(function (s) { return !s.current; }).length;
      var btn = $('acc-revoke'); if (btn) btn.style.display = others ? '' : 'none';
      text('acc-sess-msg', others ? '' : 'Aucun autre appareil n’est connecté à votre compte.');
    });
  }
  function loadJournal() {
    Promise.all([
      getJson('/api/admin/audit?limit=20'),
      getJson('/api/admin/pages')
    ]).then(function (res) {
      var d = res[0], pRes = res[1];
      var card = $('acc-journal'), body = $('acc-journal-rows');
      if (!d.ok || !card || !body) return;
      var customById = {};
      if (pRes && pRes.ok && Array.isArray(pRes.pages)) {
        pRes.pages.forEach(function (p) { customById[String(p.id)] = p; });
      }
      card.hidden = false;
      body.innerHTML = '';
      if (!d.entries.length) { body.innerHTML = '<tr><td colspan="3" style="padding:10px 12px" class="hint">Aucune action enregistrée pour l’instant.</td></tr>'; return; }
      d.entries.forEach(function (e) {
        var tr = document.createElement('tr'); tr.style.borderTop = '1px solid #F3EAD8';
        var label = formatAuditAction(e, customById);
        [when(e.createdAt), label, e.username].forEach(function (v) {
          var td = document.createElement('td'); td.style.padding = '10px 12px'; td.textContent = v; tr.appendChild(td);
        });
        body.appendChild(tr);
      });
    });
  }
  window.__saReloadJournal = loadJournal;
  document.addEventListener('click', function (e) {
    var b = e.target.closest && e.target.closest('#acc-revoke');
    if (!b || b.getAttribute('aria-busy') === 'true') return;
    b.setAttribute('aria-busy', 'true'); b.textContent = 'Déconnexion en cours…';
    getJson('/api/auth/sessions', { method: 'DELETE', headers: { 'Content-Type': 'application/json' } }).then(function (d) {
      b.removeAttribute('aria-busy'); b.textContent = 'Déconnecter les autres appareils';
      text('acc-sess-msg', d.ok ? (d.closed + ' autre(s) appareil(s) déconnecté(s).') : (d.message || 'L’opération a échoué. Réessayez.'));
      loadSessions();
      loadJournal();
    }, function () { b.removeAttribute('aria-busy'); b.textContent = 'Déconnecter les autres appareils'; text('acc-sess-msg', 'Impossible de joindre le serveur. Réessayez.'); });
  });
  document.addEventListener('submit', function (e) {
    if (!e.target || e.target.id !== 'acc-pw') return;
    e.preventDefault();
    var cur = $('acc-cur'), n1 = $('acc-new'), n2 = $('acc-new2'), btn = $('acc-pw-btn');
    if (btn.getAttribute('aria-busy') === 'true') return;
    [cur, n1, n2].forEach(function (x) { x.removeAttribute('aria-invalid'); });
    var bad = !cur.value ? [cur, 'Entrez votre mot de passe actuel.']
      : n1.value.length < 12 ? [n1, 'Le nouveau mot de passe doit contenir au moins 12 caractères.']
      : n1.value !== n2.value ? [n2, 'Les deux nouveaux mots de passe ne correspondent pas. Retapez-le.'] : null;
    if (bad) { bad[0].setAttribute('aria-invalid', 'true'); bad[0].focus(); text('acc-pw-msg', bad[1]); return; }
    btn.setAttribute('aria-busy', 'true'); btn.textContent = 'Enregistrement…';
    getJson('/api/auth/password', { method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ current: cur.value, next: n1.value }) }).then(function (d) {
      btn.removeAttribute('aria-busy'); btn.textContent = 'Changer le mot de passe';
      if (d.ok) {
        cur.value = n1.value = n2.value = '';
        text('acc-pw-msg', 'Mot de passe changé. Vos autres appareils ont été déconnectés.');
        loadSessions();
        loadJournal();
      } else {
        if (d.code === 'wrong_current') { cur.setAttribute('aria-invalid', 'true'); cur.focus(); }
        text('acc-pw-msg', d.message || 'Le changement a échoué. Réessayez.');
      }
    }, function () { btn.removeAttribute('aria-busy'); btn.textContent = 'Changer le mot de passe'; text('acc-pw-msg', 'Impossible de joindre le serveur. Réessayez.'); });
  });
  function start() { loadMe(); loadSessions(); }
  if (document.getElementById('acc-info')) start();
  else new MutationObserver(function (m, obs) { if (document.getElementById('acc-info')) { obs.disconnect(); start(); } })
    .observe(document.documentElement, { childList: true, subtree: true });
})();
</script>
"""


def wire_site_panel():
    path = ROOT / 'SA-Site.dc.html'
    s, i, j, tpl = load(path)
    tpl = replace_div_by_id(tpl, 'sp-0', build_sp0())
    tpl = replace_div_by_id(tpl, 'sp-1', build_sp1())
    tpl = replace_div_by_id(tpl, 'sp-2', ACCOUNT_HTML)

    tpl = re.sub(r'<style id="sa-site-style">.*?</style>\s*', '', tpl, flags=re.S)
    k = tpl.index('</helmet>')
    tpl = tpl[:k] + SITE_STYLE + tpl[k:]

    comp_code = SITE_COMPONENT.replace('__ALERT_LINKS__', json.dumps([list(x) for x in ALERT_LINKS], ensure_ascii=False))
    tpl, n = re.subn(r'(<script type="text/x-dc"[^>]*>).*?(</script>)', lambda m: m.group(1) + comp_code + m.group(2), tpl, count=1, flags=re.S)
    assert n == 1, 'script text/x-dc introuvable dans SA-Site.dc.html'

    tpl = re.sub(r'<script id="sa-site-account">.*?</script>\s*', '', tpl, flags=re.S)
    k = tpl.rindex('</body>')
    tpl = tpl[:k] + ACCOUNT_SCRIPT + tpl[k:]

    save(path, s, i, j, tpl)
    print('SA-Site.dc.html : Pages publiées, Saison et langues (avec aperçu bannière), Compte et sécurité branchés')


# ---------------------------------------------------------------- Site public
PUBLIC_SCRIPT = r'''<script id="ascil-pages-sync">
(function () {
  var FILES = { pg_horaires: 'Horaires', pg_apropos: 'APropos', pg_services: 'Services', pg_dons: 'Dons',
    pg_evenements: 'Evenements', pg_ressources: 'Ressources', pg_contact: 'Contact', pg_cours: 'N2-Cours',
    pg_mariages: 'N2-Mariages', pg_funerailles: 'N2-Funerailles', pg_aide: 'N2-AideAlimentaire',
    pg_femmes: 'N2-EspaceFemmes', pg_khutba: 'N2-Khutba', pg_rappel: 'N3-Rappel', pg_campagne: 'N3-Campagne',
    pg_calendrier: 'N3-Calendrier', pg_inscription: 'N3-Inscription', pg_dua: 'N3-Dua' };
  var hidden = {};
  function fileOf(href) {
    var m = /^(?:\.?\/)?(?:M-|T-)?([A-Za-z0-9-]+?)\.dc(?:\.html)?(?:[?#].*)?$/.exec(href || '');
    return m ? m[1] : null;
  }
  function apply() {
    var links = document.querySelectorAll('a[href]');
    for (var i = 0; i < links.length; i++) {
      var a = links[i], f = fileOf(a.getAttribute('href'));
      if (!f || !hidden[f] || a.getAttribute('data-ascil-hidden')) continue;
      a.setAttribute('data-ascil-hidden', '1');
      // Dans une liste (menu, pied de page), on retire la ligne entière.
      var li = a.parentElement && a.parentElement.tagName === 'LI' && a.parentElement.children.length === 1 ? a.parentElement : null;
      (li || a).style.display = 'none';
    }
  }
  fetch('/api/settings/pages', { cache: 'no-store' })
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (d) {
      if (!d || !d.ok) return;
      Object.keys(FILES).forEach(function (k) { if (d.settings[k] === false) hidden[FILES[k]] = true; });
      if (!Object.keys(hidden).length) return;
      if (hidden[fileOf(location.pathname.split('/').pop())]) { location.replace('/'); return; }
      apply();
      new MutationObserver(apply).observe(document.documentElement, { childList: true, subtree: true });
    }, function () {});
})();
</script>
'''

ALERT_SCRIPT = r"""<script id="ascil-alert-banner">
(function () {
  var FILES = { pg_horaires: 'Horaires', pg_apropos: 'APropos', pg_services: 'Services', pg_dons: 'Dons',
    pg_evenements: 'Evenements', pg_ressources: 'Ressources', pg_contact: 'Contact', pg_cours: 'N2-Cours',
    pg_mariages: 'N2-Mariages', pg_funerailles: 'N2-Funerailles', pg_aide: 'N2-AideAlimentaire',
    pg_femmes: 'N2-EspaceFemmes', pg_khutba: 'N2-Khutba', pg_rappel: 'N3-Rappel', pg_campagne: 'N3-Campagne',
    pg_calendrier: 'N3-Calendrier', pg_inscription: 'N3-Inscription', pg_dua: 'N3-Dua' };
  // Couleurs du site ; contrastes texte / fond : blanc sur vert 9,6:1, encre sur or 6,9:1, blanc sur rouge 6,5:1.
  var TONES = {
    info: { bg: '#0B0F1A', fg: '#FFFFFF', label: 'Information' },
    attention: { bg: '#D9B46C', fg: '#141B2C', label: 'Attention' },
    urgent: { bg: '#B3261E', fg: '#FFFFFF', label: 'Urgent' }
  };
  var ICON = { info: '<circle cx="12" cy="12" r="10"></circle><path d="M12 16v-4"></path><path d="M12 8h.01"></path>',
    alert: '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"></path><path d="M12 9v4"></path><path d="M12 17h.01"></path>' };
  var banner = null;
  function today() {
    try {
      var p = {};
      new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Moncton', year: 'numeric', month: '2-digit', day: '2-digit' })
        .formatToParts(new Date()).forEach(function (x) { p[x.type] = x.value; });
      if (p.year && p.month && p.day) return p.year + '-' + p.month + '-' + p.day;
    } catch (e) {}
    var d = new Date();
    return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
  }
  function build(a) {
    var t = TONES[a.tone] || TONES.attention;
    var el = document.createElement('div');
    el.id = 'ascil-alert';
    el.setAttribute('role', 'region');
    el.setAttribute('aria-label', 'Information importante');
    el.style.cssText = 'position:relative;z-index:60;background:' + t.bg + ';color:' + t.fg +
      ';font:600 15px/1.45 "Jost",system-ui,sans-serif;padding:10px 16px';
    var row = document.createElement('div');
    row.style.cssText = 'max-width:1180px;margin:0 auto;display:flex;align-items:center;justify-content:center;gap:10px;flex-wrap:wrap;text-align:center';
    var svg = '<svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" ' +
      'stroke-linecap="round" stroke-linejoin="round" style="flex:none">' + (a.tone === 'info' ? ICON.info : ICON.alert) + '</svg>';
    row.innerHTML = svg;
    var msg = document.createElement('p');
    msg.style.cssText = 'margin:0;min-width:0;overflow-wrap:anywhere';
    var sr = document.createElement('span');
    sr.textContent = t.label + ' : ';
    sr.style.cssText = 'position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap';
    msg.appendChild(sr);
    msg.appendChild(document.createTextNode(a.message));
    row.appendChild(msg);
    var href = a.link && a.link.type === 'page' && FILES[a.link.page] ? FILES[a.link.page] + '.dc.html'
      : a.link && a.link.type === 'custom' && /^[a-z0-9-]+$/.test(a.link.slug || '') ? '/p/' + a.link.slug
      : a.link && a.link.type === 'url' ? a.link.url : '';
    if (href) {
      var link = document.createElement('a');
      link.href = href;
      link.textContent = 'En savoir plus';
      link.style.cssText = 'color:inherit;text-decoration:underline;text-underline-offset:3px;display:inline-flex;align-items:center;min-height:24px;padding:2px 4px';
      if (a.link.type === 'url') { link.target = '_blank'; link.rel = 'noopener'; }
      row.appendChild(link);
    }
    el.appendChild(row);
    return el;
  }
  function place() {
    if (!banner || !document.body) return;
    if (document.body.firstChild !== banner) document.body.insertBefore(banner, document.body.firstChild);
  }
  fetch('/api/settings/alert', { cache: 'no-store' })
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (d) {
      if (!d || !d.ok) return;
      var a = d.settings, now = today();
      if (!a.on || !a.message) return;
      if (a.from && now < a.from) return;
      if (a.to && now > a.to) return;
      banner = build(a);
      place();
      new MutationObserver(place).observe(document.body, { childList: true });
    }, function () {});
})();
</script>
"""

LANG_SCRIPT = r"""<script id="ascil-languages">
(function () {
  var off = {};
  function hide(el) { if (el && el.style.display !== 'none') el.style.display = 'none'; }
  function apply() {
    // Liste déroulante (PC) : « العربية », « English » ; pastilles du menu mobile : « العربية », « EN ».
    document.querySelectorAll('li[role="option"]').forEach(function (li) {
      var t = li.textContent.trim();
      if ((off.ar && t === 'العربية') || (off.en && t === 'English')) hide(li);
    });
    document.querySelectorAll('span.pill').forEach(function (p) {
      var t = p.textContent.trim();
      if ((off.ar && t === 'العربية') || (off.en && t === 'EN')) hide(p);
      // Plus aucune autre langue : on retire toute la rangée de pastilles.
      if (off.ar && off.en && t === 'FR' && p.parentElement) hide(p.parentElement);
    });
    if (off.ar && off.en) document.querySelectorAll('.lang-desk').forEach(hide);
  }
  fetch('/api/settings/languages', { cache: 'no-store' })
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (d) {
      if (!d || !d.ok) return;
      off = { ar: d.settings.ar === false, en: d.settings.en === false };
      if (!off.ar && !off.en) return;
      apply();
      new MutationObserver(apply).observe(document.documentElement, { childList: true, subtree: true });
    }, function () {});
})();
</script>
"""

SEASON_SCRIPT = r"""<script id="ascil-season">
(function () {
  var TEXT = {
    ramadan: { title: 'Ramadan Moubarak', ar: 'رمضان مبارك' },
    aid_fitr: { title: 'Aïd al-Fitr Moubarak', ar: 'عيد فطر مبارك',
      sub: 'Bonne fête à toutes et à tous. L’heure de la prière de l’Aïd est indiquée dans les horaires.' },
    aid_adha: { title: 'Aïd al-Adha Moubarak', ar: 'عيد أضحى مبارك',
      sub: 'Bonne fête à toutes et à tous. L’heure de la prière de l’Aïd est indiquée dans les horaires.' }
  };
  var band = null;
  function today() {
    try {
      var p = {};
      new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Moncton', year: 'numeric', month: '2-digit', day: '2-digit' })
        .formatToParts(new Date()).forEach(function (x) { p[x.type] = x.value; });
      if (p.year && p.month && p.day) return p.year + '-' + p.month + '-' + p.day;
    } catch (e) {}
    var d = new Date();
    return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
  }
  function active(s) {
    if (!s || s.mode === 'normal' || !TEXT[s.mode]) return false;
    if (!s.auto) return true;
    var now = today();
    return !!s.from && !!s.to && now >= s.from && now <= s.to;
  }
  function build(mode, priere) {
    var t = TEXT[mode];
    var el = document.createElement('section');
    el.id = 'ascil-season';
    el.setAttribute('aria-label', t.title);
    // Fond vert du site : texte crème 8,6:1 ; titre arabe en or, en grand (≥ 18,7 px gras) : 4,3:1.
    el.style.cssText = 'background:#0B0F1A;color:#F4EBD6;border-radius:20px;padding:20px 24px;margin:16px auto;' +
      'max-width:1180px;box-sizing:border-box;display:flex;flex-wrap:wrap;align-items:center;gap:12px 24px;' +
      'font-family:"Jost",system-ui,sans-serif';
    var head = document.createElement('div');
    head.style.cssText = 'flex:1 1 260px;min-width:0';
    var h = document.createElement('p');
    h.style.cssText = 'margin:0;font-size:24px;font-weight:800;color:#FFFFFF;line-height:1.2';
    h.textContent = t.title;
    var ar = document.createElement('p');
    ar.lang = 'ar'; ar.dir = 'rtl';
    ar.style.cssText = 'margin:4px 0 0;font-size:22px;font-weight:700;color:#D9B46C;text-align:start';
    ar.textContent = t.ar;
    head.appendChild(h); head.appendChild(ar);
    var info = document.createElement('p');
    info.style.cssText = 'margin:0;flex:1 1 260px;min-width:0;font-size:16px;line-height:1.5';
    if (mode === 'ramadan') {
      var parts = [];
      if (priere && priere.fajr && priere.fajr !== '—') parts.push('Suhoor jusqu’à ' + priere.fajr);
      var magh = priere && (priere.maghrib || priere.maghreb);
      if (magh && magh !== '—') parts.push('Iftar à ' + magh);
      info.textContent = parts.length ? parts.join(' · ') + ' (aujourd’hui).' : 'Les heures de Suhoor et d’Iftar sont indiquées dans les horaires du mois.';
    } else {
      info.textContent = t.sub;
    }
    var link = document.createElement('a');
    link.href = 'Horaires.dc.html';
    link.textContent = 'Horaires du mois';
    link.style.cssText = 'display:inline-flex;align-items:center;min-height:44px;padding:0 18px;border-radius:999px;' +
      'background:#D9B46C;color:#141B2C;font-weight:700;text-decoration:none';
    el.appendChild(head); el.appendChild(info); el.appendChild(link);
    return el;
  }
  function place() {
    var main = document.querySelector('main');
    if (!band || !main) return;
    if (main.firstElementChild !== band) main.insertBefore(band, main.firstChild);
  }
  var get = function (u) { return fetch(u, { cache: 'no-store' }).then(function (r) { return r.ok ? r.json() : null; }); };
  get('/api/settings/season').then(function (d) {
    if (!d || !d.ok || !active(d.settings)) return;
    var mode = d.settings.mode;
    (mode === 'ramadan' ? get('/api/prayer-times/today') : Promise.resolve(null)).then(function (pt) {
      var priere = pt && pt.ok && pt.prayers ? pt.prayers : null;
      band = build(mode, priere);
      place();
      new MutationObserver(place).observe(document.documentElement, { childList: true, subtree: true });
    }, function () {});
  }, function () {});
})();
</script>
"""

HOME_PAGES = {'Main.dc.html', 'index.html', 'M-Accueil.dc.html', 'T-Accueil.dc.html'}


def wire_public():
    n = 0
    for path in sorted(ROOT.glob('*.dc.html')) + [ROOT / 'index.html']:
        if path.name.startswith('SA-'):
            continue
        s, i, j, tpl = load(path)
        tpl = re.sub(r'<script id="ascil-(?:pages-sync|alert-banner|languages|season)">.*?</script>\s*', '', tpl, flags=re.S)
        k = tpl.rindex('</body>')
        extra = SEASON_SCRIPT if path.name in HOME_PAGES else ''
        tpl = tpl[:k] + PUBLIC_SCRIPT + ALERT_SCRIPT + LANG_SCRIPT + extra + tpl[k:]
        save(path, s, i, j, tpl)
        n += 1
    print('pages publiques reliées :', n)


if __name__ == '__main__':
    wire_site_panel()
    wire_public()
