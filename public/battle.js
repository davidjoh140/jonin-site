/* Daily battle (David, 2026-11-27): two random characters a day, visitors vote who would win and earn scrolls.
   Renders into every [data-battle] element (homepage sidebar box, /battle/ page). Data: today_battle() and
   vote_battle() in Supabase (db/038_daily_battle.sql). PLACEHOLDERS for David: 5 scrolls a vote, a new battle at
   midnight New York time, sign in to vote, results after you vote, wording. */
(function(){
  var SUPA='https://cfzpayanhvvqtkuqfgof.supabase.co',KEY='sb_publishable_ZR1zggWL9FxxwfwoIASwSg_YDV3Nvfe',TK='sb-cfzpayanhvvqtkuqfgof-auth-token';
  var els=[].slice.call(document.querySelectorAll('[data-battle]'));if(!els.length)return;
  function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]})}
  function session(){try{var s=JSON.parse(localStorage.getItem(TK)||'null');if(s&&s.currentSession)s=s.currentSession;return s&&s.access_token&&s.user&&(!s.expires_at||s.expires_at*1000>Date.now())?s:null}catch(_){return null}}
  function rpc(fn,body){var s=session(),h={apikey:KEY,'Content-Type':'application/json'};if(s)h.Authorization='Bearer '+s.access_token;
    return fetch(SUPA+'/rest/v1/rpc/'+fn,{method:'POST',headers:h,body:JSON.stringify(body||{})}).then(function(r){if(!r.ok)throw r.status;return r.json()})}
  function nice(slug){return String(slug||'').split('-').map(function(w){return w.charAt(0).toUpperCase()+w.slice(1)}).join(' ')}
  // Fighter art (2026-11-27): the 480x360 card-art crops from the character pages (/char-art/), not the small face crops.
  function face(c){return '<span class="art"><img src="/char-art/'+esc(c.slug)+'.webp" alt="'+esc(c.label)+'" width="480" height="360" decoding="async"></span>'}
  function pct(n,t){return t?Math.round(n/t*100):0}
  var css='.jbt{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:12px;display:grid;gap:10px}'+
    '.jbt h3{margin:0;font:700 18px/1.1 "Baloo 2",sans-serif;display:flex;justify-content:space-between;align-items:baseline;gap:8px}.jbt h3 small{font:600 12px Inter,sans-serif;color:var(--acc)}'+
    '.jbt .q{margin:0;font-size:13px;color:var(--mute)}.jbt .vs{display:grid;grid-template-columns:1fr auto 1fr;align-items:center;gap:8px}'+
    '.jbt .vs b.x{font:800 20px "Baloo 2",sans-serif;color:var(--acc);text-shadow:0 0 12px rgba(0,0,0,.6)}'+
    '.jbt .f{all:unset;cursor:pointer;display:grid;justify-items:center;gap:6px;padding:6px;border-radius:10px;border:1px solid var(--line);text-align:center;transition:border-color .15s,transform .15s}'+
    '.jbt .f:hover{border-color:var(--acc);transform:translateY(-1px)}.jbt .f:focus-visible{outline:2px solid var(--acc)}'+
    '.jbt .f .art{position:relative;display:block;width:100%;aspect-ratio:4/5;border-radius:8px;overflow:hidden;background:rgba(0,0,0,.25)}.jbt .f .art img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:50% 25%;transition:transform .25s}.jbt .f:hover .art img{transform:scale(1.04)}.jbt .f.done .art img{transform:none}.jbt .f>span.nm{font:800 15px/1.1 \"Baloo 2\",sans-serif;letter-spacing:.2px}'+
    '.jbt .f.done{cursor:default;transform:none}.jbt .f.mine{border-color:var(--acc);box-shadow:0 0 0 1px var(--acc) inset}.jbt .f.done:not(.mine){opacity:.75}'+
    '.jbt .bar{height:6px;width:100%;border-radius:4px;background:rgba(255,255,255,.08);overflow:hidden}.jbt .bar i{display:block;height:100%;background:var(--acc)}'+
    '.jbt .f em{font:700 13px Inter,sans-serif;font-style:normal;color:var(--acc)}.jbt .ft{margin:0;font-size:12px;color:var(--mute)}.jbt .ft a{color:var(--acc)}'+
    '.jbt.big{padding:18px;gap:14px}.jbt.big h3{font-size:24px}.jbt.big .f>span.nm{font-size:20px}.jbt.big .vs{gap:14px}';
  var st=document.createElement('style');st.textContent=css;document.head.appendChild(st);

  var D=null,busy=false;
  function render(){els.forEach(function(el){
    var big=el.hasAttribute('data-big');el.className=(el.className.replace(/\bjbt\b|\bbig\b/g,'')+' jbt'+(big?' big':'')).trim();
    if(!D){el.innerHTML='<h3>⚔️ Daily battle</h3><p class="q">Loading today’s battle…</p>';return}
    var voted=!!D.mine,t=D.votes?D.votes.a+D.votes.b:0,s=D.scrolls||0;
    var side=function(c,k){var n=D.votes?D.votes[k]:0,p=pct(n,t);
      return '<button type="button" class="f'+(voted?' done':'')+(D.mine===c.slug?' mine':'')+'" data-pick="'+esc(c.slug)+'"'+(voted?' disabled':'')+' aria-label="Vote '+esc(c.label)+'">'+face(c)+'<span class="nm">'+esc(c.label)+'</span>'+
        (voted?'<div class="bar" aria-hidden="true"><i style="width:'+p+'%"></i></div><em>'+p+'%</em>':'')+'</button>'};
    var y=D.yesterday,yt=y?(+y.va)+(+y.vb):0,yl='';
    if(y&&yt){var w=+y.va>=+y.vb?[y.a,y.va,y.b]:[y.b,y.vb,y.a];yl=(+y.va===+y.vb?'Yesterday: '+esc(nice(y.a))+' vs '+esc(nice(y.b))+' was a tie.':'Yesterday: '+esc(nice(w[0]))+' beat '+esc(nice(w[2]))+' with '+pct(+w[1],yt)+'% of the vote.')}
    el.innerHTML='<h3>⚔️ Daily battle'+(s?'<small>+'+s+' scrolls</small>':'')+'</h3>'+
      '<p class="q">'+(voted?'You picked '+esc(D.mine===D.a.slug?D.a.label:D.b.label)+'. '+t+' vote'+(t===1?'':'s')+' so far. New battle tomorrow.':'Who wins in a 1v1? Tap to vote.')+'</p>'+
      '<div class="vs">'+side(D.a,'a')+'<b class="x" aria-hidden="true">VS</b>'+side(D.b,'b')+'</div>'+
      (!D.signed_in?'<p class="ft">Sign in free to vote and earn '+s+' scrolls a day.</p>':'')+
      (yl?'<p class="ft">'+yl+'</p>':'')+(big?'':'<p class="ft"><a href="/battle/">Battle page →</a></p>');
  })}
  function load(){rpc('today_battle').then(function(d){D=d;render()}).catch(function(){els.forEach(function(el){el.innerHTML='<h3>⚔️ Daily battle</h3><p class="q">Couldn’t load today’s battle. Refresh to try again.</p>'})})}
  document.addEventListener('click',function(e){var b=e.target.closest&&e.target.closest('.jbt [data-pick]');if(!b||!D||D.mine||busy)return;
    if(!session()){if(typeof window.openAuth==='function')window.openAuth('up');else location.href='/#signup';if(window.jtrack)jtrack('battle-signin',{});return}
    busy=true;var pick=b.getAttribute('data-pick');
    rpc('vote_battle',{p_pick:pick}).then(function(d){D=d;render();if(window.jtrack)jtrack('battle-vote',{pick:pick});
    }).catch(function(){alertless(b)}).then(function(){busy=false})});
  function alertless(b){var p=b.closest('.jbt').querySelector('.q');if(p)p.textContent='That vote didn’t go through. Refresh and try again.'}
  // Sign-in or sign-out in this tab or another: reload so the battle shows your vote state.
  var WHO=(session()||{user:{}}).user.id||'';
  setInterval(function(){var w=(session()||{user:{}}).user.id||'';if(w!==WHO){WHO=w;load()}},4000);
  window.addEventListener('storage',function(e){if(e.key===TK)load()});
  load();
})();
