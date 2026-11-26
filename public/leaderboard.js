/* jonin.cards /leaderboard/: members ranked by scrolls. Reads scroll_leaderboard() from Supabase
   (db/029_scroll_leaderboard.sql). Only members who turned on sharing appear (David, 2026-11-26). Shows name, picture, status, rank and scrolls only.
   PLACEHOLDERS (set in Supabase): top 25, members with 1+ scroll, ties share a place. Signed-in members outside the
   top 25 get their own row pinned underneath. */
(function () {
  var SUPA = 'https://cfzpayanhvvqtkuqfgof.supabase.co', KEY = 'sb_publishable_ZR1zggWL9FxxwfwoIASwSg_YDV3Nvfe';
  var TK = 'sb-cfzpayanhvvqtkuqfgof-auth-token', LIMIT = 25;
  var THEMEF = ['naruto', 'sasuke', 'itachi', 'kakashi', 'gaara', 'hinata', 'sakura', 'rock-lee'];
  var css = document.createElement('style');
  css.textContent =
    '.lbx{border:1px solid var(--line);border-radius:14px;background:var(--panel);padding:8px;margin:0 0 16px}' +
    '.lbx ol{list-style:none;margin:0;padding:0;display:grid;gap:6px}' +
    '.lbr{display:grid;grid-template-columns:44px 44px 1fr auto;align-items:center;gap:12px;padding:10px 12px;border-radius:10px;border:1px solid transparent}' +
    '.lbr:nth-child(odd){background:rgba(255,255,255,.03)}.lbr.me{border-color:#F2C14E;background:rgba(242,193,78,.08)}' +
    '.lbp{font:800 22px "Baloo 2",sans-serif;text-align:center;opacity:.8}.lbr.p1 .lbp{color:#F2C14E;opacity:1}.lbr.p2 .lbp{color:#C9CED6;opacity:1}.lbr.p3 .lbp{color:#C98A4B;opacity:1}' +
    '.lba{width:44px;height:44px;border-radius:50%;overflow:hidden;display:flex;align-items:center;justify-content:center;background:rgba(255,255,255,.08);font:800 18px "Baloo 2",sans-serif}' +
    '.lba img{width:100%;height:100%;object-fit:cover}.lba.founding{box-shadow:0 0 0 3px #F2C14E}.lba.premium{box-shadow:0 0 0 3px #E2553B}' +
    '.lbn{min-width:0}.lbn b{display:block;font-size:16px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.lbn a{color:inherit;text-decoration:none}.lbn a:hover{text-decoration:underline}' +
    '.lbn span{font-size:13px;opacity:.75}.lbs{font:800 18px "Baloo 2",sans-serif;color:#F2C14E;white-space:nowrap}' +
    '.lbgap{text-align:center;opacity:.5;padding:2px 0;letter-spacing:4px}.lbe{padding:18px;text-align:center}' +
    '@media(max-width:520px){.lbr{grid-template-columns:30px 36px 1fr auto;gap:8px;padding:8px}.lba{width:36px;height:36px}.lbp{font-size:18px}}';
  document.head.appendChild(css);

  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function session() { var s = null; try { s = JSON.parse(localStorage.getItem(TK) || 'null'); } catch (_) {} if (s && s.currentSession) s = s.currentSession; return s && s.access_token && s.user && (!s.expires_at || s.expires_at * 1000 > Date.now()) ? s : null; }
  function avSrc(sl, a) { if (!sl) return ''; if (a === 'portrait' && THEMEF.indexOf(sl) > -1) return '/theme-faces/' + sl + '.webp'; if (a === 'action') return '/char-art/' + sl + '.webp'; return '/chars/' + sl + '.webp'; }
  function sc(n) { return n === 1 ? ' scroll' : ' scrolls'; }
  var LABEL = { founding: 'Founding member', premium: 'Jonin Club member' };

  function row(r) {
    var src = avSrc(r.fav, r.avatar), name = esc(r.handle || 'Member');
    var pic = src ? '<img src="' + esc(src) + '" alt="" width="44" height="44" loading="lazy">' : esc((r.handle || '?').charAt(0).toUpperCase());
    var who = r.slug ? '<a href="/#u=' + encodeURIComponent(r.slug) + '">' + name + '</a>' : name;
    return '<li class="lbr p' + r.pos + (r.me ? ' me' : '') + '"><span class="lbp">' + r.pos + '</span>' +
      '<span class="lba ' + (r.badge || '') + '"' + (r.badge ? ' title="' + LABEL[r.badge] + '"' : '') + '>' + pic + '</span>' +
      '<span class="lbn"><b>' + who + (r.me ? ' (you)' : '') + '</b><span>' + esc(r.rank) + (r.badge ? ' · ' + LABEL[r.badge] : '') + '</span></span>' +
      '<span class="lbs">📜 ' + r.xp + sc(r.xp) + '</span></li>';
  }

  var box = document.getElementById('lbx'), s = session();
  fetch(SUPA + '/rest/v1/rpc/scroll_leaderboard', { method: 'POST', headers: { apikey: KEY, Authorization: 'Bearer ' + (s ? s.access_token : KEY), 'Content-Type': 'application/json' }, body: JSON.stringify({ p_limit: LIMIT }) })
    .then(function (r) { if (!r.ok) throw r.status; return r.json(); })
    .then(function (d) {
      var rows = d.rows || [];
      if (!rows.length) box.innerHTML = '<p class="lbe mt">No one is on the board yet. <a href="/missions/">Be the first</a>.</p>';
      else {
      var html = rows.map(row).join('');
      if (d.me && !d.me.shown) html += '<li class="lbgap" aria-hidden="true">· · ·</li>' + row(d.me);
      box.innerHTML = '<ol>' + html + '</ol>';
      }
      var foot = document.getElementById('lbfoot');
      if (foot) foot.innerHTML = !s ? '<a href="/#signup">Sign up free</a> and do <a href="/missions/">missions</a> to earn scrolls and get on the board.'
        : d.me_hidden ? 'Only members who share their profile show here. Turn on sharing on <a href="/#collection">My collection</a> to join the board.'
        : !d.me ? 'You’re not on the board yet. <a href="/missions/">Earn your first scrolls</a>.'
        : 'You’re #' + d.me.pos + ' of ' + d.total + '. <a href="/missions/">Earn more scrolls</a>.';
    })
    .catch(function () { box.innerHTML = '<p class="lbe mt">The leaderboard couldn’t load. Try again in a minute.</p>'; });
})();
