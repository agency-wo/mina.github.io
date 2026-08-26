// [UI-016] shop.js — the SQ shop index controller: filter state and the grid.
// DOES:   fetches watches.json, merges the live CRM stock feed into it BEFORE
//         the first render, then owns every piece of filter state (condition
//         chip, brand chip, search term, sort, price window) and repaints
//         #shopGrid on each change. Brand chips are built from the data, seeded
//         from ?brand= and written back to the URL, so a filtered grid is a
//         link somebody can send.
// IN:     watches.json over the network; .filter-chip, #brandChips, #styleChips, #shopSearch,
//         #shopSort, #priceSliderWrap; ?brand= on the query string.
// OUT:    #shopGrid innerHTML, the #shopCount line, one WhatsApp link per card.
// CALLS:  /watches.json, same-origin; api.watch.al/public/stock
//         (the [UI-002] block below; [SEC-002] owns the CSP that allows it).
// NOTES:  THE INVARIANT: watchCard() mirrors gen_shop_index.card() ([DB-007.b])
//         BYTE FOR BYTE, down to the \u00a0 before the L in a Lek price. The
//         page ships pre-rendered and this file repaints it from the same data,
//         so one differing byte is a visible flicker on hydration. Change one
//         and change the other in the same edit, or keep the change CSS-only.
//         A SECOND renderer (watch.js) was deleted for printing NaN Lek prices;
//         never add another.
//         The stock merge is capped at 4s by Promise.race on purpose: a hung,
//         blackholed route neither resolves nor rejects, and an optional feed
//         must never hold the chips, search and sort hostage. See [UI-002].
//         The three copies are NOT identical: 269, 195 and 199 lines of code in
//         en, it and sq before these headers went in. All three carry the
//         dual-handle price slider (bounds derived from the catalogue, 5-euro snap)
//         since 2026-08-20; before that EN alone did and this one rendered dead.
//         This file also prints Lek FIRST and carries lekVal() for it, which no
//         other copy has, so the sub-indices below run one letter further from
//         .e on. Nothing ships in one language: all three change in one edit.
(function(){
  var condMap = {'New':'I ri','Pre-owned':'I p\u00ebrdorur'};
  var currentFilter = 'all';
  var currentBrand  = 'all';
  var currentSearch = '';
  var BRAND_ALL_LABEL = 'Të gjitha markat';
  var currentSort   = 'default';
  var currentStyle  = 'all';
  var STYLE_ORDER = ['chronograph','dress','sport','digital','gold-tone','moonphase'];
  var STYLE_ALL_LABEL = 'Të gjitha stilet';
  var STYLE_LABELS = {'chronograph':'Kronograf','dress':'Veshjeje','sport':'Sportive','digital':'Dixhitale','gold-tone':'Ngjyrë ari','moonphase':'Fazat e hënës'};
  var currentMinPrice = 50;
  var currentMaxPrice = 200;
  // seeded only; the real bounds are derived from WATCHES below
  var PRICE_MIN = 50, PRICE_MAX = 200;
  // Swiss Made marked on the physical watch, owner-verified; mirrors shop_bits.SWISS_BRANDS
  var SWISS_BRANDS = ['Hislon', 'Cortébert'];

  // [UI-002] live CRM stock (P125): merged into the catalog BEFORE any render.
  // Linked refs are governed in both directions; a failed fetch changes
  // nothing (fail-closed — the pre-rendered sold flags stand).
  // Promise.race: a HUNG connection (blackholed route) neither resolves nor
  // rejects for 30s+ — without the 4s cap it would hold every shop control
  // (chips, search, sort, slider) hostage to an optional feed.
  var stockFetch = Promise.race([
    fetch('https://api.watch.al/public/stock').then(function(r){ return r.ok ? r.json() : null; }),
    new Promise(function(res){ setTimeout(function(){ res(null); }, 4000); })
  ]).catch(function(){ return null; });

  fetch('/watches.json?v=3')
    .then(function(r){ return r.json(); })
    .then(function(WATCHES){
      return stockFetch.then(function(live){
        if(live && live.stock){
          WATCHES.forEach(function(w){
            var ref = String(w.reference || '').trim().toUpperCase();
            if(ref && Object.prototype.hasOwnProperty.call(live.stock, ref)) w.sold = live.stock[ref] === 0;
          });
        }
        return WATCHES;
      });
    })
    .then(function(WATCHES){
      // [UI-016.f] Slider bounds come from the CATALOGUE, never from a constant.
      // They were 50 and 200, and renderWatches drops anything above
      // currentMaxPrice, so a 249 euro watch was unreachable by the filter and
      // vanished from the pre-rendered grid the moment this script hydrated.
      // gen_shop_index rewrites this page in place and never touches the slider
      // markup, so nothing else could have healed it.
      // Rounded outward to a multiple of 5 because the handles snap in 5s: a
      // max of 249 could never be reached by a snapped handle.
      (function(){
        var ps = [];
        WATCHES.forEach(function(w){ if(!w.deleted && w.price) ps.push(w.price); });
        if(!ps.length) return;
        PRICE_MIN = Math.floor(Math.min.apply(null, ps) / 5) * 5;
        PRICE_MAX = Math.ceil(Math.max.apply(null, ps) / 5) * 5;
        if(PRICE_MAX <= PRICE_MIN) PRICE_MAX = PRICE_MIN + 5;
        currentMinPrice = PRICE_MIN;
        currentMaxPrice = PRICE_MAX;
      })();
      initBrandChips(WATCHES);
      initStyleChips(WATCHES);
      renderWatches(WATCHES);

      document.querySelectorAll('.filter-chip:not([data-brand]):not([data-style])').forEach(function(chip){
        chip.addEventListener('click', function(){
          document.querySelectorAll('.filter-chip:not([data-brand]):not([data-style])').forEach(function(c){ c.classList.remove('active'); c.removeAttribute('aria-pressed'); });
          chip.classList.add('active');
          chip.setAttribute('aria-pressed','true');
          currentFilter = chip.dataset.filter;
          renderWatches(WATCHES);
        });
      });

      var searchInput = document.getElementById('shopSearch');
      if(searchInput){
        function onSearch(){ currentSearch = searchInput.value.trim().toLowerCase(); renderWatches(WATCHES); }
        searchInput.addEventListener('input', onSearch);
        searchInput.addEventListener('search', onSearch);
      }

      var sortEl = document.getElementById('shopSort');
      if(sortEl){
        sortEl.addEventListener('change', function(){ currentSort = this.value; renderWatches(WATCHES); });
      }

      var priceWrap = document.getElementById('priceSliderWrap');
      var priceFill = document.getElementById('priceSliderFill');
      var handleMin = document.getElementById('handleMin');
      var handleMax = document.getElementById('handleMax');
      if(priceWrap && handleMin && handleMax){
        var minVal = PRICE_MIN, maxVal = PRICE_MAX;
        handleMin.setAttribute('aria-valuemin', PRICE_MIN);
        handleMin.setAttribute('aria-valuemax', PRICE_MAX);
        handleMax.setAttribute('aria-valuemin', PRICE_MIN);
        handleMax.setAttribute('aria-valuemax', PRICE_MAX);
        var pctOf = function(v){ return (v - PRICE_MIN) / (PRICE_MAX - PRICE_MIN) * 100; };
        var snapVal = function(v){ return Math.round(v / 5) * 5; };
        var applyPricePos = function(){
          handleMin.style.left = pctOf(minVal) + '%';
          handleMax.style.left = pctOf(maxVal) + '%';
          priceFill.style.left  = pctOf(minVal) + '%';
          priceFill.style.width = (pctOf(maxVal) - pctOf(minVal)) + '%';
          handleMin.setAttribute('aria-valuenow', minVal);
          handleMax.setAttribute('aria-valuenow', maxVal);
          var disp = document.getElementById('priceRangeDisplay');
          if(disp) disp.textContent = '€' + minVal + ' - €' + maxVal;
          currentMinPrice = minVal;
          currentMaxPrice = maxVal;
          renderWatches(WATCHES);
        };
        var onSliderStart = function(e){
          e.preventDefault();
          var cx = e.touches ? e.touches[0].clientX : e.clientX;
          var rect = priceWrap.getBoundingClientRect();
          var frac = Math.max(0, Math.min(1, (cx - rect.left) / rect.width));
          var val  = snapVal(PRICE_MIN + frac * (PRICE_MAX - PRICE_MIN));
          var isMin = Math.abs(val - minVal) <= Math.abs(val - maxVal);
          if(isMin) minVal = Math.min(val, maxVal);
          else maxVal = Math.max(val, minVal);
          applyPricePos();
          var onMove = function(ev){
            ev.preventDefault();
            var rect2 = priceWrap.getBoundingClientRect();
            var cx2 = ev.touches ? ev.touches[0].clientX : ev.clientX;
            var f2  = Math.max(0, Math.min(1, (cx2 - rect2.left) / rect2.width));
            var v2  = snapVal(PRICE_MIN + f2 * (PRICE_MAX - PRICE_MIN));
            if(isMin) minVal = Math.min(v2, maxVal);
            else maxVal = Math.max(v2, minVal);
            applyPricePos();
          };
          var onEnd = function(){
            document.removeEventListener('mousemove', onMove);
            document.removeEventListener('mouseup',   onEnd);
            document.removeEventListener('touchmove', onMove);
            document.removeEventListener('touchend',  onEnd);
          };
          document.addEventListener('mousemove', onMove);
          document.addEventListener('mouseup',   onEnd);
          document.addEventListener('touchmove', onMove, {passive:false});
          document.addEventListener('touchend',  onEnd);
        };
        priceWrap.addEventListener('mousedown',  onSliderStart);
        priceWrap.addEventListener('touchstart', onSliderStart, {passive:false});
        handleMin.addEventListener('keydown', function(e){
          if(e.key==='ArrowLeft')       minVal = Math.max(PRICE_MIN, minVal-5);
          else if(e.key==='ArrowRight') minVal = Math.min(maxVal, minVal+5);
          else return;
          applyPricePos();
        });
        handleMax.addEventListener('keydown', function(e){
          if(e.key==='ArrowLeft')       maxVal = Math.max(minVal, maxVal-5);
          else if(e.key==='ArrowRight') maxVal = Math.min(PRICE_MAX, maxVal+5);
          else return;
          applyPricePos();
        });
        applyPricePos();
      }
    })
    .catch(function(){
      // keep the pre-rendered grid if the live fetch fails (stale cache / offline)
      var g = document.getElementById('shopGrid');
      var _shopHasPre = g && g.querySelector('.watch-card');
      if(_shopHasPre) return;
      if(g) g.innerHTML = '<p class="no-watches">Nuk mund të ngarkohen orët. Rifresko faqen.</p>';
    });

  // [UI-016.a] initBrandChips — the brand row is DERIVED, never a typed list
  // DOES:   tallies live watches per brand, orders by count then name, draws the
  //         chip row and wires ONE delegated click handler on the wrapper.
  // NOTES:  nothing here is hard-coded, so a new brand appears the moment it
  //         lands in watches.json and a retired one leaves no dead chip behind.
  //         ?brand= is read on load and written back with replaceState, never
  //         pushState: the back button must leave the shop, not walk the visitor
  //         back through one filter click at a time.
  function initBrandChips(WATCHES){
    var wrap = document.getElementById('brandChips');
    if(!wrap) return;
    var counts = {};
    WATCHES.forEach(function(w){ if(w.brand && !w.deleted) counts[w.brand] = (counts[w.brand]||0) + 1; });
    var brands = Object.keys(counts).sort(function(a,b){ return (counts[b]-counts[a]) || a.localeCompare(b); });

    var param = '';
    try { param = (new URLSearchParams(window.location.search).get('brand') || '').toLowerCase(); } catch(e){}
    brands.forEach(function(b){ if(b.toLowerCase() === param) currentBrand = b; });

    var html = ['<button class="filter-chip' + (currentBrand==='all' ? ' active" aria-pressed="true' : '') + '" data-brand="all">' + BRAND_ALL_LABEL + '</button>'];
    brands.forEach(function(b){
      var esc = b.replace(/"/g, '&quot;');
      html.push('<button class="filter-chip' + (currentBrand===b ? ' active" aria-pressed="true' : '') + '" data-brand="' + esc + '">' + b + '</button>');
    });
    wrap.innerHTML = html.join('');

    wrap.addEventListener('click', function(e){
      var chip = e.target.closest ? e.target.closest('[data-brand]') : null;
      if(!chip) return;
      wrap.querySelectorAll('[data-brand]').forEach(function(c){ c.classList.remove('active'); c.removeAttribute('aria-pressed'); });
      chip.classList.add('active');
      chip.setAttribute('aria-pressed','true');
      currentBrand = chip.dataset.brand;
      try {
        var u = new URL(window.location.href);
        if(currentBrand === 'all') u.searchParams.delete('brand');
        else u.searchParams.set('brand', currentBrand);
        history.replaceState(null, '', u.pathname + (u.search || '') + (u.hash || ''));
      } catch(err){}
      renderWatches(WATCHES);
    });
  }

  // styleChips mirrors initBrandChips: data-driven, so a style appears the
  // moment a watch in watches.json carries it, and vanishes when none does.
  function initStyleChips(WATCHES){
    var wrap = document.getElementById('styleChips');
    if(!wrap) return;
    var present = STYLE_ORDER.filter(function(s){
      return WATCHES.some(function(w){ return !w.deleted && (w.styles||[]).indexOf(s) !== -1; });
    });
    if(!present.length) return;
    var html = ['<button class="filter-chip active" aria-pressed="true" data-style="all">' + STYLE_ALL_LABEL + '</button>'];
    present.forEach(function(s){
      html.push('<button class="filter-chip" data-style="' + s + '">' + (STYLE_LABELS[s]||s) + '</button>');
    });
    wrap.innerHTML = html.join('');
    wrap.addEventListener('click', function(e){
      var chip = e.target.closest ? e.target.closest('[data-style]') : null;
      if(!chip) return;
      wrap.querySelectorAll('[data-style]').forEach(function(c){ c.classList.remove('active'); c.removeAttribute('aria-pressed'); });
      chip.classList.add('active');
      chip.setAttribute('aria-pressed','true');
      currentStyle = chip.dataset.style;
      renderWatches(WATCHES);
    });
  }

  // [UI-016.b] renderWatches — the ONE render path: filter, sort, repaint
  // DOES:   applies condition, brand, search and the price window in that order,
  //         sorts, then replaces #shopGrid wholesale. It writes no count.
  // NOTES:  full repaint on purpose. Nothing mutates a card in place, so the grid
  //         can never show a half-applied filter. With a search term and sort
  //         left at default, a prefix hit on brand or model is scored to the top,
  //         so typing "his" lands Hislon first instead of alphabetically.
  function renderWatches(watches){
    // [DB-006] deleted (retired) entries leave the catalog everywhere; SOLD
    // ones stay visible with their badge — the two must never be confused
    var filtered = watches.filter(function(w){ return !w.deleted; });
    if(currentFilter !== 'all') filtered = filtered.filter(function(w){ return w.condition === currentFilter; });

    if(currentBrand !== 'all'){
      filtered = filtered.filter(function(w){ return w.brand === currentBrand; });
    }

    if(currentStyle !== 'all'){
      filtered = filtered.filter(function(w){ return (w.styles||[]).indexOf(currentStyle) !== -1; });
    }

    if(currentSearch){
      var s = currentSearch;
      filtered = filtered.filter(function(w){
        return (w.model+' '+w.brand+' '+(w.reference||'')+' '+(w.description_sq||'')).toLowerCase().includes(s);
      });
    }

    filtered = filtered.filter(function(w){
      // an unpriced watch (Price on request) is exempt from the price window:
      // 0 would fail the lower bound and the card would vanish on hydration
      return !w.price || ((w.price||0) >= currentMinPrice && (w.price||0) <= currentMaxPrice);
    });

    // Sort
    if(currentSearch && currentSort === 'default'){
      var s = currentSearch;
      filtered.sort(function(a,b){
        var aScore = (a.brand.toLowerCase().startsWith(s)?2:0)+(a.model.toLowerCase().startsWith(s)?1:0);
        var bScore = (b.brand.toLowerCase().startsWith(s)?2:0)+(b.model.toLowerCase().startsWith(s)?1:0);
        return bScore - aScore;
      });
    } else if(currentSort === 'price-asc'){
      filtered.sort(function(a,b){ return (a.price||0)-(b.price||0); });
    } else if(currentSort === 'price-desc'){
      filtered.sort(function(a,b){ return (b.price||0)-(a.price||0); });
    } else if(currentSort === 'brand'){
      filtered.sort(function(a,b){ return (a.brand+a.model).localeCompare(b.brand+b.model); });
    }

    var grid  = document.getElementById('shopGrid');
    // NO COUNT HERE, DELIBERATELY. This used to write "<n> watches available"
    // into #shopCount on every render. That is a published count of the
    // catalogue, which CLAUDE.md forbids in digits or in words, because the
    // shop holds more stock than it lists and any number understates the
    // shelf. It survived because all three layers that enforce the rule read
    // static HTML (catalog_stats.TOKEN_RE, gen_stats.render, verify-stats
    // check G) and this number was assembled at runtime. #shopCount now
    // carries a fixed line in the HTML. Do not write to it, and do not add a
    // count back: verify-stats.py check H reads this file and will fail.
    // Sold cards stay in the grid with their badge; they are simply not for sale.
    if(!filtered.length){
      grid.innerHTML = '<p class="no-watches">Asnj\u00eb or\u00eb nuk p\u00ebrputhet me k\u00ebt\u00eb filtro tani. Kthehuni s\u00eb shpejti!</p>';
      return;
    }
    grid.innerHTML = filtered.map(function(w){ return watchCard(w); }).join('');
  }



  // Lek per euro. MIRRORS catalog_stats.LEK_RATE -- change both together;
  // verify-stats.py check C now fails the build if they disagree.
  var EUR_TO_LEK = 92.25;
  var SEP = '.';
  /* Comma in EN, dot in IT and SQ. Mirrors catalog_stats.SEP byte for byte.
     Never toLocaleString(): it asks the browser for the separator, so an
     Italian phone reflowed the grid from 18,300 L to 18.300 L after hydration
     and the rendered page disagreed with the HTML the server sent. */
  // [UI-016.c] group — the thousands separator, fixed per language by hand
  // NOTES:  the note just above is the reason. The browser is never asked:
  //         toLocaleString() reads the phone's locale, and an Italian phone
  //         reflowed the grid from 18,300 L to 18.300 L after hydration, so the
  //         rendered page disagreed with the HTML the server had just sent.
  function group(n){ return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, SEP); }
  // [UI-016.d] fmt — the euro figure, or an honest fallback
  // NOTES:  a missing or zero price prints "Çmimi me kërkesë", never a
  //         zero. No price in the data is a data hole, and a hole must never
  //         read as a free watch.
  function fmt(price, currency){
    if(!price) return '<span class="por">\u00c7mimi me k\u00ebrkes\u00eb</span>';
    return (currency === 'EUR' ? '\u20ac' : currency) + group(price);
  }
  // [UI-016.e] lekVal — the Lek figure as a number, for the SQ price line
  // NOTES:  SQ leads with Lek and demotes the euro figure to the aside, because
  //         Albanian customers judge the Lek number; EN and IT do the opposite
  //         and never needed the value split out of its markup. Same half-up
  //         rounding as fmtLek below, so the two can never disagree about the
  //         same watch.
  function lekVal(price, currency){
    if(!price || currency !== 'EUR') return 0;
    return Math.round(price * EUR_TO_LEK / 100) * 100;
  }
  // [UI-016.f] fmtLek — the euro-first Lek suffix, and DEAD in this file
  // NOTES:  nothing here calls it. watchCard() below builds the SQ price line
  //         itself from lekVal(), and this stayed behind when the order flipped.
  //         It is the byte-for-byte twin of the EN and IT copies, which is the
  //         reason to leave it: it keeps the three files diffable, and it is the
  //         shape to restore if SQ ever goes back to euro-first.
  function fmtLek(price, currency){
    if(!price || currency !== 'EUR') return '';
    return '<span style="font-size:.78rem;color:#888;font-weight:400"> \u00b7 ' + group(Math.round(price * EUR_TO_LEK / 100) * 100) + '\u00a0L</span>';
  }

  // [UI-016.g] waMsg — the prefilled WhatsApp message, which IS the checkout
  // NOTES:  there is no cart and no payment page on this site, so this link is
  //         the whole conversion path. The message carries brand, model and
  //         reference because the owner answers these on a phone and must not
  //         have to ask which watch the customer is looking at.
  function waMsg(w){
    var msg = 'Pershendetje, jam i interesuar per oren ' + w.brand + ' ' + w.model + (w.reference ? ' (Ref. ' + w.reference + ')' : '') + ' ne faqen tuaj.';
    return 'https://api.whatsapp.com/send?phone=355676360510&text=' + encodeURIComponent(msg);
  }

  // [UI-016.h] watchCard — the card markup, and the mirror half of the site
  // DOES:   builds one <article class="watch-card"> exactly as
  //         gen_shop_index.card() does: picture/webp source, sold overlay,
  //         condition badge, sale badge, brand (+ the Swiss tag on Hislon),
  //         model, ref line, description, price block, Instagram link, CTA.
  // NOTES:  THIS IS THE MIRROR. Static equals runtime: the page arrives
  //         pre-rendered by gen_shop_index.py and this function repaints it
  //         from the same watches.json, so a single differing byte shows up as
  //         a flicker the moment the fetch lands. Change this and change
  //         [DB-007.b] in the same edit, or make the change CSS-only. A second
  //         renderer (watch.js) was deleted once for producing NaN Lek prices;
  //         do not reintroduce one.
  function watchCard(w){
    var cond = condMap[w.condition] || w.condition;
    var imgHtml = w.image
      ? '<a href="/sq/shop/' + w.id + '.html" aria-label="' + w.brand + ' ' + w.model + (SWISS_BRANDS.indexOf(w.brand) !== -1 ? ' Swiss Watch' : '') + '"><picture><source srcset="' + w.image.replace(/\.jpe?g$/i, '.webp') + '" type="image/webp"><img src="' + w.image + '" alt="' + w.brand + ' ' + w.model + (SWISS_BRANDS.indexOf(w.brand) !== -1 ? ' Swiss Watch' : '') + '" loading="lazy"></picture></a>'
      : '<div class="watch-img-placeholder"><i class="fas fa-clock" aria-hidden="true"></i></div>';
    var soldOverlay = w.sold ? '<div class="sold-overlay">Shitur</div>' : '';
    var ctaHtml = w.sold
      ? '<span style="font-size:.82rem;color:#888">Shitur</span>'
      : '<a href="' + waMsg(w) + '" target="_blank" rel="noopener noreferrer" class="watch-cta" data-fb-contact="1" aria-label="Pyesni per ' + w.brand + ' ' + w.model + ' ne WhatsApp"><i class="fab fa-whatsapp" aria-hidden="true"></i> Pyesni</a>';
    return '<article class="watch-card' + (w.sold?' sold-card':'') + '">'
      + '<div class="watch-card-img">' + imgHtml + soldOverlay
      + '<span class="watch-badge">' + cond + '</span>'
      + (w.originalPrice ? '<span class="sale-badge">−10%</span>' : '')
      + '</div>'
      + '<div class="watch-card-body">'
      + '<p class="watch-brand">' + w.brand + (SWISS_BRANDS.indexOf(w.brand) !== -1 ? '<span style="font-size:.65rem;letter-spacing:.08em;text-transform:uppercase;color:#8a9abf;font-weight:500;margin-left:.4rem;vertical-align:middle">Swiss</span>' : '') + '</p>'
      + '<h2 class="watch-model">' + w.model + '</h2>'
      + (w.reference ? '<p class="watch-ref">Ref. ' + w.reference + '</p>' : '')
      + '<p class="watch-desc">' + (w.description_sq || '') + '</p>'
      + '<div class="watch-card-footer">'
      + '<div>'
      + '<p class="watch-price">' + /* LEK_FIRST: Albanian customers judge the Lek figure */ (lekVal(w.price,w.currency) ? group(lekVal(w.price,w.currency)) + ' L<span style="font-size:.78rem;color:#888;font-weight:400"> · ' + fmt(w.price,w.currency) + '</span>' : fmt(w.price, w.currency)) + '</p>'
      + (w.originalPrice ? '<p class="was-price-line">Was ' + (w.currency==='EUR'?'\u20ac':w.currency) + w.originalPrice + '</p>' : '')
      + '</div>'
      + '<a href="https://instagram.com/iglisiwatch" target="_blank" rel="noopener noreferrer" class="watch-ig-link" aria-label="Shiko n\u00eb Instagram"><i class="fab fa-instagram" aria-hidden="true"></i></a>'
      + ctaHtml
      + '</div></div></article>';
  }
})();
