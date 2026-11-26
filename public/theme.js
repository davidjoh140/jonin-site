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
  var s=document.createElement('script');
  s.defer=true;s.src='https://cloud.umami.is/script.js';
  s.setAttribute('data-website-id','8f5abd87-d29c-4e49-8544-c1ca76ff15b0');
  s.setAttribute('data-domains','jonin.cards');
  document.head.appendChild(s);
})();
