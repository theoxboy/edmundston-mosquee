-- Étape 2 : Réglages du site (accueil et autres pages)
CREATE TABLE IF NOT EXISTS site_settings (
  key        TEXT PRIMARY KEY,
  value      TEXT NOT NULL,                            -- JSON
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
  updated_by INTEGER REFERENCES admins(id)
);
CREATE INDEX IF NOT EXISTS idx_site_settings_updated ON site_settings(updated_at);

-- Réglages initiaux pour la page d'accueil du Centre Islamique d'Edmundston
INSERT OR IGNORE INTO site_settings (key, value) VALUES (
  'home',
  '{
    "general": {
      "email": "",
      "facebook": "",
      "address": "34, 37e Avenue",
      "city": "Edmundston, NB E3V 3S2",
      "mapUrl": "https://maps.google.com/?q=34+37e+Avenue+Edmundston+NB+E3V+3S2"
    },
    "ordre": ["acces", "campagne", "annonces", "bienvenue", "invitation"],
    "on": {
      "chargement": true, "bandeau": true, "compte": true, "mail": true, "fb": true,
      "don": true, "langue": true, "horaires": true, "apropos": true, "services": true,
      "evenements": true, "ressources": true, "contact": true, "hero": true, "priere": true,
      "hegirien": true, "progression": true, "puces": true, "acces": true, "campagne": false,
      "barre": false, "annonces": true, "bienvenue": true, "invitation": true, "haut": true,
      "pHor": true, "pIti": true, "pFb": false, "pTcom": false, "pCciq": false, "pMail": false
    },
    "chargement": {
      "duration": "normale"
    },
    "hero": {
      "h1": "Page : Horaires du mois",
      "h2": "Page : Faire un don"
    },
    "priere": {
      "fajr": "",
      "lever": "",
      "dohr": "",
      "jumua": "",
      "asr": "",
      "maghreb": "",
      "icha": ""
    },
    "acces": {
      "cartes": [
        { "id": "vendredi", "on": true, "lien": "Page : Horaires du mois" },
        { "id": "trouver", "on": true, "lien": "Page : Contact" },
        { "id": "campagne", "on": false, "lien": "Page : Faire un don" }
      ]
    },
    "campagne": {
      "objectif": 0,
      "recolte": 0,
      "btnInterac": "",
      "btnSuivre": ""
    },
    "annonces": {
      "max": 3,
      "btnTous": "Page : Événements",
      "items": []
    },
    "bienvenue": {
      "lien": "Page : Contact"
    },
    "invitation": {
      "lien": "Page : Contact"
    },
    "pied": {
      "tcom": "",
      "cciq": ""
    }
  }'
);
