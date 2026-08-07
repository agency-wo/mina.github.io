(function(){
  var condMap = {'New':'I ri','Pre-owned':'I p\u00ebrdorur'};
  var currentFilter = 'all';
  var currentBrand  = 'all';
  var currentSearch = '';
  var BRAND_ALL_LABEL = 'Të gjitha markat';
  var currentSort   = 'default';

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

  fetch('https://raw.githubusercontent.com/agency-wo/mina.github.io/main/watches.json?v=3')
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
      initBrandChips(WATCHES);
      renderWatches(WATCHES);

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
    })
    .catch(function(){
      // keep the pre-rendered grid if the live fetch fails (stale cache / offline)
      var g = document.getElementById('shopGrid');
      var _shopHasPre = g && g.querySelector('.watch-card');
      if(_shopHasPre) return;
      if(g) g.innerHTML = '<p class="no-watches">Nuk mund të ngarkohen orët. Rifresko faqen.</p>';
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
        return (w.model+' '+w.brand+' '+(w.reference||'')+' '+(w.description_sq||'')).toLowerCase().includes(s);
      });
    }

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
    count.textContent = filtered.length + ' or\u00eb e disponueshme';
    if(!filtered.length){
      grid.innerHTML = '<p class="no-watches">Asnj\u00eb or\u00eb nuk p\u00ebrputhet me k\u00ebt\u00eb filtro tani. Kthehuni s\u00eb shpejti!</p>';
      return;
    }
    grid.innerHTML = filtered.map(function(w){ return watchCard(w); }).join('');
  }



  var EUR_TO_LEK = 97;
  var SEP = '.';
  /* Comma in EN, dot in IT and SQ. Mirrors catalog_stats.SEP byte for byte.
     Never toLocaleString(): it asks the browser for the separator, so an
     Italian phone reflowed the grid from 18,300 L to 18.300 L after hydration
     and the rendered page disagreed with the HTML the server sent. */
  function group(n){ return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, SEP); }
  function fmt(price, currency){
    if(!price) return '\u00c7mimi me k\u00ebrkese';
    return (currency === 'EUR' ? '\u20ac' : currency) + group(price);
  }
  function lekVal(price, currency){
    if(!price || currency !== 'EUR') return 0;
    return Math.round(price * EUR_TO_LEK / 100) * 100;
  }
  function fmtLek(price, currency){
    if(!price || currency !== 'EUR') return '';
    return '<span style="font-size:.78rem;color:#888;font-weight:400"> \u00b7 ' + group(Math.round(price * EUR_TO_LEK / 100) * 100) + '\u00a0L</span>';
  }

  function waMsg(w){
    var msg = 'Pershendetje, jam i interesuar per oren ' + w.brand + ' ' + w.model + ' (Ref. ' + (w.reference||'N/A') + ') ne faqen tuaj.';
    return 'https://api.whatsapp.com/send?phone=355676360510&text=' + encodeURIComponent(msg);
  }

  function watchCard(w){
    var cond = condMap[w.condition] || w.condition;
    var imgHtml = w.image
      ? '<a href="/sq/shop/' + w.id + '.html" aria-label="' + w.brand + ' ' + w.model + (w.brand === 'Hislon' ? ' Swiss Watch' : '') + '"><picture><source srcset="' + w.image.replace(/\.jpe?g$/i, '.webp') + '" type="image/webp"><img src="' + w.image + '" alt="' + w.brand + ' ' + w.model + (w.brand === 'Hislon' ? ' Swiss Watch' : '') + '" loading="lazy"></picture></a>'
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
      + '<p class="watch-brand">' + w.brand + (w.brand === 'Hislon' ? '<span style="font-size:.65rem;letter-spacing:.08em;text-transform:uppercase;color:#8a9abf;font-weight:500;margin-left:.4rem;vertical-align:middle">Swiss</span>' : '') + '</p>'
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
