(function () {
  'use strict';

  const KEY = 'wowReviewReadingStatsV1';

  function emptyStats() {
    return { reviews: {}, totalSeconds: 0, daily: {} };
  }

  function load() {
    try {
      const raw = localStorage.getItem(KEY);
      const data = raw ? JSON.parse(raw) : emptyStats();
      if (!data || typeof data !== 'object') return emptyStats();

      // Migrate the earlier internal "books" name to "reviews".
      if (!data.reviews && data.books && typeof data.books === 'object') {
        data.reviews = data.books;
        delete data.books;
      }

      if (!data.reviews || typeof data.reviews !== 'object') data.reviews = {};
      if (!data.daily || typeof data.daily !== 'object') data.daily = {};
      if (!Number.isFinite(data.totalSeconds)) data.totalSeconds = 0;
      return data;
    } catch (_) {
      return emptyStats();
    }
  }

  function save(data) {
    try {
      localStorage.setItem(KEY, JSON.stringify(data));
    } catch (_) {}
  }

  function localDateKey(date) {
    const d = date || new Date();
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return y + '-' + m + '-' + day;
  }

  function isReviewPage() {
    return /^\/Review\/\d+\/(?:index\.html)?$/.test(location.pathname);
  }

  function getReviewId() {
    const match = location.pathname.match(/^\/Review\/(\d+)\/(?:index\.html)?$/);
    return match ? match[1] : null;
  }

  window.WOWReadingStats = {
    get: load,
    formatMinutes: function (seconds) {
      return Math.floor((seconds || 0) / 60);
    }
  };

  if (!isReviewPage()) return;

  const id = getReviewId();
  if (!id) return;

  const data = load();

  // A Review is counted once per device/browser, no matter how many times it is opened.
  if (!data.reviews[id]) {
    data.reviews[id] = {
      firstOpened: Date.now(),
      lastOpened: Date.now(),
      seconds: 0
    };
  } else {
    data.reviews[id].lastOpened = Date.now();
  }
  save(data);

  let lastActive = Date.now();

  function flush() {
    const now = Date.now();
    const seconds = Math.floor((now - lastActive) / 1000);
    lastActive = now;

    if (seconds <= 0 || seconds > 120) return;

    const d = load();
    if (!d.reviews[id]) {
      d.reviews[id] = {
        firstOpened: now,
        lastOpened: now,
        seconds: 0
      };
    }

    d.reviews[id].seconds = (d.reviews[id].seconds || 0) + seconds;
    d.reviews[id].lastOpened = now;
    d.totalSeconds = (d.totalSeconds || 0) + seconds;

    const key = localDateKey();
    d.daily[key] = (d.daily[key] || 0) + seconds;

    save(d);
  }

  const timer = setInterval(flush, 15000);

  document.addEventListener('visibilitychange', function () {
    if (document.hidden) {
      flush();
    } else {
      lastActive = Date.now();
    }
  });

  window.addEventListener('pagehide', function () {
    clearInterval(timer);
    flush();
  });

  window.addEventListener('beforeunload', function () {
    clearInterval(timer);
    flush();
  });
})();
