// [CFG-009] sw.js — a KILL-SWITCH service worker, deliberately NOT a cache.
// DOES:   skipWaiting on install, then on activate deletes EVERY Cache Storage
//         entry, claims the open clients and unregisters itself. There is no
//         fetch handler at all: this worker never serves a byte.
// OUT:    an empty Cache Storage, no registration left, and clients back on the
//         network from their next navigation on.
// NOTES:  It exists ONLY to undo the caching service worker that shipped before
//         it and went on pinning stale HTML for returning visitors. A browser
//         learns the worker changed only by fetching THIS url, so the file has
//         to stay deployed: delete it and every client still holding the old
//         worker keeps serving stale pages with nothing left to replace it.
//         Do NOT turn this back into a caching worker without a plan for the
//         clients already holding the old one, because this file IS that plan.
'use strict';
/* KILL-SWITCH: wipe all caches and unregister this SW so pages always load fresh */
self.addEventListener('install', function() { self.skipWaiting(); });
self.addEventListener('activate', function(e) {
  e.waitUntil(
    caches.keys().then(function(keys) {
      return Promise.all(keys.map(function(k) { return caches.delete(k); }));
    }).then(function() {
      return self.clients.claim();
    }).then(function() {
      return self.registration.unregister();
    })
  );
});
