(function () {
  'use strict';
  var config = {
    apiKey: 'AIzaSyBX28BIHkrQzF7QmAEsoh8OPdEIaFILYRA',
    authDomain: 'github-comment-9f76d.firebaseapp.com',
    projectId: 'github-comment-9f76d',
    storageBucket: 'github-comment-9f76d.firebasestorage.app',
    messagingSenderId: '423917068098',
    appId: '1:423917068098:web:bfb899f06ae1375741b2db'
  };
  var stats = {};
  function esc(value) {
    return String(value || '').replace(/[&<>"']/g, function (c) { return ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' })[c]; });
  }
  function card(post, metric, rank) {
    var value = metric === 'views' ? ((stats[post.id] || {}).views || 0) + ' views' : Math.floor(((stats[post.id] || {}).seconds || 0) / 60) + ' min';
    var image = post.image ? '<img src="' + esc(post.image) + '" alt="' + esc(post.title) + '" loading="lazy">' : '<div class="popular-placeholder">📖</div>';
    return '<a class="popular-card" href="' + esc(post.link) + '"><span class="popular-rank">' + rank + '</span>' + image + '<span class="popular-info"><strong>' + esc(post.title) + '</strong><small>' + esc(post.author) + ' · ' + value + '</small></span></a>';
  }
  function render(id, posts, metric) {
    var el = document.getElementById(id); if (!el) return;
    el.innerHTML = posts.slice(0, 5).map(function (p, i) { return card(p, metric, i + 1); }).join('') || '<p class="popular-empty">မကြာမီ ပြသပါမယ်။</p>';
  }
  function start(posts) {
    var newest = posts.slice().sort(function (a, b) { return String(b.date || '').localeCompare(String(a.date || '')); });
    render('newest-reviews', newest, 'views');
    if (!window.firebase) { render('popular-reviews', posts, 'views'); render('most-read-reviews', posts, 'seconds'); return; }
    try {
      if (!firebase.apps.length) firebase.initializeApp(config);
      firebase.firestore().collection('reviewStats').get().then(function (snap) {
        snap.forEach(function (doc) { stats[doc.id] = doc.data() || {}; });
        render('popular-reviews', posts.slice().sort(function (a, b) { return ((stats[b.id] || {}).views || 0) - ((stats[a.id] || {}).views || 0); }), 'views');
        render('most-read-reviews', posts.slice().sort(function (a, b) { return ((stats[b.id] || {}).seconds || 0) - ((stats[a.id] || {}).seconds || 0); }), 'seconds');
      }).catch(function () { render('popular-reviews', posts, 'views'); render('most-read-reviews', posts, 'seconds'); });
    } catch (_) { render('popular-reviews', posts, 'views'); render('most-read-reviews', posts, 'seconds'); }
  }
  fetch('assets/posts.json').then(function (r) { return r.json(); }).then(start).catch(function () {
    ['popular-reviews', 'most-read-reviews', 'newest-reviews'].forEach(function (id) { var el = document.getElementById(id); if (el) el.innerHTML = '<p class="popular-empty">ဖတ်၍မရပါ။</p>'; });
  });
}());
