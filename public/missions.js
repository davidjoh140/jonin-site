/* jonin.cards /missions/ page: fills in the signed-in member's scrolls, rank and mission progress.
   Scroll amounts and ranks come from Supabase (xp_rules, xp_ranks, my_xp), so changing them there updates this page.
   Signed out: shows the missions with a sign-up prompt. */
(function () {
  var SUPA = 'https://cfzpayanhvvqtkuqfgof.supabase.co', KEY = 'sb_publishable_ZR1zggWL9FxxwfwoIASwSg_YDV3Nvfe';
  var TK = 'sb-cfzpayanhvvqtkuqfgof-auth-token';
  var css = document.createElement('style');
  css.textContent =
    '.mhero,.mcard{border:1px solid var(--line);border-radius:14px;background:var(--panel);padding:16px 18px;margin:0 0 16px}' +
    '.mhero .mrk{display:flex;align-items:center;gap:14px;flex-wrap:wrap}.mhero .mrk b{font:800 28px "Baloo 2",sans-serif;color:#F2C14E;line-height:1}' +
    '.mhero .mrk span{font-size:15px}.mhero .mbar{margin:12px 0 6px;max-width:520px}' +
    '.mlist{display:grid;gap:0}.mtop{display:flex;justify-content:space-between;align-items:flex-start;gap:12px}.mtop h2{margin:0 0 6px;font-size:20px}' +
    '.mxp{flex:none;font:800 15px "Baloo 2",sans-serif;color:#1B1622;background:#F2C14E;border-radius:999px;padding:3px 11px}' +
    '.mprog{display:flex;align-items:center;gap:12px;margin:10px 0 12px}' +
    '.mbar{display:block;flex:1;max-width:360px;height:10px;border-radius:99px;background:rgba(255,255,255,.1);overflow:hidden}.mbar i{display:block;height:100%;background:#F2C14E;transition:width .4s}' +
    '.mch .mok{display:none;font-style:normal;color:#6FB27A;font-weight:700}.mch.done{border-color:#6FB27A}.mch.done .mok{display:inline}' +
    '.mranks ol{list-style:none;margin:8px 0 0;padding:0;display:grid;gap:6px}.mranks li{display:flex;justify-content:space-between;padding:8px 12px;border-radius:10px;border:1px solid var(--line)}' +
    '.mcard button.primary{background:var(--acc);border-color:var(--acc);color:var(--bg);font:600 15px Inter,system-ui,sans-serif;cursor:pointer}' +
    '.minv .mlink{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:4px 0 10px}.minv input{flex:1;min-width:220px;font:500 14px Inter,system-ui,sans-serif;padding:9px 12px;border-radius:10px;border:1px solid var(--line);background:var(--bg);color:inherit}' +
    '.minv button{padding:9px 14px;border-radius:10px;border:1px solid var(--line);background:var(--panel);color:inherit;font:600 14px Inter,system-ui,sans-serif;cursor:pointer}.minv button.primary{background:var(--acc);border-color:var(--acc);color:var(--bg)}' +
    '#m-cards.done{border-color:#6FB27A}.mranks li.cur{border-color:#F2C14E;background:rgba(242,193,78,.08)}.mranks li.got b::after{content:" ✓";color:#6FB27A}';
  document.head.appendChild(css);

  function $(q) { return document.querySelector(q); }
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function session() { var s = null; try { s = JSON.parse(localStorage.getItem(TK) || 'null'); } catch (_) {} if (s && s.currentSession) s = s.currentSession; return s && s.access_token && s.user && (!s.expires_at || s.expires_at * 1000 > Date.now()) ? s : null; }
  function rpc(name, tok) {
    return fetch(SUPA + '/rest/v1/rpc/' + name, { method: 'POST', headers: { apikey: KEY, Authorization: 'Bearer ' + (tok || KEY), 'Content-Type': 'application/json' }, body: '{}' })
      .then(function (r) { if (!r.ok) throw r.status; return r.json(); });
  }
  var total = document.querySelectorAll('.mch').length;

  function paint(rules, ranks, me) {
    document.querySelectorAll('[data-xp]').forEach(function (el) {
      var n = rules[el.getAttribute('data-xp')];
      if (n != null) el.textContent = '+' + n + (n===1?' scroll':' scrolls') + ({ vote_character: ' each', invite_signup: ' per friend', cards_100: ' once' }[el.getAttribute('data-xp')] || ' per note');
    });
    var xp = me ? me.xp || 0 : 0;
    $('#mladder').innerHTML = ranks.map(function (r, i) {
      var next = ranks[i + 1], cur = me && xp >= r.at && (!next || xp < next.at);
      return '<li class="' + (cur ? 'cur ' : '') + (me && xp >= r.at ? 'got' : '') + '"><b>' + esc(r.rank) + '</b><span>' + (r.at ? r.at + (r.at===1?' scroll':' scrolls') : 'Start') + '</span></li>';
    }).join('');
    var hero = $('#mhero');
    if (!me) {
      hero.innerHTML = '<div class="mrk"><b>Start your ninja path</b></div><p class="mt" style="margin:8px 0 12px">Make a free account to earn scrolls and show your rank on your profile.</p>' +
        '<p class="btns"><a class="primary" href="/#signup">Sign up free</a><a class="ghostbtn" href="/#signin">Sign in</a></p>';
      return;
    }
    var lo = me.prev_at || 0, hi = me.next_at, pct = hi ? Math.min(100, Math.round((xp - lo) / (hi - lo) * 100)) : 100;
    hero.innerHTML = '<div class="mrk"><b>' + esc(me.rank) + '</b><span>📜 ' + xp + (xp===1?' scroll':' scrolls') + '</span></div>' +
      '<span class="mbar"><i style="width:' + pct + '%"></i></span>' +
      '<p class="mt" style="margin:0">' + (me.next ? (hi - xp) + ((hi - xp)===1?' scroll':' scrolls') + ' to ' + esc(me.next) : 'Top rank. You made Kage.') + '</p>';
    var voted = me.voted || [], set = {};
    voted.forEach(function (c) { set[c] = 1; });
    var done = 0;
    document.querySelectorAll('.mch').forEach(function (a) { if (set[a.getAttribute('data-ch')]) { a.classList.add('done'); done++; } });
    // characters still to vote on come first
    var box = $('.mchips'), list = Array.prototype.slice.call(box.children);
    list.filter(function (a) { return !a.classList.contains('done'); }).concat(list.filter(function (a) { return a.classList.contains('done'); })).forEach(function (a) { box.appendChild(a); });
    $('#m-vote .mbar i').style.width = (total ? Math.round(done / total * 100) : 0) + '%';
    $('#m-vote .mcount').textContent = done + ' / ' + total;
    var cc = Math.min(100, me.cards || 0), cb = $('#m-cards');
    if (cb) { cb.querySelector('.mbar i').style.width = cc + '%'; cb.querySelector('.mcount').textContent = me.cards_100 ? 'Done ✓' : cc + ' / 100'; if (me.cards_100) cb.classList.add('done'); }
    var n = me.feedback || 0;
    $('#m-fb .mfb').textContent = n + ' note' + (n === 1 ? '' : 's') + ' used so far';
  }

  function paintInvite(inv) {
    var box = $('#m-inv .minv'); if (!box) return;
    if (!inv || !inv.code) {
      box.innerHTML = '<p class="btns" style="margin:0"><a class="primary" href="/#signup">Sign up free</a><a class="ghostbtn" href="/#signin">Sign in</a></p>';
      return;
    }
    var url = 'https://jonin.cards/?invite=' + inv.code, wait = (inv.joined || 0) - (inv.counted || 0);
    box.innerHTML = '<div class="mlink"><input readonly value="' + esc(url) + '" aria-label="Your invite link"><button type="button" class="primary" data-copy>Copy link</button>' +
      (navigator.share ? '<button type="button" data-share>Share</button>' : '') + '</div>' +
      '<div class="mprog"><b>' + (inv.counted || 0) + (inv.counted === 1 ? ' friend' : ' friends') + ' joined</b>' +
      (wait > 0 ? '<span class="mt">' + wait + ' more signed up and will count once they add a card or vote</span>' : '') + '</div>';
    box.querySelector('[data-copy]').onclick = function () {
      var b = this, inp = box.querySelector('input');
      (navigator.clipboard ? navigator.clipboard.writeText(url) : Promise.reject()).catch(function () { inp.select(); document.execCommand('copy'); })
        .then(function () { b.textContent = 'Copied ✓'; setTimeout(function () { b.textContent = 'Copy link'; }, 1800); });
    };
    var sh = box.querySelector('[data-share]');
    if (sh) sh.onclick = function () { navigator.share({ title: 'Jonin', text: 'Track your Naruto CCG collection on Jonin', url: url }).catch(function () {}); };
  }

  function load() {
    var s = session();
    Promise.all([
      rpc('xp_rules').catch(function () { return {}; }),
      rpc('xp_ranks').catch(function () { return []; }),
      s ? rpc('my_xp', s.access_token).catch(function () { return null; }) : Promise.resolve(null)
      , s ? rpc('my_invite', s.access_token).catch(function () { return null; }) : Promise.resolve(null)
    ]).then(function (r) { paint(r[0] || {}, r[1] || [], r[2]); paintInvite(r[3]); });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', load); else load();
  window.addEventListener('storage', function (e) { if (e.key === TK) load(); });
})();
