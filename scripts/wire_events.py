"""Branchement dynamique des inscriptions aux événements (étape 2c).

1. Pages publiques d'inscription :
   - N3-Inscription.dc.html
   - M-N3-Inscription.dc.html (mobile)
   - T-N3-Inscription.dc.html (tablette)
   -> Script #ascil-inscription-sync :
      - Charge les données réelles et places restantes depuis GET /api/events/registration-info
      - Remplit titre, date, lieu, description ; masque l'option végétarienne si elle est coupée
      - Fournit le fichier .ics (window.__ascilIcs)
   -> xvals() de la page (remplacé ici) : places réelles, compteur, envoi POST /api/events/register,
      écran de confirmation avec le vrai code ASC-XXXX-XXXX. La maquette inventait un code « IFT- »
      sans rien envoyer : c'est elle qui s'exécutait en premier et l'inscription n'arrivait jamais.

2. Panneau d'administration :
   - SA-Evenements.dc.html
   -> Relié désormais par wire_evenements.py (ancien script #sa-evenements-sync ci-dessous, plus installé) :
      - Charge et sauvegarde les réglages de jauge et dates via GET/PUT /api/admin/events/settings
      - Affiche le résumé en direct et la liste complète des inscrits via GET /api/admin/events/registrations
      - Permet l'annulation d'une inscription via DELETE /api/admin/events/registrations?id=...
      - Connecte le bouton « Exporter la liste (.csv) » vers /api/admin/events/export
      - Connecte le bouton « Écrire aux inscrits » (mailto: en Cci)
"""

import json, re, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent

PUBLIC_INSCRIPTION_SYNC_SCRIPT = r'''<script id="ascil-inscription-sync">
(function() {
  var eventData = null;
  var currentCount = 1;
  var isVeg = false;

  function esc(s) {
    if (!s) return '';
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function downloadIcs(title, dateStr, location, desc) {
    // Fichier iCalendar universel (.ics)
    var nowStr = new Date().toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z';
    // Événement Iftar ou personnalisé (défaut : 20 fév 2027 17h15 - 20h00 heure de Montréal/Toronto)
    var dtStart = '20270220T221500Z'; // 17h15 EST en UTC
    var dtEnd   = '20270221T010000Z'; // 20h00 EST en UTC

    var ics = [
      'BEGIN:VCALENDAR',
      'VERSION:2.0',
      'PRODID:-//ASCIL//Evenements//FR',
      'CALSCALE:GREGORIAN',
      'METHOD:PUBLISH',
      'BEGIN:VEVENT',
      'UID:ascil-' + Date.now() + '@ascil-mosquee.pages.dev',
      'DTSTAMP:' + nowStr,
      'DTSTART:' + dtStart,
      'DTEND:' + dtEnd,
      'SUMMARY:' + (title || 'Événement ASCIL'),
      'DESCRIPTION:' + (desc || ''),
      'LOCATION:' + (location || '106, rue de l’Église, Edmundston'),
      'STATUS:CONFIRMED',
      'END:VEVENT',
      'END:VCALENDAR'
    ].join('\r\n');

    var blob = new Blob([ics], { type: 'text/calendar;charset=utf-8' });
    var link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'evenement-ascil.ics';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  function updateUI(ev) {
    if (!ev) return;
    eventData = ev;

    // 1. Titre & infos
    var titleEl = document.getElementById('ev-t');
    if (titleEl && ev.title) titleEl.textContent = ev.title;

    var dateEl = document.querySelector('section[aria-labelledby="ev-t"] p.tnum:first-of-type');
    if (dateEl && ev.date_str) {
      dateEl.innerHTML = '<svg class="icon" aria-hidden="true" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#D9B46C" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="width:20px;height:20px"><rect x="4" y="5" width="16" height="15" rx="2"></rect><path d="M4 10h16M9 3v4M15 3v4"></path></svg>' + esc(ev.date_str);
    }

    var locEl = document.querySelector('section[aria-labelledby="ev-t"] p:nth-of-type(2)');
    if (locEl && ev.location) {
      locEl.innerHTML = '<svg class="icon" aria-hidden="true" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#D9B46C" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="width:20px;height:20px"><path d="M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21z"></path><circle cx="12" cy="9.5" r="2.5"></circle></svg>' + esc(ev.location);
    }

    var descEl = document.querySelector('section[aria-labelledby="ev-t"] p:nth-of-type(3)');
    if (descEl && ev.description) descEl.textContent = ev.description;

    // Places, compteur, envoi et confirmation : gérés par xvals() de la page (données réelles).
    var vegLabel = document.querySelector('input[type="checkbox"]')?.closest('label');
    if (vegLabel && ev.opt_vege === false) {
      vegLabel.style.display = 'none';
    }
  }

  function init() {
    fetch('/api/events/registration-info')
      .then(function(r) { return r.ok ? r.json() : null; })
      .then(function(d) {
        if (d && d.ok && d.event) {
          updateUI(d.event);
        }
      })
      .catch(function() {});

  }

  window.__ascilIcs = downloadIcs;

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
</script>
'''

ADMIN_EVENEMENTS_SYNC_SCRIPT = r'''<script id="sa-evenements-sync">
(function() {
  var initialSettings = null;
  var isDirty = false;
  var allRegistrations = [];
  var lastRestricted = '';

  function esc(s) {
    if (!s) return '';
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function toast(msg) {
    var existing = document.getElementById('sa-toast');
    if (!existing) {
      existing = document.createElement('div');
      existing.id = 'sa-toast';
      existing.style.cssText = 'position:fixed;bottom:24px;left:50%;transform:translateX(-50%);background:#0E4D3C;color:#fff;padding:12px 24px;border-radius:12px;box-shadow:0 6px 20px rgba(0,0,0,.25);font-size:14px;font-weight:600;z-index:99999;transition:opacity .2s;opacity:0;pointer-events:none;';
      document.body.appendChild(existing);
    }
    existing.textContent = msg;
    existing.style.opacity = '1';
    clearTimeout(window.__saToastTimer);
    window.__saToastTimer = setTimeout(function() {
      existing.style.opacity = '0';
    }, 3200);
  }

  function setStatus(dirty, text) {
    isDirty = dirty;
    var dot = document.querySelector('header.top .sdot');
    var p = document.querySelector('header.top .status');
    var saveBtn = document.querySelector('header.top button.btn-gold');
    var cancelBtn = document.querySelector('header.top button.btn-onDark');

    if (dot) dot.style.background = dirty ? '#C49A4A' : '#1D7A58';
    if (p) p.innerHTML = '<span class="sdot" aria-hidden="true" style="width:9px;height:9px;border-radius:50%;background:' + (dirty ? '#C49A4A' : '#1D7A58') + '"></span>' + (text || (dirty ? 'Modifications non enregistrées' : 'Tout est enregistré'));
    if (saveBtn) {
      if (dirty) saveBtn.removeAttribute('disabled');
      else saveBtn.setAttribute('disabled', 'true');
    }
    if (cancelBtn) {
      if (dirty) cancelBtn.removeAttribute('disabled');
      else cancelBtn.setAttribute('disabled', 'true');
    }
  }

  function markDirty() {
    setStatus(true);
  }

  function getSwitch(label, fallback) {
    var sw = document.querySelector('button.sw[aria-label="' + label + '"]');
    if (!sw) return fallback != null ? fallback : false;
    return sw.getAttribute('aria-checked') === 'true';
  }

  function setSwitch(label, val) {
    var sw = document.querySelector('button.sw[aria-label="' + label + '"]');
    if (!sw) return;
    sw.setAttribute('aria-checked', val ? 'true' : 'false');
  }

  function loadSettings() {
    fetch('/api/admin/events/settings', { credentials: 'same-origin' })
      .then(function(r) { return r.ok ? r.json() : null; })
      .then(function(d) {
        if (!d || !d.ok || !d.settings) return;
        var s = d.settings;
        initialSettings = JSON.parse(JSON.stringify(s));

        // Formulaire Jauge / Inscription (sp-3)
        var f19 = document.getElementById('f19');
        var f20 = document.getElementById('f20');
        var f21 = document.getElementById('f21');
        var f22 = document.getElementById('f22');

        if (f19 && s.event_title) {
          // Si l'option n'existe pas, on l'ajoute
          var exists = false;
          for (var i = 0; i < f19.options.length; i++) {
            if (f19.options[i].value === s.event_title || f19.options[i].text === s.event_title) {
              f19.selectedIndex = i;
              exists = true;
              break;
            }
          }
          if (!exists) {
            var opt = document.createElement('option');
            opt.value = s.event_title;
            opt.text = s.event_title;
            f19.appendChild(opt);
            f19.value = s.event_title;
          }
        }

        if (f20 && s.total_seats != null) f20.value = s.total_seats;
        if (f21 && s.max_per_reg != null) f21.value = s.max_per_reg;
        if (f22 && s.deadline != null) f22.value = s.deadline;

        setSwitch('Inscriptions ouvertes', s.is_open);
        setSwitch('Option « Repas végétarien »', s.opt_vege);
        setSwitch('Code de confirmation', s.opt_code);
        setSwitch('Bouton « Ajouter à mon agenda »', s.opt_agenda);

        setStatus(false, 'Tout est enregistré');
      })
      .catch(function() {});
  }

  function loadRegistrations() {
    fetch('/api/admin/events/registrations', { credentials: 'same-origin' })
      .then(function(r) { return r.ok ? r.json() : null; })
      .then(function(d) {
        if (!d || !d.ok) return;
        allRegistrations = d.registrations || [];
        if (d.restricted) {
          // Éditeur : synthèse seulement, ni noms ni contacts, ni export ni courriel groupé.
          Array.prototype.forEach.call(document.querySelectorAll('button, a'), function(b) {
            var txt = (b.textContent || '').trim();
            if (txt.indexOf('Exporter la liste (.csv)') > -1 || txt.indexOf('Écrire aux inscrits') > -1) b.style.display = 'none';
          });
        }
        var sm = d.summary || {};

        // Résumé en haut de la carte
        var infoP = document.querySelector('#sp-3 section[aria-label="Inscrits"] p.info');
        if (infoP) {
          var totalSeats = initialSettings ? initialSettings.total_seats : 120;
          infoP.textContent = (sm.total_attendees || 0) + ' places réservées sur ' + totalSeats + ' · ' + (sm.total_registrations || 0) + ' inscription(s) confirmée(s) · ' + (sm.vegetarian_count || 0) + ' repas végétarien(s)';
        }

        // Tableau des inscrits
        lastRestricted = d.restricted ? (d.message || 'La liste nominative est réservée au superadmin et au responsable des événements.') : '';
        renderRegistrationsTable(allRegistrations);
      })
      .catch(function() {});
  }

  function renderRegistrationsTable(list) {
    var cardB = document.querySelector('#sp-3 section[aria-label="Inscrits"] .card-b');
    if (!cardB) return;

    var existingWrap = document.getElementById('sa-reg-list-wrap');
    if (!existingWrap) {
      existingWrap = document.createElement('div');
      existingWrap.id = 'sa-reg-list-wrap';
      existingWrap.style.marginTop = '18px';
      cardB.appendChild(existingWrap);
    }

    if (lastRestricted) {
      existingWrap.innerHTML = '<p style="color:#4F5E57;margin-top:12px">' + esc(lastRestricted) + '</p>';
      return;
    }

    if (!list || list.length === 0) {
      existingWrap.innerHTML = '<p style="color:#5E6460;font-style:italic;margin-top:12px">Aucune inscription enregistrée pour le moment.</p>';
      return;
    }

    var html = [
      '<div style="overflow-x:auto;border:1px solid #E4D9C0;border-radius:12px;margin-top:14px;background:#fff">',
      '  <table style="width:100%;border-collapse:collapse;font-size:13px;text-align:left">',
      '    <thead>',
      '      <tr style="background:#F6EEDF;color:#0E4D3C;font-weight:700;border-bottom:1px solid #E4D9C0">',
      '        <th style="padding:10px 12px">Code</th>',
      '        <th style="padding:10px 12px">Nom</th>',
      '        <th style="padding:10px 12px">Contact</th>',
      '        <th style="padding:10px 12px;text-align:center">Places</th>',
      '        <th style="padding:10px 12px;text-align:center">Végé</th>',
      '        <th style="padding:10px 12px">Date</th>',
      '        <th style="padding:10px 12px;text-align:center">Statut</th>',
      '        <th style="padding:10px 12px;text-align:right">Action</th>',
      '      </tr>',
      '    </thead>',
      '    <tbody>'
    ];

    list.forEach(function(r) {
      var isConfirmed = r.status === 'confirmed';
      var statusTag = isConfirmed
        ? '<span style="display:inline-block;padding:2px 8px;border-radius:12px;background:#EAF3EF;color:#0E4D3C;font-weight:700;font-size:11px">Confirmé</span>'
        : '<span style="display:inline-block;padding:2px 8px;border-radius:12px;background:#FDEBEB;color:#B3261E;font-weight:700;font-size:11px">Annulé</span>';

      var dateStr = (r.created_at || '').slice(0, 16).replace('T', ' ');

      html.push(
        '<tr style="border-bottom:1px solid #F1E9DB;' + (!isConfirmed ? 'opacity:.6' : '') + '">',
        '  <td style="padding:10px 12px;font-family:monospace;font-weight:700;color:#0E4D3C">' + esc(r.code) + '</td>',
        '  <td style="padding:10px 12px;font-weight:600">' + esc(r.name) + '</td>',
        '  <td style="padding:10px 12px"><a href="' + (r.contact && r.contact.includes('@') ? 'mailto:' + esc(r.contact) : 'tel:' + esc(r.contact)) + '" style="color:#0E4D3C;text-decoration:underline">' + esc(r.contact) + '</a></td>',
        '  <td style="padding:10px 12px;text-align:center;font-weight:700" class="tnum">' + (r.attendees_count || 1) + '</td>',
        '  <td style="padding:10px 12px;text-align:center">' + (r.is_vegetarian ? 'Oui' : '—') + '</td>',
        '  <td style="padding:10px 12px;color:#666;font-size:12px" class="tnum">' + esc(dateStr) + '</td>',
        '  <td style="padding:10px 12px;text-align:center">' + statusTag + '</td>',
        '  <td style="padding:10px 12px;text-align:right">',
        isConfirmed
          ? '    <button type="button" class="btn-cancel-reg" data-id="' + r.id + '" data-code="' + esc(r.code) + '" style="background:#FFF0F0;color:#B3261E;border:1px solid #F5C2C2;border-radius:8px;padding:4px 10px;font-size:11px;font-weight:700;cursor:pointer">Annuler</button>'
          : '    <span style="color:#999;font-size:11px">—</span>',
        '  </td>',
        '</tr>'
      );
    });

    html.push('</tbody></table></div>');
    existingWrap.innerHTML = html.join('');
  }

  function collectPayload() {
    var f19 = document.getElementById('f19');
    var f20 = document.getElementById('f20');
    var f21 = document.getElementById('f21');
    var f22 = document.getElementById('f22');

    return {
      event_slug: initialSettings ? initialSettings.event_slug : '',
      event_title: f19 ? f19.value : 'Iftar communautaire',
      date_str: initialSettings ? initialSettings.date_str : 'Samedi 20 février 2027 · 17 h 15',
      location: initialSettings ? initialSettings.location : '34, 37e Avenue',
      description: initialSettings ? initialSettings.description : '',
      total_seats: parseInt(f20 ? f20.value : 120, 10) || 120,
      max_per_reg: parseInt(f21 ? f21.value : 6, 10) || 6,
      deadline: f22 ? f22.value : '2027-02-18',
      is_open: getSwitch('Inscriptions ouvertes', true),
      opt_vege: getSwitch('Option « Repas végétarien »', true),
      opt_code: getSwitch('Code de confirmation', true),
      opt_agenda: getSwitch('Bouton « Ajouter à mon agenda »', true)
    };
  }

  function init() {
    loadSettings();
    loadRegistrations();

    // Surveillance des champs
    document.addEventListener('input', function(e) {
      if (e.target && e.target.closest('#sp-3')) markDirty();
    });
    document.addEventListener('change', function(e) {
      if (e.target && e.target.closest('#sp-3')) markDirty();
    });

    document.addEventListener('click', function(e) {
      var t = e.target;
      if (t && t.matches('button.sw') && t.closest('#sp-3')) {
        setTimeout(markDirty, 50);
      }

      // Enregistrer
      var isSave = t && (t.matches('header.top button.btn-gold') || t.closest('header.top button.btn-gold'));
      if (isSave) {
        e.preventDefault();
        e.stopPropagation();
        var btn = t.closest('header.top button.btn-gold') || t;
        btn.setAttribute('disabled', 'true');
        btn.textContent = 'Enregistrement…';

        var payload = collectPayload();
        fetch('/api/admin/events/settings', {
          method: 'PUT',
          credentials: 'same-origin',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        })
        .then(function(r) { return r.json(); })
        .then(function(d) {
          btn.textContent = 'Enregistrer';
          if (d && d.ok) {
            initialSettings = JSON.parse(JSON.stringify(d.settings || payload));
            setStatus(false, 'Tout est enregistré');
            toast('Paramètres d’inscription enregistrés avec succès.');
            loadRegistrations();
          } else {
            btn.removeAttribute('disabled');
            toast('Erreur : ' + (d.message || 'Échec de la sauvegarde.'));
          }
        })
        .catch(function() {
          btn.textContent = 'Enregistrer';
          btn.removeAttribute('disabled');
          toast('Erreur de communication avec le serveur.');
        });
        return;
      }

      // Annuler les changements
      var isCancel = t && (t.matches('header.top button.btn-onDark') || t.closest('header.top button.btn-onDark'));
      if (isCancel) {
        e.preventDefault();
        e.stopPropagation();
        if (initialSettings) {
          loadSettings();
          toast('Modifications annulées.');
        }
        return;
      }

      // Exporter CSV
      var isExport = t && (t.textContent.includes('Exporter la liste (.csv)') || t.closest('button')?.textContent.includes('Exporter la liste (.csv)'));
      if (isExport) {
        e.preventDefault();
        e.stopPropagation();
        window.location.href = '/api/admin/events/export';
        return;
      }

      // Écrire aux inscrits
      var isMailto = t && (t.textContent.includes('Écrire aux inscrits') || t.closest('button')?.textContent.includes('Écrire aux inscrits'));
      if (isMailto) {
        e.preventDefault();
        e.stopPropagation();
        var emails = allRegistrations
          .filter(function(r) { return r.status === 'confirmed' && r.contact && r.contact.includes('@'); })
          .map(function(r) { return r.contact.trim(); });

        var uniqueEmails = Array.from(new Set(emails));
        if (uniqueEmails.length === 0) {
          alert('Aucune adresse courriel trouvée parmi les inscrits confirmés.');
          return;
        }

        var mailtoUrl = 'mailto:?bcc=' + encodeURIComponent(uniqueEmails.join(',')) + '&subject=' + encodeURIComponent('Information — ' + (initialSettings ? initialSettings.event_title : 'Événement ASCIL'));
        window.location.href = mailtoUrl;
        return;
      }

      // Annuler une réservation individuelle
      if (t && t.matches('button.btn-cancel-reg')) {
        e.preventDefault();
        e.stopPropagation();
        var regId = t.getAttribute('data-id');
        var regCode = t.getAttribute('data-code');
        if (!confirm('Voulez-vous vraiment annuler l’inscription ' + regCode + ' ? Les places seront immédiatement libérées.')) {
          return;
        }

        t.setAttribute('disabled', 'true');
        t.textContent = 'Annulation…';

        fetch('/api/admin/events/registrations?id=' + regId, {
          method: 'DELETE',
          credentials: 'same-origin'
        })
        .then(function(r) { return r.json(); })
        .then(function(d) {
          if (d && d.ok) {
            toast('Inscription ' + regCode + ' annulée.');
            loadRegistrations();
          } else {
            t.removeAttribute('disabled');
            t.textContent = 'Annuler';
            toast('Erreur : ' + (d.message || 'Impossible d’annuler l’inscription.'));
          }
        })
        .catch(function() {
          t.removeAttribute('disabled');
          t.textContent = 'Annuler';
          toast('Erreur de connexion.');
        });
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
</script>
'''

XVALS = """
  xvals() {
    /*ascil-inscription*/
    const st = this.state, v = this.v;
    if (!this.evLoad) {
      this.evLoad = true;
      this.evFetch = () => { try { fetch('/api/events/registration-info', { cache: 'no-store' }).then((r) => (r.ok ? r.json() : null)).then((d) => { if (d && d.ok && d.event) this.setState({ ev: d.event }); }).catch(() => {}); } catch (e) {} };
      this.evFetch();
    }
    const ev = st.ev || null;
    const total = ev ? Math.max(0, Number(ev.total_seats) || 0) : 0;
    const taken = ev ? Math.max(0, Number(ev.reserved_seats) || 0) : 0;
    const left = ev ? (typeof ev.remaining_seats === 'number' ? ev.remaining_seats : Math.max(0, total - taken)) : 0;
    const open = !!(ev && ev.is_open && left > 0);
    const maxN = Math.max(1, Math.min(Number(ev && ev.max_per_reg) || 6, left || 1));
    const n = Math.max(1, Math.min(st.n, maxN));
    const r = st.res || null;
    const closedTxt = !ev ? 'Chargement des places…' : (left <= 0 ? 'Complet' : (ev.is_expired ? 'Inscriptions closes (date limite passée)' : 'Inscriptions fermées'));
    return {
      taken, totalSeats: total || 1, maxN, takenPct: total ? Math.min(100, Math.round(taken / total * 100)) : 0,
      placesTxt: !ev ? 'Chargement des places…' : (left > 0 ? left + ' places restantes sur ' + total : 'Complet'),
      formShow: !st.iDone, iDone: st.iDone, formEyebrow: open ? 'Réserver mes places' : closedTxt,
      n, nMinus: () => this.setState({ n: Math.max(1, n - 1) }), nPlus: () => this.setState({ n: Math.min(maxN, n + 1) }),
      iCta: st.busy ? 'Enregistrement…' : (open ? 'Réserver ' + n + ' place' + (n > 1 ? 's' : '') : closedTxt),
      iName: (e) => { v.iname = e.target.value; }, iMail: (e) => { v.imail = e.target.value; },
      iNameErr: !!st.ierr.n, iMailErr: !!st.ierr.m, iNameBd: st.ierr.n ? '#B3261E' : '#CDBF9C', iMailBd: st.ierr.m ? '#B3261E' : '#CDBF9C',
      iFail: !!st.ifail, iFailTxt: st.ifail || '',
      iSend: () => {
        if (st.busy || !open) return;
        const name = (v.iname || (document.getElementById('i1') || {}).value || '').trim();
        const contact = (v.imail || (document.getElementById('i2') || {}).value || '').trim();
        const er = {}; if (name.length < 2) er.n = 1; if (contact.length < 5) er.m = 1;
        if (Object.keys(er).length) return this.setState({ ierr: er, ifail: '' });
        const veg = document.querySelector('.card[aria-live="polite"] input[type="checkbox"]');
        this.setState({ ierr: {}, ifail: '', busy: true });
        fetch('/api/events/register', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name, contact, attendees_count: n, is_vegetarian: !!(veg && veg.checked) }) })
          .then((x) => x.json().catch(() => null))
          .then((d) => {
            if (d && d.ok) { this.setState({ busy: false, iDone: true, res: d }); this.evFetch(); }
            else { this.setState({ busy: false, ifail: (d && (d.message || (d.error && d.error.message))) || 'L\\u2019inscription n\\u2019a pas pu être enregistrée. Réessayez dans un instant.' }); this.evFetch(); }
          })
          .catch(() => this.setState({ busy: false, ifail: 'La connexion a échoué. Vérifiez votre accès à Internet et réessayez.' }));
      },
      doneTitle: 'C\\u2019est réservé !',
      doneText: r ? r.attendees_count + ' place' + (r.attendees_count > 1 ? 's' : '') + (r.event_title ? ' pour ' + r.event_title : '') + (r.date_str ? ', ' + r.date_str : '') + '.' : '',
      code: r ? r.code : '', iAgenda: () => { try { window.__ascilIcs && r && window.__ascilIcs(r.event_title, r.date_str, r.location, 'Réservation ASCIL code ' + r.code); } catch (e) {} this.setState({ iag: true }); },
      iAgendaLab: st.iag ? 'Ajouté à l\\u2019agenda' : 'Ajouter à mon agenda',
      iReset: () => { this.v.iname = ''; this.v.imail = ''; this.setState({ iDone: false, n: 1, res: null, iag: false, ifail: '' }); },
    };
  }
"""

ERR_OLD = '<p class="muted" style="margin:0;font-size:14px">Environ 30 secondes. Aucun compte à créer.</p>'
ERR_NEW = ('<sc-if value="{{iFail}}" hint-placeholder-val="{{ false }}"><p class="err" role="alert" style="margin:0">{{iFailTxt}}</p></sc-if>' + ERR_OLD)


def patch_logic(tpl, name):
    """Remplace la fausse inscription de la maquette (code IFT- inventé, rien d'envoyé) par la vraie."""
    tpl2, k = re.subn(r'\n  xvals\(\) \{\n.*?\n  \}\n(?=\n  /\*ascil-prayer\*/)', lambda _: XVALS, tpl, count=1, flags=re.S)
    assert k == 1, 'xvals introuvable dans ' + name
    for a, b in (('aria-valuemax="80" aria-valuenow="{{taken}}"', 'aria-valuemax="{{totalSeats}}" aria-valuenow="{{taken}}"'),
                 ('<span class="muted" style="font-size:14px">max. 6</span>', '<span class="muted" style="font-size:14px">max. {{maxN}}</span>')):
        if b not in tpl2:
            assert tpl2.count(a) == 1, a + ' introuvable dans ' + name
            tpl2 = tpl2.replace(a, b, 1)
    if '{{iFail}}' not in tpl2:
        assert tpl2.count(ERR_OLD) == 1, 'note du formulaire introuvable dans ' + name
        tpl2 = tpl2.replace(ERR_OLD, ERR_NEW, 1)
    assert "'IFT-'" not in tpl2 and 'ascil-inscription' in tpl2
    return tpl2


def update_file(path, script_tag, script_id):
    content = path.read_text(encoding='utf-8')
    m = re.search(r'<script type="__bundler/template">(.*?)</script>', content, re.S)
    if not m:
        raise ValueError(f"No __bundler/template in {path}")
    tpl = json.loads(m.group(1))

    # Supprime toute version antérieure de ce script
    pat = re.compile(r'<script id="' + re.escape(script_id) + r'">.*?</script>\s*', re.S)
    tpl = pat.sub('', tpl)
    tpl = patch_logic(tpl, path.name)

    # Insère immédiatement avant </body>
    idx_body = tpl.rindex('</body>')
    tpl = tpl[:idx_body] + script_tag + '\n' + tpl[idx_body:]

    enc = json.dumps(tpl).replace('</', '<\\u002F')
    assert json.loads(enc) == tpl

    i = content.index('<script type="__bundler/template">')
    j = content.index('</script>', i)
    new_content = content[:i] + '<script type="__bundler/template">' + enc + content[j:]
    path.write_text(new_content, encoding='utf-8')
    print(f"Modifié avec succès : {path.name} (script #{script_id})")

def main():
    # 1. Le panneau SA-Evenements est relié par wire_evenements.py (inscrits, export, réglages compris).

    # 2. Pages d'inscription publiques
    for name in ['N3-Inscription.dc.html', 'M-N3-Inscription.dc.html', 'T-N3-Inscription.dc.html']:
        p = ROOT / name
        if p.exists():
            update_file(p, PUBLIC_INSCRIPTION_SYNC_SCRIPT, 'ascil-inscription-sync')

if __name__ == '__main__':
    main()
