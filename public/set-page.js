/* Jonin set pages (/set/<id>/): search, filter and sort the set's cards, right on the page.
   Filters: search (name or number), rarity and card type chips (several = any of them), element, village, has foils.
   The breakdown rows (Rarity, Card type, Element, Village) set the same filters.
   Filtered-out cards get .fout (not [hidden]) so set-progress.js's "missing only" toggle keeps working alongside.
   State lives in the URL hash (#q=..&r=SR,R&el=Fire&sort=px) so a filtered view can be shared. */
(function () {
  var grid = document.getElementById('setgrid');
  if (!grid) return;
  var tiles = [].slice.call(grid.querySelectorAll('.tile'));
  tiles.forEach(function (t, i) { t._i = i; });
  var $ = function (id) { return document.getElementById(id); };
  var q = $('sq'), sel = { el: $('sel-el'), vil: $('sel-vil') }, sortSel = $('sel-sort');
  var S = { q: '', r: [], t: [], el: '', vil: '', foil: '', sort: 'num' };
  var RORD = { UR: 6, ALT: 5.5, SR: 5, R: 4, U: 3, C: 2, P: 1, F: 0, '': -1 };
  var EL = ['Fire', 'Water', 'Wind', 'Lightning', 'Earth', 'Void'];

  function num(v) { return v === '' || v == null ? null : +v; }
  function cmpNull(a, b, dir) { if (a == null && b == null) return 0; if (a == null) return 1; if (b == null) return -1; return dir * (a - b); }
  var SORTS = {
    num: function (a, b) { return a._i - b._i; },
    name: function (a, b) { return a.dataset.name.localeCompare(b.dataset.name) || a._i - b._i; },
    'rar-d': function (a, b) { return (RORD[b.dataset.r] || 0) - (RORD[a.dataset.r] || 0) || a._i - b._i; },
    rar: function (a, b) { return (RORD[a.dataset.r] || 0) - (RORD[b.dataset.r] || 0) || a._i - b._i; },
    px: function (a, b) { return cmpNull(num(a.dataset.px), num(b.dataset.px), -1) || a._i - b._i; },
    'px-a': function (a, b) { return cmpNull(num(a.dataset.px), num(b.dataset.px), 1) || a._i - b._i; },
    tc: function (a, b) { return cmpNull(num(a.dataset.tc), num(b.dataset.tc), 1) || a._i - b._i; },
    'tc-d': function (a, b) { return cmpNull(num(a.dataset.tc), num(b.dataset.tc), -1) || a._i - b._i; },
    el: function (a, b) { var x = EL.indexOf(a.dataset.el), y = EL.indexOf(b.dataset.el); return cmpNull(x < 0 ? null : x, y < 0 ? null : y, 1) || a._i - b._i; },
    vil: function (a, b) { var x = a.dataset.vil, y = b.dataset.vil; if (!x !== !y) return x ? -1 : 1; return x.localeCompare(y) || a._i - b._i; }
  };

  function readHash() {
    var h = new URLSearchParams(location.hash.slice(1));
    S.q = h.get('q') || ''; S.el = h.get('el') || ''; S.vil = h.get('vil') || ''; S.foil = h.get('foil') || '';
    S.r = (h.get('r') || '').split(',').filter(Boolean); S.t = (h.get('t') || '').split(',').filter(Boolean);
    S.sort = SORTS[h.get('sort')] ? h.get('sort') : 'num';
  }
  function writeHash() {
    var h = new URLSearchParams();
    if (S.q) h.set('q', S.q); if (S.r.length) h.set('r', S.r.join(',')); if (S.t.length) h.set('t', S.t.join(','));
    if (S.el) h.set('el', S.el); if (S.vil) h.set('vil', S.vil); if (S.foil) h.set('foil', S.foil);
    if (S.sort !== 'num') h.set('sort', S.sort);
    var s = h.toString();
    history.replaceState(null, '', s ? '#' + s : location.pathname + location.search);
  }
  function active() { return !!(S.q || S.r.length || S.t.length || S.el || S.vil || S.foil); }

  function apply(save) {
    var words = S.q.toLowerCase().trim().split(/\s+/).filter(Boolean), shown = 0;
    tiles.forEach(function (t) {
      var d = t.dataset, ok = words.every(function (w) { return d.name.indexOf(w) >= 0 || d.n.toLowerCase().indexOf(w) >= 0; }) &&
        (!S.r.length || S.r.indexOf(d.r) >= 0) && (!S.t.length || S.t.indexOf(d.t) >= 0) &&
        (!S.el || d.el === S.el) && (!S.vil || d.vil === S.vil) && (!S.foil || d.foil === '1');
      t.classList.toggle('fout', !ok);
      if (ok) shown++;
    });
    tiles.slice().sort(SORTS[S.sort]).forEach(function (t) { grid.appendChild(t); });
    $('scount').textContent = active() ? shown + ' of ' + tiles.length + ' cards' : tiles.length + ' cards';
    $('sclear').hidden = !active();
    $('snone').hidden = shown > 0;
    paint();
    if (save) writeHash();
  }
  function on(f, v) { return f === 'r' || f === 't' ? S[f].indexOf(v) >= 0 : S[f] === v; }
  function paint() {
    if (q && document.activeElement !== q) q.value = S.q;
    if (sel.el) sel.el.value = S.el; if (sel.vil) sel.vil.value = S.vil;
    if (sortSel) sortSel.value = S.sort;
    [].forEach.call(document.querySelectorAll('[data-f][data-v]'), function (b) {
      var x = on(b.dataset.f, b.dataset.v); b.setAttribute('aria-pressed', x); b.classList.toggle('on', x);
    });
  }
  function toggle(f, v) {
    if (f === 'r' || f === 't') { var i = S[f].indexOf(v); if (i >= 0) S[f].splice(i, 1); else S[f].push(v); }
    else S[f] = S[f] === v ? '' : v;
  }

  document.addEventListener('click', function (ev) {
    var b = ev.target.closest('[data-f][data-v]');
    if (b) {
      toggle(b.dataset.f, b.dataset.v); apply(true);
      if (b.classList.contains('bdrow')) document.getElementById('cards').scrollIntoView({ behavior: 'smooth', block: 'start' });
      return;
    }
    if (ev.target.closest('#sclear,[data-clear]')) { S.q = ''; S.r = []; S.t = []; S.el = ''; S.vil = ''; S.foil = ''; apply(true); return; }
    var j = ev.target.closest('[data-sortjump]');
    if (j) { ev.preventDefault(); S.sort = j.dataset.sortjump; apply(true); document.getElementById('cards').scrollIntoView({ behavior: 'smooth', block: 'start' }); }
  });
  var tm;
  if (q) q.addEventListener('input', function () { clearTimeout(tm); tm = setTimeout(function () { S.q = q.value; apply(true); }, 120); });
  ['el', 'vil'].forEach(function (k) { if (sel[k]) sel[k].addEventListener('change', function () { S[k] = sel[k].value; apply(true); }); });
  if (sortSel) sortSel.addEventListener('change', function () { S.sort = sortSel.value; apply(true); });
  // Only read the hash if it looks like filters (not a jump link like #sealed).
  if (/[=]/.test(location.hash)) readHash();
  apply(false);
})();
