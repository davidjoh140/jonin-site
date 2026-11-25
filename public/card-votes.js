/* Jonin card page vote count — loaded on /card/<slug>/ pages for character cards.
   Shows how many people voted this card as one of the coolest cards on each of its character pages,
   and its place in that character's Top 3 once the Top 3 is showing (MIN_VOTERS, same as vote.js). */
(function () {
  var SUPA = 'https://cfzpayanhvvqtkuqfgof.supabase.co', KEY = 'sb_publishable_ZR1zggWL9FxxwfwoIASwSg_YDV3Nvfe';
  var MIN_VOTERS = 5; // PLACEHOLDER: keep in step with vote.js
  var el = document.querySelector('.cvotes');
  if (!el) return;
  var esc = function (v) { return String(v == null ? '' : v).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); };
  var chars = (el.dataset.chars || '').split(',').filter(Boolean).map(function (x) { var i = x.indexOf(':'); return { slug: x.slice(0, i), label: x.slice(i + 1) }; });
  function draw(rows) {
    var by = {}; (rows || []).forEach(function (r) { by[r.character] = r; });
    el.innerHTML = chars.map(function (ch) {
      var r = by[ch.slug], n = r ? r.votes : 0;
      var top = r && r.voters >= MIN_VOTERS && r.rank <= 3 ? ' · <b class="cvrank">#' + r.rank + ' coolest ' + esc(ch.label) + ' card</b>' : '';
      var what = chars.length > 1 ? ' as a ' + esc(ch.label) + ' card' : '';
      return '<span class="cvline">▲ ' + n + ' vote' + (n === 1 ? '' : 's') + what + top +
        ' · <a href="/character/' + esc(ch.slug) + '/#vote-top">Vote on ' + esc(ch.label) + '’s page</a></span>';
    }).join('');
  }
  fetch(SUPA + '/rest/v1/rpc/card_vote_summary', {
    method: 'POST', headers: { apikey: KEY, 'Content-Type': 'application/json' },
    body: JSON.stringify({ p_card_id: el.dataset.card })
  }).then(function (r) { return r.ok ? r.json() : []; }).then(draw).catch(function () { draw([]); });
})();
