(function () {
  'use strict';

  var config = {
    apiKey: 'AIzaSyBX28BIHkrQzF7QmAEsoh8OPdEIaFILYRA',
    authDomain: 'github-comment-9f76d.firebaseapp.com',
    projectId: 'github-comment-9f76d',
    storageBucket: 'github-comment-9f76d.firebasestorage.app',
    messagingSenderId: '423917068098',
    appId: '1:423917068098:web:bfb899f06ae1375741b2db',
    measurementId: 'G-JCNEDWBDB1'
  };

  var panel = document.getElementById('commentsPanel');
  if (!panel || !window.firebase) return;
  var postId = panel.getAttribute('data-post-id');
  var commentsList = document.getElementById('commentsList');
  var form = document.getElementById('commentForm');
  var nameInput = document.getElementById('commentName');
  var textInput = document.getElementById('commentText');
  var ratingInput = document.getElementById('commentRating');
  var status = document.getElementById('commentStatus');
  var submit = document.getElementById('commentSubmit');
  var selectedRating = 0;

  try { firebase.initializeApp(config); } catch (e) {
    if (!/already exists/.test(String(e))) { status.textContent = 'Comment စနစ်ကို ချိတ်ဆက်၍မရပါ။'; return; }
  }
  var db = firebase.firestore();
  var auth = firebase.auth();

  function setStatus(message, error) {
    status.textContent = message;
    status.classList.toggle('error', !!error);
  }

  function drawStars(value) {
    document.querySelectorAll('.rating-star').forEach(function (button) {
      var n = Number(button.getAttribute('data-rating'));
      button.classList.toggle('selected', n <= value);
      button.setAttribute('aria-pressed', n <= value ? 'true' : 'false');
    });
  }

  document.querySelectorAll('.rating-star').forEach(function (button) {
    button.addEventListener('click', function () {
      selectedRating = Number(button.getAttribute('data-rating'));
      ratingInput.value = String(selectedRating);
      drawStars(selectedRating);
    });
  });

  function renderComments(snapshot) {
    var rows = [];
    snapshot.forEach(function (doc) { rows.push({ id: doc.id, data: doc.data() }); });
    rows.sort(function (a, b) {
      var at = a.data.createdAt && a.data.createdAt.toMillis ? a.data.createdAt.toMillis() : 0;
      var bt = b.data.createdAt && b.data.createdAt.toMillis ? b.data.createdAt.toMillis() : 0;
      return bt - at;
    });
    commentsList.innerHTML = '';
    if (!rows.length) {
      commentsList.innerHTML = '<p class="comments-empty">အတည်ပြုပြီးသော comment မရှိသေးပါ။ ပထမဆုံးရေးပေးနိုင်ပါတယ်။</p>';
      return;
    }
    rows.forEach(function (row) {
      var item = document.createElement('article');
      item.className = 'comment-item';
      var head = document.createElement('div');
      head.className = 'comment-head';
      var author = document.createElement('strong');
      author.textContent = row.data.displayName || 'စာဖတ်သူ';
      var stars = document.createElement('span');
      stars.className = 'comment-stars';
      stars.textContent = '★'.repeat(Math.max(0, Math.min(5, Number(row.data.rating) || 0)));
      head.appendChild(author); head.appendChild(stars);
      var body = document.createElement('p');
      body.className = 'comment-text';
      body.textContent = row.data.text || '';
      item.appendChild(head); item.appendChild(body);
      if (String(row.data.text || '').length > 100) {
        item.classList.add('comment-collapsed');
        var toggle = document.createElement('button');
        toggle.type = 'button';
        toggle.className = 'comment-toggle';
        toggle.setAttribute('aria-expanded', 'false');
        toggle.textContent = 'ဆက်ဖတ်ရန် ↓';
        toggle.addEventListener('click', function () {
          var expanded = item.classList.toggle('comment-expanded');
          item.classList.toggle('comment-collapsed', !expanded);
          toggle.setAttribute('aria-expanded', expanded ? 'true' : 'false');
          toggle.textContent = expanded ? 'လျှော့ပြရန် ↑' : 'ဆက်ဖတ်ရန် ↓';
        });
        item.appendChild(toggle);
      }
      commentsList.appendChild(item);
    });
  }

  var activeCommentUid = null;
  var commentUnsubscribe = null;
  var anonymousSignInPending = false;
  auth.onAuthStateChanged(function (user) {
    if (!user) {
      if (!anonymousSignInPending) {
        anonymousSignInPending = true;
        auth.signInAnonymously().catch(function () { setStatus('Comment ရေးရန် ချိတ်ဆက်၍မရပါ။', true); }).then(function () { anonymousSignInPending = false; });
      }
      return;
    }
    if (activeCommentUid === user.uid) return;
    if (commentUnsubscribe) commentUnsubscribe();
    activeCommentUid = user.uid;
    commentUnsubscribe = db.collection('posts').doc(String(postId)).collection('comments')
      .limit(50).onSnapshot(renderComments, function () {
        setStatus('Comment များကို ရယူ၍မရပါ။', true);
      });
  }, function () { setStatus('Comment များကို ရယူ၍မရပါ။', true); });

  form.addEventListener('submit', function (event) {
    event.preventDefault();
    var user = auth.currentUser;
    var name = nameInput.value.trim();
    var text = textInput.value.trim();
    var rating = Number(ratingInput.value);
    if (!user) return setStatus('Comment စနစ်ကို ချိတ်ဆက်နေပါသည်။ ခဏစောင့်ပါ။', true);
    if (name.length < 1 || name.length > 40) return setStatus('အမည်ကို ၁ မှ ၄၀ စာလုံးအတွင်း ထည့်ပါ။', true);
    if (text.length < 2 || text.length > 1000) return setStatus('Comment ကို ၂ မှ ၁၀၀၀ စာလုံးအတွင်း ထည့်ပါ။', true);
    if (rating < 1 || rating > 5) return setStatus('ကြယ် rating ရွေးပါ။', true);
    submit.disabled = true;
    setStatus('ပို့နေပါသည်…');
    db.collection('posts').doc(String(postId)).collection('comments').add({
      uid: '', authorMode: 'anonymous',
      displayName: 'Anonymous', text: text, rating: rating,
      status: 'approved', createdAt: firebase.firestore.FieldValue.serverTimestamp()
    }).then(function () {
      form.reset(); selectedRating = 0; drawStars(0);
      setStatus('ကျေးဇူးတင်ပါတယ်။ Comment ပေါ်လာပါပြီ။');
    }).catch(function () { setStatus('Comment မပို့နိုင်ပါ။ ပြန်ကြိုးစားပါ။', true); })
      .finally(function () { submit.disabled = false; });
  });
}());
