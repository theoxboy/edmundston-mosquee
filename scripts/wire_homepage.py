"""Branchement dynamique de la page d'accueil, des statistiques (étape 2b) et du panneau superadmin.

1. SA-Panneau.dc.html (la logique de la page est remplacée par scripts/panneau_component.js) :
   - Bandeau synthétique des statistiques réelles (Campagne, Visites, Événements, Sécurité)
   - Pré-remplit les champs et réglages depuis GET /api/admin/settings/home
   - Récupère les métriques en direct depuis GET /api/admin/stats
   - Détecte toute modification (texte, sélecteurs, interrupteurs, ordre)
   - Sauvegarde vers PUT /api/admin/settings/home lors du clic sur « Enregistrer »
   - Rétablit les valeurs en cas de clic sur « Annuler »

2. Main.dc.html, index.html, M-Accueil.dc.html, T-Accueil.dc.html :
   - Enregistre anonymement la visite via POST /api/views (sans cookies, sans IP)
   - Charge les réglages depuis le cache immédiat (localStorage) et l'API GET /api/settings/home
   - Applique en direct :
     • Coordonnées (adresse, courriel, facebook, lien itinéraire)
     • Heures de prière et calcul dynamique de la prochaine prière (compte à rebours, puces, footer, menu)
     • Campagne nouveau lieu (objectif, récolté, pourcentage, barre de progression)
     • Dernières annonces (titres, dates, résumés, liens)
     • Affichage / masquage de tous les widgets
     • Réordonnancement dynamique des 5 sections modulaires selon settings.ordre
"""

import json, re, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent

STATS_BANNER_HTML = r'''   <!-- Bandeau des statistiques réelles (étape 2b) -->
   <div id="sa-stats-banner" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin:2px 0 6px">
    <div style="background:#fff;border:1px solid #E4D9C0;border-radius:14px;padding:14px 16px;display:flex;flex-direction:column;gap:3px">
     <div style="display:flex;align-items:center;justify-content:space-between;color:#7A5A1E;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.08em">
      <span>Campagne</span>
      <span style="display:inline-flex;color:#7A5A1E"><svg aria-hidden="true" width="18" height="18" sc-camel-view-box="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 7V4a1 1 0 0 0-1-1H5a2 2 0 0 0 0 4h15a1 1 0 0 1 1 1v4h-3a2 2 0 0 0 0 4h3a1 1 0 0 0 1-1v-2a1 1 0 0 0-1-1"></path><path d="M3 5v14a2 2 0 0 0 2 2h15a1 1 0 0 0 1-1v-4"></path></svg></span>
     </div>
     <div id="stat-campagne-val" style="font-size:20px;font-weight:800;color:#0E4D3C" class="tnum">—</div>
     <div id="stat-campagne-sub" style="font-size:12px;color:#4F5E57" class="tnum">—</div>
    </div>
    <div style="background:#fff;border:1px solid #E4D9C0;border-radius:14px;padding:14px 16px;display:flex;flex-direction:column;gap:3px">
     <div style="display:flex;align-items:center;justify-content:space-between;color:#7A5A1E;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.08em">
      <span>Visites du site</span>
      <span style="display:inline-flex;color:#7A5A1E"><svg aria-hidden="true" width="18" height="18" sc-camel-view-box="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2.062 12.348a1 1 0 0 1 0-.696 10.75 10.75 0 0 1 19.876 0 1 1 0 0 1 0 .696 10.75 10.75 0 0 1-19.876 0"></path><circle cx="12" cy="12" r="3"></circle></svg></span>
     </div>
     <div id="stat-visits-val" style="font-size:20px;font-weight:800;color:#0E4D3C" class="tnum">—</div>
     <div id="stat-visits-sub" style="font-size:12px;color:#4F5E57" class="tnum">—</div>
    </div>
    <div style="background:#fff;border:1px solid #E4D9C0;border-radius:14px;padding:14px 16px;display:flex;flex-direction:column;gap:3px">
     <div style="display:flex;align-items:center;justify-content:space-between;color:#7A5A1E;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.08em">
      <span>Événements</span>
      <span style="display:inline-flex;color:#7A5A1E"><svg aria-hidden="true" width="18" height="18" sc-camel-view-box="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8 2v4"></path><path d="M16 2v4"></path><rect width="18" height="18" x="3" y="4" rx="2"></rect><path d="M3 10h18"></path></svg></span>
     </div>
     <div id="stat-events-val" style="font-size:20px;font-weight:800;color:#0E4D3C" class="tnum">—</div>
     <div id="stat-events-sub" style="font-size:12px;color:#4F5E57" class="tnum">—</div>
    </div>
    <div id="stat-card-sec" style="background:#fff;border:1px solid #E4D9C0;border-radius:14px;padding:14px 16px;display:flex;flex-direction:column;gap:3px">
     <div style="display:flex;align-items:center;justify-content:space-between;color:#7A5A1E;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.08em">
      <span>Sécurité & Accès</span>
      <span style="display:inline-flex;color:#7A5A1E"><svg aria-hidden="true" width="18" height="18" sc-camel-view-box="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"></path></svg></span>
     </div>
     <div id="stat-sec-val" style="font-size:20px;font-weight:800;color:#0E4D3C" class="tnum">—</div>
     <div id="stat-sec-sub" style="font-size:12px;color:#4F5E57" class="tnum">—</div>
    </div>
   </div>'''

PANNEAU_SYNC_SCRIPT = r'''<script id="sa-panneau-sync">
(function() {
  // Panneau Accueil : enregistrement réel (PUT /api/admin/settings/home) et statistiques.
  // Les interrupteurs, l'ordre, les cartes, les annonces et les heures vivent dans la logique de la
  // page (window.__saHome, voir scripts/panneau_component.js) ; ce script gère les autres champs.
  var lastSettings = null;
  var DOM_FIELDS = ['f-mail', 'f-fb', 'f-adr', 'f-ville', 'f-map', 'f-dur', 'f-h1', 'f-h2', 'f-obj', 'f-rec',
    'f-int', 'f-sui', 'f-tous', 'f-bv', 'f-inv', 'f-tcom', 'f-cciq'];

  function bridge() { return window.__saHome; }
  function toast(msg) { var b = bridge(); if (b) b.flash(msg); }
  // Valeurs réelles des champs : la page peut redessiner une carte, et un champ redessiné reprend la
  // valeur de la maquette (ex. « 20 000 »). On garde donc la vraie valeur ici, on la remet dès qu'un
  // champ réapparaît, et on la lit même quand le champ n'est pas affiché.
  var cur = {};
  function setVal(id, v) {
    if (v == null) return;
    cur[id] = String(v);
    var el = document.getElementById(id);
    if (el) { el.value = cur[id]; el.setAttribute('data-sa-v', '1'); }
  }
  function getVal(id) {
    var el = document.getElementById(id);
    if (el && el.getAttribute('data-sa-v') === '1') return el.value.trim();
    return Object.prototype.hasOwnProperty.call(cur, id) ? String(cur[id]).trim() : (el ? el.value.trim() : '');
  }
  document.addEventListener('input', function(e) {
    var t = e.target;
    if (t && t.id && DOM_FIELDS.indexOf(t.id) > -1) { cur[t.id] = t.value; t.setAttribute('data-sa-v', '1'); }
  }, true);
  document.addEventListener('change', function(e) {
    var t = e.target;
    if (t && t.id && DOM_FIELDS.indexOf(t.id) > -1) { cur[t.id] = t.value; t.setAttribute('data-sa-v', '1'); }
  }, true);
  var refillT = null;
  new MutationObserver(function() {
    clearTimeout(refillT);
    refillT = setTimeout(function() {
      DOM_FIELDS.forEach(function(id) {
        var el = document.getElementById(id);
        if (el && el.getAttribute('data-sa-v') !== '1' && Object.prototype.hasOwnProperty.call(cur, id)) {
          el.value = cur[id]; el.setAttribute('data-sa-v', '1');
        }
      });
    }, 0);
  }).observe(document.documentElement, { childList: true, subtree: true });
  function fmt(n) { return String(n || 0).replace(/\B(?=(\d{3})+(?!\d))/g, ' '); }
  function api(url, opt) {
    return fetch(url, Object.assign({ credentials: 'same-origin', headers: { 'Content-Type': 'application/json' } }, opt || {}))
      .then(function(r) { return r.json().catch(function() { return { ok: false }; }); });
  }

  function loadStats() {
    fetch('/api/admin/stats', { credentials: 'same-origin' })
      .then(function(r) { return r.ok ? r.json() : null; })
      .then(function(d) {
        if (!d || !d.ok) return;

        // 1. Campagne
        if (d.campagne) {
          var cVal = document.getElementById('stat-campagne-val');
          var cSub = document.getElementById('stat-campagne-sub');
          if (cVal) cVal.textContent = (d.campagne.recolte || 0).toLocaleString('fr-CA') + ' $';
          if (cSub) cSub.textContent = (d.campagne.pct || 0) + ' % de ' + (d.campagne.objectif || 0).toLocaleString('fr-CA') + ' $';
        }

        // 2. Visites
        if (d.visits) {
          var vVal = document.getElementById('stat-visits-val');
          var vSub = document.getElementById('stat-visits-sub');
          if (vVal) vVal.textContent = (d.visits.total || 0).toLocaleString('fr-CA') + ' visites';
          if (vSub) vSub.textContent = (d.visits.today || 0) + ' aujourd’hui · ' + (d.visits.week || 0) + ' ces 7 jours';
        }

        // 3. Événements
        if (d.events) {
          var eVal = document.getElementById('stat-events-val');
          var eSub = document.getElementById('stat-events-sub');
          if (eVal) eVal.textContent = (d.events.count || 0) + ' événement(s)';
          if (eSub) eSub.textContent = (d.events.registrations || 0) + ' inscription(s)';
        }

        // 4. Sécurité
        var secCard = document.getElementById('stat-card-sec');
        if (d.security) {
          if (secCard) secCard.style.display = '';
          var sVal = document.getElementById('stat-sec-val');
          var sSub = document.getElementById('stat-sec-sub');
          if (sVal) sVal.textContent = (d.security.activeAdmins || 0) + ' compte(s) actif(s)';
          if (sSub) sSub.textContent = (d.security.activeSessions || 0) + ' session(s) · ' + (d.security.recentFailures || 0) + ' échec récent';
        } else if (secCard) {
          secCard.style.display = 'none';
        }
      })
      .catch(function() {});
  }
  function populateDom(s) {
    if (!s) return;
    if (s.general) {
      setVal('f-mail', s.general.email); setVal('f-fb', s.general.facebook); setVal('f-adr', s.general.address);
      setVal('f-ville', s.general.city); setVal('f-map', s.general.mapUrl);
    }
    if (s.chargement) setVal('f-dur', s.chargement.duration === 'rapide' ? 'Rapide (environ 1,5 s)' : 'Normale (environ 3 s)');
    if (s.hero) { setVal('f-h1', s.hero.h1); setVal('f-h2', s.hero.h2); }
    if (s.campagne) {
      setVal('f-obj', fmt(s.campagne.objectif || 0)); setVal('f-rec', fmt(s.campagne.recolte || 0));
      setVal('f-int', s.campagne.btnInterac); setVal('f-sui', s.campagne.btnSuivre);
    }
    if (s.annonces) setVal('f-tous', s.annonces.btnTous);
    if (s.bienvenue) setVal('f-bv', s.bienvenue.lien);
    if (s.invitation) setVal('f-inv', s.invitation.lien);
    if (s.pied) { setVal('f-tcom', s.pied.tcom); setVal('f-cciq', s.pied.cciq); }
  }

  function collect() {
    var num = function(v) { return parseInt(String(v || '').replace(/[^\d]/g, ''), 10) || 0; };
    var part = bridge().part();
    return {
      general: { email: getVal('f-mail'), facebook: getVal('f-fb'), address: getVal('f-adr'), city: getVal('f-ville'), mapUrl: getVal('f-map') },
      ordre: part.ordre,
      on: part.on,
      chargement: { duration: getVal('f-dur').toLowerCase().indexOf('rapide') > -1 ? 'rapide' : 'normale' },
      hero: { h1: getVal('f-h1'), h2: getVal('f-h2') },
      priere: part.priere,
      acces: { cartes: part.cartes },
      campagne: { objectif: num(getVal('f-obj')), recolte: num(getVal('f-rec')), btnInterac: getVal('f-int'), btnSuivre: getVal('f-sui') },
      annonces: { max: part.max, btnTous: getVal('f-tous'), items: part.items },
      bienvenue: { lien: getVal('f-bv') },
      invitation: { lien: getVal('f-inv') },
      pied: { tcom: getVal('f-tcom'), cciq: getVal('f-cciq') }
    };
  }

  function check(p) {
    if (!p.campagne.objectif) return 'Indiquez l’objectif de la campagne (en dollars), par exemple 50 000.';
    if (p.general.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(p.general.email)) return 'Le courriel de l’association n’est pas valide. Exemple : nom@exemple.com';
    var bad = p.annonces.items.filter(function(a) { return a.on && !a.titre; });
    if (bad.length) return 'Une annonce affichée n’a pas de titre. Donnez-lui un titre ou masquez-la.';
    return '';
  }

  window.saHomeSave = function() {
    var b = bridge();
    if (!b || b.state.saving) return;
    var payload = collect();
    var err = check(payload);
    if (err) { toast(err); return; }
    b.setState({ saving: true });
    api('/api/admin/settings/home', { method: 'PUT', body: JSON.stringify(payload) }).then(function(d) {
      if (!d.ok) { b.setState({ saving: false }); toast(d.message || 'La sauvegarde a échoué. Réessayez.'); return; }
      lastSettings = JSON.parse(JSON.stringify(d.settings));
      populateDom(d.settings);
      b.load(d.settings);
      b.commit();
      toast('Réglages enregistrés. L’accueil du site est à jour.');
      loadStats();
    }, function() { b.setState({ saving: false }); toast('Impossible de joindre le serveur. Vérifiez votre connexion et réessayez.'); });
  };

  window.saHomeUndo = function() {
    var b = bridge();
    if (!b) return;
    if (lastSettings) populateDom(lastSettings);
    b.revert();
    toast('Changements annulés.');
  };

  // Menu « … » ---------------------------------------------------------------
  window.saHomeExport = function() {
    if (!bridge()) return;
    var blob = new Blob([JSON.stringify(collect(), null, 2)], { type: 'application/json' });
    var a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'reglages-accueil-edmundston-' + new Date().toISOString().slice(0, 10) + '.json';
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(function() { URL.revokeObjectURL(a.href); }, 1000);
    toast('Réglages exportés : le fichier .json est dans vos téléchargements.');
  };

  window.saHomeImport = function() {
    var input = document.createElement('input');
    input.type = 'file'; input.accept = 'application/json,.json';
    input.addEventListener('change', function() {
      var f = input.files && input.files[0];
      if (!f) return;
      if (f.size > 200 * 1024) { toast('Fichier trop lourd : un fichier de réglages fait quelques ko.'); return; }
      f.text().then(function(txt) {
        var s;
        try { s = JSON.parse(txt); } catch (e) { s = null; }
        if (!s || typeof s !== 'object' || !s.general || !s.on) {
          toast('Ce fichier n’est pas un export des réglages de l’accueil. Choisissez un fichier exporté depuis ce panneau.');
          return;
        }
        populateDom(s);
        bridge().apply(s);
        toast('Réglages importés dans le panneau. Vérifiez-les, puis cliquez sur « Enregistrer » pour les mettre en ligne.');
      });
    });
    input.click();
  };

  window.saHomeReset = function() {
    if (!window.confirm('Remettre tous les réglages de l’accueil à leurs valeurs d’origine ?\n\nRien n’est mis en ligne tant que vous ne cliquez pas sur « Enregistrer ». « Annuler » revient aux réglages actuels.')) return;
    api('/api/admin/settings/home?defaults=1').then(function(d) {
      if (!d.ok) { toast(d.message || 'Impossible de charger les valeurs d’origine.'); return; }
      populateDom(d.settings);
      bridge().apply(d.settings);
      toast('Valeurs d’origine chargées dans le panneau. Cliquez sur « Enregistrer » pour les mettre en ligne.');
    }, function() { toast('Impossible de joindre le serveur. Réessayez.'); });
  };

  // Champs gérés ici : toute modification rend la page « non enregistrée ».
  function onField(e) {
    var t = e.target;
    if (t && DOM_FIELDS.indexOf(t.id) > -1 && bridge()) bridge().markExt();
  }
  document.addEventListener('input', onField);
  document.addEventListener('change', onField);

  function init() {
    api('/api/admin/settings/home').then(function(d) {
      if (!d.ok) { toast(d.message || 'Impossible de charger les réglages de l’accueil. Rechargez la page.'); return; }
      lastSettings = JSON.parse(JSON.stringify(d.settings));
      populateDom(d.settings);
      bridge().load(d.settings);
    }, function() { toast('Impossible de joindre le serveur. Rechargez la page.'); });
    loadStats();
  }
  function ready() { return window.__saHome && document.getElementById('f-mail'); }
  if (ready()) init();
  else {
    var obs = new MutationObserver(function() { if (ready()) { obs.disconnect(); init(); } });
    obs.observe(document.documentElement, { childList: true, subtree: true });
  }
})();
</script>
'''

PUBLIC_HOME_SYNC_SCRIPT = r'''<script id="ascil-home-sync">
(function() {
  var URL_MAP = {
    'Page : Horaires du mois': 'Horaires.dc.html',
    'Page : Rappel de prière': 'N3-Rappel.dc.html',
    'Page : Langue de la khutba': 'N2-Khutba.dc.html',
    'Page : Faire un don': 'Dons.dc.html',
    'Page : Campagne en direct': 'N3-Campagne.dc.html',
    'Page : Événements': 'Evenements.dc.html',
    'Page : Calendrier du mois': 'N3-Calendrier.dc.html',
    'Page : Contact': 'Contact.dc.html',
    'Page : Ressources': 'Ressources.dc.html',
    'Page : À propos': 'APropos.dc.html',
    'Page : Services': 'Services.dc.html'
  };

  function toUrl(val) {
    if (!val) return '';
    return URL_MAP[val] || val;
  }

  function escHtml(str) {
    var d = document.createElement('div');
    d.textContent = str == null ? '' : String(str);
    return d.innerHTML;
  }
  function escAttr(str) {
    return String(str || '').replace(/"/g, '&quot;');
  }

  // Les heures du jour viennent de la base (tableau du mois, repli sur les heures de ces réglages) :
  // la page les affiche elle-même (scripts/wire_prieres.py). Ici, seulement les puces et la progression.
  function updatePrayerDisplay(p, on) {
    var ppTitle = document.getElementById('pp-title');
    var ppWrap = ppTitle && ppTitle.closest('.pad-m');
    if (!ppWrap) return;
    var g5 = ppWrap.querySelector('.g5');
    if (g5) g5.style.display = on.puces === false ? 'none' : '';
    var prog = ppWrap.querySelector('.prog');
    if (prog) prog.style.display = on.progression === false ? 'none' : '';
  }

  function applySettings(s) {
    if (!s) return;
    try {
      // Écran de chargement : masqué (jamais retiré de la page, ce qui ferait planter son affichage).
      var ld = document.querySelector('div[role="status"][aria-label="Chargement"]');
      if (ld && s.on && s.on.chargement === false) {
        ld.style.display = 'none';
      } else if (ld && s.chargement && s.chargement.duration === 'rapide') {
        setTimeout(function() { ld.style.display = 'none'; }, 1500);
      }

      var topBar = document.querySelector('header.hdr > div:first-child');
      if (topBar && s.on) {
        if (s.on.bandeau === false) {
          topBar.style.display = 'none';
        } else {
          topBar.style.display = '';
          var topMail = topBar.querySelector('a[href^="mailto:"]');
          var topFb = topBar.querySelector('a[href*="facebook.com"]');
          var topCompte = topBar.querySelector('.tnum');
          if (topMail) topMail.style.display = s.on.mail === false ? 'none' : '';
          if (topFb) topFb.style.display = s.on.fb === false ? 'none' : '';
          if (topCompte) {
            var cdSpan = topCompte.querySelector('.hide-m:last-child');
            if (cdSpan) cdSpan.style.display = s.on.compte === false ? 'none' : '';
          }
        }
      }

      if (s.general) {
        if (s.general.email) {
          document.querySelectorAll('a[href^="mailto:"]').forEach(function(a) {
            a.href = 'mailto:' + s.general.email;
            if (a.textContent.includes('@')) {
              var svg = a.querySelector('svg');
              if (svg) {
                a.innerHTML = '';
                a.appendChild(svg);
                a.appendChild(document.createTextNode(s.general.email));
              } else {
                a.textContent = s.general.email;
              }
            }
          });
        }
        if (s.general.facebook) {
          document.querySelectorAll('a[href*="facebook.com"]').forEach(function(a) {
            a.href = s.general.facebook;
          });
        }
        if (s.general.mapUrl) {
          document.querySelectorAll('a[href*="maps.google.com"]').forEach(function(a) {
            a.href = s.general.mapUrl;
          });
        }
        if (s.general.address || s.general.city) {
          var footAdr = document.querySelector('footer .g4 > div:first-child > p:nth-of-type(1)');
          if (footAdr) {
            footAdr.innerHTML = (s.general.address || '34, 37e Avenue') + '<br>' + (s.general.city || 'Edmundston, NB E3V 3S2');
          }
          var cardAdr = document.querySelector('section[aria-label="Accès rapides"] a[href="Contact.dc.html"] p.h3');
          if (cardAdr) {
            cardAdr.textContent = 'Nous trouver — ' + (s.general.address || '34, 37e Avenue');
          }
        }
      }

      if (s.on) {
        var donBtn = document.querySelectorAll('.don-btn');
        donBtn.forEach(function(b) { b.style.display = s.on.don === false ? 'none' : ''; });
        var langDesk = document.querySelectorAll('.lang-desk');
        langDesk.forEach(function(l) { l.style.display = s.on.langue === false ? 'none' : ''; });

        var menuItems = [
          ['horaires', 'Horaires.dc.html'],
          ['apropos', 'APropos.dc.html'],
          ['services', 'Services.dc.html'],
          ['evenements', 'Evenements.dc.html'],
          ['ressources', 'Ressources.dc.html'],
          ['contact', 'Contact.dc.html']
        ];
        menuItems.forEach(function(item) {
          var k = item[0], href = item[1];
          if (s.on[k] === false) {
            document.querySelectorAll('.nav-desk a[href="' + href + '"], nav[aria-label="Menu mobile"] a[href="' + href + '"]').forEach(function(a) {
              var parentDd = a.closest('.dd');
              if (parentDd) parentDd.style.display = 'none';
              else a.style.display = 'none';
            });
          } else {
            document.querySelectorAll('.nav-desk a[href="' + href + '"], nav[aria-label="Menu mobile"] a[href="' + href + '"]').forEach(function(a) {
              var parentDd = a.closest('.dd');
              if (parentDd) parentDd.style.display = '';
              else a.style.display = '';
            });
          }
        });
      }

      var heroSec = document.querySelector('section[aria-labelledby="hero-t"]');
      if (heroSec && s.on) {
        heroSec.style.display = s.on.hero === false ? 'none' : '';
        if (s.hero) {
          var h1Btn = heroSec.querySelector('.btn-gold');
          var h2Btn = heroSec.querySelector('.btn-ghost');
          if (h1Btn && s.hero.h1) h1Btn.href = toUrl(s.hero.h1);
          if (h2Btn && s.hero.h2) h2Btn.href = toUrl(s.hero.h2);
        }
      }

      var priereSec = document.querySelector('section[aria-labelledby="pp-title"]');
      // Date hégirienne (« samedi 7 novembre 2026 · 26 joumada I 1448 ») : masquée si désactivée.
      if (priereSec && s.on && s.on.hegirien === false) {
        priereSec.querySelectorAll('p').forEach(function(p) {
          var first = p.firstChild, sp = p.querySelector(':scope > span');
          if (sp && first && first.nodeType === 3 && / · $/.test(first.textContent)) {
            sp.style.display = 'none';
            first.textContent = first.textContent.replace(/ · $/, '');
          }
        });
      }
      if (priereSec && s.on) {
        priereSec.style.display = s.on.priere === false ? 'none' : '';
      }
      if (s.priere) {
        updatePrayerDisplay(s.priere, s.on || {});
      }

      var accesSec = document.querySelector('section[aria-label="Accès rapides"]');
      if (accesSec && s.on) {
        accesSec.style.display = s.on.acces === false ? 'none' : '';
        if (s.acces && Array.isArray(s.acces.cartes)) {
          // Cartes dans l'ordre enregistré : propriété CSS « order » (la grille ne bouge pas les éléments).
          var cards = accesSec.querySelectorAll('.wrap.g3 > a.card');
          var CARD_IDS = ['vendredi', 'trouver', 'campagne'];
          s.acces.cartes.forEach(function(k, pos) {
            var el = cards[CARD_IDS.indexOf(k.id)];
            if (!el) return;
            el.style.display = k.on === false ? 'none' : '';
            el.style.order = String(pos);
            if (k.lien) el.href = toUrl(k.lien);
          });
        }
      }

      var campSec = document.querySelector('section[aria-labelledby="camp-t"]');
      if (campSec && s.on) {
        campSec.style.display = s.on.campagne === false ? 'none' : '';
      }
      if (campSec && s.campagne) {
        var obj = Number(s.campagne.objectif) || 0;
        var rec = Number(s.campagne.recolte) || 0;
        var pct = obj > 0 ? Math.min(100, Math.round((rec / obj) * 100)) : 0;

        var objEl = campSec.querySelector('p.serif.tnum');
        if (objEl) objEl.textContent = obj.toLocaleString('fr-CA') + ' $';

        var barWrap = campSec.querySelector('div[role="progressbar"]');
        var recText = campSec.querySelector('p.tnum:not(.serif)');
        var noRecMsg = campSec.querySelector('p.ph');

        if (s.on && s.on.barre === false) {
          if (barWrap) barWrap.style.display = 'none';
        } else if (barWrap) {
          barWrap.style.display = '';
        }

        if (rec > 0 && obj > 0) {
          if (barWrap) {
            barWrap.setAttribute('aria-valuemax', String(obj));
            var bar = barWrap.querySelector('.bar');
            if (bar) bar.style.width = pct + '%';
          }
          if (recText) {
            recText.style.display = '';
            recText.textContent = rec.toLocaleString('fr-CA') + ' $ récoltés · ' + pct + ' %';
          }
          if (noRecMsg) noRecMsg.style.display = 'none';
        } else {
          if (barWrap) barWrap.style.display = 'none';
          if (recText) recText.style.display = 'none';
          if (noRecMsg) noRecMsg.style.display = '';
        }

        if (s.campagne.btnInterac) {
          var btnInt = campSec.querySelector('a.btn-green');
          if (btnInt) btnInt.href = toUrl(s.campagne.btnInterac);
        }
        if (s.campagne.btnSuivre) {
          var btnSui = campSec.querySelector('a.link');
          if (btnSui) btnSui.href = toUrl(s.campagne.btnSuivre);
        }
      }

      var annSec = document.querySelector('section[aria-labelledby="ann-t"]');
      if (annSec && s.on) {
        annSec.style.display = s.on.annonces === false ? 'none' : '';
      }
      if (annSec && s.annonces) {
        if (s.annonces.btnTous) {
          var tousLink = annSec.querySelector('a.link');
          if (tousLink) tousLink.href = toUrl(s.annonces.btnTous);
        }
        if (Array.isArray(s.annonces.items)) {
          var max = s.annonces.max || 3;
          var activeItems = s.annonces.items.filter(function(a) { return a.on !== false; }).slice(0, max);
          var annContainer = annSec.querySelector('.g3');
          // Aucune annonce à afficher : la section disparaît au lieu de montrer les exemples d'origine.
          if (!activeItems.length) annSec.style.display = 'none';
          if (annContainer && activeItems.length) {
            annContainer.innerHTML = activeItems.map(function(item) {
              return '<a class="card" href="' + escAttr(toUrl(item.lien || 'Page : Événements')) + '">'
                + '<span class="pill tnum" style="background:#0E4D3C;color:#fff">' + escHtml(item.date) + '</span>'
                + '<p class="h3" style="margin-top:16px;font-size:20px">' + escHtml(item.titre) + '</p>'
                + '<p class="muted" style="margin:8px 0 0">' + escHtml(item.resume) + '</p>'
                + '</a>';
            }).join('');
          }
        }
      }

      var bvSec = document.querySelector('section[aria-labelledby="bv-t"]');
      if (bvSec && s.on) {
        bvSec.style.display = s.on.bienvenue === false ? 'none' : '';
        if (s.bienvenue && s.bienvenue.lien) {
          var bvLink = bvSec.querySelector('a.link');
          if (bvLink) bvLink.href = toUrl(s.bienvenue.lien);
        }
      }

      var invSec = document.querySelector('section[aria-label="Invitation"]');
      if (invSec && s.on) {
        invSec.style.display = s.on.invitation === false ? 'none' : '';
        if (s.invitation && s.invitation.lien) {
          var invBtn = invSec.querySelector('a.btn-green');
          if (invBtn) invBtn.href = toUrl(s.invitation.lien);
        }
      }

      var toTop = document.querySelector('.totop');
      if (toTop && s.on) {
        toTop.style.display = s.on.haut === false ? 'none' : '';
      }

      // Liens TCOM et CCIQ, lignes du pied de page et bouton Itinéraire : script commun
      // #ascil-pied-live (scripts/wire_pied.py), le même sur toutes les pages publiques.
      if (s.on) {
        var footHor = document.querySelector('footer .g4 > div:first-child > p.tnum');
        if (footHor) footHor.style.display = s.on.pHor === false ? 'none' : '';
      }

      if (Array.isArray(s.ordre) && s.ordre.length) {
        var main = document.querySelector('main.pagein');
        if (main) {
          var secMap = {
            acces: main.querySelector('section[aria-label="Accès rapides"]'),
            campagne: main.querySelector('section[aria-labelledby="camp-t"]'),
            annonces: main.querySelector('section[aria-labelledby="ann-t"]'),
            bienvenue: main.querySelector('section[aria-labelledby="bv-t"]'),
            invitation: main.querySelector('section[aria-label="Invitation"]')
          };
          var anchor = main.querySelector('.totop') || null;
          s.ordre.forEach(function(id) {
            var el = secMap[id];
            if (el && main.contains(el)) {
              if (anchor) main.insertBefore(el, anchor);
              else main.appendChild(el);
            }
          });
        }
      }
    } catch (err) {
      console.warn('[ascil-sync] applySettings error:', err);
    }
  }

  // 1. Enregistrement anonyme de la visite (sans cookies, sans IP)
  try {
    var pName = location.pathname || '/';
    if (!sessionStorage.getItem('ascil_viewed_' + pName)) {
      sessionStorage.setItem('ascil_viewed_' + pName, '1');
      fetch('/api/views', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: pName })
      }).catch(function() {});
    }
  } catch (e) {}

  // 2. Cache local immédiat
  try {
    var cached = localStorage.getItem('ascil_home_settings');
    if (cached) applySettings(JSON.parse(cached));
  } catch (e) {}

  // 3. Mise à jour en direct
  function syncLive() {
    fetch('/api/settings/home')
      .then(function(r) { return r.ok ? r.json() : null; })
      .then(function(d) {
        if (d && d.ok && d.settings) {
          try { localStorage.setItem('ascil_home_settings', JSON.stringify(d.settings)); } catch (e) {}
          applySettings(d.settings);
        }
      })
      .catch(function() {});
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', syncLive);
  } else {
    syncLive();
  }
})();
</script>
'''

def remove_stats_banner(tpl):
    """Retire le bandeau des statistiques déjà injecté (commentaire + <div id="sa-stats-banner"> entier).

    Compte les <div> ouvertes et fermées pour retirer le bloc complet : une simple expression
    régulière s'arrêtait à la fin de la première carte et laissait le reste du bandeau.
    """
    start = tpl.find('<!-- Bandeau des statistiques réelles (étape 2b) -->')
    if start < 0:
        return tpl
    div = tpl.find('<div id="sa-stats-banner"', start)
    assert div > -1, 'bandeau sans <div id="sa-stats-banner">'
    depth, k = 0, div
    for m in re.finditer(r'<div\b|</div>', tpl[div:]):
        depth += 1 if m.group(0) != '</div>' else -1
        if depth == 0:
            k = div + m.end()
            break
    assert depth == 0, 'bandeau mal fermé'
    while start > 0 and tpl[start - 1] in ' \t\n':
        start -= 1
    return tpl[:start] + tpl[k:]


# ---------------------------------------------------------------- logique du panneau Accueil
# La logique de la maquette gardait des textes fixes (annonces, heures, liens) et laissait les champs
# figés ; elle est remplacée par scripts/panneau_component.js, et le gabarit est relié à ce nouvel état.
COMPONENT_FILE = pathlib.Path(__file__).resolve().parent / 'panneau_component.js'
OPTS = '<sc-for list="{{%s.opts}}" as="op" hint-placeholder-count="3"><option value="{{op.v}}">{{op.t}}</option></sc-for>'
PANEL_PATCHES = [
    ('<input class="in tnum" id="h-{{$index}}" type="time" value="{{hh.v}}">',
     '<input class="in tnum" id="h-{{$index}}" type="time" value="{{hh.v}}" sc-camel-on-change="{{hh.set}}">'),
    ('<input class="in" id="a-d-{{$index}}" value="{{a.date}}">',
     '<input class="in" id="a-d-{{$index}}" value="{{a.date}}" maxlength="40" placeholder="Ex. 27 mai 2026" sc-camel-on-change="{{a.setDate}}">'),
    ('<input class="in" id="a-t-{{$index}}" value="{{a.titre}}">',
     '<input class="in" id="a-t-{{$index}}" value="{{a.titre}}" maxlength="160" sc-camel-on-change="{{a.setTitre}}">'),
    ('<textarea class="in" id="a-r-{{$index}}" rows="2" value="{{a.resume}}"></textarea>',
     '<textarea class="in" id="a-r-{{$index}}" rows="2" maxlength="400" value="{{a.resume}}" sc-camel-on-change="{{a.setResume}}"></textarea>'),
    ('<button type="button" class="btn btn-line" style="align-self:flex-start">+ Ajouter une annonce</button>',
     '<button type="button" class="btn btn-line" style="align-self:flex-start" disabled="{{annFull}}" sc-camel-on-click="{{addAnn}}">+ Ajouter une annonce</button>'),
    ('<button type="button" class="ico" aria-label="Supprimer {{a.titre}}">',
     '<button type="button" class="ico" aria-label="Supprimer {{a.lbl}}" sc-camel-on-click="{{a.del}}" style="color:#B3261E;border-color:#E9B4AF">'),
    ('<span style="flex:1;min-width:150px;font-weight:700">{{a.pos}}. {{a.titre}}</span>',
     '<span style="flex:1;min-width:150px;font-weight:700">{{a.pos}}. {{a.lbl}}</span>'),
    ('aria-label="Monter {{a.titre}}"', 'aria-label="Monter {{a.lbl}}"'),
    ('aria-label="Descendre {{a.titre}}"', 'aria-label="Descendre {{a.lbl}}"'),
    ('aria-label="Afficher {{a.titre}}"', 'aria-label="Afficher {{a.lbl}}"'),
    ('sc-camel-on-click="{{toggleMore}}" style="display:flex;width:100%;align-items:center;min-height:44px;padding:0 12px;border:0;background:none;border-radius:10px;cursor:pointer;text-align:left">Exporter les réglages (.json)',
     'sc-camel-on-click="{{doExport}}" style="display:flex;width:100%;align-items:center;min-height:44px;padding:0 12px;border:0;background:none;border-radius:10px;cursor:pointer;text-align:left">Exporter les réglages (.json)'),
    ('sc-camel-on-click="{{toggleMore}}" style="display:flex;width:100%;align-items:center;min-height:44px;padding:0 12px;border:0;background:none;border-radius:10px;cursor:pointer;text-align:left">Importer des réglages…',
     'sc-camel-on-click="{{doImport}}" style="display:flex;width:100%;align-items:center;min-height:44px;padding:0 12px;border:0;background:none;border-radius:10px;cursor:pointer;text-align:left">Importer des réglages…'),
    ('sc-camel-on-click="{{toggleMore}}" style="display:flex;width:100%;align-items:center;min-height:44px;padding:0 12px;border:0;background:none;border-radius:10px;cursor:pointer;text-align:left">Revenir aux valeurs d’origine',
     'sc-camel-on-click="{{doReset}}" style="display:flex;width:100%;align-items:center;min-height:44px;padding:0 12px;border:0;background:none;border-radius:10px;cursor:pointer;text-align:left">Revenir aux valeurs d’origine'),
]


def patch_panel(path):
    content = path.read_text(encoding='utf-8')
    m = re.search(r'<script type="__bundler/template">(.*?)</script>', content, re.S)
    tpl = json.loads(m.group(1))
    code = COMPONENT_FILE.read_text(encoding='utf-8')
    tpl = re.sub(r'(<script type="text/x-dc"[^>]*>).*?(</script>)', lambda x: x.group(1) + code + x.group(2), tpl, count=1, flags=re.S)
    if 'sc-camel-on-change="{{hh.set}}"' not in tpl:
        # Listes de liens des cartes et des annonces : options fournies par la logique (quelles que
        # soient les options d'exemple encore présentes dans la maquette).
        for sel, var in (('k', 'k'), ('a-l', 'a')):
            tpl, n = re.subn(r'<sc-raw-select class="in" id="' + sel + r'-\{\{\$index\}\}">.*?</sc-raw-select>',
                             lambda m, sel=sel, var=var: ('<sc-raw-select class="in" id="' + sel + '-{{$index}}" value="{{' + var + '.lien}}" '
                                                          'sc-camel-on-change="{{' + var + '.setLien}}">' + OPTS % var + '</sc-raw-select>'),
                             tpl, count=1, flags=re.S)
            assert n == 1, sel
        for a, b in PANEL_PATCHES:
            assert tpl.count(a) == 1, a[:80]
            tpl = tpl.replace(a, b)
    enc = json.dumps(tpl).replace('</', '<\\u002F')
    assert json.loads(enc) == tpl
    i = content.index('<script type="__bundler/template">') + len('<script type="__bundler/template">')
    j = content.index('</script>', i)
    path.write_text(content[:i] + enc + content[j:], encoding='utf-8')
    print(f"Logique du panneau Accueil remplacée : {path.name}")


def update_file(path, script_tag, script_id, inject_html=None, inject_anchor=None):
    content = path.read_text(encoding='utf-8')
    m = re.search(r'<script type="__bundler/template">(.*?)</script>', content, re.S)
    if not m:
        raise ValueError(f"No __bundler/template in {path}")
    tpl = json.loads(m.group(1))

    # Supprime toute version antérieure de ce script
    pat = re.compile(r'<script id="' + re.escape(script_id) + r'">.*?</script>\s*', re.S)
    tpl = pat.sub('', tpl)

    # Injection HTML optionnelle (ex. bandeau stats)
    if inject_html and inject_anchor and inject_anchor in tpl:
        # Supprime ancienne version du bandeau si présente
        tpl = remove_stats_banner(tpl)
        idx_anchor = tpl.index(inject_anchor) + len(inject_anchor)
        tpl = tpl[:idx_anchor] + '\n' + inject_html + tpl[idx_anchor:]

    # Insère immédiatement avant </body>
    idx_body = tpl.rindex('</body>')
    tpl = tpl[:idx_body] + script_tag + '\n' + tpl[idx_body:]

    enc = json.dumps(tpl).replace('</', '<\\u002F')
    assert json.loads(enc) == tpl

    i = content.index('<script type="__bundler/template">') + len('<script type="__bundler/template">')
    j = content.index('</script>', i)
    new_content = content[:i] + enc + content[j:]
    path.write_text(new_content, encoding='utf-8')
    print(f"Modifié avec succès : {path.name} (script #{script_id})")

def main():
    # 1. Panneau superadmin (avec bandeau stats)
    panneau = ROOT / 'SA-Panneau.dc.html'
    intro_anchor = 'L’aperçu change tout de suite ; le site, après <strong>Enregistrer</strong>.</p>\n   </div>'
    update_file(panneau, PANNEAU_SYNC_SCRIPT, 'sa-panneau-sync', inject_html=STATS_BANNER_HTML, inject_anchor=intro_anchor)
    patch_panel(panneau)

    # 2. Pages d'accueil publiques
    for name in ['Main.dc.html', 'index.html', 'M-Accueil.dc.html', 'T-Accueil.dc.html']:
        p = ROOT / name
        if p.exists():
            update_file(p, PUBLIC_HOME_SYNC_SCRIPT, 'ascil-home-sync')

if __name__ == '__main__':
    main()
