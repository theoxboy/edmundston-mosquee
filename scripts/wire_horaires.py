"""Branche le panneau « Horaires → Horaires du mois » (SA-Horaires.dc.html, étape H3).

Fonctionnalités branchées dans #sp-0 (« Horaires du mois ») :
1. Choix du mois (mois courant en fuseau America/Moncton + les 2 mois suivants).
2. Tableau éditable du mois (tous les jours du mois), lu et enregistré via l'API H2
   (GET / PUT /api/admin/prayer-times/:month).
3. « Copier une heure sur tout le mois » (choix de la prière, de l'heure, et de la portée :
   tous les jours, cases vides seulement, ou vendredis seulement + bouton pour vider la colonne).
4. « Coller depuis Excel » (collage de colonnes copiées depuis Excel / Google Sheets, ou collage
   direct dans les cellules du tableau — aucun import ni téléversement de fichier).
5. Cartes de réglages reliées à GET / PUT /api/admin/settings/horaires :
   - Tableau du mois : filtre « Vendredis » (mois.vendredis)
   - Bloc « Aujourd'hui » (aujourdhui : on, compte, hijri, lienRappel, lienKhutba)
   - Prière du vendredi (vendredi : on, avance, conseil) + Heure de Jumu'a lue et écrite
     directement dans les vendredis du tableau mensuel (source unique = prayer_times)
   - Ramadan (ramadan : on, suhoor, iftar, tarawih, tarawihHeure) + dates du Ramadan lues
     depuis « Site entier → Mode du site » (GET /api/admin/settings/season, source unique)
   - Prières de l'Aïd (aid : on, lieu, itineraire, fitrDate, fitrHeure, adhaDate, adhaHeure)
   - Qibla (qibla : on, degres, repere)
6. Interrupteur « Page publiée » relié à GET / PUT /api/admin/settings/pages (pg_horaires).

À relancer après scripts/install_superadmin.py, suivi de scripts/fix_inputs.py. Idempotent.
"""
import json, pathlib, re

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


SP0_HTML = (
    '<div id="sp-0" class="sp">'
    '<div class="sp-h">'
    '<div style="flex:1;min-width:220px"><p class="eyebrow">Page</p>'
    '<h2 class="serif" style="margin:4px 0 0;font-size:26px;color:#0E4D3C;font-weight:700">Horaires du mois</h2>'
    '<p class="dsc" style="margin-top:4px">Les heures du jour sur l’accueil viennent de ce tableau.</p></div>'
    '<div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap">'
    '<div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">'
    '<span class="tag" style="background:{{pub.pub_horaires.bg}};color:{{pub.pub_horaires.fg}}">{{pub.pub_horaires.t}}</span>'
    '<span style="font-size:13px;font-weight:600;color:#4F5E57">Page publiée</span>'
    '<button type="button" class="sw" role="switch" aria-label="Publier la page Horaires du mois" aria-checked="{{s.pub_horaires.c}}" sc-camel-on-click="{{s.pub_horaires.t}}"></button>'
    '</div>'
    '<a class="btn btn-line" href="Horaires.dc.html" style="min-height:40px">'
    '<svg aria-hidden="true" width="16" height="16" sc-camel-view-box="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z"></path><circle cx="12" cy="12" r="3"></circle></svg>'
    'Voir la page</a></div></div>'

    # 1. Tableau du mois
    '<section class="card" aria-label="Tableau du mois">'
    '<div class="card-h"><span class="num" aria-hidden="true">1</span>'
    '<div><h3 class="ttl">Tableau du mois</h3>'
    '<p class="dsc">Une ligne par jour. Pour le jour courant, une case vide reprend l’heure par défaut de l’Accueil, sinon « — ».</p></div></div>'
    '<div class="card-b">'
    '<div class="g2">'
    '<div class="fld"><label class="lbl" for="f1">Mois affiché</label>'
    '<sc-raw-select class="in" id="f1"><option>Chargement…</option></sc-raw-select>'
    '<p class="hint">Mois en cours et les 2 mois suivants.</p></div>'
    '<div class="fld"><span class="lbl">État du tableau</span>'
    '<div id="h-month-status" style="display:flex;align-items:center;min-height:44px;padding:8px 12px;border:1px solid #E4D9C0;border-radius:10px;background:#FBF8F1;font-size:13px;color:#4F5E57">Chargement du mois…</div>'
    '<p class="hint" id="h-defaults-hint">Repli Accueil du jour : Fajr 06:30 · Jumu’a 12:30 · Icha 19:00.</p></div>'
    '</div>'
    '<div id="h-month-table-wrap" style="overflow-x:auto;max-height:540px;overflow-y:auto;border:1px solid #E4D9C0;border-radius:12px;background:#fff"></div>'
    '<div class="g2">'
    '<button type="button" class="btn btn-line" id="btn-h-copy" style="align-self:flex-start">Copier une heure sur tout le mois</button>'
    '<button type="button" class="btn btn-line" id="btn-h-paste" style="align-self:flex-start">Coller depuis Excel</button>'
    '</div>'

    # Panneau repliable : Copier une heure sur tout le mois
    '<div id="h-copy-panel" style="display:none;border:1px solid #E4D9C0;border-radius:12px;padding:14px;background:#FBF8F1;flex-direction:column;gap:12px">'
    '<div style="font-weight:700;color:#0E4D3C;font-size:14px">Copier une heure sur tout le mois</div>'
    '<div class="g3">'
    '<div class="fld"><label class="lbl" for="h-copy-col">Colonne</label>'
    '<sc-raw-select class="in" id="h-copy-col">'
    '<option value="fajr">Fajr</option>'
    '<option value="lever">Lever</option>'
    '<option value="dohr">Dohr</option>'
    '<option value="jumuha">Jumu’a (vendredis)</option>'
    '<option value="asr">Asr</option>'
    '<option value="maghreb">Maghreb</option>'
    '<option value="isha">Icha</option>'
    '</sc-raw-select></div>'
    '<div class="fld"><label class="lbl" for="h-copy-time">Heure (HH:MM)</label>'
    '<input class="in tnum" id="h-copy-time" type="time" value="06:30"></div>'
    '<div class="fld"><label class="lbl" for="h-copy-scope">Jours à remplir</label>'
    '<sc-raw-select class="in" id="h-copy-scope">'
    '<option value="all">Tous les jours du mois</option>'
    '<option value="empty">Seulement les cases vides</option>'
    '<option value="fridays">Les vendredis seulement</option>'
    '</sc-raw-select></div>'
    '</div>'
    '<div style="display:flex;gap:10px;flex-wrap:wrap">'
    '<button type="button" class="btn btn-gold" id="btn-h-copy-apply" style="min-height:38px">Appliquer au mois</button>'
    '<button type="button" class="btn btn-line" id="btn-h-copy-clear" style="min-height:38px">Vider cette colonne</button>'
    '<button type="button" class="btn btn-line" id="btn-h-copy-close" style="min-height:38px">Fermer</button>'
    '</div>'
    '</div>'

    # Panneau repliable : Coller depuis Excel (sans upload de fichier)
    '<div id="h-paste-panel" style="display:none;border:1px solid #E4D9C0;border-radius:12px;padding:14px;background:#FBF8F1;flex-direction:column;gap:12px">'
    '<div style="font-weight:700;color:#0E4D3C;font-size:14px">Coller depuis Excel ou Google Sheets</div>'
    '<p class="hint" style="margin:0">Copiez vos lignes dans votre tableur (colonnes Fajr, Lever, Dohr, Asr, Maghreb, Icha — avec ou sans la colonne Jour en premier), ou une seule colonne d’heures, puis collez-les ci-dessous. Vous pouvez aussi coller directement dans une case du tableau.</p>'
    '<div class="fld"><label class="lbl" for="h-paste-col">Colonnes collées</label>'
    '<sc-raw-select class="in" id="h-paste-col">'
    '<option value="all">Tableau complet (Fajr, Lever, Dohr, Asr, Maghreb, Icha)</option>'
    '<option value="fajr">Colonne Fajr uniquement</option>'
    '<option value="lever">Colonne Lever uniquement</option>'
    '<option value="dohr">Colonne Dohr uniquement</option>'
    '<option value="jumuha">Colonne Jumu’a (vendredis uniquement)</option>'
    '<option value="asr">Colonne Asr uniquement</option>'
    '<option value="maghreb">Colonne Maghreb uniquement</option>'
    '<option value="isha">Colonne Icha uniquement</option>'
    '</sc-raw-select></div>'
    '<div class="fld"><label class="lbl" for="h-paste-area">Données copiées</label>'
    '<textarea class="in tnum" id="h-paste-area" rows="6" placeholder="06:15\t07:32\t12:10\t14:25\t16:40\t18:55&#10;06:16\t07:33\t12:10\t14:24\t16:39\t18:54" style="width:100%;font-family:monospace;font-size:13px;padding:10px"></textarea></div>'
    '<div style="display:flex;gap:10px;flex-wrap:wrap">'
    '<button type="button" class="btn btn-gold" id="btn-h-paste-apply" style="min-height:38px">Remplir le tableau</button>'
    '<button type="button" class="btn btn-line" id="btn-h-paste-close" style="min-height:38px">Fermer</button>'
    '</div>'
    '</div>'

    '<div><div class="row"><div><div style="font-weight:600;font-size:14px">Filtre « Vendredis »</div>'
    '<p class="hint">Bouton qui ne montre que les vendredis.</p></div>'
    '<button type="button" class="sw" role="switch" aria-label="Filtre « Vendredis »" aria-checked="{{s.h_vendredis.c}}" sc-camel-on-click="{{s.h_vendredis.t}}"></button></div></div>'
    '</div></section>'

    # 2. Bloc Aujourd'hui
    '<section class="card {{off.h_auj}}" aria-label="Bloc « Aujourd’hui »">'
    '<div class="card-h"><span class="num" aria-hidden="true">2</span><div><h3 class="ttl">Bloc « Aujourd’hui »</h3></div>'
    '<div class="hsw"><span aria-hidden="true">Afficher</span>'
    '<button type="button" class="sw" role="switch" aria-label="Afficher Bloc « Aujourd’hui »" aria-checked="{{s.h_auj.c}}" sc-camel-on-click="{{s.h_auj.t}}"></button></div></div>'
    '<div class="card-b"><div>'
    '<div class="row"><div><div style="font-weight:600;font-size:14px">Compte à rebours</div><p class="hint">Prochaine prière et temps restant.</p></div>'
    '<button type="button" class="sw" role="switch" aria-label="Compte à rebours" aria-checked="{{s.h_compte.c}}" sc-camel-on-click="{{s.h_compte.t}}"></button></div>'
    '<div class="row"><div><div style="font-weight:600;font-size:14px">Date hégirienne</div></div>'
    '<button type="button" class="sw" role="switch" aria-label="Date hégirienne" aria-checked="{{s.h_hijri.c}}" sc-camel-on-click="{{s.h_hijri.t}}"></button></div>'
    '<div class="row"><div><div style="font-weight:600;font-size:14px">Lien « Activer un rappel de prière »</div></div>'
    '<button type="button" class="sw" role="switch" aria-label="Lien « Activer un rappel de prière »" aria-checked="{{s.h_lienRappel.c}}" sc-camel-on-click="{{s.h_lienRappel.t}}"></button></div>'
    '<div class="row"><div><div style="font-weight:600;font-size:14px">Lien « Langue de la khutba »</div></div>'
    '<button type="button" class="sw" role="switch" aria-label="Lien « Langue de la khutba »" aria-checked="{{s.h_lienKhutba.c}}" sc-camel-on-click="{{s.h_lienKhutba.t}}"></button></div>'
    '</div></div></section>'

    # 3. Prière du vendredi
    '<section class="card {{off.h_jumua}}" aria-label="Prière du vendredi">'
    '<div class="card-h"><span class="num" aria-hidden="true">3</span><div><h3 class="ttl">Prière du vendredi</h3></div>'
    '<div class="hsw"><span aria-hidden="true">Afficher</span>'
    '<button type="button" class="sw" role="switch" aria-label="Afficher Prière du vendredi" aria-checked="{{s.h_jumua.c}}" sc-camel-on-click="{{s.h_jumua.t}}"></button></div></div>'
    '<div class="card-b"><div class="g2">'
    '<div class="fld"><label class="lbl" for="f3">Heure de Jumu’a</label>'
    '<input class="in tnum" id="f3" type="time" value="12:30">'
    '<p class="hint">Enregistrée dans les vendredis du tableau mensuel (source unique).</p></div>'
    '<div class="fld"><label class="lbl" for="f4">Arriver à l’avance (minutes)</label>'
    '<input class="in tnum" id="f4" type="number" min="0" max="120" value="15" inputmode="numeric"></div>'
    '</div><div>'
    '<div class="row"><div><div style="font-weight:600;font-size:14px">Conseil de stationnement</div>'
    '<p class="hint">« Le stationnement étant limité dans la rue. »</p></div>'
    '<button type="button" class="sw" role="switch" aria-label="Conseil de stationnement" aria-checked="{{s.h_conseil.c}}" sc-camel-on-click="{{s.h_conseil.t}}"></button></div>'
    '</div></div></section>'

    # 4. Ramadan
    '<section class="card {{off.h_ramadan}}" aria-label="Ramadan">'
    '<div class="card-h"><span class="num" aria-hidden="true">4</span>'
    '<div><h3 class="ttl">Ramadan</h3><p class="dsc">Affiché pendant le Ramadan. Les dates proviennent de Site entier → Mode du site.</p></div>'
    '<div class="hsw"><span aria-hidden="true">Afficher</span>'
    '<button type="button" class="sw" role="switch" aria-label="Afficher Ramadan" aria-checked="{{s.h_ramadan.c}}" sc-camel-on-click="{{s.h_ramadan.t}}"></button></div></div>'
    '<div class="card-b">'
    '<div class="g2">'
    '<div class="fld"><label class="lbl" for="f5">Premier jour (Mode du site)</label>'
    '<input class="in tnum" id="f5" type="date" value="" readonly disabled style="background:#F5EFE2;color:#4F5E57;cursor:not-allowed"></div>'
    '<div class="fld"><label class="lbl" for="f6">Dernier jour (Mode du site)</label>'
    '<input class="in tnum" id="f6" type="date" value="" readonly disabled style="background:#F5EFE2;color:#4F5E57;cursor:not-allowed"></div>'
    '</div>'
    '<p class="hint" style="margin:-4px 0 4px">Source unique des dates : <a href="SA-Site.dc.html" style="color:#0E4D3C;font-weight:600;text-decoration:underline">Site entier → Mode du site</a>.</p>'
    '<div>'
    '<div class="row"><div><div style="font-weight:600;font-size:14px">Colonne Suhoor</div></div>'
    '<button type="button" class="sw" role="switch" aria-label="Colonne Suhoor" aria-checked="{{s.h_suhoor.c}}" sc-camel-on-click="{{s.h_suhoor.t}}"></button></div>'
    '<div class="row"><div><div style="font-weight:600;font-size:14px">Colonne Iftar</div></div>'
    '<button type="button" class="sw" role="switch" aria-label="Colonne Iftar" aria-checked="{{s.h_iftar.c}}" sc-camel-on-click="{{s.h_iftar.t}}"></button></div>'
    '<div class="row"><div><div style="font-weight:600;font-size:14px">Heure des Tarawih</div></div>'
    '<button type="button" class="sw" role="switch" aria-label="Heure des Tarawih" aria-checked="{{s.h_tarawih.c}}" sc-camel-on-click="{{s.h_tarawih.t}}"></button></div>'
    '</div>'
    '<div class="fld" id="h-tarawih-wrap" style="max-width:260px">'
    '<label class="lbl" for="f-tarawih">Horaire des Tarawih</label>'
    '<input class="in tnum" id="f-tarawih" type="time" value="">'
    '<p class="hint">Affiché si « Heure des Tarawih » est activée.</p>'
    '</div>'
    '</div></section>'

    # 5. Prières de l'Aïd
    '<section class="card {{off.h_aid}}" aria-label="Prières de l’Aïd">'
    '<div class="card-h"><span class="num" aria-hidden="true">5</span><div><h3 class="ttl">Prières de l’Aïd</h3></div>'
    '<div class="hsw"><span aria-hidden="true">Afficher</span>'
    '<button type="button" class="sw" role="switch" aria-label="Afficher Prières de l’Aïd" aria-checked="{{s.h_aid.c}}" sc-camel-on-click="{{s.h_aid.t}}"></button></div></div>'
    '<div class="card-b">'
    '<div class="g2">'
    '<div class="fld"><label class="lbl" for="f7">Lieu</label><input class="in" id="f7" type="text" value="Salle louée — 15 rue Frontenac" maxlength="120"></div>'
    '<div class="fld"><label class="lbl" for="f8">Lien itinéraire</label><input class="in" id="f8" type="url" value="https://maps.google.com/?q=15+rue+Frontenac+Edmundston" maxlength="500"></div>'
    '</div>'
    '<div class="g2">'
    '<div class="fld"><label class="lbl" for="f9">Aïd al-Fitr — date</label><input class="in tnum" id="f9" type="date" value=""><p class="hint">Vide = « Selon l’annonce TCOM ».</p></div>'
    '<div class="fld"><label class="lbl" for="f10">Aïd al-Fitr — heure</label><input class="in tnum" id="f10" type="time" value=""></div>'
    '</div>'
    '<div class="g2">'
    '<div class="fld"><label class="lbl" for="f11">Aïd al-Adha — date</label><input class="in tnum" id="f11" type="date" value=""></div>'
    '<div class="fld"><label class="lbl" for="f12">Aïd al-Adha — heure</label><input class="in tnum" id="f12" type="time" value=""></div>'
    '</div>'
    '</div></section>'

    # 6. Qibla
    '<section class="card {{off.h_qibla}}" aria-label="Qibla">'
    '<div class="card-h"><span class="num" aria-hidden="true">6</span><div><h3 class="ttl">Qibla</h3><p class="dsc">Encadré avec la direction de la prière.</p></div>'
    '<div class="hsw"><span aria-hidden="true">Afficher</span>'
    '<button type="button" class="sw" role="switch" aria-label="Afficher Qibla" aria-checked="{{s.h_qibla.c}}" sc-camel-on-click="{{s.h_qibla.t}}"></button></div></div>'
    '<div class="card-b"><div class="g2">'
    '<div class="fld"><label class="lbl" for="f13">Direction (degrés)</label><input class="in" id="f13" type="text" value="61,6"></div>'
    '<div class="fld"><label class="lbl" for="f14">Repère sur place</label><input class="in" id="f14" type="text" value="" placeholder="Ex. Flèche au mur de la salle de prière" maxlength="160"></div>'
    '</div></div></section>'
    '</div>'
)


# Onglets « Langue de la khutba » (#sp-1, clé khutba) et « Rappel de prière » (#sp-2, clé rappel) : étape H6.
SP12_HTML = (
    '<div id="sp-1" class="sp">'
    '<div class="sp-h"><div style="flex:1;min-width:220px"><p class="eyebrow">Page</p>'
    '<h2 class="serif" style="margin:4px 0 0;font-size:26px;color:#0E4D3C;font-weight:700">Langue de la khutba</h2></div>'
    '<div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap"><div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">'
    '<span class="tag" style="background:{{pub.pub_khutba.bg}};color:{{pub.pub_khutba.fg}}">{{pub.pub_khutba.t}}</span>'
    '<span style="font-size:13px;font-weight:600;color:#4F5E57">Page publiée</span>'
    '<button type="button" class="sw" role="switch" aria-label="Publier la page Langue de la khutba" aria-checked="{{s.pub_khutba.c}}" sc-camel-on-click="{{s.pub_khutba.t}}"></button></div>'
    '<a class="btn btn-line" href="N2-Khutba.dc.html" style="min-height:40px"><svg aria-hidden="true" width="16" height="16" sc-camel-view-box="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z"></path><circle cx="12" cy="12" r="3"></circle></svg>Voir la page</a></div></div>'
    '<p class="warn">Le site montre les vendredis à venir, dans l’ordre des dates, avec l’heure de Jumu’a du tableau du mois. '
    'La page reste masquée tant que vous ne la publiez pas.</p>'
    '<section class="card" aria-label="Vendredis à venir"><div class="card-h"><span class="num" aria-hidden="true">1</span>'
    '<div><h3 class="ttl">Vendredis à venir</h3><p class="dsc">Une ligne par vendredi. Les vendredis passés ne sont plus affichés sur le site.</p></div></div>'
    '<div class="card-b"><div id="kh-list"><p class="hint">Chargement…</p></div>'
    '<div style="display:flex;gap:10px;flex-wrap:wrap;align-items:flex-end">'
    '<div class="fld" style="min-width:200px"><label class="lbl" for="kh-new-date">Date du vendredi à ajouter</label>'
    '<input class="in" id="kh-new-date" type="date"></div>'
    '<button type="button" class="btn btn-line" id="kh-add" style="min-height:44px">+ Ajouter un vendredi</button></div>'
    '<div class="g2"><div class="fld"><label class="lbl" for="f21">Nombre de vendredis affichés</label>'
    '<sc-raw-select class="in" id="f21"><option value="2">2</option><option value="4">4</option><option value="6">6</option><option value="8">8</option></sc-raw-select></div>'
    '<div class="fld"><label class="lbl" for="f22">Mode de traduction</label><sc-raw-select class="in" id="f22">'
    '<option>Résumé imprimé à l’entrée</option><option>Traduction orale</option><option>Écran</option></sc-raw-select></div></div>'
    '</div></section></div>'

    '<div id="sp-2" class="sp">'
    '<div class="sp-h"><div style="flex:1;min-width:220px"><p class="eyebrow">Petite app</p>'
    '<h2 class="serif" style="margin:4px 0 0;font-size:26px;color:#0E4D3C;font-weight:700">Rappel de prière</h2></div>'
    '<div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap"><div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">'
    '<span class="tag" style="background:{{pub.pub_rappel.bg}};color:{{pub.pub_rappel.fg}}">{{pub.pub_rappel.t}}</span>'
    '<span style="font-size:13px;font-weight:600;color:#4F5E57">Page publiée</span>'
    '<button type="button" class="sw" role="switch" aria-label="Publier la page Rappel de prière" aria-checked="{{s.pub_rappel.c}}" sc-camel-on-click="{{s.pub_rappel.t}}"></button></div>'
    '<a class="btn btn-line" href="N3-Rappel.dc.html" style="min-height:40px"><svg aria-hidden="true" width="16" height="16" sc-camel-view-box="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z"></path><circle cx="12" cy="12" r="3"></circle></svg>Voir la page</a></div></div>'
    '<p class="warn">Les rappels fonctionnent dans le navigateur des visiteurs, sans compte, tant que la page reste ouverte. '
    'Ils peuvent aussi les ajouter à leur calendrier (fichier .ics) pour être prévenus page fermée.</p>'
    '<section class="card" aria-label="Prières proposées"><div class="card-h"><span class="num" aria-hidden="true">1</span>'
    '<div><h3 class="ttl">Prières proposées</h3><p class="dsc">Les visiteurs choisissent parmi celles-ci. Les heures viennent du tableau du mois.</p></div></div>'
    '<div class="card-b"><div>'
    + ''.join(
        '<div class="row"><div><div style="font-weight:600;font-size:14px">%s</div>%s</div>'
        '<button type="button" class="sw" role="switch" aria-label="%s" aria-checked="{{s.%s.c}}" sc-camel-on-click="{{s.%s.t}}"></button></div>'
        % (n, '<p class="hint">Proposée seulement les jours où son heure est dans le tableau du mois.</p>' if hint else '', n, k, k)
        for n, k, hint in [('Fajr', 'r_fajr', False), ('Dohr', 'r_dohr', True), ('Jumu’a', 'r_jumua', False),
                           ('Asr', 'r_asr', True), ('Maghreb', 'r_maghreb', True), ('Icha', 'r_icha', False)])
    + '</div></div></section>'
    '<section class="card" aria-label="Délais de rappel"><div class="card-h"><span class="num" aria-hidden="true">2</span>'
    '<div><h3 class="ttl">Délais de rappel</h3><p class="dsc">« À l’heure » est toujours proposé en plus.</p></div></div>'
    '<div class="card-b"><div class="fld"><span class="lbl" id="f23">Délais proposés</span>'
    '<div class="seg" id="rp-delais" role="group" aria-labelledby="f23" style="align-self:flex-start;flex-wrap:wrap">'
    '<button type="button" data-rp-delai="5" aria-pressed="true">5 min</button><button type="button" data-rp-delai="10" aria-pressed="true">10 min</button>'
    '<button type="button" data-rp-delai="15" aria-pressed="true">15 min</button><button type="button" data-rp-delai="30" aria-pressed="true">30 min</button>'
    '<button type="button" data-rp-delai="60" aria-pressed="true">1 h</button></div></div>'
    '<div class="g2"><div class="fld"><label class="lbl" for="f24">Délai coché par défaut</label><sc-raw-select class="in" id="f24">'
    '<option value="5">5 min</option><option value="10">10 min</option><option value="15">15 min</option><option value="30">30 min</option><option value="60">1 h</option>'
    '</sc-raw-select></div>'
    '<div class="fld"><label class="lbl" for="f25">Titre de la notification</label><input class="in" id="f25" type="text" maxlength="80">'
    '<p class="hint">{délai} est remplacé par le délai choisi, par exemple « 15 min ».</p></div></div>'
    '<div><div class="row"><div><div style="font-weight:600;font-size:14px">Option « Son »</div></div>'
    '<button type="button" class="sw" role="switch" aria-label="Option « Son »" aria-checked="{{s.r_son.c}}" sc-camel-on-click="{{s.r_son.t}}"></button></div>'
    '<div class="row"><div><div style="font-weight:600;font-size:14px">Option « Vibration »</div></div>'
    '<button type="button" class="sw" role="switch" aria-label="Option « Vibration »" aria-checked="{{s.r_vib.c}}" sc-camel-on-click="{{s.r_vib.t}}"></button></div></div>'
    '</div></section></div>'
)


COMPONENT_SCRIPT = r"""class Component extends DCLogic {
  constructor(props) {
    super(props);
    this.base = {"pub_horaires": true, "h_vendredis": true, "h_pdf": true, "h_auj": true, "h_compte": true, "h_hijri": true, "h_lienRappel": true, "h_lienKhutba": true, "h_jumua": true, "h_conseil": true, "h_ramadan": true, "h_suhoor": true, "h_iftar": true, "h_tarawih": false, "h_aid": true, "h_qibla": true, "pub_khutba": false, "kh_0": true, "kh_1": true, "pub_rappel": false, "r_fajr": true, "r_dohr": false, "r_jumua": true, "r_asr": false, "r_maghreb": false, "r_icha": true, "r_son": true, "r_vib": true};
    this.pubKeys = ["pub_horaires", "pub_khutba", "pub_rappel"];
    this.state = { on: Object.assign({}, this.base), extDirty: false, toast: '' };
    window.__saHoraires = this;
  }
  componentDidMount() {
    window.dispatchEvent(new Event('sa-horaires-ready'));
  }
  componentWillUnmount() {
    clearTimeout(this.tt);
    if (window.__saHoraires === this) window.__saHoraires = null;
  }
  setSwitches(sw, asBase) {
    const next = Object.assign({}, this.state.on, sw);
    if (asBase) this.base = Object.assign({}, this.base, sw);
    this.setState({ on: next });
  }
  setExtDirty(flag) {
    if (!!this.state.extDirty !== !!flag) this.setState({ extDirty: !!flag });
    else this.forceUpdate();
  }
  commitBase() {
    this.base = Object.assign({}, this.state.on);
    this.setState({ extDirty: false });
  }
  revertBase() {
    this.setState({ on: Object.assign({}, this.base), extDirty: false });
  }
  flash(m) {
    this.setState({ toast: m });
    clearTimeout(this.tt);
    this.tt = setTimeout(() => this.setState({ toast: '' }), 3200);
  }
  renderVals() {
    const on = this.state.on;
    const swDirty = Object.keys(on).some((k) => on[k] !== this.base[k]);
    const dirty = swDirty || !!this.state.extDirty;
    const s = {}, off = {}, op = {}, pub = {};
    Object.keys(on).forEach((k) => {
      s[k] = {
        c: String(!!on[k]),
        t: () => {
          const next = Object.assign({}, this.state.on, { [k]: !this.state.on[k] });
          this.setState({ on: next }, () => {
            if (window.__saHorairesOnSwitch) window.__saHorairesOnSwitch(k, next[k]);
          });
        }
      };
      off[k] = on[k] ? '' : 'off';
      op[k] = on[k] ? 1 : 0.5;
    });
    this.pubKeys.forEach((k) => { pub[k] = on[k] ? { t: 'Publiée', bg: '#DCEFE6', fg: '#0E4D3C' } : { t: 'Masquée du site', bg: '#F3EAD8', fg: '#7A5A1E' }; });
    return {
      s, off, op, pub,
      clean: !dirty, dot: dirty ? '#C49A4A' : '#7FB89F', statusTxt: dirty ? 'Changements non enregistrés' : 'Tout est enregistré',
      save: () => { if (window.__saHorairesSave) window.__saHorairesSave(); },
      undo: () => { if (window.__saHorairesUndo) window.__saHorairesUndo(); },
      toast: this.state.toast
    };
  }
}"""


HORAIRES_SYNC_SCRIPT = r'''<script id="sa-horaires-sync">
(function () {
  var MONTHS_FR = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin', 'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'];
  var DAYS_FR = ['dim.', 'lun.', 'mar.', 'mer.', 'jeu.', 'ven.', 'sam.'];
  var COLS = ['fajr', 'lever', 'dohr', 'asr', 'maghreb', 'isha'];
  var COL_LABELS = { fajr: 'Fajr', lever: 'Lever', dohr: 'Dohr', asr: 'Asr', maghreb: 'Maghreb', isha: 'Icha', jumuha: 'Jumu’a' };
  var HHMM_RE = /^([01]\d|2[0-3]):[0-5]\d$/;

  var allowedMonths = [];
  var currentMonth = '';
  var monthBase = {};    // ym -> JSON string of days array
  var monthDraft = {};   // ym -> array of { date, fajr, lever, dohr, asr, maghreb, isha, jumuha, source }
  var homeDefaults = { fajr: '06:30', lever: '', dohr: '', asr: '', maghreb: '', isha: '19:00', jumuha: '12:30' };
  var settingsBase = null;
  var pagesBase = null;
  var seasonDates = { from: '', to: '' };
  var saving = false;

  function comp() { return window.__saHoraires; }
  function flash(msg) { var c = comp(); if (c) c.flash(msg); }
  function getEl(id) { return document.getElementById(id); }
  // Valeurs réelles des champs, gardées ici : un champ redessiné par la page reprend la valeur de la
  // maquette (ou se vide) ; on la remet dès qu'il réapparaît, et on la lit même s'il n'est pas affiché.
  var cur = {};
  function setVal(id, v) { cur[id] = v == null ? '' : String(v); var e = getEl(id); if (e) { e.value = cur[id]; e.setAttribute('data-sa-v', '1'); } }
  function getVal(id) {
    var e = getEl(id);
    if (e && (e.getAttribute('data-sa-v') === '1' || !Object.prototype.hasOwnProperty.call(cur, id))) return String(e.value).trim();
    return Object.prototype.hasOwnProperty.call(cur, id) ? String(cur[id]).trim() : '';
  }
  ['input', 'change'].forEach(function (ev) {
    document.addEventListener(ev, function (e) { var t = e.target; if (t && t.id && Object.prototype.hasOwnProperty.call(cur, t.id)) { cur[t.id] = t.value; t.setAttribute('data-sa-v', '1'); } }, true);
  });
  var refillT = null;
  new MutationObserver(function () {
    clearTimeout(refillT);
    refillT = setTimeout(function () {
      Object.keys(cur).forEach(function (id) { var e = getEl(id); if (e && e.getAttribute('data-sa-v') !== '1') { e.value = cur[id]; e.setAttribute('data-sa-v', '1'); } });
    }, 0);
  }).observe(document.documentElement, { childList: true, subtree: true });

  function normalizeTime(raw) {
    if (raw == null) return '';
    var t = String(raw).trim();
    if (!t || t === '—' || t === '-' || t === '–') return '';
    if (HHMM_RE.test(t)) return t;
    var m = /^(\d{1,2})\s*[:hH]\s*([0-5]\d)(?::[0-5]\d)?$/.exec(t);
    if (!m) return null;
    var hh = Number(m[1]);
    if (hh < 0 || hh > 23) return null;
    return (hh < 10 ? '0' + hh : '' + hh) + ':' + m[2];
  }

  function computeAllowedMonths() {
    var nowStr = '';
    try {
      nowStr = new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Moncton', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date());
    } catch (e) {
      nowStr = new Date().toISOString().slice(0, 10);
    }
    var y = parseInt(nowStr.slice(0, 4), 10);
    var m = parseInt(nowStr.slice(5, 7), 10);
    var list = [];
    for (var i = 0; i < 3; i++) {
      var yy = y + Math.floor((m - 1 + i) / 12);
      var mm = ((m - 1 + i) % 12) + 1;
      var ym = yy + '-' + (mm < 10 ? '0' + mm : '' + mm);
      var label = MONTHS_FR[mm - 1] + ' ' + yy;
      list.push({ ym: ym, label: label });
    }
    return list;
  }

  function dayOfWeek(dateStr) {
    var parts = dateStr.split('-');
    var dt = new Date(Date.UTC(parseInt(parts[0], 10), parseInt(parts[1], 10) - 1, parseInt(parts[2], 10)));
    return dt.getUTCDay();
  }

  function isFriday(dateStr) {
    return dayOfWeek(dateStr) === 5;
  }

  function dayLabel(dateStr) {
    var dow = dayOfWeek(dateStr);
    var dNum = parseInt(dateStr.slice(8, 10), 10);
    return DAYS_FR[dow] + ' ' + dNum;
  }

  function emptyMonthDays(ym) {
    var parts = ym.split('-');
    var y = parseInt(parts[0], 10), m = parseInt(parts[1], 10);
    var total = new Date(Date.UTC(y, m, 0)).getUTCDate();
    var out = [];
    for (var d = 1; d <= total; d++) {
      var date = ym + '-' + (d < 10 ? '0' + d : '' + d);
      out.push({ date: date, fajr: '', lever: '', dohr: '', asr: '', maghreb: '', isha: '', jumuha: '', source: '' });
    }
    return out;
  }

  function syncJumuaInputFromMonth(ym) {
    var days = monthDraft[ym] || [];
    var found = '';
    for (var i = 0; i < days.length; i++) {
      if (isFriday(days[i].date)) {
        var v = days[i].jumuha || days[i].dohr;
        if (v) { found = v; break; }
      }
    }
    if (!found) found = homeDefaults.jumuha || '12:30';
    setVal('f3', found);
  }

  function applyJumuaInputToMonth(ym, timeVal) {
    var clean = normalizeTime(timeVal);
    if (clean === null) return;
    var days = monthDraft[ym];
    if (!days) return;
    for (var i = 0; i < days.length; i++) {
      if (isFriday(days[i].date)) {
        days[i].jumuha = clean;
        days[i].dohr = clean;
        var inp = document.querySelector('#h-month-table-wrap input[data-date="' + days[i].date + '"][data-col="dohr"]');
        if (inp) inp.value = clean;
      }
    }
    updateMonthStatus(ym);
    checkDirty();
  }

  function updateMonthStatus(ym) {
    var days = monthDraft[ym] || [];
    var filledDays = 0;
    for (var i = 0; i < days.length; i++) {
      var r = days[i];
      if (r.fajr || r.lever || r.dohr || r.asr || r.maghreb || r.isha || r.jumuha) filledDays++;
    }
    var st = getEl('h-month-status');
    if (st) {
      st.textContent = filledDays + ' jour' + (filledDays > 1 ? 's' : '') + ' renseigné' + (filledDays > 1 ? 's' : '') + ' sur ' + days.length;
    }
    var hint = getEl('h-defaults-hint');
    if (hint && homeDefaults) {
      hint.textContent = 'Repli Accueil du jour : Fajr ' + (homeDefaults.fajr || '06:30') +
        ' · Jumu’a ' + (homeDefaults.jumuha || '12:30') +
        ' · Icha ' + (homeDefaults.isha || '19:00') + '.';
    }
  }

  function renderMonthTable(ym) {
    var wrap = getEl('h-month-table-wrap');
    if (!wrap) return;
    var days = monthDraft[ym] || emptyMonthDays(ym);
    var mLabel = (allowedMonths.find(function (x) { return x.ym === ym; }) || { label: ym }).label;

    var html = [
      '<table style="border-collapse:collapse;width:100%" aria-label="Horaires de ' + mLabel + '">',
      '<thead style="position:sticky;top:0;background:#FBF8F1;z-index:2;border-bottom:1.5px solid #E4D9C0">',
      '<tr>',
      '<th scope="col" style="text-align:left;padding:8px 8px;font-size:13px;color:#4F5E57;font-weight:700;white-space:nowrap">Jour</th>',
      '<th scope="col" style="text-align:left;padding:8px 6px;font-size:13px;color:#4F5E57;font-weight:700;white-space:nowrap">Fajr</th>',
      '<th scope="col" style="text-align:left;padding:8px 6px;font-size:13px;color:#4F5E57;font-weight:700;white-space:nowrap">Lever</th>',
      '<th scope="col" style="text-align:left;padding:8px 6px;font-size:13px;color:#4F5E57;font-weight:700;white-space:nowrap">Dohr / Jumu’a</th>',
      '<th scope="col" style="text-align:left;padding:8px 6px;font-size:13px;color:#4F5E57;font-weight:700;white-space:nowrap">Asr</th>',
      '<th scope="col" style="text-align:left;padding:8px 6px;font-size:13px;color:#4F5E57;font-weight:700;white-space:nowrap">Maghreb</th>',
      '<th scope="col" style="text-align:left;padding:8px 6px;font-size:13px;color:#4F5E57;font-weight:700;white-space:nowrap">Icha</th>',
      '</tr></thead><tbody>'
    ];

    for (var i = 0; i < days.length; i++) {
      var r = days[i];
      var fri = isFriday(r.date);
      var lbl = dayLabel(r.date);
      var rowBg = fri ? 'background:#FDF6E4;' : '';
      html.push('<tr style="border-top:1px solid #F3EAD8;' + rowBg + '">');
      html.push(
        '<th scope="row" style="text-align:left;padding:4px 8px;font-weight:' + (fri ? '700' : '600') + ';color:' + (fri ? '#0E4D3C' : '#1E2B26') + ';white-space:nowrap;font-size:13px">' +
        lbl +
        (fri ? ' <span style="display:inline-block;margin-left:4px;padding:1px 6px;border-radius:99px;background:#F3E3B8;color:#7A5A1E;font-size:10px;font-weight:700">VEN.</span>' : '') +
        '</th>'
      );
      for (var c = 0; c < COLS.length; c++) {
        var col = COLS[c];
        var val = col === 'dohr' && fri ? (r.jumuha || r.dohr || '') : (r[col] || '');
        var ph = col === 'fajr' ? (homeDefaults.fajr || '06:30')
          : col === 'isha' ? (homeDefaults.isha || '19:00')
          : (col === 'dohr' && fri) ? (homeDefaults.jumuha || '12:30')
          : '—';
        html.push(
          '<td style="padding:4px 6px">' +
          '<input class="in tnum h-cell" type="text" inputmode="numeric" maxlength="5" ' +
          'aria-label="' + lbl + ' ' + (col === 'dohr' && fri ? 'Jumu’a' : COL_LABELS[col]) + '" ' +
          'data-date="' + r.date + '" data-row="' + i + '" data-col="' + col + '" ' +
          'placeholder="' + ph + '" value="' + val.replace(/"/g, '&quot;') + '" ' +
          'style="min-height:36px;padding:5px 8px;min-width:76px;max-width:96px;font-size:13px">' +
          '</td>'
        );
      }
      html.push('</tr>');
    }

    html.push('</tbody></table>');
    wrap.innerHTML = html.join('');
    updateMonthStatus(ym);
  }

  function loadMonth(ym, forceReload) {
    currentMonth = ym;
    var sel = getEl('f1');
    if (sel && sel.value !== ym) sel.value = ym;

    if (!forceReload && monthDraft[ym]) {
      renderMonthTable(ym);
      syncJumuaInputFromMonth(ym);
      return Promise.resolve();
    }

    var st = getEl('h-month-status');
    if (st) st.textContent = 'Chargement de ' + ym + '…';

    return fetch('/api/admin/prayer-times/' + encodeURIComponent(ym), { credentials: 'same-origin' })
      .then(function (r) { return r.json().catch(function () { return { ok: false }; }); })
      .then(function (d) {
        if (!d || !d.ok) {
          var fallback = emptyMonthDays(ym);
          monthBase[ym] = JSON.stringify(fallback);
          monthDraft[ym] = JSON.parse(monthBase[ym]);
          renderMonthTable(ym);
          flash((d && d.message) || 'Impossible de charger les horaires de ce mois.');
          return;
        }
        if (d.defaults) homeDefaults = d.defaults;
        var normalized = (d.days || emptyMonthDays(ym)).map(function (r) {
          var fri = isFriday(r.date);
          var dohrVal = r.dohr || (fri ? r.jumuha : '') || '';
          var jumuhaVal = r.jumuha || (fri ? r.dohr : '') || '';
          return {
            date: r.date,
            fajr: r.fajr || '',
            lever: r.lever || '',
            dohr: dohrVal,
            asr: r.asr || '',
            maghreb: r.maghreb || '',
            isha: r.isha || '',
            jumuha: jumuhaVal,
            source: r.source || ''
          };
        });
        monthBase[ym] = JSON.stringify(normalized);
        monthDraft[ym] = JSON.parse(monthBase[ym]);
        renderMonthTable(ym);
        syncJumuaInputFromMonth(ym);
        checkDirty();
      })
      .catch(function () {
        flash('Impossible de joindre le serveur pour charger le mois.');
      });
  }

  function readHorairesForm() {
    var c = comp();
    var on = (c && c.state && c.state.on) ? c.state.on : {};
    var av = parseInt(getVal('f4'), 10);
    if (isNaN(av) || av < 0 || av > 120) av = 15;
    var deg = getVal('f13').replace('.', ',') || '61,6';
    return {
      aujourdhui: {
        on: !!on.h_auj,
        compte: !!on.h_compte,
        hijri: !!on.h_hijri,
        lienRappel: !!on.h_lienRappel,
        lienKhutba: !!on.h_lienKhutba
      },
      mois: {
        vendredis: !!on.h_vendredis
      },
      vendredi: {
        on: !!on.h_jumua,
        avance: av,
        conseil: !!on.h_conseil
      },
      ramadan: {
        on: !!on.h_ramadan,
        suhoor: !!on.h_suhoor,
        iftar: !!on.h_iftar,
        tarawih: !!on.h_tarawih,
        tarawihHeure: normalizeTime(getVal('f-tarawih')) || ''
      },
      aid: {
        on: !!on.h_aid,
        lieu: getVal('f7'),
        itineraire: getVal('f8'),
        fitrDate: getVal('f9'),
        fitrHeure: normalizeTime(getVal('f10')) || '',
        adhaDate: getVal('f11'),
        adhaHeure: normalizeTime(getVal('f12')) || ''
      },
      qibla: {
        on: !!on.h_qibla,
        degres: deg,
        repere: getVal('f14')
      }
    };
  }

  function applyHorairesToForm(s, asBase) {
    if (!s) return;
    if (asBase) settingsBase = JSON.parse(JSON.stringify(s));
    var sw = {
      h_vendredis: !!(s.mois && s.mois.vendredis),
      h_auj: !!(s.aujourdhui && s.aujourdhui.on),
      h_compte: !!(s.aujourdhui && s.aujourdhui.compte),
      h_hijri: !!(s.aujourdhui && s.aujourdhui.hijri),
      h_lienRappel: !!(s.aujourdhui && s.aujourdhui.lienRappel),
      h_lienKhutba: !!(s.aujourdhui && s.aujourdhui.lienKhutba),
      h_jumua: !!(s.vendredi && s.vendredi.on),
      h_conseil: !!(s.vendredi && s.vendredi.conseil),
      h_ramadan: !!(s.ramadan && s.ramadan.on),
      h_suhoor: !!(s.ramadan && s.ramadan.suhoor),
      h_iftar: !!(s.ramadan && s.ramadan.iftar),
      h_tarawih: !!(s.ramadan && s.ramadan.tarawih),
      h_aid: !!(s.aid && s.aid.on),
      h_qibla: !!(s.qibla && s.qibla.on)
    };
    var c = comp();
    if (c) c.setSwitches(sw, asBase);

    setVal('f4', s.vendredi && s.vendredi.avance != null ? s.vendredi.avance : 15);
    setVal('f-tarawih', (s.ramadan && s.ramadan.tarawihHeure) || '');
    setVal('f7', (s.aid && s.aid.lieu) || '');
    setVal('f8', (s.aid && s.aid.itineraire) || '');
    setVal('f9', (s.aid && s.aid.fitrDate) || '');
    setVal('f10', (s.aid && s.aid.fitrHeure) || '');
    setVal('f11', (s.aid && s.aid.adhaDate) || '');
    setVal('f12', (s.aid && s.aid.adhaHeure) || '');
    setVal('f13', (s.qibla && s.qibla.degres) || '61,6');
    setVal('f14', (s.qibla && s.qibla.repere) || '');
    updateTarawihVisibility(sw.h_tarawih);
  }

  function updateTarawihVisibility(on) {
    var w = getEl('h-tarawih-wrap');
    if (w) w.style.opacity = on ? '1' : '0.5';
  }

  function dirtyMonthsList() {
    var out = [];
    Object.keys(monthDraft).forEach(function (ym) {
      if (monthBase[ym] && JSON.stringify(monthDraft[ym]) !== monthBase[ym]) {
        out.push(ym);
      }
    });
    return out;
  }

  function isSettingsDirty() {
    if (khBase && JSON.stringify(readKhutba()) !== khBase) return true;
    if (rpDomBase && rpDomSig() !== rpDomBase) return true;
    if (!settingsBase) return false;
    return JSON.stringify(readHorairesForm()) !== JSON.stringify(settingsBase);
  }

  function checkDirty() {
    var c = comp();
    if (!c) return;
    var dirty = dirtyMonthsList().length > 0 || isSettingsDirty();
    c.setExtDirty(dirty);
  }

  // Outil 1 : Copier une heure sur tout le mois
  function applyCopyToMonth(clearMode) {
    var col = getVal('h-copy-col') || 'fajr';
    var scope = getVal('h-copy-scope') || 'all';
    var rawTime = clearMode ? '' : getVal('h-copy-time');
    var clean = clearMode ? '' : normalizeTime(rawTime);
    if (!clearMode && !clean) {
      flash('Choisissez une heure valide au format HH:MM (ex. 06:30).');
      return;
    }
    var days = monthDraft[currentMonth];
    if (!days) return;

    var count = 0;
    for (var i = 0; i < days.length; i++) {
      var r = days[i];
      var fri = isFriday(r.date);
      if (col === 'jumuha' && !fri) continue;
      if (scope === 'fridays' && !fri) continue;

      var targetCol = col === 'jumuha' ? 'dohr' : col;
      var curVal = (col === 'jumuha' || (col === 'dohr' && fri)) ? (r.jumuha || r.dohr) : r[col];
      if (scope === 'empty' && curVal) continue;

      if (col === 'jumuha' || (col === 'dohr' && fri)) {
        r.jumuha = clean;
        r.dohr = clean;
      } else {
        r[col] = clean;
      }
      var inp = document.querySelector('#h-month-table-wrap input[data-date="' + r.date + '"][data-col="' + targetCol + '"]');
      if (inp) {
        inp.value = clean;
        inp.style.borderColor = '';
      }
      count++;
    }

    if (col === 'jumuha' || col === 'dohr') syncJumuaInputFromMonth(currentMonth);
    updateMonthStatus(currentMonth);
    checkDirty();
    flash(clearMode
      ? 'Colonne ' + (COL_LABELS[col] || col) + ' vidée (' + count + ' jour' + (count > 1 ? 's' : '') + ').'
      : 'Heure ' + clean + ' copiée sur ' + count + ' jour' + (count > 1 ? 's' : '') + ' (' + (COL_LABELS[col] || col) + ').');
  }

  // Outil 2 : Coller depuis Excel (colonnes copiées, sans fichier)
  function looksLikeDayCell(cell) {
    var s = String(cell || '').trim().toLowerCase();
    if (!s) return false;
    if (/^\d{1,2}$/.test(s)) {
      var n = parseInt(s, 10);
      return n >= 1 && n <= 31;
    }
    if (/^\d{4}-\d{2}-\d{2}$/.test(s) || /^\d{1,2}[\/\-]\d{1,2}(?:[\/\-]\d{2,4})?$/.test(s)) return true;
    if (/^(dim|lun|mar|mer|jeu|ven|sam)/.test(s)) return true;
    return false;
  }

  function looksLikeHeaderRow(cells) {
    var joined = cells.join(' ').toLowerCase();
    return /(fajr|lever|dohr|dhuhr|asr|maghreb|maghrib|icha|isha|jour|date)/.test(joined);
  }

  function applyExcelPaste(rawText, mode, startRowIndex, startColIndex) {
    var text = String(rawText || '').replace(/\r\n/g, '\n').replace(/\r/g, '\n').trim();
    if (!text) {
      flash('Collez d’abord les cellules copiées depuis Excel.');
      return 0;
    }
    var days = monthDraft[currentMonth];
    if (!days || !days.length) return 0;

    var lines = text.split('\n').map(function (l) { return l.trim(); }).filter(Boolean);
    if (!lines.length) return 0;

    var rows = lines.map(function (line) {
      if (line.indexOf('\t') > -1) return line.split('\t').map(function (c) { return c.trim(); });
      if (line.indexOf(';') > -1) return line.split(';').map(function (c) { return c.trim(); });
      return line.split(/\s{2,}|\s+/).map(function (c) { return c.trim(); });
    });

    if (rows.length > 0 && looksLikeHeaderRow(rows[0])) {
      rows.shift();
    }
    if (!rows.length) {
      flash('Aucune ligne d’horaires détectée dans le texte collé.');
      return 0;
    }

    var updatedCells = 0;
    var invalidCells = 0;
    var rStart = typeof startRowIndex === 'number' ? startRowIndex : 0;

    for (var rIdx = 0; rIdx < rows.length; rIdx++) {
      var cells = rows[rIdx];
      if (!cells.length) continue;

      var targetRow = rStart + rIdx;
      var colOffset = 0;

      // Si on colle en mode « all » et que la 1re cellule est un numéro de jour ou une date
      if ((mode === 'all' || startColIndex === undefined) && cells.length > 1 && looksLikeDayCell(cells[0])) {
        var dayMatch = /(\d{1,2})\s*$/.exec(cells[0]) || /^(\d{1,2})\b/.exec(cells[0]);
        if (/^\d{4}-\d{2}-(\d{2})$/.test(cells[0])) {
          targetRow = parseInt(cells[0].slice(8, 10), 10) - 1;
        } else if (dayMatch) {
          var dNum = parseInt(dayMatch[1], 10);
          if (dNum >= 1 && dNum <= days.length) targetRow = dNum - 1;
        }
        colOffset = 1;
      }

      if (targetRow < 0 || targetRow >= days.length) continue;
      var dayObj = days[targetRow];
      var fri = isFriday(dayObj.date);

      if (mode && mode !== 'all') {
        // Collage d'une seule colonne choisie
        if (mode === 'jumuha' && !fri) continue;
        var valStr = cells[colOffset] !== undefined ? cells[colOffset] : cells[0];
        var cleaned = normalizeTime(valStr);
        if (cleaned === null) { invalidCells++; continue; }
        var domCol = mode === 'jumuha' ? 'dohr' : mode;
        if (mode === 'jumuha' || (mode === 'dohr' && fri)) {
          dayObj.jumuha = cleaned;
          dayObj.dohr = cleaned;
        } else {
          dayObj[mode] = cleaned;
        }
        var inpSingle = document.querySelector('#h-month-table-wrap input[data-date="' + dayObj.date + '"][data-col="' + domCol + '"]');
        if (inpSingle) { inpSingle.value = cleaned; inpSingle.style.borderColor = ''; }
        updatedCells++;
      } else {
        // Collage multi-colonnes à partir de startColIndex (ou 0)
        var cStart = typeof startColIndex === 'number' ? startColIndex : 0;
        for (var cIdx = 0; cIdx + colOffset < cells.length && (cStart + cIdx) < COLS.length; cIdx++) {
          var colName = COLS[cStart + cIdx];
          var rawCell = cells[cIdx + colOffset];
          var cleanCell = normalizeTime(rawCell);
          if (cleanCell === null) { invalidCells++; continue; }
          if (colName === 'dohr' && fri) {
            dayObj.dohr = cleanCell;
            dayObj.jumuha = cleanCell;
          } else {
            dayObj[colName] = cleanCell;
          }
          var inp = document.querySelector('#h-month-table-wrap input[data-date="' + dayObj.date + '"][data-col="' + colName + '"]');
          if (inp) { inp.value = cleanCell; inp.style.borderColor = ''; }
          updatedCells++;
        }
      }
    }

    syncJumuaInputFromMonth(currentMonth);
    updateMonthStatus(currentMonth);
    checkDirty();

    if (updatedCells > 0) {
      flash(updatedCells + ' horaire' + (updatedCells > 1 ? 's' : '') + ' collé' + (updatedCells > 1 ? 's' : '') +
        (invalidCells > 0 ? ' (' + invalidCells + ' valeur(s) ignorée(s))' : '') + '. Cliquez sur Enregistrer pour sauvegarder.');
    } else if (invalidCells > 0) {
      flash('Format d’heure non reconnu. Utilisez le format HH:MM (ex. 06:30).');
    }
    return updatedCells;
  }

  function validateTableInputs() {
    var inputs = document.querySelectorAll('#h-month-table-wrap input.h-cell');
    for (var i = 0; i < inputs.length; i++) {
      var inp = inputs[i];
      var c = normalizeTime(inp.value);
      if (c === null) {
        inp.style.borderColor = '#B3261E';
        inp.focus();
        return { error: 'Heure invalide (' + inp.getAttribute('aria-label') + ') : écrivez au format HH:MM (ex. 06:30) ou laissez vide.' };
      }
      inp.style.borderColor = '';
      inp.value = c;
    }
    return { ok: true };
  }


  // ---- H6 : onglet « Langue de la khutba » (clé khutba) ----
  var KH_LANGUES = ['Français', 'Arabe', 'Anglais', 'Arabe et français'];
  var KH_TRADS = ['Aucune', 'Arabe', 'Français', 'Anglais'];
  var KH_TRASH = '<svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"></path><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"></path><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>';
  var khBase = null, khDraft = null, rpBase = null, rpDomBase = null;
  // Interrupteurs : suivis par la logique du panneau (état « on » / « base ») ; ici, seulement les champs.
  function rpDomSig() { return JSON.stringify({ delais: rpSelectedDelais(), defaut: parseInt(getVal('f24'), 10) || 15, titre: oneSpace(getVal('f25')) }); }

  function escH(v) {
    return String(v == null ? '' : v).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; });
  }
  function todayIso() {
    try { return new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Moncton', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date()); }
    catch (e) { return new Date().toISOString().slice(0, 10); }
  }
  function longFr(iso) {
    try { return new Intl.DateTimeFormat('fr-CA', { timeZone: 'UTC', weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' }).format(new Date(iso + 'T12:00:00Z')); }
    catch (e) { return iso; }
  }
  function opts(list, cur) {
    return list.map(function (v) { return '<option' + (v === cur ? ' selected' : '') + '>' + escH(v) + '</option>'; }).join('');
  }
  function oneSpace(v) { return String(v || '').replace(/\s+/g, ' ').trim(); }

  function renderKhutba() {
    var wrap = getEl('kh-list');
    if (!wrap || !khDraft) return;
    var list = khDraft.vendredis, t = todayIso();
    if (!list.length) {
      wrap.innerHTML = '<p class="hint" style="margin:0">Aucun vendredi pour l’instant. Choisissez une date ci-dessous pour ajouter le premier.</p>';
      return;
    }
    wrap.innerHTML = '<ol style="list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:10px">' + list.map(function (v, i) {
      var lab = longFr(v.date), past = v.date < t;
      return '<li style="border:1px solid #E4D9C0;border-radius:14px;background:#fff">' +
        '<div style="display:flex;align-items:center;gap:10px;padding:10px 10px 10px 14px;flex-wrap:wrap;border-bottom:1px solid #F3EAD8">' +
        '<span class="pos">' + (i + 1) + '</span>' +
        '<span style="flex:1;min-width:150px;font-weight:700;color:#0E4D3C;text-transform:capitalize">' + escH(lab) + '</span>' +
        (past ? '<span class="tag" style="background:#F3EAD8;color:#7A5A1E">Passé, plus affiché</span>' : '') +
        '<button type="button" class="ico" data-kh-del="' + i + '" aria-label="Supprimer le ' + escH(lab) + '">' + KH_TRASH + '</button>' +
        '<button type="button" class="sw" role="switch" data-kh-on="' + i + '" aria-label="Afficher le ' + escH(lab) + '" aria-checked="' + (v.on ? 'true' : 'false') + '"></button>' +
        '</div><div class="li-b" style="opacity:' + (v.on ? 1 : 0.5) + '"><div class="g3">' +
        '<div class="fld"><label class="lbl" for="kh-l-' + i + '">Langue principale</label><select class="in" id="kh-l-' + i + '" data-i="' + i + '" data-f="langue">' + opts(KH_LANGUES, v.langue) + '</select></div>' +
        '<div class="fld"><label class="lbl" for="kh-t-' + i + '">Traduction</label><select class="in" id="kh-t-' + i + '" data-i="' + i + '" data-f="traduction">' + opts(KH_TRADS, v.traduction) + '</select></div>' +
        '<div class="fld"><label class="lbl" for="kh-i-' + i + '">Imam</label><input class="in" id="kh-i-' + i + '" type="text" maxlength="80" data-i="' + i + '" data-f="imam" placeholder="Nom de l’imam" value="' + escH(v.imam) + '"></div>' +
        '</div></div></li>';
    }).join('') + '</ol>';
  }

  function applyKhutba(k, asBase) {
    if (!k) return;
    if (asBase) khBase = JSON.stringify(k);
    khDraft = JSON.parse(JSON.stringify(k));
    setVal('f21', String(k.nombre || 4));
    setVal('f22', k.mode || 'Résumé imprimé à l’entrée');
    renderKhutba();
  }

  function readKhutba() {
    if (!khDraft) return null;
    return {
      vendredis: khDraft.vendredis.map(function (v) {
        return { date: v.date, langue: v.langue, traduction: v.traduction, imam: oneSpace(v.imam), on: !!v.on };
      }),
      nombre: parseInt(getVal('f21'), 10) || 4,
      mode: getVal('f22') || 'Résumé imprimé à l’entrée'
    };
  }

  function addKhutbaDay() {
    var d = getVal('kh-new-date');
    if (!/^\d{4}-\d{2}-\d{2}$/.test(d)) { flash('Choisissez d’abord la date du vendredi à ajouter.'); return; }
    if (dayOfWeek(d) !== 5) { flash('Cette date n’est pas un vendredi. Choisissez un vendredi.'); return; }
    if (!khDraft) return;
    if (khDraft.vendredis.some(function (v) { return v.date === d; })) { flash('Ce vendredi est déjà dans la liste.'); return; }
    khDraft.vendredis.push({ date: d, langue: 'Arabe', traduction: 'Français', imam: '', on: true });
    khDraft.vendredis.sort(function (a, b) { return a.date < b.date ? -1 : 1; });
    setVal('kh-new-date', '');
    renderKhutba();
    checkDirty();
    flash('Vendredi ajouté. Cliquez sur Enregistrer pour le publier.');
  }

  // ---- H6 : onglet « Rappel de prière » (clé rappel) ----
  var RP_KEYS = { fajr: 'r_fajr', dohr: 'r_dohr', jumua: 'r_jumua', asr: 'r_asr', maghreb: 'r_maghreb', icha: 'r_icha' };
  function rpSelectedDelais() {
    var out = [];
    document.querySelectorAll('#rp-delais [data-rp-delai]').forEach(function (b) {
      if (b.getAttribute('aria-pressed') === 'true') out.push(parseInt(b.getAttribute('data-rp-delai'), 10));
    });
    return out;
  }
  function rpRefreshDefaut(wanted) {
    var sel = getEl('f24');
    if (!sel) return;
    var list = rpSelectedDelais();
    var cur = wanted != null ? String(wanted) : sel.value;
    sel.innerHTML = list.map(function (d) { return '<option value="' + d + '">' + (d === 60 ? '1 h' : d + ' min') + '</option>'; }).join('');
    sel.value = list.indexOf(parseInt(cur, 10)) > -1 ? cur : (list.indexOf(15) > -1 ? '15' : String(list[0]));
  }
  function readRappel() {
    var c = comp();
    var on = (c && c.state && c.state.on) ? c.state.on : {};
    var prieres = {};
    Object.keys(RP_KEYS).forEach(function (k) { prieres[k] = !!on[RP_KEYS[k]]; });
    return {
      prieres: prieres,
      delais: rpSelectedDelais(),
      defaut: parseInt(getVal('f24'), 10) || 15,
      titre: oneSpace(getVal('f25')),
      son: !!on.r_son,
      vibration: !!on.r_vib
    };
  }
  function applyRappel(r, asBase) {
    if (!r) return;
    if (asBase) rpBase = JSON.stringify(r);
    var sw = { r_son: !!r.son, r_vib: !!r.vibration };
    Object.keys(RP_KEYS).forEach(function (k) { sw[RP_KEYS[k]] = !!(r.prieres && r.prieres[k]); });
    var c = comp();
    if (c) c.setSwitches(sw, asBase);
    document.querySelectorAll('#rp-delais [data-rp-delai]').forEach(function (b) {
      var d = parseInt(b.getAttribute('data-rp-delai'), 10);
      b.setAttribute('aria-pressed', (r.delais || []).indexOf(d) > -1 ? 'true' : 'false');
    });
    rpRefreshDefaut(r.defaut);
    setVal('f25', r.titre || 'Prière dans {délai}');
    if (asBase) rpDomBase = rpDomSig();
  }

  function bindH6() {
    var list = getEl('kh-list');
    if (list) {
      var onField = function (e) {
        var t = e.target;
        if (!t || !t.getAttribute || t.getAttribute('data-f') == null || !khDraft) return;
        var row = khDraft.vendredis[parseInt(t.getAttribute('data-i'), 10)];
        if (!row) return;
        row[t.getAttribute('data-f')] = t.value;
        checkDirty();
      };
      list.addEventListener('input', onField);
      list.addEventListener('change', onField);
      list.addEventListener('click', function (e) {
        var b = e.target && e.target.closest ? e.target.closest('button') : null;
        if (!b || !khDraft) return;
        if (b.hasAttribute('data-kh-del')) {
          khDraft.vendredis.splice(parseInt(b.getAttribute('data-kh-del'), 10), 1);
          renderKhutba();
          checkDirty();
          flash('Vendredi retiré. « Annuler les changements » le remet.');
        } else if (b.hasAttribute('data-kh-on')) {
          var row = khDraft.vendredis[parseInt(b.getAttribute('data-kh-on'), 10)];
          if (!row) return;
          row.on = !row.on;
          renderKhutba();
          checkDirty();
        }
      });
    }
    var add = getEl('kh-add');
    if (add) add.addEventListener('click', addKhutbaDay);
    ['f21', 'f22', 'f24', 'f25'].forEach(function (id) {
      var el = getEl(id);
      if (!el) return;
      el.addEventListener('input', checkDirty);
      el.addEventListener('change', checkDirty);
    });
    var seg = getEl('rp-delais');
    if (seg) {
      seg.addEventListener('click', function (e) {
        var b = e.target && e.target.closest ? e.target.closest('[data-rp-delai]') : null;
        if (!b) return;
        var pressed = b.getAttribute('aria-pressed') === 'true';
        if (pressed && rpSelectedDelais().length === 1) { flash('Gardez au moins un délai proposé.'); return; }
        b.setAttribute('aria-pressed', pressed ? 'false' : 'true');
        rpRefreshDefaut(null);
        checkDirty();
      });
    }
  }

  function saveAll() {
    if (saving) return;
    var check = validateTableInputs();
    if (check.error) { flash(check.error); return; }

    var horairesPayload = readHorairesForm();
    if (horairesPayload.aid.itineraire && !/^https?:\/\/\S{3,}$/i.test(horairesPayload.aid.itineraire)) {
      flash('Le lien itinéraire de l’Aïd doit commencer par https://');
      var f8 = getEl('f8');
      if (f8) f8.focus();
      return;
    }

    var khPayload = readKhutba(), rpPayload = readRappel();
    if (rpPayload && !rpPayload.titre) {
      flash('Écrivez le titre de la notification (onglet Rappel de prière).');
      var f25 = getEl('f25');
      if (f25) f25.focus();
      return;
    }

    saving = true;
    flash('Enregistrement…');

    var monthsToSave = dirtyMonthsList();
    if (currentMonth && monthsToSave.indexOf(currentMonth) === -1) {
      monthsToSave.push(currentMonth);
    }

    var putJson = function (url, body) {
      return fetch(url, {
        method: 'PUT',
        credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      }).then(function (r) { return r.json().catch(function () { return { ok: false }; }); });
    };

    var tasks = [
      putJson('/api/admin/settings/horaires', horairesPayload),
      khPayload ? putJson('/api/admin/settings/khutba', khPayload) : Promise.resolve({ ok: true }),
      rpPayload ? putJson('/api/admin/settings/rappel', rpPayload) : Promise.resolve({ ok: true })
    ];

    monthsToSave.forEach(function (ym) {
      tasks.push(
        putJson('/api/admin/prayer-times/' + encodeURIComponent(ym), {
          month: ym,
          days: monthDraft[ym] || []
        })
      );
    });

    // Si l'interrupteur « Page publiée » (pub_horaires) a changé et qu'on a pagesBase
    var c = comp();
    if (pagesBase && c && c.state && c.state.on) {
      var nextPages = Object.assign({}, pagesBase, {
        pg_horaires: !!c.state.on.pub_horaires,
        pg_khutba: !!c.state.on.pub_khutba,
        pg_rappel: !!c.state.on.pub_rappel
      });
      if (JSON.stringify(nextPages) !== JSON.stringify(pagesBase)) {
        tasks.push(
          putJson('/api/admin/settings/pages', nextPages).then(function (res) {
            if (res && res.ok && res.settings) pagesBase = res.settings;
            return res;
          })
        );
      }
    }

    Promise.all(tasks)
      .then(function (results) {
        saving = false;
        var failed = results.find(function (r) { return !r || !r.ok; });
        if (failed) {
          flash((failed && failed.message) || 'L’enregistrement a échoué. Vérifiez vos valeurs et réessayez.');
          return;
        }
        if (results[1] && results[1].settings) applyKhutba(results[1].settings, true);
        if (results[2] && results[2].settings) applyRappel(results[2].settings, true);
        var hRes = results[0];
        if (hRes && hRes.settings) {
          applyHorairesToForm(hRes.settings, true);
        } else {
          settingsBase = JSON.parse(JSON.stringify(horairesPayload));
        }

        monthsToSave.forEach(function (ym) {
          if (monthDraft[ym]) {
            monthBase[ym] = JSON.stringify(monthDraft[ym]);
          }
        });

        if (c) c.commitBase();
        updateMonthStatus(currentMonth);
        flash('Horaires et réglages enregistrés. Le site est à jour.');
      })
      .catch(function () {
        saving = false;
        flash('Impossible de joindre le serveur. Vérifiez votre connexion et réessayez.');
      });
  }

  function undoAll() {
    Object.keys(monthBase).forEach(function (ym) {
      monthDraft[ym] = JSON.parse(monthBase[ym]);
    });
    if (currentMonth) {
      renderMonthTable(currentMonth);
      syncJumuaInputFromMonth(currentMonth);
    }
    if (settingsBase) {
      applyHorairesToForm(settingsBase, false);
    }
    if (khBase) applyKhutba(JSON.parse(khBase), false);
    if (rpBase) applyRappel(JSON.parse(rpBase), false);
    var c = comp();
    if (c) c.revertBase();
    flash('Changements annulés.');
  }

  function bindEvents() {
    var selMonth = getEl('f1');
    if (selMonth) {
      selMonth.addEventListener('change', function () {
        var ym = selMonth.value;
        if (ym && ym !== currentMonth) {
          loadMonth(ym, false);
        }
      });
    }

    // Saisie directe dans le tableau mensuel
    var wrap = getEl('h-month-table-wrap');
    if (wrap) {
      wrap.addEventListener('input', function (e) {
        var t = e.target;
        if (!t || !t.classList || !t.classList.contains('h-cell')) return;
        var date = t.getAttribute('data-date');
        var col = t.getAttribute('data-col');
        var rowIdx = parseInt(t.getAttribute('data-row'), 10);
        var days = monthDraft[currentMonth];
        if (!days || !days[rowIdx]) return;

        var clean = normalizeTime(t.value);
        if (clean === null) {
          t.style.borderColor = '#C49A4A';
          return;
        }
        t.style.borderColor = '';
        if (col === 'dohr' && isFriday(date)) {
          days[rowIdx].dohr = clean;
          days[rowIdx].jumuha = clean;
          syncJumuaInputFromMonth(currentMonth);
        } else {
          days[rowIdx][col] = clean;
        }
        updateMonthStatus(currentMonth);
        checkDirty();
      });

      wrap.addEventListener('blur', function (e) {
        var t = e.target;
        if (!t || !t.classList || !t.classList.contains('h-cell')) return;
        var clean = normalizeTime(t.value);
        if (clean !== null) {
          t.value = clean;
          t.style.borderColor = '';
        } else {
          t.style.borderColor = '#B3261E';
        }
      }, true);

      // Collage direct multi-cellules dans le tableau
      wrap.addEventListener('paste', function (e) {
        var t = e.target;
        if (!t || !t.classList || !t.classList.contains('h-cell')) return;
        var clip = (e.clipboardData || window.clipboardData);
        if (!clip) return;
        var text = clip.getData('text');
        if (!text || (text.indexOf('\n') === -1 && text.indexOf('\t') === -1)) return;
        e.preventDefault();
        var rIdx = parseInt(t.getAttribute('data-row'), 10) || 0;
        var colName = t.getAttribute('data-col') || 'fajr';
        var cIdx = Math.max(0, COLS.indexOf(colName));
        var hasTabs = text.indexOf('\t') > -1 || text.indexOf(';') > -1;
        applyExcelPaste(text, hasTabs ? 'all' : colName, rIdx, cIdx);
      });
    }

    // Heure de Jumu'a (#f3) -> synchronisée avec les vendredis du tableau mensuel
    var f3 = getEl('f3');
    if (f3) {
      f3.addEventListener('input', function () {
        applyJumuaInputToMonth(currentMonth, f3.value);
      });
      f3.addEventListener('change', function () {
        applyJumuaInputToMonth(currentMonth, f3.value);
      });
    }

    // Autres champs de réglages
    ['f4', 'f-tarawih', 'f7', 'f8', 'f9', 'f10', 'f11', 'f12', 'f13', 'f14'].forEach(function (id) {
      var el = getEl(id);
      if (!el) return;
      el.addEventListener('input', checkDirty);
      el.addEventListener('change', checkDirty);
    });

    // Boutons « Copier une heure sur tout le mois » et « Coller depuis Excel »
    var btnCopy = getEl('btn-h-copy');
    var panelCopy = getEl('h-copy-panel');
    var btnPaste = getEl('btn-h-paste');
    var panelPaste = getEl('h-paste-panel');

    if (btnCopy && panelCopy) {
      btnCopy.addEventListener('click', function () {
        var show = panelCopy.style.display === 'none';
        panelCopy.style.display = show ? 'flex' : 'none';
        if (show && panelPaste) panelPaste.style.display = 'none';
      });
    }
    if (btnPaste && panelPaste) {
      btnPaste.addEventListener('click', function () {
        var show = panelPaste.style.display === 'none';
        panelPaste.style.display = show ? 'flex' : 'none';
        if (show && panelCopy) panelCopy.style.display = 'none';
        if (show) {
          var area = getEl('h-paste-area');
          if (area) area.focus();
        }
      });
    }

    var btnCopyApply = getEl('btn-h-copy-apply');
    if (btnCopyApply) btnCopyApply.addEventListener('click', function () { applyCopyToMonth(false); });

    var btnCopyClear = getEl('btn-h-copy-clear');
    if (btnCopyClear) btnCopyClear.addEventListener('click', function () { applyCopyToMonth(true); });

    var btnCopyClose = getEl('btn-h-copy-close');
    if (btnCopyClose && panelCopy) btnCopyClose.addEventListener('click', function () { panelCopy.style.display = 'none'; });

    var btnPasteApply = getEl('btn-h-paste-apply');
    if (btnPasteApply) {
      btnPasteApply.addEventListener('click', function () {
        var area = getEl('h-paste-area');
        var mode = getVal('h-paste-col') || 'all';
        var n = applyExcelPaste(area ? area.value : '', mode, 0, 0);
        if (n > 0 && panelPaste) {
          panelPaste.style.display = 'none';
          if (area) area.value = '';
        }
      });
    }

    var btnPasteClose = getEl('btn-h-paste-close');
    if (btnPasteClose && panelPaste) btnPasteClose.addEventListener('click', function () { panelPaste.style.display = 'none'; });
  }

  window.__saHorairesSave = saveAll;
  window.__saHorairesUndo = undoAll;
  window.__saHorairesOnSwitch = function (k, val) {
    if (k === 'h_tarawih') updateTarawihVisibility(val);
    checkDirty();
  };

  function start() {
    allowedMonths = computeAllowedMonths();
    currentMonth = allowedMonths[0].ym;

    var sel = getEl('f1');
    if (sel) {
      sel.innerHTML = allowedMonths.map(function (m) {
        return '<option value="' + m.ym + '">' + m.label + '</option>';
      }).join('');
      sel.value = currentMonth;
    }

    bindEvents();
    bindH6();

    var getJson = function (url) {
      return fetch(url, { credentials: 'same-origin' }).then(function (r) { return r.json().catch(function () { return { ok: false }; }); });
    };

    Promise.all([
      getJson('/api/admin/settings/horaires'),
      getJson('/api/admin/settings/season'),
      getJson('/api/admin/settings/pages'),
      loadMonth(currentMonth, true),
      getJson('/api/admin/settings/khutba'),
      getJson('/api/admin/settings/rappel')
    ]).then(function (res) {
      var hData = res[0], sData = res[1], pData = res[2];
      if (res[4] && res[4].ok && res[4].settings) applyKhutba(res[4].settings, true);
      else { var kl = getEl('kh-list'); if (kl) kl.innerHTML = '<p class="hint" style="margin:0">Impossible de charger la liste des vendredis. Rechargez la page.</p>'; }
      if (res[5] && res[5].ok && res[5].settings) applyRappel(res[5].settings, true);
      if (hData && hData.ok && hData.settings) {
        applyHorairesToForm(hData.settings, true);
      }
      if (sData && sData.ok && sData.settings) {
        seasonDates = { from: sData.settings.from || '', to: sData.settings.to || '' };
        setVal('f5', seasonDates.from);
        setVal('f6', seasonDates.to);
      }
      if (pData && pData.ok && pData.settings) {
        pagesBase = pData.settings;
        var c = comp();
        if (c) {
          c.setSwitches({
            pub_horaires: pData.settings.pg_horaires !== false,
            pub_khutba: !!pData.settings.pg_khutba,
            pub_rappel: !!pData.settings.pg_rappel
          }, true);
        }
      }
      checkDirty();
    }).catch(function () {});
  }

  if (comp() && getEl('h-month-table-wrap')) start();
  else window.addEventListener('sa-horaires-ready', start, { once: true });
})();
</script>
'''


def wire_horaires_panel():
    path = ROOT / 'SA-Horaires.dc.html'
    s, i, j, tpl = load(path)

    # 1. Remplace le contenu de #sp-0 (« Horaires du mois »)
    a = tpl.index('<div id="sp-0" class="sp">')
    b = tpl.index('<div id="sp-1" class="sp">')
    tpl = tpl[:a] + SP0_HTML + tpl[b:]

    # 1 bis. Remplace #sp-1 (khutba) et #sp-2 (rappel), jusqu'à la fin de <main> (étape H6)
    a = tpl.index('<div id="sp-1" class="sp">')
    b = tpl.index('</main>', a)
    tpl = tpl[:a] + SP12_HTML + tpl[b:]

    # 2. Remplace la classe Component par la version reliée
    tpl, n = re.subn(r'class Component extends DCLogic \{.*?\n\}', lambda _: COMPONENT_SCRIPT, tpl, count=1, flags=re.S)
    assert n == 1, 'Component introuvable dans SA-Horaires.dc.html'

    # 3. Injecte le script #sa-horaires-sync avant </body>
    tpl = re.sub(r'<script id="sa-horaires-sync">.*?</script>\s*', '', tpl, flags=re.S)
    k = tpl.rindex('</body>')
    tpl = tpl[:k] + HORAIRES_SYNC_SCRIPT + tpl[k:]

    save(path, s, i, j, tpl)
    print('SA-Horaires.dc.html : Horaires du mois branché (tableau mensuel, copie, collage Excel, réglages)')


if __name__ == '__main__':
    wire_horaires_panel()
