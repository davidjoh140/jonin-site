/* Character theme picker for jonin.cards. Load in <head> (no defer) so the theme applies before first paint. */
(function(){
  var T=[
    {id:'jonin',f:'/apple-touch-icon.png',  n:'Jonin',   d:'Night & Akatsuki red', bg:'#1B1622',a:'#B5121B',c:'#F57C00'},
    {id:'naruto',f:'/theme-faces/naruto.webp', n:'Naruto',  d:'Orange & navy',        bg:'#17130F',a:'#FF7A00',c:'#263A6E'},
    {id:'sasuke',f:'/theme-faces/sasuke.webp', n:'Sasuke',  d:'Purple & Chidori blue',bg:'#12121F',a:'#6A3FD6',c:'#7FB2FF'},
    {id:'itachi',f:'/theme-faces/itachi.webp', n:'Itachi',  d:'Black & crimson moon', bg:'#0D0A0B',a:'#C3141E',c:'#E5484D'},
    {id:'kakashi',f:'/theme-faces/kakashi.webp',n:'Kakashi', d:'Silver & steel blue',  bg:'#12171B',a:'#3F6E86',c:'#B8D5E4'},
    {id:'gaara',f:'/theme-faces/gaara.webp',  n:'Gaara',   d:'Sand & brick',         bg:'#1A1410',a:'#A8322A',c:'#D9A65A'},
    {id:'hinata',f:'/theme-faces/hinata.webp', n:'Hinata',  d:'Lavender',             bg:'#15142A',a:'#7B67D1',c:'#C4B2F5'},
    {id:'sakura',f:'/theme-faces/sakura.webp', n:'Sakura',  d:'Cherry blossom pink',  bg:'#1A1216',a:'#D94B7F',c:'#F48FB1'},
    {id:'leaf',f:'/theme-faces/rock-lee.webp',   n:'Hidden Leaf',d:'Forest green',      bg:'#0F1712',a:'#2E8B4A',c:'#7FCB6B'}
  ];
  var K='jtheme',root=document.documentElement;
  function get(){try{return localStorage.getItem(K)||'jonin'}catch(_){return 'jonin'}}
  function find(id){for(var i=0;i<T.length;i++)if(T[i].id===id)return T[i];return T[0]}
  function apply(id){
    var t=find(id);
    if(t.id==='jonin')root.removeAttribute('data-theme');else root.setAttribute('data-theme',t.id);
    var m=document.querySelector('meta[name=theme-color]');if(m)m.setAttribute('content',t.bg);
    return t;
  }
  apply(get());
  window.JONIN_THEMES=T;
  window.joninSetTheme=function(id){var t=apply(id);try{localStorage.setItem(K,t.id)}catch(_){}var b=document.querySelector('.tp .tpb');if(b){b.querySelector('.tsw').setAttribute('style',st(t));b.querySelector('.tpn').textContent=t.n;document.querySelectorAll('.tp [data-t]').forEach(function(y){y.setAttribute('aria-checked',y.getAttribute('data-t')===t.id)})}return t.id};
  function st(t){return '--a:'+t.bg+';--b:'+t.a+';--c:'+t.c+";--f:url('"+t.f+"')"}
  function sw(t){return 'style="'+st(t)+'"'}
  function build(){
    var hw=document.querySelector('header .hw');if(!hw||hw.querySelector('.tp')||hw.querySelector('#acct'))return; // pages with the profile button keep the theme in its menu
    var cur=find(get());
    var w=document.createElement('div');w.className='tp';
    w.innerHTML='<button type="button" class="tpb" aria-haspopup="menu" aria-expanded="false" aria-label="Theme: '+cur.n+'" title="Change theme"><span class="tsw" '+sw(cur)+'></span><span class="tpn">'+cur.n+'</span></button>'+
      '<div class="tpl" role="menu" hidden>'+T.map(function(t){return '<button type="button" role="menuitemradio" data-t="'+t.id+'" aria-checked="'+(t.id===cur.id)+'"><span class="tsw" '+sw(t)+'></span><span>'+t.n+'<small>'+t.d+'</small></span></button>'}).join('')+'</div>';
    var sell=hw.querySelector('.sell');if(sell)hw.insertBefore(w,sell);else hw.appendChild(w);
    var b=w.querySelector('.tpb'),l=w.querySelector('.tpl');
    function open(o){l.hidden=!o;b.setAttribute('aria-expanded',o);if(o){var s=l.querySelector('[aria-checked=true]')||l.querySelector('button');s.focus()}}
    b.addEventListener('click',function(){open(l.hidden)});
    l.addEventListener('click',function(ev){
      var x=ev.target.closest('[data-t]');if(!x)return;
      var t=apply(x.getAttribute('data-t'));try{localStorage.setItem(K,t.id)}catch(_){}
      l.querySelectorAll('[data-t]').forEach(function(y){y.setAttribute('aria-checked',y===x)});
      b.querySelector('.tsw').setAttribute('style',st(t));
      b.querySelector('.tpn').textContent=t.n;b.setAttribute('aria-label','Theme: '+t.n);
      open(false);b.focus();
    });
    l.addEventListener('keydown',function(ev){
      var bs=[].slice.call(l.querySelectorAll('button')),i=bs.indexOf(document.activeElement);
      if(ev.key==='Escape'){open(false);b.focus()}
      else if(ev.key==='ArrowDown'){ev.preventDefault();bs[(i+1)%bs.length].focus()}
      else if(ev.key==='ArrowUp'){ev.preventDefault();bs[(i-1+bs.length)%bs.length].focus()}
    });
    document.addEventListener('click',function(ev){if(!w.contains(ev.target)&&!l.hidden)open(false)});
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',build);else build();
})();
/* Umami visitor analytics (cloud.umami.is, Jonin site). theme.js loads on every public page, so this covers the whole site. */
(function(){
  if(document.querySelector('script[data-website-id]'))return;
  if(window.top!==window)return;   // the card page's embedded collection panel isn't a page view
  var s=document.createElement('script');
  s.defer=true;s.src='https://cloud.umami.is/script.js';
  s.setAttribute('data-website-id','8f5abd87-d29c-4e49-8544-c1ca76ff15b0');
  s.setAttribute('data-domains','jonin.cards');
  document.head.appendChild(s);
})();
/* Visitor tracking for sign-ups (Umami custom events) and the "New to Jonin?" box.
   - Remembers the first page a visitor ever landed on (and where from: google, instagram...) for 30 days,
     plus this visit's landing page, and sends them with every event so Umami shows which pages bring members.
   - window.jtrack(name, props) sends an event; links with data-jt="name" send one on click (data-jt-* become props).
   - "signup" fires once per new account (account made in the last 30 minutes), whichever sign-up form was used. */
(function(){
  var AUTH='sb-cfzpayanhvvqtkuqfgof-auth-token';
  function ls(k,v){try{if(v===undefined)return localStorage.getItem(k);localStorage.setItem(k,v)}catch(e){return null}}
  function ss(k,v){try{if(v===undefined)return sessionStorage.getItem(k);sessionStorage.setItem(k,v)}catch(e){return null}}
  function src(){var r='';try{r=document.referrer?new URL(document.referrer).hostname:''}catch(e){}
    if(!r||/(^|\.)jonin\.cards$/.test(r))return r?'internal':'direct';
    var m=r.match(/google|bing|duckduckgo|yahoo|instagram|facebook|reddit|discord|youtube|tiktok|twitter|x\.com/);return m?m[0].replace('.com',''):r}
  var path=location.pathname;
  if(!ss('jt_land')){ss('jt_land',path);ss('jt_src',src())}
  var first=null;try{first=JSON.parse(ls('jt_first')||'null')}catch(e){}
  if(!first||Date.now()-first.t>30*864e5){first={p:path,s:ss('jt_src')||src(),t:Date.now()};ls('jt_first',JSON.stringify(first))}
  function base(){return {page:path,landing:ss('jt_land')||path,source:ss('jt_src')||'',first_landing:first.p,first_source:first.s}}
  var q=[];
  window.jtrack=function(name,props){var d=base();for(var k in props||{})d[k]=props[k];
    if(window.umami&&umami.track)umami.track(name,d);else q.push([name,d])};
  var tries=0,iv=setInterval(function(){if(window.umami&&umami.track){clearInterval(iv);q.forEach(function(x){umami.track(x[0],x[1])});q=[]}else if(++tries>40)clearInterval(iv)},500);
  document.addEventListener('click',function(ev){var l=ev.target.closest&&ev.target.closest('a[href]');
    if(l&&!l.hasAttribute('data-jt')){var h=l.getAttribute('href')||'';
      var n=/sell\.jonin\.cards/.test(h)?'sell-click':/^\/club\//.test(h)?'premium-click':/instagram\.com/.test(h)?'instagram-click':'';
      if(n)jtrack(n,{})}},true);
  document.addEventListener('click',function(ev){var a=ev.target.closest&&ev.target.closest('[data-jt]');if(!a)return;
    var p={};for(var i=0;i<a.attributes.length;i++){var n=a.attributes[i].name;if(n.indexOf('data-jt-')===0)p[n.slice(8)]=a.attributes[i].value}
    jtrack(a.getAttribute('data-jt'),p)},true);
  function user(){try{var s=JSON.parse(ls(AUTH)||'null');return s&&s.user||null}catch(e){return null}}
  function checkSignup(){var u=user();if(!u||!u.created_at)return;var done=ls('jt_su')||'';
    if(done.indexOf(u.id)>=0)return;
    if(Date.now()-new Date(u.created_at).getTime()<30*60e3){ls('jt_su',done+','+u.id);
      jtrack('signup',{method:(u.app_metadata&&u.app_metadata.provider)||'email'})}else ls('jt_su',done+','+u.id)}
  checkSignup();setInterval(function(){checkSignup();newbie()},5000);
  function newbie(){var signed=!!user();document.querySelectorAll('[data-newbie]').forEach(function(el){el.hidden=signed})}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',newbie);else newbie();
  window.addEventListener('storage',function(ev){if(ev.key===AUTH){newbie();checkSignup()}});
  /* Reading time: counts seconds the tab is visible and the visitor has scrolled, tapped, moved the mouse or typed in the
     last 60s. Sends "read-30s" and "read-2m" once per page, so a long read on one page shows as engaged, not as a
     zero-second bounce. */
  var active=0,last=Date.now(),sent={};
  ['scroll','mousemove','keydown','touchstart','click','wheel'].forEach(function(t){window.addEventListener(t,function(){last=Date.now()},{passive:true})});
  setInterval(function(){if(document.hidden||Date.now()-last>60e3)return;active+=5;
    if(active>=30&&!sent.a){sent.a=1;jtrack('read-30s',{})}
    if(active>=120&&!sent.b){sent.b=1;jtrack('read-2m',{})}},5000);
})();
