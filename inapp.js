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
// IN:     navigator.userAgent. No DOM beyond document.documentElement.
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
  if(typeof module !== 'undefined' && module.exports) module.exports = classify;
})();
