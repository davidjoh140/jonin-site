/* jonin.cards homepage app (audit fix 2026-11-27: moved out of index.html so browsers keep it between visits).
   Loaded with a plain <script> at the same spot in the page, so it runs in the same order as before.
   build_pages.py updates the ?v= in index.html whenever this file changes. */
{
const $=s=>document.querySelector(s);
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const RNAME={C:'Common',U:'Uncommon',R:'Rare',SR:'Super Rare',ALT:'Alt Art /20',UR:'Ultra Rare',P:'Promo',F:'Starter','':'Unknown'};
// PLACEHOLDER mapping from printing names in the data to David's five foil types; confirm with him
const FOILS={'Flat foil':['flat','Flat foil'],'Full foil':['flat','Flat foil'],'Diamond foil':['diamond','Diamond'],'Wavy foil':['wavy','Wavy'],'Prism foil':['prism','Prism'],'Spiral foil':['spiral','Spiral'],'Diamond-checkered foil':['prism','Prism'],'Diamond-spiral foil':['spiral','Spiral']};
const rsym=k=>{const n={U:1,R:2,SR:3}[k];const inner=n?'<i></i>'.repeat(n):({C:'C',ALT:'/20',UR:'UR',P:'PR',F:'ST','':'?'}[k]??esc(k));return `<span class="rs rs-${esc(k||'X')}" title="${esc(RNAME[k]||k)}">${inner}</span>`};
const foilsOf=c=>{const seen=new Set(),out=[];(c.v||[]).forEach(v=>{const f=FOILS[v];if(f&&!seen.has(f[0])){seen.add(f[0]);out.push(f)}});return out};
// PSA pop report pages per set (links from David). Promos are split by year on PSA, so promo cards get one link per year.
const PSA_POP='https://www.psacard.com/pop/tcg-cards/',PSA={"1": "2006/naruto-ccg-series-1-path-hokage/224462", "2": "2006/naruto-ccg-series-2-coils-snake/224780", "3": "2006/naruto-ccg-series-3-curse-sand/224465", "4": "2007/naruto-ccg-series-4-revenge-rebirth/224467", "5": "2007/naruto-ccg-series-5-dream-legacy/224234", "6": "2007/naruto-ccg-series-6-eternal-rivalry/224226", "7": "2007/naruto-ccg-series-7-quest-power/224852", "8": "2008/naruto-ccg-series-8-battle-destiny/224854", "9": "2008/naruto-ccg-series-9-chosen/224464", "10": "2008/naruto-ccg-series-10-lineage-legends/224460", "11": "2008/naruto-ccg-series-11-approaching-wind/224459", "12": "2009/naruto-ccg-series-12-new-chronicle/228769", "13": "2009/naruto-ccg-series-13-fateful-reunion/224856", "14": "2009/naruto-ccg-series-14-emerging-alliance/224858", "15": "2009/naruto-ccg-series-15-foretold-prophecy/224463", "16": "2010/naruto-ccg-series-16-broken-promise/224859", "17": "2010/naruto-ccg-series-17-will-fire/234830", "18": "2010/naruto-ccg-series-18-fangs-snake/224781", "19": "2010/naruto-ccg-series-19-path-pain/224405", "20": "2011/naruto-ccg-series-20-tales-gallant-sage/224328", "21": "2011/naruto-ccg-series-21-shattered-truth/224326", "22": "2011/naruto-ccg-series-22-weapons-war/224457", "23": "2011/naruto-ccg-series-23-invasion/230138", "24": "2012/naruto-ccg-series-24-sages-legacy/225147", "25": "2012/naruto-ccg-series-25-kage-summit/225149", "26": "2012/naruto-ccg-series-26-avengers-wrath/224862", "27": "2012/naruto-ccg-series-27-heros-ascension/224622", "28": "2013/naruto-ccg-series-28-ultimate-ninja-storm-3/224407", "TP1": "2010/naruto-ccg-tournament-pack-1/230139", "TP2": "2010/naruto-ccg-tournament-pack-2/232468", "TP3": "2011/naruto-ccg-tournament-pack-3/235895", "TP4": "2012/naruto-ccg-tournament-pack-4/230143", "T2": "2010/naruto-ccg-untouchable-tins/230974", "T3": "2011/naruto-ccg-ultimate-battle-tins/224461", "T4": "2011/naruto-ccg-rebirth-tins/224867"},PSA_PROMO=[["2007", "2007/naruto-ccg-promo/239407"], ["2008", "2008/naruto-ccg-promo/258492"], ["2009", "2009/naruto-ccg-promo/237155"], ["2010", "2010/naruto-ccg-promo/233876"], ["2011", "2011/naruto-ccg-promo/224868"], ["2012", "2012/naruto-ccg-promo/235909"], ["2013", "2013/naruto-ccg-promo/231188"]];
// Jump to the card on PSA's set page: a browser text fragment that highlights and scrolls to the card number
// (PSA style, e.g. N259 / NUS017) and the card name. Browsers without text fragments just open the set page.
const psaFrag=c=>{const num=c.n.replace(/-/g,''),nm=c.name.replace(/\s*[\[(].*?[\])]\s*/g,' ').trim();const f=t=>'text='+encodeURIComponent(t).replace(/-/g,'%2D');return '#:~:'+f(num)+'&'+f(nm)};
const TYPES=['','Ninja','Jutsu','Mission','Client'];
const RARS=[['','All rarities'],['C','Common'],['U','Uncommon'],['R','Rare'],['SR','Super Rare'],['ALT','Alt Art /20'],['P','Promo']];
// PLACEHOLDER character list (fan favorites that have cards); David to confirm. 'A|B' = either name, e.g. Minato also printed as The Fourth Hokage
const S0=()=>({q:'',set:'',type:'',chars:[],rars:[],sort:'',el:'',tc:'',hc:'',vil:''});
// Card details read off the scans and approved by David (cards.json el/tc/hc/vil). Each dropdown only shows once some cards have that detail.
const DETAILS=[['el','Element'],['tc','Turn cost'],['hc','Hand cost'],['vil','Village']];
const EL_ORDER=['Fire','Water','Wind','Lightning','Earth','Void'];
// Icons cut from the card scans (public/icons). Values without an icon get a plain number badge.
const VIL_ICON={'Leaf':'leaf','Sand':'sand','Sound':'sound','Mist':'mist','Rain':'rain','Rock':'rock','Cloud':'cloud','Rogue Ninja':'rogue'};
const ICON_HAVE={tc:[0,1,2,3,4,5,6],hc:[0,1]};
function dIcon(k,v,cls){cls=cls||'dic';if(v==null||v==='')return '';
  if(k==='el')return `<img class="${cls}" src="/icons/el-${esc(String(v).toLowerCase())}.png" alt="" width="22" height="22">`;
  if(k==='vil')return VIL_ICON[v]?`<img class="${cls}" src="/icons/vil-${VIL_ICON[v]}.png" alt="" width="22" height="22">`:'';
  if((k==='tc'||k==='hc')&&ICON_HAVE[k].includes(+v))return `<img class="${cls}" src="/icons/${k}-${+v}.png" alt="" width="22" height="22">`;
  if(k==='tc'||k==='hc')return `<span class="${cls} dnum ${k}">${esc(String(v))}</span>`;return ''}
const dLabel=(k,v)=>k==='tc'||k==='hc'?(v===''?'Any':String(v)):(v||'Any');
function buildDetails(){const box=$('#details');if(!box||document.documentElement.classList.contains('embed'))return;box.innerHTML=DETAILS.map(([k,l])=>{const cnt=new Map();D.cards.forEach(c=>{const v=c[k];if(v!=null&&v!=='')cnt.set(v,(cnt.get(v)||0)+1)});if(!cnt.size)return '';
  const vals=[...cnt.keys()].sort((a,b)=>k==='el'?EL_ORDER.indexOf(a)-EL_ORDER.indexOf(b):typeof a==='number'?a-b:String(a).localeCompare(String(b)));
  return `<div class="dd" data-dk="${k}"><button type="button" class="pill ddb" aria-haspopup="listbox" aria-expanded="false"><span class="ddl">${l}</span><span class="ddv"></span><span class="chev" aria-hidden="true">▾</span></button>
  <ul class="ddp" role="listbox" aria-label="${l}" hidden><li role="option" class="ddo" data-v=""><span class="dic dany">✕</span><span>Any ${l.toLowerCase()}</span></li>${vals.map(v=>`<li role="option" class="ddo" data-v="${esc(String(v))}">${dIcon(k,v)}<span>${k==='tc'?'Turn cost '+v:k==='hc'?'Hand cost '+v:esc(String(v))}</span><span class="ddn">${cnt.get(v).toLocaleString()}</span></li>`).join('')}</ul></div>`}).join('');
  box.hidden=!box.innerHTML;paintDetails()}
function paintDetails(){document.querySelectorAll('#details .dd').forEach(dd=>{const k=dd.dataset.dk,v=S[k]||'';dd.querySelector('.ddv').innerHTML=v?dIcon(k,k==='tc'||k==='hc'?+v:v,'dic sm')+`<b>${esc(dLabel(k,v))}</b>`:'<span class="ddany">Any</span>';
  dd.querySelector('.ddb').classList.toggle('on',!!v);dd.querySelectorAll('.ddo').forEach(o=>o.setAttribute('aria-selected',o.dataset.v===v))})}
function ddClose(){document.querySelectorAll('#details .ddp').forEach(p=>{p.hidden=true;p.previousElementSibling.setAttribute('aria-expanded','false')})}
document.addEventListener('click',e=>{const b=e.target.closest('#details .ddb'),o=e.target.closest('#details .ddo');
  if(b){const p=b.nextElementSibling,open=p.hidden;ddClose();if(open){p.hidden=false;b.setAttribute('aria-expanded','true')}return}
  if(o){const k=o.closest('.dd').dataset.dk;S[k]=o.dataset.v;ddClose();writeHash();renderCards(true);return}
  if(!e.target.closest('#details'))ddClose()});
document.addEventListener('keydown',e=>{if(e.key==='Escape')ddClose()});
let VIEW='cards',D=null,S=S0(),list=[],shown=0,sel=-1;
const PAGE=48;   // tiles per batch; more load as you scroll (was 120, 2026-11-26 speed-up)
const setName=id=>D.byId[id]?.name||id;
const setLabel=s=>s.kind==='Main'?'Set '+s.id:s.kind==='Promo'?'Promo':s.id;
const SYMV='2';const symUrl=u=>u?u+(u.includes('?')?'&':'?')+'v='+SYMV:'';
const setTag=id=>{const s=D.byId[id]||{id,name:id};return `<span class="stag">${s.symbol?`<img class="ssym" src="${esc(symUrl(s.symbol))}" alt="" loading="lazy">`:''}<span>${esc(s.name||id)}</span></span>`};
const baseName=n=>n.replace(/\s*\(.*?\)\s*/g,'').trim();
function readHash(){const h=location.hash.slice(1);if(h==='sets')return 'sets';if(h==='mine')return 'mine';if(h==='lists'){MTAB='lists';return 'mine'}if(h.startsWith('u='))return 'user';S=S0();h.split('&').forEach(p=>{const i=p.indexOf('=');if(i<0)return;const k=p.slice(0,i),v=decodeURIComponent(p.slice(i+1));if(!v)return;
  if(k==='chars'||k==='rars')S[k]=v.split(',').filter(Boolean);else if(k==='rar')S.rars=[v];else if(k==='quick'){const[a,b]=v.split(':');if(a==='char')S.chars=[b];if(a==='rar')S.rars=[b]}else if(k in S)S[k]=v});if(S.sort==='px-d')S.sort='';return 'cards'}
function writeHash(){const h=Object.entries(S).filter(([k,v])=>Array.isArray(v)?v.length:v).map(([k,v])=>k+'='+encodeURIComponent(Array.isArray(v)?v.join(','):v)).join('&');history.replaceState(null,'',h?'#'+h:location.pathname)}
const active=()=>Object.values(S).some(v=>Array.isArray(v)?v.length:v);
const tog=(a,v)=>a.includes(v)?a.filter(x=>x!==v):[...a,v];
// Card number search (2026-11-26): "N-001", "n001", "n1", "#12", "12", "jus3" all find the card by number.
// Dashes, spaces, # and leading zeros are ignored; a bare number matches that number in any prefix (N-012, J-012…).
const numKey=x=>x.toUpperCase().replace(/[#\s-]/g,'').replace(/(^|[A-Z])0+(?=\d)/g,'$1');
function numHit(w,n){if(!/\d/.test(w))return false;const k=numKey(w),cn=numKey(n);
  if(/^\d+[A-Z]?$/.test(k))return cn.replace(/^[A-Z]+/,'')===k;return cn===k}
// Search aliases: squashed or alternate spellings for terms in card notes (add more as they come up).
const ALIAS={gencon:'gen con',e3expo:'e3',sdcc:'comic con',comiccon:'comic con'};
// Alt arts: "alt arts", "altart", "alt-art", "alternate/alternative art" all search as "alt art" (the rarity is "Alt Art /20").
const qNorm=q=>q.replace(/(^|[^a-z0-9])alt(?:ernate|ernative)?[\s-]*arts?(?![a-z0-9])/g,'$1alt art');
// Short words (3 letters or less, like "e3") must start a word, so they don't hit inside "the 3rd".
const wordHit=(w,hay)=>w.length<=3?new RegExp('(^|[^a-z0-9])'+w.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')).test(hay):hay.includes(w);
// Multi-word search: if any card holds the whole phrase ("gen con", "dream legacy"), only phrase matches show;
// otherwise each word matches on its own ("kakashi 12"). Checked once per query.
const flatOf=c=>(c.name+' '+c.n+' '+setName(c.s)+' '+(D.byId[c.s]?.code||'')+' '+(c.src==='ALT'?c.r:'')+' '+(c.note||'')+' '+(c.deck||'')+' '+(c.t||'')+' '+(c.el||'')+' '+(c.vil||'')).toLowerCase().replace(/[\s'’.-]/g,'');
// Speed (2026-11-26): each card's search text and character names are worked out once (prep), and the search words
// once per query (qPrep), instead of for every card on every click and keystroke.
const hayOf=c=>c._hay||(c._hay=(c.name+' '+c.n+' '+setName(c.s)+' '+(D.byId[c.s]?.code||'')+' '+(c.src==='ALT'?c.r:'')+' '+(c.note||'')+' '+(c.deck||'')+' '+(c.t||'')+' '+(c.el||'')+' '+(c.vil||'')).toLowerCase());
const flatC=c=>c._flat||(c._flat=flatOf(c));
const namesOf=c=>c._nm||(c._nm=c.name.split(/\s*&\s*/).map(baseName));
let QP={q:null};
function qPrep(){if(QP.q===S.q)return QP;const q0=qNorm(S.q.toLowerCase().trim()),ws=(ALIAS[q0.replace(/[\s'’.-]/g,'')]||q0).split(/\s+/).filter(Boolean);
  QP={q:S.q,ws:ws.map(w=>({w,num:/^#?\d+$/.test(w),re:w.length<=3?new RegExp('(^|[^a-z0-9])'+w.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')):null}))};return QP}
let PH={q:null,k:'',on:false};
const phraseOn=()=>{if(PH.q!==S.q){const k=qNorm(S.q.toLowerCase()).replace(/[\s'’.-]/g,'');PH={q:S.q,k,on:k.length>2&&D.cards.some(c=>flatC(c).includes(k))}}return PH.on};
// Typo help (audit fix 2026-11-27): when a search finds nothing, each word of 4+ letters that appears in no card is swapped
// for the closest word from card, character and set names (1 letter off, or 2 for longer words), e.g. "kakshi" → "kakashi".
let SUGG=null,VOCAB=null;const tcase=t=>t.replace(/\b[a-z]/g,m=>m.toUpperCase());
function editDist(a,b,max){if(Math.abs(a.length-b.length)>max)return max+1;let p=Array.from({length:b.length+1},(_,j)=>j);
  for(let i=1;i<=a.length;i++){const c=[i];let lo=i;for(let j=1;j<=b.length;j++){c[j]=Math.min(p[j]+1,c[j-1]+1,p[j-1]+(a[i-1]===b[j-1]?0:1));if(c[j]<lo)lo=c[j]}if(lo>max)return max+1;p=c}return p[b.length]}
function typoFix(q){if(!VOCAB){const v=new Set();D.cards.forEach(c=>(c.name+' '+setName(c.s)).toLowerCase().split(/[^a-z0-9']+/).forEach(w=>{w=w.replace(/'/g,'');if(w.length>=4)v.add(w)}));VOCAB=[...v]}
  let changed=false;const out=q.toLowerCase().trim().split(/\s+/).map(w=>{if(w.length<4||/\d/.test(w)||VOCAB.some(x=>x.includes(w)))return w;
    const max=w.length>=6?2:1;let best=null,bd=max+1;for(const x of VOCAB){const d=editDist(w,x,max);if(d<bd||(d===bd&&best&&x.length<best.length)){bd=d;best=x}}if(best&&bd<=max){changed=true;return best}return w});
  return changed?out.join(' '):null}
function match(c){
  if(S.set&&c.s!==S.set)return false;
  if(S.rars.length&&!S.rars.includes(c.src))return false;
  if(S.type&&c.t!==S.type)return false;
  for(const [k] of DETAILS)if(S[k]&&String(c[k]??'')!==S[k])return false;
  if(S.chars.length){const names=namesOf(c);if(!S.chars.some(v=>v.split('|').some(w=>names.includes(w))))return false}
  if(S.q){const {ws}=qPrep();if(ws.length>1&&phraseOn()){if(!flatC(c).includes(PH.k))return false}else{const hay=hayOf(c);if(!ws.every(o=>numHit(o.w,c.n)||(!o.num&&(o.re?o.re.test(hay):hay.includes(o.w)))))return false}}
  return true}
// Price band on each grid tile (free). Exact prices are Jonin Club only.
const BANDS0=['Under $10','$10–50','$50–200','$200+'],money0=v=>'$'+(v>=100?Math.round(v).toLocaleString('en-US'):String(v)),band=c=>{if(c.pr&&c.pr.length===2)return c.pr[0]===c.pr[1]?'about '+money0(c.pr[0]):money0(c.pr[0])+'–'+money0(c.pr[1]);const b=(D&&D.bands)||BANDS0;return c.pb==null?null:b[c.pb]??null};
const tpx=c=>{if(MEMBER&&EST){const e=tileEst(c);return e?`<div class="tpx est">≈ ${money(e.estimate)}</div>`:'<div class="tpx none"></div>'}
  const bd=band(c);return bd?`<div class="tpx">${esc(bd)}</div>`:'<div class="tpx none"></div>'};
// Jonin Club: price estimates per exact version (weighted toward the newest sales), loaded once for members.
// Tiles show the RAW estimate of the card's most-sold version (David's call); ties prefer Unlimited, then Normal.
let EST=null;
function tileEst(c){const rows=(EST&&EST.get(c.s+':'+c.n)||[]).filter(r=>(r.grader||'Raw')==='Raw');if(!rows.length)return null;
  return rows.slice().sort((a,b)=>b.sales_count-a.sales_count||(a.edition!=='Unlimited')-(b.edition!=='Unlimited')||(a.printing!=='Normal')-(b.printing!=='Normal'))[0]}
async function loadEstimates(){if(!MEMBER||!sbc()){EST=null;return}
  // Card-page collection frame: only this card's estimates (audit fix 2026-11-27), not every card's.
  const one=document.documentElement.classList.contains('embed')?new URLSearchParams(location.search).get('card'):null;
  let qe=sb.from('price_estimates').select('card_id,printing,edition,grader,grade,estimate,sales_count,last_sold_at,last_price');if(one)qe=qe.eq('card_id',one);
  const r=await qe.limit(20000);
  if(r.error||!MEMBER){EST=null;return}EST=new Map();(r.data||[]).forEach(x=>{if(!EST.has(x.card_id))EST.set(x.card_id,[]);EST.get(x.card_id).push(x)});
  let qc=sb.from('price_estimates_cond').select('card_id,printing,edition,condition,estimate,sales_count,last_sold_at,last_price');if(one)qc=qc.eq('card_id',one);
  const rc=await qc.limit(20000);
  ESTC=new Map();if(!rc.error)(rc.data||[]).forEach(x=>{if(!ESTC.has(x.card_id))ESTC.set(x.card_id,[]);ESTC.get(x.card_id).push(x)})}
// Conditional pricing: the RAW estimate of this exact version in this condition, from price-check sales with that condition.
// David (2026-11-26): only condition-specific estimates. No sales in that condition = no price (the copy counts as unpriced).
let ESTC=new Map();const COMPS=new Map();
const edK=x=>x||'Unlimited';
function estCond(card,printing,edition,cond){const r=(ESTC.get(card)||[]).find(x=>x.printing===printing&&edK(x.edition)===edK(edition)&&x.condition===cond);
  return r?Object.assign({exact:true},r):null}
// Approved price-check sales (comps) for a card, with condition. Cached per card while the page is open.
function cardComps(id){if(!MEMBER||!sbc())return Promise.resolve([]);if(COMPS.has(id))return COMPS.get(id);
  const p=sb.rpc('member_card_comps',{p_card_id:id}).then(r=>r.error?sb.rpc('member_card_sales',{p_card_id:id}).then(r2=>r2.error?[]:(r2.data||[])):(r.data||[])).catch(()=>[]).then(v=>{p.v=v;return v});COMPS.set(id,p);return p}
const compsFor=(list,p,e,cond)=>list.filter(x=>(x.grader||'Raw')==='Raw'&&x.printing===p&&edK(x.edition)===edK(e)&&x.condition===cond);
const cardUrl=c=>'/card/'+encodeURIComponent((c.s+'-'+c.n).toLowerCase())+'/';
// Back from a card page puts the grid back where it was (2026-11-26): search/filters live in the hash, scroll + how many were shown here.
function saveGrid(){try{sessionStorage.setItem('jgrid',JSON.stringify({h:location.hash,y:scrollY,n:shown,v:VIEW}))}catch(_){}}
function tile(c,i,extra){const sr=c.src==='SR'||c.src==='UR';const fl=foilsOf(c);
  return `<a class="card in" href="${cardUrl(c)}" style="--k:${Math.min(i%PAGE,24)}" data-i="${i}" aria-label="${esc(c.name)}, ${esc(setName(c.s))} ${esc(c.n)}, ${esc(RNAME[c.src]||c.r)}${fl.length?', foils: '+esc(fl.map(f=>f[1]).join(', ')):''}"><div class="art${sr?' sr':''}">${/^https:\/\//.test(c.img||'')?`<img src="${esc(c.th||c.img)}" alt="" loading="lazy" decoding="async">`:''}<span class="num">${esc(c.n)}</span><span class="ty">${esc(c.t)}</span>${marks(c)}${fl.length?`<span class="fchips">${fl.map(f=>`<span class="fx f-${f[0]}" title="${f[1]}"></span>`).join('')}</span>`:''}</div>${tpx(c)}<div class="nm">${esc(c.name)}</div><div class="mt">${setTag(c.s)}</div><div class="mt tmeta">${esc(c.n)} · ${rsym(c.src)}${c.el?dIcon('el',c.el,'tic'):''}${c.tc!=null?dIcon('tc',c.tc,'tic'):''}</div>${extra||''}</a>`}
// Sort options. PLACEHOLDER choices for David to confirm: rarity order (UR > SR > R > U > C, then Promo, Starter, unknown),
// "Newest sets first" = main sets 28 down to 1, then packs/tins/promos; "market value" = the price band (free data only); cards with no sales always go last.
// Default sort (David, 2026-11-26): market value high to low, so visitors see the big cards first. 'num' = set & number.
const SORTS=[['','Market value: high to low'],['num','Set & number'],['name','Name A–Z'],['name-d','Name Z–A'],['rar-d','Rarity: high to low'],['rar','Rarity: low to high'],['px','Market value: low to high'],['set-d','Newest sets first'],['tc','Turn cost: low to high'],['tc-d','Turn cost: high to low'],['hc','Hand cost: low to high'],['hc-d','Hand cost: high to low'],['el','Element'],['vil','Village'],['type','Card type']];
const TYPE_ORD=['Ninja','Jutsu','Mission','Client','Promo'];
const NULL_LAST=new Set(['px','tc','hc','el','vil']);
const RORD={UR:6,SR:5,R:4,U:3,C:2,P:1,F:0,'':-1};
const pxOf=c=>{if(MEMBER&&EST){const e=tileEst(c);return e?+e.estimate:null}return c.pb==null?null:c.pb};
function sorted(a){const k=!S.sort||S.sort==='px-d'?'px-d':S.sort;if(k==='num')return a;const ix=new Map(D.cards.map((c,i)=>[c,i])),so=new Map(D.sets.map((s,i)=>[s.id,i]));const d=k.endsWith('-d')?-1:1,b=k.replace(/-d$/,'');
  const key={name:c=>c.name.toLowerCase(),rar:c=>RORD[c.src]??-1,px:pxOf,tc:c=>c.tc??null,hc:c=>c.hc??null,el:c=>c.el?EL_ORDER.indexOf(c.el):null,vil:c=>c.vil?(c.vil==='Rogue Ninja'?'~':c.vil):null,type:c=>{const i=TYPE_ORD.indexOf(c.t);return i<0?9:i},set:c=>{const i=so.get(c.s)??0;return (D.byId[c.s]||{}).kind==='Main'?i:i-1000}}[b];
  return a.map(c=>[c,key(c)]).sort(([x,kx],[y,ky])=>{if(NULL_LAST.has(b)&&(kx==null||ky==null)){if(kx==null&&ky==null)return ix.get(x)-ix.get(y);return kx==null?1:-1}
    if(b==='rar'&&d===1){const lo=v=>v<2?99:v;kx=lo(kx);ky=lo(ky)}
    const r=kx<ky?-d:kx>ky?d:0;return r||ix.get(x)-ix.get(y)}).map(p=>p[0])}
// Custom Set dropdown with set symbols. Codes: S1–S28 main sets, TP/T as is, PR for promos.
const scode=s=>s.kind==='Main'?'S'+s.id:s.kind==='Promo'?'PR':s.id;
const sopt=s=>s?`${s.symbol?`<img src="${esc(symUrl(s.symbol))}" alt="" loading="lazy">`:'<span class="nosym" aria-hidden="true"></span>'}<b>${esc(scode(s))}</b><span class="nm2">${esc(s.name)}</span>`:'<span class="nosym all" aria-hidden="true">★</span><span class="nm2">All sets</span>';
const SGRP={'Main':'Main sets','Tournament pack':'Tournament packs','Tin':'Tins','Promo':'Promos'};
function buildSetList(){let last=null,h=`<li class="opt sddo" role="option" id="so-" data-sv="">${sopt(null)}</li>`;
  D.sets.forEach(s=>{if(s.kind!==last){last=s.kind;h+=`<li class="grp" role="presentation">${esc(SGRP[s.kind]||s.kind)}</li>`}h+=`<li class="opt sddo" role="option" id="so-${esc(s.id)}" data-sv="${esc(s.id)}">${sopt(s)}</li>`});$('#sddl').innerHTML=h}
function paintSet(){$('#setsel').innerHTML=`<span class="sddo">${sopt(D.byId[S.set])}</span>`;document.querySelectorAll('#sddl .opt').forEach(o=>o.setAttribute('aria-selected',o.dataset.sv===S.set))}
const sddOpts=()=>[...document.querySelectorAll('#sddl .opt')];
function sddCur(o){sddOpts().forEach(x=>x.classList.toggle('cur',x===o));if(o){$('#sddl').setAttribute('aria-activedescendant',o.id);o.scrollIntoView({block:'nearest'})}}
function sddOpen(){const l=$('#sddl');l.hidden=false;$('#setsel').setAttribute('aria-expanded','true');sddCur(sddOpts().find(o=>o.dataset.sv===S.set)||sddOpts()[0]);l.focus()}
function sddClose(focusBtn){$('#sddl').hidden=true;$('#setsel').setAttribute('aria-expanded','false');if(focusBtn)$('#setsel').focus()}
function sddPick(v){sddClose(true);if(v===S.set)return;S.set=v;writeHash();renderCards(true)}
// Character panel: count of cards per character under every current filter except the character picks
function paintChars(){const rows=[...document.querySelectorAll('#clist .crow')];if(!rows.length||!D)return;const keep=S.chars;S.chars=[];const base=D.cards.filter(match);S.chars=keep;
  const idx=new Map();rows.forEach((b,i)=>b.dataset.q.split('|').forEach(w=>{if(!idx.has(w))idx.set(w,[]);idx.get(w).push(i)}));
  const n=rows.map(()=>0);for(const c of base){const hit=new Set();for(const nm of namesOf(c)){const r=idx.get(nm);if(r)r.forEach(i=>hit.add(i))}hit.forEach(i=>n[i]++)}const mx=Math.max(1,...n);
  {const q=$('#qn'),on=QUICK.filter(([l,v])=>S.chars.includes(v.replace(/^char:/,''))).map(([l])=>l);q.textContent=on.length?'· '+on.join(', '):'('+QUICK.length+')';q.classList.toggle('on',!!on.length)}
  {const cl=$('#clist'),ord=rows.map((b,i)=>[b,n[i],i]).sort((a,b)=>(+b[0].classList.contains('fav'))-(+a[0].classList.contains('fav'))||b[1]-a[1]||a[2]-b[2]);if(ord.some(([b],i)=>cl.children[i]!==b))ord.forEach(([b])=>cl.appendChild(b))}
  rows.forEach((b,i)=>{b.setAttribute('aria-pressed',S.chars.includes(b.dataset.q));b.classList.toggle('zero',!n[i]);b.querySelector('.cnum').textContent=n[i];b.querySelector('.cbar i').style.width=(n[i]/mx*100).toFixed(1)+'%';b.title=n[i]+' card'+(n[i]===1?'':'s')})}
function renderCards(reset){
  {const k=S.rars.length+(S.type?1:0)+DETAILS.filter(([d])=>S[d]).length;$('#fn').textContent=k?'· '+k:''}
  if(reset){list=sorted(D.cards.filter(match));SUGG=null;if(!list.length&&S.q){const t=typoFix(S.q);if(t){const q0=S.q;S.q=t;const alt=sorted(D.cards.filter(match));S.q=q0;if(alt.length){list=alt;SUGG=t}}}shown=0;const g=$('#grid');if(g.dataset.r)g.classList.add('quick');g.dataset.r='1';g.innerHTML=''}
  const next=list.slice(shown,shown+PAGE);$('#grid').insertAdjacentHTML('beforeend',next.map((c,j)=>tile(c,shown+j)).join(''));shown+=next.length;
  {const ct=$('#count'),txt=list.length.toLocaleString()+' cards';if(ct.textContent!==txt){ct.textContent=txt;if(reset){ct.classList.remove('bump');void ct.offsetWidth;ct.classList.add('bump')}}}$('#more').hidden=shown>=list.length;
  $('#clear').hidden=!active();
  if(reset&&SUGG)$('#grid').insertAdjacentHTML('afterbegin',`<p class="empty sugg" style="grid-column:1/-1;margin:0 0 4px">No cards for “${esc(S.q)}”. Showing <b>${esc(tcase(SUGG))}</b> instead. <button class="clear" data-usesugg="${esc(SUGG)}">Search “${esc(tcase(SUGG))}”</button></p>`);
  if(!list.length){const fk=S.rars.length+(S.type?1:0)+DETAILS.filter(([d])=>S[d]).length+(S.set?1:0)+S.chars.length;
    $('#grid').innerHTML=`<p class="empty">No cards match${S.q?' “'+esc(S.q)+'”':''}${fk?' with the '+fk+' filter'+(fk===1?'':'s')+' you have on':''}. ${fk&&S.q?'<button class="clear" data-keepq>Clear filters, keep search</button> ':''}<button class="clear" data-clear>↺ Reset</button></p>`}
  if(reset)paintChars();
  document.querySelectorAll('#rars .pill').forEach(b=>b.setAttribute('aria-pressed',b.dataset.r?S.rars.includes(b.dataset.r):!S.rars.length));
  paintSet();$('#sortsel').value=S.sort;document.querySelectorAll('#types .pill').forEach(b=>b.setAttribute('aria-pressed',b.dataset.ty===S.type));if($('#details .dd'))paintDetails();if(document.activeElement!==$('#q'))$('#q').value=S.q}
// Set completion (rule confirmed by David): a card counts as owned if you have any printing/edition of it.
// Master set: every printing x edition of every card; by.p[set] = printings you have, PRINTS[set] = printings that exist.
let PRINTS=null;function setPrints(){if(PRINTS)return PRINTS;PRINTS={};D.cards.forEach(c=>{PRINTS[c.s]=(PRINTS[c.s]||0)+Math.max(1,(c.v||[]).length)*Math.max(1,(c.ed||[]).filter(Boolean).length)});return PRINTS}
function setOwned(){const by={p:{}},have=[...COLL.entries()].filter(([k,q])=>q>0&&k.split('|')[3]==='have').map(([k])=>k.split('|'));new Set(have.map(a=>a[0])).forEach(id=>{const s=id.split(':')[0];by[s]=(by[s]||0)+1});new Set(have.map(a=>a.slice(0,3).join('|'))).forEach(k=>{const s=k.split(':')[0];by.p[s]=(by.p[s]||0)+1});return by}
function renderSets(){const own=setOwned(),any=Object.keys(own).length>0;$('#sets').innerHTML=D.sets.map((s,k)=>{const h=own[s.id]||0,p=s.count?Math.round(h/s.count*100):0;return `<button class="set in" style="--k:${Math.min(k,24)}" data-set="${esc(s.id)}"><div class="top"><span class="no">${esc(s.kind==='Main'?s.id:s.kind==='Promo'?'PR':s.id)}</span>${s.symbol?`<img src="${esc(symUrl(s.symbol))}" alt="${esc(s.name)} set symbol">`:''}</div><h3>${esc(s.name)}</h3><span class="mt">${s.count} cards${s.rel?' · '+esc(s.rel):''}</span>${any?`<span class="sprog"><span class="sbar"><i style="width:${p}%"></i></span><span class="snum">${h}/${s.count}${h&&h===s.count?' ✓':''}</span></span>${own.p[s.id]?`<span class="smaster">Master set ${Math.min(own.p[s.id],setPrints()[s.id]||0)}/${setPrints()[s.id]||0} printings</span>`:''}`:''}</button>`}).join('')}
function view(v){const was=VIEW;VIEW=v;if(v==='sets'&&D)renderSets();$('#v-cards').hidden=v!=='cards';$('#v-sets').hidden=v!=='sets';$('#v-mine').hidden=v!=='mine';$('#v-user').hidden=v!=='user';if(v==='cards'&&(was==='mine'||was==='user'))renderCards(true);if(v==='mine')renderMine();if(v==='user')renderUser(decodeURIComponent(location.hash.slice(3)));document.querySelectorAll('nav a').forEach(a=>a.classList.toggle('on',a.dataset.v===v))}
const money=v=>'$'+(v>=100?Math.round(v).toLocaleString():(+v).toFixed(2).replace(/\.00$/,''));
// Jonin Club members: exact price ranges by edition, foil and grade, read live from Supabase (members-only access).
const shortDate=d=>d?new Date(d).toLocaleDateString('en-US',{month:'short',day:'numeric'}):'';
const vkey=r=>[r.printing||'',r.edition||'',r.grader||'Raw',r.grade||''].join('|');
// Free view: one price band per card. Exact prices by edition, foil and grade, and sold listings, are Jonin Club only.
// eBay Partner Network tracking (campaign 5339262225). customid shows which part of the site the click came from.
const EPN='mkevt=1&amp;mkcid=1&amp;mkrid=711-53200-19255-0&amp;campid=5339262225&amp;toolid=10001&amp;customid=jonin-site';
// Phone back-swipe (feedback #9, 2026-11-26): an open card gets its own history entry, so Back closes the card instead of leaving the page.
let CARDH=0,POPSKIP=null;
// One card view only (2026-11-26): opening a card goes to its card page (the old popup is gone).
function openCard(i){const c=list[i];if(!c)return;saveGrid();location.href=cardUrl(c)}
// Feedback widget (/feedback.js) asks which card is open, so card notes carry the card id.
window.joninFbCard=()=>sel>=0&&list[sel]?{id:list[sel].s+':'+list[sel].n,name:list[sel].name+' · '+list[sel].n}:null;
window.joninFbUser=()=>ME&&ME.email||null;
window.joninFbCardAt=i=>list[i]?{id:list[i].s+':'+list[i].n,name:list[i].name+' · '+list[i].n}:null;
function pop(el){el.classList.remove('pop');void el.offsetWidth;el.classList.add('pop')}
function close(){$('#ov').hidden=true;sel=-1;if(CARDH){CARDH=0;POPSKIP=location.href;history.back()}}
addEventListener('popstate',()=>{if(POPSKIP!=null){const u=POPSKIP;POPSKIP=null;if(u!==location.href)history.replaceState(null,'',u);return}
  if(CARDH){CARDH=0;$('#ov').hidden=true;sel=-1;return}
  if(!D||location.hash==='#feedback')return;const v=readHash();view(v);if(v==='cards')renderCards(true);scrollTo(0,0)});
$('#q').addEventListener('input',e=>{S.q=e.target.value.trim();clearTimeout(trackT);if(S.q.length>=2){const t=S.q.slice(0,80);trackT=setTimeout(()=>track('search',{term:t}),1500)}clearTimeout(QT);QT=setTimeout(()=>{writeHash();renderCards(true)},90)});let QT=0;   // redraw once typing pauses (90ms)
$('#setsel').addEventListener('click',()=>$('#sddl').hidden?sddOpen():sddClose(false));
$('#setsel').addEventListener('keydown',e=>{if(['ArrowDown','ArrowUp','Enter',' '].includes(e.key)){e.preventDefault();sddOpen()}});
$('#sddl').addEventListener('click',e=>{const o=e.target.closest('.opt');if(o)sddPick(o.dataset.sv)});
$('#sddl').addEventListener('mousemove',e=>{const o=e.target.closest('.opt');if(o&&!o.classList.contains('cur'))sddCur(o)});
$('#sddl').addEventListener('keydown',e=>{const os=sddOpts(),i=os.findIndex(o=>o.classList.contains('cur'));let n=null;
  if(e.key==='ArrowDown')n=os[Math.min(i+1,os.length-1)];else if(e.key==='ArrowUp')n=os[Math.max(i-1,0)];else if(e.key==='Home')n=os[0];else if(e.key==='End')n=os[os.length-1];
  else if(e.key==='PageDown')n=os[Math.min(i+8,os.length-1)];else if(e.key==='PageUp')n=os[Math.max(i-8,0)];
  else if(e.key==='Enter'||e.key===' '){e.preventDefault();if(os[i])sddPick(os[i].dataset.sv);return}else if(e.key==='Escape'){e.preventDefault();sddClose(true);return}else if(e.key==='Tab'){sddClose(false);return}
  else if(/^[a-z0-9]$/i.test(e.key)){const k=e.key.toLowerCase();n=os.find((o,j)=>j>i&&o.textContent.trim().toLowerCase().includes(k))||os.find(o=>o.textContent.toLowerCase().includes(k))}
  if(n){e.preventDefault();sddCur(n)}});
document.addEventListener('click',e=>{if(!$('#sddl').hidden&&!e.target.closest('#sdd'))sddClose(false)});
$('#sortsel').addEventListener('change',e=>{S.sort=e.target.value;writeHash();renderCards(true)});
$('#more').addEventListener('click',()=>renderCards(false));
document.addEventListener('click',e=>{const t=e.target.closest('button,a');if(!t)return;
  if(t.dataset.q!=null){S.chars=tog(S.chars,t.dataset.q);writeHash();renderCards(true);pop(t)}
  else if(t.dataset.ty!=null){S.type=t.dataset.ty&&S.type!==t.dataset.ty?t.dataset.ty:'';writeHash();renderCards(true);pop(t)}
  else if(t.dataset.r!=null){S.rars=t.dataset.r?tog(S.rars,t.dataset.r):[];writeHash();renderCards(true);pop(t)}
  else if(t.id==='clear'||t.dataset.clear!=null){S=S0();writeHash();renderCards(true)}
  else if(t.dataset.keepq!=null){S=Object.assign(S0(),{q:S.q});writeHash();renderCards(true)}
  else if(t.dataset.usesugg!=null){S.q=t.dataset.usesugg;writeHash();renderCards(true)}
  else if(t.dataset.i!=null){if(t.tagName==="A"){saveGrid();return}openCard(+t.dataset.i)}
  else if(t.dataset.step){openCard((sel+ +t.dataset.step+list.length)%list.length)}
  else if(t.dataset.close!=null||t.id==='ovbg')close();
  else if(t.dataset.set){const ps=VIEW!=='cards';S=Object.assign(S0(),{set:t.dataset.set});view('cards');if(ps)history.pushState(null,'',location.href);writeHash();renderCards(true);scrollTo(0,0)}
  else if(t.dataset.v){e.preventDefault();if(t.dataset.v==='sets'){history.replaceState(null,'','#sets');view('sets')}else if(t.dataset.v==='mine'){if(!ME&&!gCount()){openAuth('up');return}history.replaceState(null,'','#mine');view('mine');scrollTo(0,0)}else{writeHash();view('cards')}}
  else collClick(t,e)});
document.addEventListener('change',e=>{const t=e.target;if(!t.matches||!t.matches('select[data-cond]'))return;const c=list[sel];if(!c)return;
  const [p,ed]=combos(c)[+t.dataset.cond],k=ck(cid(c),p,ed,'have'),a=condsOf(k);a[+t.dataset.ci]=t.value;setItem(c,p,ed,'have',COLL.get(k)||0,a)});
document.addEventListener('keydown',e=>{if($('#ov').hidden)return;if(e.key==='Escape')close();if(e.key==='ArrowRight')openCard((sel+1)%list.length);if(e.key==='ArrowLeft')openCard((sel-1+list.length)%list.length)});
new IntersectionObserver(es=>{if(es[0].isIntersecting&&!$('#more').hidden)renderCards(false)},{rootMargin:'600px'}).observe($('#more'));

// Live scan images: read straight from the Jonin database (Supabase), so new scans show up without waiting
// for cards.json to be rebuilt. Public read-only view + publishable key (safe to ship in the page).
const SUPA='https://cfzpayanhvvqtkuqfgof.supabase.co',SUPA_KEY='sb_publishable_ZR1zggWL9FxxwfwoIASwSg_YDV3Nvfe';
// Visitor counter: anonymous events (page view, search term, card opened) into Supabase site_events (insert-only).
// The visitor id is a random string kept in this browser, nothing personal.
const VID=(()=>{try{let v=localStorage.getItem('jv');if(!v){v=Math.random().toString(36).slice(2,12);localStorage.setItem('jv',v)}return v}catch(_){return ''}})();
function track(kind,o){try{fetch(SUPA+'/rest/v1/site_events',{method:'POST',keepalive:true,headers:{apikey:SUPA_KEY,'Content-Type':'application/json',Prefer:'return=minimal'},body:JSON.stringify(Object.assign({kind,visitor:VID},o))}).catch(()=>{})}catch(_){}}
let trackT;
// ---------- accounts: haves & wants (Supabase auth; each person's rows are private to them, RLS) ----------
let sb=null,ME=null,MYP=null,MEMBER=false,MYBADGE=null;const COLL=new Map();
// Condition per have copy (David, 2026-11-26): CONDS key = have key, value = one condition per copy. New copies start NM.
const CONDS=new Map(),CONDL=[['NM','Near Mint'],['LP','Lightly Played'],['MP','Moderately Played'],['HP','Heavily Played'],['DMG','Damaged']],CONDOK=new Set(CONDL.map(x=>x[0]));
function condsOf(k){const q=COLL.get(k)||0,a=(CONDS.get(k)||[]).filter(x=>CONDOK.has(x)).slice(0,q);while(a.length<q)a.push('NM');return a}
// Guest collection: signed-out visitors can mark haves, wants and slabs. It lives in this browser until they sign up, then moves into their account.
let SLABS=[],SLABFORM='',GSH=false;const GKEY='jonin_guest_v1';
function gLoad(){try{const g=JSON.parse(localStorage.getItem(GKEY)||'{}');(g.items||[]).forEach(([k,q])=>COLL.set(k,q));(g.conds||[]).forEach(([k,a])=>{if(Array.isArray(a))CONDS.set(k,a)});SLABS=Array.isArray(g.slabs)?g.slabs:[];GSH=!!g.slabsHave}catch(_){}}
function gSave(){try{if(!COLL.size&&!SLABS.length&&!GSH)localStorage.removeItem(GKEY);else localStorage.setItem(GKEY,JSON.stringify({items:[...COLL],conds:[...CONDS].filter(([k])=>COLL.has(k)),slabs:SLABS,slabsHave:GSH}))}catch(_){}}
// Profile setting: slabs count toward haves. Each slab remembers if it added a have, so removing it takes exactly that one back.
const slabsHave=()=>ME?!!(MYP&&MYP.slabs_count_as_haves):GSH;
function gCount(){return new Set([...COLL.keys()].map(k=>k.split('|')[0]).concat(SLABS.map(s=>s.card_id))).size}
const plural=(n,w)=>n+' '+w+(n===1?'':'s');
function nudge(){if(ME)return;let seen=null;try{seen=sessionStorage.getItem('jnudge')}catch(_){}if(seen)return;try{sessionStorage.setItem('jnudge','1')}catch(_){}
  const t=document.createElement('div');t.className='gtoast';t.setAttribute('role','status');
  t.innerHTML='<span>Saved on this device only. <b>Sign up free so you don’t lose your collection.</b></span><button class="pill" data-auth="up">Sign up</button><button class="x" aria-label="Dismiss">×</button>';
  t.addEventListener('click',e=>{if(e.target.closest('.x')||e.target.closest('[data-auth]'))setTimeout(()=>t.remove(),0)});document.body.appendChild(t);setTimeout(()=>t.remove(),12000)}
// Founding members: spots left from Supabase (null until loaded = treat as open).
// Founding offer shows only once spots are confirmed open (audit fix 2026-11-27). Starts from the last count this browser saw.
let FLEFT=(()=>{try{const v=JSON.parse(localStorage.getItem('jonin_fleft')||'null');return v&&typeof v.n==='number'&&Date.now()-v.t<864e5?v.n:null}catch(_){return null}})();const offerOpen=()=>FLEFT!==null&&FLEFT>0;
function loadFounding(){if(!sbc())return;/* kept in the card-page frame too: its sign-up box shows the founding offer only while spots are left */sb.rpc('founding_spots_left').then(r=>{if(!r.error&&typeof r.data==='number'){FLEFT=r.data;try{localStorage.setItem('jonin_fleft',JSON.stringify({n:FLEFT,t:Date.now()}))}catch(_){}paintAcct()}}).catch(()=>{})}
const foundingLine=()=>offerOpen()?`<p class="fnd"><svg class="jstar" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3.2l2.6 5.3 5.8.8-4.2 4.1 1 5.8L12 16.5l-5.2 2.7 1-5.8-4.2-4.1 5.8-.8z"/></svg> <b>Founding offer:</b> the first 20 members get Jonin Club free, forever.${FLEFT!==null?` <b>${plural(FLEFT,'spot')} left.</b>`:''}</p>`:(ME&&MYBADGE==='founding'?'':`<p class="fnd"><svg class="jstar" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3.2l2.6 5.3 5.8.8-4.2 4.1 1 5.8L12 16.5l-5.2 2.7 1-5.8-4.2-4.1 5.8-.8z"/></svg> <b>Founding spots are gone.</b> Jonin Club opens soon. <a href="/club/#join">Join the waitlist</a></p>`);
// Set progress for the card's set: cards you have any printing/edition of (same rule as the set pages).
function setProg(c){if(!D)return null;const ids=new Set();for(const [k,v] of COLL){const a=k.split('|');if(a[3]==='have'&&v>0)ids.add(a[0])}
  SLABS.forEach(x=>{if(slabsHave()&&x.counted)ids.add(x.card_id)});const cs=D.cards.filter(x=>x.s===c.s);return {name:(D.byId[c.s]||{}).name||'This set',have:cs.filter(x=>ids.has(cid(x))).length,total:cs.length}}
function progToast(c){const p=setProg(c);if(!p)return;const pct=p.total?Math.round(p.have/p.total*100):0;
  const t=document.createElement('div');t.className='gtoast ptoast';t.setAttribute('role','status');
  t.innerHTML=`<span class="pt"><span><b>${esc(p.name)}: ${p.have} / ${p.total}</b> cards</span><span class="pbar"><i style="width:${pct}%"></i></span>${ME?'':'<small>Saved on this device only.</small>'}</span>${ME?'':'<button class="pill" data-auth="up">Sign up to save</button>'}<button class="x" aria-label="Dismiss">×</button>`;
  t.addEventListener('click',e=>{if(e.target.closest('.x')||e.target.closest('[data-auth]'))setTimeout(()=>t.remove(),0)});
  document.querySelectorAll('.ptoast').forEach(x=>x.remove());document.body.appendChild(t);setTimeout(()=>t.remove(),7000)}
// Third card marked while signed out: ask them to sign up once (per device).
function askAtThird(c){if(ME||gCount()<3)return false;let done=null;try{done=localStorage.getItem('j3ask')}catch(_){}if(done)return false;try{localStorage.setItem('j3ask','1')}catch(_){}
  document.querySelectorAll('.ptoast').forEach(x=>x.remove());const p=setProg(c);openAuth('up','',p?`You’re at ${p.have} of ${p.total} cards in ${p.name}.`:'');return true}
// Sell prompts (2026-11-26, David's settings): a "Get an offer" box always on My collection, plus a one-time popup
// once someone has 25+ different cards or any slab. "Not now" (or ×) waits 30 days; tapping Get an offer stops it for good.
const SELL_URL='/sell/',SELL_MIN=25,SELL_WAIT=30*864e5,SKEY='jsell';
function sellCount(){const ids=new Set(SLABS.map(s=>s.card_id));for(const [k,v] of COLL){const a=k.split('|');if(a[3]==='have'&&v>0)ids.add(a[0])}return ids.size}
// Plain-text card list for the offer form: one line per card, haves by version plus slabs (counted slabs aren't listed twice).
function sellList(){if(!D)return'';const by={},rows={},sl={};D.cards.forEach(c=>by[cid(c)]=c);
  SLABS.forEach(s=>{if(s.counted){const k=s.card_id+'|'+s.printing+'|'+(s.edition||'');sl[k]=(sl[k]||0)+1}});
  for(const [k,v] of COLL){const a=k.split('|');if(a[3]!=='have'||!(v>0))continue;const q=v-(sl[a[0]+'|'+a[1]+'|'+a[2]]||0);if(q>0)(rows[a[0]]=rows[a[0]]||[]).push(a[1]+(a[2]?' '+a[2]:'')+' x'+q)}
  SLABS.forEach(s=>(rows[s.card_id]=rows[s.card_id]||[]).push(s.grader+' '+s.grade+' slab ('+s.printing+(s.edition?' '+s.edition:'')+')'+(s.cert?' cert '+s.cert:'')));
  return Object.keys(rows).map(id=>{const c=by[id],st=c&&D.byId[c.s];return (c?c.name:id)+' - '+(st?setLabel(st)+' ':'')+'#'+(c?c.n:id)+': '+rows[id].join(', ')}).join('\n')}
function sellState(){try{return localStorage.getItem(SKEY)}catch(_){return null}}
function sellSet(v){try{localStorage.setItem(SKEY,v)}catch(_){}}
const sellBox=()=>{const n=sellCount();return `<div class="sellbox"><span><b>Selling?</b> ${n?'Get an offer from Jonin or a trusted buyer. Your card list gets copied so you can paste it in.':'Get an offer from Jonin or a trusted buyer.'}</span><a class="pill" href="${SELL_URL}" target="_blank" rel="noopener" data-sellgo>Get an offer</a></div>`};
function sellAsk(){if(sellCount()<SELL_MIN&&!SLABS.length)return;const st=sellState();if(st==='done'||(st&&Date.now()-(+st||0)<SELL_WAIT))return;
  let seen=null;try{seen=sessionStorage.getItem('jsellv')}catch(_){}if(seen||document.querySelector('.sellask,.mile,.slabask'))return;
  const ao=$('#authov');if(ao&&!ao.hidden)return;try{sessionStorage.setItem('jsellv','1')}catch(_){}
  document.querySelectorAll('.gtoast').forEach(x=>x.remove());
  const t=document.createElement('div');t.className='gtoast sellask';t.setAttribute('role','dialog');t.setAttribute('aria-label','Get an offer');
  t.innerHTML=`<span class="st"><b>${sellCount()<SELL_MIN?'Nice slab.':'That’s a real collection.'}</b> Want an offer from Jonin or a trusted buyer?</span><a class="pill" href="${SELL_URL}" target="_blank" rel="noopener" data-sellgo>Get an offer</a><button type="button" class="clear" data-sellno>Not now</button><button class="x" aria-label="Not now">×</button>`;
  t.addEventListener('click',e=>{if(e.target.closest('[data-sellno]')||e.target.closest('.x')){sellSet(String(Date.now()));t.remove()}else if(e.target.closest('[data-sellgo]'))setTimeout(()=>t.remove(),0)});
  document.body.appendChild(t)}
document.addEventListener('click',e=>{if(!e.target.closest('[data-sellgo]'))return;sellSet('done');const l=sellList();
  if(l&&navigator.clipboard)navigator.clipboard.writeText('My Jonin collection ('+plural(sellCount(),'card')+'):\n'+l).catch(()=>{})});
// First-slab privacy question (David, 2026-11-26): once a signed-in member has a slab, ask one time whether their slabs
// are public or private. profiles.slab_privacy_asked_at marks it answered (× counts too). "Make public" turns on
// show_slabs, and sharing too if it's off, since slabs can't show on an unshared profile. Members who already had slabs
// get it the next time they open My collection (placeholder). Guests get it after they sign in.
async function slabAsk(){if(!ME||!MYP||!SLABS.length||MYP.slab_privacy_asked_at||document.querySelector('.slabask'))return;
  if(MYP.show_slabs&&MYP.sharing){slabMark({});return}
  document.querySelectorAll('.gtoast').forEach(x=>x.remove());
  const t=document.createElement('div');t.className='gtoast slabask';t.setAttribute('role','dialog');t.setAttribute('aria-label','Slab privacy');
  t.innerHTML=`<button class="x" aria-label="Keep private">×</button><span class="st"><b>Show your slabs on your public profile?</b><span class="mt">Grade only, never cert numbers. You can change this anytime on My collection.</span></span><button type="button" class="pill" data-slabpub>Make public</button><button type="button" class="clear" data-slabpriv>Keep private</button>`;
  t.addEventListener('click',e=>{if(e.target.closest('[data-slabpub]')){t.remove();slabMark({show_slabs:true,sharing:true})}
    else if(e.target.closest('[data-slabpriv]')||e.target.closest('.x')){t.remove();slabMark({})}});
  document.body.appendChild(t)}
async function slabMark(extra){const r=await sb.from('profiles').update(Object.assign({slab_privacy_asked_at:new Date().toISOString()},extra)).eq('id',ME.id).select().maybeSingle();
  if(!r.error&&r.data){MYP=r.data;if(extra.show_slabs){toast('Your slabs now show on your public profile.');if(window.jtrack)jtrack('slabs-public',{})}if(VIEW==='mine')renderMine()}}
// 100-card thank-you (2026-11-26): the first time a signed-in member has 100+ different cards (haves + slabs, same count as
// the sell popup), Supabase gives a one-time scroll bonus (claim_card_milestone, amount in xp_rules().cards_100) and we say thanks.
const MILE_AT=100;let MILEDONE=false;
async function mileCheck(){if(!ME||MILEDONE||sellCount()<MILE_AT||!sbc())return;MILEDONE=true;
  const r=await sb.rpc('claim_card_milestone').catch(()=>null);if(!r||r.error||!r.data){MILEDONE=false;return}
  if(!r.data.ok){if(r.data.why==='not_yet')MILEDONE=false;return}if(!r.data.new)return;
  const n=r.data.scrolls||0;document.querySelectorAll('.gtoast').forEach(x=>x.remove());
  const t=document.createElement('div');t.className='gtoast mile';t.setAttribute('role','dialog');t.setAttribute('aria-label','Thank you');
  t.innerHTML=`<button class="x" aria-label="Close">×</button><span class="mi">📜</span><b>100 cards logged. Thank you!</b><p>Every card you log helps build the Naruto CCG database. Here’s a little thank-you: <b style="font-size:inherit">+${n} ${n===1?'scroll':'scrolls'}</b>.</p><div class="mbtns"><a class="pill" href="/missions/">See your rank</a><button type="button" class="clear" data-mok>Keep going</button></div>`;
  t.addEventListener('click',e=>{if(e.target.closest('.x')||e.target.closest('[data-mok]'))t.remove()});
  document.body.appendChild(t);if(window.jtrack)jtrack('cards-100',{});loadFbPts();if(window.JoninAcct&&JoninAcct.refresh)JoninAcct.refresh()}
function toast(msg){const t=document.createElement('div');t.className='gtoast';t.setAttribute('role','status');t.innerHTML='<span>'+esc(msg)+'</span><button class="x" aria-label="Dismiss">×</button>';t.querySelector('.x').onclick=()=>t.remove();document.body.appendChild(t);setTimeout(()=>t.remove(),6000)}
async function mergeGuest(g){const rows=[];
  g.items.forEach(([k,q])=>{const a=k.split('|');const cur=COLL.get(k)||0;const n=Math.max(cur,q);if(n!==cur){COLL.set(k,n);if(a[3]==='have'&&n>cur&&g.conds&&g.conds.get(k))CONDS.set(k,g.conds.get(k));const row={user_id:ME.id,card_id:a[0],printing:a[1],edition:a[2],kind:a[3],qty:n,updated_at:new Date().toISOString()};if(a[3]==='have')row.conds=condsOf(k);rows.push(row)}});
  let ok=true;if(rows.length){const r=await sb.from('collection_items').upsert(rows);if(r.error)ok=false}
  if(g.slabs.length){const r=await sb.from('collection_slabs').insert(g.slabs.map(s=>({card_id:s.card_id,printing:s.printing,edition:s.edition,grader:s.grader,grade:s.grade,cert:s.cert||null,counted:!!s.counted}))).select('id,card_id,printing,edition,grader,grade,cert,counted,psa_status,psa_front');if(r.error)ok=false;else SLABS=SLABS.concat(r.data||[])}
  if(g.slabsHave&&MYP&&!MYP.slabs_count_as_haves){const r=await sb.from('profiles').update({slabs_count_as_haves:true}).eq('id',ME.id).select().maybeSingle();if(!r.error&&r.data)MYP=r.data}
  if(ok){try{localStorage.removeItem(GKEY)}catch(_){}const n=new Set(g.items.map(([k])=>k.split('|')[0]).concat(g.slabs.map(s=>s.card_id))).size;if(n)toast('Saved '+plural(n,'card')+' from this device to your account.')}}
const cid=c=>c.s+':'+c.n;
const ck=(id,p,e,k)=>id+'|'+p+'|'+e+'|'+k;
function qtyOf(c,kind){let n=0;for(const [k,v] of COLL)if(k.startsWith(cid(c)+'|')&&k.endsWith('|'+kind))n+=v;return n}
function marks(c){if(!ME&&!COLL.size&&!SLABS.length)return '<span class="mk"></span>';const h=qtyOf(c,'have'),w=qtyOf(c,'want');const sl=SLABS.filter(x=>x.card_id===cid(c));return `<span class="mk">${h?`<span class="h" title="You have ${h}">✓ ${h}</span>`:''}${w?'<span class="w" title="On your wants">♡</span>':''}${sl.length?`<span class="sl" title="${esc(sl.map(x=>x.grader+' '+x.grade).join(', '))}">▣ ${esc(sl[0].grader+' '+sl[0].grade)}${sl.length>1?' +'+(sl.length-1):''}</span>`:''}</span>`}
function refreshMarks(){if(VIEW==='sets'&&D)renderSets();document.querySelectorAll('.card[data-i]').forEach(b=>{const c=list[+b.dataset.i];const m=b.querySelector('.mk');if(c&&m)m.outerHTML=marks(c)})}
function sbc(){if(!sb&&window.supabase)sb=window.supabase.createClient(SUPA,SUPA_KEY);return sb}
async function setUser(u){if((u&&u.id)===(ME&&ME.id))return;if(u)sentClear();const guest=!ME?{items:[...COLL],conds:new Map(CONDS),slabs:SLABS.slice(),slabsHave:GSH}:null;ME=u;COLL.clear();CONDS.clear();COMPS.clear();SLABS=[];SLABFORM='';MYP=null;MEMBER=false;MYBADGE=null;NMNEXT=undefined;NMEDIT=false;LISTS=[];LITEMS=new Map();OPENL='';
  if(u){const [p,it,mb,sl]=await Promise.all([sb.from('profiles').select('*').eq('id',u.id).maybeSingle(),sb.from('collection_items').select('card_id,printing,edition,kind,qty,conds').limit(20000),sb.from('memberships').select('active,until,founding').eq('user_id',u.id).maybeSingle(),sb.from('collection_slabs').select('id,card_id,printing,edition,grader,grade,cert,counted,psa_status,psa_front').order('created_at').limit(5000)]);MYP=p.data;(it.data||[]).forEach(i=>{const k=ck(i.card_id,i.printing,i.edition,i.kind);COLL.set(k,i.qty);if(Array.isArray(i.conds))CONDS.set(k,i.conds)});SLABS=sl.data||[];const m=mb.data;MEMBER=!!(m&&m.active&&(!m.until||new Date(m.until)>new Date()));MYBADGE=MEMBER?(m.founding?'founding':'premium'):null;loadFbPts();loadLists();
    if(guest&&(guest.items.length||guest.slabs.length||guest.slabsHave))await mergeGuest(guest);setTimeout(mileCheck,1500);
    // Theme follows the account across devices.
    if(MYP&&MYP.theme&&window.joninSetTheme){let cur='';try{cur=localStorage.getItem('jtheme')||''}catch(_){}if(cur!==MYP.theme)joninSetTheme(MYP.theme)}
    // One-time setup page after sign-up (favorite characters, a few questions, theme). Finishing or skipping sets setup_done_at.
    if(MYP&&!MYP.setup_done_at){try{sessionStorage.setItem('jret',location.pathname+location.hash)}catch(_){}location.href='/welcome/';return}}else gLoad();
  EST=null;if(MEMBER)await loadEstimates();if(VIEW==='cards'&&D&&D.byId)renderCards(true);
  paintAcct();favFirst();refreshMarks();if(sel>=0&&list[sel])renderMyColl(list[sel]);if(VIEW==='mine'){if(ME||gCount())renderMine();else{history.replaceState(null,'',location.pathname);view('cards')}}}
let AUTHREADY=false;
function hasSession(){if(ME)return true;try{for(let i=0;i<localStorage.length;i++){const k=localStorage.key(i);if(/^sb-.*-auth-token$/.test(k)&&(!AUTHREADY||!sb))return true}}catch(_){}return false}
function paintAcct(){const n=ME?0:gCount(),el=$('#acct');if(el&&window.JoninAcct){const st={home:1,user:!!ME,uid:ME&&ME.id,handle:(MYP&&MYP.handle)||'',fav:MYP&&MYP.fav_character&&favName(MYP.fav_character)?MYP.fav_character:null,avatar:MYP&&MYP.avatar,badge:MYBADGE,pts:FBPTS,guest:n};const cc=JoninAcct.cached();const c=cc&&(ME?(!MYP&&cc.uid===ME.id):(!AUTHREADY&&hasSession()))?cc:null;if(c)Object.assign(st,c,{user:true,pts:FBPTS||c.pts,badge:MYBADGE||c.badge});el.innerHTML=JoninAcct.html(st);if(AUTHREADY&&(!ME||MYP))JoninAcct.cache(ME?st:null);}
  const b=$('#ctaband');if(!b)return;let off=false;try{off=Date.now()-(+localStorage.getItem('jcta')||0)<864e5}catch(_){} // closed banner comes back after a day
  // wait until we know whether they're signed in, so signed-in people never see a sign-up banner flash
  b.hidden=!!ME||off||hasSession();if(b.hidden)return;
  b.innerHTML=ctaHTML(n,offerOpen())}
function openAuth(mode,msg,prog){const up=mode==='up',reset=mode==='reset';if(typeof getOauth==='function')getOauth();
  if(up&&!msg){const p=sentGet();if(p){showSent(p.email);$('#authov').hidden=false;return}}
  $('#authform').innerHTML=`<h2>${reset?'Reset password':up?'Create your Jonin account':'Sign in'}</h2>
  <p class="mt" style="margin:0">${reset?'We will email you a link to set a new password.':up&&gCount()?`Save the ${plural(gCount(),'card')} you’ve marked so you don’t lose ${gCount()===1?'it':'them'}. It’s free.`:'Track your haves, wants and slabs, vote for the coolest cards, and share your list. It’s free.'}</p>
  ${up&&prog?`<p class="fprog">${esc(prog)}</p>`:''}${up?foundingLine():''}
  ${reset?'':`<div class="oauth"><button type="button" class="oa" data-oauth="google"><svg viewBox="0 0 48 48" width="18" height="18" aria-hidden="true"><path fill="#FFC107" d="M43.6 20.5H42V20H24v8h11.3C33.7 32.7 29.2 36 24 36c-6.6 0-12-5.4-12-12s5.4-12 12-12c3.1 0 5.8 1.2 7.9 3.1l5.7-5.7C34 6.1 29.3 4 24 4 12.9 4 4 12.9 4 24s8.9 20 20 20 20-8.9 20-20c0-1.3-.1-2.4-.4-3.5z"/><path fill="#FF3D00" d="m6.3 14.7 6.6 4.8C14.7 15.1 19 12 24 12c3.1 0 5.8 1.2 7.9 3.1l5.7-5.7C34 6.1 29.3 4 24 4 16.3 4 9.7 8.3 6.3 14.7z"/><path fill="#4CAF50" d="M24 44c5.2 0 9.9-2 13.4-5.2l-6.2-5.2C29.2 35.1 26.7 36 24 36c-5.2 0-9.6-3.3-11.3-7.9l-6.5 5C9.5 39.6 16.2 44 24 44z"/><path fill="#1976D2" d="M43.6 20.5H42V20H24v8h11.3c-.8 2.2-2.2 4.2-4.1 5.6l6.2 5.2C37 39.2 44 34 44 24c0-1.3-.1-2.4-.4-3.5z"/></svg>Continue with Google</button><button type="button" class="oa" data-oauth="discord"><svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path fill="#5865F2" d="M20.3 4.4A19.8 19.8 0 0 0 15.4 3l-.6 1.3a18.4 18.4 0 0 0-5.6 0L8.6 3a19.7 19.7 0 0 0-4.9 1.4C.6 9.1-.3 13.6.1 18.1a19.9 19.9 0 0 0 6 3l1.3-2.1a12.9 12.9 0 0 1-2-1l.5-.4a14.2 14.2 0 0 0 12.2 0l.5.4a12.9 12.9 0 0 1-2 1l1.3 2.1a19.8 19.8 0 0 0 6-3c.5-5.2-.8-9.7-3.6-13.7zM8 15.4c-1.2 0-2.2-1.1-2.2-2.4S6.8 10.6 8 10.6s2.2 1.1 2.2 2.4-1 2.4-2.2 2.4zm8 0c-1.2 0-2.2-1.1-2.2-2.4s1-2.4 2.2-2.4 2.2 1.1 2.2 2.4-1 2.4-2.2 2.4z"/></svg>Continue with Discord</button></div><div class="orline"><span>or use email</span></div>`}
  ${up?'<label>Username<input name="handle" autocomplete="username" placeholder="letters, numbers, _" maxlength="24"></label>':''}
  <label>Email<input name="email" type="email" autocomplete="email" required></label>
  ${reset?'':`<label>Password<input name="password" type="password" autocomplete="${up?'new-password':'current-password'}" minlength="8" required></label>`}
  <button class="go" type="submit">${reset?'Send reset link':up?'Sign up':'Sign in'}</button>
  <div class="msg" id="amsg">${esc(msg||'')}</div>
  <div class="tabs">${up?'<button type="button" class="clear" data-auth="in">I already have an account</button>':'<button type="button" class="clear" data-auth="up">Create an account</button>'}${up||reset?'':'<button type="button" class="clear" data-auth="reset">Forgot password?</button>'}</div>`;
  $('#authform').dataset.mode=mode;$('#authov').hidden=false;const f=$('#authform').querySelector('input');if(f)f.focus()}
// Show only the one-click buttons whose provider is switched on in Supabase (checked once, then every sign-in box uses it).
let OAUTH_ON=null,OAUTH_ASKED=false;function getOauth(){if(OAUTH_ASKED)return;OAUTH_ASKED=true;fetch(SUPA+'/auth/v1/settings',{headers:{apikey:SUPA_KEY}}).then(r=>r.json()).then(j=>{OAUTH_ON=j.external||{};paintOauth()}).catch(()=>{OAUTH_ON={}})}
// The card-page collection frame asks only when its sign-in box opens.
if(!document.documentElement.classList.contains('embed'))getOauth();
function paintOauth(){if(!OAUTH_ON)return;document.querySelectorAll('[data-oauth]').forEach(b=>{b.hidden=!OAUTH_ON[b.dataset.oauth]});document.querySelectorAll('.oauth').forEach(o=>{const any=[...o.querySelectorAll('[data-oauth]')].some(b=>!b.hidden);o.hidden=!any;const l=o.nextElementSibling;if(l&&l.classList.contains('orline'))l.hidden=!any})}
new MutationObserver(paintOauth).observe(document.getElementById('authform'),{childList:true});
// One-click sign-in with Google or Discord (Supabase OAuth). Comes back to the same page; a guest collection merges in as usual.
document.addEventListener('click',async e=>{const b=e.target.closest('[data-oauth]');if(!b||!sbc())return;e.preventDefault();b.disabled=true;
  const r=await sb.auth.signInWithOAuth({provider:b.dataset.oauth,options:{redirectTo:location.origin+location.pathname}});
  if(r.error){b.disabled=false;const m=$('#amsg');if(m)m.textContent=r.error.message||'Could not start sign-in.'}});
// "Check your inbox" screen after email sign-up (David, 2026-11-27). Replaces the form so it can't be re-submitted;
// Resend unlocks after 60s (Supabase allows one email per person per 60s, and each new email cancels the last link).
// Remembered in this tab for 30 min so reopening Sign up shows this screen, not a fresh form.
const RESEND_WAIT=60,SENT_KEEP=30*60e3;let SENTT=0;
function sentGet(){try{const p=JSON.parse(sessionStorage.getItem('jsent')||'null');return p&&p.email&&Date.now()-p.at<SENT_KEEP?p:null}catch(_){return null}}
function sentSet(email,at){try{sessionStorage.setItem('jsent',JSON.stringify({email,at:at||Date.now(),last:Date.now()}))}catch(_){}}
function sentClear(){try{sessionStorage.removeItem('jsent')}catch(_){}}
function showSent(email){const f=$('#authform');f.dataset.mode='sent';clearInterval(SENTT);
  f.innerHTML=`<h2>Check your inbox</h2>
  <p style="margin:0">We sent a link to <b>${esc(email)}</b>. Tap it to finish signing up.</p>
  <ul class="mt" style="margin:0;padding-left:18px;display:grid;gap:4px;font-size:13px">
    <li>It can take a minute to arrive. Check spam and Promotions too.</li>
    <li>Use the <b>newest</b> email. Sending a new one cancels the link in the old one.</li>
    ${gCount()?'<li>Your marked cards stay on this device and move into your account when you come back.</li>':''}
  </ul>
  <button class="go" type="button" id="aresend" disabled>Resend email</button>
  <div class="msg" id="amsg"></div>
  <div class="tabs"><button type="button" class="clear" id="adiff">Use a different email</button><button type="button" class="clear" data-auth="in">I already confirmed, sign in</button></div>`;
  const b=$('#aresend'),m=$('#amsg');
  const tick=()=>{let last=0;try{last=(JSON.parse(sessionStorage.getItem('jsent')||'{}').last)||0}catch(_){}
    const left=Math.ceil(RESEND_WAIT-(Date.now()-last)/1e3);if(left>0){b.disabled=true;b.textContent='Resend email in '+left+'s'}else{b.disabled=false;b.textContent='Resend email';clearInterval(SENTT)}};
  tick();SENTT=setInterval(tick,1000);
  b.onclick=async()=>{if(!sbc())return;b.disabled=true;m.className='msg';m.textContent='Sending…';
    const r=await sb.auth.resend({type:'signup',email,options:{emailRedirectTo:location.origin+'/#mine'}});
    if(r.error){const wait=/second|rate|429/i.test(r.error.message||'');if(wait){const p=sentGet();sentSet(email,p&&p.at)}m.className='msg err';m.textContent=wait?'Almost: wait a few more seconds, then try again.':(r.error.message||'Could not resend. Try again in a minute.');tick();clearInterval(SENTT);SENTT=setInterval(tick,1000);return}
    const p=sentGet();sentSet(email,p&&p.at);m.textContent='Sent a new email. Use that one: the earlier link no longer works.';tick();clearInterval(SENTT);SENTT=setInterval(tick,1000);if(window.jtrack)jtrack('signup-email-resend',{})};
  $('#adiff').onclick=()=>{clearInterval(SENTT);sentClear();openAuth('up')}}
// Clicking an old or expired email link lands here with an error in the address: explain and offer the next step.
(()=>{const h=location.hash||'';if(!/error_code=|error=access_denied/.test(h))return;const q=new URLSearchParams(h.slice(1)),code=q.get('error_code')||'';
  history.replaceState(null,'',location.pathname+location.search);
  setTimeout(()=>{if(ME)return;const p=sentGet();
    if(p&&/otp_expired|access_denied/.test(code+q.get('error'))){showSent(p.email);$('#authov').hidden=false;const m=$('#amsg');if(m){m.className='msg err';m.textContent='That link expired or was replaced by a newer email. Open the newest email, or resend below.'}}
    else openAuth('in',code==='otp_expired'?'That email link expired or was replaced by a newer one. If you already confirmed, sign in. Otherwise sign up again to get a fresh link.':'That link didn’t work. Try signing in, or sign up again for a fresh link.')},400)})();
$('#authform').addEventListener('submit',async e=>{e.preventDefault();const f=e.target,mode=f.dataset.mode,m=$('#amsg'),btn=f.querySelector('.go');
  const email=f.email.value.trim(),pw=f.password?f.password.value:'',handle=f.handle?f.handle.value.trim():'';
  const err=t=>{m.className='msg err';m.textContent=t};m.className='msg';
  if(!sbc())return err('Could not reach the account service. Try again in a moment.');
  if(!/^\S+@\S+\.\S+$/.test(email))return err('Enter a valid email.');
  if(mode!=='reset'&&pw.length<8)return err('Password needs at least 8 characters.');
  if(mode==='up'&&handle&&!/^[A-Za-z0-9_]{3,24}$/.test(handle))return err('Username: 3–24 letters, numbers or _.');
  btn.disabled=true;m.textContent='One moment…';
  try{let r;
    if(mode==='up'){r=await sb.auth.signUp({email,password:pw,options:{data:{handle},emailRedirectTo:location.origin+'/#mine'}});if(r.error)throw r.error;
      if(!r.data.session){const u=r.data.user;
        // Supabase answers "success" for an email that already has a confirmed account (no identities): send them to sign in.
        if(u&&Array.isArray(u.identities)&&!u.identities.length){btn.disabled=false;openAuth('in','That email already has an account. Sign in below, or use Forgot password.');const ie=$('#authform').querySelector('[name=email]');if(ie)ie.value=email;return}
        sentSet(email);showSent(email);if(window.jtrack)jtrack('signup-email-sent',{});return}}
    else if(mode==='in'){r=await sb.auth.signInWithPassword({email,password:pw});if(r.error)throw r.error}
    else{r=await sb.auth.resetPasswordForEmail(email,{redirectTo:location.origin+'/#reset'});if(r.error)throw r.error;m.textContent='If that email has an account, a reset link is on its way.';btn.disabled=false;return}
    $('#authov').hidden=true}
  catch(x){err(x.message||'Something went wrong.')}btn.disabled=false});
async function setItem(c,p,ed,kind,qty,conds){const id=cid(c),k=ck(id,p,ed,kind),before=COLL.get(k),cbefore=CONDS.get(k);
  if(kind==='have'){const a=conds||condsOf(k);while(a.length<qty)a.push('NM');a.length=Math.max(0,qty);if(qty>0)CONDS.set(k,a);else CONDS.delete(k)}
  if(qty>0)COLL.set(k,qty);else COLL.delete(k);renderMyColl(c);refreshMarks();
  if(qty>0&&kind==='have'){if(!askAtThird(c))progToast(c);setTimeout(sellAsk,2500)}
  if(qty>0&&!before&&window.jtrack)jtrack('collection-add',{kind,signed_in:!!ME});
  if(!ME){gSave();paintAcct();return}
  const r=qty>0?await sb.from('collection_items').upsert(Object.assign({user_id:ME.id,card_id:id,printing:p,edition:ed,kind,qty,updated_at:new Date().toISOString()},kind==='have'?{conds:condsOf(k)}:{})):await sb.from('collection_items').delete().match({user_id:ME.id,card_id:id,printing:p,edition:ed,kind});
  if(r.error){if(before)COLL.set(k,before);else COLL.delete(k);if(cbefore)CONDS.set(k,cbefore);else CONDS.delete(k);renderMyColl(c);refreshMarks();const b=$('#mycoll');if(b)b.insertAdjacentHTML('beforeend','<p class="mt" style="color:#ff8b8b;margin:0">Could not save. Check your connection and try again.</p>')}else if(qty>0&&kind==='have')mileCheck()}
const combos=c=>{const eds=(c.ed||[]).filter(Boolean);const ps=(c.v&&c.v.length?c.v:['Normal']);return (eds.length?eds:['']).flatMap(e=>ps.map(p=>[p,e]))};
const GRADERS=['PSA','BGS','CGC','SGC','TAG','Other'];
// PSA cert lookup (2026-11-26): typing a PSA cert calls the psa-lookup Edge Function, which fills in the grade, checks the
// cert is this card and brings PSA's slab photo. Verification itself happens in Supabase (slab_apply_psa), not here.
const psaTag=s=>s.psa_status==='verified'?'<span class="psv" title="PSA cert matches this card">✓ PSA verified</span>':s.psa_status==='mismatch'?'<span class="psx" title="The PSA cert is for a different card">⚠ Cert is a different card</span>':s.psa_status==='pending'?'<span class="mt" title="PSA lookups are limited per day; this one runs automatically">PSA check pending</span>':s.psa_status==='not_found'?'<span class="psx">PSA has no record of this cert</span>':'';
let PSAT=0,PSAQ='';
function psaInput(inp){const f=$('#slabf'),out=$('#psaprev');if(!f||!out||!ME)return;const cert=inp.value.replace(/\D/g,'');clearTimeout(PSAT);
  if(cert.length<7){out.innerHTML='<span class="mt">PSA cert? We’ll fill in the grade and check it matches this card.</span>';PSAQ='';return}
  if(cert===PSAQ)return;PSAT=setTimeout(()=>psaLook(cert),600)}
async function psaLook(cert){const c=sel>=0?list[sel]:null,out=$('#psaprev'),f=$('#slabf');if(!c||!out||!f)return;PSAQ=cert;out.innerHTML='<span class="mt">Checking PSA…</span>';
  let r;try{r=await sb.functions.invoke('psa-lookup',{body:{cert,card_id:cid(c)}})}catch(_){r={error:1}}
  if(PSAQ!==cert||!$('#psaprev'))return;const d=r&&r.data;
  if(r.error||!d){out.innerHTML='<span class="mt">Couldn’t reach PSA right now. Save it and we’ll check it automatically.</span>';return}
  if(d.status==='ok'){const g=f.querySelector('[name=g]'),gr=f.querySelector('[name=gr]');if(g)g.value='PSA';if(gr&&d.grade)gr.value=d.grade;
    out.innerHTML=`${/^https:\/\//.test(d.front||'')?`<img class="psth" src="${esc(d.front)}" alt="PSA slab photo">`:''}<span>${d.match?'<span class="psv">✓ Matches this card</span>':'<span class="psx">⚠ This cert looks like a different card</span>'} <b>${esc(d.grade_label||'')}</b><br><span class="mt">${esc([d.year,d.brand,d.subject,d.card_number?'#'+d.card_number:'',d.variety].filter(Boolean).join(' · '))}</span></span>`}
  else if(d.status==='not_found')out.innerHTML='<span class="psx">PSA has no record of this cert. Check the number.</span>';
  else if(d.status==='queued')out.innerHTML='<span class="mt">PSA lookups are maxed out for today. Save it and we’ll check it automatically within a day.</span>';
  else out.innerHTML='<span class="mt">That doesn’t look like a PSA cert number.</span>'}
document.addEventListener('input',e=>{if(e.target&&e.target.name==='ce'&&e.target.closest('#slabf'))psaInput(e.target)});
function slabBlock(c){const id=cid(c),mine=SLABS.filter(s=>s.card_id===id),cs=combos(c);
  const form=SLABFORM===id?`<div class="slabf" id="slabf">${cs.length>1?`<label class="wide">Version<select name="v">${cs.map(([p,e],j)=>`<option value="${j}">${esc(p)}${e?' · '+esc(e):''}</option>`).join('')}</select></label>`:''}
    <label>Grader<select name="g">${GRADERS.map(g=>`<option>${g}</option>`).join('')}</select></label>
    <label>Grade<input name="gr" maxlength="12" placeholder="10, 9.5, Pristine…"></label>
    <label class="wide">Cert number (optional)<input name="ce" maxlength="30" inputmode="numeric" placeholder="e.g. 84512377"></label><div class="wide psap" id="psaprev">${ME?'<span class="mt">PSA cert? We’ll fill in the grade and check it matches this card.</span>':''}</div>
    <div class="row"><button type="button" class="pill" data-slabsave>Save slab</button><button type="button" class="clear" data-slabcancel>Cancel</button><span class="mt" id="slabmsg"></span></div></div>`:'';
  return `<div class="slabs"><div class="slh"><b>Slabs${mine.length?' · '+mine.length:''}</b>${SLABFORM===id?'':'<button type="button" class="clear" data-slabadd>+ Add a slab</button>'}</div>
  ${mine.map(s=>`<div class="slab">${/^https:\/\//.test(s.psa_front||'')?`<a href="https://www.psacard.com/cert/${encodeURIComponent(s.cert)}" target="_blank" rel="noopener"><img class="psth" src="${esc(s.psa_front)}" alt="PSA slab photo" loading="lazy"></a>`:''}<span class="sg">${esc(s.grader)} ${esc(s.grade)}</span>${psaTag(s)}<span class="mt">${esc(s.printing)}${s.edition?' · '+esc(s.edition):''}${s.cert?' · cert '+esc(s.cert):''}</span><button type="button" class="clear" data-slabdel="${esc(s.id)}" aria-label="Remove this slab">×</button></div>`).join('')}${form}</div>`}
function renderMyColl(c){const box=$('#mycoll');if(!box)return;const n=gCount();
  const note=ME?'':`<div class="gsave"><span>${n?'Saved on this device only.':'Mark what you have. No account needed to start.'}</span><button type="button" class="pill" data-auth="up">${n?'Sign up so you don’t lose it':'Make a free account'}</button></div>`;
  box.innerHTML='<h4>Your collection</h4>'+note+combos(c).map(([p,e],j)=>{const h=COLL.get(ck(cid(c),p,e,'have'))||0,w=COLL.has(ck(cid(c),p,e,'want'));const f=FOILS[p];
    return `<div class="mrow"><span>${f?`<span class="fx f-${f[0]}" style="font-size:5px;vertical-align:middle;margin-right:6px" aria-hidden="true"></span>`:''}${esc(p)}${e?` · <span class="mt">${esc(e)}</span>`:''}</span>
    <span class="step${h?' on':''}" aria-label="How many you have"><button data-have="${j}" data-d="-1" aria-label="One less">−</button><b>${h}</b><button data-have="${j}" data-d="1" aria-label="One more">+</button></span>
    <button class="wt" data-want="${j}" aria-pressed="${w}">♡ Want</button></div>${h?condBlock(c,p,e,j):''}`}).join('')+slabBlock(c)+listBlock(c);
  if(MEMBER&&combos(c).some(([p,e])=>COLL.get(ck(cid(c),p,e,'have')))&&!COMPS.has(cid(c)))cardComps(cid(c)).then(()=>{if(sel>=0&&list[sel]===c)renderMyColl(c)})}
// Condition of each copy (new copies start NM), and for Jonin Club: the price for that condition plus the matching sold comps.
const CMAX=12;
function condBlock(c,p,e,j){const k=ck(cid(c),p,e,'have'),cs=condsOf(k),id=cid(c);
  const pick=(cd,i)=>`<select class="cnd" data-cond="${j}" data-ci="${i}" aria-label="Condition of copy ${i+1}">${CONDL.map(([v,l])=>`<option value="${v}"${v===cd?' selected':''} title="${l}">${v}</option>`).join('')}</select>`;
  const sel=`<div class="cnds"><span class="mt">${cs.length>1?'Condition of each copy':'Condition'}</span>${cs.slice(0,CMAX).map(pick).join('')}${cs.length>CMAX?`<span class="mt">+${cs.length-CMAX} more (NM)</span>`:''}</div>`;
  if(!MEMBER)return sel+`<a class="cpx lock" href="/club/"><svg class="jstar" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3.2l2.6 5.3 5.8.8-4.2 4.1 1 5.8L12 16.5l-5.2 2.7 1-5.8-4.2-4.1 5.8-.8z"/></svg> Price for this condition and matching sold comps · Jonin Club</a>`;
  if(!EST)return sel;
  const done=COMPS.get(id),all=done&&done.v||null,uniq=[...new Set(cs)];
  return sel+uniq.map(cd=>{const est=estCond(id,p,e,cd),n=cs.filter(x=>x===cd).length;
    const cm=all?compsFor(all,p,e,cd).slice(0,3):[];
    const val=est?`<b>≈ ${money(+est.estimate)}</b>${n>1?` <span class="mt">each · ${money(est.estimate*n)} for ${n}</span>`:''}<span class="mt"> · ${est.exact?plural(est.sales_count,cd+' sale'):'no '+cd+' sales yet, all-conditions estimate'}</span>`:`<span class="mt">No ${cd} sales yet</span>`;
    return `<div class="cpx"><span class="cb">${cd}</span>${val}${cm.length?`<span class="cmps">${cm.map(x=>{const t=`${money(+x.price)} · ${esc(shortDate(x.sold_at))}`;return /^https:\/\//.test(x.url||'')?`<a href="${esc(x.url)}${x.url.includes('?')?'&amp;':'?'}${EPN}" target="_blank" rel="sponsored noopener" title="Open this ${cd} comp on eBay">${t} ↗</a>`:`<a>${t}</a>`}).join('')}</span>`:''}</div>`}).join('')}
async function saveSlab(c){const f=$('#slabf');if(!f)return;const msg=$('#slabmsg');const cs=combos(c),j=f.querySelector('[name=v]')?+f.querySelector('[name=v]').value:0;const [p,e]=cs[j]||['Normal',''];
  const grade=f.querySelector('[name=gr]').value.trim(),cert=f.querySelector('[name=ce]').value.trim(),grader=f.querySelector('[name=g]').value;
  if(!grade){msg.textContent='Add the grade.';return}
  const row={card_id:cid(c),printing:p,edition:e||'',grader,grade:grade.slice(0,12),cert:cert.slice(0,30)||null,counted:slabsHave()};
  if(ME){msg.textContent='Saving…';const r=await sb.from('collection_slabs').insert(row).select('id,card_id,printing,edition,grader,grade,cert,counted,psa_status,psa_front').single();if(r.error){msg.textContent='Could not save. Try again.';return}SLABS.push(r.data);mileCheck();slabAsk()}
  else{SLABS.push(Object.assign({id:'g'+Date.now()},row));gSave();paintAcct();nudge()}
  SLABFORM='';setTimeout(sellAsk,2500);if(row.counted){const k=ck(row.card_id,row.printing,row.edition,'have');await setItem(c,row.printing,row.edition,'have',(COLL.get(k)||0)+1)}renderMyColl(c);refreshMarks()}
async function delSlab(c,id){const i=SLABS.findIndex(s=>String(s.id)===id);if(i<0)return;const [old]=SLABS.splice(i,1);renderMyColl(c);refreshMarks();
  const unhave=()=>{if(!old.counted)return;const k=ck(old.card_id,old.printing,old.edition,'have');return setItem(c,old.printing,old.edition,'have',Math.max(0,(COLL.get(k)||0)-1))};
  if(!ME){gSave();await unhave();paintAcct();return}const r=await sb.from('collection_slabs').delete().eq('id',old.id);if(r.error){SLABS.splice(i,0,old);renderMyColl(c);refreshMarks();return}await unhave()}
async function toggleSlabsHave(){const v=!slabsHave();if(!ME){GSH=v;gSave();renderMine();return}if(!MYP)return;const r=await sb.from('profiles').update({slabs_count_as_haves:v}).eq('id',ME.id).select().maybeSingle();if(!r.error&&r.data)MYP=r.data;renderMine()}
function collClick(t,e){
  if(t.dataset.auth){e.preventDefault();openAuth(t.dataset.auth)}
  else if(t.dataset.authclose!=null)$('#authov').hidden=true;
  else if(t.dataset.signout!=null)sb&&sb.auth.signOut();
  else if(t.dataset.ctax!=null){try{localStorage.setItem('jcta',String(Date.now()))}catch(_){}$('#ctaband').hidden=true}
  else if(t.dataset.slabadd!=null){const c=list[sel];if(!c)return;SLABFORM=cid(c);renderMyColl(c);const g=$('#slabf [name=gr]');if(g)g.focus()}
  else if(t.dataset.slabcancel!=null){const c=list[sel];SLABFORM='';if(c)renderMyColl(c)}
  else if(t.dataset.slabsave!=null){const c=list[sel];if(c)saveSlab(c)}
  else if(t.dataset.slabdel!=null){const c=list[sel];if(c)delSlab(c,t.dataset.slabdel)}
  else if(t.dataset.have!=null||t.dataset.want!=null){const c=list[sel];if(!c)return;const [p,ed]=combos(c)[+(t.dataset.have??t.dataset.want)];
    if(t.dataset.have!=null){const k=ck(cid(c),p,ed,'have');setItem(c,p,ed,'have',Math.max(0,(COLL.get(k)||0)+ +t.dataset.d))}
    else{const k=ck(cid(c),p,ed,'want');setItem(c,p,ed,'want',COLL.has(k)?0:1)}}
  else if(t.dataset.mtab){MTAB=t.dataset.mtab;MISS='';LAST?listView(...LAST):renderMine()}
  else if(t.dataset.miss!=null){MISS=MISS===t.dataset.miss?'':t.dataset.miss;listView(...LAST)}
  else if(t.dataset.redosetup!=null)redoSetup();
  else if(t.dataset.share!=null)toggleShare();
  else if(t.dataset.showslabs!=null)toggleShowSlabs();
  else if(t.dataset.nmsave!=null){const i=$('#nmin');saveName(i?i.value:'')}
  else if(t.dataset.nmedit!=null){NMEDIT=true;renderMine();const i=$('#nmin');if(i){i.focus();i.select()}}
  else if(t.dataset.nmcancel!=null){NMEDIT=false;renderMine()}
  else if(t.dataset.igsave!=null){const i=$('#igin');saveIg(i?i.value:'')}
  else if(t.dataset.igedit!=null){IGEDIT=true;renderMine();const i=$('#igin');if(i)i.focus()}
  else if(t.dataset.igcancel!=null){IGEDIT=false;renderMine()}
  else if(t.dataset.igdel!=null)saveIg(null);
  else if(t.dataset.favedit!=null){FAVEDIT=true;renderMine()}
  else if(t.dataset.favcancel!=null){FAVEDIT=false;renderMine()}
  else if(t.dataset.avpick!=null){e.preventDefault();saveAv(t.dataset.avpick)}
  else if(t.dataset.favpick!=null){e.preventDefault();saveFav(t.dataset.favpick)}
  else if(t.dataset.slabhave!=null)toggleSlabsHave();
  else if(t.dataset.export!=null)exportColl();
  else if(t.dataset.copy!=null){navigator.clipboard&&navigator.clipboard.writeText(t.dataset.copy).then(()=>{t.textContent='Copied'})}}
let MTAB='have';
function cardsWith(kind,src){const ids=new Set();for(const k of src.keys()){const a=k.split('|');if(a[3]===kind)ids.add(a[0])}return D.cards.filter(c=>ids.has(cid(c)))}
function progress(src){const have=new Set();for(const k of src.keys()){const a=k.split('|');if(a[3]==='have')have.add(a[0])}
  return D.sets.map(s=>{const n=D.cards.filter(c=>c.s===s.id&&have.has(cid(c))).length;return {s,n}}).filter(x=>x.n)}
let MISS='',LAST=null;
// My collection sort & filter (2026-11-27). PLACEHOLDER choices for David: default sort is Set & number (binder order);
// filters are search, set, rarity, card type, plus version (foil / 1st Edition) on Haves & Wants and grader on Slabs.
// Set and rarity menus only list what's in the tab. Choices stay put while you move around the site, until a reload.
let CF={q:'',set:'',rar:'',type:'',ver:'',sort:'',tab:''},MCTX=null;
const CVER=[['fo','Foil'],['nf','Non-foil'],['st','1st Edition'],['un','Unlimited']];
function cfSorts(){const a=[['','Set & number'],['px-d','Market value: high to low'],['px','Market value: low to high'],['name','Name A–Z'],['name-d','Name Z–A'],['rar-d','Rarity: high to low'],['rar','Rarity: low to high'],['set-d','Newest sets first']];
  if(MTAB==='have')a.push(['qty-d','Most copies']);if(MTAB==='slab')a.push(['grade-d','Highest grade']);return a}
function cfInfo(src){const kind=MTAB==='want'?'want':'have',m=new Map();for(const [k,q] of src){const a=k.split('|');if(a[3]!==kind||(kind==='have'&&!q))continue;
  const o=m.get(a[0])||{fo:0,nf:0,st:0,un:0,q:0},n=kind==='have'?q:1;if(/foil|Super Rare|Gold/i.test(a[1]))o.fo+=n;else o.nf+=n;if(/1st/.test(a[2]))o.st+=n;else o.un+=n;o.q+=n;m.set(a[0],o)}return m}
const gradeNum=g=>{const v=parseFloat(String(g||'').replace(/[^\d.]/g,''));return isNaN(v)?-1:v};
function cfApply(items,src,SL){const f=CF,info=MTAB==='slab'?null:cfInfo(src);const ws=f.q.trim().toLowerCase().split(/\s+/).filter(Boolean);
  let out=items.filter(c=>{if(f.set&&c.s!==f.set)return false;if(f.rar&&c.src!==f.rar)return false;if(f.type&&c.t!==f.type)return false;
    if(f.ver){if(MTAB==='slab'){if(!SL.some(x=>x.card_id===cid(c)&&x.grader===f.ver))return false}else{const o=info.get(cid(c));if(!o||!o[f.ver])return false}}
    if(ws.length){const h=hayOf(c);if(!ws.every(w=>numHit(w,c.n)||h.includes(w)))return false}return true});
  const k=f.sort;if(!k)return out;
  if(k==='qty-d'){const ix=new Map(out.map((c,i)=>[c,i]));return out.slice().sort((x,y)=>((info.get(cid(y))||{}).q||0)-((info.get(cid(x))||{}).q||0)||ix.get(x)-ix.get(y))}
  if(k==='grade-d'){const best=new Map();SL.forEach(x=>best.set(x.card_id,Math.max(best.get(x.card_id)??-1,gradeNum(x.grade))));const ix=new Map(out.map((c,i)=>[c,i]));return out.slice().sort((x,y)=>(best.get(cid(y))??-1)-(best.get(cid(x))??-1)||ix.get(x)-ix.get(y))}
  const keep=S.sort;S.sort=k;try{out=sorted(out)}finally{S.sort=keep}return out}
function cfBar(base,SL){if(MTAB==='lists'||base.length<2&&!cfOn())return '';
  const cnt=(f)=>{const m=new Map();base.forEach(c=>{const v=f(c);if(v)m.set(v,(m.get(v)||0)+1)});return m};
  const sets=cnt(c=>c.s),rars=cnt(c=>c.src),types=cnt(c=>c.t);
  const opt=(v,l,on)=>`<option value="${esc(v)}"${on===v?' selected':''}>${esc(l)}</option>`;
  const sel=(k,lbl,all,opts)=>`<label class="cfsel${CF[k]?' on':''}"><span>${lbl}</span><select data-cf="${k}">${opt('',all,CF[k])}${opts.join('')}</select></label>`;
  const setOpts=D.sets.filter(s=>sets.has(s.id)).map(s=>opt(s.id,setLabel(s)+' · '+s.name+' ('+sets.get(s.id)+')',CF.set));
  const rarOpts=Object.keys(RORD).sort((a,b)=>RORD[b]-RORD[a]).filter(r=>rars.has(r)).map(r=>opt(r,(RNAME[r]||r)+' ('+rars.get(r)+')',CF.rar));
  const typeOpts=TYPE_ORD.filter(t=>types.has(t)).map(t=>opt(t,t+' ('+types.get(t)+')',CF.type));
  const verOpts=MTAB==='slab'?GRADERS.filter(g=>SL.some(x=>x.grader===g)).map(g=>opt(g,g,CF.ver)):CVER.map(([v,l])=>opt(v,l,CF.ver));
  return `<div class="cfbar"><input id="cfq" type="search" placeholder="Search your ${MTAB==='slab'?'slabs':MTAB==='want'?'wants':'cards'}" value="${esc(CF.q)}" autocomplete="off" aria-label="Search this tab">
  ${sel('set','Set','All sets',setOpts)}${sel('rar','Rarity','All rarities',rarOpts)}${types.size>1||CF.type?sel('type','Type','All types',typeOpts):''}${sel('ver',MTAB==='slab'?'Grader':'Version',MTAB==='slab'?'All graders':'All versions',verOpts)}
  <label class="cfsel cfsort"><span>Sort</span><select data-cf="sort">${cfSorts().map(([v,l])=>opt(v,l,CF.sort)).join('')}</select></label>
  <span class="cfn mt" id="cfn">${cfCount()}</span>${cfOn()?'<button type="button" class="clear" data-cfreset>Clear</button>':''}</div>`}
const cfOn=()=>!!(CF.q.trim()||CF.set||CF.rar||CF.type||CF.ver);
const cfCount=()=>cfOn()&&MCTX?`Showing ${list.length.toLocaleString()} of ${MCTX.n.toLocaleString()}`:'';
function mGrid(items,SL,ro,total){if(!cfOn())total=0;return items.length?items.map((c,i)=>(()=>{if(MTAB!=='slab')return tile(c,i);const mine=SL.filter(x=>x.card_id===cid(c)),ph=mine.map(x=>ro?x.front:x.psa_front).find(u=>/^https:\/\//.test(u||''));
    return tile(ph?Object.assign({},c,{img:ph}):c,i,`<div class="slg">${mine.map(x=>esc(x.grader+' '+x.grade)+((ro?x.verified:x.psa_status==='verified')?' ✓':'')).join(' · ')}</div>`)})()).join(''):total?`<p class="empty">No cards match these filters. <button type="button" class="clear" data-cfreset>Clear filters</button></p>`:`<p class="empty">${ro?'Nothing here yet.':MTAB==='slab'?'No slabs yet. Open any card and tap + Add a slab.':MTAB==='have'?'No cards yet. Open any card and use + to add the printings you have.':'No wants yet. Open any card and tap ♡ Want.'}</p>`}
function cfGridOnly(){if(!MCTX||!LAST)return;const el=$("#mgrid");if(!el)return listView(...LAST);
  const ids=new Set(MCTX.SL.map(x=>x.card_id));const base=MTAB==='slab'?D.cards.filter(c=>ids.has(cid(c))):cardsWith(MTAB,MCTX.src);
  list=cfApply(base,MCTX.src,MCTX.SL);el.innerHTML=mGrid(list,MCTX.SL,MCTX.ro,base.length);const n=$('#cfn');if(n)n.textContent=cfCount();
  const bar=document.querySelector('.cfbar');if(bar){const has=bar.querySelector('[data-cfreset]');if(cfOn()&&!has)bar.insertAdjacentHTML('beforeend','<button type="button" class="clear" data-cfreset>Clear</button>');else if(!cfOn()&&has)has.remove()}}
let CFT=0;
document.addEventListener('input',e=>{if(e.target&&e.target.id==='cfq'){CF.q=e.target.value;clearTimeout(CFT);CFT=setTimeout(cfGridOnly,120)}});
document.addEventListener('change',e=>{const k=e.target&&e.target.dataset&&e.target.dataset.cf;if(!k||!LAST)return;CF[k]=e.target.value;listView(...LAST)});
document.addEventListener('click',e=>{if(e.target.closest('[data-cfreset]')){CF=Object.assign(CF,{q:'',set:'',rar:'',type:'',ver:''});if(LAST)listView(...LAST)}});

// Jonin Club collection tools (David, 2026-11-26): collection value, spreadsheet export, profile badge.
// Value: each have is priced by the Raw estimate of its exact version (printing + edition); if that version has no
//   estimate, the same printing in any edition is used (PLACEHOLDER fallback). Slabs use the same grader + grade, exact
//   version first, then any edition (PLACEHOLDER). Copies with no matching estimate are left out and counted as unpriced.
function estFor(card,printing,edition,grader,grade){const rows=(EST&&EST.get(card))||[];const g=grader||'Raw';
  const ok=r=>(r.grader||'Raw')===g&&(g==='Raw'||String(r.grade||'')===String(grade||''))&&r.printing===printing;
  const ed=x=>x||'Unlimited';return rows.find(r=>ok(r)&&ed(r.edition)===ed(edition))||rows.filter(ok).sort((a,b)=>b.sales_count-a.sales_count)[0]||null}
function collValue(src){let raw=0,rawN=0,rawAll=0,sl=0,slN=0;const per=new Map();
  for(const [k,q] of src){const a=k.split('|');if(a[3]!=='have'||!q)continue;rawAll+=q;const cs=src===COLL?condsOf(k):Array(q).fill('NM');for(const cd of cs){const e=estCond(a[0],a[1],a[2],cd);if(e){raw+=+e.estimate;rawN++;per.set(a[0],(per.get(a[0])||0)+(+e.estimate))}}}
  for(const x of SLABS){const e=estFor(x.card_id,x.printing,x.edition,x.grader,x.grade);if(e){sl+=+e.estimate;slN++;per.set(x.card_id,(per.get(x.card_id)||0)+(+e.estimate))}}
  return {raw,rawN,rawAll,sl,slN,slAll:SLABS.length,per}}
// Free collection value (David, 2026-11-27): signed-in members who aren't in Jonin Club get the totals from
// my_collection_value() (db/037) — same pricing rules as collValue, but the per-card estimates stay Club.
// Signed-out visitors see a sign-up prompt in its place. Refetched ~1.5s after the collection changes so saves land first.
let FCV=null,FCVK='',FCVT=0;
function freeCV(){if(!ME||MEMBER||!sbc())return null;const k=[...COLL].map(([a,q])=>a+q).join()+'|'+[...CONDS].map(([a,c])=>a+c).join()+'|'+SLABS.map(x=>x.id||x.card_id).join();
  if(k===FCVK)return FCV;FCVK=k;clearTimeout(FCVT);FCVT=setTimeout(()=>sb.rpc('my_collection_value').then(r=>{if(r.error||!ME||MEMBER)return;FCV=(r.data||[])[0]||null;if(LAST)listView(...LAST)}).catch(()=>{}),1500);return FCV}
const freeStat=(l,v,n,all)=>v!=null?`<div class="vstat" title="Estimated from recent sales. ${n} of ${all} priced."><b>≈ ${money(v)}</b><span>${l} · ${n} of ${all} priced</span></div>`:`<div class="vstat"><b>…</b><span>${l}</span></div>`;
const signStat=l=>`<button type="button" class="lstat" onclick="openAuth('up')"><b>+</b><span>${l} · Sign up free</span></button>`;
const lockStat=l=>`<a class="lstat" href="/club/"><b><svg class="jstar" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3.2l2.6 5.3 5.8.8-4.2 4.1 1 5.8L12 16.5l-5.2 2.7 1-5.8-4.2-4.1 5.8-.8z"/></svg></b><span>${l} · Jonin Club</span></a>`;
const badgeHtml=b=>b==='founding'?'<span class="pbadge fnd2" title="One of the first 20 members"><svg class="jstar" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3.2l2.6 5.3 5.8.8-4.2 4.1 1 5.8L12 16.5l-5.2 2.7 1-5.8-4.2-4.1 5.8-.8z"/></svg> Founding member</span>':b==='premium'?'<span class="pbadge" title="Jonin Club member"><svg class="jstar" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3.2l2.6 5.3 5.8.8-4.2 4.1 1 5.8L12 16.5l-5.2 2.7 1-5.8-4.2-4.1 5.8-.8z"/></svg> Club member</span>':'';
function csvCell(v){v=v==null?'':String(v);return /[",\n]/.test(v)?'"'+v.replace(/"/g,'""')+'"':v}
function exportColl(){if(!MEMBER)return;const byId=new Map(D.cards.map(c=>[cid(c),c])),rows=[['Type','Set','Set name','Number','Name','Rarity','Printing','Edition','Condition','Qty','Grader','Grade','Cert','Estimate each','Estimated value']];
  const info=id=>{const c=byId.get(id)||{};return [c.s?setLabel(D.byId[c.s]||{id:c.s,kind:''}):'',c.s?setName(c.s):'',c.n||id,c.name||'',RNAME[c.src]||c.r||'']};
  const num=v=>v==null?'':(+v).toFixed(2);
  for(const [k,q] of COLL){const a=k.split('|');if(!q&&a[3]==='have')continue;if(a[3]!=='have'){rows.push(['Want',...info(a[0]),a[1],a[2],'','','','','','',''].slice(0,15));continue}
    const by={};condsOf(k).forEach(cd=>by[cd]=(by[cd]||0)+1);for(const [cd,n] of Object.entries(by)){const e=estCond(a[0],a[1],a[2],cd);rows.push(['Have',...info(a[0]),a[1],a[2],cd,n,'','','',e?num(e.estimate):'',e?num(e.estimate*n):''])}}
  for(const x of SLABS){const e=estFor(x.card_id,x.printing,x.edition,x.grader,x.grade);rows.push(['Slab',...info(x.card_id),x.printing,x.edition,'',1,x.grader,x.grade,x.cert||'',e?num(e.estimate):'',e?num(e.estimate):''])}
  const blob=new Blob(['﻿'+rows.map(r=>r.map(csvCell).join(',')).join('\r\n')],{type:'text/csv;charset=utf-8'});
  const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='jonin-collection-'+new Date().toISOString().slice(0,10)+'.csv';document.body.appendChild(a);a.click();setTimeout(()=>{URL.revokeObjectURL(a.href);a.remove()},500)}
function collStats(src){let copies=0,first=0,foil=0;const have=new Set(),want=new Set();
  for(const [k,q] of src){const a=k.split('|');if(a[3]==='have'){have.add(a[0]);copies+=q;if(/1st/.test(a[2]))first+=q;if(/foil|Super Rare|Gold/i.test(a[1]))foil+=q}else if(a[3]==='want')want.add(a[0])}
  const per=D.sets.map(s=>{const all=D.cards.filter(c=>c.s===s.id);const n=all.filter(c=>have.has(cid(c))).length;return {s,n,t:all.length,miss:all.filter(c=>!have.has(cid(c)))}}).filter(x=>x.n);
  return {have,want,copies,first,foil,per,done:per.filter(x=>x.n>=x.t).length}}
function listView(el,title,src,ro){LAST=[el,title,src,ro];const st=collStats(src);const ms=MISS&&MTAB==='have'?st.per.find(x=>x.s.id===MISS):null;if(!ms)MISS='';
  const SL=ro?VSLABS:SLABS;if(ro&&(MTAB==='lists'||(MTAB==='slab'&&!SL.length)))MTAB='have';const slabIds=new Set(SL.map(x=>x.card_id));
  if(CF.tab!==MTAB){CF.tab=MTAB;CF.ver='';if(/qty|grade/.test(CF.sort))CF.sort=''}const base=ms?ms.miss:MTAB==='slab'?D.cards.filter(c=>slabIds.has(cid(c))):cardsWith(MTAB,src);const items=ms||MTAB==='lists'?base:cfApply(base,src,SL);list=items;MCTX={src,SL,ro,n:base.length};
  const stat=(n,l)=>`<div><b>${n.toLocaleString()}</b><span>${l}</span></div>`;const cv=!ro&&MEMBER&&EST?collValue(src):null;let fcv=null;
  el.innerHTML=`${title}
  <div class="row"><button class="pill" data-mtab="have" aria-pressed="${MTAB==='have'}">Haves · ${st.have.size}</button><button class="pill" data-mtab="want" aria-pressed="${MTAB==='want'}">Wants · ${st.want.size}</button>${ro?(SL.length?`<button class="pill" data-mtab="slab" aria-pressed="${MTAB==='slab'}">Slabs · ${SL.length}</button>`:''):`<button class="pill" data-mtab="slab" aria-pressed="${MTAB==='slab'}">Slabs · ${SLABS.length}</button><button class="pill" data-mtab="lists" aria-pressed="${MTAB==='lists'}">Lists${ME?' · '+LISTS.length:''}</button>${ME?(MEMBER?'<button type="button" class="clear mexp" data-export title="Haves, wants and slabs with versions, grades and estimated values. Opens in Excel or Google Sheets.">⤓ Download CSV</button>':'<a class="clear mexp" href="/club/"><svg class="jstar" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3.2l2.6 5.3 5.8.8-4.2 4.1 1 5.8L12 16.5l-5.2 2.7 1-5.8-4.2-4.1 5.8-.8z"/></svg> Export CSV with Jonin Club</a>'):''}`}</div>${MTAB==='lists'&&!ro?listsPane():''}
  ${MTAB==='slab'&&!ro?`<button type="button" class="shv" data-slabhave aria-pressed="${slabsHave()}"><span class="bx" aria-hidden="true">${slabsHave()?'✓':''}</span><span title="Adding a slab adds 1 to that version’s haves; removing it takes 1 away.">Count my slabs as haves and toward set completion</span></button>`:''}
  ${MTAB==='slab'&&SL.length?`<div class="cstats">${stat(SL.length,'slabs')}${stat(slabIds.size,'different cards')}${GRADERS.filter(g=>SL.some(x=>x.grader===g)).map(g=>stat(SL.filter(x=>x.grader===g).length,g)).join('')}${ro?'':MEMBER&&EST?`<div class="vstat"><b>≈ ${money(cv.sl)}</b><span>slab value · ${cv.slN} of ${cv.slAll} priced</span></div>`:ME&&!MEMBER?(fcv=freeCV(),freeStat('slab value',fcv&&fcv.slab,fcv&&fcv.slab_n,fcv?fcv.slab_all:SL.length)):signStat('Slab value')}</div>`:''}
  ${MTAB==='have'&&st.have.size?`<div class="cstats">${stat(st.have.size,'different cards')}${stat(st.copies,'total copies')}${stat(st.first,'1st Edition copies')}${stat(st.foil,'foil copies')}${stat(st.per.length,'sets started')}${stat(st.done,'sets complete')}${ro?'':MEMBER&&EST?`<div class="vstat" title="Estimated from recent sales. ${cv.rawN} of ${cv.rawAll} copies have a price."><b>≈ ${money(cv.raw)}</b><span>estimated value · ${cv.rawN} of ${cv.rawAll} copies priced</span></div>`:ME&&!MEMBER?(fcv=freeCV(),freeStat('estimated value',fcv&&fcv.raw,fcv&&fcv.raw_n,fcv?fcv.raw_all:st.copies)):signStat('Collection value')}</div>`:''}
  ${MTAB==='have'&&st.per.length?`<div class="sp">${st.per.map(({s,n,t,miss})=>`<div class="spc${MISS===s.id?' on':''}"><button data-set="${esc(s.id)}" title="Browse this set"><span><b>${esc(setLabel(s))}</b> · ${esc(s.name)}</span><span class="mt">${n} / ${t} cards · ${Math.floor(n/t*100)}%</span><span class="bar2"><i style="width:${Math.min(100,n/t*100)}%"></i></span></button>${miss.length?`<button class="msb" data-miss="${esc(s.id)}" aria-pressed="${MISS===s.id}">${MISS===s.id?'Hide missing':'Missing · '+miss.length}</button>`:'<span class="msb done">Complete ✓</span>'}</div>`).join('')}</div>`:''}
  ${ms?`<div class="row misshead"><b>Missing from ${esc(setLabel(ms.s))} · ${esc(ms.s.name)}: ${ms.miss.length} cards</b><button class="clear" data-copy="${esc(ms.miss.map(c=>c.n+'  '+c.name).join('\n'))}">Copy list</button>${ro?'':'<span class="mt">Open a card and tap ♡ Want to add it to your wants.</span>'}<button class="clear" data-miss="${esc(ms.s.id)}">Back to my haves</button></div>`:''}
  ${MTAB==='lists'&&!ro?'':`${ms?'':cfBar(base,SL)}<div class="grid" id="mgrid">${mGrid(items,SL,ro,base.length)}</div>`}`}
// Scrolls (stored as xp, 2026-11-26): from accepted feedback notes and first votes per character; amounts and ranks are placeholders set in Supabase xp_rules()/xp_rank().
let FBPTS=null;
window.addEventListener('jonin:xp',()=>loadFbPts());   // daily battle vote etc. (rank-up popup, header scrolls)
function loadFbPts(){if(!ME||!sbc())return;sb.rpc('my_xp').then(r=>{if(!r.error&&r.data){FBPTS=r.data;if(window.JoninAcct&&JoninAcct.rankCheck)JoninAcct.rankCheck(ME.id,r.data);paintAcct();const el=$('#v-mine');if(el&&el.innerHTML)renderMine()}}).catch(()=>{})}
function rankRow(){if(!FBPTS)return '';const p=FBPTS.xp!=null?FBPTS.xp:(FBPTS.points||0),lo=FBPTS.prev_at||0;const pct=FBPTS.next_at?Math.min(100,Math.round((p-lo)/(FBPTS.next_at-lo)*100)):100;
  return `<div class="share fbrank"><span>Rank:</span><b>${esc(FBPTS.rank)}</b><span class="mt">📜 ${p} ${p===1?'scroll':'scrolls'}${FBPTS.next?` · ${FBPTS.next_at-p} ${FBPTS.next_at-p===1?'scroll':'scrolls'} to ${esc(FBPTS.next)}`:''}</span><span class="fbbar" aria-hidden="true"><i style="width:${pct}%"></i></span><a class="clear" href="/missions/" style="text-decoration:none">Missions: earn scrolls</a></div>`}
function renderMine(){const el=$('#v-mine');if(ME)setTimeout(slabAsk,800);if(!ME){const n=gCount();if(!n){el.innerHTML='<h1>My collection</h1><p class="mt">Sign up or sign in to track your haves, wants and slabs.</p><div class="row"><button class="pill" data-auth="up">Sign up</button><button class="clear" data-auth="in">Sign in</button></div>'+sellBox();return}
    listView(el,`<div class="mhead"><h1>My collection</h1><div class="macts"></div></div><div class="gsave"><span><b>Saved on this device only.</b> If you clear your browser or switch phones, it’s gone. Make a free account to keep it and share it.</span><button type="button" class="pill" data-auth="up">Sign up so you don’t lose it</button><button type="button" class="clear" data-auth="in">I have an account</button></div>${sellSlim()}`,COLL,false);return}
  const link=MYP?location.origin+'/u/'+encodeURIComponent(MYP.share_slug)+'/':'';
  // Cleanup (2026-11-26): profile/sharing rows live in one collapsible "Profile settings" panel; rank, share link and Get an offer sit in the header.
  const open=SETOPEN||NMEDIT||IGEDIT||FAVEDIT,todo=MYP&&!MYP.fav_character;
    const head=`<div class="mhead"><h1 class="ph">${MYP?avImg(MYP.fav_character,MYP.avatar,48):''}<span>${esc(MYP&&MYP.handle?MYP.handle+"'s collection":'My collection')}</span>${badgeHtml(MYBADGE)}</h1>
  <div class="macts">${MYP?`<button type="button" class="pill" data-settoggle aria-expanded="${!!open}">⚙ Profile settings${todo&&!open?'<i class="mdot" aria-label="Unfinished"></i>':''}</button>`:''}</div></div>
  <div class="msub">${rankChip()}${MYP?(MYP.sharing?`<button type="button" class="mchip" data-copy="${esc(link)}" title="${esc(link)}">🔗 Copy share link</button><a class="mchip" href="#u=${esc(MYP.share_slug)}">View my profile</a>`:`<button type="button" class="mchip off" data-settoggle>🔒 Profile is private</button>`):''}${todo&&!open?'<button type="button" class="mchip nudge" data-settoggle>Pick your favorite character</button>':''}</div>`;
  const panel=MYP&&open?`<div class="mset">${nameRow()}${favRow()}${avRow()}${igRow()}<div class="share"><span>Share link${MYP.sharing?'':' (off)'}:</span>${MYP.sharing?`<code>${esc(link)}</code><button class="clear" data-copy="${esc(link)}">Copy</button>`:''}<button class="clear" data-share>${MYP.sharing?'Turn off sharing':'Turn on sharing'}</button></div>${MYP.sharing?`<div class="share"><span>Slabs on profile:</span><button class="clear" data-showslabs>${MYP.show_slabs?'Hide my slabs':'Show my slabs'}</button><span class="mt">${MYP.show_slabs?'On. Grader and grade only, never cert numbers.':'Off. Your slabs stay private.'}</span></div>`:''}${setupRow()}</div>`:'';
  listView(el,head+panel+sellSlim(),COLL,false)}
let SETOPEN=false;
// Slim sell line (2026-11-26): one thin row under the header; the card list still gets copied on click (data-sellgo).
const sellSlim=()=>`<div class="sellslim"><span><b>Selling?</b> ${sellCount()?'Get an offer from Jonin or a trusted buyer.<span class="sx"> Your card list gets copied for you.</span>':'Get an offer from Jonin or a trusted buyer.'}</span><a href="${SELL_URL}" target="_blank" rel="noopener" data-sellgo>Get an offer →</a></div>`;
function rankChip(){if(!FBPTS)return '';const p=FBPTS.xp!=null?FBPTS.xp:(FBPTS.points||0),lo=FBPTS.prev_at||0;const pct=FBPTS.next_at?Math.min(100,Math.round((p-lo)/(FBPTS.next_at-lo)*100)):100;
  return `<a class="mchip rk" href="/missions/" title="${FBPTS.next?`${FBPTS.next_at-p} ${FBPTS.next_at-p===1?'scroll':'scrolls'} to ${esc(FBPTS.next)}. `:''}Missions: earn scrolls">📜 <b>${esc(FBPTS.rank)}</b><span>${p} ${p===1?'scroll':'scrolls'}</span><span class="fbbar" aria-hidden="true"><i style="width:${pct}%"></i></span></a>`}
document.addEventListener('click',e=>{if(e.target.closest('[data-settoggle]')){SETOPEN=!(SETOPEN||NMEDIT||IGEDIT||FAVEDIT);if(!SETOPEN){NMEDIT=IGEDIT=FAVEDIT=false}renderMine()}});
// Redo setup (2026-11-26): reopens /welcome/ with their saved answers filled in, then comes back here. Skipping setup left nothing filled, so that case says "Finish setup".
function setupRow(){if(!MYP)return '';const any=(MYP.fav_characters&&MYP.fav_characters.length)||MYP.found_via||(MYP.collector_types&&MYP.collector_types.length);
  return `<div class="share setuprow"><span>Setup:</span><button type="button" class="clear" data-redosetup>${any?'Redo setup':'Finish setup'}</button><span class="mt">${any?'Change your favorite characters, answers or theme.':'Pick your favorite characters, answer a few questions and choose a theme.'}</span></div>`}
function redoSetup(){try{sessionStorage.setItem('jret',location.pathname+location.hash)}catch(_){}location.href='/welcome/'}
// Favorite character on the profile: picked from the site's 40 characters, shown on their shared collection with a link to that character's page.
let FAVEDIT=false;const chSlug=l=>l.toLowerCase().replace(/[^a-z0-9]+/g,'-');
const FAVS=()=>QUICK.filter(([l,q])=>q.startsWith('char:')).map(([l])=>[chSlug(l),l]);
const favName=sl=>{const f=FAVS().find(x=>x[0]===sl);return f?f[1]:null};
const favImg=sl=>`<img src="/chars/${esc(sl)}.webp" alt="" width="28" height="28" loading="lazy" decoding="async">`;
// Profile picture: one of the crops taken of their favorite character (face, theme portrait for 8 characters, action art).
const THEMEF=['naruto','sasuke','itachi','kakashi','gaara','hinata','sakura','rock-lee'];
const avOpts=sl=>[['face','Face','/chars/'+sl+'.webp'],...(THEMEF.includes(sl)?[['portrait','Portrait','/theme-faces/'+sl+'.webp']]:[]),['action','Action','/char-art/'+sl+'.webp']];
const avSrc=(sl,a)=>{const o=avOpts(sl);return (o.find(x=>x[0]===a)||o[0])[2]};
const avImg=(sl,a,sz)=>sl&&favName(sl)?`<img class="avatar" src="${esc(avSrc(sl,a))}" alt="" width="${sz}" height="${sz}" decoding="async">`:'';
function avRow(){const f=MYP&&MYP.fav_character;if(!f||!favName(f)||FAVEDIT)return '';const cur=(avOpts(f).find(x=>x[0]===MYP.avatar)||avOpts(f)[0])[0];
  return `<div class="share avrow"><span>Profile picture:</span><div class="avgrid">${avOpts(f).map(([k,l,src])=>`<button type="button" class="avopt${k===cur?' on':''}" data-avpick="${k}" aria-pressed="${k===cur}" title="${esc(l)}"><img src="${esc(src)}" alt="" width="56" height="56" loading="lazy" decoding="async"><small>${esc(l)}</small></button>`).join('')}</div><span class="mt">From your favorite character. Change your favorite to get other pictures.</span></div>`}
async function saveAv(k){if(!MYP)return;const r=await sb.from('profiles').update({avatar:k}).eq('id',ME.id).select().maybeSingle();if(!r.error&&r.data)MYP=r.data;renderMine();paintAcct()}
function favRow(){const f=MYP&&MYP.fav_character,n=f&&favName(f);
  if(n&&!FAVEDIT)return `<div class="share favrow"><span>Favorite character:</span><a class="favchip" href="/character/${esc(f)}/">${favImg(f)}${esc(n)}</a><button class="clear" data-favedit>Change</button><button class="clear" data-favpick="">Remove</button></div>`;
  return `<div class="share favrow"><span>${n?'Pick a new favorite character:':'Pick your favorite character. It shows on your shared collection.'}</span><div class="favgrid">${FAVS().map(([sl,l])=>`<button type="button" class="favchip${sl===f?' on':''}" data-favpick="${esc(sl)}">${favImg(sl)}${esc(l)}</button>`).join('')}</div>${n?'<button class="clear" data-favcancel>Cancel</button>':''}</div>`}
// Signed-in favorite goes to the top of the Characters filter; everyone else sees the normal order.
function favFirst(){const cl=$('#clist');if(!cl||!cl.children.length)return;
  const fs=ME&&MYP?[...new Set([MYP.fav_character,...(MYP.fav_characters||[])].filter(Boolean))]:[];
  const ks=fs.map(f=>((QUICK.find(([l,q])=>q.startsWith('char:')&&chSlug(l)===f)||[])[1]||'').replace(/^char:/,'')).filter(Boolean);
  [...cl.children].forEach(b=>b.classList.toggle('fav',ks.includes(b.dataset.q)));
  ks.slice().reverse().forEach(k=>{const b=[...cl.children].find(x=>x.dataset.q===k);if(b)cl.prepend(b)});if(D&&D.byId)paintChars()}
async function saveFav(sl){const v=sl||null;const rest=((MYP&&MYP.fav_characters)||[]).filter(x=>x!==v&&x!==(MYP&&MYP.fav_character));const r=await sb.from('profiles').update({fav_character:v,fav_characters:v?[v,...rest].slice(0,3):rest}).eq('id',ME.id).select().maybeSingle();if(!r.error&&r.data){MYP=r.data;FAVEDIT=false}favFirst();renderMine();paintAcct()}
// Instagram handle on the profile: shown on their shared collection page with a link to their IG.
// Profile name (2026-11-26): members can change their name any time. Rules come from the database: 3-24 letters, numbers or _, unique.
// Cooldown and protected names are enforced in Supabase (db/018_profile_name_rules.sql); this only explains them.
let NMEDIT=false,NMNEXT,NMDAYS=30;
function loadNmRules(){if(!ME||!sbc()||NMNEXT!==undefined)return;NMNEXT=null;
  Promise.all([sb.rpc('my_handle_next_change'),sb.rpc('handle_cooldown_days')]).then(([a,b])=>{if(!a.error)NMNEXT=a.data?new Date(a.data):null;if(!b.error&&b.data)NMDAYS=b.data;const el=$('#v-mine');if(el&&el.innerHTML&&$('.nmrow'))renderMine()}).catch(()=>{})}
const nmDate=d=>d.toLocaleDateString(undefined,{month:'short',day:'numeric'});
function nameRow(){if(!MYP)return '';loadNmRules();const h=MYP.handle||'';const locked=NMNEXT&&NMNEXT>new Date();
  if(h&&!NMEDIT)return `<div class="share nmrow"><span>Profile name:</span><b>${esc(h)}</b>${locked?`<span class="mt">You can change it again on ${esc(nmDate(NMNEXT))}</span>`:'<button class="clear" data-nmedit>Change</button>'}</div>`;
  return `<div class="share nmrow"><label for="nmin">Profile name</label><input id="nmin" class="nmin" maxlength="24" placeholder="yourname" value="${esc(h)}" autocomplete="off" spellcheck="false"><button class="pill" data-nmsave>Save</button>${h?'<button class="clear" data-nmcancel>Cancel</button>':''}<span class="mt nmtip" id="nmmsg">3–24 letters, numbers or _. ${MYP.handle_changed_at?'':'Your first change is free. '}After a change you can change it again in ${NMDAYS} days.</span></div>`}
async function saveName(v){const m=$('#nmmsg');const h=String(v||'').trim().replace(/^@/,'').replace(/\s+/g,'_');
  if(!/^[A-Za-z0-9_]{3,24}$/.test(h)){if(m)m.textContent='Use 3–24 letters, numbers or _ (no spaces or symbols).';return}
  if(h===MYP.handle){NMEDIT=false;renderMine();return}
  if(m)m.textContent='Saving…';
  const r=await sb.from('profiles').update({handle:h}).eq('id',ME.id).select().maybeSingle();
  if(r.error){const e=r.error;if(m)m.textContent=e.code==='23505'?'That name is taken. Try another.':e.hint==='reserved'?'That name is reserved. Try another.':e.hint==='cooldown'?(e.message||'You changed your name recently.')+'.':'Could not save. Try again.';return}
  if(r.data)MYP=r.data;NMEDIT=false;NMNEXT=undefined;renderMine();paintAcct()}
document.addEventListener('keydown',e=>{if(e.key==='Enter'&&e.target&&e.target.id==='nmin'){e.preventDefault();saveName(e.target.value)}else if(e.key==='Escape'&&e.target&&e.target.id==='nmin'&&MYP&&MYP.handle){NMEDIT=false;renderMine()}});
let IGEDIT=false;const igUrl=h=>'https://www.instagram.com/'+encodeURIComponent(h)+'/';
function igRow(){const h=MYP&&MYP.instagram;
  if(h&&!IGEDIT)return `<div class="share igrow"><span>Instagram:</span><a href="${igUrl(h)}" target="_blank" rel="noopener">@${esc(h)}</a><button class="clear" data-igedit>Change</button><button class="clear" data-igdel>Remove</button><span class="mt igtip">${MYP.sharing?'Shows on your shared collection. Put your share link in your Instagram bio so people can see it.':'Turn on sharing so people can see your collection and your Instagram.'}</span></div>`;
  return `<div class="share igrow"><label for="igin">Instagram</label><span class="igat">@<input id="igin" maxlength="60" placeholder="yourhandle" value="${esc(h||'')}" autocomplete="off" spellcheck="false"></span><button class="pill" data-igsave>Save</button>${h?'<button class="clear" data-igcancel>Cancel</button>':''}<span class="mt igtip" id="igmsg">Add your Instagram to show it on your shared collection.</span></div>`}
async function saveIg(v){const m=$('#igmsg');let h=v==null?null:String(v).trim().replace(/^https?:\/\/(www\.)?instagram\.com\//i,'').replace(/^@/,'').replace(/[/?#].*$/,'');
  if(h==='')h=null;if(h&&!/^[A-Za-z0-9._]{1,30}$/.test(h)){if(m)m.textContent='Handles use letters, numbers, . and _ (up to 30).';return}
  const r=await sb.from('profiles').update({instagram:h}).eq('id',ME.id).select().maybeSingle();if(r.error){if(m)m.textContent='Could not save. Try again.';return}MYP=r.data;IGEDIT=false;renderMine()}
async function toggleShowSlabs(){if(!MYP)return;const r=await sb.from('profiles').update({show_slabs:!MYP.show_slabs}).eq('id',ME.id).select().maybeSingle();if(!r.error&&r.data)MYP=r.data;renderMine()}
async function toggleShare(){if(!MYP)return;const v=!MYP.sharing;const r=await sb.from('profiles').update({sharing:v}).eq('id',ME.id).select().maybeSingle();if(!r.error&&r.data)MYP=r.data;renderMine()}
// Public profile (#u=<slug>, 2026-11-26): only when the member has sharing on. Slabs show only if they turned on
// "Show my slabs" (profiles.show_slabs, off by default); grader + grade only, never cert numbers.
let VSLABS=[];
async function renderUser(slug){const el=$('#v-user');el.innerHTML='<p class="empty">Loading…</p>';VSLABS=[];if(!sbc()){el.innerHTML='<p class="empty">Could not load this profile.</p>';return}
  const [r,pr,ss]=await Promise.all([sb.rpc('shared_list',{slug}),sb.rpc('shared_profile',{slug}),sb.rpc('shared_slabs',{slug})]);const prof=pr&&pr.data&&pr.data[0],ig=prof&&prof.instagram,fav=prof&&prof.fav_character&&favName(prof.fav_character)?prof.fav_character:null;if(!r.error&&prof&&(!r.data||!r.data.length))r.data=[];if(r.error||!r.data||(!r.data.length&&!prof)){el.innerHTML='<h1>Collector profile</h1><p class="empty">This profile is private, or the link is wrong.</p>';return}
  VSLABS=(ss&&!ss.error&&ss.data)||[];
  const m=new Map();r.data.forEach(i=>m.set(ck(i.card_id,i.printing,i.edition,i.kind),i.qty));const who=(prof&&prof.handle)||(r.data[0]&&r.data[0].handle)||'A collector';
  const since=prof&&prof.joined?new Date(prof.joined).toLocaleDateString('en-US',{month:'short',year:'numeric'}):'';
  const own=ME&&MYP&&MYP.share_slug===slug;
  listView(el,`<h1 class="ph">${fav?avImg(fav,prof.avatar,56):''}<span>${esc(who)}'s collection</span>${badgeHtml(prof&&prof.badge)}</h1><div class="pbadges">${fav?`<a class="favchip big" href="/character/${esc(fav)}/">${favImg(fav)}<span><small>Favorite character</small>${esc(favName(fav))}</span></a>`:''}${prof&&prof.rank?`<span class="pchip">📜 ${esc(prof.rank)}${prof.xp?' · '+prof.xp+' scrolls':''}</span>`:''}${since?`<span class="pchip">Member since ${esc(since)}</span>`:''}${ig?`<a class="igbadge" href="${igUrl(ig)}" target="_blank" rel="noopener"><span aria-hidden="true">📷</span> @${esc(ig)} on Instagram</a>`:''}</div><p class="mt">${own?'This is how others see your profile. <a class="clear" href="#mine" data-v="mine">Back to My collection</a>':'Shared from Jonin. '+(ME?'':'<button class="clear" data-auth="up">Make your own profile</button>')}</p>`,m,true)}
// Card lists (2026-11-26): members make their own named lists of cards (e.g. "Trade binder", "Sasuke PC").
// Private to the owner for now (Supabase card_lists / card_list_items, owner-only RLS). card_lists.visibility and
// share_slug are already there so lists can be made public/shareable later.
// PLACEHOLDERS to revisit with David: lists hold whole cards (any version, no printing/edition); members only (signed-out
// visitors get a signup prompt); up to 50 lists and 1,000 cards per list (enforced in Supabase); newest-changed list first.
let LISTS=[],LITEMS=new Map(),OPENL='',LNEW=false,LREN=false,LDIRTY=false,LBUSY=false;
async function loadLists(){LISTS=[];LITEMS=new Map();if(!ME||!sbc())return;
  const [l,it]=await Promise.all([sb.from('card_lists').select('id,name,note,updated_at,created_at').order('updated_at',{ascending:false}).limit(100),sb.from('card_list_items').select('list_id,card_id,added_at').order('added_at',{ascending:false}).limit(50000)]);
  if(l.error)return;LISTS=l.data||[];LISTS.forEach(x=>LITEMS.set(x.id,[]));(it.data||[]).forEach(i=>{const a=LITEMS.get(i.list_id);if(a)a.push(i.card_id)});
  if(sel>=0&&list[sel])renderMyColl(list[sel]);if(VIEW==='mine'&&MTAB==='lists')renderMine()}
const lCount=id=>(LITEMS.get(id)||[]).length;
const lHas=(id,card)=>(LITEMS.get(id)||[]).includes(card);
function lBump(id){const i=LISTS.findIndex(x=>x.id===id);if(i>0){const [x]=LISTS.splice(i,1);LISTS.unshift(x)}}
function listBlock(c){const id=cid(c);
  if(!ME)return `<div class="lists"><div class="slh"><b>Lists</b></div><p class="mt" style="margin:0">Make your own card lists, like “Trade binder” or “Sasuke PC”.</p><div class="row"><button type="button" class="pill" data-auth="up">Sign up to make lists</button></div></div>`;
  const on=LISTS.filter(l=>lHas(l.id,id)).length;
  return `<div class="lists"><div class="slh"><b>Lists${on?' · in '+on:''}</b>${LNEW?'':'<button type="button" class="clear" data-lnew="card">+ New list</button>'}</div>
  ${LISTS.length?`<div class="lchips">${LISTS.map(l=>{const h=lHas(l.id,id);return `<button type="button" class="lchip${h?' on':''}" data-ltog="${esc(l.id)}" aria-pressed="${h}">${h?'✓ ':'+ '}${esc(l.name)}</button>`}).join('')}</div>`:(LNEW?'':'<p class="mt" style="margin:0">Make a list and add this card to it. Only you can see your lists.</p>')}
  ${LNEW?lForm('card'):''}</div>`}
const lForm=(where,val)=>`<div class="lform"><input id="lname" maxlength="60" placeholder="List name, e.g. Trade binder" value="${esc(val||'')}" autocomplete="off"><button type="button" class="pill" data-lsave="${where}">${val!=null?'Save':'Create'}</button><button type="button" class="clear" data-lcancel>Cancel</button><span class="mt" id="lmsg"></span></div>`;
function listsPane(){
  if(!ME)return `<div class="share"><span>Make your own card lists (a trade binder, a character PC, cards to grade…). Lists are saved to your account.</span><button type="button" class="pill" data-auth="up">Sign up</button><button type="button" class="clear" data-auth="in">Sign in</button></div>`;
  const L=LISTS.find(x=>x.id===OPENL);if(!L)OPENL='';
  if(!L){list=[];return `<div class="lhead"><span class="mt">Only you can see your lists.</span>${LNEW?'':'<button type="button" class="pill" data-lnew="pane">+ New list</button>'}</div>${LNEW?lForm('pane'):''}
    ${LISTS.length?`<div class="lgrid">${LISTS.map(l=>{const ids=LITEMS.get(l.id)||[],c0=ids.length?D.cards.find(c=>cid(c)===ids[0]):null;
      return `<button type="button" class="lcard" data-lopen="${esc(l.id)}"><span class="lth">${c0&&/^https:\/\//.test(c0.img||'')?`<img src="${esc(c0.img)}" alt="" loading="lazy" decoding="async">`:'<span aria-hidden="true">🗂️</span>'}</span><span><b>${esc(l.name)}</b><span class="mt">${ids.length.toLocaleString()} card${ids.length===1?'':'s'}</span></span></button>`}).join('')}</div>`
    :(LNEW?'':'<p class="empty">No lists yet. Make one here, or open any card and tap + New list.</p>')}`}
  const ids=LITEMS.get(L.id)||[],byId=new Map(D.cards.map(c=>[cid(c),c]));const items=ids.map(i=>byId.get(i)).filter(Boolean);list=items;
  return `<div class="lhead"><button type="button" class="clear" data-lback>‹ All lists</button>${LREN?'':`<h2>${esc(L.name)}</h2><span class="mt">${items.length.toLocaleString()} card${items.length===1?'':'s'} · private</span>`}
    ${LREN?lForm('ren',L.name):`<span class="lact"><button type="button" class="clear" data-lren>Rename</button>${items.length?`<button type="button" class="clear" data-copy="${esc(items.map(c=>c.n+'  '+c.name).join('\n'))}">Copy list</button>`:''}<button type="button" class="clear ldel" data-ldel>Delete list</button></span>`}</div>
  <div class="grid">${items.length?items.map((c,i)=>tile(c,i)).join(''):'<p class="empty">This list is empty. Open any card and tap this list’s name under Lists to add it.</p>'}</div>`}
async function lCreate(where){const i=$('#lname'),m=$('#lmsg'),name=(i?i.value:'').trim().replace(/\s+/g,' ');if(!name){if(m)m.textContent='Give it a name.';return}
  if(LISTS.some(l=>l.name.toLowerCase()===name.toLowerCase())){if(m)m.textContent='You already have a list with that name.';return}
  if(LBUSY)return;LBUSY=true;if(m)m.textContent='Saving…';const r=await sb.from('card_lists').insert({name:name.slice(0,60)}).select('id,name,note,updated_at,created_at').single();LBUSY=false;
  if(r.error){if(m)m.textContent=/50 lists/.test(r.error.message)?'You can have up to 50 lists.':'Could not save. Try again.';return}
  LISTS.unshift(r.data);LITEMS.set(r.data.id,[]);LNEW=false;
  if(where==='card'&&sel>=0&&list[sel]){await lToggle(r.data.id,list[sel])}else if(where==='pane'){OPENL=r.data.id}
  lRepaint()}
async function lToggle(lid,c){const id=cid(c),a=LITEMS.get(lid);if(!a)return;const had=a.includes(id);
  if(had)a.splice(a.indexOf(id),1);else a.unshift(id);lBump(lid);if(VIEW==='mine')LDIRTY=true;renderMyColl(c);
  const r=had?await sb.from('card_list_items').delete().match({list_id:lid,card_id:id}):await sb.from('card_list_items').insert({list_id:lid,card_id:id});
  if(r.error&&!(r.error.code==='23505')){if(had)a.unshift(id);else a.splice(a.indexOf(id),1);renderMyColl(c);const b=$('#mycoll');if(b)b.insertAdjacentHTML('beforeend',`<p class="mt" style="color:#ff8b8b;margin:0">${/1,000 cards/.test(r.error.message)?'That list is full (1,000 cards).':'Could not save. Check your connection and try again.'}</p>`)}}
async function lRename(){const L=LISTS.find(x=>x.id===OPENL),i=$('#lname'),m=$('#lmsg');if(!L)return;const name=(i?i.value:'').trim().replace(/\s+/g,' ');if(!name){if(m)m.textContent='Give it a name.';return}
  const r=await sb.from('card_lists').update({name:name.slice(0,60),updated_at:new Date().toISOString()}).eq('id',L.id).select('id,name,note,updated_at,created_at').single();if(r.error){if(m)m.textContent='Could not save. Try again.';return}
  Object.assign(L,r.data);LREN=false;lRepaint()}
async function lDelete(){const L=LISTS.find(x=>x.id===OPENL);if(!L)return;const n=lCount(L.id);
  if(!confirm(`Delete “${L.name}”${n?` and its ${n} card${n===1?'':'s'}`:''}? Your collection isn’t touched.`))return;
  const r=await sb.from('card_lists').delete().eq('id',L.id);if(r.error){toast('Could not delete the list. Try again.');return}
  LISTS=LISTS.filter(x=>x.id!==L.id);LITEMS.delete(L.id);OPENL='';lRepaint()}
function lRepaint(){if(sel>=0&&list[sel]&&!$('#ov').hidden){renderMyColl(list[sel]);if(VIEW==='mine')LDIRTY=true}else if(VIEW==='mine')renderMine();const i=$('#lname');if(i)i.focus()}
document.addEventListener('click',e=>{const t=e.target.closest('[data-lmine]');if(t)MTAB='lists'},true);
document.addEventListener('click',e=>{const t=e.target.closest('button');if(!t)return;const d=t.dataset;
  if(d.lnew!=null){LNEW=true;LREN=false;lRepaint()}
  else if(d.lcancel!=null){LNEW=false;LREN=false;lRepaint()}
  else if(d.lsave!=null){d.lsave==='ren'?lRename():lCreate(d.lsave)}
  else if(d.ltog!=null){const c=list[sel];if(c)lToggle(d.ltog,c)}
  else if(d.lopen!=null){OPENL=d.lopen;LNEW=false;LREN=false;renderMine();scrollTo(0,0)}
  else if(d.lback!=null){OPENL='';LREN=false;renderMine()}
  else if(d.lren!=null){LREN=true;renderMine()}
  else if(d.ldel!=null)lDelete()});
document.addEventListener('keydown',e=>{if(e.key==='Enter'&&e.target&&e.target.id==='lname'){e.preventDefault();const b=document.querySelector('[data-lsave]');if(b)b.click()}});
// Refresh the open list (cards removed or added from the card panel) once the panel closes.
new MutationObserver(()=>{if($('#ov').hidden&&LDIRTY&&VIEW==='mine'){LDIRTY=false;renderMine()}}).observe($('#ov'),{attributes:true,attributeFilter:['hidden']});
document.addEventListener('keydown',e=>{if(e.target&&e.target.id==='lname'&&/^Arrow/.test(e.key))e.stopImmediatePropagation()},true);
gLoad();if(sbc()){sb.auth.getSession().then(async({data})=>{await setUser(data.session?data.session.user:null);AUTHREADY=true;paintAcct()}).catch(()=>{AUTHREADY=true;paintAcct()});sb.auth.onAuthStateChange((ev,ses)=>{setUser(ses?ses.user:null);if(ev==='PASSWORD_RECOVERY'){const pw=prompt('Choose a new password (at least 8 characters)');if(pw&&pw.length>=8)sb.auth.updateUser({password:pw})}})}
// Cards tracked ticker (homepage): every have, want and slab saved to an account adds 1. Count comes from
// cards_tracked() in Supabase (db/017_cards_tracked.sql). Rolls up when it changes; re-checks every 5 minutes while the tab is open, and when you return to the tab.
let TICK=null;
function paintTick(n,c){const el=$('#tick'),tn=$('#tickn');if(!el||!tn)return;const old=TICK,str=n.toLocaleString('en-US'),prev=old===null?'':old.toLocaleString('en-US');
  if(old===null||(str.length!==prev.length))tn.innerHTML=[...str].map(d=>'<span'+(old!==null?' class="up"':'')+'>'+d+'</span>').join('');
  else tn.innerHTML=[...str].map((d,i)=>'<span'+(d!==prev[i]?' class="up"':'')+'>'+d+'</span>').join('');
  $('#tickc').textContent=plural(c,'collector');el.hidden=false;
  if(old!==null&&n>old){el.classList.add('bump');setTimeout(()=>el.classList.remove('bump'),900)}TICK=n}
function loadTick(){if(!sbc()||!$('#tick')||document.documentElement.classList.contains('embed'))return;sb.rpc('cards_tracked').then(r=>{const d=r&&r.data;if(!r.error&&d&&typeof d.cards==='number'){
  const to=d.cards,from=TICK===null?Math.max(0,to-Math.min(to,40)):TICK;if(to===TICK)return;
  // First paint counts up from a little below; later changes roll straight to the new number.
  if(TICK===null&&to>from&&!matchMedia('(prefers-reduced-motion:reduce)').matches){let i=from;TICK=null;paintTick(i,d.collectors);const st=setInterval(()=>{i+=Math.max(1,Math.ceil((to-i)/8));if(i>=to){i=to;clearInterval(st)}paintTick(i,d.collectors)},45)}
  else paintTick(to,d.collectors)}}).catch(()=>{})}
setInterval(()=>{if(!document.hidden)loadTick()},300000);   // every 5 minutes (David OK'd, 2026-11-27); also refreshes when you come back to the tab
document.addEventListener('visibilitychange',()=>{if(!document.hidden)loadTick()});
if(!sbc())AUTHREADY=true;paintAcct();loadFounding();loadTick();
if(location.hash==='#signup'||location.hash==='#signin'){const m=location.hash==='#signin'?'in':'up';history.replaceState(null,'',location.pathname);setTimeout(()=>{if(!ME&&!hasSession())openAuth(m)},300)}
// Live images (audit fix 2026-11-27): only ask Supabase about the few cards with no image in cards.json yet, after the grid
// has drawn. Before, every visit downloaded every card's image link (6 calls) and held the grid back until it arrived.
function liveFill(){if(!D||document.documentElement.classList.contains('embed'))return;const miss=D.cards.filter(c=>!c.img).map(c=>'"'+c.s+':'+c.n+'"');if(!miss.length)return;
  fetch(SUPA+'/rest/v1/site_card_images?select=card_id,url&card_id=in.('+encodeURIComponent(miss.join(','))+')',{headers:{apikey:SUPA_KEY}}).then(r=>r.ok?r.json():[]).then(rows=>{if(applyLive(rows)&&VIEW==='cards')renderCards(true)}).catch(()=>{})}
// Live list only fills cards that have no image in cards.json yet (images are served from jonin.cards; see pipeline/mirror_images.py)
// Back from a card page: same search/filters (hash), render as many cards as before, then scroll back.
function restoreGrid(v){let g=null;try{g=JSON.parse(sessionStorage.getItem('jgrid')||'null');sessionStorage.removeItem('jgrid')}catch(_){}
  if(!g||g.h!==location.hash||g.v!==v)return;if(v==='cards')while(shown<Math.min(g.n||0,list.length))renderCards(false);
  const go=()=>scrollTo(0,g.y||0);go();requestAnimationFrame(go);setTimeout(go,300)}
// Embedded "Your collection" panel for card pages (/?embed=coll&card=ID). The same collection editor as before, so slabs,
// conditions, lists, scrolls and prompts all keep working. The frame sizes itself to the panel; the sign-in overlay
// takes the whole screen while open; toasts and prompts are moved onto the card page.
const EMBED=document.documentElement.classList.contains('embed');
function embedBoot(){const id=new URLSearchParams(location.search).get('card')||'',c=D.cards.find(x=>x.s+':'+x.n===id);
  const fr=window.frameElement,top=fr&&fr.ownerDocument;
  const root=document.createElement('div');root.id='embedroot';root.innerHTML=c?'<div class="mycoll" id="mycoll"></div>':'<p class="mt">Card not found.</p>';document.body.appendChild(root);
  {const b=document.createElement('base');b.target='_top';document.head.appendChild(b)}
  if(window.parent!==window&&parent.jtrack)window.jtrack=(n,d)=>parent.jtrack(n,d);
  if(!c||!fr)return;renderCards=()=>{};renderSets=()=>{};renderMine=()=>{};renderUser=()=>{};listView=()=>{};   // no grid here: grid refreshes (e.g. when member prices load) would swap the card being edited
  list=[c];sel=0;renderMyColl(c);
  const su=setUser;setUser=async u=>{await su(u);if(list[0]===c){sel=0;renderMyColl(c)}};
  const size=()=>{if(!fr.classList.contains('full'))fr.style.height=Math.ceil(root.getBoundingClientRect().height+4)+'px'};
  new ResizeObserver(size).observe(root);size();
  // Toast CSS (and the pill buttons inside them) copied onto the card page once.
  let cssDone=false;const copyCss=()=>{if(cssDone)return;cssDone=true;let out='';
    for(const sh of document.styleSheets){let rs;try{rs=sh.cssRules}catch(_){continue}for(const r of rs){const t=r.cssText;
      if(/gtoast|ptoast|sellask|slabask|\.mile|pbar/.test(t))out+=t+'\n';else if(r.selectorText&&/^\.pill\b/.test(r.selectorText))out+=r.cssText.replace(r.selectorText,r.selectorText.split(',').map(x=>'.gtoast '+x.trim()).join(','))+'\n'}}
    const st=top.createElement('style');st.textContent=out;top.head.appendChild(st)};
  const sync=()=>{const full=!!document.querySelector('body>.ov:not([hidden])');if(full!==fr.classList.contains('full')){fr.classList.toggle('full',full);root.style.visibility=full?'hidden':'';if(!full)size()}
    document.querySelectorAll('body>.gtoast').forEach(t=>{copyCss();top.querySelectorAll('body>.gtoast').forEach(x=>x.remove());
      t.addEventListener('click',e=>{const a=e.target.closest('[data-auth]');if(a){e.preventDefault();openAuth(a.dataset.auth)}
        if(e.target.closest('[data-sellgo]')){sellSet('done');const l=sellList();if(l&&navigator.clipboard)navigator.clipboard.writeText('My Jonin collection ('+plural(sellCount(),'card')+'):\n'+l).catch(()=>{})}});
      top.body.appendChild(t)})};
  new MutationObserver(sync).observe(document.body,{childList:true,subtree:true,attributes:true,attributeFilter:['hidden']});sync();
  // ← → still flip cards when focus is inside the panel.
  document.addEventListener('keydown',e=>{if(e.metaKey||e.ctrlKey||e.altKey||e.shiftKey||!$('#authov').hidden)return;const t=e.target;if(t&&(t.isContentEditable||/^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName)))return;
    const k=e.key==='ArrowLeft'?'prev':e.key==='ArrowRight'?'next':'';const a=k&&top.querySelector('.cnav a[data-key="'+k+'"]');if(a){e.preventDefault();top.defaultView.location.href=a.href}})}
function applyLive(rows){if(!D||!rows||!rows.length)return false;const m={};rows.forEach(r=>{if(r&&r.url)m[r.card_id]=r.url});let n=0;D.cards.forEach(c=>{const u=m[c.s+':'+c.n];if(u&&/^https:\/\//.test(u)&&!c.img){c.img=u;n++}});return n>0}
fetch('cards.json').then(r=>r.json()).then(async d=>{D=d;setTimeout(liveFill,1500);D.byId={};D.sets.forEach(s=>{D.byId[s.id]=s;if(s.id==='21')s.symbol='symbols/21.png'});
  $('#qn').textContent='('+QUICK.length+')';favFirst();
  $('#ftog').addEventListener('click',e=>{e.stopPropagation();const o=$('#fbar').classList.toggle('fopen');$('#ftog').setAttribute('aria-expanded',String(o))});
  {const d=$('#quick');d.addEventListener('toggle',()=>{try{localStorage.setItem('jq',d.open?'0':'1')}catch(_){}})}
  $('#rars').innerHTML=RARS.map(([k,l])=>`<button class="pill" data-r="${k}" aria-pressed="false">${k?rsym(k)+' ':''}${l}</button>`).join('');$('#types').innerHTML=TYPES.map(k=>`<button class="pill" data-ty="${k}" aria-pressed="false">${k||'All types'}</button>`).join('');
  $('#sortsel').innerHTML=SORTS.map(([k,l])=>`<option value="${k}">${l}</option>`).join('');buildSetList();buildDetails();
  if(EMBED){embedBoot();return}renderSets();const v=readHash();view(v);renderCards(true);restoreGrid(v);let rf='';try{rf=document.referrer?new URL(document.referrer).hostname:''}catch(_){}track('view',{page:v,ref:rf.slice(0,80)||null})}).catch(()=>{$('#count').textContent='Could not load cards'});
}

