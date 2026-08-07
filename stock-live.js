// [UI-001] stock-live.js — CRM-driven availability for watch.al (P125 W2).
// DOES:   Fetches https://api.watch.al/public/stock (CRM truth, 60s cache) and
//         flips sold state live. Product pages: #ld-json sku → "Sold" badge +
//         the WhatsApp CTA swapped for a localized "tell me when it's back"
//         link. Brand pages: #brandGrid cards flipped by their "Ref." line.
//         Linked refs are governed in BOTH directions (restock un-flips with
//         no manual step); unlinked refs and failed fetches leave the static
//         page standing.
// IN:     Page DOM; <html lang> selects the strings (en / sq / it).
// OUT:    Class toggles (.stock-oos on #watch-content, .sold-card on cards) +
//         one injected <style>. No storage, no other requests; JSON-LD is
//         untouched (the rebuild leg owns what crawlers see).
// CALLS:  GET api.watch.al/public/stock (CSP connect-src — see [SEC-002]).
// NOTES:  Fail-closed: no data → no change; availability is never invented.
//         Trusted-Types-safe (no innerHTML anywhere). The shop index is NOT
//         handled here — shop.js merges live stock into its own data before
//         rendering ([UI-002]). Contract: part-tracker repo, docs/CRM_SYNC.md.
(function(){
  var STRINGS = {
    en: { sold: 'Sold', notify: 'Tell me when it’s back', avail: 'Availability', availSold: 'Sold out',
          msg: 'Hi! The {W} (Ref. {R}) on watch.al is sold out - please let me know when it is back.' },
    sq: { sold: 'Shitur', notify: 'Më njofto kur të kthehet', avail: 'Disponueshmëria', availSold: 'E shitur',
          msg: 'Përshëndetje! {W} (Ref. {R}) në watch.al është shitur - më njoftoni kur të kthehet ju lutem.' },
    it: { sold: 'Venduto', notify: 'Avvisami quando torna', avail: 'Disponibilità', availSold: 'Esaurito',
          msg: 'Ciao! Il {W} (Rif. {R}) su watch.al è esaurito - avvisatemi quando torna disponibile.' }
  };
  var lang = (document.documentElement.getAttribute('lang') || 'en').slice(0, 2);
  var L = STRINGS[lang] || STRINGS.en;

  var product = document.getElementById('ld-json') && document.getElementById('watch-content');
  var brandGrid = document.getElementById('brandGrid');
  if (!product && !brandGrid) return;
  if (document.getElementById('shopGrid')) return;   // shop.js owns the index grid

  var st = document.createElement('style');
  st.textContent =
    '.stock-oos-badge{display:none}' +
    // width:fit-content — the badge lands in .watch-info's flex column, where
    // inline-block blockifies and default stretch would draw a full-width bar
    '.stock-oos .stock-oos-badge{display:inline-block;width:fit-content;background:#8a2b20;color:#fff;font-weight:700;font-size:.85rem;letter-spacing:.04em;padding:.35rem .95rem;border-radius:9999px;margin:0}' +
    '.stock-oos .watch-cta-main:not(.stock-notify){display:none!important}' +
    '.stock-notify{display:none}' +
    '.stock-oos .stock-notify{display:inline-flex!important;background:#6d6a63}' +
    '.sold-card .watch-cta{display:none!important}' +
    // brand grids only: undo the whole-card fade (it drowned the overlay text
    // to ~1.8:1), fade the photo and body instead, and darken the scrim
    '#brandGrid .watch-card.sold-card{opacity:1}' +
    '#brandGrid .sold-card .watch-card-img picture,#brandGrid .sold-card .watch-card-body{opacity:.55}' +
    '#brandGrid .sold-card .sold-overlay{background:rgba(0,0,0,.62)}';
  document.head.appendChild(st);

  // "Ref. X" / "Rif. X" → the normalized key the CRM publishes
  function norm(s){ return String(s || '').replace(/^\s*(Ref\.|Rif\.)\s*/i, '').trim().toUpperCase(); }

  fetch('https://api.watch.al/public/stock')
    .then(function(r){ if (!r.ok) throw new Error('http ' + r.status); return r.json(); })
    .then(function(d){
      if (!d || !d.stock) return;
      if (product) applyProduct(d.stock);
      if (brandGrid) applyCards(d.stock, brandGrid);
    })
    .catch(function(){ /* fail-closed: the static page (kept true by the rebuild leg) stands */ });

  // [UI-001.a] product page: badge before the CTA row, notify link inside it,
  // everything driven by ONE class so the rebuild leg can pre-render the same
  // state statically and this layer can un-flip it when stock returns.
  function applyProduct(stock){
    var ld = null;
    try { ld = JSON.parse(document.getElementById('ld-json').textContent); } catch (e) { return; }
    var sku = norm(ld && ld.sku);
    if (!sku || !Object.prototype.hasOwnProperty.call(stock, sku)) return;   // unlinked: static stands
    var root = document.getElementById('watch-content');
    var wrap = root && root.querySelector('.watch-cta-wrap');
    if (!root || !wrap) return;
    if (!root.querySelector('.stock-oos-badge')) {
      var b = document.createElement('p');
      b.className = 'stock-oos-badge';
      b.textContent = L.sold;
      wrap.parentNode.insertBefore(b, wrap);
    }
    if (!wrap.querySelector('.stock-notify')) {
      // every catalog name already starts with the brand — prepend only when
      // it doesn't, or the message reads "Hislon Hislon Classic"
      var brandNm = ld.brand && ld.brand.name ? String(ld.brand.name) : '';
      var baseNm = String(ld.name || '');
      var name = ((brandNm && baseNm.toLowerCase().indexOf(brandNm.toLowerCase()) !== 0 ? brandNm + ' ' : '') + baseNm).trim() || 'watch';
      var a = document.createElement('a');
      a.className = 'watch-cta-main stock-notify';
      a.target = '_blank';
      a.rel = 'noopener noreferrer';
      a.href = 'https://api.whatsapp.com/send?phone=355676360510&text=' +
        encodeURIComponent(L.msg.replace('{W}', name).replace('{R}', sku));
      var i = document.createElement('i');
      i.className = 'fab fa-whatsapp';
      i.setAttribute('aria-hidden', 'true');
      a.appendChild(i);
      a.appendChild(document.createTextNode(' ' + L.notify));
      wrap.appendChild(a);
    }
    var soldOut = stock[sku] === 0;
    root.classList.toggle('stock-oos', soldOut);
    // [UI-001.c] the visible "Availability" spec row lives in #watch-extra, a
    // SIBLING of the flipped subtree — left alone it would keep saying
    // "In stock in Durrës" under a Sold badge. Original text is stashed so a
    // restock restores it verbatim.
    var dts = document.querySelectorAll('#watch-extra dt');
    for (var k = 0; k < dts.length; k++) {
      if (dts[k].textContent.trim() !== L.avail) continue;
      var dd = dts[k].nextElementSibling;
      if (!dd) break;
      if (soldOut) {
        if (!dd.getAttribute('data-stock-orig')) dd.setAttribute('data-stock-orig', dd.textContent);
        dd.textContent = L.availSold;
      } else if (dd.getAttribute('data-stock-orig')) {
        dd.textContent = dd.getAttribute('data-stock-orig');
        dd.removeAttribute('data-stock-orig');
      }
      break;
    }
  }

  // [UI-001.b] brand grids: flip static cards. A card whose static state was
  // pre-rendered sold (no CTA in the DOM) just loses the overlay on restock —
  // the buy path is one click deeper, on the product page, which flips fully.
  function applyCards(stock, grid){
    var cards = grid.querySelectorAll('.watch-card');
    for (var k = 0; k < cards.length; k++) {
      var card = cards[k];
      var refEl = card.querySelector('.watch-ref');
      var ref = norm(refEl && refEl.textContent);
      if (!ref || !Object.prototype.hasOwnProperty.call(stock, ref)) continue;   // unlinked: static stands
      var soldOut = stock[ref] === 0;
      card.classList.toggle('sold-card', soldOut);
      var img = card.querySelector('.watch-card-img');
      var ov = img && img.querySelector('.sold-overlay');
      if (soldOut && img && !ov) {
        var o = document.createElement('div');
        o.className = 'sold-overlay';
        o.textContent = L.sold;
        img.appendChild(o);
      } else if (!soldOut && ov) {
        ov.parentNode.removeChild(ov);
      }
    }
  }
})();
