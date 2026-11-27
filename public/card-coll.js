/* Card page "Your collection" panel + quick navigation (2026-11-26).
   Clicking a card anywhere on the site now opens its card page (the homepage popup is gone), so the collection editor
   lives here. It is the homepage's own editor, embedded (/?embed=coll&card=ID): haves/wants, conditions, slabs with PSA
   cert lookup, lists, scrolls and the sign-up/sell prompts all work exactly as before, from one copy of the code.
   It loads right away for anyone with a collection or an account; first-time visitors (most Google traffic) see a light
   "Add to your collection" button and only load it when they tap. Also: ‹ › arrow keys flip cards, and the feedback
   widget knows which card you're on. */
(function(){
  var box=document.getElementById('coll');
  var id=box&&box.getAttribute('data-card'),name=box&&box.getAttribute('data-name');
  if(id)window.joninFbCard=function(){return {id:id,name:name}};
  function has(k){try{var v=JSON.parse(localStorage.getItem(k)||'null');return !!v}catch(_){return false}}
  function guest(){try{var g=JSON.parse(localStorage.getItem('jonin_guest_v1')||'null');return !!(g&&((g.items&&g.items.length)||(g.slabs&&g.slabs.length)))}catch(_){return false}}
  function load(){if(!box||box.querySelector('iframe'))return;
    var f=document.createElement('iframe');f.title='Your collection';f.setAttribute('scrolling','no');
    f.src='/?embed=coll&card='+encodeURIComponent(id);
    box.classList.add('on');box.innerHTML='<p class="mt cload">Loading your collection…</p>';box.appendChild(f);
    f.addEventListener('load',function(){var l=box.querySelector('.cload');if(l)l.remove()});
  }
  if(box){
    if(has('sb-cfzpayanhvvqtkuqfgof-auth-token')||guest())load();
    box.addEventListener('click',function(e){if(e.target.closest('[data-collgo]'))load()});
  }
  // ← → flip to the previous / next card (not while typing).
  document.addEventListener('keydown',function(e){
    if(e.metaKey||e.ctrlKey||e.altKey||e.shiftKey)return;
    var t=e.target;if(t&&(t.isContentEditable||/^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName)))return;
    var k=e.key==='ArrowLeft'?'prev':e.key==='ArrowRight'?'next':'';if(!k)return;
    var a=document.querySelector('.cnav a[data-key="'+k+'"]');if(a){e.preventDefault();location.href=a.href}
  });
})();
