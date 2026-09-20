// Service worker cleanup for Review.
// The Review site no longer needs a service worker.
// This file unregisters any existing worker and removes old caches.

self.addEventListener('install', event => {
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.map(key => caches.delete(key)));
    await self.registration.unregister();
  })());
});

// Intentionally no fetch handler.
// Requests go directly to the network.
