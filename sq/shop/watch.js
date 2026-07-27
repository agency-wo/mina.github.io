(function(){
  var btt = document.getElementById('backToTop');
  if(btt){
    window.addEventListener('scroll', function(){ btt.classList.toggle('show', window.scrollY > 400); }, {passive:true});
    btt.addEventListener('click', function(){ window.scrollTo({top:0,behavior:'smooth'}); });
  }
  var fy = document.getElementById('footerYear');
  if(fy) fy.textContent = new Date().getFullYear();

  var params = new URLSearchParams(window.location.search);
  var watchId = params.get('id');
  if(!watchId){var _m=window.location.pathname.match(/\/([^\/]+)\.html$/);if(_m&&_m[1]!=='index'&&_m[1]!=='watch')watchId=_m[1];}

  if(!watchId){
    window.location.replace('/sq/shop/');
    return;
  }

  var _pre = document.getElementById('watch-content');
  var _hasPre = _pre && _pre.className.indexOf('pre-rendered') !== -1;
  if(!window.WATCHES_DATA){ if(_hasPre) return; showError('Nuk mund t\u00eb ngarkohet e dhena e or\u00ebs.', 'Ju lutem rifreskoni ose kthehuni n\u00eb dyqan.'); return; }
  var w = window.WATCHES_DATA.find(function(x){ return x.id === watchId; });
  if(!w){ if(_hasPre) return; showError('Ora nuk u gjet.', 'Kjo or\u00eb mund t\u00eb jet\u00eb shitur ose hequr. Shfletoni dyqanin p\u00ebr ato t\u00eb disponueshme.'); return; }
  render(w);

  var EUR_TO_LEK = 97;
  function fmt(price, currency){
    if(!price) return '\u00c7mimi me k\u00ebrkese';
    return (currency === 'EUR' ? '\u20ac' : currency) + Number(price).toLocaleString('sq-AL');
  }
  function lekPrice(price, currency){
    if(!price || currency !== 'EUR') return 0;
    return Math.round(price * EUR_TO_LEK / 100) * 100;
  }

  function waMsg(w){
    var msg = 'Pershendetje, jam i interesuar per oren ' + w.brand + ' ' + w.model + ' (Ref. ' + (w.reference||'N/A') + ') - a mund te konfirmoni nese \u00ebsht\u00eb ende e disponueshme?';
    return 'https://api.whatsapp.com/send?phone=355676360510&text=' + encodeURIComponent(msg);
  }

  function render(w){
    // title must stay identical to gen_product_pages.py title_for(); the reference is
    // appended only for brand+model collisions (Hislon Classic / Classic Queen).
    var _DUP_NAMES = ['Hislon Classic','Hislon Classic Queen'];
    var _nm = w.brand + ' ' + w.model;
    if (w.reference && _DUP_NAMES.indexOf(_nm) !== -1) { _nm += ' ' + w.reference; }
    var title = _nm + (w.price ? ' - €' + w.price : '') + ' | Blej Orë në Durrës';
    var desc = (w.brand === 'Hislon' ? 'Or\u00eb zvicerane Hislon. ' : '') + (w.description_sq || w.description_en || '') + ' E disponueshme tek Iglisi Watch, Durr\u00ebs, Shqip\u00ebri.';
    var imgUrl = w.image ? 'https://watch.al' + w.image : 'https://watch.al/og-image.png';
    var pageUrl = 'https://watch.al/sq/shop/' + w.id + '.html';
    var enUrl = 'https://watch.al/en/shop/' + w.id + '.html';

    document.getElementById('page-title').textContent = title;
    document.getElementById('page-desc').setAttribute('content', desc);
    document.getElementById('og-title').setAttribute('content', title);
    document.getElementById('og-desc').setAttribute('content', desc);
    document.getElementById('og-image').setAttribute('content', imgUrl);
    document.getElementById('og-url').setAttribute('content', pageUrl);
    ['twitter:title','twitter:description','twitter:image'].forEach(function(name,i){var val=[title,desc,imgUrl][i];var m=document.querySelector('meta[name="'+name+'"]');if(!m){m=document.createElement('meta');m.setAttribute('name',name);document.head.appendChild(m);}m.setAttribute('content',val);});
    document.getElementById('canonical').setAttribute('href', pageUrl);
    var itUrl = 'https://watch.al/it/shop/' + w.id + '.html';
    document.getElementById('hreflang-sq').setAttribute('href', pageUrl);
    document.getElementById('hreflang-en').setAttribute('href', enUrl);
    document.getElementById('hreflang-it').setAttribute('href', itUrl);
    document.getElementById('hreflang-xd').setAttribute('href', enUrl);

    var lt = document.querySelector('.lang-toggle');
    if(lt) lt.href = '/it/shop/' + w.id + '.html';

    var ld = {
      '@context': 'https://schema.org',
      '@type': 'Product',
      'name': w.brand + ' ' + w.model + (w.brand === 'Hislon' ? ' Swiss Watch' : ''),
      'sku': w.reference || '',
      'brand': {'@type': 'Brand', 'name': w.brand},
      'countryOfOrigin': w.brand === 'Hislon' ? {'@type': 'Country', 'name': 'Switzerland'} : w.brand === 'Casio' ? {'@type': 'Country', 'name': 'Japan'} : w.brand === 'Citizen' ? {'@type': 'Country', 'name': 'Japan'} : undefined,
      'description': w.description_sq || w.description_en || '',
      'image': imgUrl,
      'hasMerchantReturnPolicy': {
        '@type': 'MerchantReturnPolicy',
        'applicableCountry': 'AL',
        'returnPolicyCategory': 'https://schema.org/MerchantReturnFiniteReturnWindow',
        'merchantReturnDays': 30,
        'returnMethod': 'https://schema.org/ReturnInStore',
        'returnFees': 'https://schema.org/FreeReturn'
      },
      'offers': {
        '@type': 'Offer',
        'priceCurrency': w.currency,
        'price': String(w.price),
        'priceSpecification': [
          {'@type': 'PriceSpecification', 'price': String(w.price), 'priceCurrency': w.currency},
          {'@type': 'PriceSpecification', 'price': String(lekPrice(w.price, w.currency)), 'priceCurrency': 'ALL'}
        ],
        'availability': w.sold ? 'https://schema.org/SoldOut' : 'https://schema.org/InStock',
        'priceValidUntil': '2026-12-31',
        'itemCondition': w.condition === 'Pre-owned' ? 'https://schema.org/UsedCondition' : 'https://schema.org/NewCondition',
        'seller': {'@type': 'Organization', 'name': 'Iglisi Watch'},
        'url': pageUrl,
        'shippingDetails': {
          '@type': 'OfferShippingDetails',
          'shippingRate': {'@type': 'MonetaryAmount', 'value': '0', 'currency': 'EUR'},
          'shippingDestination': {'@type': 'DefinedRegion', 'addressCountry': 'AL'},
          'deliveryTime': {
            '@type': 'ShippingDeliveryTime',
            'handlingTime': {'@type': 'QuantitativeValue', 'minValue': 0, 'maxValue': 1, 'unitCode': 'DAY'},
            'transitTime': {'@type': 'QuantitativeValue', 'minValue': 3, 'maxValue': 7, 'unitCode': 'DAY'}
          }
        }
      }
    };
    document.getElementById('ld-json').textContent = JSON.stringify(ld);
    var bc = {
      '@context': 'https://schema.org',
      '@type': 'BreadcrumbList',
      'itemListElement': (function(){
        // must match shop_bits.crumb_jsonld() in the static generator
        var _BRAND_SLUGS = 'Daniel Klein:daniel-klein|Navimarine:navimarine|Hislon:hislon|Philippe Lauren:philippe-lauren';
        var _s = null, _parts = _BRAND_SLUGS.split('|');
        for (var _i = 0; _i < _parts.length; _i++) {
          var _kv = _parts[_i].split(':');
          if (_kv[0] === w.brand) { _s = _kv[1]; break; }
        }
        var _out = [
          {'@type': 'ListItem', 'position': 1, 'name': 'Kryefaqja', 'item': 'https://watch.al/sq/'},
          {'@type': 'ListItem', 'position': 2, 'name': 'Dyqani', 'item': 'https://watch.al/sq/shop/'}
        ];
        if (_s) { _out.push({'@type': 'ListItem', 'position': 3, 'name': w.brand,
          'item': 'https://watch.al/sq/shop/brand/' + _s + '.html'}); }
        _out.push({'@type': 'ListItem', 'position': _out.length + 1,
          'name': w.brand + ' ' + w.model, 'item': pageUrl});
        return _out;
      })()
    };
    document.getElementById('ld-breadcrumb').textContent = JSON.stringify(bc);

    var imgHtml = w.image ? '<picture><source srcset="' + w.image.replace(/\.jpe?g$/i, '.webp') + '" type="image/webp"><img src="' + w.image + '" alt="' + w.brand + ' ' + w.model + (w.brand === 'Hislon' ? ' Swiss Watch' : '') + (w.reference ? ' ' + w.reference : '') + '" fetchpriority="high"></picture>' : '';
    var ctaBlock = w.sold
      ? '<p style="font-size:1rem;color:#888;font-weight:600">Kjo or\u00eb \u00ebsht\u00eb shitur.</p>'
      : '<div class="watch-cta-wrap">'
        + '<a href="' + waMsg(w) + '" target="_blank" rel="noopener noreferrer" class="watch-cta-main" data-fb-contact="1" aria-label="Pyesni via WhatsApp"><i class="fab fa-whatsapp" aria-hidden="true"></i> Pyesni n\u00eb WhatsApp</a>'
        + '<a href="https://instagram.com/iglisiwatch" target="_blank" rel="noopener noreferrer" class="watch-ig" aria-label="Shiko Instagram-in ton\u00eb"><i class="fab fa-instagram" aria-hidden="true"></i> Instagram</a>'
        + '</div>';

    if (w.originalPrice && !document.getElementById('pg-sale-style')) {
      var s = document.createElement('style');
      s.id = 'pg-sale-style';
      s.textContent = '.sale-badge{position:absolute;top:1.15rem;left:-2.1rem;width:7.5rem;text-align:center;background:var(--btn-start);color:var(--accent-gold);font-size:.62rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;padding:.32rem 0;transform:rotate(-45deg);z-index:3;box-shadow:0 2px 8px rgba(0,0,0,.28)}.was-price-pg{font-size:.9rem;color:#aaa;text-decoration:line-through;margin:.1rem 0 .25rem}';
      document.head.appendChild(s);
    }
    document.getElementById('watch-content').className = 'watch-page';
    document.getElementById('watch-content').innerHTML =
      '<div class="watch-img-wrap">'
        + imgHtml
        + '<span class="watch-badge-pg">' + (w.sold ? 'Shitur' : (w.condition === 'New' ? 'I ri' : 'I p\u00ebrdorur')) + '</span>'
      + '</div>'
      + '<div class="watch-info">'
        + '<a href="/sq/shop/" class="back-link"><i class="fas fa-arrow-left" aria-hidden="true"></i> Kthehu n\u00eb dyqan</a>'
        + '<div>'
          + '<p class="watch-brand-pg">' + w.brand + '</p>'
          + (w.brand === 'Hislon' ? '<p style="font-size:.72rem;letter-spacing:.1em;text-transform:uppercase;color:#8a9abf;font-weight:600;margin:.0rem 0 .3rem">Markë Zvicerane</p>' : '')
          + '<h1 class="watch-title-pg">' + w.brand + ' ' + w.model + '</h1>'
          + '<p class="watch-ref-pg">Ref. ' + (w.reference||'\u2014') + '</p>'
        + '</div>'
        + '<p class="watch-price-pg">' + (lekPrice(w.price,w.currency) ? lekPrice(w.price,w.currency).toLocaleString() + ' L<span style="font-size:1.1rem;color:#888;font-weight:500;margin-left:.5rem">· ' + fmt(w.price, w.currency) + '</span>' : fmt(w.price, w.currency)) + '</p>'
        + '<p class="watch-desc-pg">' + (w.description_sq || w.description_en || '') + '</p>'
        + ctaBlock
        + '<div class="trust-row">'
          + '<span class="trust-item" style="color:#1a7a3f;font-weight:600"><i class="fas fa-money-bill" aria-hidden="true" style="color:#1a7a3f"></i> Para n\u00eb dor\u00ebzim</span>'
          + '<span class="trust-item"><i class="fas fa-shield-alt" aria-hidden="true"></i> Garanci 1 vit</span>'
          + '<span class="trust-item"><i class="fas fa-star" aria-hidden="true"></i> E re &amp; origjinale</span>'
          + '<span class="trust-item"><i class="fas fa-clock" aria-hidden="true"></i> H\u00ebn\u2013Sht 8:30\u201320:30</span>'
        + '</div>'
      + '</div>';
  }

  function showError(heading, body){
    document.getElementById('watch-content').className = 'error-state';
    document.getElementById('watch-content').innerHTML =
      '<h2>' + heading + '</h2>'
      + '<p>' + body + '</p>'
      + '<a href="/sq/shop/" style="display:inline-block;margin-top:1.5rem;background:#06153b;color:#fff;padding:.7rem 1.8rem;border-radius:9999px;font-weight:700;text-decoration:none">Shfletoni Dyqanin</a>';
  }
})();
