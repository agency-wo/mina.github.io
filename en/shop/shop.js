(function(){
  var currentFilter = 'all';
  var currentBrand  = 'all';
  var currentSearch = '';
  var currentSort   = 'default';
  var BRAND_ALL_LABEL = 'All brands';
  var currentMinPrice = 50;
  var currentMaxPrice = 200;
  var PRICE_MIN = 50, PRICE_MAX = 200;

  fetch('https://raw.githubusercontent.com/agency-wo/mina.github.io/main/watches.json?v=3')
    .then(function(r){ return r.json(); })
    .then(function(WATCHES){
      initBrandChips(WATCHES);
      renderWatches(WATCHES);
      injectItemListSchema(WATCHES, 'en');

      document.querySelectorAll('.filter-chip:not([data-brand])').forEach(function(chip){
        chip.addEventListener('click', function(){
          document.querySelectorAll('.filter-chip:not([data-brand])').forEach(function(c){ c.classList.remove('active'); c.removeAttribute('aria-pressed'); });
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
      if(g) g.innerHTML = '<p class="no-watches">Could not load watches. Please refresh.</p>';
    });

  function initBrandChips(WATCHES){
    var wrap = document.getElementById('brandChips');
    if(!wrap) return;
    var counts = {};
    WATCHES.forEach(function(w){ if(w.brand) counts[w.brand] = (counts[w.brand]||0) + 1; });
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

  function renderWatches(watches){
    var filtered = currentFilter === 'all' ? watches.slice() : watches.filter(function(w){ return w.condition === currentFilter; });

    if(currentBrand !== 'all'){
      filtered = filtered.filter(function(w){ return w.brand === currentBrand; });
    }

    if(currentSearch){
      var s = currentSearch;
      filtered = filtered.filter(function(w){
        return (w.model+' '+w.brand+' '+(w.reference||'')+' '+(w.description_en||'')).toLowerCase().includes(s);
      });
    }

    filtered = filtered.filter(function(w){
      return (w.price||0) >= currentMinPrice && (w.price||0) <= currentMaxPrice;
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

    var count = document.getElementById('shopCount');
    var grid  = document.getElementById('shopGrid');
    count.textContent = filtered.length + ' watch' + (filtered.length !== 1 ? 'es' : '') + ' available';
    if(!filtered.length){
      grid.innerHTML = '<p class="no-watches">No watches match this filter right now. Check back soon!</p>';
      return;
    }
    grid.innerHTML = filtered.map(function(w){ return watchCard(w); }).join('');
  }

  function injectItemListSchema(watches, lang) {
    var base = 'https://watch.al/' + lang + '/shop/';
    var items = watches.filter(function(w){ return !w.sold; }).map(function(w, i){
      return {
        '@type': 'ListItem',
        'position': i + 1,
        'url': base + w.id + '.html',
        'item': {
          '@type': 'Product',
          'name': w.brand + ' ' + w.model + (w.brand === 'Hislon' ? ' Swiss Watch' : ''),
          'image': w.image ? 'https://watch.al' + w.image : 'https://watch.al/og-image.png',
          'brand': {'@type': 'Brand', 'name': w.brand},
          'sku': w.reference || '',
          'offers': {
            '@type': 'Offer',
            'priceCurrency': w.currency || 'EUR',
            'price': String(w.price || ''),
            'availability': 'https://schema.org/InStock',
        'priceValidUntil': '2026-12-31',
            'itemCondition': 'https://schema.org/NewCondition',
            'seller': {'@type': 'Organization', 'name': 'Iglisi Watch'},
            'url': base + w.id + '.html'
          }
        }
      };
    });
    var schema = {
      '@context': 'https://schema.org',
      '@type': 'ItemList',
      'name': 'Watches for Sale at Iglisi Watch',
      'url': 'https://watch.al/' + lang + '/shop/',
      'numberOfItems': items.length,
      'itemListElement': items
    };
    var el = document.getElementById('shop-ld-list');
    if (el) el.textContent = JSON.stringify(schema);
  }

  var EUR_TO_LEK = 97;
  function fmt(price, currency){
    if(!price) return 'Price on request';
    return (currency === 'EUR' ? '\u20ac' : currency) + Number(price).toLocaleString('en-EU');
  }
  function fmtLek(price, currency){
    if(!price || currency !== 'EUR') return '';
    return '<span style="font-size:.78rem;color:#888;font-weight:400"> \u00b7 ' + (Math.round(price * EUR_TO_LEK / 100) * 100).toLocaleString() + '\u00a0L</span>';
  }

  function waMsg(w){
    var msg = "Hi, I\u2019m interested in the " + w.brand + ' ' + w.model + ' (Ref. ' + (w.reference||'N/A') + ') listed on your website.';
    return 'https://api.whatsapp.com/send?phone=355676360510&text=' + encodeURIComponent(msg);
  }

  function watchCard(w){
    var imgHtml = w.image
      ? '<a href="/en/shop/' + w.id + '.html" aria-label="' + w.brand + ' ' + w.model + (w.brand === 'Hislon' ? ' Swiss Watch' : '') + '"><picture><source srcset="' + w.image.replace(/\.jpe?g$/i, '.webp') + '" type="image/webp"><img src="' + w.image + '" alt="' + w.brand + ' ' + w.model + (w.brand === 'Hislon' ? ' Swiss Watch' : '') + '" loading="lazy"></picture></a>'
      : '<div class="watch-img-placeholder"><i class="fas fa-clock" aria-hidden="true"></i></div>';
    var soldOverlay = w.sold ? '<div class="sold-overlay">Sold</div>' : '';
    var ctaHtml = w.sold
      ? '<span style="font-size:.82rem;color:#888">Sold</span>'
      : '<a href="' + waMsg(w) + '" target="_blank" rel="noopener noreferrer" class="watch-cta" data-fb-contact="1" aria-label="Enquire about ' + w.brand + ' ' + w.model + ' via WhatsApp"><i class="fab fa-whatsapp" aria-hidden="true"></i> Enquire</a>';
    return '<article class="watch-card' + (w.sold?' sold-card':'') + '">'
      + '<div class="watch-card-img">' + imgHtml + soldOverlay
      + '<span class="watch-badge">' + w.condition + '</span>'
      + (w.originalPrice ? '<span class="sale-badge">−10%</span>' : '')
      + '</div>'
      + '<div class="watch-card-body">'
      + '<p class="watch-brand">' + w.brand + (w.brand === 'Hislon' ? '<span style="font-size:.65rem;letter-spacing:.08em;text-transform:uppercase;color:#8a9abf;font-weight:500;margin-left:.4rem;vertical-align:middle">Swiss</span>' : '') + '</p>'
      + '<h2 class="watch-model">' + w.model + '</h2>'
      + (w.reference ? '<p class="watch-ref">Ref. ' + w.reference + '</p>' : '')
      + '<p class="watch-desc">' + (w.description_en || '') + '</p>'
      + '<div class="watch-card-footer">'
      + '<div>'
      + '<p class="watch-price">' + fmt(w.price, w.currency) + fmtLek(w.price, w.currency) + '</p>'
      + (w.originalPrice ? '<p class="was-price-line">Was ' + (w.currency==='EUR'?'€':w.currency) + w.originalPrice + '</p>' : '')
      + '</div>'
      + '<a href="https://instagram.com/iglisiwatch" target="_blank" rel="noopener noreferrer" class="watch-ig-link" aria-label="See on Instagram"><i class="fab fa-instagram" aria-hidden="true"></i></a>'
      + ctaHtml
      + '</div></div></article>';
  }
})();
