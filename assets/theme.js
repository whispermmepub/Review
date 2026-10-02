(function () {
  'use strict';
  var KEY = 'wow-theme';
  var root = document.documentElement;
  function getTheme() {
    try {
      var saved = localStorage.getItem(KEY);
      if (saved === 'dark' || saved === 'light') return saved;
    } catch (_) {}
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
  function apply(theme) {
    root.setAttribute('data-theme', theme);
    document.querySelectorAll('[data-theme-toggle]').forEach(function (button) {
      var dark = theme === 'dark';
      button.textContent = dark ? '☀️ Light mode' : '🌙 Dark mode';
      button.setAttribute('aria-pressed', dark ? 'true' : 'false');
      button.setAttribute('aria-label', dark ? 'Light mode သို့ပြောင်းရန်' : 'Dark mode သို့ပြောင်းရန်');
    });
  }
  function toggle() {
    var next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    try { localStorage.setItem(KEY, next); } catch (_) {}
    apply(next);
  }
  window.WOWTheme = { apply: apply, toggle: toggle };
  apply(getTheme());
  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('[data-theme-toggle]').forEach(function (button) {
      button.addEventListener('click', toggle);
    });
    apply(root.getAttribute('data-theme') || getTheme());
  });
}());
