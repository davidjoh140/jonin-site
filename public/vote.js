/* Jonin character voting — loaded on /character/<slug>/ pages.
   Signed-in people pick their coolest cards for each character (3 per character, set in Supabase by
   card_vote_limit()). They can move votes anytime. The live Top 3 shows once MIN_VOTERS people have voted.
   Uses the same Supabase project and login as the rest of jonin.cards, so a session from the homepage carries over. */
(function () {
  var SUPA = 'https://cfzpayanhvvqtkuqfgof.supabase.co', KEY = 'sb_publishable_ZR1zggWL9FxxwfwoIASwSg_YDV3Nvfe';
  var MIN_VOTERS = 5; // people who must vote before a character's Top 3 shows (David confirmed 5)
  var box = document.getElementById('vote-top');
  if (!box) return;
  var CHAR = box.dataset.character, CNAME = box.dataset.name || 'this character';
  var sb = null, me = null, mine = new Set(), limit = 3, busy = false;
  // XP (2026-11-26): the first vote on a character earns XP once (Supabase xp_on_vote / xp_rules; amount is a PLACEHOLDER David sets there).
  var earned = true, xpEach = 0;
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
  // A vote tapped while signed out is remembered and cast as soon as they're signed in (also after the email-confirm link).
  var PKEY = 'jonin_pending_vote', pending = null;
  function pend(card) { pending = card; try { localStorage.setItem(PKEY, JSON.stringify({ c: CHAR, card: card, t: Date.now() })); } catch (_) {} }
  function takePending() {
    var p = null; try { p = JSON.parse(localStorage.getItem(PKEY) || 'null'); } catch (_) {}
    if (p && p.c === CHAR && Date.now() - p.t < 864e5) { try { localStorage.removeItem(PKEY); } catch (_) {} return p.card; }
    return null;
  }
  function loadMine() {
    mine.clear();
    if (!me) { paint(); return Promise.resolve(); }
    sb.from('xp_events').select('ref').eq('kind', 'vote').eq('ref', CHAR).then(function (r) { if (!r.error) earned = (r.data || []).length > 0; });
    sb.rpc('xp_rules').then(function (r) { if (!r.error && r.data) xpEach = r.data.vote_character || 0; });
    return sb.from('card_votes').select('card_id').eq('character', CHAR).then(function (r) {
      (r.data || []).forEach(function (x) { mine.add(x.card_id); }); paint();
      var c = takePending();
      if (c && !mine.has(c)) { if (mine.size < limit) { toggle(c); say('Vote cast. You have ' + (limit - mine.size - 1) + ' left for ' + CNAME + '.'); } else say('You already used all ' + limit + ' votes for ' + CNAME + '.'); }
    });
  }

  function say(msg) {
    var t = $('#vote-toast'); t.textContent = msg; t.hidden = false;
    clearTimeout(say.h); say.h = setTimeout(function () { t.hidden = true; }, 4000);
  }

  function toggle(card) {
    if (!sb || busy) return;
    if (!me) { pend(card); openAuth('up'); return; }
    var on = mine.has(card);
    if (!on && mine.size >= limit) { say('You have used all ' + limit + ' votes for ' + CNAME + '. Tap a ✓ Voted card to free one up.'); return; }
    busy = true; paint();
    var q = on ? sb.from('card_votes').delete().eq('character', CHAR).eq('card_id', card)
               : sb.from('card_votes').insert({ character: CHAR, card_id: card });
    q.then(function (r) {
      busy = false;
      if (r.error) { say(r.error.message || 'Could not save your vote.'); paint(); return; }
      if (on) mine.delete(card); else mine.add(card);
      if (!on && !earned) {
        earned = true;
        if (xpEach) say('+' + xpEach + ' XP for voting on ' + CNAME + '! More missions on the Missions page.');
        if (window.JoninAcct && JoninAcct.refresh) JoninAcct.refresh();
      }
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
      '<p>' + (mode === 'up' ? (pending ? 'Make a free account to cast your vote. It counts as soon as you’re in.' : 'Vote for the coolest cards, and track your haves, wants and slabs.') : (pending ? 'Sign in to cast your vote.' : 'Welcome back.')) + '</p>' +
      '<div class="oauth"><button type="button" class="oa" data-oauth="google"><svg viewBox="0 0 48 48" width="18" height="18" aria-hidden="true"><path fill="#FFC107" d="M43.6 20.5H42V20H24v8h11.3C33.7 32.7 29.2 36 24 36c-6.6 0-12-5.4-12-12s5.4-12 12-12c3.1 0 5.8 1.2 7.9 3.1l5.7-5.7C34 6.1 29.3 4 24 4 12.9 4 4 12.9 4 24s8.9 20 20 20 20-8.9 20-20c0-1.3-.1-2.4-.4-3.5z"/><path fill="#FF3D00" d="m6.3 14.7 6.6 4.8C14.7 15.1 19 12 24 12c3.1 0 5.8 1.2 7.9 3.1l5.7-5.7C34 6.1 29.3 4 24 4 16.3 4 9.7 8.3 6.3 14.7z"/><path fill="#4CAF50" d="M24 44c5.2 0 9.9-2 13.4-5.2l-6.2-5.2C29.2 35.1 26.7 36 24 36c-5.2 0-9.6-3.3-11.3-7.9l-6.5 5C9.5 39.6 16.2 44 24 44z"/><path fill="#1976D2" d="M43.6 20.5H42V20H24v8h11.3c-.8 2.2-2.2 4.2-4.1 5.6l6.2 5.2C37 39.2 44 34 44 24c0-1.3-.1-2.4-.4-3.5z"/></svg>Continue with Google</button><button type="button" class="oa" data-oauth="discord"><svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path fill="#5865F2" d="M20.3 4.4A19.8 19.8 0 0 0 15.4 3l-.6 1.3a18.4 18.4 0 0 0-5.6 0L8.6 3a19.7 19.7 0 0 0-4.9 1.4C.6 9.1-.3 13.6.1 18.1a19.9 19.9 0 0 0 6 3l1.3-2.1a12.9 12.9 0 0 1-2-1l.5-.4a14.2 14.2 0 0 0 12.2 0l.5.4a12.9 12.9 0 0 1-2 1l1.3 2.1a19.8 19.8 0 0 0 6-3c.5-5.2-.8-9.7-3.6-13.7zM8 15.4c-1.2 0-2.2-1.1-2.2-2.4S6.8 10.6 8 10.6s2.2 1.1 2.2 2.4-1 2.4-2.2 2.4zm8 0c-1.2 0-2.2-1.1-2.2-2.4s1-2.4 2.2-2.4 2.2 1.1 2.2 2.4-1 2.4-2.2 2.4z"/></svg>Continue with Discord</button></div><div class="orline"><span>or use email</span></div>' +
      (mode === 'up' ? '<label>Username<input name="handle" autocomplete="username" maxlength="24" required></label>' : '') +
      '<label>Email<input name="email" type="email" autocomplete="email" required></label>' +
      '<label>Password<input name="pw" type="password" autocomplete="' + (mode === 'up' ? 'new-password' : 'current-password') + '" minlength="8" required></label>' +
      '<p class="verr" hidden></p><button class="vgo" type="submit">' + (mode === 'up' ? 'Create account' : 'Sign in') + '</button>' +
      '<p class="vswap">' + (mode === 'up' ? 'Have an account? <button type="button" class="vlink" data-vauth="in">Sign in</button>' : 'New here? <button type="button" class="vlink" data-vauth="up">Make a free account</button>') + '</p>';
  }
  ov.addEventListener('click', function (e) { if (e.target.classList.contains('vbg')) ov.hidden = true; });
  // Only show one-click buttons for providers switched on in Supabase.
  var OAUTH_ON = null;
  function paintOauth() {
    if (!OAUTH_ON) return;
    var any = false;
    Array.prototype.forEach.call(ov.querySelectorAll('[data-oauth]'), function (b) { b.hidden = !OAUTH_ON[b.dataset.oauth]; if (!b.hidden) any = true; });
    var o = ov.querySelector('.oauth'), l = ov.querySelector('.orline'); if (o) o.hidden = !any; if (l) l.hidden = !any;
  }
  fetch(SUPA + '/auth/v1/settings', { headers: { apikey: KEY } }).then(function (r) { return r.json(); }).then(function (j) { OAUTH_ON = j.external || {}; paintOauth(); }).catch(function () { OAUTH_ON = {}; });
  new MutationObserver(paintOauth).observe($('form', ov), { childList: true });
  // One-click sign-in with Google or Discord; comes back to this character page (a pending vote is kept in this browser).
  ov.addEventListener('click', function (e) {
    var b = e.target.closest('[data-oauth]'); if (!b || !sb) return; e.preventDefault(); b.disabled = true;
    sb.auth.signInWithOAuth({ provider: b.dataset.oauth, options: { redirectTo: location.origin + location.pathname } }).then(function (r) {
      if (r.error) { b.disabled = false; var er = $('.verr', ov); er.textContent = r.error.message || 'Could not start sign-in.'; er.hidden = false; }
    });
  });
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
      if (mode === 'up' && !r.data.session) { err.textContent = 'Check your email and click the link to finish signing up. You will land back here and your vote will be cast.'; err.hidden = false; go.disabled = false; return; }
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
