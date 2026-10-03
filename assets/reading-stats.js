(function () {
  'use strict';

  var KEY = 'wowReviewReadingStatsV1';
  var DEVICE_KEY = 'wowReviewStatsDeviceV1';
  var PROFILE_KEY = 'wowGoogleProfileV1';
  var config = {
    apiKey: 'AIzaSyBX28BIHkrQzF7QmAEsoh8OPdEIaFILYRA',
    authDomain: 'github-comment-9f76d.firebaseapp.com',
    projectId: 'github-comment-9f76d',
    storageBucket: 'github-comment-9f76d.firebasestorage.app',
    messagingSenderId: '423917068098',
    appId: '1:423917068098:web:bfb899f06ae1375741b2db'
  };

  function emptyStats() { return { reviews: {}, totalSeconds: 0, daily: {} }; }
  function number(value) { value = Number(value); return Number.isFinite(value) && value > 0 ? value : 0; }
  function normalize(data) {
    if (!data || typeof data !== 'object') return emptyStats();
    var rawReviews = data.reviews && typeof data.reviews === 'object' ? data.reviews : data.books;
    var result = emptyStats();
    result.totalSeconds = number(data.totalSeconds);
    if (rawReviews && typeof rawReviews === 'object') {
      Object.keys(rawReviews).forEach(function (key) {
        var item = rawReviews[key];
        if (!item || typeof item !== 'object') return;
        result.reviews[key] = {
          firstOpened: number(item.firstOpened),
          lastOpened: number(item.lastOpened),
          seconds: number(item.seconds)
        };
      });
    }
    if (data.daily && typeof data.daily === 'object') {
      Object.keys(data.daily).forEach(function (key) { result.daily[key] = number(data.daily[key]); });
    }
    return result;
  }
  function load() {
    try {
      var raw = localStorage.getItem(KEY);
      return raw ? normalize(JSON.parse(raw)) : emptyStats();
    } catch (_) { return emptyStats(); }
  }
  function save(data, schedule) {
    var safe = normalize(data);
    try { localStorage.setItem(KEY, JSON.stringify(safe)); } catch (_) {}
    if (schedule !== false) scheduleCloudSync(false);
    return safe;
  }
  function getStoredProfilePhoto(user) {
    if (!user) return '';
    try {
      var raw = localStorage.getItem(PROFILE_KEY);
      var saved = raw ? JSON.parse(raw) : null;
      return saved && saved.uid === user.uid ? String(saved.photoURL || '') : '';
    } catch (_) { return ''; }
  }
  function dateKey(date) {
    var d = date || new Date();
    return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
  }
  function getId() {
    var match = location.pathname.match(/^\/Review\/(?:\d{4}\/\d{2}\/)?([^/]+)\/?(?:index\.html)?$/);
    if (!match) return null;
    var segment = match[1];
    if (/^\d+$/.test(segment)) return segment;
    var id = segment.match(/-(\d+)$/);
    return id ? id[1] : null;
  }
  function getDeviceId() {
    try {
      var value = localStorage.getItem(DEVICE_KEY);
      if (!value) {
        value = window.crypto && crypto.randomUUID ? crypto.randomUUID() : 'd-' + Date.now().toString(36) + Math.random().toString(36).slice(2);
        localStorage.setItem(DEVICE_KEY, value);
      }
      return value;
    } catch (_) { return 'd-' + Date.now().toString(36); }
  }
  function mergeSameDevice(first, second) {
    first = normalize(first); second = normalize(second);
    var merged = emptyStats();
    merged.totalSeconds = Math.max(first.totalSeconds, second.totalSeconds);
    Object.keys(first.daily).concat(Object.keys(second.daily)).forEach(function (day) {
      merged.daily[day] = Math.max(first.daily[day] || 0, second.daily[day] || 0);
    });
    var keys = Object.keys(first.reviews).concat(Object.keys(second.reviews));
    keys.forEach(function (key) {
      if (merged.reviews[key]) return;
      var a = first.reviews[key] || {}, b = second.reviews[key] || {};
      var opened = [number(a.firstOpened), number(b.firstOpened)].filter(Boolean);
      merged.reviews[key] = {
        firstOpened: opened.length ? Math.min.apply(Math, opened) : 0,
        lastOpened: Math.max(number(a.lastOpened), number(b.lastOpened)),
        seconds: Math.max(number(a.seconds), number(b.seconds))
      };
    });
    return merged;
  }
  function addSource(target, source) {
    source = normalize(source);
    target.totalSeconds += source.totalSeconds;
    Object.keys(source.daily).forEach(function (day) { target.daily[day] = (target.daily[day] || 0) + source.daily[day]; });
    Object.keys(source.reviews).forEach(function (key) {
      var item = source.reviews[key], current = target.reviews[key];
      if (!current) {
        target.reviews[key] = { firstOpened: item.firstOpened, lastOpened: item.lastOpened, seconds: item.seconds };
      } else {
        var dates = [current.firstOpened, item.firstOpened].filter(Boolean);
        current.firstOpened = dates.length ? Math.min.apply(Math, dates) : 0;
        current.lastOpened = Math.max(current.lastOpened, item.lastOpened);
        current.seconds += item.seconds;
      }
    });
  }

  var pageId = getId();
  var firebase = window.firebase || null;
  var auth = null;
  var db = null;
  var authUser = null;
  var signedInUser = null;
  var lastAccountUid = null;
  var cloudSources = null;
  var syncTimer = null;
  var syncing = false;
  var syncAgain = false;
  var viewCounted = false;
  var lastActive = Date.now();
  var flushReadingTime = function () {};

  function status(text, isError) {
    var el = document.getElementById('stats-sync-status');
    if (el) {
      el.textContent = text;
      el.classList.toggle('is-error', !!isError);
    }
  }
  function notifyStatsChanged() {
    try { window.dispatchEvent(new CustomEvent('wow:reading-stats-updated')); } catch (_) {}
  }
  function getStats() {
    var local = load();
    if (!signedInUser || !cloudSources) return local;
    var sources = Object.assign({}, cloudSources);
    var deviceId = getDeviceId();
    sources[deviceId] = mergeSameDevice(local, sources[deviceId] || emptyStats());
    var combined = emptyStats();
    Object.keys(sources).forEach(function (key) { addSource(combined, sources[key]); });
    return combined;
  }
  function setAccountControls(user) {
    var signInButton = document.getElementById('stats-sync-signin');
    var signOutButton = document.getElementById('stats-sync-signout');
    var label = document.getElementById('stats-account-label');
    if (!signInButton || !signOutButton) return;
    var connected = !!(user && !user.isAnonymous);
    signInButton.hidden = false;
    signOutButton.hidden = !connected;
    signInButton.disabled = false;
    signInButton.replaceChildren();
    var providerPhoto = '';
    if (connected && Array.isArray(user.providerData)) {
      for (var providerIndex = 0; providerIndex < user.providerData.length; providerIndex += 1) {
        if (user.providerData[providerIndex] && user.providerData[providerIndex].photoURL) {
          providerPhoto = user.providerData[providerIndex].photoURL;
          break;
        }
      }
    }
    var photoUrl = connected && (user.photoURL || providerPhoto || getStoredProfilePhoto(user));
    function showAvatarFallback() {
      signInButton.replaceChildren();
      var fallback = document.createElement('span');
      fallback.className = 'account-avatar-fallback';
      fallback.setAttribute('aria-hidden', 'true');
      fallback.textContent = 'G';
      signInButton.appendChild(fallback);
    }
    if (photoUrl) {
      var image = document.createElement('img');
      image.src = photoUrl;
      image.alt = user.displayName || 'Google profile';
      image.referrerPolicy = 'no-referrer';
      image.addEventListener('error', showAvatarFallback, { once: true });
      signInButton.appendChild(image);
    } else {
      showAvatarFallback();
    }
    var accountName = connected ? (user.displayName || 'Google account') : 'Google login';
    signInButton.setAttribute('aria-label', connected ? accountName + ' — Google account' : 'Google အကောင့်ဖြင့် ဝင်ရန်');
    signInButton.title = connected ? accountName : 'Google အကောင့်ဖြင့် ဝင်ရန်';
    if (label) label.textContent = accountName;
    var panelEmail = document.getElementById('accountPanelEmail');
    if (panelEmail) panelEmail.textContent = connected ? (user.email || 'Google account ဖြင့် ချိတ်ဆက်ထားသည်') : 'Google account ဖြင့် ဝင်ရောက်ရန်';
    if (connected) status('Google အကောင့်နှင့် ချိတ်ဆက်ထားပြီး မှတ်တမ်းကို အွန်လိုင်းတွင် အရန်သိမ်းနေပါသည်။');
    else status('လောလောဆယ် ဤ browser ထဲတွင်သာ သိမ်းထားပါသည်။ Google အကောင့်နှင့် ချိတ်လျှင် browser ဒေတာရှင်းပြီးနောက် ပြန်ရယူနိုင်ပါသည်။');
  }
  function syncCloud() {
    if (!db || !signedInUser) return Promise.resolve(false);
    if (syncing) { syncAgain = true; return Promise.resolve(false); }
    syncing = true;
    var user = signedInUser;
    var deviceId = getDeviceId();
    var devices = db.collection('users').doc(user.uid).collection('readingStats');
    status('အွန်လိုင်းအရန်သိမ်းဆည်းမှုကို အပ်ဒိတ်လုပ်နေပါသည်…');
    return devices.get().then(function (snapshot) {
      var sources = {};
      snapshot.forEach(function (doc) { sources[doc.id] = normalize(doc.data()); });
      var local = mergeSameDevice(load(), sources[deviceId] || emptyStats());
      save(local, false);
      var payload = {
        schema: 1,
        reviews: local.reviews,
        totalSeconds: local.totalSeconds,
        daily: local.daily,
        updatedAt: firebase.firestore.FieldValue.serverTimestamp()
      };
      return devices.doc(deviceId).set(payload, { merge: true }).then(function () {
        if (signedInUser && signedInUser.uid === user.uid) {
          sources[deviceId] = local;
          cloudSources = sources;
          status('စာရင်းကို Google အကောင့်တွင် အရန်သိမ်းပြီးပါပြီ။ Browser ဒေတာရှင်းသွားလည်း ထိုအကောင့်ဖြင့် ပြန်ဝင်လျှင် ပြန်ရယူနိုင်ပါသည်။');
          notifyStatsChanged();
        }
        return true;
      });
    }).catch(function (error) {
      var code = error && error.code || '';
      if (code === 'permission-denied') status('အွန်လိုင်းအရန်သိမ်းခွင့်ကို Firebase တွင် မဖွင့်ရသေးပါ။ ယခုစာရင်းကို ဤ browser ထဲတွင် ဆက်သိမ်းထားပါသည်။', true);
      else status('အွန်လိုင်းအရန်သိမ်းရန် မချိတ်ဆက်နိုင်ပါ။ အင်တာနက်ကို စစ်ပြီး ထပ်ကြိုးစားပါ။', true);
      return false;
    }).then(function (result) {
      syncing = false;
      if (syncAgain) { syncAgain = false; scheduleCloudSync(true); }
      return result;
    });
  }
  function scheduleCloudSync(immediate) {
    if (!signedInUser || !db) return;
    if (syncing) { syncAgain = true; return; }
    if (syncTimer) {
      if (!immediate) return;
      clearTimeout(syncTimer);
    }
    syncTimer = setTimeout(function () { syncTimer = null; syncCloud(); }, immediate ? 0 : 12000);
  }
  function signIn() {
    if (!auth || !firebase || !firebase.auth.GoogleAuthProvider) {
      status('အကောင့်ဝင်စနစ်ကို ယခုအချိန်တွင် မစတင်နိုင်ပါ။', true);
      return Promise.reject(new Error('Firebase Auth is unavailable'));
    }
    var provider = new firebase.auth.GoogleAuthProvider();
    provider.setCustomParameters({ prompt: 'select_account' });
    var persistence = firebase.auth.Auth && firebase.auth.Auth.Persistence ? firebase.auth.Auth.Persistence.LOCAL : null;
    var prepare = persistence && auth.setPersistence ? auth.setPersistence(persistence) : Promise.resolve();
    return prepare.then(function () {
      var current = auth.currentUser;
      if (current && current.isAnonymous && current.linkWithPopup) {
        return current.linkWithPopup(provider).catch(function (error) {
          if (error.code === 'auth/credential-already-in-use' && error.credential && auth.signInWithCredential) return auth.signInWithCredential(error.credential);
          throw error;
        });
      }
      return auth.signInWithPopup(provider);
    }).catch(function (error) {
      if (error.code === 'auth/popup-blocked' || error.code === 'auth/operation-not-supported-in-this-environment') {
        var current = auth.currentUser;
        if (current && current.isAnonymous && current.linkWithRedirect) return current.linkWithRedirect(provider);
        if (auth.signInWithRedirect) return auth.signInWithRedirect(provider);
      }
      throw error;
    }).then(function (result) {
      if (result && result.user) {
        var additional = result.additionalUserInfo && result.additionalUserInfo.profile;
        var resultPhoto = additional && (additional.picture || additional.photoURL);
        if (resultPhoto) {
          try { localStorage.setItem(PROFILE_KEY, JSON.stringify({ uid: result.user.uid, photoURL: resultPhoto })); } catch (_) {}
        }
        signedInUser = result.user.isAnonymous ? null : result.user;
        if (signedInUser) { lastAccountUid = signedInUser.uid; syncCloud(); }
      }
      return result;
    }).catch(function (error) {
      var code = error && error.code || '';
      if (code === 'auth/operation-not-allowed') status('Firebase တွင် Google ဖြင့် ဝင်ရောက်ခွင့်ကို မဖွင့်ရသေးပါ။', true);
      else if (code === 'auth/unauthorized-domain') status('ဤ website လိပ်စာကို Firebase တွင် ခွင့်ပြုစာရင်းထည့်ရန် လိုအပ်ပါသည်။', true);
      else if (code === 'auth/popup-blocked' || code === 'auth/operation-not-supported-in-this-environment' || code === 'auth/web-storage-unsupported') status('Telegram အတွင်းမှ ဝင်ရောက်မရပါက website ကို Chrome တွင်ဖွင့်ပြီး ထပ်ကြိုးစားပါ။', true);
      else if (code !== 'auth/popup-closed-by-user' && code !== 'auth/cancelled-popup-request') status('အကောင့်ဝင်ရာတွင် မအောင်မြင်ပါ။ ထပ်ကြိုးစားပါ။', true);
      throw error;
    });
  }
  function signOut() {
    if (!auth) return Promise.resolve();
    return auth.signOut().then(function () {
      signedInUser = null; lastAccountUid = null; cloudSources = null;
      closeAccountPanel();
      setAccountControls(null); notifyStatsChanged();
    });
  }
  function renderPanelAvatar(user) {
    var holder = document.getElementById('accountPanelAvatar');
    if (!holder) return;
    holder.replaceChildren();
    var providerPhoto = '';
    if (user && Array.isArray(user.providerData)) {
      for (var i = 0; i < user.providerData.length; i += 1) {
        if (user.providerData[i] && user.providerData[i].photoURL) { providerPhoto = user.providerData[i].photoURL; break; }
      }
    }
    var photo = user && (user.photoURL || providerPhoto || getStoredProfilePhoto(user));
    if (photo) {
      var image = document.createElement('img');
      image.src = photo;
      image.alt = user.displayName || 'Google profile';
      image.referrerPolicy = 'no-referrer';
      holder.appendChild(image);
    } else holder.textContent = 'G';
  }
  function activityItem(link, title, detail) {
    var item = document.createElement(link ? 'a' : 'div');
    item.className = 'account-activity-item';
    if (link) item.href = link;
    var strong = document.createElement('strong'); strong.textContent = title; item.appendChild(strong);
    if (detail) { var span = document.createElement('span'); span.textContent = detail; item.appendChild(span); }
    return item;
  }
  function setActivityMessage(id, text) {
    var list = document.getElementById(id); if (!list) return;
    list.replaceChildren(); var message = document.createElement('p'); message.className = 'account-muted'; message.textContent = text; list.appendChild(message);
  }
  function loadAccountActivity() {
    var readList = document.getElementById('accountReadReviews');
    var commentList = document.getElementById('accountComments');
    if (!readList || !commentList || !signedInUser) return;
    fetch('assets/posts.json').then(function (response) { return response.json(); }).then(function (posts) {
      var byId = {}; (Array.isArray(posts) ? posts : []).forEach(function (post) { byId[String(post.id)] = post; });
      var reviews = getStats().reviews || {};
      var ids = Object.keys(reviews).sort(function (a,b) { return (reviews[b].lastOpened || 0) - (reviews[a].lastOpened || 0); });
      readList.replaceChildren();
      if (!ids.length) setActivityMessage('accountReadReviews', 'ဖတ်ထားသော Review မရှိသေးပါ။');
      else ids.slice(0,40).forEach(function (id) { var post = byId[id] || {}; var target = post.link ? '/Review/' + String(post.link).replace(/^\/+/, '') : ''; readList.appendChild(activityItem(target, post.title || ('Review #' + id), 'ဖတ်ချိန် ' + Math.floor((reviews[id].seconds || 0) / 60) + ' min')); });
    }).catch(function () { setActivityMessage('accountReadReviews', 'ဖတ်ထားသော Review စာရင်းကို ရယူ၍မရပါ။'); });
    if (!db || !db.collectionGroup) { setActivityMessage('accountComments', 'Comment စာရင်းကို ယခုမရနိုင်သေးပါ။'); return; }
    db.collectionGroup('comments').where('uid', '==', signedInUser.uid).get().then(function (snapshot) {
      var rows = []; snapshot.forEach(function (doc) { var data = doc.data() || {}; rows.push({ data: data, postId: doc.ref.parent.parent ? doc.ref.parent.parent.id : '' }); });
      rows.sort(function (a,b) { var at=a.data.createdAt && a.data.createdAt.toMillis ? a.data.createdAt.toMillis() : 0; var bt=b.data.createdAt && b.data.createdAt.toMillis ? b.data.createdAt.toMillis() : 0; return bt-at; });
      return fetch('assets/posts.json').then(function (response) { return response.json(); }).then(function (posts) { var byId={}; (Array.isArray(posts)?posts:[]).forEach(function(post){byId[String(post.id)]=post;}); commentList.replaceChildren(); if (!rows.length) { setActivityMessage('accountComments','ရေးထားသော Comment မရှိသေးပါ။'); return; } rows.slice(0,40).forEach(function(row){ var post=byId[row.postId]||{}; var target=post.link?'/Review/'+String(post.link).replace(/^\/+/, ''):''; var text=String(row.data.text||'').replace(/\s+/g,' ').trim(); commentList.appendChild(activityItem(target,post.title||('Review #'+row.postId),text.length>90?text.slice(0,90)+'…':text)); }); });
    }).catch(function () { setActivityMessage('accountComments', 'ရေးထားသော Comment စာရင်းကို ရယူ၍မရပါ။'); });
  }
  function openAccountPanel() {
    if (!signedInUser) return;
    var panel = document.getElementById('accountPanel'); if (!panel) return;
    var title = document.getElementById('accountPanelTitle'); if (title) title.textContent = signedInUser.displayName || 'Google account';
    renderPanelAvatar(signedInUser); panel.hidden = false; panel.setAttribute('aria-hidden','false'); loadAccountActivity();
  }
  function closeAccountPanel() { var panel=document.getElementById('accountPanel'); if (panel) { panel.hidden=true; panel.setAttribute('aria-hidden','true'); } }
  function bindAccountControls() {
    var signInButton = document.getElementById('stats-sync-signin');
    var signOutButton = document.getElementById('stats-sync-signout');
    if (signInButton) signInButton.addEventListener('click', function () {
      if (signedInUser) { openAccountPanel(); return; }
      signInButton.disabled = true;
      status('Google အကောင့်နှင့် ချိတ်ဆက်နေပါသည်…');
      signIn().catch(function () {}).then(function () { signInButton.disabled = false; });
    });
    if (signOutButton) signOutButton.addEventListener('click', function () {
      signOutButton.disabled = true;
      signOut().catch(function () { status('အကောင့်မှ ထွက်ရာတွင် အမှားဖြစ်ပါသည်။', true); }).then(function () { signOutButton.disabled = false; });
    });
    document.querySelectorAll('[data-account-close]').forEach(function (button) { button.addEventListener('click', closeAccountPanel); });
    var panelSignout = document.getElementById('accountPanelSignout');
    if (panelSignout) panelSignout.addEventListener('click', function () { panelSignout.disabled = true; signOut().catch(function () { status('အကောင့်မှ ထွက်ရာတွင် အမှားဖြစ်ပါသည်။', true); }).then(function () { panelSignout.disabled = false; closeAccountPanel(); }); });
  }

  window.WOWReadingStats = {
    get: getStats,
    flush: function () { flushReadingTime(); },
    formatMinutes: function (seconds) { return Math.floor((seconds || 0) / 60); },
    signIn: signIn,
    signOut: signOut,
    isCloudConnected: function () { return !!signedInUser; }
  };

  bindAccountControls();
  if (firebase) {
    try {
      if (!firebase.apps.length) firebase.initializeApp(config);
      auth = firebase.auth();
      db = firebase.firestore();
      if (auth.onAuthStateChanged) auth.onAuthStateChanged(function (user) {
        authUser = user || null;
        var accountUser = user && !user.isAnonymous ? user : null;
        signedInUser = accountUser;
        if (accountUser) {
          if (lastAccountUid !== accountUser.uid) {
            lastAccountUid = accountUser.uid;
            cloudSources = null;
            syncCloud();
          }
        } else {
          lastAccountUid = null;
          cloudSources = null;
        }
        setAccountControls(accountUser);
        if (accountUser && typeof accountUser.reload === 'function') {
          accountUser.reload().then(function () {
            var freshUser = auth && auth.currentUser && !auth.currentUser.isAnonymous ? auth.currentUser : null;
            if (freshUser && freshUser.uid === accountUser.uid) {
              signedInUser = freshUser;
              setAccountControls(freshUser);
            }
          }).catch(function () {});
        }
        notifyStatsChanged();
        if (user && pageId && db && !viewCounted) {
          viewCounted = true;
          db.collection('reviewStats').doc(pageId).set({ views: firebase.firestore.FieldValue.increment(1), updatedAt: firebase.firestore.FieldValue.serverTimestamp() }, { merge: true }).catch(function () {});
        }
      }, function () { setAccountControls(null); });
    } catch (_) { auth = null; db = null; }
  }

  if (!pageId) return;

  var initial = load();
  var now = Date.now();
  if (!initial.reviews[pageId]) initial.reviews[pageId] = { firstOpened: now, lastOpened: now, seconds: 0 };
  else initial.reviews[pageId].lastOpened = now;
  save(initial);

  flushReadingTime = function () {
    var current = Date.now();
    var elapsed = Math.floor((current - lastActive) / 1000);
    if (elapsed <= 0) { lastActive = current; return; }
    var seconds = Math.min(elapsed, 300);
    lastActive = current;
    var local = load();
    if (!local.reviews[pageId]) local.reviews[pageId] = { firstOpened: current, lastOpened: current, seconds: 0 };
    local.reviews[pageId].seconds = (local.reviews[pageId].seconds || 0) + seconds;
    local.reviews[pageId].lastOpened = current;
    local.totalSeconds = (local.totalSeconds || 0) + seconds;
    var key = dateKey();
    local.daily[key] = (local.daily[key] || 0) + seconds;
    save(local);
    if (db && authUser) {
      db.collection('reviewStats').doc(pageId).set({ seconds: firebase.firestore.FieldValue.increment(seconds), updatedAt: firebase.firestore.FieldValue.serverTimestamp() }, { merge: true }).catch(function () {});
    }
  };

  var timer = setInterval(flushReadingTime, 5000);
  document.addEventListener('visibilitychange', function () {
    if (document.hidden) { flushReadingTime(); scheduleCloudSync(true); }
    else lastActive = Date.now();
  });
  window.addEventListener('pagehide', function () { flushReadingTime(); scheduleCloudSync(true); clearInterval(timer); });
  window.addEventListener('beforeunload', function () { flushReadingTime(); scheduleCloudSync(true); clearInterval(timer); });
}());
