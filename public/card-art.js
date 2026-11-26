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
