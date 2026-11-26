/* jonin.cards header profile button (every page).
   Signed in: avatar + status symbol (headband worn on the avatar = founding, gem = premium, leaf = free) + username + rank (from scrolls),
   with a hover menu (rank/scrolls, My collection, Missions, Premium, Send feedback, Theme, Sign out).
   Signed out: one "Sign up" button whose hover menu holds Sign in, the guest collection and Theme.
   The homepage renders it through JoninAcct.html(state); other pages mark <span id="acct" data-auto> and this file fills it in,
   reading the signed-in session the homepage's Supabase client saved in localStorage (no Supabase library needed here). */
(function(){
  var SUPA='https://cfzpayanhvvqtkuqfgof.supabase.co',KEY='sb_publishable_ZR1zggWL9FxxwfwoIASwSg_YDV3Nvfe';
  var TK='sb-cfzpayanhvvqtkuqfgof-auth-token',GK='jonin_guest_v1',CK='jonin_acct_v1';
  var THEMEF=['naruto','sasuke','itachi','kakashi','gaara','hinata','sakura','rock-lee'];
  function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]})}
  function ls(k){try{return JSON.parse(localStorage.getItem(k)||'null')}catch(_){return null}}
  function avSrc(sl,a){if(!sl)return '';if(a==='portrait'&&THEMEF.indexOf(sl)>-1)return '/theme-faces/'+sl+'.webp';if(a==='action')return '/char-art/'+sl+'.webp';return '/chars/'+sl+'.webp'}

  // Status symbols (PLACEHOLDER look, David to fine-tune)
  var ICON={
    founding:'<svg viewBox="0 0 26 16" aria-hidden="true"><path d="M19.6 7.4c2.4.4 4 1.9 5.6 4.6l-1.7.8c-1.2-2-2.6-3.1-4.3-3.5z" fill="#31426A" stroke="#0B1222" stroke-width=".7" stroke-linejoin="round"/><path d="M19.4 9.2c1.6 1 2.6 2.6 3.2 5.1l-1.8.4c-.5-2-1.3-3.2-2.4-4z" fill="#3A4D78" stroke="#0B1222" stroke-width=".7" stroke-linejoin="round"/><path d="M.8 5.6Q10 4 20.4 5.6v5.2Q10 9.2.8 10.8z" fill="#3A4D78" stroke="#0B1222" stroke-width=".8" stroke-linejoin="round"/><rect x="5" y="3" width="11" height="10" rx="1.3" fill="#C3CCD6" stroke="#3E4856" stroke-width=".9"/><path d="M6.2 4.3h8.6" stroke="#F4F7FA" stroke-width=".8" stroke-linecap="round"/><circle cx="6.5" cy="5.6" r=".55" fill="#6B7684"/><circle cx="14.5" cy="5.6" r=".55" fill="#6B7684"/><circle cx="6.5" cy="11.3" r=".55" fill="#6B7684"/><circle cx="14.5" cy="11.3" r=".55" fill="#6B7684"/><path d="M10.5 5.4l.75 2.3 2.3.75-2.3.75-.75 2.3-.75-2.3-2.3-.75 2.3-.75z" fill="none" stroke="#3E4856" stroke-width=".75" stroke-linejoin="round"/></svg>',
    premium:'<svg viewBox="0 0 18 16" aria-hidden="true"><path d="M4.2 1h9.6L17 5.4 9 15 1 5.4z" fill="#F2C14E" stroke="#8C5F14" stroke-width="1" stroke-linejoin="round"/><path d="M1 5.4h16M6 5.4 9 15l3-9.6M4.2 1 6 5.4 9 1l3 4.4L13.8 1" fill="none" stroke="#8C5F14" stroke-width=".7" stroke-linejoin="round"/></svg>',
    free:'<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M8 1.2C12.6 3 14.6 7 13 11.4 11.7 14.6 6.9 15.6 4.3 13 1.8 10.4 2.9 5.4 8 1.2z" fill="#6FB27A" stroke="#2F5E37" stroke-width="1" stroke-linejoin="round"/><path d="M5 12.4C7 9.6 8.6 7.2 9.8 4.2" fill="none" stroke="#2F5E37" stroke-width="1" stroke-linecap="round"/></svg>'
  };
  // Founding members' avatars wear the headband (sits across the forehead, tails hang off the right)
  var WORN='<svg viewBox="0 0 40 30" aria-hidden="true"><path d="M29.7 10.77c3.6.3 6.6 2.7 9.2 7l-2.1 1.1c-2-3.3-4.3-5.1-7.3-5.4z" fill="#31426A" stroke="#0B1222" stroke-width=".8" stroke-linejoin="round"/><path d="M29.5 12.57c2.4 1.6 4 4.2 4.9 7.9l-2.3.5c-.7-3-1.8-5-3.3-6.2z" fill="#3A4D78" stroke="#0B1222" stroke-width=".8" stroke-linejoin="round"/><path d="M1.19 9.14 L3.16 8.47 L5.14 7.9 L7.11 7.43 L9.08 7.07 L11.05 6.81 L13.03 6.65 L15 6.6 L16.97 6.65 L18.95 6.81 L20.92 7.07 L22.89 7.43 L24.86 7.9 L26.84 8.47 L28.81 9.14 A15 15 0 0 1 30 14.8 L27.86 14 L25.71 13.33 L23.57 12.78 L21.43 12.35 L19.29 12.04 L17.14 11.86 L15 11.8 L12.86 11.86 L10.71 12.04 L8.57 12.35 L6.43 12.78 L4.29 13.33 L2.14 14 L0 14.8 A15 15 0 0 1 1.19 9.14Z" fill="#3A4D78" stroke="#0B1222" stroke-width=".9" stroke-linejoin="round"/><path d="M2.19 9.89Q15 5.51 27.81 9.89" fill="none" stroke="#5A6E9C" stroke-width=".6" stroke-linecap="round" opacity=".7"/><circle cx="29.7" cy="11.97" r="1.25" fill="#31426A" stroke="#0B1222" stroke-width=".8"/><rect x="9.4" y="4.2" width="11.2" height="8.5" rx="1.3" fill="#C3CCD6" stroke="#3E4856" stroke-width=".9"/><path d="M10.6 5.3h8.8" stroke="#F4F7FA" stroke-width=".8" stroke-linecap="round"/><circle cx="10.9" cy="6.5" r=".55" fill="#6B7684"/><circle cx="10.9" cy="11.2" r=".55" fill="#6B7684"/><circle cx="19.1" cy="6.5" r=".55" fill="#6B7684"/><circle cx="19.1" cy="11.2" r=".55" fill="#6B7684"/><path d="M15 5.85l0.83 1.77 1.77 0.83-1.77 0.83-0.83 1.77-0.83-1.77-1.77-0.83 1.77-0.83z" fill="none" stroke="#3E4856" stroke-width=".7" stroke-linejoin="round"/></svg>';
  function band(st){return st==='founding'?'<i class="jhb">'+WORN+'</i>':''}
  // Menu item icons (bookcase, open scroll, closed scroll set by David; the rest are PLACEHOLDERS to fine-tune)
  var MI={
    shelf:'<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="2" width="18" height="20" rx="1.6" fill="#8A5A2B" stroke="#4A2E14" stroke-width="1"/><rect x="5" y="4" width="14" height="16" fill="#3B2412"/><rect x="5.6" y="5" width="2" height="4" fill="#D9534F"/><rect x="7.9" y="5.6" width="1.8" height="3.4" fill="#F0A13A"/><rect x="10" y="4.8" width="2.2" height="4.2" fill="#4F86C6"/><rect x="13.4" y="5.4" width="1.8" height="3.6" fill="#6FB27A"/><rect x="5.6" y="10.8" width="2" height="3.8" fill="#F2C14E"/><rect x="7.9" y="11.2" width="2" height="3.4" fill="#9B6FC6"/><rect x="10.2" y="10.6" width="1.8" height="4" fill="#D9534F"/><path d="M13 14.6l2.6-3.6 1.4 1-2.6 3.6z" fill="#4F86C6"/><rect x="5.6" y="16.4" width="2.2" height="3.6" fill="#4F86C6"/><rect x="8.1" y="16" width="1.8" height="4" fill="#6FB27A"/><rect x="13" y="16.6" width="2" height="3.4" fill="#F0A13A"/><rect x="15.3" y="16.2" width="2" height="3.8" fill="#D9534F"/><rect x="5" y="9" width="14" height="1.4" fill="#8A5A2B"/><rect x="5" y="14.6" width="14" height="1.4" fill="#8A5A2B"/></svg>',
    scrollOpen:'<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="6" y="4" width="12" height="16" fill="#F3E2B8" stroke="#8C5F14" stroke-width="1"/><path d="M8.5 8.2h7M8.5 10.7h7M8.5 13.2h5.5M8.5 15.7h6.4" stroke="#B08A4A" stroke-width="1" stroke-linecap="round"/><rect x="4" y="2.3" width="16" height="3.2" rx="1.6" fill="#E3C17E" stroke="#8C5F14" stroke-width="1"/><rect x="4" y="18.5" width="16" height="3.2" rx="1.6" fill="#E3C17E" stroke="#8C5F14" stroke-width="1"/></svg>',
    scrollClosed:'<svg viewBox="0 0 24 24" aria-hidden="true"><g transform="rotate(-28 12 12)"><path d="M12 16.4l-2 4.4M12 16.4l2.2 4.2" stroke="#B83A35" stroke-width="1.6" stroke-linecap="round"/><rect x="2.5" y="8" width="18" height="8" rx="4" fill="#F3E2B8" stroke="#8C5F14" stroke-width="1"/><ellipse cx="18.5" cy="12" rx="2" ry="4" fill="#E3C17E" stroke="#8C5F14" stroke-width="1"/><ellipse cx="18.5" cy="12" rx=".8" ry="1.6" fill="none" stroke="#8C5F14" stroke-width=".8"/><rect x="10.4" y="7.5" width="3.2" height="9" rx=".6" fill="#D9534F" stroke="#8C2B28" stroke-width=".7"/></g></svg>',
    lock:'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 11V8a4 4 0 0 1 8 0v3" fill="none" stroke="#8C5F14" stroke-width="2"/><rect x="5" y="10.5" width="14" height="10.5" rx="2.2" fill="#F2C14E" stroke="#8C5F14" stroke-width="1"/><circle cx="12" cy="15.2" r="1.5" fill="#8C5F14"/><path d="M12 15.6v2.6" stroke="#8C5F14" stroke-width="1.4" stroke-linecap="round"/></svg>',
    chat:'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5.5A2.5 2.5 0 0 1 6.5 3h11A2.5 2.5 0 0 1 20 5.5v8a2.5 2.5 0 0 1-2.5 2.5H11l-4.5 4v-4h0A2.5 2.5 0 0 1 4 13.5z" fill="#7FB3E8" stroke="#2F5A86" stroke-width="1" stroke-linejoin="round"/><circle cx="8.5" cy="9.5" r="1.1" fill="#2F5A86"/><circle cx="12" cy="9.5" r="1.1" fill="#2F5A86"/><circle cx="15.5" cy="9.5" r="1.1" fill="#2F5A86"/></svg>',
    key:'<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="8" cy="12" r="4.5" fill="#F2C14E" stroke="#8C5F14" stroke-width="1"/><circle cx="8" cy="12" r="1.6" fill="#8C5F14"/><path d="M12.3 12H21M18 12v3M20.5 12v2.2" stroke="#8C5F14" stroke-width="2" stroke-linecap="round"/></svg>',
    join:'<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="10" cy="8" r="4" fill="#F0A13A" stroke="#8C4F14" stroke-width="1"/><path d="M2.5 21a7.5 7.5 0 0 1 15 0z" fill="#F0A13A" stroke="#8C4F14" stroke-width="1" stroke-linejoin="round"/><circle cx="18.5" cy="6.5" r="4" fill="#6FB27A" stroke="#2F5E37" stroke-width="1"/><path d="M18.5 4.6v3.8M16.6 6.5h3.8" stroke="#fff" stroke-width="1.5" stroke-linecap="round"/></svg>',
    door:'<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="4" y="2.5" width="11" height="19" rx="1.2" fill="#A9784A" stroke="#4A2E14" stroke-width="1"/><circle cx="12.4" cy="12.4" r="1" fill="#F2C14E"/><path d="M14.5 12H21M18.2 9l2.9 3-2.9 3" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>'
  };
  function ic(k){return '<i class="jic">'+MI[k]+'</i>'}
  // Wraps a label (+ optional <small>) so the icon sits in its own column
  function lb(k,t){return ic(k)+'<span class="jtx">'+t+'</span>'}
  var LABEL={founding:'Founding member',premium:'Premium member',free:'Free member'};
  var CARET='<svg class="jcar" viewBox="0 0 10 6" aria-hidden="true"><path d="M1 1l4 4 4-4" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>';

  function themeRow(){
    var T=window.JONIN_THEMES||[];if(!T.length)return '';
    var cur;try{cur=localStorage.getItem('jtheme')||'jonin'}catch(_){cur='jonin'}
    return '<div class="jth"><span>Theme</span><div class="jsw">'+T.map(function(t){
      return '<button type="button" data-jt="'+t.id+'" aria-checked="'+(t.id===cur)+'" role="menuitemradio" title="'+esc(t.n+' · '+t.d)+'" aria-label="Theme: '+esc(t.n)+'" style="--a:'+t.bg+';--b:'+t.a+';--c:'+t.c+";--f:url('"+t.f+"')"+'"></button>'}).join('')+'</div></div>';
  }
  function avatar(s,sz){
    var src=avSrc(s.fav,s.avatar);
    return src?'<img src="'+esc(src)+'" alt="" width="'+sz+'" height="'+sz+'" decoding="async">':'<span class="jini">'+esc((s.handle||'').charAt(0).toUpperCase())+'</span>';
  }

  // s = {home, user, handle, fav, avatar, badge:'founding'|'premium'|null, pts:{xp,rank,next,next_at,prev_at}|null (from my_xp), guest}
  function html(s){
    var mine=s.home?'href="#mine" data-v="mine"':'href="/#mine"';
    var up=s.home?'<button type="button" class="jab jsu" data-auth="up"':'<a class="jab jsu" href="/#signup"';
    var upEnd=s.home?'</button>':'</a>';
    var inB=s.home?'<button type="button" class="jmi" role="menuitem" data-auth="in">'+lb('key','Sign in')+'</button>':'<a class="jmi" role="menuitem" href="/#signin">'+lb('key','Sign in')+'</a>';
    var fb='<button type="button" class="jmi" role="menuitem" data-fb data-fbname="Header profile menu">'+lb('chat','Send feedback<small>Notes we use earn scrolls</small>')+'</button>';
    if(!s.user){
      return '<div class="jac">'+up+' aria-haspopup="menu">'+'<span>'+(s.guest?'Sign up<span class="jx"> to save</span>':'Sign up')+'</span>'+CARET+upEnd+
        '<div class="jam" role="menu"><div class="jmp"><b>Free account</b><span>Save your collection and vote for the coolest cards. The first 20 members get Premium free, forever.</span></div>'+
        (s.home?'<button type="button" class="jmi jgo" role="menuitem" data-auth="up">'+lb('join','Create free account')+'</button>':'<a class="jmi jgo" role="menuitem" href="/#signup">'+lb('join','Create free account')+'</a>')+
        inB+(s.guest?'<a class="jmi" role="menuitem" '+mine+'>'+lb('shelf','My collection<small>'+s.guest+' card'+(s.guest===1?'':'s')+' saved on this device only</small>')+'</a>':'')+
        '<a class="jmi" role="menuitem" href="/missions/">'+lb('scrollClosed','Missions<small>Earn scrolls and rank up</small>')+'</a>'+fb+themeRow()+'</div></div>';
    }
    var st=s.badge==='founding'?'founding':s.badge==='premium'?'premium':'free';
    var p=s.pts,rank=p&&p.rank?p.rank:'',pts=p?(p.xp!=null?p.xp:(p.points||0)):0,lo=p&&p.prev_at||0;
    var pct=p&&p.next_at?Math.min(100,Math.round((pts-lo)/(p.next_at-lo)*100)):100;
    var name=s.handle||'',ld=!name; // no name yet: profile still loading, show a quiet placeholder
    return '<div class="jac">'+
      '<a class="jab jpf st-'+st+'" '+mine+' aria-haspopup="menu" title="'+esc((name||'Profile')+' · '+LABEL[st]+(rank?' · '+rank:''))+'">'+
        '<span class="jav">'+avatar(s,30)+(st==='founding'?band(st):'<i class="jbg">'+ICON[st]+'</i>')+'</span>'+
        '<span class="jat">'+(ld?'<i class="jld"></i>':'<b>'+esc(name)+'</b>')+(rank?'<small>'+esc(rank)+'</small>':'')+'</span>'+CARET+'</a>'+
      '<div class="jam" role="menu">'+
        '<div class="jah"><span class="jav big">'+avatar(s,48)+band(st)+'</span><div><b>'+esc(name||'Loading…')+'</b><span class="jst st-'+st+'">'+ICON[st]+LABEL[st]+'</span></div></div>'+
        (p?'<a class="jrk" href="/missions/" role="menuitem" style="display:block;text-decoration:none" title="See your missions"><div><span>Rank</span> <b>'+esc(rank)+'</b><span class="jpt">📜 '+pts+(pts===1?' scroll':' scrolls')+'</span></div><span class="jbar"><i style="width:'+pct+'%"></i></span>'+
          (p.next?'<small>'+(p.next_at-pts)+((p.next_at-pts)===1?' scroll':' scrolls')+' to '+esc(p.next)+'</small>':'<small>Top rank</small>')+'</a>':'')+
        '<a class="jmi" role="menuitem" '+mine+'>'+lb('shelf','My collection<small>Haves, wants, slabs and profile</small>')+'</a>'+
        '<a class="jmi" role="menuitem" '+(s.home?'href="#lists" data-v="mine" data-lmine':'href="/#lists"')+'>'+lb('scrollOpen','My lists<small>Your own card lists</small>')+'</a>'+
        '<a class="jmi" role="menuitem" href="/missions/">'+lb('scrollClosed','Missions<small>Earn scrolls and rank up</small>')+'</a>'+
        (st==='free'?'<a class="jmi jprem" role="menuitem" href="/premium/">'+lb('lock','Unlock Premium')+'</a>':'')+
        fb+themeRow()+
        '<button type="button" class="jmi jout" role="menuitem" '+(s.home?'data-signout':'data-jsignout')+'>'+lb('door','Sign out')+'</button>'+
      '</div></div>';
  }

  // Remember what the header showed, so other pages can show it right away
  function cache(s){try{if(s&&s.user)localStorage.setItem(CK,JSON.stringify({uid:s.uid,handle:s.handle,fav:s.fav,avatar:s.avatar,badge:s.badge,pts:s.pts}));else localStorage.removeItem(CK)}catch(_){}}

  // Interactions: hover/focus opens on desktop (CSS); on touch the first tap opens the menu
  var touch=window.matchMedia&&matchMedia('(hover: none)').matches;
  function closeAll(except){var o=document.querySelectorAll('.jac.open');for(var i=0;i<o.length;i++)if(o[i]!==except)o[i].classList.remove('open');var a=document.activeElement;if(a&&a.closest&&a.closest('.jac')&&!(except&&except.contains(a)))a.blur()}
  document.addEventListener('click',function(ev){
    var t=ev.target;
    var ab=t.closest&&t.closest('.jab');
    if(ab&&touch){var w=ab.parentNode;if(!w.classList.contains('open')){ev.preventDefault();ev.stopPropagation();closeAll(w);w.classList.add('open');return}}
    var th=t.closest&&t.closest('[data-jt]');
    if(th&&window.joninSetTheme){var id=window.joninSetTheme(th.getAttribute('data-jt'));var b=document.querySelectorAll('[data-jt]');for(var i=0;i<b.length;i++)b[i].setAttribute('aria-checked',b[i].getAttribute('data-jt')===id);return}
    if(t.closest&&t.closest('[data-jsignout]')){signOut();return}
    if(t.closest&&t.closest('.jmi'))closeAll();
    else if(!(t.closest&&t.closest('.jac')))closeAll();
  },true);
  document.addEventListener('keydown',function(ev){if(ev.key==='Escape'){closeAll();var a=document.activeElement;if(a&&a.closest&&a.closest('.jam'))a.blur()}});

  // ---- other pages ----
  var EL=null;
  function session(){var s=ls(TK);if(s&&s.currentSession)s=s.currentSession;return s&&s.access_token&&s.user?s:null}
  // same count as the homepage: distinct cards across haves, wants and slabs
  function guestCount(){var g=ls(GK);if(!g)return 0;var ids={},n=0,it=g.items||[],sl=g.slabs||[],i,k;
    for(i=0;i<it.length;i++){k=String(it[i][0]||'').split('|')[0];if(k&&!ids[k]){ids[k]=1;n++}}
    for(i=0;i<sl.length;i++){k=sl[i]&&sl[i].card_id;if(k&&!ids[k]){ids[k]=1;n++}}return n}
  function paint(st){if(EL)EL.innerHTML=html(st)}
  function rest(path,tok,body){
    return fetch(SUPA+path,{method:body?'POST':'GET',headers:{apikey:KEY,Authorization:'Bearer '+tok,'Content-Type':'application/json'},body:body?JSON.stringify(body):undefined}).then(function(r){if(!r.ok)throw r.status;return r.json()});
  }
  var LAST='';
  function load(){
    if(!EL)return;
    var s=session();
    var key=s?s.user.id:'out:'+guestCount();if(key===LAST)return;LAST=key;
    if(!s){paint({user:false,guest:guestCount()});return}
    var c=ls(CK);if(!c||c.uid!==s.user.id)c={uid:s.user.id};
    var base={user:true,uid:s.user.id,handle:c.handle||'',fav:c.fav,avatar:c.avatar,badge:c.badge,pts:c.pts};
    paint(base);
    if(s.expires_at&&s.expires_at*1000<Date.now()+5000)return; // stale token: keep showing the remembered profile
    var tok=s.access_token,uid=encodeURIComponent(s.user.id);
    Promise.all([
      rest('/rest/v1/profiles?id=eq.'+uid+'&select=handle,fav_character,avatar',tok).catch(function(){return null}),
      rest('/rest/v1/memberships?user_id=eq.'+uid+'&select=active,until,founding',tok).catch(function(){return null}),
      rest('/rest/v1/rpc/my_xp',tok,{}).catch(function(){return null})
    ]).then(function(r){
      var p=r[0]&&r[0][0],m=r[1]&&r[1][0];
      if(p){base.handle=p.handle||base.handle;base.fav=p.fav_character||null;base.avatar=p.avatar||null}
      if(r[1]){var on=!!(m&&m.active&&(!m.until||new Date(m.until)>new Date()));base.badge=on?(m.founding?'founding':'premium'):null}
      if(r[2])base.pts=r[2];
      paint(base);cache(base);
    });
  }
  function signOut(){
    var s=session();
    if(s&&s.access_token)fetch(SUPA+'/auth/v1/logout',{method:'POST',headers:{apikey:KEY,Authorization:'Bearer '+s.access_token}}).catch(function(){});
    try{localStorage.removeItem(TK);localStorage.removeItem(CK)}catch(_){}
    LAST='';closeAll();load();
  }
  function auto(){
    EL=document.querySelector('#acct[data-auto]');if(!EL)return;
    load();
    // pick up a sign-in or sign-out made elsewhere on the page or in another tab
    window.addEventListener('storage',function(e){if(e.key===TK||e.key===GK||e.key===CK){LAST='';load()}});
    document.addEventListener('visibilitychange',function(){if(!document.hidden)load()});
    setInterval(load,4000);
  }

  window.JoninAcct={html:html,cache:cache,cached:function(){return ls(CK)},icon:ICON,label:LABEL,refresh:function(){LAST='';load()}};
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',auto);else auto();
})();
