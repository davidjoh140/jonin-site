/* jonin.cards header profile button (every page).
   Signed in: avatar + status symbol (crown = founding, gem = premium, leaf = free) + username + rank (from scrolls),
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
    founding:'<svg viewBox="0 0 20 16" aria-hidden="true"><path d="M2 13.5 1 3.6l5 4L10 1l4 6.6 5-4-1 9.9z" fill="#F2C14E" stroke="#8C5F14" stroke-width="1" stroke-linejoin="round"/><rect x="2" y="13" width="16" height="2.4" rx="1" fill="#E0A63A" stroke="#8C5F14" stroke-width=".8"/></svg>',
    premium:'<svg viewBox="0 0 18 16" aria-hidden="true"><path d="M4.2 1h9.6L17 5.4 9 15 1 5.4z" fill="#F2C14E" stroke="#8C5F14" stroke-width="1" stroke-linejoin="round"/><path d="M1 5.4h16M6 5.4 9 15l3-9.6M4.2 1 6 5.4 9 1l3 4.4L13.8 1" fill="none" stroke="#8C5F14" stroke-width=".7" stroke-linejoin="round"/></svg>',
    free:'<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M8 1.2C12.6 3 14.6 7 13 11.4 11.7 14.6 6.9 15.6 4.3 13 1.8 10.4 2.9 5.4 8 1.2z" fill="#6FB27A" stroke="#2F5E37" stroke-width="1" stroke-linejoin="round"/><path d="M5 12.4C7 9.6 8.6 7.2 9.8 4.2" fill="none" stroke="#2F5E37" stroke-width="1" stroke-linecap="round"/></svg>'
  };
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
    var inB=s.home?'<button type="button" class="jmi" role="menuitem" data-auth="in">Sign in</button>':'<a class="jmi" role="menuitem" href="/#signin">Sign in</a>';
    var fb='<button type="button" class="jmi" role="menuitem" data-fb data-fbname="Header profile menu">Send feedback<small>Notes we use earn scrolls</small></button>';
    if(!s.user){
      return '<div class="jac">'+up+' aria-haspopup="menu">'+'<span>'+(s.guest?'Sign up<span class="jx"> to save</span>':'Sign up')+'</span>'+CARET+upEnd+
        '<div class="jam" role="menu"><div class="jmp"><b>Free account</b><span>Save your collection and vote for the coolest cards. The first 20 members get Premium free, forever.</span></div>'+
        (s.home?'<button type="button" class="jmi jgo" role="menuitem" data-auth="up">Create free account</button>':'<a class="jmi jgo" role="menuitem" href="/#signup">Create free account</a>')+
        inB+(s.guest?'<a class="jmi" role="menuitem" '+mine+'>My collection<small>'+s.guest+' card'+(s.guest===1?'':'s')+' saved on this device only</small></a>':'')+
        '<a class="jmi" role="menuitem" href="/missions/">Missions<small>Earn scrolls and rank up</small></a>'+fb+themeRow()+'</div></div>';
    }
    var st=s.badge==='founding'?'founding':s.badge==='premium'?'premium':'free';
    var p=s.pts,rank=p&&p.rank?p.rank:'',pts=p?(p.xp!=null?p.xp:(p.points||0)):0,lo=p&&p.prev_at||0;
    var pct=p&&p.next_at?Math.min(100,Math.round((pts-lo)/(p.next_at-lo)*100)):100;
    var name=s.handle||'',ld=!name; // no name yet: profile still loading, show a quiet placeholder
    return '<div class="jac">'+
      '<a class="jab jpf st-'+st+'" '+mine+' aria-haspopup="menu" title="'+esc((name||'Profile')+' · '+LABEL[st]+(rank?' · '+rank:''))+'">'+
        '<span class="jav">'+avatar(s,30)+'<i class="jbg">'+ICON[st]+'</i></span>'+
        '<span class="jat">'+(ld?'<i class="jld"></i>':'<b>'+esc(name)+'</b>')+(rank?'<small>'+esc(rank)+'</small>':'')+'</span>'+CARET+'</a>'+
      '<div class="jam" role="menu">'+
        '<div class="jah"><span class="jav big">'+avatar(s,48)+'</span><div><b>'+esc(name||'Loading…')+'</b><span class="jst st-'+st+'">'+ICON[st]+LABEL[st]+'</span></div></div>'+
        (p?'<a class="jrk" href="/missions/" role="menuitem" style="display:block;text-decoration:none" title="See your missions"><div><span>Rank</span> <b>'+esc(rank)+'</b><span class="jpt">📜 '+pts+(pts===1?' scroll':' scrolls')+'</span></div><span class="jbar"><i style="width:'+pct+'%"></i></span>'+
          (p.next?'<small>'+(p.next_at-pts)+((p.next_at-pts)===1?' scroll':' scrolls')+' to '+esc(p.next)+'</small>':'<small>Top rank</small>')+'</a>':'')+
        '<a class="jmi" role="menuitem" '+mine+'>My collection<small>Haves, wants, slabs and profile</small></a>'+
        '<a class="jmi" role="menuitem" '+(s.home?'href="#lists" data-v="mine" data-lmine':'href="/#lists"')+'>My lists<small>Your own card lists</small></a>'+
        '<a class="jmi" role="menuitem" href="/missions/">Missions<small>Earn scrolls and rank up</small></a>'+
        (st==='free'?'<a class="jmi jprem" role="menuitem" href="/premium/">Unlock Premium</a>':'')+
        fb+themeRow()+
        '<button type="button" class="jmi jout" role="menuitem" '+(s.home?'data-signout':'data-jsignout')+'>Sign out</button>'+
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
