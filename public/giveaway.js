/* jonin.cards /giveaway/ page.
   Reads the newest giveaway from Supabase (giveaways table: prize, dates, entry amounts) and, for a signed-in member,
   checks their bonus entries with my_giveaway_status: a linked Instagram handle plus at least one card vote.
   Members can add their Instagram handle right here. */
(function () {
  var SUPA = 'https://cfzpayanhvvqtkuqfgof.supabase.co', KEY = 'sb_publishable_ZR1zggWL9FxxwfwoIASwSg_YDV3Nvfe';
  var TK = 'sb-cfzpayanhvvqtkuqfgof-auth-token';
  var css = document.createElement('style');
  css.textContent =
    '.mcard{border:1px solid var(--line);border-radius:14px;background:var(--panel);padding:16px 18px;margin:0 0 16px}' +
    '.mtop{display:flex;justify-content:space-between;align-items:flex-start;gap:12px}.mtop h2{margin:0 0 6px;font-size:20px}' +
    '.mxp{flex:none;font:800 15px "Baloo 2",sans-serif;color:#1B1622;background:#F2C14E;border-radius:999px;padding:3px 11px}' +
    '.ghero{display:flex;gap:18px;align-items:center;flex-wrap:wrap;border-color:#F2C14E}.ghero img{width:120px;height:auto;border-radius:10px}' +
    '.ghero b.gp{display:block;font:800 24px "Baloo 2",sans-serif;line-height:1.15}.ghero .gt{color:#F2C14E;font-weight:600;margin-top:4px}' +
    '.gsteps{margin:4px 0 12px;padding-left:20px;line-height:1.7}.grules ul{padding-left:20px;line-height:1.6}' +
    '.gchk ul{list-style:none;margin:6px 0 10px;padding:0;display:grid;gap:8px}.gchk li{display:flex;gap:10px;align-items:center;flex-wrap:wrap}' +
    '.gchk li i{font-style:normal;width:22px;text-align:center}.gchk li.ok i{color:#6FB27A}.gchk li.no i{color:var(--mute)}' +
    '.gchk input{font:500 14px Inter,system-ui,sans-serif;padding:8px 11px;border-radius:10px;border:1px solid var(--line);background:var(--bg);color:inherit;min-width:180px}' +
    '.gchk button,.gchk .sm{padding:8px 13px;border-radius:10px;border:1px solid var(--acc);background:var(--acc);color:var(--bg);font:600 14px Inter,system-ui,sans-serif;cursor:pointer;text-decoration:none}' +
    '.gchk .done{margin:10px 0 0;padding:10px 12px;border-radius:10px;background:rgba(111,178,122,.12);border:1px solid #6FB27A}.gchk .gmsg{font-size:13px;color:var(--mute)}';
  document.head.appendChild(css);

  function $(q) { return document.querySelector(q); }
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function session() { var s = null; try { s = JSON.parse(localStorage.getItem(TK) || 'null'); } catch (_) {} if (s && s.currentSession) s = s.currentSession; return s && s.access_token && s.user && (!s.expires_at || s.expires_at * 1000 > Date.now()) ? s : null; }
  function api(path, opt, tok) {
    opt = opt || {};
    opt.headers = Object.assign({ apikey: KEY, Authorization: 'Bearer ' + (tok || KEY), 'Content-Type': 'application/json' }, opt.headers || {});
    return fetch(SUPA + path, opt).then(function (r) { if (!r.ok) throw r.status; return r.status === 204 ? null : r.json(); });
  }
  function day(d) { return new Date(d).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' }); }
  function cleanIg(v) { return String(v || '').trim().replace(/^https?:\/\/(www\.)?instagram\.com\//i, '').replace(/^@+/, '').replace(/[/?#\s].*$/, '').toLowerCase(); }

  var G = null, S = session();

  function paintGiveaway() {
    document.querySelectorAll('[data-g]').forEach(function (el) { var v = G[el.getAttribute('data-g')]; if (v != null) el.textContent = v; });
    var now = Date.now(), st = G.starts_at && new Date(G.starts_at), en = G.ends_at && new Date(G.ends_at), when;
    if (G.winner_ig) when = '🎉 Winner: @' + esc(G.winner_ig) + '. Congrats, and thanks to everyone who entered!';
    else if (!st || now < st) when = st ? 'Starts ' + day(st) + '. Get your bonus entries ready now.' : 'Starting soon. Get your bonus entries ready now.';
    else if (en && now > en) when = 'Entries are closed. The winner will be drawn live on our Instagram stories.';
    else if (en) { var d = Math.max(1, Math.ceil((en - now) / 864e5)); when = 'Ends ' + day(en) + ' · ' + d + (d === 1 ? ' day' : ' days') + ' left'; }
    else when = 'Open now.';
    if (st && en) $('#grun').textContent = 'from ' + day(st) + ' to ' + day(en);
    $('#gwhen').textContent = 'Free to enter. ' + G.eligibility + '.';
    $('#gprize').innerHTML = (G.prize_img ? '<img src="' + esc(G.prize_img) + '" alt="">' : '') +
      '<div><b class="gp">' + esc(G.prize) + '</b><div class="gt">' + when + '</div></div>';
  }

  function paintCheck(st) {
    var box = $('#gchk');
    if (!S || !st || !st.signed_in) {
      box.innerHTML = '<p class="btns"><a class="primary" href="/#signup">Sign up free</a><a class="ghostbtn" href="/#signin">Sign in</a></p>' +
        '<p class="gmsg">Already have an account? Sign in, then come back to this page to check your bonus.</p>';
      return;
    }
    var ig = st.instagram, voted = st.voted, bonus = st.bonus || G.bonus_entries;
    box.innerHTML = '<ul>' +
      '<li class="ok"><i>✓</i>Free jonin.cards account</li>' +
      '<li class="' + (ig ? 'ok' : 'no') + '"><i>' + (ig ? '✓' : '○') + '</i>' +
        (ig ? 'Instagram: <b>@' + esc(ig) + '</b> <a href="#" id="gigedit">change</a>' : 'Add your Instagram handle') +
        '<span id="gigform"' + (ig ? ' hidden' : '') + '><input id="gig" placeholder="@yourhandle" autocomplete="off" value="' + esc(ig || '') + '"> <button type="button" id="gigsave">Save</button></span></li>' +
      '<li class="' + (voted ? 'ok' : 'no') + '"><i>' + (voted ? '✓' : '○') + '</i>' +
        (voted ? 'Voted for a card' : 'Vote for your favorite card on any character <a class="sm" href="/characters/">Pick a character</a>') + '</li>' +
      '</ul><p class="gmsg" id="gigmsg"></p>' +
      (ig && voted ? '<p class="done">You have <b>+' + bonus + ' bonus entries</b> as @' + esc(ig) + '. Make sure you enter on the Instagram post with this same account.</p>' : '');
    var ed = $('#gigedit');
    if (ed) ed.onclick = function (e) { e.preventDefault(); $('#gigform').hidden = false; $('#gig').focus(); };
    $('#gigsave').onclick = function () {
      var h = cleanIg($('#gig').value), m = $('#gigmsg');
      if (!/^[a-z0-9._]{1,30}$/.test(h)) { m.textContent = 'That doesn\'t look like an Instagram handle.'; return; }
      m.textContent = 'Saving…';
      api('/rest/v1/profiles?id=eq.' + encodeURIComponent(S.user.id), { method: 'PATCH', headers: { Prefer: 'return=minimal' }, body: JSON.stringify({ instagram: h }) }, S.access_token)
        .then(load).catch(function () { m.textContent = 'Could not save. Try again.'; });
    };
  }

  function load() {
    if (!S) return paintCheck(null);
    return api('/rest/v1/rpc/my_giveaway_status', { method: 'POST', body: JSON.stringify({ p_slug: G.slug }) }, S.access_token)
      .then(paintCheck).catch(function () { paintCheck(null); });
  }

  api('/rest/v1/giveaways?select=*&order=created_at.desc&limit=1').then(function (rows) {
    G = rows && rows[0];
    if (!G) { $('#gprize').innerHTML = '<p class="mt">No giveaway running right now. Follow <a href="https://www.instagram.com/jonin.cards/">@jonin.cards</a> to hear about the next one.</p>'; $('#gbonus').hidden = true; return; }
    paintGiveaway(); load();
  }).catch(function () { $('#gprize').innerHTML = '<p class="mt">Couldn\'t load the giveaway. Refresh to try again.</p>'; });
})();
