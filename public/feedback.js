/* Jonin feedback widget — loaded on every page.
   Anyone can leave a note on the whole page or point at one spot (a card, a section, a button).
   Notes go into the Supabase `feedback` table (insert-only for visitors; only the owner reads them in /admin/). */
(function(){
  if(window.__joninFb)return;window.__joninFb=1;
  var SUPA='https://cfzpayanhvvqtkuqfgof.supabase.co',KEY='sb_publishable_ZR1zggWL9FxxwfwoIASwSg_YDV3Nvfe';
  var css=`
.jfb-fab{position:fixed;left:16px;bottom:16px;z-index:900;background:var(--deep,#17121D);border:1px solid var(--edge,#3A3046);color:var(--ink,#FFF4E6);border-radius:999px;padding:10px 14px;font:600 14px Inter,system-ui,sans-serif;cursor:pointer;box-shadow:0 10px 30px -10px rgba(0,0,0,.7)}
.jfb-fab:hover{border-color:var(--red,#B5121B)}
.jfb-ov{position:fixed;inset:0;z-index:1000;background:rgba(10,7,14,.82);backdrop-filter:blur(6px);-webkit-backdrop-filter:blur(6px);display:flex;align-items:center;justify-content:center;padding:16px}
.jfb-ov[hidden]{display:none}
.jfb-box{position:relative;width:min(440px,100%);max-height:100%;overflow-y:auto;background:var(--deep,#17121D);border:1px solid var(--edge2,#30283A);border-radius:18px;padding:22px;display:grid;gap:12px;color:var(--ink,#FFF4E6);font:14px/1.45 Inter,system-ui,sans-serif;box-shadow:0 30px 80px -20px rgba(0,0,0,.8)}
.jfb-box h2{margin:0;font:800 24px "Baloo 2",sans-serif}
.jfb-box p{margin:0;color:var(--mute,#B8AEA6)}
.jfb-box label{display:grid;gap:4px;font-size:13px;color:var(--mute,#B8AEA6)}
.jfb-box input,.jfb-box textarea{background:var(--panel,#241E2D);border:1px solid var(--edge,#3A3046);border-radius:10px;padding:11px 13px;color:var(--ink,#FFF4E6);font:15px/1.45 Inter,system-ui,sans-serif;outline:none;width:100%;box-sizing:border-box}
.jfb-box textarea{resize:vertical;min-height:110px}
.jfb-box input:focus,.jfb-box textarea:focus{border-color:var(--red,#B5121B)}
.jfb-kinds{display:flex;flex-wrap:wrap;gap:6px}
.jfb-kinds button,.jfb-pick,.jfb-clr{background:var(--panel,#241E2D);border:1px solid var(--edge,#3A3046);color:var(--ink,#FFF4E6);border-radius:999px;padding:7px 12px;font:13px Inter,system-ui,sans-serif;cursor:pointer}
.jfb-kinds button[aria-pressed="true"]{background:var(--red,#B5121B);border-color:var(--red,#B5121B);color:#fff}
.jfb-about{display:flex;align-items:center;gap:8px;flex-wrap:wrap;background:var(--panel,#241E2D);border-radius:10px;padding:9px 12px;font-size:13px}
.jfb-about b{font-weight:600}.jfb-about .jfb-clr{padding:3px 9px;font-size:12px;margin-left:auto}
.jfb-pick{border-style:dashed;text-align:left;border-radius:10px;padding:9px 12px}
.jfb-pick:hover{border-color:var(--acc,#F57C00)}
.jfb-two{display:grid;grid-template-columns:1fr 1fr;gap:10px}@media(max-width:480px){.jfb-two{grid-template-columns:1fr}}
.jfb-go{min-height:44px;border-radius:10px;background:var(--red,#B5121B);border:0;color:var(--ont,#fff);font:600 15px Inter,system-ui,sans-serif;cursor:pointer}
.jfb-go:disabled{opacity:.6;cursor:default}
.jfb-x{position:absolute;top:8px;right:10px;background:none;border:0;color:var(--mute,#B8AEA6);font-size:20px;cursor:pointer;padding:6px}
.jfb-msg{font-size:13px;color:var(--mute,#B8AEA6);min-height:18px}.jfb-msg.err{color:#ff8b8b}.jfb-msg.ok{color:#6CC24A}
.jfb-hp{position:absolute;left:-9999px;width:1px;height:1px;opacity:0}
.jfb-hl{position:fixed;z-index:1001;pointer-events:none;border:2px solid var(--acc,#F57C00);background:rgba(245,124,0,.12);border-radius:8px;transition:all .06s;display:none}
.jfb-tip{position:fixed;z-index:1002;left:50%;top:12px;transform:translateX(-50%);background:var(--acc,#F57C00);color:var(--bg,#1B1622);font:600 14px Inter,system-ui,sans-serif;padding:10px 14px;border-radius:999px;box-shadow:0 10px 30px -10px rgba(0,0,0,.7);display:flex;gap:10px;align-items:center;max-width:calc(100% - 24px)}
.jfb-tip button{background:var(--bg,#1B1622);color:var(--ink,#FFF4E6);border:0;border-radius:999px;padding:5px 10px;font:600 12px Inter,system-ui,sans-serif;cursor:pointer}
.jfb-picking,.jfb-picking *{cursor:crosshair!important}
.jfb-spot{outline:3px solid var(--acc,#F57C00)!important;outline-offset:3px;border-radius:6px}`;
  var st=document.createElement('style');st.textContent=css;document.head.appendChild(st);

  function esc(s){return String(s).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
  function vid(){try{var v=localStorage.getItem('jv');if(!v){v=Math.random().toString(36).slice(2,12);localStorage.setItem('jv',v)}return v}catch(_){return null}}

  var wrap=document.createElement('div');
  wrap.innerHTML=`<button class="jfb-fab" type="button" data-fb aria-label="Send feedback">💬 Feedback</button>
<div class="jfb-ov" hidden><form class="jfb-box" novalidate>
  <button type="button" class="jfb-x" data-jfbx aria-label="Close">✕</button>
  <h2>Feedback</h2>
  <p>Spotted a wrong card, have an idea, or found a bug? Leave a note on this page, or point at the exact spot.</p>
  <div class="jfb-about"></div>
  <button type="button" class="jfb-pick">📍 Point at a spot on the page</button>
  <div class="jfb-kinds" role="group" aria-label="What's it about"><button type="button" data-k="card" aria-pressed="false">🃏 Card info</button><button type="button" data-k="idea" aria-pressed="false">💡 Idea</button><button type="button" data-k="bug" aria-pressed="false">🐞 Bug</button><button type="button" data-k="other" aria-pressed="true">💬 Other</button></div>
  <label>Your note<textarea name="m" maxlength="4000" placeholder="What should we know?"></textarea></label>
  <div class="jfb-two"><label>Name (optional)<input name="n" maxlength="80" autocomplete="name"></label><label>Email or IG (optional, for a reply)<input name="c" maxlength="200"></label></div>
  <input class="jfb-hp" name="w" tabindex="-1" autocomplete="off" aria-hidden="true">
  <button class="jfb-go" type="submit">Send feedback</button>
  <div class="jfb-msg" role="status"></div>
</form></div>
<div class="jfb-hl"></div>
<div class="jfb-tip" hidden><span>Tap the part of the page you want to comment on</span><button type="button" data-jfbcancel>Cancel</button></div>`;
  document.body.appendChild(wrap);
  var fab=wrap.querySelector('.jfb-fab'),ov=wrap.querySelector('.jfb-ov'),form=wrap.querySelector('form'),about=wrap.querySelector('.jfb-about'),
      pickBtn=wrap.querySelector('.jfb-pick'),msg=wrap.querySelector('.jfb-msg'),hl=wrap.querySelector('.jfb-hl'),tip=wrap.querySelector('.jfb-tip'),go=wrap.querySelector('.jfb-go');
  tip.style.display='none';

  var CARD=null,TARGET=null,SELECTOR=null,picking=false,hoverEl=null;
  function pageName(){var h=document.querySelector('h1');var t=(h&&h.textContent.trim())||document.title||location.pathname;return t.slice(0,80)}
  function paintAbout(){
    var parts=[];if(CARD)parts.push('🃏 <b>'+esc(CARD.name)+'</b>');if(TARGET)parts.push('📍 <b>'+esc(TARGET)+'</b>');
    if(!parts.length)parts.push('📄 This page: <b>'+esc(pageName())+'</b>');
    about.innerHTML='<span>About: '+parts.join(' · ')+'</span>'+(TARGET||CARD?'<button type="button" class="jfb-clr" data-jfbclr>Whole page instead</button>':'');
    pickBtn.textContent=TARGET?'📍 Point at a different spot':'📍 Point at a spot on the page';
  }
  function setKind(k){form.querySelectorAll('.jfb-kinds button').forEach(function(b){b.setAttribute('aria-pressed',b.dataset.k===k)})}
  function open(opts){opts=opts||{};
    if(opts.fresh){form.reset();msg.textContent='';msg.className='jfb-msg';go.disabled=false;CARD=opts.card||null;TARGET=null;SELECTOR=null;setKind(CARD?'card':'other')}
    paintAbout();ov.hidden=false;fab.style.display='none';setTimeout(function(){form.m.focus()},30)}
  function close(){ov.hidden=true;fab.style.display='';if(location.hash==='#feedback')history.replaceState(null,'',location.pathname+location.search)}

  // ---- describing the spot someone pointed at ----
  var MEANING='[data-fbname],.card,aside,section,header,footer,nav,form,button,a,img,h1,h2,h3,h4,li,tr,label,.box,.facts>div,.links,.buy,.alert,.px,[id]';
  function meaningful(el){var e=el;for(var i=0;e&&e!==document.body&&i<6;i++,e=e.parentElement){if(e.matches&&e.matches(MEANING)){var r=e.getBoundingClientRect();if(r.width>=16&&r.height>=12)return e}}return el}
  function txt(e){return ((e.innerText||e.textContent||'')+'').replace(/\s+/g,' ').trim()}
  function label(el){
    var card=el.closest&&el.closest('.card');
    if(card){var nm=card.querySelector('.nm,b,strong');return ('Card tile: '+(nm?txt(nm):txt(card))).slice(0,200)}
    var t=el.getAttribute('data-fbname')||el.getAttribute('aria-label')||el.getAttribute('alt')||'';
    if(!t){var hd=el.matches('h1,h2,h3,h4')?el:el.querySelector&&el.querySelector('h1,h2,h3,h4,b,strong');t=(hd&&txt(hd))||txt(el)}
    t=t.replace(/\s+/g,' ').trim().slice(0,70);
    var kind={IMG:'Image',BUTTON:'Button',A:'Link',H1:'Heading',H2:'Heading',H3:'Heading',H4:'Heading',HEADER:'Top bar',FOOTER:'Footer',NAV:'Menu',FORM:'Form',TR:'Row',LI:'Item',ASIDE:'Panel',SECTION:'Section'}[el.tagName]||'Section';
        return (kind+(t?': '+t:'')).slice(0,200);
  }
  function selectorOf(el){var path=[];for(var e=el,i=0;e&&e.nodeType===1&&e!==document.body&&i<7;e=e.parentElement,i++){
      if(e.id&&!/^\d/.test(e.id)){path.unshift('#'+CSS.escape(e.id));break}
      var s=e.tagName.toLowerCase(),p=e.parentElement;if(p){var sib=[].filter.call(p.children,function(c){return c.tagName===e.tagName});if(sib.length>1)s+=':nth-of-type('+(sib.indexOf(e)+1)+')'}
      path.unshift(s)}return path.join(' > ').slice(0,600)}
  function ours(el){return el&&(wrap.contains(el))}

  function startPick(){picking=true;ov.hidden=true;fab.style.display='none';tip.hidden=false;tip.style.display='flex';document.documentElement.classList.add('jfb-picking')}
  function stopPick(){picking=false;tip.hidden=true;tip.style.display='none';hl.style.display='none';hoverEl=null;document.documentElement.classList.remove('jfb-picking')}
  function show(el){if(!el){hl.style.display='none';return}var r=el.getBoundingClientRect();hl.style.display='block';hl.style.left=(r.left-4)+'px';hl.style.top=(r.top-4)+'px';hl.style.width=(r.width+8)+'px';hl.style.height=(r.height+8)+'px'}
  function under(x,y){hl.style.display='none';var el=document.elementFromPoint(x,y);return el&&!ours(el)?meaningful(el):null}
  window.addEventListener('pointermove',function(e){if(!picking||e.pointerType==='touch')return;if(ours(e.target)){show(null);return}hoverEl=under(e.clientX,e.clientY);show(hoverEl)},true);
  function choose(el){var ct=el.closest&&el.closest('.card');if(ct)el=ct;TARGET=label(el);SELECTOR=selectorOf(el);
    var c=el.closest&&el.closest('.card[data-i]');if(c&&!CARD&&window.joninFbCardAt){var cc=window.joninFbCardAt(+c.dataset.i);if(cc){CARD=cc;setKind('card')}}
    show(el);setTimeout(function(){stopPick();open()},250)}
  ['pointerdown','mousedown','touchstart','pointerup','mouseup','touchend'].forEach(function(ev){window.addEventListener(ev,function(e){if(!picking||ours(e.target))return;e.preventDefault();e.stopPropagation()},{capture:true,passive:false})});
  window.addEventListener('click',function(e){
    if(picking){if(e.target.closest('[data-jfbcancel]')){e.preventDefault();stopPick();open();return}if(ours(e.target))return;
      e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();var el=under(e.clientX,e.clientY);if(el)choose(el);return}
    var t=e.target.closest('[data-fb],[data-jfbx],[data-jfbclr],.jfb-pick,.jfb-kinds button');if(!t)return;
    if(t.dataset.jfbx!=null){e.preventDefault();close();return}
    if(t.dataset.jfbclr!=null){e.preventDefault();TARGET=SELECTOR=null;CARD=null;setKind('other');paintAbout();return}
    if(t.classList.contains('jfb-pick')){e.preventDefault();startPick();return}
    if(t.dataset.k){e.preventDefault();setKind(t.dataset.k);return}
    e.preventDefault();e.stopPropagation();
    var card=t.hasAttribute('data-fbcard')&&window.joninFbCard?window.joninFbCard():null;
    if(!card&&document.body.dataset.fbcard)card=JSON.parse(document.body.dataset.fbcard);
    open({fresh:true,card:card})},true);
  ov.addEventListener('click',function(e){if(e.target===ov)close()});
  window.addEventListener('keydown',function(e){if(e.key!=='Escape')return;if(picking){e.stopImmediatePropagation();e.preventDefault();stopPick();open()}else if(!ov.hidden){e.stopImmediatePropagation();e.preventDefault();close()}},true);

  form.addEventListener('submit',function(e){e.preventDefault();
    var m=form.m.value.trim();if(m.length<2){msg.className='jfb-msg err';msg.textContent='Write a short note first.';form.m.focus();return}
    if(form.w.value){msg.className='jfb-msg ok';msg.textContent='Thanks!';return}
    var k=(form.querySelector('.jfb-kinds [aria-pressed="true"]')||{dataset:{}}).dataset.k||'other';
    var user=window.joninFbUser?window.joninFbUser():null;
    var row={kind:k,message:m,name:form.n.value.trim()||null,contact:form.c.value.trim()||user||null,card_id:CARD?CARD.id:null,
      page:(location.pathname+location.search+(location.hash&&location.hash!=='#feedback'?location.hash:'')).slice(0,300),visitor:vid(),target:TARGET,selector:SELECTOR};
    go.disabled=true;msg.className='jfb-msg';msg.textContent='Sending…';
    fetch(SUPA+'/rest/v1/feedback',{method:'POST',headers:{apikey:KEY,'Content-Type':'application/json',Prefer:'return=minimal'},body:JSON.stringify(row)})
      .then(function(r){if(r.ok)return;return r.json().catch(function(){return{}}).then(function(j){throw new Error(j.message||'failed')})})
      .then(function(){msg.className='jfb-msg ok';msg.textContent='Thanks! Your note was sent.';setTimeout(function(){if(!ov.hidden)close()},1600)})
      .catch(function(x){go.disabled=false;msg.className='jfb-msg err';msg.textContent=/Too many/.test(x.message)?'Please wait 20 seconds before sending another note.':'Could not send. Please try again.'});
  });

  if(location.hash==='#feedback')setTimeout(function(){open({fresh:true})},300);
  // From /admin/: ?fbspot=<selector> outlines the spot a note was left on.
  var sp=new URLSearchParams(location.search).get('fbspot');
  if(sp)setTimeout(function(){try{var el=document.querySelector(sp);if(el){el.classList.add('jfb-spot');el.scrollIntoView({block:'center'})}}catch(_){}},1500);
})();
