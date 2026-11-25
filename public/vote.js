/* Jonin character voting — loaded on /character/<slug>/ pages.
   Signed-in people pick their coolest cards for each character (3 per character, set in Supabase by
   card_vote_limit()). They can move votes anytime. The live Top 3 shows once MIN_VOTERS people have voted.
   Uses the same Supabase project and login as the rest of jonin.cards, so a session from the homepage carries over. */
(function () {
  var SUPA = 'https://cfzpayanhvvqtkuqfgof.supabase.co', KEY = 'sb_publishable_ZR1zggWL9FxxwfwoIASwSg_YDV3Nvfe';
  var MIN_VOTERS = 5; // PLACEHOLDER: people who must vote before a character's Top 3 shows. David to confirm.
  var box = document.getElementById('vote-top');
  if (!box) return;
  var CHAR = box.dataset.character, CNAME = box.dataset.name || 'this character';
  var sb = null, me = null, mine = new Set(), limit = 3, busy = false;
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var esc = function (v) { return String(v == null ? '' : v).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); };
  var tiles = Array.prototype.slice.call(document.querySelectorAll('.tile[data-card]'));

  function load(src, cb) { var s = document.createElement('script'); s.src = src; s.onload = cb; document.head.appendChild(s); }

  // One vote button per tile (a card can appear twice: Key cards and its set).
  tiles.forEach(function (t) {
    var b = document.createElement('button');
    b.type = 'button'; b.className = 'vbtn'; b.dataset.card = t.dataset.card;
    b.innerHTML = '<span class="vi">▲</span><span class="vt">Vote</span><span class="vn"></span>';
    b.addEventListener('click', function (ev) { ev.preventDefault(); ev.stopPropagation(); toggle(t.dataset.card); });
    t.appendChild(b);
  });

  function paint(totals) {
    var left = limit - mine.size;
    document.querySelectorAll('.vbtn').forEach(function (b) {
      var on = mine.has(b.dataset.card);
      b.classList.toggle('on', on);
      $('.vt', b).textContent = on ? 'Voted' : 'Vote';
      b.disabled = busy;
      b.title = on ? 'Remove your vote' : me ? (left > 0 ? 'Vote for this card' : 'Remove a vote to pick this card') : 'Sign in to vote';
    });
    var bar = $('#vote-bar');
    if (bar) bar.innerHTML = me
      ? '<b>' + left + ' of ' + limit + '</b> votes left for ' + esc(CNAME) + '. Tap ▲ on a card to vote, tap again to take it back.'
      : 'Vote for the coolest ' + esc(CNAME) + ' cards. Everyone gets ' + limit + ' votes per character. <button type="button" class="vlink" data-vauth="in">Sign in</button> or <button type="button" class="vlink" data-vauth="up">make a free account</button> to vote.';
    if (totals) renderTop(totals);
  }

  var lastTotals = null;
  function renderTop(t) {
    lastTotals = t; limit = t.limit || limit;
    var counts = {}; (t.cards || []).forEach(function (c) { counts[c.card_id] = c.votes; });
    var show = t.voters >= MIN_VOTERS;
    document.querySelectorAll('.vbtn').forEach(function (b) { $('.vn', b).textContent = show && counts[b.dataset.card] ? counts[b.dataset.card] : ''; });
    var grid = $('#vote-grid'), note = $('#vote-note');
    if (!show) {
      grid.innerHTML = '';
      note.textContent = 'The Top 3 shows once ' + MIN_VOTERS + ' people have voted' + (t.voters ? ' (' + t.voters + ' so far).' : '. Be the first.');
      return;
    }
    note.textContent = t.voters + ' ' + (t.voters === 1 ? 'person has' : 'people have') + ' voted. Updates live.';
    var top = (t.cards || []).filter(function (c) { return document.querySelector('.cgroup .tile[data-card="' + CSS.escape(c.card_id) + '"]'); }).slice(0, 3);
    grid.innerHTML = '';
    top.forEach(function (c, i) {
      var src = document.querySelector('.cgroup .tile[data-card="' + CSS.escape(c.card_id) + '"]');
      var el = src.cloneNode(true); el.classList.add('ranked');
      var old = $('.vbtn', el); if (old) old.remove();
      var rk = document.createElement('span'); rk.className = 'rank'; rk.textContent = '#' + (i + 1);
      var vc = document.createElement('span'); vc.className = 'tn vcount'; vc.textContent = c.votes + (c.votes === 1 ? ' vote' : ' votes');
      el.insertBefore(rk, el.firstChild); el.appendChild(vc);
      grid.appendChild(el);
    });
  }

  function refresh() {
    return sb.rpc('character_votes', { p_character: CHAR }).then(function (r) { if (!r.error && r.data) renderTop(r.data); paint(); });
  }
  function loadMine() {
    mine.clear();
    if (!me) { paint(); return Promise.resolve(); }
    return sb.from('card_votes').select('card_id').eq('character', CHAR).then(function (r) {
      (r.data || []).forEach(function (x) { mine.add(x.card_id); }); paint();
    });
  }

  function say(msg) {
    var t = $('#vote-toast'); t.textContent = msg; t.hidden = false;
    clearTimeout(say.h); say.h = setTimeout(function () { t.hidden = true; }, 4000);
  }

  function toggle(card) {
    if (!sb || busy) return;
    if (!me) { openAuth('up'); return; }
    var on = mine.has(card);
    if (!on && mine.size >= limit) { say('You have used all ' + limit + ' votes for ' + CNAME + '. Tap a ✓ Voted card to free one up.'); return; }
    busy = true; paint();
    var q = on ? sb.from('card_votes').delete().eq('character', CHAR).eq('card_id', card)
               : sb.from('card_votes').insert({ character: CHAR, card_id: card });
    q.then(function (r) {
      busy = false;
      if (r.error) { say(r.error.message || 'Could not save your vote.'); paint(); return; }
      if (on) mine.delete(card); else mine.add(card);
      refresh();
    });
  }

  // Sign in / sign up, same accounts as the homepage.
  var ov = document.createElement('div');
  ov.className = 'vov'; ov.hidden = true;
  ov.innerHTML = '<button class="vbg" type="button" aria-label="Close"></button><form class="vbox" novalidate></form>';
  document.body.appendChild(ov);
  var mode = 'up';
  function openAuth(m) { mode = m; drawAuth(); ov.hidden = false; var f = $('input', ov); if (f) f.focus(); }
  function drawAuth() {
    $('form', ov).innerHTML =
      '<h2>' + (mode === 'up' ? 'Make a free account' : 'Sign in') + '</h2>' +
      '<p>' + (mode === 'up' ? 'Vote for the coolest cards and keep a list of your collection.' : 'Welcome back.') + '</p>' +
      (mode === 'up' ? '<label>Username<input name="handle" autocomplete="username" maxlength="24" required></label>' : '') +
      '<label>Email<input name="email" type="email" autocomplete="email" required></label>' +
      '<label>Password<input name="pw" type="password" autocomplete="' + (mode === 'up' ? 'new-password' : 'current-password') + '" minlength="8" required></label>' +
      '<p class="verr" hidden></p><button class="vgo" type="submit">' + (mode === 'up' ? 'Create account' : 'Sign in') + '</button>' +
      '<p class="vswap">' + (mode === 'up' ? 'Have an account? <button type="button" class="vlink" data-vauth="in">Sign in</button>' : 'New here? <button type="button" class="vlink" data-vauth="up">Make a free account</button>') + '</p>';
  }
  ov.addEventListener('click', function (e) { if (e.target.classList.contains('vbg')) ov.hidden = true; });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') ov.hidden = true; });
  document.addEventListener('click', function (e) { var b = e.target.closest('[data-vauth]'); if (b) { e.preventDefault(); openAuth(b.dataset.vauth); } });
  $('form', ov).addEventListener('submit', function (e) {
    e.preventDefault();
    var f = e.target, err = $('.verr', f), go = $('.vgo', f);
    var email = f.email.value.trim(), pw = f.pw.value, handle = f.handle ? f.handle.value.trim() : '';
    function fail(m) { err.textContent = m; err.hidden = false; go.disabled = false; }
    if (!/^\S+@\S+\.\S+$/.test(email)) return fail('Enter your email.');
    if (pw.length < 8) return fail('Password: at least 8 characters.');
    if (mode === 'up' && !/^[A-Za-z0-9_]{3,24}$/.test(handle)) return fail('Username: 3–24 letters, numbers or _.');
    go.disabled = true; err.hidden = true;
    var p = mode === 'up'
      ? sb.auth.signUp({ email: email, password: pw, options: { data: { handle: handle }, emailRedirectTo: location.href } })
      : sb.auth.signInWithPassword({ email: email, password: pw });
    p.then(function (r) {
      if (r.error) return fail(r.error.message || 'Something went wrong.');
      if (mode === 'up' && !r.data.session) { err.textContent = 'Check your email and click the link to finish signing up. You will land back here to vote.'; err.hidden = false; go.disabled = false; return; }
      ov.hidden = true;
    });
  });

  function start() {
    sb = window.supabase.createClient(SUPA, KEY);
    sb.auth.getSession().then(function (r) { me = r.data.session ? r.data.session.user : null; loadMine(); });
    sb.auth.onAuthStateChange(function (ev, s) { var u = s ? s.user : null; if ((u && u.id) !== (me && me.id)) { me = u; loadMine(); } });
    refresh();
    setInterval(function () { if (!document.hidden) refresh(); }, 30000);
  }
  paint();
  if (window.supabase) start(); else load('https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.119.2/dist/umd/supabase.min.js', start);
})();
