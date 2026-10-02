(function () {
  'use strict';

  var KEY = 'wowReviewReadingStatsV1';
  var config = {
    apiKey: 'AIzaSyBX28BIHkrQzF7QmAEsoh8OPdEIaFILYRA',
    authDomain: 'github-comment-9f76d.firebaseapp.com',
    projectId: 'github-comment-9f76d',
    storageBucket: 'github-comment-9f76d.firebasestorage.app',
    messagingSenderId: '423917068098',
    appId: '1:423917068098:web:bfb899f06ae1375741b2db'
  };

  function emptyStats() { return { reviews: {}, totalSeconds: 0, daily: {} }; }
  function load() {
    try {
      var raw = localStorage.getItem(KEY), data = raw ? JSON.parse(raw) : emptyStats();
      if (!data || typeof data !== 'object') return emptyStats();
      if (!data.reviews && data.books && typeof data.books === 'object') { data.reviews = data.books; delete data.books; }
      if (!data.reviews || typeof data.reviews !== 'object') data.reviews = {};
      if (!data.daily || typeof data.daily !== 'object') data.daily = {};
      if (!Number.isFinite(data.totalSeconds)) data.totalSeconds = 0;
      return data;
    } catch (_) { return emptyStats(); }
  }
  function save(data) { try { localStorage.setItem(KEY, JSON.stringify(data)); return true; } catch (_) { return false; } }
  function dateKey(date) { var d = date || new Date(); return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0'); }
  function getId() { var m = location.pathname.match(/^\/Review\/(\d+)\/?(?:index\.html)?$/); return m ? m[1] : null; }
  var id = getId();
  var flushReadingTime = function () {};

  window.WOWReadingStats = {
    get: load,
    flush: function () { flushReadingTime(); },
    formatMinutes: function (seconds) { return Math.floor((seconds || 0) / 60); }
  };
  if (!id) return;

  var data = load(), now = Date.now();
  if (!data.reviews[id]) data.reviews[id] = { firstOpened: now, lastOpened: now, seconds: 0 };
  else data.reviews[id].lastOpened = now;
  save(data);

  var db = null, serverReady = false, lastActive = Date.now();
  try {
    if (window.firebase) {
      if (!firebase.apps.length) firebase.initializeApp(config);
      db = firebase.firestore();
      firebase.auth().onAuthStateChanged(function (user) {
        if (!user || serverReady) return;
        serverReady = true;
        db.collection('reviewStats').doc(id).set({ views: firebase.firestore.FieldValue.increment(1), updatedAt: firebase.firestore.FieldValue.serverTimestamp() }, { merge: true });
      });
    }
  } catch (_) {}

  flushReadingTime = function () {
    var current = Date.now(), elapsed = Math.floor((current - lastActive) / 1000);
    if (elapsed <= 0) { lastActive = current; return; }
    var seconds = Math.min(elapsed, 300); lastActive = current;
    var local = load();
    if (!local.reviews[id]) local.reviews[id] = { firstOpened: current, lastOpened: current, seconds: 0 };
    local.reviews[id].seconds = (local.reviews[id].seconds || 0) + seconds;
    local.reviews[id].lastOpened = current; local.totalSeconds = (local.totalSeconds || 0) + seconds;
    var key = dateKey(); local.daily[key] = (local.daily[key] || 0) + seconds; save(local);
    if (serverReady && db) db.collection('reviewStats').doc(id).set({ seconds: firebase.firestore.FieldValue.increment(seconds), updatedAt: firebase.firestore.FieldValue.serverTimestamp() }, { merge: true });
  };

  var timer = setInterval(flushReadingTime, 5000);
  document.addEventListener('visibilitychange', function () { if (document.hidden) flushReadingTime(); else lastActive = Date.now(); });
  window.addEventListener('pagehide', function () { flushReadingTime(); clearInterval(timer); });
  window.addEventListener('beforeunload', function () { flushReadingTime(); clearInterval(timer); });
}());
