// Service worker intentionally disabled for Review pages.
// Keeping this worker inactive prevents stale interception/caching from
// breaking individual Review post pages while the site remains network-first.
self.addEventListener('install', event => {
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.map(key => caches.delete(key)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', event => {
  // Always use the network. No HTML transformation and no cache fallback.
  event.respondWith(fetch(event.request));
});
