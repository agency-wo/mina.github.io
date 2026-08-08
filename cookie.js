// [UX-002] cookie.js — cookie consent banner + preferences modal (analytics on/off)
// DOES:   shows the banner until a versioned choice exists, persists {v, ts,
//         analytics} in localStorage under 'iglisi_consent', and broadcasts every
//         decision as the 'iglisi:consent' CustomEvent (pixel.js listens for it).
// IN:     #cookie-banner / #cookie-modal-overlay markup the page already carries
// OUT:    localStorage + banner/modal visibility + the consent event; focus is
//         trapped inside the open modal and restored on close
// NOTES:  no stored choice means "not asked yet", never "denied" — closing the
//         modal without saving re-shows the banner.
/* Cookie consent manager */
(function () {
  'use strict';
  var KEY = 'iglisi_consent', VER = '1';
  var _prevFocus = null;

  // [UX-002.a] getConsent — the stored decision, or null
  // DOES:   returns the parsed record only when its version matches VER, so a schema
  //         bump automatically re-asks everyone; corrupt JSON also reads as "no choice".
  function getConsent() {
    try { var d = JSON.parse(localStorage.getItem(KEY) || 'null'); return d && d.v === VER ? d : null; } catch (e) { return null; }
  }
  // [UX-002.b] saveConsent — persist AND announce a decision
  // DOES:   writes the versioned record, then fires 'iglisi:consent' so consumers
  //         (pixel.js) can react without polling storage; both steps fail-soft.
  function saveConsent(prefs) {
    try { localStorage.setItem(KEY, JSON.stringify({ v: VER, ts: Date.now(), analytics: prefs.analytics })); } catch (e) {}
    try { document.dispatchEvent(new CustomEvent('iglisi:consent', { detail: prefs })); } catch (e) {}
  }
  function el(id) { return document.getElementById(id); }

  function showBanner() { var b = el('cookie-banner'); if (b) { b.hidden = false; b.removeAttribute('hidden'); } }
  function hideBanner() { var b = el('cookie-banner'); if (b) b.hidden = true; }

  // [UX-002.c] openModal — preferences dialog
  // DOES:   remembers the trigger element for focus restoration, pre-checks the
  //         analytics toggle from the stored choice (default: checked when no
  //         explicit refusal exists), and moves focus to the first control.
  function openModal() {
    var m = el('cookie-modal-overlay');
    if (!m) return;
    _prevFocus = document.activeElement;
    m.hidden = false;
    m.removeAttribute('hidden');
    var cb = el('cookie-toggle-analytics');
    var consent = getConsent();
    if (cb) cb.checked = !consent || consent.analytics !== false;
    var focusable = m.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
    if (focusable.length) focusable[0].focus();
  }

  // [UX-002.d] closeModal — dismiss + give focus back to whoever opened it
  function closeModal() {
    var m = el('cookie-modal-overlay');
    if (m) m.hidden = true;
    if (_prevFocus && _prevFocus.focus) { _prevFocus.focus(); }
    _prevFocus = null;
  }

  // The three terminal decisions: each persists a choice and tears the UI down.
  // analytics:false is an explicit refusal, distinct from never having answered.
  function acceptAll() { saveConsent({ analytics: true }); hideBanner(); closeModal(); }
  function rejectAll() { saveConsent({ analytics: false }); hideBanner(); closeModal(); }
  function savePrefs() { var cb = el('cookie-toggle-analytics'); saveConsent({ analytics: cb ? cb.checked : false }); hideBanner(); closeModal(); }

  // [UX-002.e] init — wire every control the page happens to carry
  // DOES:   binds banner buttons, modal buttons, the footer re-open trigger, the
  //         overlay click-out, the Tab focus trap and the Escape close; finally shows
  //         the banner if no decision is stored. Every lookup is null-guarded so
  //         pages with partial markup still work.
  function init() {
    var b1 = el('cookie-accept-all'), b2 = el('cookie-reject-non-essential'), b3 = el('cookie-customize');
    var mc = el('cookie-modal-close'), ms = el('cookie-save-preferences');
    var ftrig = el('footer-cookie-settings');
    var overlay = el('cookie-modal-overlay');

    if (b1) b1.addEventListener('click', acceptAll);
    if (b2) b2.addEventListener('click', rejectAll);
    if (b3) b3.addEventListener('click', function () { hideBanner(); openModal(); });
    if (mc) mc.addEventListener('click', function () { closeModal(); if (!getConsent()) showBanner(); });
    if (ms) ms.addEventListener('click', savePrefs);
    if (ftrig) ftrig.addEventListener('click', showBanner);
    if (overlay) overlay.addEventListener('click', function (e) { if (e.target === overlay) { closeModal(); if (!getConsent()) showBanner(); } });

    /* Focus trap: keep Tab cycling within the modal while it is open */
    if (overlay) overlay.addEventListener('keydown', function (e) {
      if (e.key !== 'Tab') return;
      var focusable = overlay.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
      if (!focusable.length) return;
      var first = focusable[0], last = focusable[focusable.length - 1];
      if (e.shiftKey) {
        if (document.activeElement === first) { e.preventDefault(); last.focus(); }
      } else {
        if (document.activeElement === last) { e.preventDefault(); first.focus(); }
      }
    });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') { closeModal(); if (!getConsent()) showBanner(); }
    });

    if (!getConsent()) showBanner();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
