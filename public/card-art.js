/* Card pages are rebuilt every ~15 minutes; this swaps in a newer scan as soon as it's in Supabase
   (site_card_images = one best public image per card), so a new scan shows within a minute or two. */
(function(){
  var SUPA='https://cfzpayanhvvqtkuqfgof.supabase.co',KEY='sb_publishable_ZR1zggWL9FxxwfwoIASwSg_YDV3Nvfe';
  var box=document.querySelector('.cardpage .art[data-card]');if(!box)return;
  var id=box.getAttribute('data-card'),alt=box.getAttribute('data-alt')||'';
  var tail=function(u){var i=(u||'').indexOf('/scans/');return i<0?u:u.slice(i+7)};
  fetch(SUPA+'/rest/v1/site_card_images?select=url&card_id=eq.'+encodeURIComponent(id),{headers:{apikey:KEY}})
    .then(function(r){return r.ok?r.json():[]}).then(function(rows){
      var url=rows&&rows[0]&&rows[0].url;if(!url||!/^https:\/\//.test(url))return;
      var cur=box.querySelector('img');
      if(cur&&tail(cur.getAttribute('src'))===tail(url))return;   // already the newest scan
      var img=new Image();img.width=750;img.height=1050;img.alt=alt;
      img.onload=function(){box.textContent='';box.appendChild(img)};img.src=url;
    }).catch(function(){});
})();

/* "For sale now" (2026-11-26): active eBay listings for this card, free for everyone, cheapest first,
   placed above the price/sold-listings section. Data: card_listings() RPC (db/032_card_listings.sql), filled by the
   collect-sales workflow every ~15 minutes. PLACEHOLDERS for David: 5 shown before "Show all", the empty-state text,
   the "Offers OK" label and the affiliate note wording. */
(function(){
  var SUPA='https://cfzpayanhvvqtkuqfgof.supabase.co',KEY='sb_publishable_ZR1zggWL9FxxwfwoIASwSg_YDV3Nvfe';
  var EPN='mkevt=1&mkcid=1&mkrid=711-53200-19255-0&campid=5339262225&toolid=10001&customid=jonin-forsale';
  var SHOW=5;
  var art=document.querySelector('.cardpage .art[data-card]'),info=document.querySelector('.market')||document.querySelector('.cardpage .info');if(!art||!info)return;
  var id=art.getAttribute('data-card'),name=(document.querySelector('.cardpage h1')||{}).textContent||'';
  function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]})}
  function money(v){v=+v;return '$'+(v>=100?Math.round(v).toLocaleString('en-US'):v.toFixed(2).replace(/\.00$/,''))}
  function left(d){var ms=new Date(d)-Date.now();if(!(ms>0))return 'ending';var h=ms/36e5;return h<1?Math.max(1,Math.round(ms/6e4))+'m left':h<48?Math.round(h)+'h left':Math.round(h/24)+'d left'}
  function type(x){if(x.kind==='AUCTION')return 'Auction · '+(x.ends_at?left(x.ends_at)+' · ':'')+x.bids+' bid'+(x.bids===1?'':'s');return 'Buy It Now'+(x.best_offer?' · Offers OK':'')}
  var sec=document.createElement('section');sec.className='fs';sec.innerHTML='<h3>For sale now</h3><p class="none">Loading listings…</p>';
  // 2026-11-26 cleanup: full-width .market row under the card, For sale now on the left, price estimate on the right.
  var px=info.querySelector('section.px');if(px)info.insertBefore(sec,px);else info.appendChild(sec);
  fetch(SUPA+'/rest/v1/rpc/card_listings',{method:'POST',headers:{apikey:KEY,'Content-Type':'application/json'},body:JSON.stringify({p_card_id:id})})
    .then(function(r){return r.ok?r.json():[]}).catch(function(){return []}).then(function(rows){
      rows=(rows||[]).filter(function(x){return /^\d{9,13}$/.test(x.item_id||'')});
      var q='https://www.ebay.com/sch/i.html?_nkw='+encodeURIComponent(('naruto ccg '+name+' '+id.split(':')[1]).trim())+'&'+EPN;
      if(!rows.length){sec.classList.add('empty');sec.innerHTML='<h3>For sale now</h3><p class="none">Nothing listed right now. <a href="'+esc(q)+'" target="_blank" rel="sponsored noopener">Search eBay →</a></p>';return}
      var list=rows.map(function(x,i){
        var g=x.grader==='Raw'||!x.grader?'Raw':x.grader+' '+(x.grade||'');
        var ver=[x.edition,x.printing].filter(Boolean).map(esc).join(' · ')+' · <em'+(g==='Raw'?'':' class="slab"')+'>'+esc(g)+'</em>';
        var img=x.image_url?'<img src="'+esc(x.image_url.replace(/s-l\d+\./,'s-l225.'))+'" alt="" loading="lazy" width="56" height="56">':'<i></i>';
        return '<a class="fsr'+(i>=SHOW?' fsx" hidden':'"')+' href="https://www.ebay.com/itm/'+x.item_id+'?'+EPN+'" target="_blank" rel="sponsored noopener" data-jt="ebay-click" data-jt-kind="for-sale">'+
          img+'<span class="fsm"><span class="fst">'+esc(x.title)+'</span><small>'+ver.replace(/^ · /,'')+'<span class="fsk">'+esc(type(x))+'</span></small></span>'+
          '<b>'+money(x.price)+'</b></a>'}).join('');
      sec.innerHTML='<h3>For sale now <span class="fsn">'+rows.length+' on eBay · from <b>'+money(rows[0].price)+'</b></span></h3><div class="fsl0">'+list+'</div>'+
        (rows.length>SHOW?'<button class="pvmore" type="button">Show all '+rows.length+' listings</button>':'')+
        '<p class="none">Cheapest first · updates every ~15 min · Jonin may earn a commission.</p>';
      var b=sec.querySelector('.pvmore');if(b)b.onclick=function(){[].forEach.call(sec.querySelectorAll('.fsx'),function(a){a.hidden=false});b.remove()};
    });
})();
