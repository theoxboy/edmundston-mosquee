# Backend du superadmin (Cloudflare Pages Functions + D1)

Le site statique reste servi depuis la racine du dépôt. L'API vit dans `functions/`,
sur le même domaine : pas de CORS, cookie de session `HttpOnly; Secure; SameSite=Strict`.
Base : D1 `edmundston-mosquee`, liée sous le nom `DB` (voir `wrangler.toml` et Pages → Paramètres → Liaisons).
Photos (étape M1) : espace KV `edmundston-medias` (palier gratuit, sans carte bancaire), lié sous le nom `MEDIA` dans `wrangler.toml` (ce fichier fait foi pour les liaisons). Clé = `media.file_key`. KV est finalement cohérent : une photo neuve peut mettre jusqu'à une minute à être visible partout (le panneau l'annonce, `/media/` ne met jamais un 404 en cache). Palier gratuit : 1 Go, 100 000 lectures et 1 000 écritures (envois et suppressions) par jour.

## Feuille de route

| Étape | Contenu | État |
|---|---|---|
| 1 | Compte superadmin (un seul, imposé par la base), sessions, limitation des essais, journal ; connexion et déconnexion ; pages `SA-*` protégées côté serveur | en ligne |
| 2a | Autres comptes à rôle limité (`editor`, `events`), mot de passe provisoire à changer à la 1re connexion, page `SA-Comptes.html` | en ligne |
| 2 | Réglages des widgets de l'accueil (`site_settings` clé `home`) ; « Enregistrer » du panneau Accueil ; l'accueil public les applique | en ligne |
| Accueil | Panneau Accueil fiabilisé : vraie logique (`scripts/panneau_component.js`), heures et annonces modifiables, rubriques du menu, ordres, nombre d'annonces, menu « … » (exporter, importer, valeurs d'origine) ; accueil public : durée de chargement, date hégirienne, ordre des cartes | fait, à pousser |
| 2b | Statistiques réelles (`page_views`, `/api/admin/stats`) et bandeau du panneau Accueil | en ligne |
| 2c | Inscriptions aux événements (`event_registrations`, clé `event_registration`), panneau Événements, export CSV | en ligne |
| Site entier | « Pages publiées » (clé `pages`, pastilles d'état réel pour niveaux 1/2/3, interrupteur Accueil verrouillé) ; « Compte et sécurité » avec les vraies données de session et journal détaillé (nom des pages modifiées) | fait, à pousser |
| Site entier | « Bannière d'alerte » (clé `alert`) : bande en haut de toutes les pages publiques, avec message, lien, période, couleur, aperçu en direct et cohérence message vide / OFF | fait, à pousser |
| Site entier | « Mode du site » (clé `season`) : bandeau Ramadan / Aïd en haut de l'accueil pendant la période ; « Langues » (clé `languages`, interrupteur Français verrouillé) | fait, à pousser |
| 5a | Créer une page : base (`custom_pages`, `page_redirects`) et API (créer, lire, modifier, dupliquer, supprimer) | en ligne |
| 5b | Créer une page : écrans « Mes pages » (création avec titre, lien et visibilité, Brouillon par défaut) et éditeur (blocs Texte, Bouton, Tableau complet, compteurs, sauvegarde haut/bas et suppression avec confirmation) | fait, à pousser |
| 5c | Créer une page : affichage public `/p/<lien>` (publiée, lien privé, brouillon pour les comptes connectés) | en ligne |
| 5d | Créer une page : pages proposées dans les liens de la bannière d'alerte, des boutons de l'accueil et de l'éditeur | en ligne |
| H1 | Horaires : `prayer_times` complétée (lever, une ligne par jour) ; clé `horaires` (bloc Aujourd'hui, vendredi, Ramadan, Aïd, Qibla) | en ligne |
| H2 | Horaires : API du tableau du mois (`GET`/`PUT /api/admin/prayer-times`) et API publique du mois et du jour (`GET /api/prayer-times`, repli sur les défauts Accueil) | en ligne |
| H3 | Horaires : panneau `SA-Horaires` (« Horaires du mois », tableau mensuel éditable, copie sur tout le mois, collage Excel, réglages `horaires`, dates Ramadan depuis `season`, Jumu'a depuis le tableau mensuel) | en ligne |
| H4 | Horaires : page publique (et M-/T-) reliée à la base : heures du jour, tableau du mois avec « Aujourd'hui » sur le vrai jour, carte du vendredi, Ramadan (dates du Mode du site, Suhoor, Iftar, Tarawih), Aïd, Qibla, réglages du bloc Aujourd'hui ; bouton PDF retiré (`scripts/wire_prieres.py`) | en ligne |
| H5 | Horaires : heures du jour sur les 58 pages publiques (barre « Prochaine prière », menu mobile, pied de page, carte « Prochaine prière » de l'accueil), sur toutes les heures remplies ; le script de l'accueil ne garde que l'affichage des puces et de la progression | en ligne |
| H6 | Horaires : onglets « Langue de la khutba » (clé `khutba` : vendredis datés, langue, traduction, imam, nombre affiché, mode) et « Rappel de prière » (clé `rappel` : prières et délais proposés, délai par défaut, titre, son, vibration) ; pages N2-Khutba et N3-Rappel reliées (vraies notifications page ouverte, choix mémorisés sur l'appareil, fichier calendrier .ics du mois) | en ligne |
| A | À propos : onglet « L’association » (clé `apropos` : présentation, valeurs, histoire datée, liens du projet, équipe avec photos réduites et accord écrit, chiffres et sources) et onglet « Campagne en direct » (clé `campagne` : donateurs, mise à jour automatique depuis `donations`, étapes, dons par semaine, derniers dons ; objectif et récolté dans `home.campagne`) ; pages APropos et N3-Campagne reliées, simulation retirée ; route publique `GET /api/campagne` | en ligne |
| S1 | Services : onglet « Tous les services » (clé `services` : cartes ordonnées, affichées ou masquées, cartes libres ajoutées ou supprimées ; prières et Jumu'a avec les heures du tableau du mois ; Aïd avec le lieu commun `horaires.aid.lieu` et la Zakat al-Fitr ; cartes « Les autres services », équipements, bloc « Une question ? ») ; interrupteurs « Page publiée » des 6 onglets reliés à `pages` ; page Services (et M-/T-) reliée, mentions de brouillon retirées | en ligne |
| S2 | Boîte de réception : table `form_messages` (migration 0009), envoi public `POST /api/forms` (champ piège, délai minimal de 3 s, 5 envois par connexion en 15 min), onglet « Demandes reçues » dans Contact (filtres, statut nouveau / lu / traité, répondre, suppression définitive) via `GET`/`PATCH`/`DELETE /api/admin/forms` ; le formulaire Contact envoie au site au lieu d'ouvrir le logiciel de courriel | en ligne |
| S3-S5 | Services : onglets « Cours » (clé `cours` : fiches des cours, inscriptions, liste d’attente, cours d’essai, tarifs calculés), « Mariages » (`mariages` : étapes, documents, formulaire), « Funérailles » (`funerailles` : téléphone ou courriel d’urgence, étapes, documents, prise en charge), « Aide alimentaire » (`aide` : formulaire, besoins du mois, dépôt, don Interac) et « Espace femmes » (`femmes` : horaires par jour sur 2 plages, fermeture exceptionnelle datée, plan d’accès réduit, infos pratiques, règles) ; 15 pages N2 (PC, M-, T-) reliées, mentions de brouillon retirées ; formulaires Cours, Mariages et Aide envoyés dans Contact → Demandes reçues | en ligne |
| D | Faire un don : onglet « Page Dons » (clé `dons` : affichage de la campagne, Virement Interac avec montants proposés, Desjardins masqué tant que les 3 numéros manquent, autres formes de don, questions fréquentes, reçus fiscaux ; objectif et montant récolté écrits dans `home.campagne`, zakat al-Fitr reprise de la carte Aïd des Services) et onglet « Bloc Merci » (clé `merci` : bandeau en bas de la page Dons, partage Facebook et WhatsApp réels, bouton de suivi) ; 3 pages Dons (PC, M-, T-) reliées, mentions « À remplir » retirées | en ligne |
| E | Événements : onglet « Annonces » (clé `evenements` : liste des événements avec fiche détaillée dépliable, inscription par formulaire ou par message, événement à la une automatique ou choisi, filtres par lieu, événements passés le lendemain de leur date, rendez-vous fixes, bloc « Aller plus loin », partage), onglet « Calendrier du mois » (clé `calendrier` : catégories, cours de la semaine, vue par défaut, fichier agenda .ics) et onglet « Inscription » relié à la liste ; onglet « Détail d’un événement » retiré ; « Dernières annonces » de l’accueil calculées depuis les événements (`GET /api/settings/home`) ; pages Événements et Calendrier (PC, M-, T-) reliées, mentions de brouillon et « Alertes par courriel » retirées | en ligne |
| R | Ressources : onglet « Nouveaux arrivants » (clé `ressources` : phrase d’accueil, Manger halal, mosquées et centres voisins avec copie d’adresse et itinéraire, services publics et repères personnels avec liens réels, cartes « Pour bien s’installer », Étudier et scolariser) et onglet « Dua et annonces » : mur réel, table `dua_messages` (migration 0010), envoi public `POST /api/dua` (champ piège, délai minimal de 3 s, 5 envois par connexion en 15 min), compteur « J’ai fait une dua » (une fois par connexion et par jour), signalement qui retire le message jusqu’à relecture, modération `GET/PATCH/DELETE /api/admin/dua` (superadmin, editor), règles du mur (clé `dua` : longueur, délai, catégories, onglets, compteur, signature anonyme, pause) ; pages Ressources et N3-Dua (PC, M-, T-) reliées, mentions de brouillon retirées | en ligne |
| C | Contact : onglet « Page Contact » (clé `contact` : carte et coordonnées GPS, code postal, lignes pratiques modifiables, étiquette de visite en conseils, bouton Copier, lien Facebook des coordonnées générales, demandes particulières avec liens, sujets du formulaire, longueur maximale vérifiée aussi par `POST /api/forms`, page après envoi : remerciement, page du site ou une de mes pages) ; adresse, ville et courriel tirés de `home.general` ; onglet « Page 404 » (clé `p404` : titre, texte, raccourcis) et nouvelle page `404.html` servie par Cloudflare Pages pour toute adresse inconnue ; fausses options « Page : Merci » et « Ma page : Inscriptions Ramadan 2027 » retirées | en ligne |
| M1 | Photos : bloc « + Photo » de l'éditeur de pages ; envoi `POST /api/admin/media` (corps = fichier, 5 Mo au plus), format reconnu d'après le contenu (JPEG, PNG, WebP, GIF ; pas de SVG), nom aléatoire, fichier rangé dans KV `MEDIA` (clé = `file_key`) et fiche dans `media` (migration 0011) ; `GET /api/admin/media`, `DELETE /api/admin/media/:id` (superadmin, editor) ; photo servie par `GET /media/<nom>` (vrai type, nosniff, aucun script) ; texte alternatif obligatoire, légende, taille ; largeur et hauteur lues dans le fichier pour éviter les sauts de page | en ligne |
| M2 | Vidéos : bloc « + Vidéo » ; lien YouTube (lu par youtube-nocookie.com), Vimeo (dnt=1) ou Facebook, reconnu des deux côtés (`functions/_lib/video.js`) ; tout autre site refusé ; aperçu dans l'éditeur | en ligne |
| M3 | Widgets HTML / CSS / JS : bloc « + Widget » ; code rangé dans `page_widgets` (migration 0011), jamais dans la page ; servi seul par `GET /w/:id` avec CSP `sandbox allow-scripts` (origine opaque : pas d'accès à la session, aux cookies, aux données du site ni à la page qui l'affiche) et affiché dans `<iframe sandbox="allow-scripts">` ; sans l'interrupteur « Internet », aucune connexion possible (`connect-src 'none'`) ; création et modification `POST/PUT/DELETE /api/admin/widgets` réservées au superadmin, l'éditeur peut seulement placer un widget existant | en ligne |
| M4 | Python : langage « Python » du widget, exécuté par Pyodide 0.26.4 (cdn.jsdelivr.net) dans la même boîte isolée ; `print()` affiché sous le widget | en ligne |
| M5 | Formulaires : nouvelle rubrique `SA-Formulaires` (lien dans le menu de toutes les pages du panneau, avec le nombre de nouvelles réponses) ; tables `custom_forms` et `form_entries` (migration 0011) ; champs texte court, texte long, courriel, téléphone, nombre, date, liste, choix unique, cases à cocher (libellé, aide, obligatoire, choix, ordre) ; bloc « + Formulaire » de l'éditeur ; envoi public `POST /api/forms/custom/:id` par un vrai formulaire HTML (la page reste sans script) : champ piège, délai minimal de 3 s, 5 envois par connexion en 15 min, seuls les champs connus gardés et vérifiés selon leur type, retour sur la page avec le message de remerciement ou l'erreur ; réponses `GET/PATCH /api/admin/custom-forms/:id/entries` (superadmin, editor), suppression (superadmin) ; tableau avec filtre, recherche, statut, export CSV pour Excel (formules neutralisées) ; création et modification des formulaires réservées au superadmin | en ligne |
| V | Vérification finale : réglages communs (courriel, Facebook, carte, adresse, liens TCOM et CCIQ, lignes du pied de page, heures, bouton Itinéraire) appliqués sur les 59 pages publiques par un même script (`wire_pied.py`), et non plus seulement sur l'accueil ; ligne CCIQ masquée tant qu'elle n'a pas de lien ; morceau d'annonce orphelin retiré du panneau Accueil ; mentions de brouillon retirées de la page Inscription | en ligne |
| N | Nettoyage : libellés « Services (niveau 2) » et « Applications (niveau 3) » dans « Pages publiées », ligne CCIQ masquée dans la page tant qu'elle est vide (plus de lien « # »), lien Facebook de l'ASCIL appliqué aussi hors du pied de page, bouton « Revenir en haut » vers le haut de page, textes de réserve reformulés | en ligne |
| L1 | Langues : le sélecteur FR / العربية / English change vraiment de langue (choix gardé dans le navigateur, ou `?lang=ar` / `?lang=en` dans l'adresse) ; arabe de droite à gauche avec la police Cairo (`/fonts/cairo`, licence SIL OFL) ; en-tête, menus, pied de page, textes fixes des 59 pages, messages, dates et contenus par défaut traduits (786 textes) ; une langue désactivée dans Site entier → Langues n'est jamais appliquée. Les textes saisis dans le panneau restent en français (étape suivante) | en ligne |
| L2 | Traductions du panneau : nouvelle rubrique « Traductions » (superadmin et éditeur). Tous les textes saisis dans les rubriques, relus en direct, avec un champ arabe et un champ anglais ; filtre « À traduire », recherche ; correction des traductions des textes fixes ; retrait des traductions plus utilisées. Clé `traductions` (sans migration), lisible publiquement, appliquée par les pages publiques avant le dictionnaire du site. Les pages créées (/p/…) ne sont pas encore traduites | en ligne |
| P1 | Photos de l'Accueil : dans le panneau Accueil, cartes « Héros » et « Bienvenue aux visiteurs », un bloc Photo permet de choisir la photo (JPEG, PNG, WebP ou GIF, 5 Mo au plus), de la décrire et de remettre la photo d'origine. Clé `photos` (superadmin et éditeur, lisible publiquement), aucune migration. | en ligne |
| G | Page « Un site gratuit pour votre mosquée » (`/site-gratuit-mosquee`) en français, arabe et anglais, sans nom mis en avant ; absente du menu principal, lien discret dans le pied de page de toutes les pages publiques | en ligne |
| R1 | Thème Ramadan (maquettes « event templates ») : quand Site entier → Mode du site est sur Ramadan (dans ses dates si le changement automatique est coché), l'adresse de l'Accueil affiche l'Accueil Ramadan (`TH-Ramadan-Accueil.dc.html`, servi par `functions/_middleware.js`, sans redirection) et « Ramadan » apparaît dans le menu, vers la page du mois (`TH-Ramadan-Page.dc.html` : calendrier semaine par semaine, nuits du Qadr). Vraies données seulement : dates de `season`, heures de `/api/prayer-times` (iftar = Maghreb ; le mois renvoie maintenant `resolved`, les heures retenues de chaque jour), campagne et annonces de `home`. Imsak, Tarawih, programme, zakat, questions et iftars communautaires restent cachés jusqu'à la rubrique Ramadan du panneau (R2). Aucune migration | poussé |
| A1 | Thèmes Aïd al-Fitr et Aïd al-Adha (maquettes « event templates ») : même fonctionnement que le Ramadan. Mode du site sur l'un des deux Aïd → l'adresse de l'Accueil affiche `TH-Fitr-Accueil.dc.html` ou `TH-Adha-Accueil.dc.html`, et le menu propose « Aïd al-Fitr » ou « Aïd al-Adha » (pages `TH-Fitr-Page` et `TH-Adha-Page`). Vraies données : date, heure, lieu et itinéraire de Horaires → Aïd (sinon dates du Mode du site), zakat al-Fitr de la carte Aïd de Services ; dix jours, Arafat et Tachriq calculés depuis la date. Programme heure par heure, café, enfants, bénévoles, udhiya et prix, questions : cachés. Formulaires publics : message clair quand la table `form_messages` (migration 0009) manque. Aucune migration | poussé |
| AU1 | Corrections de l'audit du 9 nov. 2026 : (1) inscriptions aux événements : la page publique exécutait la fausse inscription de la maquette (code « IFT- » inventé, rien envoyé) ; elle envoie maintenant vraiment à `/api/events/register`, affiche le vrai code ASC-XXXX-XXXX, les places réelles et les erreurs du serveur (`scripts/wire_events.py`). (2) Champs du panneau (Accueil, À propos, Horaires, Services) : un champ redessiné reprenait la valeur de la maquette (ex. « 140 000 ») et l'enregistrement l'écrivait ; la vraie valeur est gardée et remise. (3) Campagne en direct : le montant s'affiche même quand l'onglet est en arrière-plan. (4) Tableau du mois : chaque jour affiche les heures retenues (`resolved`). (5) Ressources : « {x.texte} » n'apparaît plus. (6) Pages /p/ : l'adresse courriel ne devient plus « [email protected] », menu aligné sur le site (À propos). (7) Tableau de bord : nombre d'événements compté depuis Événements du panneau. Aucune migration | poussé |
| V1 | Thème du vendredi (maquette « joumoaa ») : Site entier → Mode du site → « Thème du vendredi » : Désactivé, Automatique (chaque vendredi, de minuit à minuit, heure de Edmundston) ou Activé tous les jours (champ `season.vendredi`). Actif : l'adresse de l'Accueil affiche `TH-Vendredi-Accueil.dc.html` (servi par `functions/_middleware.js`) ; pages `TH-Vendredi-Horaires` et `TH-Vendredi-Khutba` liées depuis cet Accueil, et menant aux pages normales quand le thème est éteint. Un mode Ramadan ou Aïd en cours passe avant. Vraies données : heures du tableau du mois, conseil d'arrivée (Horaires → Vendredi), langue, traduction et imam (Horaires → Langue de la khutba), campagne. Heures fixes, thème et résumé d'exemple, PDF, faux rappels : retirés. Aucune migration | fait, à pousser |
| 4 | Annonces, dons : API sur les tables existantes `announcements`, `donations`, `events` | à faire |

Les tables existantes ne sont jamais recréées : on les complète avec `ALTER TABLE`.

## Migrations

| Fichier | Contenu |
|---|---|
| `0001_superadmin_auth.sql` | complète `admins` (identifiant, mot de passe haché…), un seul superadmin ; `admin_sessions`, `login_attempts`, `audit_log` |
| `0002_comptes_roles.sql` | `admins.must_change_password`, `admins.created_by` |
| `0003_site_settings.sql` | `site_settings (key, value JSON, updated_at ISO, updated_by)` + clé `home` |
| `0004_page_views.sql` | `page_views (path, viewed_date, count)` : visites anonymes, sans cookie ni IP |
| `0005_event_registrations.sql` | `event_registrations` + clé `event_registration` |
| `0006_dates_iso_et_limites.sql` | `site_settings.updated_at` remis au format ISO ; `rate_limits` (limite des inscriptions publiques) |
| `0007_custom_pages.sql` | `custom_pages` (titre, lien unique, blocs JSON, visibilité, mise en page, largeur, description) ; `page_redirects` (ancienne adresse → page) |
| `0008_prayer_times.sql` | complète `prayer_times` : colonne `lever`, index unique `ux_prayer_times_date` (une ligne par jour, date AAAA-MM-JJ) |
| `0009_form_messages.sql` | nouvelle table `form_messages` (boîte de réception des formulaires publics : formulaire d'origine, nom, courriel ou téléphone, message, champs propres, statut) ; aucune table existante modifiée |
| `0010_dua_messages.sql` | nouvelle table `dua_messages` (mur Dua et annonces : type, catégorie, texte, signature, statut attente/publie/refuse, signalé, compteur de dua, dates) ; aucune table existante modifiée |
| `0011_medias_widgets_formulaires.sql` | nouvelles tables `media` (photos), `page_widgets` (code des widgets), `custom_forms` (formulaires créés) et `form_entries` (leurs réponses) ; aucune table existante modifiée |

Les migrations sont appliquées à la main dans la console D1. Après chaque application,
enregistrer la ligne correspondante dans `d1_migrations`, sinon `wrangler d1 migrations apply --remote`
tenterait de la rejouer (un `ALTER TABLE` rejoué échoue) :

```sql
INSERT OR IGNORE INTO d1_migrations (name) VALUES ('0006_dates_iso_et_limites.sql');
```

## Réglages (`site_settings`)

| Clé | Écrite par | Route | Lue par le public |
|---|---|---|---|
| `home` | superadmin, editor | `PUT /api/admin/settings/home` | `GET /api/settings/home` |
| `pages` | superadmin, editor | `PUT /api/admin/settings/pages` | `GET /api/settings/pages` + middleware |
| `alert` | superadmin, editor | `PUT /api/admin/settings/alert` | `GET /api/settings/alert` |
| `season` | superadmin, editor | `PUT /api/admin/settings/season` | `GET /api/settings/season` (accueil) |
| `languages` | superadmin, editor | `PUT /api/admin/settings/languages` | `GET /api/settings/languages` |
| `horaires` | superadmin, editor | `PUT /api/admin/settings/horaires` | `GET /api/settings/horaires` (page Horaires) |
| `khutba` | superadmin, editor | `PUT /api/admin/settings/khutba` | `GET /api/settings/khutba` (page Langue de la khutba) |
| `rappel` | superadmin, editor | `PUT /api/admin/settings/rappel` | `GET /api/settings/rappel` (page Rappel de prière) |
| `apropos` | superadmin, editor | `PUT /api/admin/settings/apropos` (corps jusqu’à 1 Mo : photos) | `GET /api/settings/apropos` (page À propos) |
| `services` | superadmin, editor | `PUT /api/admin/settings/services` | `GET /api/settings/services` (page Services) |
| `cours`, `mariages`, `funerailles`, `aide`, `femmes` | superadmin, editor | `PUT /api/admin/settings/<clé>` (`femmes` jusqu’à 400 Ko : plan d’accès) | `GET /api/settings/<clé>` (pages N2 correspondantes) ; nettoyées d’après `SERVICE_PAGE_SCHEMAS` |
| `dons`, `merci` | superadmin, editor | `PUT /api/admin/settings/<clé>` | `GET /api/settings/<clé>` (page Dons) ; nettoyées d’après `DONS_SCHEMA` et `MERCI_SCHEMA` |
| `evenements`, `calendrier` | superadmin, editor, events | `PUT /api/admin/settings/<clé>` | `GET /api/settings/<clé>` (pages Événements et Calendrier, annonces de l’accueil) ; nettoyées d’après `EVENEMENTS_SCHEMA` et `CALENDRIER_SCHEMA` |
| `ressources`, `dua` | superadmin, editor | `PUT /api/admin/settings/<clé>` | `GET /api/settings/<clé>` (page Ressources) et `GET /api/dua` (règles et messages publiés du mur) ; nettoyées d’après `RESSOURCES_SCHEMA` et `DUA_SCHEMA` |
| `contact`, `p404` | superadmin, editor | `PUT /api/admin/settings/<clé>` | `GET /api/settings/<clé>` (page Contact, page 404) ; nettoyées d’après `CONTACT_SCHEMA` et `P404_SCHEMA` |
| `campagne` | superadmin, editor | `PUT /api/admin/settings/campagne` | `GET /api/campagne` (calculé : objectif et récolté de `home`, ou totaux de `donations` en mode automatique) |
| `event_registration` | superadmin, events | `PUT /api/admin/events/settings` | `GET /api/events/registration-info` |

La route générique `/api/admin/settings/:key` n'accepte que les clés de `GENERIC_KEYS`
(`functions/_lib/settings.js`), chacune avec ses rôles et sa validation : aucune clé arbitraire.
La lecture publique `/api/settings/:key` est limitée à `PUBLIC_KEYS` (`home`, `pages`, `alert`, `season`, `languages`, `horaires`, `khutba`, `rappel`, `apropos`).
En mode automatique de la campagne, `GET /api/settings/home` et le tableau de bord renvoient le montant récolté calculé depuis `donations` (tous les dons de la table).

Horaires : les heures sont dans `prayer_times` (une ligne par jour) ; une case vide prend la valeur par défaut de la carte
« Prochaine prière » de l'Accueil (`home.priere` : Fajr 06:30, Jumu'a 12:30, Icha 19:00), puis « — ». Les dates du Ramadan viennent de la clé `season`.
Routes du tableau mensuel : `GET`/`PUT /api/admin/prayer-times` (ou `/:month`, superadmin + éditeur) et `GET /api/prayer-times` (ou `/today`, `/:month`, `/:date`, publique sans authentification).

Liens de l'accueil (`home`) : seuls « Page : … », `/p/<lien>` et `https://…` sont acceptés ; toute autre valeur
revient à la valeur par défaut. La bannière accepte aussi un lien vers une page créée (`{ type: 'custom', slug }`).

Limites connues : le mode du site ne change pas les couleurs du site (pas de variables de couleur),
et les textes ne sont pas traduits : les langues ne règlent que ce que propose le sélecteur.
`updated_at` est toujours une date ISO, `updated_by` l'id du compte.

## Routes

- **Authentification** (`functions/api/auth/`)
  - `POST login`, `POST logout`, `GET me`, `POST password` ;
  - `GET sessions` liste les appareils connectés, `DELETE sessions` déconnecte les autres.
- **Comptes** (`/api/admin/accounts`, superadmin) : liste, création avec mot de passe provisoire, modification, désactivation, réinitialisation.
- **Journal** (`GET /api/admin/audit`, superadmin) : les dernières actions, affichées dans Site entier → Compte et sécurité.
- **Pages créées** (`/api/admin/pages`, superadmin et éditeur) :
  - `GET` liste, `POST { title, slug?, visibility? }` crée une page (en brouillon par défaut ; lien tiré du titre et rendu unique s'il n'est pas fourni) ;
  - `GET/PUT/DELETE /api/admin/pages/:id` ; changer le lien crée une redirection depuis l'ancien ;
  - `POST /api/admin/pages/:id/duplicate` (copie en brouillon) ;
  - règles (lien, blocs Texte / Bouton / Tableau, limites) dans `functions/_lib/custom-pages.js`.
- **Pages publiques** : `GET /p/<lien>` (`functions/p/[slug].js`), rendu serveur sans script
  (`functions/_lib/render-page.js`) : publiée = visible et indexée ; lien privé = visible, jamais indexée ;
  brouillon = comptes connectés seulement (bandeau), sinon page introuvable ; ancienne adresse = 301 ;
  mise en page « avec menu et pied » = en-tête, pied et bannière d'alerte du site ; « vierge » = sans.
- **Réglages, valeurs d'origine** : `GET /api/admin/settings/:key?defaults=1` (sans rien enregistrer).
- **Statistiques** : `GET /api/admin/stats`.
- **Visites** : `POST /api/views`, qui ne compte que les pages connues du site.
- **Événements, côté public** :
  - `GET /api/events/registration-info` ;
  - `POST /api/events/register` : 5 inscriptions par IP en 15 min, code `ASC-` suivi de deux groupes de 4 caractères tiré par `crypto.getRandomValues`, places vérifiées et réservées en une seule requête SQL (pas de dépassement de jauge).
- **Événements, côté admin** :
  - `GET/PUT /api/admin/events/settings` ;
  - `GET /api/admin/events/registrations` : liste nominative pour le superadmin et le responsable événements, synthèse chiffrée seulement pour l'éditeur ;
  - `DELETE /api/admin/events/registrations` ;
  - `GET /api/admin/events/export` (CSV, superadmin et responsable événements).
  - Toutes ces routes ne portent que sur l'événement en cours (`event_slug`).

Rôles et pages autorisées : `functions/_lib/roles.js` (superadmin : tout ; editor : tout sauf Comptes ;
events : Événements seulement). Le middleware renvoie chaque rôle vers sa page s'il en ouvre une autre.

## Scripts de génération des pages : ordre obligatoire

Les pages `SA-*` sont générées depuis la planche d’origine (`superadmin.html`), puis « branchées » sur l'API par des scripts qui
modifient les pages générées. Régénérer sans rebrancher efface les branchements.

1. `scripts/install_superadmin.py /Users/mac/Documents/mosque/superadmin.html .` régénère les pages `SA-*`.
   **Il relance lui-même les étapes 2 à 25**, sauf avec `--sans-branchements`.
2. `scripts/wire_ramadan.py` : **en premier**. Reconstruit `TH-Ramadan-Accueil.dc.html` et `TH-Ramadan-Page.dc.html` depuis les maquettes gardées dans `scripts/maquettes/` (seul le modèle change, l'enveloppe du fichier reste), les relie aux vraies données et ajoute le script `#ascil-ramadan-menu` (lien de la saison : Ramadan ou Aïd) aux pages publiques ; les étapes suivantes y ajoutent leurs scripts communs (langues, pied de page, bannière d'alerte).
3. `scripts/wire_aid.py` : juste après wire_ramadan. Reconstruit `TH-Fitr-Accueil`, `TH-Fitr-Page`, `TH-Adha-Accueil` et `TH-Adha-Page` (`.dc.html`) depuis les maquettes de `scripts/maquettes/`, reliées à Horaires → Aïd, Services (zakat) et au Mode du site.
4. `scripts/wire_homepage.py` : accueil public (réglages, visites), panneau Accueil, bandeau statistiques.
   Il remplace la logique du panneau par `scripts/panneau_component.js` (état unique : interrupteurs,
   ordre, cartes, annonces, heures) ; le script `#sa-panneau-sync` enregistre via `window.__saHome`.
5. `scripts/wire_events.py` : inscriptions publiques, panneau Événements.
6. `scripts/wire_site.py` : tout Site entier (pages publiées, mode du site, langues, bannière d'alerte, compte et sécurité),
   et sur le site public : masquage des pages, bannière d'alerte, sélecteur de langues, bandeau de saison (accueil).

7. `scripts/wire_pages.py` : Créer une page (« Mes pages » et l'éditeur `SA-PageEditeur.dc.html?id=<page>`),
   et les liens de l'accueil (pages créées proposées, « Lien externe… » qui demande l'adresse).
8. `scripts/wire_horaires.py` : panneau `SA-Horaires` (« Horaires du mois » : choix du mois courant + 2 suivants,
   tableau mensuel éditable relié à `/api/admin/prayer-times/:month`, « Copier une heure sur tout le mois »,
   « Coller depuis Excel », réglages reliés à `horaires`, dates Ramadan lues depuis `season`, Jumu'a lu/écrit dans le tableau mensuel).
9. `scripts/wire_prieres.py` : les 58 pages publiques, heures de prière tirées de la base (`GET /api/prayer-times`) ; page Horaires :
   tableau du mois, cartes et réglages `horaires`. Le script `#ascil-prayer-live` range les données dans `window.__ascilPrayer`
   et prévient la page (événement `ascil:prayer`).
10. `scripts/wire_apropos.py` : panneau `SA-APropos` (clés `apropos`, `campagne`, objectif et récolté de `home`)
   et pages publiques APropos et N3-Campagne (données de `/api/settings/apropos` et `/api/campagne`, relues chaque minute sur la campagne).
11. `scripts/wire_services.py` : panneau `SA-Services` (clé `services`, lieu de l'Aïd dans `horaires`, pages publiées) et page publique Services
12. `scripts/wire_service_pages.py` : onglets 2 à 6 de `SA-Services` (moteur commun construit d’après la description des champs) et les 15 pages N2 des services
13. `scripts/wire_dons.py` : onglets « Page Dons » et « Bloc Merci » de `SA-Dons` (même moteur que les Services) et les 3 pages Dons
14. `scripts/wire_evenements.py` : panneau `SA-Evenements` (onglets Annonces, Calendrier, Inscription avec inscrits, export et annulation), renvoi « Dernières annonces » du panneau Accueil, pages Événements et N3-Calendrier
15. `scripts/wire_ressources.py` : panneau `SA-Ressources` (onglets Nouveaux arrivants et Dua et annonces avec modération), pages Ressources et N3-Dua
16. `scripts/wire_inbox.py` : onglet « Demandes reçues » de `SA-Contact` et formulaire de la page Contact
17. `scripts/wire_contact.py` : onglets « Page Contact » et « Page 404 » de `SA-Contact`, pages Contact et nouvelle page `404.html` (construite depuis Contact, liens absolus)
18. `scripts/wire_formulaires.py` : nouvelle page `SA-Formulaires` (construite depuis `SA-Pages` déjà reliée), lien « Formulaires » dans le menu de toutes les pages du panneau et de `SA-Comptes.html`
19. `scripts/wire_traductions.py` : nouvelle page `SA-Traductions` (construite depuis `SA-Pages`) : textes saisis dans le panneau, textes fixes du site et traductions plus utilisées, chacun avec un champ arabe et un champ anglais, enregistrés dans la clé `traductions` ; lien « Traductions » dans le menu de toutes les pages du panneau
20. `scripts/wire_pied.py` : réglages communs (coordonnées et pied de page) sur toutes les pages publiques, nettoyage de la page Inscription, aide du champ CCIQ
21. `scripts/wire_nettoyage.py` : dernières mentions de brouillon retirées (bouton « Revenir en haut », lieu de l'Aïd vide, certification halal, description du panneau Services)
22. `scripts/wire_photos.py` : photos de l'Accueil (grande photo du haut et photo « Vous venez pour la première fois ? ») choisies dans le panneau Accueil, cartes Héros et Bienvenue aux visiteurs ; envoi par `/api/admin/media`, chemin gardé dans la clé `photos` ; script `#ascil-photos-live` sur les 4 versions de l'Accueil
23. `scripts/wire_langues.py` : versions arabe et anglaise. Construit `i18n/ar.json` et `i18n/en.json` depuis `scripts/i18n/strings.json` et `scripts/i18n/*.tsv` (français, arabe, anglais), installe le script commun `#ascil-i18n` sur les 59 pages publiques et liste dans `scripts/i18n-a-traduire.txt` les textes fixes encore sans traduction
24. `scripts/wire_gratuit.py` : page publique `site-gratuit-mosquee.html` (adresse `/site-gratuit-mosquee`), construite depuis `404.html`, en trois langues (textes dans `scripts/i18n/lot-gratuit.tsv`) ; lien discret dans le pied de page de toutes les pages publiques ; pas dans le menu principal
25. `scripts/fix_inputs.py` : **toujours en dernier**. Les pages sont rendues par React : un champ écrit
   avec `value="…"` dans la planche d’origine devient « contrôlé » et refuse toute saisie (impossible d'écrire ou
   de choisir une date). Le script transforme ces valeurs en valeurs de départ (`defaultValue`,
   `defaultChecked`). Le contenu des balises `<script>` n'est pas touché (champs construits en HTML par les panneaux). Les scripts 2 à 24 s'appuient sur les attributs d'origine, d'où cet ordre.

Les scripts 2 à 24 peuvent être relancés seuls autant de fois que nécessaire : ils remplacent
leurs propres ajouts au lieu de les dupliquer.

Autres scripts : `scripts/create-superadmin.mjs` (`--sql` pour la console D1, `--reset` pour un nouveau mot de passe).

## Sécurité

- Mots de passe : PBKDF2-SHA256, 100 000 itérations, sel aléatoire, hachés côté serveur (ou sur le Mac pour le superadmin).
- Sessions : jeton de 256 bits, seule son empreinte SHA-256 est stockée ; 12 h, ou 30 jours avec « Rester connecté ».
- Connexion : 5 échecs en 15 minutes, par IP ou par identifiant, bloquent pendant 15 minutes.
- Écritures refusées si elles ne viennent pas du site (en-tête `Origin`).
- `functions/`, `migrations/`, `scripts/`, `wrangler.toml` ne sont jamais servis.
- `_routes.json` limite les Functions à l'API, au superadmin, aux pages publiques masquables et à `/p/*`.
- `/p/<lien>` : en-tête `Content-Security-Policy` sans aucun script, tout texte échappé.
