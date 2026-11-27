/* Sealed collection box on /sealed/<item>/ pages (2026-11-27): members mark a sealed item as one they have (with a
   count) or want. Saved in collection_sealed (private to each member, like card haves). Each pack art, blister and deck
   is its own item, so collectors can track every art separately. Guests see a sign-up prompt.
   PLACEHOLDER for David: no edition picker yet (saved as edition ''), and sealed isn't in My collection or its value yet. */
(function () {
  var SUPA = 'https://cfzpayanhvvqtkuqfgof.supabase.co', KEY = 'sb_publishable_ZR1zggWL9FxxwfwoIASwSg_YDV3Nvfe';
  var box = document.getElementById('scoll');
  if (!box) return;
  var PID = box.dataset.product, sb, me, have = 0, want = false, busy = false;

  function guest() {
    box.innerHTML = '<h4>Your sealed collection</h4><p class="mt">Track the sealed packs, boxes and decks you have and want, each art on its own. ' +
      '<a href="/#signup" data-jt="signup-click" data-jt-from="sealed-page">Sign up free</a> or <a href="/#signin">sign in</a>.</p>';
  }
  function paint() {
    box.innerHTML = '<h4>Your sealed collection</h4><div class="scrow">' +
      '<span class="sclbl">Have</span><button type="button" class="scb" data-d="-1" aria-label="One less"' + (have ? '' : ' disabled') + '>−</button>' +
      '<b class="scn" aria-live="polite">' + have + '</b><button type="button" class="scb" data-d="1" aria-label="One more">+</button>' +
      '<button type="button" class="scw' + (want ? ' on' : '') + '" aria-pressed="' + want + '">' + (want ? '★ Wanted' : '☆ Want') + '</button></div>' +
      '<p class="mt scmsg"></p>';
  }
  function msg(t) { var m = box.querySelector('.scmsg'); if (m) m.textContent = t; }
  function save(kind, qty) {
    var q = qty > 0
      ? sb.from('collection_sealed').upsert({ user_id: me, product_id: PID, kind: kind, qty: qty, edition: '', updated_at: new Date().toISOString() })
      : sb.from('collection_sealed').delete().match({ user_id: me, product_id: PID, kind: kind, edition: '' });
    return q.then(function (r) { if (r.error) throw r.error; });
  }
  box.addEventListener('click', function (e) {
    var b = e.target.closest('button'); if (!b || !me || busy) return;
    var before = [have, want];
    if (b.dataset.d) have = Math.max(0, Math.min(999, have + +b.dataset.d));
    else if (b.classList.contains('scw')) want = !want;
    else return;
    busy = true; paint();
    (b.dataset.d ? save('have', have) : save('want', want ? 1 : 0))
      .then(function () { msg(b.dataset.d ? (have ? 'Saved: you have ' + have + '.' : 'Removed from your sealed.') : (want ? 'Added to your wants.' : 'Removed from your wants.')); })
      .catch(function () { have = before[0]; want = before[1]; paint(); msg("Couldn't save. Try again."); })
      .then(function () { busy = false; });
  });
  function start() {
    sb = window.supabase.createClient(SUPA, KEY);
    sb.auth.getSession().then(function (r) {
      var s = r.data.session; if (!s) return guest();
      me = s.user.id;
      sb.from('collection_sealed').select('kind,qty').eq('product_id', PID).then(function (q) {
        (q.data || []).forEach(function (x) { if (x.kind === 'have') have += x.qty; if (x.kind === 'want' && x.qty > 0) want = true; });
        paint();
      });
    });
  }
  var hasSession = false;
  try { for (var i = 0; i < localStorage.length; i++) { if (/^sb-.*-auth-token$/.test(localStorage.key(i))) hasSession = true; } } catch (_) {}
  if (!hasSession) return guest();
  if (window.supabase) start();
  else { var s = document.createElement('script'); s.src = 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.119.2/dist/umd/supabase.min.js'; s.onload = start; document.head.appendChild(s); }
})();
