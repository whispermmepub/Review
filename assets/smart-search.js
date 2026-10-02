(function () {
  'use strict';

  function normalize(value) {
    return String(value || '')
      .normalize('NFC')
      .toLowerCase()
      .replace(/[\u200b\ufeff]/g, '')
      .replace(/နှင့်/g, 'နှင့်')
      .replace(/၏/g, 'ရဲ့')
      .replace(/[“”"'‘’`.,!?;:()[\]{}<>/\\|_+=*#@~^%&$-]/g, ' ')
      .replace(/\s+/g, ' ')
      .trim();
  }

  function compact(value) {
    return normalize(value).replace(/\s+/g, '');
  }

  function tokens(value) {
    return normalize(value).split(' ').filter(Boolean);
  }

  var aliases = {
    'ဟဲမင်းဝေး': 'hemingway ernest hemingway',
    'ပင်လယ် တံငါ': 'old man sea',
    'တံငါအို': 'old man sea',
    'ဖန်တက်စီ': 'fantasy',
    'ဒစ်စတိုပီးယန်း': 'dystopian'
  };

  function expandQuery(value) {
    var clean = normalize(value);
    var extras = [];
    Object.keys(aliases).forEach(function (key) {
      if (clean.indexOf(normalize(key)) !== -1) extras.push(aliases[key]);
    });
    return extras.length ? clean + ' ' + extras.join(' ') : clean;
  }

  function levenshtein(a, b) {
    if (a === b) return 0;
    if (!a) return b.length;
    if (!b) return a.length;
    var previous = Array.from({ length: b.length + 1 }, function (_, i) { return i; });
    for (var i = 1; i <= a.length; i += 1) {
      var current = [i];
      for (var j = 1; j <= b.length; j += 1) {
        current[j] = Math.min(
          current[j - 1] + 1,
          previous[j] + 1,
          previous[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1)
        );
      }
      previous = current;
    }
    return previous[b.length];
  }

  function tokenMatch(queryToken, fieldTokens, fieldCompact) {
    if (!queryToken) return 0;
    if (fieldTokens.some(function (token) { return token === queryToken; })) return 1;
    if (fieldTokens.some(function (token) { return token.indexOf(queryToken) === 0; })) return 0.88;
    if (fieldCompact.indexOf(queryToken) !== -1) return 0.72;
    var best = 0;
    fieldTokens.forEach(function (token) {
      var maxLen = Math.max(queryToken.length, token.length);
      if (maxLen < 3) return;
      var distance = levenshtein(queryToken, token);
      var similarity = 1 - distance / maxLen;
      if (similarity >= 0.72) best = Math.max(best, similarity * 0.65);
    });
    return best;
  }

  function score(post, query) {
    var queryTokens = tokens(expandQuery(query));
    if (!queryTokens.length) return 0;
    var fields = [
      { value: post.title, weight: 8 },
      { value: post.author, weight: 6 },
      { value: post.category, weight: 4 },
      { value: post.tags, weight: 3 },
      { value: post.excerpt, weight: 2 }
    ];
    var total = 0;
    var matched = 0;
    fields.forEach(function (field) {
      var value = Array.isArray(field.value) ? field.value.join(' ') : field.value;
      var fieldTokens = tokens(value);
      var fieldCompact = compact(value);
      var fieldScore = 0;
      queryTokens.forEach(function (queryToken) {
        fieldScore += tokenMatch(queryToken, fieldTokens, fieldCompact);
      });
      if (fieldScore > 0) {
        matched += 1;
        total += fieldScore * field.weight;
      }
    });
    if (matched === 0) return 0;
    var whole = compact(query);
    var titleCompact = compact(post.title);
    if (titleCompact.indexOf(whole) !== -1) total += 12;
    if (compact(post.author).indexOf(whole) !== -1) total += 8;
    return total * (matched === fields.length ? 1.12 : 1);
  }

  function search(posts, query) {
    var clean = expandQuery(query);
    if (!clean) return posts.slice();
    return posts
      .map(function (post, index) {
        return { post: post, score: score(post, clean), index: index };
      })
      .filter(function (item) { return item.score > 0; })
      .sort(function (a, b) { return b.score - a.score || a.index - b.index; })
      .map(function (item) { return item.post; });
  }

  window.WOWSmartSearch = { normalize: normalize, search: search };
}());
