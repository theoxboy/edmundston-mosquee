-- Migration 0005 : Inscriptions aux événements (étape 2c)

CREATE TABLE IF NOT EXISTS event_registrations (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  event_slug      TEXT    NOT NULL DEFAULT '',
  event_title     TEXT    NOT NULL,
  code            TEXT    NOT NULL UNIQUE,
  name            TEXT    NOT NULL,
  contact         TEXT    NOT NULL,
  attendees_count INTEGER NOT NULL DEFAULT 1,
  is_vegetarian   INTEGER NOT NULL DEFAULT 0,
  status          TEXT    NOT NULL DEFAULT 'confirmed', -- 'confirmed', 'cancelled'
  notes           TEXT,
  created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_reg_event ON event_registrations(event_slug, status);
CREATE INDEX IF NOT EXISTS idx_reg_code  ON event_registrations(code);
CREATE INDEX IF NOT EXISTS idx_reg_date  ON event_registrations(created_at);

-- Initialise les réglages par défaut de la jauge et de l'événement si non existants
INSERT OR IGNORE INTO site_settings (key, value, updated_at)
VALUES (
  'event_registration',
  '{"event_slug":"","event_title":"[À compléter]","date_str":"","location":"34, 37e Avenue, Edmundston, NB E3V 3S2","description":"","total_seats":0,"max_per_reg":1,"deadline":"","is_open":false,"opt_vege":false,"opt_code":false,"opt_agenda":false}',
  strftime('%s', 'now')
);
