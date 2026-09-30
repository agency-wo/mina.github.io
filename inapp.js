// [UI-019] inapp.js — flags embedded in-app browsers on <html> before first paint
// DOES:   reads navigator.userAgent once and adds classes to <html>:
//           in-app          any embedded WebView (Instagram, WhatsApp, Facebook,
//                           Messenger, TikTok, Telegram... on iOS or Android)
//           in-app-overlay  hosts known to float a translucent bar OVER the top
//                           of the page instead of above it: Meta and TikTok
//           in-app-ios / in-app-android
//         shared.css keys on them to push the header clear of the host bar and
//         to unstick it, so the logo, call and WhatsApp buttons stop hiding
//         under the host's chrome. Nothing else reads these classes.
//         Also adds shop-filtered on a {lang}/shop/ page opened with a ?brand= or
//         ?gender= filter, for the same before-first-paint reason; that page's CSS
//         and shop.js own it (the second block below).
// IN:     navigator.userAgent, location. No DOM beyond document.documentElement.
// OUT:    class names on <html>; classify() exported for tools/test_inapp.js.
// NOTES:  Loaded SYNCHRONOUSLY in <head> right after the viewport meta, on
//         purpose: a deferred script would add the class after first paint and
//         the header would visibly jump. Same origin, so the CSP's script-src
//         'self' allows it on every page including the nonced homepages.
//         UA sniffing is the only signal a page gets about its host. The iOS
//         rule is the standard one: a WKWebView UA carries AppleWebKit and
//         Mobile/ but no "Safari/" token, which Safari, Chrome (CriOS),
//         Firefox (FxiOS) and Edge (EdgiOS) all carry. A spoofed UA costs the
//         visitor a slightly taller header, nothing worse.
//         No nudge bar here, ever: the owner declined one (2026-08-20).
(function(){
  function classify(ua){
    ua = ua || '';
    var overlay = /Instagram|FBAN|FBAV|FB_IAB|Messenger|musical_ly|BytedanceWebview|TikTok/i.test(ua);
    var ios = /iPhone|iPad|iPod/i.test(ua);
    var android = /Android/i.test(ua);
    var iosWebView = ios && /AppleWebKit/i.test(ua) && !/Safari\//i.test(ua) && !/CriOS|FxiOS|EdgiOS|OPiOS/i.test(ua);
    var androidWebView = android && (/; wv\)/i.test(ua) || /Version\/\d+\.\d+.*Chrome\//i.test(ua));
    var cls = [];
    if(overlay || iosWebView || androidWebView){
      cls.push('in-app');
      if(overlay) cls.push('in-app-overlay');
      if(ios) cls.push('in-app-ios');
      if(android) cls.push('in-app-android');
    }
    return cls;
  }
  if(typeof document !== 'undefined' && document.documentElement && typeof navigator !== 'undefined'){
    var c = classify(navigator.userAgent);
    for(var i = 0; i < c.length; i++) document.documentElement.classList.add(c[i]);
  }
  // A shop page opened already filtered (a shared ?brand= or ?gender= link, or Back from a
  // watch opened from the results) is marked here, before first paint, so that page's own CSS
  // keeps New Arrivals and the "Browse by brand" links out of the way from the first frame.
  // Decided later, in the deferred shop.js, the page painted New Arrivals at the restored
  // scroll position and then yanked it away: a layout shift of 0.76 on desktop (measured
  // 2026-09-30). shop.js owns the class once the catalogue has loaded (syncArrivals).
  if(typeof location !== 'undefined' && typeof document !== 'undefined' && document.documentElement){
    var path = location.pathname;
    var shop = path === '/en/shop/' || path === '/it/shop/' || path === '/sq/shop/' ||
               path === '/en/shop/index.html' || path === '/it/shop/index.html' || path === '/sq/shop/index.html';
    if(shop && /[?&](brand=[^&]|gender=(men|women)(&|$))/i.test(location.search))
      document.documentElement.classList.add('shop-filtered');
  }
  if(typeof module !== 'undefined' && module.exports) module.exports = classify;
})();
