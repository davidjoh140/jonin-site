"""/sealed/ (every sealed product, by set) and /sealed/<slug>/ (one product: price by edition, last five sold,
what's listed now). Data: pipeline/sealed.json from sealed_export.py. Free for everyone (David, 2026-11-27).
PLACEHOLDER copy throughout for David to edit."""
import html
import json
import os
import re
import shutil

B = None   # build_pages module, set by setup()
DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sealed.json')
EPN = '&mkevt=1&mkcid=1&mkrid=711-53200-19255-0&campid=5339262225&toolid=10001&customid=jonin-sealed'
KIND = {'booster_box': 'Booster box', 'booster_pack': 'Booster pack', 'blister_pack': 'Blister pack',
        'blister_3pack': '3-pack blister', 'blister_box': 'Blister box', 'theme': 'Theme deck',
        'starter': 'Starter deck', 'tin': 'Tin', 'tournament_pack': 'Tournament pack'}
KIND_PLURAL = {'booster_box': 'Booster boxes', 'booster_pack': 'Booster packs', 'blister_pack': 'Blister packs',
               'blister_3pack': '3-pack blisters', 'blister_box': 'Blister boxes', 'theme': 'Theme decks',
               'starter': 'Starter decks', 'tin': 'Tins', 'tournament_pack': 'Tournament packs'}
KIND_ORDER = ['booster_box', 'booster_pack', 'blister_box', 'blister_3pack', 'blister_pack', 'theme', 'starter', 'tin', 'tournament_pack']
ICON = {'booster_box': '📦', 'booster_pack': '🎴', 'blister_box': '📦', 'blister_3pack': '🎴', 'blister_pack': '🎴', 'theme': '🃏', 'starter': '🃏', 'tin': '🥫', 'tournament_pack': '🏆'}


_BY_SET = None


def set_link(set_id):
    """'Sealed from this set' button for set pages ('' if the set has no sealed products)."""
    global _BY_SET
    if _BY_SET is None:
        _BY_SET = {}
        for p in load():
            _BY_SET.setdefault(p['set'], 0)
            _BY_SET[p['set']] += 1
    return f'<a class="ghostbtn" href="/sealed/#set-{html.escape(set_id.lower(), quote=True)}">Sealed from this set</a>' if _BY_SET.get(set_id) else ''


# What's inside, shown on set pages when a product has no contents filled in yet.
# Taken from retailer listings (ToyWiz, Noble Knight: 24 packs per box, 10 cards per pack). PLACEHOLDER for David to confirm.
KIND_ABOUT = {
    'booster_box': '24 booster packs of 10 cards.',
    'booster_pack': '10 random cards from the set.',
    'theme': 'A ready-to-play preconstructed deck.',
    'starter': 'Ready-to-play starter decks, with cards marked by red dots that are only found in starters.',
    'tin': 'A collector tin with exclusive cards.',
    'tournament_pack': 'Booster packs made for draft and sealed events.',
}


def for_set(set_id):
    """Sealed products for one set, boxes first."""
    ps = [p for p in load() if p['set'] == set_id]
    return sorted(ps, key=lambda p: KIND_ORDER.index(p['kind']) if p['kind'] in KIND_ORDER else 99)


def set_block(set_id, set_name):
    """'Sealed products' section for a set page: art, what's inside, price, listed now. '' if none."""
    ps = for_set(set_id)
    if not ps:
        return ''
    items = ''
    for p in ps:
        sp = span(p)
        about = p.get('contents') or KIND_ABOUT.get(p['kind'], '')
        price = f'<b class="sbpx">{e(span_text(sp))}</b>' if sp else '<span class="sbpx none">No sales yet</span>'
        live = f'<span class="sblive">{p["live_n"]} listed now</span>' if p.get('live_n') else ''
        rel = f'<span>Released {e(p["released"])}</span>' if p.get('released') else ''
        msrp = f'<span>MSRP {e(B.money(p["msrp"]))}</span>' if p.get('msrp') else ''
        items += (f'<a class="sbitem" href="/sealed/{e(p["slug"])}/" data-jt="set-sealed" data-jt-to="{e(p["slug"])}">'
                  f'<span class="sbart">{pic(p, "simg")}</span>'
                  f'<span class="sbtxt"><span class="sbkind">{ICON.get(p["kind"], "📦")} {e(KIND.get(p["kind"], "Sealed"))}</span>'
                  f'<b class="sbname">{e(short(p))}</b><span class="sbabout">{e(about)}</span>'
                  f'<span class="sbmeta">{rel}{msrp}</span><span class="sbprice">{price}{live}</span>'
                  f'<span class="sbgo">Prices, sales and listings →</span></span></a>')
    return (f'<section class="setsec" id="sealed"><div class="sechd"><h2>Sealed products</h2>'
            f'<a class="seclink" href="/sealed/#set-{e(set_id.lower())}">All sealed from {e(set_name)} →</a></div>'
            f'<div class="sblist">{items}</div></section>')


def setup(mod):
    global B
    B = mod


def e(x):
    return B.e(x)


def load():
    return json.load(open(DATA, encoding='utf-8'))['products'] if os.path.isfile(DATA) else []


def short(p):
    """'Booster box', 'Theme deck: Tidal Wave' (the name without the set in front)."""
    n = p['name']
    if p.get('art') and p['kind'] in ('booster_pack', 'blister_pack'):
        return f"{KIND[p['kind']]}: {p['art']} art"
    if p['kind'] in ('theme', 'starter') and ':' in n:
        return KIND[p['kind']] + ': ' + n.split(':', 1)[1].strip()
    if p['kind'] in ('booster_box', 'booster_pack', 'blister_box', 'blister_3pack', 'blister_pack'):
        return KIND[p['kind']]
    return n


def ebay(u):
    return u + ('&' if '?' in u else '?') + EPN.lstrip('&') if u.startswith('https://') and 'ebay.com' in u else u


def span(p):
    """(low, high) across every edition, or None."""
    rs = p.get('ranges') or []
    return (min(r['low'] for r in rs), max(r['high'] for r in rs)) if rs else None


def span_text(lohi):
    lo, hi = lohi
    return B.money(lo) if round(lo) == round(hi) else f'{B.money(lo)}–{B.money(hi)}'


def ed_word(ed):
    return ed or 'Edition not stated'


def pic(p, cls='', eager=False):
    if p.get('img'):
        src = re.sub(r's-l\d+\.', 's-l500.', p['img']) if 'ebayimg.com' in p['img'] else p['img']
        return (f'<img class="{cls}" src="{e(src)}" alt="{e(p["name"])} sealed, Naruto CCG (Bandai)" '
                f'loading="{"eager" if eager else "lazy"}" decoding="async">')
    return f'<span class="{cls} snoimg" aria-hidden="true"><b>{ICON.get(p["kind"], "📦")}</b><small>No photo yet</small></span>'


def tile(p):
    s = span(p)
    price = f'<span class="tn tpx">{e(span_text(s))}</span>' if s else '<span class="tn">No sales yet</span>'
    live = f'<span class="tn">{p["live_n"]} listed now</span>' if p.get('live_n') else ''
    return (f'<a class="tile stile" href="/sealed/{e(p["slug"])}/" data-kind="{e(p["kind"])}">{pic(p, "simg")}'
            f'<span class="tt">{e(short(p))}</span><span class="tn">{e(p["set_name"])}</span>{price}{live}</a>')


def index_page(ps, sets_by_id):
    url = f'{B.SITE}/sealed/'
    priced = [p for p in ps if p.get('ranges')]
    title = 'Naruto CCG sealed prices: booster boxes, packs, theme decks and tins | Jonin'
    desc = ('What sealed Bandai Naruto CCG product is worth (2006–2013): booster boxes, booster packs, theme and '
            'starter decks, tins and tournament packs, priced from real sold listings and checked by hand.')
    groups, order = {}, []
    for p in ps:
        if p['set'] not in groups:
            groups[p['set']] = []
            order.append(p['set'])
        groups[p['set']].append(p)
    blocks = ''
    for sid in order:
        s = sets_by_id.get(sid) or {'id': sid, 'name': groups[sid][0]['set_name']}
        head = (f'<a href="/set/{e(B.set_slug(s))}/">{B.sym_img(s)}{e(s["name"])}</a>' if sid in sets_by_id else e(s['name']))
        blocks += (f'<section class="cgroup" id="set-{e(sid.lower())}"><h2>{head}<span>{len(groups[sid])} item{"s" if len(groups[sid]) != 1 else ""}</span></h2>'
                   f'<div class="grid sgrid">{"".join(tile(p) for p in groups[sid])}</div></section>')
    kinds = [k for k in KIND_ORDER if any(p['kind'] == k for p in ps)]
    chips = ('<div class="chips sfilt" role="group" aria-label="Show only"><button class="chip on" type="button" data-sk="">All</button>'
             + ''.join(f'<button class="chip" type="button" data-sk="{k}">{ICON[k]} {e(KIND_PLURAL[k])}</button>' for k in kinds) + '</div>')
    top = sorted(priced, key=lambda p: -span(p)[1])[:8]
    toprow = (f'<section class="others"><h2>Highest sealed sales<span>top of each range</span></h2><div class="grid sgrid">{"".join(tile(p) for p in top)}</div></section>'
              if len(top) >= 3 else '')
    body = f'''<nav class="crumb"><a href="/">All cards</a> › Sealed</nav>
<section class="sethead"><h1>Naruto CCG sealed product</h1>
<p class="lede">Every sealed item from the original Bandai Naruto CCG (2006–2013): booster boxes, booster packs, theme and starter decks, tins and tournament packs. Prices come from real sold listings, and every sale is checked by hand before it counts. {len(priced)} of {len(ps)} items have a recorded sale so far.</p>
<p class="mt">1st Edition and Unlimited sell for different prices, so each one gets its own range. Opened, resealed and multi-item lots are left out.</p>
{chips}</section>
{toprow}{blocks}
<section class="others"><h2>Have sealed Naruto CCG?</h2><p class="mt">Sell to Jonin or a trusted buyer. <a href="/sell/" data-jt="sell-click" data-jt-from="sealed-index">Get an offer →</a></p></section>
<script>(function(){{var bs=document.querySelectorAll('.sfilt [data-sk]');[].forEach.call(bs,function(b){{b.onclick=function(){{var k=b.getAttribute('data-sk');[].forEach.call(bs,function(x){{x.classList.toggle('on',x===b)}});
[].forEach.call(document.querySelectorAll('.stile'),function(t){{t.hidden=!!k&&t.getAttribute('data-kind')!==k}});
[].forEach.call(document.querySelectorAll('.cgroup'),function(g){{g.hidden=!g.querySelector('.stile:not([hidden])')}})}}}})}})();</script>
'''
    img = next((p['img'] for p in top if p.get('img')), B.SITE + '/og.png')
    ld = B.ld_json({'@context': 'https://schema.org', '@graph': [
        {'@type': 'CollectionPage', 'name': title, 'description': desc, 'url': url},
        B.crumbs(('Naruto CCG cards', B.SITE + '/'), ('Sealed', url))]})
    return B.HEAD.format(title=e(title), desc=e(desc), url=url, img=e(img), tw='summary_large_image', ld=ld) + body + B.FOOT


def live_block(p):
    q = 'https://www.ebay.com/sch/i.html?_nkw=' + B.quote('naruto ccg ' + p['name'] + ' sealed') + EPN
    ll = p.get('live') or []
    if not ll:
        return (f'<section class="fs empty"><h3>For sale now</h3><p class="none">Nothing listed right now. '
                f'<a href="{e(q)}" target="_blank" rel="sponsored noopener" data-jt="ebay-click" data-jt-kind="sealed-search">Search eBay →</a></p></section>')
    rows = ''
    for x in ll:
        small = re.sub(r's-l\d+\.', 's-l225.', x.get('img') or '')
        img = f'<img src="{e(small)}" alt="" loading="lazy" width="56" height="56">' if small else '<i></i>'
        kind = 'Auction' + (f' · {x["b"]} bid{"s" if x["b"] != 1 else ""}' if x.get('b') is not None else '') if x.get('k') == 'AUCTION' else 'Buy It Now' + (' · Offers OK' if x.get('bo') else '')
        rows += (f'<a class="fsr" href="{e(ebay(x["u"]))}" target="_blank" rel="sponsored noopener" data-jt="ebay-click" data-jt-kind="sealed-for-sale">{img}'
                 f'<span class="fsm"><span class="fst">{e(x["t"])}</span><small>{e(ed_word(x.get("ed")))}<span class="fsk">{e(kind)}</span></small></span>'
                 f'<b>{B.money(x["p"])}</b></a>')
    n = p.get('live_n') or len(ll)
    return (f'<section class="fs"><h3>For sale now <span class="fsn">{n} on eBay · from <b>{B.money(ll[0]["p"])}</b></span></h3>'
            f'<div class="fsl0">{rows}</div><p class="none">Cheapest first · updates about every hour · Jonin may earn a commission. '
            f'<a href="{e(q)}" target="_blank" rel="sponsored noopener">See all on eBay →</a></p></section>')


def price_block(p):
    rs = p.get('ranges') or []
    if rs:
        rows = ''.join(f'<tr><td>{e(ed_word(r["ed"]))}<small>{r["n"]} sale{"s" if r["n"] != 1 else ""}'
                       f'{" · last " + e(B.sale_date(r["last"])) if r.get("last") else ""}</small></td><td>{e(span_text((r["low"], r["high"])))}</td></tr>'
                       for r in rs)
        top = f'<table>{rows}</table>'
    else:
        top = '<p class="none">No sales recorded yet. Prices show here once a sale is checked.</p>'
    recent = ''
    for price, ed, d, u, src in p.get('recent') or []:
        eb = u.startswith('https://') and 'ebay.com' in u
        tag = (f'a class="pvsr pvfr" href="{e(ebay(u))}" target="_blank" rel="{"sponsored " if eb else ""}noopener"'
               if u.startswith('https://') else 'span class="pvsr pvfr"')
        recent += (f'<{tag}><span>{e(B.sale_date(d))}</span><span class="pvty">{e(ed_word(ed))}</span><b>{B.money(price)}</b>'
                   f'<span class="pvl">{"eBay ↗" if eb else ""}</span></{tag.split()[0]}>')
    recent = f'<div class="pxfree"><h4 class="pxfh">Recent sales</h4><div class="pvsl">{recent}</div></div>' if recent else ''
    return (f'<section class="px" id="prices"><h3>Market price<span>sealed, by edition</span></h3>{top}{recent}'
            '<p class="mt pgl">Each range comes from sold listings in the last 6 months (or the 3 newest if there are none), checked by hand. Opened, resealed and multi-item lots are left out.</p>'
            '<p class="mt pgl sellnote"><a href="/sell/" data-jt="sell-click" data-jt-from="sealed-page">Have this sealed? Sell to Jonin or a trusted buyer →</a></p></section>')


def product_page(p, ps, sets_by_id):
    url = f'{B.SITE}/sealed/{p["slug"]}/'
    s = sets_by_id.get(p['set'])
    sp = span(p)
    yr = B.set_year(s) if s else ''
    title = f'{p["name"]} (sealed) price · Naruto CCG{" " + yr if yr else ""} | Jonin'
    desc = (f'What a sealed {p["name"]} from the Bandai Naruto CCG is worth' + (f': {span_text(sp)} from real sold listings' if sp else '')
            + '. Price by edition, recent sales and what is listed now.')
    facts = [('Product', KIND.get(p['kind'], p['kind']))]
    if s:
        facts.append(('Set', f'<a href="/set/{e(B.set_slug(s))}/">{e(s["name"])}</a>'))
    if p.get('released'):
        facts.append(('Released', e(p['released'])))
    if p.get('contents'):
        facts.append(('Contents', e(p['contents'])))
    if p.get('msrp') is not None:
        facts.append(('Original price', B.money(p['msrp'])))
    facts_html = ''.join(f'<div><dt>{k}</dt><dd>{v}</dd></div>' for k, v in facts)
    note = '' if p.get('confirmed') else '<p class="mt snote">Product details are still being checked. Know what came in it? <button class="linkbtn" type="button" data-fb>Tell us</button>.</p>'
    val = (f'<a class="valline" href="#prices"><span>Sealed value</span><b>{e(span_text(sp))}</b><small>all editions · sales ↓</small></a>' if sp else '')
    kids = [x for x in ps if x.get('parent') == p['id']]
    up = next((x for x in ps if x['id'] == p.get('parent')), None)
    word = 'art' if p['kind'] in ('booster_pack', 'blister_pack') else 'deck'
    family = ''
    if kids:
        family = (f'<section class="others"><h2>{"Pack arts" if word == "art" else "Decks"}<span>each tracked on its own</span></h2>'
                  f'<p class="mt">The price above counts every sale of this {e(KIND.get(p["kind"], "item").lower())}, including listings that don\'t say which {word} it is. '
                  f'Each {word} also has its own page with only the sales that name it.</p>'
                  f'<div class="grid sgrid">{"".join(tile(x) for x in kids)}</div></section>')
    elif up:
        sib = [x for x in ps if x.get('parent') == up['id'] and x['id'] != p['id']]
        family = (f'<section class="others"><h2>Other {word}s<span>{e(up["name"])}</span></h2>'
                  f'<p class="mt">This page only counts sales that name this {word}. <a href="/sealed/{e(up["slug"])}/">Every sale of the {e(KIND.get(up["kind"], "item").lower())}, any {word} →</a></p>'
                  + (f'<div class="grid sgrid">{"".join(tile(x) for x in sib)}</div>' if sib else '') + '</section>')
    fam_ids = {x['id'] for x in kids} | ({up['id']} | {x['id'] for x in ps if x.get('parent') == up['id']} if up else set())
    same = [x for x in ps if x['set'] == p['set'] and x['id'] != p['id'] and x['id'] not in fam_ids and not x.get('parent')]
    others = (f'<section class="others"><h2>More sealed from {e(p["set_name"])}</h2><div class="grid sgrid">{"".join(tile(x) for x in same)}</div></section>' if same else '')
    credit = f'<p class="mt scred">{e(p["credit"])} from an eBay listing</p>' if p.get('credit') else ''
    body = f'''<nav class="crumb"><a href="/">All cards</a> › <a href="/sealed/">Sealed</a> › {e(p["name"])}</nav>
<section class="cardpage sealpage"><div class="art">{pic(p, "sbig", eager=True)}{credit}</div>
<div class="info"><h1>{e(p["name"])}</h1>
<p class="mt">Sealed {e(KIND.get(p["kind"], "product").lower())} · Bandai Naruto CCG{" · " + e(yr) if yr else ""}</p>
{val}<dl class="sfacts">{facts_html}</dl>{note}
<section class="scoll" id="scoll" data-product="{e(p["id"])}" data-name="{e(p["name"])}"><h4>Your sealed collection</h4><p class="mt">Sign in to mark this as one you have or want.</p></section>
{live_block(p)}</div></section>
<section class="market one">{price_block(p)}</section>
{family}
{f'<p class="btns"><a class="ghostbtn" href="/set/{e(B.set_slug(s))}/">Every card in {e(s["name"])} →</a></p>' if s else ''}
{others}
<section class="others"><h2>All sealed</h2><p class="mt"><a href="/sealed/">Every Naruto CCG sealed product and its price →</a></p></section>
'''
    graph = [B.crumbs(('Naruto CCG cards', B.SITE + '/'), ('Sealed', B.SITE + '/sealed/'), (p['name'], url))]
    prod = {'@type': 'Product', 'name': f'{p["name"]} (sealed)', 'brand': {'@type': 'Brand', 'name': 'Bandai'},
            'category': 'Collectible card game sealed product', 'url': url}
    if p.get('img'):
        prod['image'] = p['img']
    ll = p.get('live') or []
    if ll:
        prod['offers'] = {'@type': 'AggregateOffer', 'priceCurrency': 'USD', 'lowPrice': ll[0]['p'],
                          'highPrice': max(x['p'] for x in ll), 'offerCount': p.get('live_n') or len(ll)}
        graph.append(prod)
    ld = B.ld_json({'@context': 'https://schema.org', '@graph': graph})
    body += f'<script src="/sealed-coll.js?v={B.file_version("sealed-coll.js")}" defer></script>\n'
    return B.HEAD.format(title=e(title), desc=e(desc), url=url, img=e(p.get('img') or B.SITE + '/og.png'),
                         tw='summary_large_image', ld=ld) + body + B.FOOT


def build(sets_by_id):
    """Writes the pages; returns (files changed, urls for the sitemap)."""
    ps = load()
    root = os.path.join(B.ROOT, 'sealed')
    if not ps:
        return 0, []
    changed, keep = 0, set()
    changed += B.write(os.path.join(root, 'index.html'), index_page(ps, sets_by_id))
    for p in ps:
        keep.add(p['slug'])
        changed += B.write(os.path.join(root, p['slug'], 'index.html'), product_page(p, ps, sets_by_id))
    for name in sorted(os.listdir(root)):
        if os.path.isdir(os.path.join(root, name)) and name not in keep:
            shutil.rmtree(os.path.join(root, name))
    return changed, [f'{B.SITE}/sealed/'] + [f'{B.SITE}/sealed/{p["slug"]}/' for p in ps]
