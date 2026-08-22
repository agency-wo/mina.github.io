// [UI-019] test_inapp.js — smoke test for inapp.js classify(); shares the UI-019
//          tag by design, this file exercises nothing but that one function.
// DOES:   feeds real-world user agents through classify() and asserts the class
//         set each must produce. Run: node tools/test_inapp.js  (from mina.github.io/)
// OUT:    "OK n cases" and exit 0, or the first mismatch and exit 1.
var classify = require('../inapp.js');
var cases = [
  ['Safari iOS',
   'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1',
   []],
  ['Chrome iOS',
   'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/126.0.0.0 Mobile/15E148 Safari/604.1',
   []],
  ['Chrome Android',
   'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36',
   []],
  ['Desktop Chrome',
   'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
   []],
  ['Instagram iOS',
   'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Instagram 330.0.0.0.0 (iPhone15,2; iOS 17_5; en_US; en; scale=3.00; 1179x2556; 600000000)',
   ['in-app', 'in-app-overlay', 'in-app-ios']],
  ['Facebook Android',
   'Mozilla/5.0 (Linux; Android 14; SM-S918B Build/UP1A.231005.007; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/126.0.0.0 Mobile Safari/537.36 [FB_IAB/FB4A;FBAV/470.0.0.0.0;]',
   ['in-app', 'in-app-overlay', 'in-app-android']],
  ['WhatsApp-style iOS WKWebView (no Safari token)',
   'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148',
   ['in-app', 'in-app-ios']],
  ['Android WebView generic',
   'Mozilla/5.0 (Linux; Android 13; Pixel 7; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/125.0.0.0 Mobile Safari/537.36',
   ['in-app', 'in-app-android']],
  ['TikTok iOS',
   'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 musical_ly_34.5.0 JsSdk/2.0 NetType/WIFI Channel/App Store ByteLocale/en Region/US BytedanceWebview/d8a21c6',
   ['in-app', 'in-app-overlay', 'in-app-ios']]
];
var fail = 0;
for(var i = 0; i < cases.length; i++){
  var got = classify(cases[i][1]).join(' '), want = cases[i][2].join(' ');
  if(got !== want){ fail++; console.log('FAIL ' + cases[i][0] + ': got [' + got + '] want [' + want + ']'); }
}
if(fail){ process.exit(1); }
console.log('OK ' + cases.length + ' cases');
