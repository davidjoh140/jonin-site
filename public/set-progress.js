/* Jonin set completion — loaded on /set/<id>/ pages.
   Shows how many cards of this set you have (owned/total + progress bar), ticks the cards you have,
   and lets you show only the ones you're missing.
   Rules (confirmed by David): a card counts as owned if you have ANY printing or edition of it.
   The master set is different: every printing x edition of every card (e.g. Kunai Normal 1st Edition,
   Kunai Diamond foil Unlimited, ...), shown as a second count. */
(function () {
  var SUPA = 'https://cfzpayanhvvqtkuqfgof.supabase.co', KEY = 'sb_publishable_ZR1zggWL9FxxwfwoIASwSg_YDV3Nvfe';
  var box = document.getElementById('set-progress');
  if (!box) return;
  var SET = box.dataset.set, TOTAL = +box.dataset.total, PRINTS = +box.dataset.prints || 0;
  var tiles = Array.prototype.slice.call(document.querySelectorAll('.grid .tile[data-card]'));
  var missingOnly = false;

  function guestHaves() {
    var out = new Set(); out.prints = new Set();
    try {
      var g = JSON.parse(localStorage.getItem('jonin_guest_v1') || '{}');
      (g.items || []).forEach(function (it) { var a = String(it[0]).split('|'); if (a[3] === 'have' && it[1] > 0 && a[0].indexOf(SET + ':') === 0) { out.add(a[0]); out.prints.add(a[0] + '|' + a[1] + '|' + a[2]); } });
    } catch (_) {}
    return out;
  }

  function paint(owned, signedIn) {
    var have = tiles.filter(function (t) { return owned.has(t.dataset.card); }).length;
    var pct = TOTAL ? Math.round(have / TOTAL * 100) : 0;
    tiles.forEach(function (t) {
      var on = owned.has(t.dataset.card);
      t.classList.toggle('owned', on);
      t.hidden = missingOnly && on;
    });
    if (!have && !signedIn) {
      box.innerHTML = '<p class="spx-cta">Track your collection and see how close you are to finishing this set. ' +
        '<a href="/#mine">Start your collection</a></p>';
      return;
    }
    box.innerHTML =
      '<div class="spx-top"><b>' + have + ' / ' + TOTAL + '</b> cards' + (have === TOTAL && TOTAL ? ' · <span class="spx-done">Set complete!</span>' : ' · ' + (TOTAL - have) + ' to go') +
      '<span class="spx-pct">' + pct + '%</span></div>' +
      '<div class="spx-bar" role="progressbar" aria-valuemin="0" aria-valuemax="' + TOTAL + '" aria-valuenow="' + have + '"><i style="width:' + pct + '%"></i></div>' +
      (PRINTS ? (function () { var pn = Math.min(owned.prints ? owned.prints.size : 0, PRINTS), pp = Math.floor(pn / PRINTS * 1000) / 10;
        return '<div class="spx-master"><span>Master set: <b>' + pn + ' / ' + PRINTS + '</b> printings' + (pn === PRINTS ? ' · <span class="spx-done">Complete!</span>' : '') +
          ' <span class="spx-why" title="Every printing and edition of every card: each foil, 1st Edition and Unlimited.">ⓘ</span></span><span class="spx-pct">' + pp + '%</span></div>' +
          '<div class="spx-bar thin"><i style="width:' + pp + '%"></i></div>'; })() : '') +
      '<div class="spx-row"><button type="button" class="spx-tog" aria-pressed="' + missingOnly + '">' + (missingOnly ? 'Show all cards' : 'Show only missing') + '</button>' +
      '<a href="/#set=' + encodeURIComponent(SET) + '">Add cards you have</a></div>';
    box.querySelector('.spx-tog').onclick = function () { missingOnly = !missingOnly; paint(owned, signedIn); };
  }

  paint(guestHaves(), false);

  function start() {
    var sb = window.supabase.createClient(SUPA, KEY);
    sb.auth.getSession().then(function (r) {
      if (!r.data.session) return;
      sb.from('collection_items').select('card_id,printing,edition').eq('kind', 'have').gt('qty', 0).like('card_id', SET + ':%').limit(5000)
        .then(function (q) {
          if (q.error) return;
          var owned = new Set((q.data || []).map(function (x) { return x.card_id; }));
          owned.prints = new Set((q.data || []).map(function (x) { return x.card_id + '|' + x.printing + '|' + x.edition; }));
          paint(owned, true);
        });
    });
  }
  // Only signed-in members need the Supabase client; check for a stored session first so guests skip the download.
  var hasSession = false;
  try { for (var i = 0; i < localStorage.length; i++) { if (/^sb-.*-auth-token$/.test(localStorage.key(i))) hasSession = true; } } catch (_) {}
  if (!hasSession) return;
  if (window.supabase) start();
  else { var s = document.createElement('script'); s.src = 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.119.2/dist/umd/supabase.min.js'; s.onload = start; document.head.appendChild(s); }
})();
