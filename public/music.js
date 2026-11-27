/* Naruto music button for jonin.cards. Loaded on every page by theme.js.
   A small round button in the bottom-right corner opens /music/ in a pop-out window, so the
   YouTube playlist keeps playing while the visitor browses (page changes don't stop it).
   PLACEHOLDER: playlist id lives in /music/index.html; button spot = bottom-right. */
(function(){
  if(window.__jmusic)return;window.__jmusic=1;
  var p=location.pathname;if(/^\/(admin|music)(\/|$)/.test(p))return;
  var NAME='joninmusic';
  function open(){
    var w=420,h=330,l=Math.max(0,(screen.availWidth||1200)-w-24),t=Math.max(0,(screen.availHeight||800)-h-80);
    var win=null;try{win=window.open('/music/',NAME,'popup=yes,width='+w+',height='+h+',left='+l+',top='+t)}catch(_){}
    if(!win)location.href='/music/';else try{win.focus()}catch(_){}
    try{if(window.jtrack)jtrack('music-open',{page:p})}catch(_){}
  }
  function build(){
    if(document.getElementById('jmusic'))return;
    var s=document.createElement('style');
    s.textContent='#jmusic{position:fixed;right:16px;bottom:16px;z-index:890;width:46px;height:46px;border-radius:50%;'+
      'display:flex;align-items:center;justify-content:center;background:var(--deep,#17121D);border:1px solid var(--edge,#3A3046);'+
      'color:var(--ink,#FFF4E6);font-size:20px;line-height:1;cursor:pointer;box-shadow:0 10px 30px -10px rgba(0,0,0,.7);transition:transform .15s,border-color .15s}'+
      '#jmusic:hover{transform:translateY(-2px);border-color:var(--acc,#F57C00)}'+
      '#jmusic .jmt{position:absolute;right:54px;white-space:nowrap;background:var(--deep,#17121D);border:1px solid var(--edge,#3A3046);'+
      'border-radius:999px;padding:6px 10px;font:600 13px Inter,system-ui,sans-serif;opacity:0;pointer-events:none;transition:opacity .15s}'+
      '#jmusic:hover .jmt{opacity:1}@media print{#jmusic{display:none}}';
    document.head.appendChild(s);
    var b=document.createElement('button');b.id='jmusic';b.type='button';
    b.setAttribute('aria-label','Play Naruto music while you browse');
    b.innerHTML='<span aria-hidden="true">🎵</span><span class="jmt">Naruto music</span>';
    b.addEventListener('click',open);document.body.appendChild(b);
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',build);else build();
})();
