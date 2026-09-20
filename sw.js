const CACHE_NAME = 'wow-books-v8-stats-fix';

self.addEventListener('install', event => {
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys
          .filter(key => key !== CACHE_NAME)
          .map(key => caches.delete(key))
      )
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;

  const url = new URL(event.request.url);
  const isNavigation = event.request.mode === 'navigate';
  const isHtml =
    url.pathname.endsWith('.html') ||
    /\/Review\/\d+\/?$/.test(url.pathname);
  const isPostsJson = url.pathname.endsWith('/assets/posts.json');

  // JSON must pass through unchanged. Never transform/cache it as HTML.
  if (isPostsJson) {
    event.respondWith(
      fetch(event.request, { cache: 'no-store' })
        .catch(() => caches.match(event.request))
    );
    return;
  }

  // HTML pages are always fetched fresh. The only transformation here is
  // hiding the post controls requested by the site owner and replacing the
  // old Burma001 font reference when an old cached post still contains it.
  if (isNavigation || isHtml) {
    event.respondWith(
      fetch(event.request, { cache: 'no-store' })
        .then(response => {
          const contentType = response.headers.get('content-type') || '';
          if (!response.ok || !contentType.includes('text/html')) {
            return response;
          }

          return response.text().then(html => {
            const waloneUrl =
              'https://raw.githubusercontent.com/whispermmepub/myanmar-yoe-shin-fonts/main/fonts/Walone-Regular.ttf';

            const transformed = html
              .replace(/Burma001/g, 'Walone')
              .replace(
                /\/Review\/assets\/Burma001-Regular\.ttf/g,
                waloneUrl
              );

            const statsScript = '<script src="/Review/assets/reading-stats.js"></script>';
            const hasStatsScript = transformed.includes('/Review/assets/reading-stats.js');
            const finalWithStats = hasStatsScript
              ? transformed
              : (transformed.includes('</body>')
                  ? transformed.replace('</body>', statsScript + '</body>')
                  : transformed + statsScript);

            const hidePostControls =
              '<style id="wow-hide-post-controls">' +
              '.share-section,.share-btn{display:none!important}' +
              '.reviewer-credit p a[href]{display:none!important}' +
              '</style>';

            const finalHtml = finalWithStats.includes('</head>')
              ? finalWithStats.replace('</head>', hidePostControls + '</head>')
              : finalWithStats + hidePostControls;

            const headers = new Headers(response.headers);
            headers.set('Content-Type', 'text/html; charset=utf-8');

            return new Response(finalHtml, {
              status: response.status,
              statusText: response.statusText,
              headers
            });
          });
        })
        .catch(() => caches.match(event.request))
    );
    return;
  }

  // Static assets only: cache-first for speed.
  event.respondWith(
    caches.match(event.request)
      .then(cached => cached || fetch(event.request).then(response => {
        if (response.ok) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache =>
            cache.put(event.request, clone)
          );
        }
        return response;
      }))
      .catch(() => caches.match('/Review/'))
  );
});
