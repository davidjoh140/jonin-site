/* Naruto music for jonin.cards. Loaded on every page by theme.js.
   Tapping the 🎵 button turns the page into a "music shell": the site keeps running inside a full-screen
   frame (named "jsite") and a small player card floats in the corner of the outer page. Clicking around the
   site only changes the frame, so the music never stops between pages. Works the same on phones (one tab,
   no pop-up). The address bar and tab title follow the page you're on, and Back/Forward work as normal.
   YouTube's rules: the player must stay visible and at least 200x200, so the card always shows the video.
   PLACEHOLDERS for David: playlist id, button corner (bottom-right), card size. */
(function(){
  if(window.__jmusic)return;window.__jmusic=1;
  var LIST='PLRW80bBvVD3VGlhepFny5ABfb4ZqY4yGI';
  var p=location.pathname;
  if(/^\/admin(\/|$)/.test(p))return;
  function ls(k,v){try{if(v===undefined)return localStorage.getItem(k);localStorage.setItem(k,v)}catch(_){}}

  /* ---- Inside the shell's frame: no button; send outside links to a new tab so the music keeps going ---- */
  if(window.top!==window){
    if(window.name!=='jsite')return;          // some other embed (e.g. the card page's collection panel)
    document.addEventListener('click',function(e){
      var a=e.target.closest&&e.target.closest('a[href]');if(!a||a.target)return;
      var u;try{u=new URL(a.href,location.href)}catch(_){return}
      if(u.origin!==location.origin&&/^https?:/.test(u.protocol)){a.target='_blank';a.rel=(a.rel?a.rel+' ':'')+'noopener'}
    },true);
    return;
  }

  /* ---- Normal page: the 🎵 button ---- */
  var css='#jmusic{position:fixed;right:16px;bottom:16px;z-index:890;width:46px;height:46px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:var(--deep,#17121D);border:1px solid var(--edge,#3A3046);color:var(--ink,#FFF4E6);font-size:20px;line-height:1;cursor:pointer;box-shadow:0 10px 30px -10px rgba(0,0,0,.7);transition:transform .15s,border-color .15s}'+
    '#jmusic:hover{transform:translateY(-2px);border-color:var(--acc,#F57C00)}'+
    '#jmusic .jmt{position:absolute;right:54px;white-space:nowrap;background:var(--deep,#17121D);border:1px solid var(--edge,#3A3046);border-radius:999px;padding:6px 10px;font:600 13px Inter,system-ui,sans-serif;opacity:0;pointer-events:none;transition:opacity .15s}'+
    '@media (hover:hover){#jmusic:hover .jmt{opacity:1}}@media print{#jmusic{display:none}}';
  function build(){
    if(document.getElementById('jmusic'))return;
    var s=document.createElement('style');s.textContent=css;document.head.appendChild(s);
    var b=document.createElement('button');b.id='jmusic';b.type='button';
    b.setAttribute('aria-label','Play Naruto music while you browse');
    b.innerHTML='<span aria-hidden="true">🎵</span><span class="jmt">Naruto music</span>';
    b.addEventListener('click',shell);document.body.appendChild(b);
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',build);else build();

  /* ---- The shell ---- */
  function shell(){
    try{if(window.jtrack)jtrack('music-open',{page:p})}catch(_){}
    var start=location.href;
    var st=document.createElement('style');
    st.textContent='html,body{margin:0!important;padding:0!important;height:100%!important;overflow:hidden!important;background:#1B1622!important}'+
      '#jsite{position:fixed;inset:0;width:100%;height:100%;height:100dvh;border:0;display:block;background:#1B1622}'+
      '#jmp{position:fixed;right:12px;bottom:12px;z-index:2147483000;width:216px;background:#17121D;border:1px solid #3A3046;border-radius:14px;padding:8px;box-shadow:0 16px 40px -12px rgba(0,0,0,.85);font:500 13px Inter,system-ui,sans-serif;color:#FFF4E6}'+
      '#jmp.left{right:auto;left:12px}'+
      '#jmp .v{width:200px;height:200px;border-radius:10px;overflow:hidden;background:#000}#jmp .v iframe{width:200px;height:200px;border:0;display:block}'+
      '#jmp .t{margin:7px 2px 6px;font-weight:700;font-size:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}'+
      '#jmp .c{display:flex;align-items:center;justify-content:space-between;gap:4px}'+
      '#jmp button{border:1px solid #3A3046;background:#241E2D;color:#FFF4E6;border-radius:50%;width:32px;height:32px;font-size:13px;cursor:pointer;display:flex;align-items:center;justify-content:center;padding:0;-webkit-tap-highlight-color:transparent}'+
      '#jmp button:hover{border-color:#F57C00}#jmp .pp{width:40px;height:40px;font-size:16px;background:#F57C00;border-color:#F57C00;color:#1B1622}#jmp .on{border-color:#F57C00;color:#F57C00}'+
      '#jmp .vol{display:flex;align-items:center;gap:6px;margin-top:6px;color:#B8AEA6}#jmp .vol input{flex:1;accent-color:#F57C00}'+
      '@media (pointer:coarse){#jmp .vol{display:none}}';
    document.head.appendChild(st);
    document.body.innerHTML='';document.body.removeAttribute('class');
    var f=document.createElement('iframe');f.id='jsite';f.name='jsite';f.title='jonin.cards';f.src=start;
    var card=document.createElement('div');card.id='jmp';
    if(ls('jmusic_side')==='left')card.className='left';
    card.innerHTML='<div class="v"><div id="jyt"></div></div><div class="t" id="jtt">🎵 Loading…</div>'+
      '<div class="c"><button id="jpv" aria-label="Previous">⏮</button><button id="jpp" class="pp" aria-label="Play or pause">▶</button>'+
      '<button id="jnx" aria-label="Next">⏭</button><button id="jsh" aria-label="Shuffle">🔀</button><button id="jsd" aria-label="Move to the other corner">⇆</button><button id="jx" aria-label="Stop music">✕</button></div>'+
      '<label class="vol"><span aria-hidden="true">🔊</span><input id="jvl" type="range" min="0" max="100" aria-label="Volume"></label>';
    document.body.appendChild(f);document.body.appendChild(card);
    ['click','keydown','pointerdown'].forEach(function(t){card.addEventListener(t,function(e){e.stopPropagation()})}); // the old page's own handlers still listen on the outer document
    var $=function(i){return document.getElementById(i)};

    /* keep the address bar + tab title in step with the page inside the frame */
    f.addEventListener('load',function(){
      try{var w=f.contentWindow;if(w.location.href!=='about:blank')history.replaceState(null,'',w.location.href);
        document.title=w.document.title;
      }catch(_){location.href=start}   // left the site somehow: get out of the shell
    });

    /* YouTube player */
    var P,fails=0,shuf=ls('jmusic_shuf')==='1',vol=+(ls('jmusic_vol')||60);
    $('jvl').value=vol;$('jsh').classList.toggle('on',shuf);
    function info(){if(!P||!P.getVideoData)return;var d=P.getVideoData()||{};if(d.title)$('jtt').textContent=d.title}
    window.onYouTubeIframeAPIReady=function(){
      P=new YT.Player('jyt',{width:200,height:200,playerVars:{listType:'playlist',list:LIST,autoplay:1,rel:0,playsinline:1},
        events:{onReady:function(){P.setVolume(vol);if(shuf){P.setShuffle(true);P.playVideoAt(0)}else P.playVideo();info()},
          onStateChange:function(e){if(e.data===1)fails=0;$('jpp').textContent=e.data===1?'⏸':'▶';info()},   // 1 = playing; if a phone blocks autoplay, tap ▶
          onError:function(e){fails++;if(fails>=5){$('jtt').textContent='YouTube blocks these tracks off YouTube (code '+e.data+')';return}$('jtt').textContent='Track unavailable, skipping…';setTimeout(function(){P.nextVideo()},1200)}}});
    };
    var y=document.createElement('script');y.src='https://www.youtube.com/iframe_api';document.head.appendChild(y);
    $('jpp').onclick=function(){if(!P)return;P.getPlayerState()===1?P.pauseVideo():P.playVideo()};
    $('jnx').onclick=function(){P&&P.nextVideo()};
    $('jpv').onclick=function(){P&&P.previousVideo()};
    $('jsh').onclick=function(){shuf=!shuf;ls('jmusic_shuf',shuf?'1':'0');this.classList.toggle('on',shuf);if(P){P.setShuffle(shuf);if(shuf)P.nextVideo()}};
    $('jsd').onclick=function(){var l=card.classList.toggle('left');ls('jmusic_side',l?'left':'right')};
    $('jvl').oninput=function(){if(P)P.setVolume(+this.value);ls('jmusic_vol',this.value)};
    $('jx').onclick=function(){var u=start;try{u=f.contentWindow.location.href}catch(_){}location.href=u};  // reload the current page without music
    setInterval(info,3000);
  }
})();
