(function () {
  'use strict';

  var VIEW_KEY = 'wow-review-catalog-view-v1';
  var VIEWS = ['grid', 'small-list', 'large-list', 'small-grid', 'large-grid'];
  var posts = [];
  var view = 'grid';
  var searchTimer = null;

  function byId(id) { return document.getElementById(id); }
  function make(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = String(text);
    return node;
  }
  function safeWebUrl(value) {
    var raw = String(value || '').trim();
    if (!raw) return '';
    try {
      var url = new URL(raw, window.location.href);
      return url.protocol === 'https:' || url.protocol === 'http:' ? url.href : '';
    } catch (_) { return ''; }
  }
  function getPostId(post) { return String(post.id || '').replace(/[^\w-]/g, ''); }

  function makeCard(post) {
    var title = String(post.title || 'စာအုပ်အညွှန်း');
    var author = String(post.author || 'Whisper Of Words');
    var target = safeWebUrl(post.link) || '#';
    var article = make('article', 'post-card');
    article.dataset.postId = getPostId(post);

    var cover = make('a', 'card-cover');
    cover.href = target;
    cover.setAttribute('aria-label', title + ' — review ဖတ်ရန်');
    var imageUrl = safeWebUrl(post.image);
    if (imageUrl) {
      var image = make('img', 'card-img');
      image.src = imageUrl;
      image.alt = title;
      image.loading = 'lazy';
      image.decoding = 'async';
      image.fetchPriority = 'low';
      cover.appendChild(image);
    } else {
      cover.appendChild(make('span', 'card-img-placeholder', '📖'));
    }
    if (post.category) cover.appendChild(make('span', 'card-category', post.category));

    var content = make('div', 'card-content');
    var meta = make('div', 'card-meta');
    meta.appendChild(make('span', 'card-author', '✍️ ' + author));
    var date = make('time', 'card-date', post.date ? '📅 ' + String(post.date) : '');
    if (/^\d{4}-\d{2}-\d{2}$/.test(String(post.date || ''))) date.dateTime = post.date;
    meta.appendChild(date);
    content.appendChild(meta);

    var heading = make('h3', 'card-title');
    var titleLink = make('a', 'card-title-link', title);
    titleLink.href = target;
    heading.appendChild(titleLink);
    content.appendChild(heading);
    content.appendChild(make('p', 'card-excerpt', post.excerpt || ''));

    var actions = make('div', 'card-actions');
    var readLink = make('a', 'card-read-more', 'ဖတ်ရန် →');
    readLink.href = target;
    actions.appendChild(readLink);
    content.appendChild(actions);

    article.appendChild(cover);
    article.appendChild(content);
    return article;
  }

  function renderCards(items) {
    var container = byId('posts-container');
    container.replaceChildren();
    if (!items.length) {
      container.appendChild(make('div', 'no-results', '🔍 ရှာဖွေချက်နှင့် ကိုက်ညီသည့် Review မတွေ့ပါ။'));
      return;
    }
    var fragment = document.createDocumentFragment();
    items.forEach(function (post, index) {
      fragment.appendChild(makeCard(post));
      if ((index + 1) % 6 === 0 && index < items.length - 1) {
        fragment.appendChild(make('div', 'book-group-divider'));
      }
    });
    container.appendChild(fragment);
  }

  function render() {
    var input = byId('search-input');
    var query = input.value.trim();
    var results = posts.slice();
    if (query && window.WOWSmartSearch && typeof window.WOWSmartSearch.search === 'function') {
      results = window.WOWSmartSearch.search(results, query);
    } else if (query) {
      var q = query.toLocaleLowerCase();
      results = results.filter(function (post) {
        return [post.title, post.author, post.category, post.tags, post.excerpt]
          .join(' ').toLocaleLowerCase().includes(q);
      });
    }
    byId('results-count').textContent = 'တွေ့ရှိမှု ' + results.length + ' / ' + posts.length + ' ခု';
    renderCards(results);
  }

  function setView(nextView, persist) {
    if (VIEWS.indexOf(nextView) === -1) nextView = 'grid';
    view = nextView;
    byId('posts-container').dataset.view = view;
    document.querySelectorAll('#view-mode-buttons [data-view]').forEach(function (button) {
      button.setAttribute('aria-pressed', String(button.dataset.view === view));
    });
    if (persist !== false) {
      try { window.localStorage.setItem(VIEW_KEY, view); } catch (_) {}
    }
    render();
  }

  function bindControls() {
    document.querySelectorAll('#view-mode-buttons [data-view]').forEach(function (button) {
      button.addEventListener('click', function () { setView(button.dataset.view); });
    });
    byId('search-input').addEventListener('input', function () {
      window.clearTimeout(searchTimer);
      searchTimer = window.setTimeout(render, 120);
    });
    byId('clear-search').addEventListener('click', function () {
      byId('search-input').value = '';
      render();
      byId('search-input').focus();
    });
  }

  async function load() {
    var container = byId('posts-container');
    try {
      var response = await fetch('assets/posts.json');
      if (!response.ok) throw new Error('Review list request failed');
      var data = await response.json();
      posts = Array.isArray(data) ? data : [];
      render();
    } catch (_) {
      container.replaceChildren(make('div', 'loading', 'ပို့စ်များကို ဖတ်၍မရပါ။ Blog မှာ ဖတ်ပါ။'));
      byId('results-count').textContent = '';
    }
  }

  function init() {
    bindControls();
    byId('posts-container').dataset.view = 'grid';
    try { window.localStorage.removeItem(VIEW_KEY); } catch (_) {}
    load();
  }

  window.WOWCatalogViews = { init: init, setView: setView };
}());
