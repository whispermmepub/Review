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
  var commentCounts = {};
  function esc(value) {
    return String(value || '').replace(/[&<>"']/g, function (c) { return ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' })[c]; });
  }
  function card(post, metric, rank) {
    var value = metric === 'views' ? ((stats[post.id] || {}).views || 0) + ' views' : metric === 'comments' ? (commentCounts[post.id] || 0) + ' comments' : Math.floor(((stats[post.id] || {}).seconds || 0) / 60) + ' min';
    var image = post.image ? '<img src="' + esc(post.image) + '" alt="' + esc(post.title) + '" loading="lazy" decoding="async">' : '<div class="popular-placeholder">📖</div>';
    var champion = metric === 'seconds' && rank === 1 ? '<span class="popular-champion-badge" aria-label="အများဆုံးဖတ်ထားသော Review နံပါတ် ၁"><span class="champion-trophy" aria-hidden="true">🏆</span><span>#1</span></span>' : metric === 'comments' && rank === 1 ? '<span class="popular-champion-badge comment-champion-badge" aria-label="Comment အများဆုံး Review နံပါတ် ၁"><span class="champion-trophy" aria-hidden="true">🏆</span><span>#1</span></span>' : '';
    var championClass = champion ? ' popular-champion-card' : '';
    return '<a class="popular-card' + championClass + '" href="' + esc(post.link) + '">' + champion + '<span class="popular-rank">' + rank + '</span>' + image + '<span class="popular-info"><strong>' + esc(post.title) + '</strong><small>' + esc(post.author) + ' · ' + value + '</small></span></a>';
  }
  function setupCarousel(el) {
    if (!el || el.dataset.carouselReady === 'true') return;
    el.dataset.carouselReady = 'true';
    el.classList.add('popular-carousel');
    el.setAttribute('role', 'region');
    el.setAttribute('aria-label', 'ဘေးသို့ ဆွဲကြည့်ရန် Reviewများ');
    var timer = null;
    var resumeTimer = null;
    function cards() { return el.querySelectorAll('.popular-card'); }
    function advance() {
      var items = cards(); if (items.length < 2) return;
      var first = items[0];
      var step = first.getBoundingClientRect().width + 10;
      var end = el.scrollLeft + el.clientWidth >= el.scrollWidth - 8;
      el.scrollTo({ left: end ? 0 : el.scrollLeft + step, behavior: 'smooth' });
    }
    function start() { if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return; if (!timer) timer = window.setInterval(advance, 4200); }
    function stop() { if (timer) { window.clearInterval(timer); timer = null; } }
    function pauseThenResume() { stop(); if (resumeTimer) window.clearTimeout(resumeTimer); resumeTimer = window.setTimeout(start, 5200); }
    el.addEventListener('mouseenter', stop); el.addEventListener('mouseleave', start);
    el.addEventListener('focusin', stop); el.addEventListener('focusout', start);
    el.addEventListener('touchstart', pauseThenResume, { passive: true });
    el.addEventListener('pointerdown', pauseThenResume, { passive: true });
    start();
  }
  function render(id, posts, metric) {
    var el = document.getElementById(id); if (!el) return;
    el.innerHTML = posts.slice(0, 5).map(function (p, i) { return card(p, metric, i + 1); }).join('') || '<p class="popular-empty">မကြာမီ ပြသပါမယ်။</p>';
    if (id === 'popular-reviews' || id === 'most-read-reviews') setupCarousel(el);
  }
  function renderFeatured(posts) {
    var el = document.getElementById('featured-review-card');
    if (!el || !posts.length) return;
    var post = posts[0];
    var image = post.image ? '<img src="' + esc(post.image) + '" alt="' + esc(post.title) + '" loading="eager" decoding="async">' : '<div class="featured-cover-placeholder">📖</div>';
    el.innerHTML = image + '<div class="featured-review-copy"><span class="featured-badge">Featured Review</span><h3>' + esc(post.title) + '</h3><p>' + esc(post.excerpt || post.author || '') + '</p><a class="read-featured" href="' + esc(post.link) + '">ဖတ်ရှုရန် →</a></div>';
  }
  function renderMostCommented(posts) {
    render('most-commented-reviews', posts.slice().sort(function (a, b) { return (commentCounts[b.id] || 0) - (commentCounts[a.id] || 0); }), 'comments');
  }
  function loadCommentCounts(posts, done) {
    var jobs = posts.map(function (post) {
      return firebase.firestore().collection('posts').doc(String(post.id)).collection('comments').where('status', '==', 'approved').get().then(function (snap) {
        commentCounts[post.id] = snap.size;
      }).catch(function () { commentCounts[post.id] = 0; });
    });
    Promise.all(jobs).then(done);
  }
  function defer(fn) {
    if (window.requestIdleCallback) window.requestIdleCallback(fn, { timeout: 1800 });
    else window.setTimeout(fn, 250);
  }
  function loadFirebaseStats(posts) {
    if (!window.firebase) return;
    try {
      if (!firebase.apps.length) firebase.initializeApp(config);
      firebase.firestore().collection('reviewStats').get().then(function (snap) {
        snap.forEach(function (doc) { stats[doc.id] = doc.data() || {}; });
        render('popular-reviews', posts.slice().sort(function (a, b) { return ((stats[b.id] || {}).views || 0) - ((stats[a.id] || {}).views || 0); }), 'views');
        render('most-read-reviews', posts.slice().sort(function (a, b) { return ((stats[b.id] || {}).seconds || 0) - ((stats[a.id] || {}).seconds || 0); }), 'seconds');
        // Comment counts are non-critical; fetch them after the first paint.
        defer(function () {
          var auth = firebase.auth();
          var load = function () { loadCommentCounts(posts, function () { renderMostCommented(posts); }); };
          if (auth.currentUser) load(); else auth.signInAnonymously().then(load).catch(load);
        });
      }).catch(function () {});
    } catch (_) {}
  }
  function start(posts) {
    var newest = posts.slice().sort(function (a, b) { return String(b.date || '').localeCompare(String(a.date || '')); });
    // Paint useful content immediately; Firebase will reorder it later.
    renderFeatured(posts);
    render('popular-reviews', posts, 'views');
    render('most-read-reviews', newest, 'seconds');
    render('newest-reviews', newest, 'views');
    defer(function () { loadFirebaseStats(posts); });
  }
  function loadPosts() {
    if (window.WOWPostsData && typeof window.WOWPostsData.load === 'function') return window.WOWPostsData.load();
    if (window.WOWPostsData && window.WOWPostsData.promise) return window.WOWPostsData.promise;
    return fetch('assets/posts.json', { cache: 'force-cache' }).then(function (r) { return r.json(); });
  }
  loadPosts().then(start).catch(function () {
    ['popular-reviews', 'most-read-reviews', 'most-commented-reviews', 'newest-reviews'].forEach(function (id) { var el = document.getElementById(id); if (el) el.innerHTML = '<p class="popular-empty">ဖတ်၍မရပါ။</p>'; });
  });
}());
