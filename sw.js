const CACHE_NAME = 'wow-books-v3';

self.addEventListener('install', e => {
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;

  const url = new URL(e.request.url);
  const isNavigation = e.request.mode === 'navigate';
  const isHtml = url.pathname.endsWith('.html') || /\/Review\/\d+\/?$/.test(url.pathname);
  const isPostsJson = url.pathname.includes('posts.json');

  // Always prefer the latest HTML/data so Telegram and other in-app browsers
  // do not keep showing an old page after site updates.
  if (isNavigation || isHtml || isPostsJson) {
    e.respondWith(
      fetch(e.request, { cache: 'no-store' })
        .then(resp => {
          if (resp && resp.ok) {
            const clone = resp.clone();
            caches.open(CACHE_NAME).then(c => c.put(e.request, clone));
          }
          return resp;
        })
        .catch(() =>
          caches.match(e.request).then(r => r || caches.match('/Review/'))
        )
    );
    return;
  }

  // Static assets can stay cache-first for speed and offline use.
  e.respondWith(
    caches.match(e.request).then(r =>
      r || fetch(e.request).then(resp => {
        if (resp && resp.ok) {
          const clone = resp.clone();
          caches.open(CACHE_NAME).then(c => c.put(e.request, clone));
        }
        return resp;
      })
    ).catch(() => caches.match('/Review/'))
  );
});
