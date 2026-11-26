/* jonin.cards header profile button (every page).
   Signed in: avatar + status symbol (founding = gold ring around the picture, premium = headband worn on the picture, free = leaf) + username + rank (from scrolls),
   with a hover menu (rank/scrolls, My collection, Missions, Jonin Club, Send feedback, Theme, Sign out).
   Signed out: one "Sign up" button whose hover menu holds Sign in, the guest collection and Theme.
   The homepage renders it through JoninAcct.html(state); other pages mark <span id="acct" data-auto> and this file fills it in,
   reading the signed-in session the homepage's Supabase client saved in localStorage (no Supabase library needed here). */
(function(){
  var SUPA='https://cfzpayanhvvqtkuqfgof.supabase.co',KEY='sb_publishable_ZR1zggWL9FxxwfwoIASwSg_YDV3Nvfe';
  var TK='sb-cfzpayanhvvqtkuqfgof-auth-token',GK='jonin_guest_v1',CK='jonin_acct_v1';
  var THEMEF=['naruto','sasuke','itachi','kakashi','gaara','hinata','sakura','rock-lee'];
  function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]})}
  function ls(k){try{return JSON.parse(localStorage.getItem(k)||'null')}catch(_){return null}}
  // Founding spots left (Supabase founding_spots_left), cached 10 minutes so the header can switch its offer text.
  var FK='jonin_fleft';
  function fleft(){var f=ls(FK);if(!f||Date.now()-f.t>6e5){fetch(SUPA+'/rest/v1/rpc/founding_spots_left',{method:'POST',headers:{apikey:KEY,'Content-Type':'application/json'},body:'{}'})
    .then(function(r){return r.ok?r.json():null}).then(function(n){if(typeof n==='number'){try{localStorage.setItem(FK,JSON.stringify({n:n,t:Date.now()}))}catch(_){}}}).catch(function(){})}
    return f?f.n:null}
  function offerLine(){var n=fleft();return n===0?'Founding spots are gone. Jonin Club opens soon: <a href="/club/#join">join the waitlist</a>.':'The first 20 members get Jonin Club free, forever.'}
  function avSrc(sl,a){if(!sl)return '';if(a==='portrait'&&THEMEF.indexOf(sl)>-1)return '/theme-faces/'+sl+'.webp';if(a==='action')return '/char-art/'+sl+'.webp';return '/chars/'+sl+'.webp'}

  // Status symbols (PLACEHOLDER look, David to fine-tune)
  var ICON={
    founding:'<svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="6" fill="none" stroke="#8C5F14" stroke-width="3.6"/><circle cx="8" cy="8" r="6" fill="none" stroke="#F2C14E" stroke-width="2.2"/><path d="M4.6 4.4a4.8 4.8 0 0 1 3.4-1.3" fill="none" stroke="#FFF1C4" stroke-width=".9" stroke-linecap="round"/></svg>',
    premium:'<svg viewBox="0 2 40 18" aria-hidden="true"><defs><linearGradient id="jhbC" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#53689A"/><stop offset=".55" stop-color="#3A4D7A"/><stop offset="1" stop-color="#2A3A5F"/></linearGradient><linearGradient id="jhbM" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#F3F6F9"/><stop offset=".46" stop-color="#C9D1DA"/><stop offset=".54" stop-color="#A9B4C1"/><stop offset="1" stop-color="#C7CED7"/></linearGradient></defs><path d="M29.3 11.17C31.9 11.47 35.7 13.67 38.1 17.67L36.2 18.87C34.9 15.47 32.1 13.47 29.3 12.97Z" fill="#33456F" stroke="#141C30" stroke-width=".6" stroke-linejoin="round"/><path d="M29.1 12.27C31.1 13.47 32.9 15.87 33.7 19.67L31.7 20.07C31.6 17.07 30.5 15.07 28.7 13.67Z" fill="#2A3A5F" stroke="#141C30" stroke-width=".6" stroke-linejoin="round"/><path d="M1.19 9.14Q15 4.06 28.81 9.14A15 15 0 0 1 30 15Q15 9 0 15A15 15 0 0 1 1.19 9.14Z" fill="url(#jhbC)" stroke="#141C30" stroke-width=".6" stroke-linejoin="round"/><path d="M2.09 12.17Q15 7.73 27.91 12.17" fill="none" stroke="#1E2B4A" stroke-width=".45" stroke-linecap="round" opacity=".55"/><ellipse cx="29.3" cy="12.07" rx="1.35" ry="1.55" fill="url(#jhbC)" stroke="#141C30" stroke-width=".6"/><path d="M9.3 6.23Q9.3 4.73 10.8 4.54Q15 4.06 19.2 4.54Q20.7 4.73 20.7 6.23L20.7 12.03Q20.7 13.53 19.2 13.34Q15 12.86 10.8 13.34Q9.3 13.53 9.3 12.03Z" fill="url(#jhbM)" stroke="#4A5462" stroke-width=".6" stroke-linejoin="round"/><path d="M10.15 6.36Q10.15 5.46 11.05 5.36Q15 4.94 18.95 5.36Q19.85 5.46 19.85 6.36L19.85 11.66Q19.85 12.56 18.95 12.46Q15 12.04 11.05 12.46Q10.15 12.56 10.15 11.66Z" fill="none" stroke="#fff" stroke-width=".4" opacity=".55"/><circle cx="10.85" cy="6.28" r=".5" fill="#7D8896"/><circle cx="10.71" cy="6.13" r=".18" fill="#fff" opacity=".8"/><circle cx="10.85" cy="12.03" r=".5" fill="#7D8896"/><circle cx="10.71" cy="11.88" r=".18" fill="#fff" opacity=".8"/><circle cx="19.15" cy="6.28" r=".5" fill="#7D8896"/><circle cx="19.01" cy="6.13" r=".18" fill="#fff" opacity=".8"/><circle cx="19.15" cy="12.03" r=".5" fill="#7D8896"/><circle cx="19.01" cy="11.88" r=".18" fill="#fff" opacity=".8"/><path d="M15 6.2L15.53 8.17L17.5 8.7L15.53 9.23L15 11.2L14.47 9.23L12.5 8.7L14.47 8.17Z" transform="translate(0 .35)" fill="none" stroke="#fff" stroke-width=".55" stroke-linejoin="round" opacity=".7"/><path d="M15 6.2L15.53 8.17L17.5 8.7L15.53 9.23L15 11.2L14.47 9.23L12.5 8.7L14.47 8.17Z" fill="none" stroke="#525C6A" stroke-width=".6" stroke-linejoin="round"/></svg>',
    free:'<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M8 1.2C12.6 3 14.6 7 13 11.4 11.7 14.6 6.9 15.6 4.3 13 1.8 10.4 2.9 5.4 8 1.2z" fill="#6FB27A" stroke="#2F5E37" stroke-width="1" stroke-linejoin="round"/><path d="M5 12.4C7 9.6 8.6 7.2 9.8 4.2" fill="none" stroke="#2F5E37" stroke-width="1" stroke-linecap="round"/></svg>'
  };
  // Jonin Club members' avatars wear the headband (sits across the forehead, tails hang off the right)
  var WORN='<svg viewBox="0 0 40 30" aria-hidden="true"><defs><linearGradient id="jhbC" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#53689A"/><stop offset=".55" stop-color="#3A4D7A"/><stop offset="1" stop-color="#2A3A5F"/></linearGradient><linearGradient id="jhbM" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#F3F6F9"/><stop offset=".46" stop-color="#C9D1DA"/><stop offset=".54" stop-color="#A9B4C1"/><stop offset="1" stop-color="#C7CED7"/></linearGradient></defs><path d="M29.3 11.17C31.9 11.47 35.7 13.67 38.1 17.67L36.2 18.87C34.9 15.47 32.1 13.47 29.3 12.97Z" fill="#33456F" stroke="#141C30" stroke-width=".6" stroke-linejoin="round"/><path d="M29.1 12.27C31.1 13.47 32.9 15.87 33.7 19.67L31.7 20.07C31.6 17.07 30.5 15.07 28.7 13.67Z" fill="#2A3A5F" stroke="#141C30" stroke-width=".6" stroke-linejoin="round"/><path d="M1.19 9.14Q15 4.06 28.81 9.14A15 15 0 0 1 30 15Q15 9 0 15A15 15 0 0 1 1.19 9.14Z" fill="url(#jhbC)" stroke="#141C30" stroke-width=".6" stroke-linejoin="round"/><path d="M2.09 12.17Q15 7.73 27.91 12.17" fill="none" stroke="#1E2B4A" stroke-width=".45" stroke-linecap="round" opacity=".55"/><ellipse cx="29.3" cy="12.07" rx="1.35" ry="1.55" fill="url(#jhbC)" stroke="#141C30" stroke-width=".6"/><path d="M9.3 6.23Q9.3 4.73 10.8 4.54Q15 4.06 19.2 4.54Q20.7 4.73 20.7 6.23L20.7 12.03Q20.7 13.53 19.2 13.34Q15 12.86 10.8 13.34Q9.3 13.53 9.3 12.03Z" fill="url(#jhbM)" stroke="#4A5462" stroke-width=".6" stroke-linejoin="round"/><path d="M10.15 6.36Q10.15 5.46 11.05 5.36Q15 4.94 18.95 5.36Q19.85 5.46 19.85 6.36L19.85 11.66Q19.85 12.56 18.95 12.46Q15 12.04 11.05 12.46Q10.15 12.56 10.15 11.66Z" fill="none" stroke="#fff" stroke-width=".4" opacity=".55"/><circle cx="10.85" cy="6.28" r=".5" fill="#7D8896"/><circle cx="10.71" cy="6.13" r=".18" fill="#fff" opacity=".8"/><circle cx="10.85" cy="12.03" r=".5" fill="#7D8896"/><circle cx="10.71" cy="11.88" r=".18" fill="#fff" opacity=".8"/><circle cx="19.15" cy="6.28" r=".5" fill="#7D8896"/><circle cx="19.01" cy="6.13" r=".18" fill="#fff" opacity=".8"/><circle cx="19.15" cy="12.03" r=".5" fill="#7D8896"/><circle cx="19.01" cy="11.88" r=".18" fill="#fff" opacity=".8"/><path d="M15 6.2L15.53 8.17L17.5 8.7L15.53 9.23L15 11.2L14.47 9.23L12.5 8.7L14.47 8.17Z" transform="translate(0 .35)" fill="none" stroke="#fff" stroke-width=".55" stroke-linejoin="round" opacity=".7"/><path d="M15 6.2L15.53 8.17L17.5 8.7L15.53 9.23L15 11.2L14.47 9.23L12.5 8.7L14.47 8.17Z" fill="none" stroke="#525C6A" stroke-width=".6" stroke-linejoin="round"/></svg>';
  function band(st){return st==='premium'?'<i class="jhb">'+WORN+'</i>':''}
  // Menu item icons (bookcase, open scroll, closed scroll set by David; the rest are PLACEHOLDERS to fine-tune)
  var MI={
    shelf:'<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="2" width="18" height="20" rx="1.6" fill="#8A5A2B" stroke="#4A2E14" stroke-width="1"/><rect x="5" y="4" width="14" height="16" fill="#3B2412"/><rect x="5.6" y="5" width="2" height="4" fill="#D9534F"/><rect x="7.9" y="5.6" width="1.8" height="3.4" fill="#F0A13A"/><rect x="10" y="4.8" width="2.2" height="4.2" fill="#4F86C6"/><rect x="13.4" y="5.4" width="1.8" height="3.6" fill="#6FB27A"/><rect x="5.6" y="10.8" width="2" height="3.8" fill="#F2C14E"/><rect x="7.9" y="11.2" width="2" height="3.4" fill="#9B6FC6"/><rect x="10.2" y="10.6" width="1.8" height="4" fill="#D9534F"/><path d="M13 14.6l2.6-3.6 1.4 1-2.6 3.6z" fill="#4F86C6"/><rect x="5.6" y="16.4" width="2.2" height="3.6" fill="#4F86C6"/><rect x="8.1" y="16" width="1.8" height="4" fill="#6FB27A"/><rect x="13" y="16.6" width="2" height="3.4" fill="#F0A13A"/><rect x="15.3" y="16.2" width="2" height="3.8" fill="#D9534F"/><rect x="5" y="9" width="14" height="1.4" fill="#8A5A2B"/><rect x="5" y="14.6" width="14" height="1.4" fill="#8A5A2B"/></svg>',
    scrollOpen:'<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="6" y="4" width="12" height="16" fill="#F3E2B8" stroke="#8C5F14" stroke-width="1"/><path d="M8.5 8.2h7M8.5 10.7h7M8.5 13.2h5.5M8.5 15.7h6.4" stroke="#B08A4A" stroke-width="1" stroke-linecap="round"/><rect x="4" y="2.3" width="16" height="3.2" rx="1.6" fill="#E3C17E" stroke="#8C5F14" stroke-width="1"/><rect x="4" y="18.5" width="16" height="3.2" rx="1.6" fill="#E3C17E" stroke="#8C5F14" stroke-width="1"/></svg>',
    scrollClosed:'<svg viewBox="0 0 24 24" aria-hidden="true"><g transform="rotate(-28 12 12)"><path d="M12 16.4l-2 4.4M12 16.4l2.2 4.2" stroke="#B83A35" stroke-width="1.6" stroke-linecap="round"/><rect x="2.5" y="8" width="18" height="8" rx="4" fill="#F3E2B8" stroke="#8C5F14" stroke-width="1"/><ellipse cx="18.5" cy="12" rx="2" ry="4" fill="#E3C17E" stroke="#8C5F14" stroke-width="1"/><ellipse cx="18.5" cy="12" rx=".8" ry="1.6" fill="none" stroke="#8C5F14" stroke-width=".8"/><rect x="10.4" y="7.5" width="3.2" height="9" rx=".6" fill="#D9534F" stroke="#8C2B28" stroke-width=".7"/></g></svg>',
    lock:'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 11V8a4 4 0 0 1 8 0v3" fill="none" stroke="#8C5F14" stroke-width="2"/><rect x="5" y="10.5" width="14" height="10.5" rx="2.2" fill="#F2C14E" stroke="#8C5F14" stroke-width="1"/><circle cx="12" cy="15.2" r="1.5" fill="#8C5F14"/><path d="M12 15.6v2.6" stroke="#8C5F14" stroke-width="1.4" stroke-linecap="round"/></svg>',
    chat:'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5.5A2.5 2.5 0 0 1 6.5 3h11A2.5 2.5 0 0 1 20 5.5v8a2.5 2.5 0 0 1-2.5 2.5H11l-4.5 4v-4h0A2.5 2.5 0 0 1 4 13.5z" fill="#7FB3E8" stroke="#2F5A86" stroke-width="1" stroke-linejoin="round"/><circle cx="8.5" cy="9.5" r="1.1" fill="#2F5A86"/><circle cx="12" cy="9.5" r="1.1" fill="#2F5A86"/><circle cx="15.5" cy="9.5" r="1.1" fill="#2F5A86"/></svg>',
    key:'<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="8" cy="12" r="4.5" fill="#F2C14E" stroke="#8C5F14" stroke-width="1"/><circle cx="8" cy="12" r="1.6" fill="#8C5F14"/><path d="M12.3 12H21M18 12v3M20.5 12v2.2" stroke="#8C5F14" stroke-width="2" stroke-linecap="round"/></svg>',
    join:'<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="10" cy="8" r="4" fill="#F0A13A" stroke="#8C4F14" stroke-width="1"/><path d="M2.5 21a7.5 7.5 0 0 1 15 0z" fill="#F0A13A" stroke="#8C4F14" stroke-width="1" stroke-linejoin="round"/><circle cx="18.5" cy="6.5" r="4" fill="#6FB27A" stroke="#2F5E37" stroke-width="1"/><path d="M18.5 4.6v3.8M16.6 6.5h3.8" stroke="#fff" stroke-width="1.5" stroke-linecap="round"/></svg>',
    mail:'<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="2.5" y="5" width="19" height="14" rx="2.2" fill="#F3E2B8" stroke="#8C5F14" stroke-width="1"/><path d="M3.2 6.2l8.8 6.6 8.8-6.6" fill="none" stroke="#8C5F14" stroke-width="1.2" stroke-linejoin="round"/><circle cx="12" cy="12.6" r="2" fill="#D9534F" stroke="#8C2B28" stroke-width=".7"/></svg>',
    door:'<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="4" y="2.5" width="11" height="19" rx="1.2" fill="#A9784A" stroke="#4A2E14" stroke-width="1"/><circle cx="12.4" cy="12.4" r="1" fill="#F2C14E"/><path d="M14.5 12H21M18.2 9l2.9 3-2.9 3" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>'
  };
  function ic(k){return '<i class="jic">'+MI[k]+'</i>'}
  // Wraps a label (+ optional <small>) so the icon sits in its own column
  function lb(k,t){return ic(k)+'<span class="jtx">'+t+'</span>'}
  var LABEL={founding:'Founding member',premium:'Jonin Club member',free:'Free member'};
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
    if(s&&s.user&&s.pts&&s.home)introMaybe(s);
    try{if(!s||!s.user)premUI(null);else if(s.badge)premUI(s.badge)}catch(_){}
    var mine=s.home?'href="#mine" data-v="mine"':'href="/#mine"';
    var up=s.home?'<button type="button" class="jab jsu" data-auth="up"':'<a class="jab jsu" href="/#signup"';
    var upEnd=s.home?'</button>':'</a>';
    var inB=s.home?'<button type="button" class="jmi" role="menuitem" data-auth="in">'+lb('key','Sign in')+'</button>':'<a class="jmi" role="menuitem" href="/#signin">'+lb('key','Sign in')+'</a>';
    var fb='<button type="button" class="jmi" role="menuitem" data-fb data-fbname="Header profile menu">'+lb('chat','Send feedback<small>Notes we use earn scrolls</small>')+'</button>';
    if(!s.user){
      return '<div class="jac">'+up+' aria-haspopup="menu">'+'<span>'+(s.guest?'Sign up<span class="jx"> to save</span>':'Sign up')+'</span>'+CARET+upEnd+
        '<div class="jam" role="menu"><div class="jmp"><b>Free account</b><span>Save your collection and vote for the coolest cards. '+offerLine()+'</span></div>'+
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
        '<span class="jav">'+avatar(s,30)+(st==='premium'?band(st):st==='free'?'<i class="jbg">'+ICON[st]+'</i>':'')+'<i class="jdot"'+(UNREAD?'':' hidden')+' title="New message"></i></span>'+
        '<span class="jat">'+(ld?'<i class="jld"></i>':'<b>'+esc(name)+'</b>')+(rank?'<small>'+esc(rank)+'</small>':'')+'</span>'+CARET+'</a>'+
      '<div class="jam" role="menu">'+
        '<div class="jah st-'+st+'"><span class="jav big">'+avatar(s,48)+band(st)+'</span><div><b>'+esc(name||'Loading…')+'</b><span class="jst st-'+st+'">'+ICON[st]+LABEL[st]+'</span></div></div>'+
        (p?'<a class="jrk" href="/missions/" role="menuitem" style="display:block;text-decoration:none" title="See your missions"><div><span>Rank</span> <b>'+esc(rank)+'</b><span class="jpt">📜 '+pts+(pts===1?' scroll':' scrolls')+'</span></div><span class="jbar"><i style="width:'+pct+'%"></i></span>'+
          (p.next?'<small>'+(p.next_at-pts)+((p.next_at-pts)===1?' scroll':' scrolls')+' to '+esc(p.next)+'</small>':'<small>Top rank</small>')+'</a>':'')+
        nextRow(s)+
        '<a class="jmi" role="menuitem" '+mine+'>'+lb('shelf','My collection<small>Haves, wants, slabs and profile</small>')+'</a>'+
        '<a class="jmi" role="menuitem" '+(s.home?'href="#lists" data-v="mine" data-lmine':'href="/#lists"')+'>'+lb('scrollOpen','My lists<small>Your own card lists</small>')+'</a>'+
        '<button type="button" class="jmi" role="menuitem" data-jmsg>'+lb('mail','Messages<b class="jmn"'+(UNREAD?'':' hidden')+'>'+UNREAD+'</b><small>Questions from Jonin about your notes</small>')+'</button>'+
        '<a class="jmi" role="menuitem" href="/missions/">'+lb('scrollClosed','Missions<small>Earn scrolls and rank up</small>')+'</a>'+
        '<a class="jmi" role="menuitem" href="/leaderboard/">'+lb('scrollClosed','Leaderboard<small>Top members by scrolls</small>')+'</a>'+
        '<a class="jmi" role="menuitem" href="/missions/#m-inv">'+lb('join','Invite friends<small>Earn scrolls for each friend who joins</small>')+'</a>'+
        (st==='free'?'<a class="jmi jprem" role="menuitem" href="/club/">'+lb('lock','Join Jonin Club')+'</a>':'')+
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
    if(t.closest&&t.closest('[data-jmsg]')){closeAll();openMsgs();return}
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
  // ---- Jonin Club unlock on every page (2026-11-26) ----
  // Members (founding or premium) never see Jonin Club locks: the header Jonin Club button loses its lock and reads
  // "⭐ Founder" / "⭐ Jonin Club", static card pages swap the blurred teaser for real price estimates and sold listings,
  // and the "Every sale of this card" locks on list pages link to the card page instead. Signing out puts it back.
  // PLACEHOLDER wording ("Founder", "Your Jonin Club includes", "See sales →") for David to fine-tune.
  var EPN='mkevt=1&mkcid=1&mkrid=711-53200-19255-0&campid=5339262225&toolid=10001&customid=jonin-site';
  var PREM='';
  function money(v){v=+v;return '$'+(v>=100?Math.round(v).toLocaleString('en-US'):v.toFixed(2).replace(/\.00$/,''))}
  function sDate(d){try{return new Date(d).toLocaleDateString('en-US',{month:'short',day:'numeric'})}catch(_){return ''}}
  function premUI(b){
    var on=b==='founding'||b==='premium',key=on?b:'';if(key===PREM)return;var was=PREM;PREM=key;
    if(!on&&was&&document.querySelector('[data-unlocked]')){location.reload();return}
    document.documentElement.classList.toggle('jmem',on);
    each('.pn>.pnb',function(a){if(a.dataset.orig==null)a.dataset.orig=a.innerHTML;
      a.innerHTML=on?'<span aria-hidden="true">⭐</span>'+(b==='founding'?'Founder':'Jonin Club'):a.dataset.orig;a.classList.toggle('mem',on)});
    each('.pdd h4',function(h){if(h.dataset.orig==null)h.dataset.orig=h.textContent;h.textContent=on?'Your Jonin Club includes':h.dataset.orig});
    if(!on)return;
    each('a.pxlock',function(a){var row=a.closest('.mvrow'),art=row&&row.querySelector('.mvart');if(!art)return;
      a.href=art.getAttribute('href');a.innerHTML='<span>Every sale of this card, by edition, foil and grade</span><b>See sales →</b>';a.setAttribute('data-unlocked','')});
    each('a.pxt',unlockCard);
  }
  function each(sel,f){[].forEach.call(document.querySelectorAll(sel),f)}
  function unlockCard(a){
    var m=/[?&]card=([^&]+)/.exec(a.getAttribute('href')||''),s=session();if(!m||!s)return;
    var id=decodeURIComponent(m[1]),tok=s.access_token,box=document.createElement('div');
    box.className='pxreal';box.setAttribute('data-unlocked','');box.innerHTML='<p class="none">Loading prices…</p>';
    a.replaceWith(box);
    var sec=box.closest('.px'),h=sec&&sec.querySelector('h3');
    if(h)h.innerHTML='Price estimate<span>⭐ Jonin Club · by version</span>';
    var band=sec&&sec.querySelector('.band');if(band)band.remove();
    Promise.all([
      rest('/rest/v1/price_estimates?card_id=eq.'+encodeURIComponent(id)+'&select=printing,edition,grader,grade,estimate,sales_count,last_sold_at,last_price',tok).catch(function(){return null}),
      rest('/rest/v1/rpc/member_card_sales',tok,{p_card_id:id}).catch(function(){return []})
    ]).then(function(r){
      var rows=r[0],sales=r[1]||[];
      if(!rows){box.innerHTML='<p class="none">Could not load prices. Refresh to try again.</p>';return}
      if(!rows.length){box.innerHTML='<p class="none">No approved sales for this card yet.</p>';return}
      var vk=function(x){return [x.printing||'',x.edition||'',x.grader||'Raw',x.grade||''].join('|')},by={};
      sales.forEach(function(x){var k=vk(x);(by[k]=by[k]||[]).push(x)});
      rows.sort(function(a,b){return (a.edition!=='1st Edition')-(b.edition!=='1st Edition')||String(a.printing).localeCompare(String(b.printing))||((a.grader||'Raw')!=='Raw')-((b.grader||'Raw')!=='Raw')||(parseFloat(b.grade)||0)-(parseFloat(a.grade)||0)});
      box.innerHTML='<table>'+rows.map(function(x){
        var g=!x.grader||x.grader==='Raw'?'Raw':x.grader+' '+(x.grade||'');
        var lab=[x.edition==='1st Edition'?'1st Ed':x.edition,x.printing,g].filter(Boolean).map(esc).join(' · ');
        var sl=(by[vk(x)]||[]).map(function(y){var t=money(y.price)+' · '+esc(sDate(y.sold_at));
          return /^https:\/\//.test(y.url||'')?'<a href="'+esc(y.url+(y.url.indexOf('?')>-1?'&':'?')+EPN)+'" target="_blank" rel="sponsored noopener">'+t+' ↗</a>':'<a>'+t+'</a>'}).join('');
        return '<tr><td>'+lab+'</td><td><b>'+money(x.estimate)+'</b><small>'+x.sales_count+' sale'+(x.sales_count>1?'s':'')+' · last '+money(x.last_price)+(x.last_sold_at?' on '+esc(sDate(x.last_sold_at)):'')+'</small></td></tr>'+
          (sl?'<tr class="sl"><td colspan="2">'+sl+'</td></tr>':'')}).join('')+'</table><p class="none">Estimates lean on the newest sales. Tap a sale to open it on eBay.</p>';
    });
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
      rest('/rest/v1/memberships?user_id=eq.'+uid+'&select=active,until,founding,upgrade_notice',tok).catch(function(){return null}),
      rest('/rest/v1/rpc/my_xp',tok,{}).catch(function(){return null})
    ]).then(function(r){
      var p=r[0]&&r[0][0],m=r[1]&&r[1][0];
      if(p){base.handle=p.handle||base.handle;base.fav=p.fav_character||null;base.avatar=p.avatar||null}
      var on=false;if(r[1]){on=!!(m&&m.active&&(!m.until||new Date(m.until)>new Date()));base.badge=on?(m.founding?'founding':'premium'):null}
      if(r[2])base.pts=r[2];
      paint(base);cache(base);if(!(on&&m.upgrade_notice&&upgradeShow(m.upgrade_notice,tok)))introMaybe(base);
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

  // ---- invites: jonin.cards/?invite=<code> ----
  // Remember the code for 30 days; once the visitor is signed in, claim it once (Supabase claim_invite only accepts
  // accounts made in the last 3 days, never your own code, one inviter per account).
  var IK='jonin_invite';
  (function(){try{var m=/[?&]invite=([a-z0-9]{4,12})/i.exec(location.search);if(!m)return;
    var cur=ls(IK);if(!cur||cur.c!==m[1].toLowerCase())localStorage.setItem(IK,JSON.stringify({c:m[1].toLowerCase(),t:Date.now()}));
    var q=location.search.replace(/([?&])invite=[^&]*&?/i,'$1').replace(/[?&]$/,'');history.replaceState(null,'',location.pathname+q+location.hash)}catch(_){}})();
  var claiming=false;
  function claimInvite(){
    var iv=ls(IK);if(!iv||claiming)return;
    if(!iv.c||Date.now()-iv.t>30*864e5){try{localStorage.removeItem(IK)}catch(_){}return}
    var s=session();if(!s||(s.expires_at&&s.expires_at*1000<Date.now()+5000))return;
    claiming=true;
    rest('/rest/v1/rpc/claim_invite',s.access_token,{p_code:iv.c}).then(function(){try{localStorage.removeItem(IK)}catch(_){}})
      .catch(function(st){if(typeof st==='number'&&st!==401){try{localStorage.removeItem(IK)}catch(_){}}}).then(function(){claiming=false});
  }
  claimInvite();setInterval(claimInvite,5000);
  // ---- last seen (2026-11-26): tells Supabase this member opened a page, at most every 5 minutes (touch_seen). Shown on /admin/ → Accounts.
  var SK='jonin_seen';
  function seen(){var s=session();if(!s||(s.expires_at&&s.expires_at*1000<Date.now()+5000))return;var l=ls(SK);
    if(l&&l.u===s.user.id&&Date.now()-l.t<3e5)return;try{localStorage.setItem(SK,JSON.stringify({u:s.user.id,t:Date.now()}))}catch(_){}
    fetch(SUPA+'/rest/v1/rpc/touch_seen',{method:'POST',headers:{apikey:KEY,Authorization:'Bearer '+s.access_token,'Content-Type':'application/json'},body:'{}'}).catch(function(){})}
  seen();setInterval(seen,6e4);document.addEventListener('visibilitychange',function(){if(!document.hidden)seen()});
  window.addEventListener('storage',function(e){if(e.key===TK)claimInvite()});


  // ---- Scroll nudges (2026-11-26) ----
  // Most members hadn't found voting, so: a "Next mission" line under the rank card in the profile menu, and a one-time
  // "How scrolls work" popup for members with fewer than INTRO_UNDER characters voted. Amounts come from my_xp.rules (Supabase xp_rules).
  // PLACEHOLDERS for David: popup shows 4s after a page opens, at most INTRO_MAX times, "Later" waits INTRO_GAP days.
  var INTRO_UNDER=3,INTRO_MAX=3,INTRO_GAP=7*864e5,CHARS=null;
  function chars(){if(CHARS)return CHARS;var c=ls('jonin_chars');if(c&&Date.now()-c.t<864e5){CHARS=c.l;return CHARS}
    fetch('/chars.json').then(function(r){return r.json()}).then(function(l){CHARS=l.map(function(x){return [x.slug,x.label]});try{localStorage.setItem('jonin_chars',JSON.stringify({t:Date.now(),l:CHARS}))}catch(_){}}).catch(function(){});
    return null}
  function scr(n){return '+'+n+' 📜'}
  function nextMission(s){var p=s&&s.pts;if(!p)return null;var R=p.rules||{},v={},i,L=chars()||[];(p.voted||[]).forEach(function(c){v[c]=1});
    var nm=function(sl){for(var j=0;j<L.length;j++)if(L[j][0]===sl)return L[j][1];return sl.charAt(0).toUpperCase()+sl.slice(1).replace(/-./g,function(m){return ' '+m.charAt(1).toUpperCase()})};
    var has=function(sl){if(!L.length)return true;for(var j=0;j<L.length;j++)if(L[j][0]===sl)return true;return false};
    var pick=s.fav&&!v[s.fav]&&has(s.fav)?s.fav:null;
    if(!pick)for(i=0;i<L.length;i++)if(!v[L[i][0]]){pick=L[i][0];break}
    if(pick&&R.vote_character)return {href:'/character/'+pick+'/#vote-top',t:'Vote for '+nm(pick)+'’s coolest cards',n:R.vote_character,ch:pick,name:nm(pick)};
    if(!p.cards_100&&R.cards_100)return {href:'/#mine',t:'Log 100 cards ('+Math.min(100,p.cards||0)+'/100)',n:R.cards_100};
    if(R.invite_signup)return {href:'/missions/#m-inv',t:'Invite a friend',n:R.invite_signup};
    return null}
  function nextRow(s){var m=nextMission(s);if(!m)return '';
    return '<a class="jnx" role="menuitem" href="'+esc(m.href)+'"><span>🎯 Next mission</span><b>'+esc(m.t)+'</b><i>'+scr(m.n)+'</i></a>'}
  (function(){var c=document.createElement('style');c.textContent=
    '.jnx{display:grid;grid-template-columns:1fr auto;gap:0 8px;margin:-2px 8px 6px;padding:8px 10px;border-radius:10px;border:1px dashed #F2C14E;background:rgba(242,193,78,.08);text-decoration:none;color:var(--ink,#FFF4E6)}'+
    '.jnx:hover{background:rgba(242,193,78,.16)}.jnx span{grid-column:1/-1;font-size:11px;letter-spacing:.5px;color:#F2C14E;font-weight:700}.jnx b{font-size:13.5px;font-weight:600}.jnx i{font-style:normal;font:800 13px "Baloo 2",sans-serif;color:#F2C14E;align-self:center}'+
    '.jsi .jmbox{width:min(460px,100%)}.jsi ul{list-style:none;margin:2px 0 4px;padding:0;display:grid;gap:6px}.jsi li{display:flex;justify-content:space-between;gap:10px;padding:9px 12px;border-radius:10px;background:var(--panel,#241E2D);border:1px solid var(--edge,#3A3046)}'+
    '.jsi li b{font:800 14px "Baloo 2",sans-serif;color:#F2C14E;white-space:nowrap}.jsi li small{display:block;color:var(--mute,#B8AEA6);font-size:12px}.jsi .jsr{font-size:15px}.jsi .jsr b{color:#F2C14E}'+
    '.jsi .jsb{display:flex;gap:8px;flex-wrap:wrap;align-items:center}.jsi .jsb a{text-decoration:none;display:inline-flex;align-items:center;justify-content:center;padding:0 16px}.jsi .jsl{background:none;border:0;color:var(--mute,#B8AEA6);font:14px Inter,system-ui,sans-serif;cursor:pointer;margin-left:auto}';
    document.head.appendChild(c)})();
  // ---- Upgrade popup (David, 2026-11-26) ----
  // When David gives someone Jonin Club or Founding member from /admin/, Supabase sets memberships.upgrade_notice.
  // The next page they open while signed in shows this once; dismiss_upgrade_notice clears it as soon as it shows.
  // PLACEHOLDER wording for David to change.
  var UPG={founding:{h:'You’re a Founding member',p:'You’ve been made one of Jonin’s founding members. Jonin Club is yours free, forever, and your profile now shows the founding ring.'},
           premium:{h:'Welcome to Jonin Club',p:'You’ve been upgraded to Jonin Club. Everything below is unlocked on your account now.'}};
  // Look: gold-edged box with a slow shine, a big cut gem badge, twinkling diamonds and diamond bullets.
  // Founding = gold gem, Jonin Club = violet gem (PLACEHOLDER colors). Motion is off for people who ask for reduced motion.
  var GEM=function(id,a,b,c){return '<svg viewBox="0 0 64 56" aria-hidden="true"><defs><linearGradient id="'+id+'" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="'+a+'"/><stop offset=".55" stop-color="'+b+'"/><stop offset="1" stop-color="'+c+'"/></linearGradient></defs>'+
    '<path d="M14 2h36l14 16-32 36L0 18z" fill="url(#'+id+')"/><path d="M0 18h64M14 2l8 16 10 36M50 2l-8 16-10 36M22 18 32 2l10 16" fill="none" stroke="rgba(255,255,255,.55)" stroke-width="1.4" stroke-linejoin="round"/>'+
    '<path d="M14 2h36l-8 16H22z" fill="rgba(255,255,255,.28)"/></svg>'};
  var DIA='<svg viewBox="0 0 10 10" aria-hidden="true"><path d="M5 0 10 5 5 10 0 5z"/></svg>';
  function upgradeCss(){if(upgradeCss.on)return;upgradeCss.on=1;var c=document.createElement('style');c.textContent=
    '.jup .jmbox{--g1:#FFE7A3;--g2:#F2C14E;--g3:#B8860B;width:min(470px,100%);overflow:hidden;text-align:center;align-items:stretch;border:2px solid transparent;'+
      'background:linear-gradient(var(--deep,#17121D),var(--deep,#17121D)) padding-box,linear-gradient(135deg,var(--g1),var(--g3) 40%,var(--g1) 60%,var(--g3)) border-box;'+
      'box-shadow:0 0 0 1px rgba(242,193,78,.15),0 0 60px -10px var(--g2),0 30px 80px -20px rgba(0,0,0,.8);animation:jupIn .5s cubic-bezier(.2,1.4,.4,1) both}'+
    '.jup.club .jmbox{--g1:#E7D4FF;--g2:#A86BFF;--g3:#5B2BB5}'+
    '.jup .jmbox:before{content:"";position:absolute;inset:0;background:radial-gradient(120% 60% at 50% 0,color-mix(in srgb,var(--g2) 28%,transparent),transparent 70%);pointer-events:none}'+
    '.jup .jmbox:after{content:"";position:absolute;top:0;bottom:0;width:40%;left:-60%;background:linear-gradient(100deg,transparent,rgba(255,255,255,.13),transparent);transform:skewX(-18deg);animation:jupShine 3.2s 1s ease-in-out infinite;pointer-events:none}'+
    '.jup .jgem{position:relative;width:92px;height:92px;margin:4px auto 2px;display:grid;place-items:center;border-radius:50%;background:radial-gradient(circle,color-mix(in srgb,var(--g2) 40%,transparent),transparent 68%)}'+
    '.jup .jgem>svg{width:64px;height:56px;filter:drop-shadow(0 4px 14px var(--g2));animation:jupFloat 3s ease-in-out infinite}'+
    '.jup .jsp{position:absolute;fill:var(--g1);opacity:0;animation:jupTw 2.4s ease-in-out infinite}.jup .jsp svg{display:block;width:100%;height:100%}'+
    '.jup .jkick{font:800 12px/1 Inter,system-ui,sans-serif;letter-spacing:.16em;text-transform:uppercase;color:var(--g2)}'+
    '.jup h2{font-size:28px;line-height:1.1;background:linear-gradient(90deg,var(--g1),var(--g2),var(--g1));-webkit-background-clip:text;background-clip:text;color:transparent}'+
    '.jup .jsr{max-width:380px;margin:0 auto}.jup ul{text-align:left}.jup li{align-items:center;justify-content:flex-start!important;border-color:color-mix(in srgb,var(--g2) 30%,var(--edge,#3A3046))!important}'+
    '.jup li i{flex:0 0 12px;width:12px;height:12px;fill:var(--g2);filter:drop-shadow(0 0 4px var(--g2))}.jup li i svg{display:block;width:100%;height:100%}'+
    '.jup .jsb{justify-content:center}.jup .jsb .jsl{margin-left:0}'+
    '.jup .jmgo{background:linear-gradient(135deg,var(--g1),var(--g2) 45%,var(--g3));color:#1B1622;font-weight:800;box-shadow:0 6px 20px -6px var(--g2)}'+
    '@keyframes jupIn{from{opacity:0;transform:scale(.85) translateY(12px)}}@keyframes jupShine{0%{left:-60%}55%,100%{left:130%}}'+
    '@keyframes jupFloat{50%{transform:translateY(-4px) rotate(-3deg)}}@keyframes jupTw{0%,100%{opacity:0;transform:scale(.4) rotate(0)}50%{opacity:1;transform:scale(1) rotate(45deg)}}'+
    '@media (prefers-reduced-motion:reduce){.jup .jmbox,.jup .jmbox:after,.jup .jgem>svg,.jup .jsp{animation:none}.jup .jsp{opacity:.8}}';
    document.head.appendChild(c)}
  function upgradeShow(kind,tok){var u=UPG[kind];if(!u||upgradeShow.on||/^\/admin\//.test(location.pathname))return false;upgradeShow.on=1;
    rest('/rest/v1/rpc/dismiss_upgrade_notice',tok,{}).catch(function(){});upgradeCss();
    var f=kind==='founding',sp=[[10,6,16,0],[80,9,12,.6],[4,26,10,1.2],[93,24,16,.3],[3,58,12,1.6],[94,62,10,.9],[28,4,9,2],[68,3,10,1.4],[5,88,9,.5],[93,90,12,1.8]].map(function(x){
      return '<span class="jsp" style="left:'+x[0]+'%;top:'+x[1]+'%;width:'+x[2]+'px;height:'+x[2]+'px;animation-delay:'+x[3]+'s">'+DIA+'</span>'}).join('');
    var d=document.createElement('div');d.className='jmo jsi jup'+(f?'':' club');
    d.innerHTML='<div class="jmbox" role="dialog" aria-modal="true" aria-labelledby="juph">'+sp+'<button class="jmx" type="button" aria-label="Close">×</button>'+
      '<div class="jgem">'+(f?GEM('jgf','#FFF3C4','#F2C14E','#9A6B00'):GEM('jgc','#F1E6FF','#A86BFF','#4A1F9E'))+'</div>'+
      '<div class="jkick">'+(f?'Founding member':'Jonin Club')+'</div><h2 id="juph">'+u.h+'</h2><p class="jsr">'+u.p+'</p><ul>'+
      ['Exact prices by edition, foil and grade','Every sold listing, linked to the sale','Price estimates and sort by market value','Alerts for the cards you’re hunting','Your collection value, a spreadsheet export and a badge']
        .map(function(t){return '<li><i>'+DIA+'</i><span>'+t+'</span></li>'}).join('')+
      '</ul><div class="jsb"><a class="jmgo" href="/#mine">See my collection</a><button type="button" class="jsl">Close</button></div></div>';
    var go=function(){if(!document.body)return setTimeout(go,50);document.body.appendChild(d);if(window.jtrack)jtrack('upgrade-popup',{kind:kind})};go();
    var close=function(){d.remove()};d.addEventListener('click',function(e){if(e.target===d||e.target.closest('.jmx,.jsl'))close()});
    document.addEventListener('keydown',function f(e){if(e.key==='Escape'){close();document.removeEventListener('keydown',f)}});
    return true}
  function introMaybe(st){
    if(!st||!st.user||!st.pts||/^\/(missions|admin)\//.test(location.pathname))return;
    var p=st.pts,R=p.rules||{};if((p.voted||[]).length>=INTRO_UNDER||!R.vote_character)return;
    var k='jonin_sintro_'+st.uid,r=ls(k)||{n:0,t:0};if(r.n>=INTRO_MAX||Date.now()-r.t<INTRO_GAP)return;
    if(introMaybe.on)return;introMaybe.on=1;
    setTimeout(function(){
      if(document.querySelector('.jmo:not([hidden]),.jfb-ov:not([hidden]),dialog[open]'))return; // never on top of another popup
      try{localStorage.setItem(k,JSON.stringify({n:r.n+1,t:Date.now()}))}catch(_){}
      var m=nextMission(st),nC=(CHARS||[]).length||40,xp=p.xp||0,d=document.createElement('div');d.className='jmo jsi';
      d.innerHTML='<div class="jmbox" role="dialog" aria-modal="true" aria-labelledby="jsih"><button class="jmx" type="button" aria-label="Close">×</button>'+
        '<h2 id="jsih">📜 Earn scrolls, rank up</h2><p class="jsr">You’re <b>'+esc(p.rank||'')+'</b> with '+xp+(xp===1?' scroll':' scrolls')+(p.next?'. '+(p.next_at-xp)+' more to reach <b>'+esc(p.next)+'</b>.':'.')+'</p>'+
        '<p>Scrolls show your rank next to your name. Here’s how to earn them:</p><ul>'+
        '<li><span>Vote for each character’s coolest cards<small>3 votes per character, '+nC+' characters</small></span><b>'+scr(R.vote_character)+' each</b></li>'+
        (R.cards_100?'<li><span>Log 100 cards in your collection<small>'+Math.min(100,p.cards||0)+' of 100 so far</small></span><b>'+scr(R.cards_100)+'</b></li>':'')+
        (R.invite_signup?'<li><span>Invite a friend who joins</span><b>'+scr(R.invite_signup)+' each</b></li>':'')+
        (R.feedback_accepted?'<li><span>Send feedback we use<small>Fixes, missing cards, ideas</small></span><b>'+scr(R.feedback_accepted)+' each</b></li>':'')+
        '</ul><div class="jsb">'+(m&&m.ch?'<a class="jmgo" href="'+esc(m.href)+'">Vote on '+esc(m.name)+'’s cards</a>':'')+'<a class="jmgo" style="background:var(--panel,#241E2D);border:1px solid var(--edge,#3A3046)" href="/missions/">All missions</a><button type="button" class="jsl">Later</button></div></div>';
      document.body.appendChild(d);if(window.jtrack)jtrack('scrolls-intro',{});
      var close=function(){d.remove()};d.addEventListener('click',function(e){if(e.target===d||e.target.closest('.jmx,.jsl'))close();else if(e.target.closest('a')&&window.jtrack)jtrack('scrolls-intro-click',{to:e.target.closest('a').getAttribute('href')})});
      document.addEventListener('keydown',function f(e){if(e.key==='Escape'){close();document.removeEventListener('keydown',f)}});
    },4000);
  }

  // ---- Messages (2026-11-26) ----
  // David can message members from /admin/ (mostly follow-up questions about their feedback notes). Members see a red dot
  // on their profile button, a count on Messages in the menu, and can reply here. Supabase: my_unread_messages, my_messages,
  // send_message (replies only once David has written; one message per 10 seconds). jonin.cards/#messages opens it.
  var UNREAD=0;
  (function(){var c=document.createElement('style');c.textContent=
    '.jdot{position:absolute;top:-2px;right:-2px;width:10px;height:10px;border-radius:50%;background:#E5322D;box-shadow:0 0 0 2px var(--bg,#1B1622)}.jdot[hidden],.jmn[hidden]{display:none}'+
    '.jmn{display:inline-block;margin-left:6px;min-width:17px;padding:0 5px;border-radius:99px;background:#E5322D;color:#fff;font:700 11px/17px Inter,system-ui,sans-serif;text-align:center;vertical-align:1px}'+
    '.jmo{position:fixed;inset:0;z-index:1000;background:rgba(10,7,14,.82);backdrop-filter:blur(6px);-webkit-backdrop-filter:blur(6px);display:flex;align-items:center;justify-content:center;padding:16px}'+
    '.jmo[hidden]{display:none}.jmbox{position:relative;width:min(480px,100%);max-height:100%;display:flex;flex-direction:column;gap:10px;background:var(--deep,#17121D);border:1px solid var(--edge2,#30283A);border-radius:18px;padding:20px;color:var(--ink,#FFF4E6);font:14px/1.45 Inter,system-ui,sans-serif;box-shadow:0 30px 80px -20px rgba(0,0,0,.8)}'+
    '.jmbox h2{margin:0;font:800 24px "Baloo 2",sans-serif}.jmbox p{margin:0;color:var(--mute,#B8AEA6)}.jmx{position:absolute;top:8px;right:10px;background:none;border:0;color:var(--mute,#B8AEA6);font-size:20px;cursor:pointer;padding:6px}'+
    '.jml{display:grid;gap:8px;overflow-y:auto;min-height:80px;max-height:52vh;padding:2px}.jmb{max-width:85%;padding:9px 12px;border-radius:12px;white-space:pre-wrap;word-wrap:break-word}'+
    '.jmb.a{justify-self:start;background:var(--panel,#241E2D);border:1px solid var(--edge,#3A3046)}.jmb.m{justify-self:end;background:var(--red,#B5121B);color:#fff}'+
    '.jmb small{display:block;margin-top:3px;font-size:11px;opacity:.75}.jmq{display:block;margin-bottom:6px;padding:6px 8px;border-left:3px solid var(--acc,#F57C00);background:rgba(255,255,255,.04);border-radius:4px;font-size:12.5px;color:var(--mute,#B8AEA6)}'+
    '.jmbox textarea{background:var(--panel,#241E2D);border:1px solid var(--edge,#3A3046);border-radius:10px;padding:10px 12px;color:var(--ink,#FFF4E6);font:15px/1.45 Inter,system-ui,sans-serif;outline:none;width:100%;box-sizing:border-box;resize:vertical;min-height:70px}'+
    '.jmbox textarea:focus{border-color:var(--red,#B5121B)}.jmgo{min-height:42px;border-radius:10px;background:var(--red,#B5121B);border:0;color:var(--ont,#fff);font:600 15px Inter,system-ui,sans-serif;cursor:pointer}.jmgo:disabled{opacity:.6}'+
    '.jme{font-size:13px;min-height:18px}.jme.err{color:#ff8b8b}';
    document.head.appendChild(c)})();
  function setUnread(n){UNREAD=n||0;each('.jdot',function(d){d.hidden=!UNREAD});each('.jmn',function(b){b.hidden=!UNREAD;b.textContent=UNREAD})}
  var lastPoll=0;
  function pollUnread(force){var s=session();if(!s){setUnread(0);return}if(s.expires_at&&s.expires_at*1000<Date.now()+5000)return;
    if(!force&&Date.now()-lastPoll<55e3){setUnread(UNREAD);return}lastPoll=Date.now();
    rest('/rest/v1/rpc/my_unread_messages',s.access_token,{}).then(function(n){setUnread(typeof n==='number'?n:0)}).catch(function(){})}
  function mDate(d){try{return new Date(d).toLocaleString('en-US',{month:'short',day:'numeric',hour:'numeric',minute:'2-digit'})}catch(_){return ''}}
  var MO=null;
  function openMsgs(){var s=session();if(!s){location.href='/#signin';return}
    if(!MO){MO=document.createElement('div');MO.className='jmo';MO.hidden=true;
      MO.innerHTML='<div class="jmbox" role="dialog" aria-modal="true" aria-labelledby="jmh"><button class="jmx" type="button" aria-label="Close">×</button><h2 id="jmh">Messages</h2><p>Questions from David at Jonin, usually about feedback you sent.</p><div class="jml"></div><form class="jmf"><textarea name="b" maxlength="2000" placeholder="Write a reply…"></textarea><div class="jme"></div><button class="jmgo">Send</button></form></div>';
      document.body.appendChild(MO);
      MO.addEventListener('click',function(e){if(e.target===MO||e.target.closest('.jmx'))MO.hidden=true});
      document.addEventListener('keydown',function(e){if(e.key==='Escape'&&MO&&!MO.hidden)MO.hidden=true});
      MO.querySelector('.jmf').onsubmit=function(e){e.preventDefault();var f=e.target,b=f.b.value.trim(),er=MO.querySelector('.jme'),s=session();if(!b||!s)return;
        f.querySelector('button').disabled=true;er.className='jme';er.textContent='';
        fetch(SUPA+'/rest/v1/rpc/send_message',{method:'POST',headers:{apikey:KEY,Authorization:'Bearer '+s.access_token,'Content-Type':'application/json'},body:JSON.stringify({p_body:b})})
          .then(function(r){return r.json().then(function(j){if(!r.ok)throw j;return j})})
          .then(function(){f.b.value='';fillMsgs()}).catch(function(j){er.className='jme err';er.textContent=(j&&j.message)||'Could not send. Try again.'})
          .then(function(){f.querySelector('button').disabled=false})};
      MO.querySelector('textarea').addEventListener('keydown',function(e){if(e.key==='Enter'&&(e.metaKey||e.ctrlKey))MO.querySelector('.jmf').requestSubmit()});
    }
    MO.hidden=false;MO.querySelector('.jml').innerHTML='<p>Loading…</p>';fillMsgs();
  }
  function fillMsgs(){var s=session(),l=MO.querySelector('.jml'),f=MO.querySelector('.jmf');if(!s)return;
    rest('/rest/v1/rpc/my_messages',s.access_token,{}).then(function(d){
      var ms=d.messages||[],notes=d.notes||{},shown={};
      f.hidden=!ms.some(function(m){return m.from_admin});
      l.innerHTML=ms.length?ms.map(function(m){var q='';
        if(m.from_admin&&m.feedback_id&&notes[m.feedback_id]&&!shown[m.feedback_id]){shown[m.feedback_id]=1;q='<span class="jmq">Your note: “'+esc(notes[m.feedback_id].message)+'”</span>'}
        return '<div class="jmb '+(m.from_admin?'a':'m')+'">'+q+esc(m.body)+'<small>'+(m.from_admin?'David · Jonin':'You')+' · '+esc(mDate(m.created_at))+'</small></div>'}).join('')
        :'<p>No messages yet. If David has a question about a note you sent, it shows up here.</p>';
      l.scrollTop=l.scrollHeight;setUnread(0);
    }).catch(function(){l.innerHTML='<p>Could not load your messages. Refresh to try again.</p>'});
  }
  pollUnread(true);setInterval(function(){if(!document.hidden)pollUnread()},6e4);
  document.addEventListener('visibilitychange',function(){if(!document.hidden)pollUnread()});
  window.addEventListener('storage',function(e){if(e.key===TK)pollUnread(true)});
  function hashOpen(){if(location.hash==='#messages'){if(session())openMsgs();try{history.replaceState(null,'',location.pathname+location.search)}catch(_){}}}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',hashOpen);else setTimeout(hashOpen,0);

  window.JoninAcct={html:html,cache:cache,cached:function(){return ls(CK)},icon:ICON,label:LABEL,refresh:function(){LAST='';load()}};
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',auto);else auto();
})();
