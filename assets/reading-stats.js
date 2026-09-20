(function () {
  'use strict';
  const KEY = 'wowReviewReadingStatsV1';
  const isPostPage = /\/Review\/\d+\/(?:index\.html)?$/.test(location.pathname);

  function load() {
    try { return JSON.parse(localStorage.getItem(KEY)) || {books:{},totalSeconds:0,daily:{}}; }
    catch (_) { return {books:{},totalSeconds:0,daily:{}}; }
  }
  function save(data) { try { localStorage.setItem(KEY, JSON.stringify(data)); } catch (_) {} }
  function today() { return new Date().toISOString().slice(0,10); }

  window.WOWReadingStats = {
    get: load,
    formatMinutes: function (seconds) { return Math.floor((seconds || 0) / 60); }
  };

  if (!isPostPage) return;

  const match = location.pathname.match(/\/Review\/(\d+)\/(?:index\.html)?$/);\n  if (!match) return;\n  const id = match[1];
  const data = load();
  if (!data.books[id]) data.books[id] = {firstOpened:Date.now(), lastOpened:Date.now(), seconds:0};
  else data.books[id].lastOpened = Date.now();
  save(data);

  let last = Date.now();
  function flush() {
    const seconds = Math.floor((Date.now() - last) / 1000);
    last = Date.now();
    if (seconds <= 0 || seconds > 120) return;
    const d = load();
    if (!d.books[id]) d.books[id] = {firstOpened:Date.now(),lastOpened:Date.now(),seconds:0};
    d.books[id].seconds = (d.books[id].seconds || 0) + seconds;
    d.totalSeconds = (d.totalSeconds || 0) + seconds;
    const key = today();
    d.daily[key] = (d.daily[key] || 0) + seconds;
    save(d);
  }

  const timer = setInterval(flush, 15000);
  document.addEventListener('visibilitychange', function () {
    if (document.hidden) flush();
    else last = Date.now();
  });
  window.addEventListener('pagehide', function () {
    clearInterval(timer);
    flush();
  });
})();