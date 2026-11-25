"""Build static, indexable pages for jonin.cards from public/cards.json.

Writes:
  public/card/<set>-<number>/index.html   one page per card
  public/set/<set>/index.html             one page per set (card list)
  public/articles/...                     articles from pipeline/articles/*.md (see articles_build.py)
  public/sitemap.xml, public/robots.txt
Output is deterministic (no timestamps), so the sync workflow only commits real changes.
Stale card/set folders (cards removed or renumbered) are deleted.
usage: python pipeline/build_pages.py
"""
import datetime, hashlib, html, json, os, re, shutil, sys
from urllib.parse import quote

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'public')
SITE = 'https://jonin.cards'
e = lambda s: html.escape(str(s or ''), quote=True)

PSA_POP = 'https://www.psacard.com/pop/tcg-cards/'
PSA = json.loads(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'psa_sets.json')).read())
SOLD = 'https://www.ebay.com/sch/i.html?LH_Sold=1&LH_Complete=1&_sop=13&_nkw='
NOT_KO = ' -kayou -mythos -proxy -custom -orica -fan'
# eBay Partner Network tracking (campaign 5339245160); customid tells card-page clicks apart in EPN reports.
EPN = '&mkevt=1&mkcid=1&mkrid=711-53200-19255-0&campid=5339245160&toolid=10001&customid=jonin-card-page'


def slug(c):
    return (c['s'] + '-' + c['n']).lower()


def set_slug(s):
    return s['id'].lower()


SYMV = '2'  # bump when symbol images change so browsers drop cached copies


def sym_img(s):
    return f'<img class="ssym" src="{e(s["symbol"])}?v={SYMV}" alt="" loading="lazy">' if s.get('symbol') else ''


def set_label(s):
    return 'Set ' + s['id'] if s.get('kind') == 'Main' else 'Promo' if s.get('kind') == 'Promo' else s['id']


def sold(q, kind):
    extra = ' (psa,bgs,cgc,sgc)' if kind == 'slab' else ' -psa -bgs -cgc -sgc'
    return SOLD + quote('naruto ' + q + extra + NOT_KO) + EPN


def card_q(c):
    m = re.search(r'\d+', c['n'])
    return '"' + re.sub(r'\s*\[.*\]', '', c['name']) + '" ' + (m.group(0) if m else '')


IG_URL = 'https://www.instagram.com/jonin.cards/'
IG_SVG = '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="5.5" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="12" cy="12" r="4.2" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="17.3" cy="6.7" r="1.3" fill="currentColor"/></svg>'
IG_HEADER = '<a class="igf" href="https://www.instagram.com/jonin.cards/" target="_blank" rel="noopener" aria-label="Follow Jonin on Instagram"><svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="5.5" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="12" cy="12" r="4.2" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="17.3" cy="6.7" r="1.3" fill="currentColor"/></svg><span>Follow<span class="h"> @jonin.cards</span></span></a>'
IG_FOOT = '<div class="igrow"><a class="igbtn" href="https://www.instagram.com/jonin.cards/" target="_blank" rel="noopener"><svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="5.5" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="12" cy="12" r="4.2" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="17.3" cy="6.7" r="1.3" fill="currentColor"/></svg><span>Follow <b class="h">@jonin.cards</b></span></a><span>New finds, top sales and set spotlights on Instagram.</span></div>'

IG_END = ('<div class="igend"><p>Get Naruto CCG news and top sales in your feed.</p>'
          f'<a class="igbtn" href="{IG_URL}" target="_blank" rel="noopener">{IG_SVG}<span>Follow <b class="h">@jonin.cards</b></span></a></div>\n')

HEAD = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{url}">
<link rel="icon" href="/favicon-32.png" sizes="32x32"><link rel="apple-touch-icon" href="/apple-touch-icon.png">
<meta name="theme-color" content="#1B1622">
<meta property="og:type" content="website"><meta property="og:site_name" content="Jonin">
<meta property="og:title" content="{title}"><meta property="og:description" content="{desc}">
<meta property="og:image" content="{img}"><meta property="og:url" content="{url}">
<meta name="twitter:card" content="{tw}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Baloo+2:wght@700;800&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/pages.css?v={cssv}"><link rel="stylesheet" href="/themes.css?v=2"><link rel="stylesheet" href="/prem.css?v={premv}"><script src="/theme.js?v=2"></script>
{ld}
</head>
<body>
<header><div class="hw"><a class="logo" href="/" aria-label="Jonin home"><span class="jc" aria-hidden="true"><i></i><i><b>J</b></i></span><span aria-hidden="true">ONIN</span></a>
<nav><a href="/">Cards</a><a href="/#sets">Sets</a><a href="/characters/">Characters</a><a href="/lists/">Lists</a><a href="/news/">News</a><a href="/articles/">Articles</a><div class="pn"><a class="pnb" href="/premium/"><svg class="lk" viewBox="0 0 14 17" aria-hidden="true"><defs><linearGradient id="lkn" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#FFE99A"/><stop offset=".45" stop-color="#F2C14E"/><stop offset="1" stop-color="#B07A1C"/></linearGradient></defs><g class="lift"><path class="sh" d="M4 8.5V5.5a3 3 0 0 1 6 0v3" fill="none" stroke="#E0B045" stroke-width="2.1" stroke-linecap="round"/></g><g class="bd"><rect x="1" y="8" width="12" height="9" rx="2.2" fill="url(#lkn)" stroke="#8C5F14" stroke-width=".6"/><circle cx="7" cy="11.7" r="1.35" fill="#5C3D0A"/><rect x="6.4" y="12" width="1.2" height="2.6" rx=".55" fill="#5C3D0A"/></g></svg>Premium</a><div class="pdd"><div class="scr"><i class="rod"></i><div class="paper"><div class="in"><div class="pad"><h4>What Premium unlocks</h4><ul><li>Exact prices by edition, foil and grade</li><li>Every sold listing, linked to the sale</li><li>Price estimates and sort by market value</li><li>Alerts for the cards you&#39;re hunting</li><li>Buy and sell posts from the Naruto CCG marketplaces</li></ul><a class="go" href="/premium/">See Premium →</a></div></div></div><i class="rod"></i></div></div></div></nav>{igh}</div></header>
<main>
'''
FOOT = '''</main>
<footer>{igf}Jonin is a fan-made database for the original Bandai Naruto Collectible Card Game (2006–2013). Not affiliated with Bandai, Shueisha or Masashi Kishimoto. Some eBay links are affiliate links: Jonin may earn a small commission at no cost to you. <a href="/privacy/">Privacy</a> · <a href="/terms/">Terms</a></footer>
<script src="/feedback.js?v=1" defer></script>
</body></html>
'''.replace('{igf}', IG_FOOT)


def ld_json(obj):
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False).replace('</', '<\\/') + '</script>'


def crumbs(*items):
    """BreadcrumbList structured data: items are (name, url) pairs, last one is the page itself."""
    return {'@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': i + 1, 'name': n, 'item': u} for i, (n, u) in enumerate(items)]}


def money(v):
    return '$' + (f'{round(v):,}' if v >= 100 else (f'{v:.2f}'.removesuffix('.00')))


BANDS = ['Under $10', '$10–50', '$50–200', '$200+']   # replaced by cards.json "bands" in main()


def price_block(c):
    """Free "Market price": one price band for the whole card. Exact prices by edition, foil and grade,
    and every sold listing, are Premium."""
    pb = c.get('pb')
    lock = (f'<a class="pxt" href="/premium/?card={quote(c["s"] + ":" + c["n"])}&amp;name={quote(c["name"])}" '
            'aria-label="See exact prices and sold listings with Premium">'
            '<div class="rows" aria-hidden="true"><div><span>1st Edition · Foil · PSA 9</span><b>$000.00</b></div><div><span>Unlimited · Raw · NM</span><b>$00.00</b></div><div><span>1st Edition · Raw · LP</span><b>$00.00</b></div></div><span class="cta"><span><svg class="lk" viewBox="0 0 14 17" aria-hidden="true"><defs><linearGradient id="lkt" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#FFE99A"/><stop offset=".45" stop-color="#F2C14E"/><stop offset="1" stop-color="#B07A1C"/></linearGradient></defs><g class="lift"><path class="sh" d="M4 8.5V5.5a3 3 0 0 1 6 0v3" fill="none" stroke="#E0B045" stroke-width="2.1" stroke-linecap="round"/></g><g class="bd"><rect x="1" y="8" width="12" height="9" rx="2.2" fill="url(#lkt)" stroke="#8C5F14" stroke-width=".6"/><circle cx="7" cy="11.7" r="1.35" fill="#5C3D0A"/><rect x="6.4" y="12" width="1.2" height="2.6" rx=".55" fill="#5C3D0A"/></g></svg>Exact prices &amp; sold listings</span><small>Every sale by edition, foil and grade</small></span>' '</a>')
    if pb is None or not 0 <= pb < len(BANDS):
        return f'<section class="px"><h3>Market price</h3>{lock}</section>'
    return (f'<section class="px"><h3>Market price<span>across all versions</span></h3>'
            f'<p class="band">{e(BANDS[pb])}</p>{lock}</section>')


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from settings import MOST_VALUABLE_CHARACTERS, MOST_VALUABLE_TOP, MOST_VALUABLE_MIN_CARDS, CHARACTER_EXTRA_NAMES
import articles_build as AB
import lists_build as LB
featured_in = lambda c: AB.featured_in(c)

NOTES = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'character_notes.json')
RANK = {'Super Rare': 0, 'Promo': 1, 'Rare': 2, 'Uncommon': 3, 'Starter': 4, 'Common': 5}


def base_name(n):
    return re.sub(r'\s*\(.*?\)\s*', ' ', n).strip()


def load_chars():
    """The character list is the homepage's QUICK list (label, 'char:Name|Alias'), so the sidebar,
    the faces in public/chars/ and these pages always agree."""
    src = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
    m = re.search(r'const QUICK=(\[.*?\]);', src)
    out = []
    for label, q in json.loads(m.group(1).replace("'", '"')) if m else []:
        if q.startswith('char:'):
            names = q[5:].split('|')
            slug = re.sub(r'[^a-z0-9]+', '-', label.lower()).strip('-')
            out.append({'label': label, 'name': names[0], 'names': names, 'slug': slug,
                        'extra': CHARACTER_EXTRA_NAMES.get(slug, [])})
    return out


def char_cards(ch, cards):
    want, exact = set(ch['names']), set(ch.get('extra') or [])
    return [c for c in cards if any(x.strip() in exact or base_name(x) in want for x in re.split(r'\s*&\s*', c['name']))]


def char_of(x, chars_by_name):
    """The character a card-name part belongs to: an exact extra name first (e.g. "Susano'o (Sasuke)"), then its base name."""
    return chars_by_name.get(x.strip()) or chars_by_name.get(base_name(x))


def char_links_for(c, chars_by_name):
    seen, out = set(), []
    for x in re.split(r'\s*&\s*', c['name']):
        ch = char_of(x, chars_by_name)
        if ch and ch['slug'] not in seen:
            seen.add(ch['slug'])
            out.append(f'<a href="/character/{ch["slug"]}/">{e(ch["name"])}</a>')
    return ', '.join(out)


def year(rel):
    m = re.search(r'(19|20)\d\d', rel or '')
    return m.group(0) if m else ''


def tile(c, s):
    img = (f'<img loading="lazy" src="{e(c["img"])}" alt="{e(c["name"])} {e(c["n"])} Naruto CCG card" width="750" height="1050">'
           if re.match(r'^https://', c.get('img') or '') else f'<span class="noimg sm"><b>{e(c["n"])}</b></span>')
    return (f'<a class="tile" href="/card/{slug(c)}/" data-card="{e(c["s"] + ":" + c["n"])}">{img}<span class="tt">{e(c["name"])}</span>'
            f'<span class="tn stag">{sym_img(s)}{e(s["name"])}</span><span class="tn">{e(c["n"])} · {e(c["r"])}</span></a>')


def char_page(ch, cs, sets_by_id, chars, notes):
    url = f'{SITE}/character/{ch["slug"]}/'
    n = len(cs)
    in_sets = [sid for sid in sets_by_id if any(c['s'] == sid for c in cs)]
    main_sets = [sid for sid in in_sets if sets_by_id[sid].get('kind') == 'Main']
    first, last = (sets_by_id[main_sets[0]], sets_by_id[main_sets[-1]]) if main_sets else (None, None)
    rc = {}
    for c in cs:
        rc[c['r']] = rc.get(c['r'], 0) + 1
    rar = ', '.join(f'{rc[r]} {r}{"s" if rc[r] > 1 and r not in ("Common", "Uncommon") else ""}'
                    for r in sorted(rc, key=lambda r: RANK.get(r, 9)) if r != 'Unknown')
    title = f"{ch['name']} Naruto CCG cards: all {n} cards | Jonin"
    span = (f" from {first['name']} ({year(first.get('rel'))}) to {last['name']} ({year(last.get('rel'))})"
            if first and last and first is not last else f" in {first['name']}" if first else '')
    desc = (f"Every {ch['name']} card in the original Bandai Naruto CCG: {n} cards across {len(in_sets)} sets{span}. "
            f"Rarities, printings, foils and 1st Editions.")
    intro = (f"{e(ch['name'])} appears on {n} card{'s' if n != 1 else ''} in the original Bandai Naruto CCG, "
             f"across {len(in_sets)} set{'s' if len(in_sets) != 1 else ''}{e(span)}"
             + (f": {e(rar)}." if rar else '.'))
    note = notes.get(ch['slug'], '').strip()
    facts = [('Cards', str(n)), ('Sets', str(len(in_sets)))]
    if first:
        fc = next(c for c in cs if c['s'] == first['id'])
        facts.append(('First card', f'<a href="/card/{slug(fc)}/">{e(fc["name"])} {e(fc["n"])}</a> · {e(first["name"])}'))
    if len(ch['names']) > 1:
        facts.append(('Also printed as', e(', '.join(ch['names'][1:]))))
    key = sorted([c for c in cs if c['r'] in ('Super Rare', 'Promo')],
                 key=lambda c: (-(c.get('pb') if c.get('pb') is not None else -1), RANK.get(c['r'], 9)))[:8] if n >= 15 else []
    groups = ''.join(
        f'<section class="cgroup"><h2><a href="/set/{set_slug(sets_by_id[sid])}/">{sym_img(sets_by_id[sid])}{e(sets_by_id[sid]["name"])}</a>'
        f'<span>{e(set_label(sets_by_id[sid]))}{" · " + e(year(sets_by_id[sid].get("rel"))) if sets_by_id[sid].get("rel") else ""}</span></h2>'
        f'<div class="grid">{"".join(tile(c, sets_by_id[sid]) for c in cs if c["s"] == sid)}</div></section>'
        for sid in in_sets)
    art = f'/char-art/{ch["slug"]}.webp'
    mvlink = (f'<a class="ghostbtn" href="/character/{ch["slug"]}/most-valuable/">💰 Most valuable {e(ch["label"])} cards</a>'
              if ch.get('mv') else '') + (f'<a class="ghostbtn" href="/character/{ch["slug"]}/most-popular/">⭐ Most popular {e(ch["label"])} cards</a>'
              if ch.get('pop') else '')
    others = ''.join(f'<a class="chip" href="/character/{o["slug"]}/"><img src="/chars/{o["slug"]}.webp" alt="" width="24" height="24" loading="lazy">{e(o["label"])}</a>'
                     for o in chars if o is not ch)
    body = f'''<nav class="crumb"><a href="/">All cards</a> › <a href="/characters/">Characters</a> › {e(ch["name"])}</nav>
<section class="sethead charhead"><img class="hero" src="{art}" alt="{e(ch["name"])} in action, from a Naruto CCG card" width="480" height="360">
<h1>{e(ch["name"])} cards</h1>
<p class="lede">{intro}</p>
{f'<p class="lede">{e(note)}</p>' if note else ''}
<dl class="inline">{''.join(f'<dt>{k}</dt><dd>{v}</dd>' for k, v in facts)}</dl>
<p class="btns"><a class="primary" href="/#quick={quote('char:' + '|'.join(ch['names']))}">Browse and filter {e(ch['label'])} cards</a>{mvlink}</p></section>
<section class="votetop" id="vote-top" data-character="{ch['slug']}" data-name="{e(ch['label'])}"><h2>Coolest {e(ch['label'])} cards<span>Top 3, voted by collectors</span></h2>
<p class="vbar" id="vote-bar"></p><p class="vnote" id="vote-note"></p><div class="grid" id="vote-grid"></div><p class="vtoast" id="vote-toast" role="status" hidden></p></section>
{f'<section class="cgroup"><h2>Key cards<span>Super Rares and promos</span></h2><div class="grid">{"".join(tile(c, sets_by_id[c["s"]]) for c in key)}</div></section>' if key else ''}
{groups}
<section class="others"><h2>More characters</h2><div class="chips">{others}</div></section>
<script src="/vote.js?v={file_version('vote.js')}" defer></script>
'''
    img = next((c['img'] for c in key + cs if re.match(r'^https://', c.get('img') or '')), SITE + '/og.png')
    ld = ld_json({'@context': 'https://schema.org', '@graph': [
        {'@type': 'CollectionPage', 'name': title, 'description': desc, 'url': url, 'image': img,
         'about': {'@type': 'Thing', 'name': ch['name']}},
        crumbs(('Naruto CCG cards', SITE + '/'), ('Characters', SITE + '/characters/'), (ch['name'], url))]})
    return HEAD.format(title=e(title), desc=e(desc), url=url, img=e(img), tw='summary_large_image', ld=ld) + body + FOOT


def mv_live(cs):
    """A character's most-valuable list is live once MOST_VALUABLE_MIN_CARDS of their cards have a sale."""
    return sum(1 for c in cs if c.get('top')) >= MOST_VALUABLE_MIN_CARDS


def most_valuable(cs, top=MOST_VALUABLE_TOP):
    """A character's cards ranked by their single highest sale. Each card appears once (its best-selling
    version), so a card and its foil can't both take spots."""
    return sorted([c for c in cs if c.get('top')], key=lambda c: c['top'][0])[:top]


def mv_page(ch, ranked, sets_by_id, mv_chars):
    url = f'{SITE}/character/{ch["slug"]}/most-valuable/'
    n = len(ranked)
    title = f"Most valuable {ch['name']} cards in the Naruto CCG (top {n}) | Jonin"
    lead = ranked[0]
    desc = (f"The {n} most valuable {ch['name']} cards in the original Bandai Naruto CCG, ranked by their highest recorded sale. "
            f"#1: {lead['name']} {lead['n']} ({sets_by_id[lead['s']]['name']}).")
    upd = max((c['top'][3] for c in ranked), default='')
    rows = []
    for i, c in enumerate(ranked):
        s = sets_by_id[c['s']]
        b, ver, sold_on = c['top'][1], c['top'][2], c['top'][3]
        price = c['top'][4] if len(c['top']) > 4 else None
        sale_url = c['top'][5] if len(c['top']) > 5 else ''
        img = (f'<img loading="{"eager" if i == 0 else "lazy"}" src="{e(c["img"])}" alt="{e(c["name"])} {e(c["n"])} Naruto CCG card" width="750" height="1050">'
               if re.match(r'^https://', c.get('img') or '') else f'<span class="noimg sm"><b>{e(c["n"])}</b></span>')
        lock = f'/premium/?card={quote(c["s"] + ":" + c["n"])}&amp;name={quote(c["name"])}'
        band = ('$' + f'{price:,.2f}'.removesuffix('.00')) if price else (e(BANDS[b]) if 0 <= b < len(BANDS) else '—')
        src = AB.sale_link(sale_url, c['top'][6] if len(c['top']) > 6 else '').removeprefix(' · ') if price else ''
        rows.append(
            f'<li class="mvrow"><span class="mvn">{i + 1}</span><a class="mvart" href="/card/{slug(c)}/">{img}</a>'
            f'<div class="mvinfo"><h2><a href="/card/{slug(c)}/">{e(c["name"])}</a></h2>'
            f'<p class="mt"><span class="stag">{sym_img(s)}{e(s["name"])}</span> · {e(c["n"])} · {e(c["r"])}</p>'
            f'<dl><dt>Top sale</dt><dd><b class="band">{band}</b></dd><dt>Version</dt><dd>{e(ver) or "—"}</dd>'
            f'<dt>Sold</dt><dd>{e(sold_on) or "—"}{" · " + src if src else ""}</dd></dl>'
            f'<a class="pxlock" href="{lock}"><span>🔒 Every sale of this card, by edition, foil and grade</span><b>Premium →</b></a></div></li>')
    others = ''.join(f'<a class="chip" href="/character/{o["slug"]}/most-valuable/"><img src="/chars/{o["slug"]}.webp" alt="" width="24" height="24" loading="lazy">{e(o["label"])}</a>'
                     for o in mv_chars if o is not ch)
    others_html = (f'<section class="others"><h2>Most valuable cards of other characters</h2><div class="chips">{others}</div></section>'
                   if others else '')
    updated = f' · latest sale counted {e(upd)}' if upd else ''
    body = f'''<nav class="crumb"><a href="/">All cards</a> › <a href="/characters/">Characters</a> › <a href="/character/{ch["slug"]}/">{e(ch["name"])}</a> › <a href="/most-valuable/">Most valuable</a></nav>
<section class="sethead charhead"><h1><img class="face" src="/chars/{ch["slug"]}.webp" alt="" width="56" height="56">Most valuable {e(ch["name"])} cards</h1>
<p class="lede">The top {n} {e(ch["name"])} cards in the original Bandai Naruto CCG, ranked by the highest price each card has sold for. Each card gets one spot, counted by its best-selling version (edition, foil or grade).</p>
<p class="mt">Updates on its own as new sales come in{updated}.</p></section>
<ol class="mvlist">{"".join(rows)}</ol>
<p class="btns" style="margin-top:26px"><a class="primary" href="/character/{ch["slug"]}/">All {e(ch["label"])} cards</a><a class="ghostbtn" href="/most-valuable/">💰 Every most-valuable list</a></p>
{others_html}
'''
    img = next((c['img'] for c in ranked if re.match(r'^https://', c.get('img') or '')), SITE + '/og.png')
    ld = ld_json({'@context': 'https://schema.org', '@graph': [
        {'@type': 'ItemList', 'name': title, 'description': desc, 'url': url, 'numberOfItems': n,
         'itemListOrder': 'https://schema.org/ItemListOrderDescending',
         'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'name': f"{c['name']} {c['n']}",
                              'url': f'{SITE}/card/{slug(c)}/'} for i, c in enumerate(ranked)]},
        crumbs(('Naruto CCG cards', SITE + '/'), ('Characters', SITE + '/characters/'),
               (ch['name'], f'{SITE}/character/{ch["slug"]}/'), ('Most valuable', url))]})
    return HEAD.format(title=e(title), desc=e(desc), url=url, img=e(img), tw='summary_large_image', ld=ld) + body + FOOT


def mv_index(mv_chars, ranked, sets_by_id):
    """/most-valuable/: every character's most-valuable list on one page (a list of lists), for search."""
    url = f'{SITE}/most-valuable/'
    names = ', '.join(c['label'] for c in mv_chars)
    title = 'Most expensive Naruto CCG cards: top lists from the Naruto card game | Jonin'
    desc = (f'The most valuable cards in the original Bandai Naruto CCG, ranked by highest recorded sale. '
            f'Top {MOST_VALUABLE_TOP} lists for {names}, updated as new sales come in.')

    def price(c):
        p = c['top'][4] if len(c['top']) > 4 else None
        return ('$' + f'{p:,.2f}'.removesuffix('.00')) if p else (e(BANDS[c['top'][1]]) if 0 <= c['top'][1] < len(BANDS) else '')

    def mini(c, i):
        img = (f'<img loading="lazy" src="{e(c["img"])}" alt="{e(c["name"])} {e(c["n"])} Naruto CCG card" width="750" height="1050">'
               if re.match(r'^https://', c.get('img') or '') else f'<span class="noimg sm"><b>{e(c["n"])}</b></span>')
        return (f'<a class="mvmini" href="/card/{slug(c)}/"><span class="mvn">{i + 1}</span>{img}'
                f'<b>{e(c["name"])}</b><span class="mt">{e(c["n"])} · {e(sets_by_id[c["s"]]["name"])}</span><span class="band">{price(c)}</span></a>')
    blocks = []
    for ch in mv_chars:
        r = ranked[ch['slug']]
        lu = f'/character/{ch["slug"]}/most-valuable/'
        blocks.append(
            f'<section class="mvlistcard"><h2><a href="{lu}"><img class="face" src="/chars/{ch["slug"]}.webp" alt="" width="44" height="44">'
            f'Most valuable {e(ch["name"])} cards</a><span>Top {len(r)}</span></h2>'
            f'<div class="mvminis">{"".join(mini(c, i) for i, c in enumerate(r[:3]))}</div>'
            f'<p class="btns"><a class="primary" href="{lu}">See the full top {len(r)} →</a></p></section>')
    body = ('<nav class="crumb"><a href="/">All cards</a> › <a href="/lists/">Lists</a> › Most valuable</nav>\n'
            '<section class="sethead"><h1>Most expensive Naruto CCG cards</h1>\n'
            '<p class="lede">The most valuable cards in the whole original Bandai Naruto card game (2006–2013), with one list per character, '
            'ranked by the highest price each card has sold for. Lists update on their own as new sales come in.</p></section>\n'
            + ''.join(blocks)
            + '\n<p class="mt" style="margin-top:22px">More characters are coming. <a href="/characters/">Browse every character</a> · <a href="/most-popular/">Most popular cards</a> · <a href="/lists/">All card lists</a>.</p>\n')
    img = next((c['img'] for ch in mv_chars for c in ranked[ch['slug']] if re.match(r'^https://', c.get('img') or '')), SITE + '/og.png')
    ld = ld_json({'@context': 'https://schema.org', '@graph': [
        {'@type': 'ItemList', 'name': title, 'description': desc, 'url': url, 'numberOfItems': len(mv_chars),
         'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'name': f"Most valuable {ch['name']} cards",
                              'url': f'{SITE}/character/{ch["slug"]}/most-valuable/'} for i, ch in enumerate(mv_chars)]},
        crumbs(('Naruto CCG cards', SITE + '/'), ('Lists', SITE + '/lists/'), ('Most valuable', url))]})
    return HEAD.format(title=e(title), desc=e(desc), url=url, img=e(img), tw='summary_large_image', ld=ld) + body + FOOT


def chars_index(chars, counts):
    url = f'{SITE}/characters/'
    title = 'Naruto CCG cards by character | Jonin'
    desc = ('Browse every card in the original Bandai Naruto CCG by character: Naruto, Sasuke, Kakashi, Itachi, Gaara '
            f'and {len(chars) - 5} more, with every printing, foil and 1st Edition.')
    cells = ''.join(f'<a class="ccell" href="/character/{c["slug"]}/"><img src="/char-art/{c["slug"]}.webp" alt="" width="480" height="360" loading="lazy">'
                    f'<b>{e(c["name"])}</b><span>{counts[c["slug"]]} cards</span></a>' for c in chars)
    mv = [c for c in chars if c.get('mv')]
    mvrow = (f'<section class="others" id="most-valuable"><h2><a href="/most-valuable/">Most valuable cards</a><span>Top {MOST_VALUABLE_TOP} by highest sale</span></h2><div class="chips">'
             + ''.join(f'<a class="chip" href="/character/{c["slug"]}/most-valuable/"><img src="/chars/{c["slug"]}.webp" alt="" width="24" height="24" loading="lazy">Most valuable {e(c["label"])} cards</a>' for c in mv)
             + '</div></section>') if mv else ''
    body = f'''<nav class="crumb"><a href="/">All cards</a> › Characters</nav>
<section class="sethead"><h1>Naruto CCG cards by character</h1>
<p class="lede">Every character card in the original Bandai Naruto CCG (2006–2013), grouped by character. Pick a character to see all of their cards set by set.</p>
<p class="btns">{'<a class="primary" href="/most-valuable/">💰 Most valuable cards</a>' if mv else ''}<a class="ghostbtn" href="/most-popular/">⭐ Most popular cards</a><a class="ghostbtn" href="/lists/">All card lists</a></p></section>
<section class="cindex">{cells}</section>
{mvrow}'''
    ld = ld_json({'@context': 'https://schema.org', '@graph': [
        {'@type': 'CollectionPage', 'name': title, 'description': desc, 'url': url},
        crumbs(('Naruto CCG cards', SITE + '/'), ('Characters', url))]})
    return HEAD.format(title=e(title), desc=e(desc), url=url, img=e(SITE + '/og.png'), tw='summary_large_image', ld=ld) + body + FOOT


def file_version(name):
    return hashlib.sha1(open(os.path.join(ROOT, name), 'rb').read()).hexdigest()[:8]


def css_version():
    # Changes whenever pages.css changes, so browsers and Cloudflare never serve a stale copy.
    return hashlib.sha1(open(os.path.join(ROOT, 'pages.css'), 'rb').read()).hexdigest()[:8]


def card_page(c, s, prev, nxt, chars_by_name=None):
    img = c.get('img') if re.match(r'^https://', c.get('img') or '') else ''
    url = f'{SITE}/card/{slug(c)}/'
    eds = [x for x in (c.get('ed') or []) if x]
    title = f"{c['name']} {c['n']} · {s['name']} | Naruto CCG | Jonin"
    desc = (f"{c['name']} ({c['n']}) from {s['name']}"
            f"{' (' + s['rel'] + ')' if s.get('rel') else ''}: {c['r']} {c['t']} card in the Bandai Naruto CCG. "
            f"Printings: {', '.join(c.get('v') or [])}{'; ' + ' and '.join(eds) if eds else ''}.")
    psa = (f'<a href="{e(PSA_POP + PSA[c["s"]])}" target="_blank" rel="noopener">PSA pop report · {e(set_label(s))}</a>'
           if c['s'] in PSA else '<a href="https://www.psacard.com/pop/tcg-cards" target="_blank" rel="noopener">PSA pop report</a>')
    art = (f'<img src="{e(img)}" alt="{e(c["name"])} {e(c["n"])} Naruto CCG card scan" width="750" height="1050">'
           if img else f'<div class="noimg"><b>{e(c["n"])}</b><span>{e(c["t"])} · scan coming soon</span></div>')
    rows = [('Set', f'<a class="stag" href="/set/{set_slug(s)}/">{sym_img(s)}{e(s["name"])}</a> · {e(set_label(s))}{" · " + e(s["rel"]) if s.get("rel") else ""}'),
            ('Number', e(c['n'])), ('Rarity', e(c['r'])), ('Type', e(c['t'])),
            ('Editions', e(', '.join(eds) or '—')),
            ('Printings', ''.join(f'<span class="pv">{e(v)}</span>' for v in (c.get('v') or [])))]
    cl = char_links_for(c, chars_by_name or {})
    if cl:
        rows.insert(1, ('Character', cl))
        chs = []
        for x in re.split(r'\s*&\s*', c['name']):
            ch = char_of(x, chars_by_name or {})
            if ch and ch['slug'] + ':' + ch['label'] not in chs:
                chs.append(ch['slug'] + ':' + ch['label'])
        rows.insert(2, ('Votes', f'<span class="cvotes" data-card="{e(c["s"] + ":" + c["n"])}" data-chars="{e(",".join(chs))}">…</span>'))
    if c.get('note'):
        rows.append(('Note', e(c['note'])))
    ld = ld_json({'@context': 'https://schema.org', '@graph': [
        {'@type': 'Thing', 'name': f"{c['name']} ({c['n']})",
         'description': desc, 'url': url, **({'image': img} if img else {}),
         'isPartOf': {'@type': 'CreativeWork', 'name': f"Naruto CCG · {s['name']}", 'url': f'{SITE}/set/{set_slug(s)}/'}},
        crumbs(('Naruto CCG cards', SITE + '/'), (s['name'], f'{SITE}/set/{set_slug(s)}/'), (f"{c['name']} {c['n']}", url))]})
    nav = ''.join([
        f'<a class="pn" href="/card/{slug(prev)}/" rel="prev">‹ {e(prev["n"])} {e(prev["name"])}</a>' if prev else '<span></span>',
        f'<a class="pn" href="/card/{slug(nxt)}/" rel="next">{e(nxt["n"])} {e(nxt["name"])} ›</a>' if nxt else '<span></span>'])
    body = f'''<nav class="crumb"><a href="/">All cards</a> › <a href="/set/{set_slug(s)}/">{e(s["name"])}</a> › {e(c["n"])}</nav>
<article class="cardpage">
<div class="art">{art}</div>
<div class="info">
<h1>{e(c["name"])}</h1>
<p class="mt">{e(s["name"])} · {e(c["n"])} · {e(c["r"])}</p>
<dl>{''.join(f'<dt>{k}</dt><dd>{v}</dd>' for k, v in rows)}</dl>
{price_block(c)}{('<script src="/card-votes.js?v=' + file_version('card-votes.js') + '" defer></script>') if cl else ''}
<div class="links">
<a class="primary" href="/#card={quote(c['s'] + ':' + c['n'])}">Track it in your collection</a>
<a href="{e(sold(card_q(c), 'slab'))}" target="_blank" rel="sponsored noopener">eBay sold · slabs</a>
<a href="{e(sold(card_q(c), 'raw'))}" target="_blank" rel="sponsored noopener">eBay sold · raw</a>
{psa}
<a href="/premium/?card={quote(c['s'] + ':' + c['n'])}&amp;name={quote(c['name'])}">🔔 Alerts for this card</a>
</div>
{featured_in(c)}
</div>
</article>
<nav class="prevnext">{nav}</nav>
'''
    return HEAD.format(title=e(title), desc=e(desc), url=url, img=e(img or SITE + '/og.png'),
                       tw='summary_large_image', ld=ld) + body + FOOT


def set_page(s, cards):
    url = f'{SITE}/set/{set_slug(s)}/'
    title = f"{s['name']} card list · Naruto CCG {set_label(s)} | Jonin"
    rar = ', '.join(f'{v} {k}' for k, v in (s.get('rar') or {}).items())
    desc = (f"Every card in {s['name']} ({set_label(s)}{', ' + s['rel'] if s.get('rel') else ''}) for the Bandai Naruto CCG: "
            f"{len(cards)} cards{', ' + rar if rar else ''}. Printings, foils and 1st Editions.")
    facts = [('Released', e(s.get('rel') or '—')), ('Cards', str(len(cards))),
             ('1st Edition', e(s.get('first') or '—')), ('Unlimited', e(s.get('unl') or '—')),
             ('Foils', e(', '.join(s.get('foils') or []) or '—'))]
    if rar:
        facts.append(('Rarities', e(rar)))
    grid = ''.join(
        f'<a class="tile" href="/card/{slug(c)}/" data-card="{e(c["s"] + ":" + c["n"])}">'
        + (f'<img loading="lazy" src="{e(c["img"])}" alt="{e(c["name"])} {e(c["n"])}" width="750" height="1050">'
           if re.match(r'^https://', c.get('img') or '') else f'<span class="noimg sm"><b>{e(c["n"])}</b></span>')
        + f'<span class="tt">{e(c["name"])}</span><span class="tn stag">{sym_img(s)}{e(s["name"])}</span><span class="tn">{e(c["n"])}</span></a>' for c in cards)
    sym = f'<img class="sym" src="{e(s["symbol"])}?v={SYMV}" alt="">' if s.get('symbol') else ''
    body = f'''<nav class="crumb"><a href="/">All cards</a> › <a href="/#sets">Sets</a> › {e(s["name"])}</nav>
<section class="sethead"><h1>{sym}{e(s["name"])}</h1>
<dl class="inline">{''.join(f'<dt>{k}</dt><dd>{v}</dd>' for k, v in facts)}</dl>
{f'<p class="note">{e(s["notes"])}</p>' if s.get('notes') else ''}
<p><a class="primary" href="/#set={quote(s['id'])}">Browse and filter this set</a></p></section>
<section class="spx" id="set-progress" data-set="{e(s['id'])}" data-total="{len(cards)}" data-prints="{sum(max(1, len(c.get('v') or [])) * max(1, len([x for x in (c.get('ed') or []) if x])) for c in cards)}" aria-live="polite"></section>
<section class="grid">{grid}</section>
<script src="/set-progress.js?v={file_version('set-progress.js')}" defer></script>
'''
    ld = ld_json({'@context': 'https://schema.org', '@graph': [
        {'@type': 'CollectionPage', 'name': title, 'description': desc, 'url': url},
        crumbs(('Naruto CCG cards', SITE + '/'), ('Sets', SITE + '/#sets'), (s['name'], url))]})
    return HEAD.format(title=e(title), desc=e(desc), url=url, img=e(SITE + '/og.png'), tw='summary_large_image', ld=ld) + body + FOOT


NEWS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'news')


def fmt_date(iso):
    d = datetime.date.fromisoformat(iso)
    return d.strftime('%B ') + str(d.day) + d.strftime(', %Y')


def load_news():
    """Articles live in pipeline/news/<slug>.html: a <!--meta {json} --> block, then the article body HTML."""
    out = []
    for f in sorted(os.listdir(NEWS)) if os.path.isdir(NEWS) else []:
        if not f.endswith('.html'):
            continue
        raw = open(os.path.join(NEWS, f), encoding='utf-8').read()
        m = re.match(r'\s*<!--meta\s*(\{.*?\})\s*-->\s*(.*)$', raw, re.S)
        if m:
            meta = json.loads(m.group(1))
            meta['body'] = m.group(2)
            out.append(meta)
    return sorted(out, key=lambda a: a['published'], reverse=True)


def news_page(a):
    url = f"{SITE}/news/{a['slug']}/"
    title = a['title'] + ' | Jonin'
    ld = ld_json({'@context': 'https://schema.org', '@graph': [
        {'@type': 'NewsArticle', 'headline': a['title'], 'description': a['description'], 'url': url,
         'image': a.get('image') or SITE + '/og.png', 'datePublished': a['published'], 'dateModified': a.get('updated') or a['published'],
         'author': {'@type': 'Organization', 'name': 'Jonin', 'url': SITE + '/'},
         'publisher': {'@type': 'Organization', 'name': 'Jonin', 'logo': {'@type': 'ImageObject', 'url': SITE + '/icon-512.png'}}},
        crumbs(('Naruto CCG cards', SITE + '/'), ('News', SITE + '/news/'), (a.get('short') or a['title'], url))]})
    upd = f" · Updated {fmt_date(a['updated'])}" if a.get('updated') and a['updated'] != a['published'] else ''
    body = (f'<nav class="crumb"><a href="/">All cards</a> › <a href="/news/">News</a> › {e(a.get("short") or a["title"])}</nav>\n'
            f'<article class="news"><h1>{e(a["title"])}</h1><p class="mt">{fmt_date(a["published"])}{upd}</p>\n{a["body"]}</article>\n'
            + IG_END)
    return HEAD.format(title=e(title), desc=e(a['description']), url=url, img=e(a.get('image') or SITE + '/og.png'),
                       tw='summary_large_image', ld=ld) + body + FOOT


def news_index(arts):
    url = f'{SITE}/news/'
    title = 'Naruto card game news | Jonin'
    desc = 'News on Naruto trading card games: Bandai\'s new Naruto Card Game (2027), the original Bandai Naruto CCG (2006–2013) and collecting.'
    items = ''.join(f'<a class="newsitem" href="/news/{a["slug"]}/"><b>{e(a["title"])}</b><span class="mt">{fmt_date(a["published"])}</span>'
                    f'<span>{e(a["description"])}</span></a>' for a in arts)
    body = (f'<nav class="crumb"><a href="/">All cards</a> › News</nav>\n<section class="sethead"><h1>News</h1>'
            f'<p class="lede">Naruto card game news, from Bandai\'s new 2027 game to the original CCG.</p></section>\n'
            f'<section class="newslist">{items}</section>\n')
    ld = ld_json({'@context': 'https://schema.org', '@graph': [
        {'@type': 'CollectionPage', 'name': title, 'description': desc, 'url': url},
        crumbs(('Naruto CCG cards', SITE + '/'), ('News', url))]})
    return HEAD.format(title=e(title), desc=e(desc), url=url, img=e(SITE + '/og.png'), tw='summary_large_image', ld=ld) + body + FOOT


PAGES = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pages')


def load_pages():
    out = []
    for f in sorted(os.listdir(PAGES)) if os.path.isdir(PAGES) else []:
        if f.endswith('.html'):
            raw = open(os.path.join(PAGES, f), encoding='utf-8').read()
            m = re.match(r'\s*<!--meta\s*(\{.*?\})\s*-->\s*(.*)$', raw, re.S)
            if m:
                meta = json.loads(m.group(1)); meta['body'] = m.group(2); out.append(meta)
    return out


def plain_page(a):
    url = f"{SITE}/{a['slug']}/"
    body = (f'<nav class="crumb"><a href="/">All cards</a> › {e(a["title"])}</nav>\n'
            f'<article class="news"><h1>{e(a["title"])}</h1><p class="mt">Last updated {fmt_date(a["updated"])}</p>\n{a["body"]}</article>\n')
    return HEAD.format(title=e(a['title'] + ' | Jonin'), desc=e(a['description']), url=url, img=e(SITE + '/og.png'),
                       tw='summary', ld='') + body + FOOT


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    old = open(path, encoding='utf-8').read() if os.path.exists(path) else None
    if old != text:
        open(path, 'w', encoding='utf-8').write(text)
        return 1
    return 0


LASTMOD = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lastmod.json')


def page_path(u):
    rel = u[len(SITE) + 1:]
    return os.path.join(ROOT, rel, 'index.html') if rel else os.path.join(ROOT, 'index.html')


def lastmods(urls):
    """Sitemap <lastmod> per page: the date a page's content last changed. pipeline/lastmod.json keeps a
    hash and date per URL; the date only moves when the hash does, so unchanged builds stay identical."""
    old = json.load(open(LASTMOD)) if os.path.exists(LASTMOD) else {}
    today, new = datetime.date.today().isoformat(), {}
    for u in urls:
        p = page_path(u)
        h = hashlib.sha1(open(p, 'rb').read()).hexdigest()[:16] if os.path.exists(p) else ''
        prev = old.get(u)
        new[u] = prev if prev and prev[0] == h else [h, today]
    return new


def set_links(sets):
    """Plain set links for the homepage, so search engines find every set page without running JavaScript."""
    groups, order = {}, []
    for s in sets:
        k = s.get('kind') or 'Other'
        if k not in groups:
            groups[k] = []
            order.append(k)
        groups[k].append(f'<a href="/set/{set_slug(s)}/">{e(s["name"])}</a>')
    names = {'Main': 'Main sets', 'Promo': 'Promos', 'Tournament pack': 'Tournament packs', 'Tin': 'Collector tins'}
    return ('<!--setlinks--><nav class="setlinks" aria-label="All sets"><h2>All Naruto CCG sets</h2>'
            + ''.join(f'<p><b>{e(names.get(k, k))}</b> {" · ".join(groups[k])}</p>' for k in order)
            + '</nav><!--/setlinks-->')


def main():
    global HEAD
    HEAD = HEAD.replace('{igh}', IG_HEADER).replace('{cssv}', css_version()).replace('{premv}', file_version('prem.css'))
    d = json.load(open(os.path.join(ROOT, 'cards.json'), encoding='utf-8'))
    global BANDS
    BANDS = d.get('bands') or BANDS
    sets = d['sets']
    by_set = {s['id']: [] for s in sets}
    for c in d['cards']:
        if c['s'] in by_set:
            by_set[c['s']].append(c)
    chars = load_chars()
    chars_by_name = {nm: ch for ch in chars for nm in ch['names'] + ch['extra']}
    AB.setup(sys.modules[__name__])
    AB.load_sales()
    articles = AB.load_articles()
    cards_by_key = {c['s'] + ':' + c['n']: c for c in d['cards']}
    AB.set_featured(articles, cards_by_key)
    changed, keep_c, keep_s = 0, set(), set()
    for s in sets:
        cs = by_set[s['id']]
        for i, c in enumerate(cs):
            keep_c.add(slug(c))
            changed += write(os.path.join(ROOT, 'card', slug(c), 'index.html'),
                             card_page(c, s, cs[i - 1] if i else None, cs[i + 1] if i + 1 < len(cs) else None, chars_by_name))
        keep_s.add(set_slug(s))
        changed += write(os.path.join(ROOT, 'set', set_slug(s), 'index.html'), set_page(s, cs))
    sets_by_id = {x['id']: x for x in sets}
    notes = json.load(open(NOTES, encoding='utf-8')) if os.path.exists(NOTES) else {}
    keep_ch, counts, ranked = set(), {}, {}
    for ch in chars:
        if ch['slug'] in MOST_VALUABLE_CHARACTERS:
            cs = char_cards(ch, d['cards'])
            ranked[ch['slug']] = most_valuable(cs)
            ch['mv'] = bool(ranked[ch['slug']]) and mv_live(cs)
    mv_chars = [ch for ch in chars if ch.get('mv')]
    LB.setup(sys.modules[__name__])
    lchanged, list_urls = LB.build([ch for ch in chars if char_cards(ch, d['cards'])], {c['s'] + ':' + c['n']: c for c in d['cards']}, sets_by_id, mv_chars)
    changed += lchanged
    for ch in chars:
        cs = char_cards(ch, d['cards'])
        counts[ch['slug']] = len(cs)
        mvdir = os.path.join(ROOT, 'character', ch['slug'], 'most-valuable')
        if cs:
            keep_ch.add(ch['slug'])
            changed += write(os.path.join(ROOT, 'character', ch['slug'], 'index.html'), char_page(ch, cs, sets_by_id, chars, notes))
            if ch.get('mv'):
                changed += write(os.path.join(mvdir, 'index.html'), mv_page(ch, ranked[ch['slug']], sets_by_id, mv_chars))
        if not ch.get('mv') and os.path.isdir(mvdir):
            shutil.rmtree(mvdir)
    chars = [ch for ch in chars if ch['slug'] in keep_ch]
    changed += write(os.path.join(ROOT, 'characters', 'index.html'), chars_index(chars, counts))
    mvidx = os.path.join(ROOT, 'most-valuable')
    if mv_chars:
        changed += write(os.path.join(mvidx, 'index.html'), mv_index(mv_chars, ranked, sets_by_id))
    elif os.path.isdir(mvidx):
        shutil.rmtree(mvidx)
    for pg in load_pages():
        changed += write(os.path.join(ROOT, pg['slug'], 'index.html'), plain_page(pg))
    arts = load_news()
    keep_n = set()
    for a in arts:
        keep_n.add(a['slug'])
        changed += write(os.path.join(ROOT, 'news', a['slug'], 'index.html'), news_page(a))
    if arts:
        changed += write(os.path.join(ROOT, 'news', 'index.html'), news_index(arts))
    changed += AB.build_articles(articles, cards_by_key, sets_by_id)
    removed = 0
    for sub, keep in (('card', keep_c), ('set', keep_s), ('character', keep_ch)):
        base = os.path.join(ROOT, sub)
        for name in sorted(os.listdir(base)) if os.path.isdir(base) else []:
            if name not in keep:
                shutil.rmtree(os.path.join(base, name))
                removed += 1
    home = os.path.join(ROOT, 'index.html')
    hs = open(home, encoding='utf-8').read()
    hs2 = re.sub(r'<!--setlinks-->.*?<!--/setlinks-->', lambda m: set_links(sets), hs, flags=re.S)
    if hs2 == hs and '<!--setlinks-->' not in hs:
        hs2 = hs.replace('</main>', set_links(sets) + '\n</main>', 1)
    changed += write(home, hs2)
    urls = [SITE + '/'] + ([SITE + '/news/'] + [f"{SITE}/news/{a['slug']}/" for a in arts] if arts else []) + [SITE + '/characters/', SITE + '/articles/'] + [f'{SITE}/articles/{a["slug"]}/' for a in articles if not a['draft']] + [f'{SITE}/character/{ch["slug"]}/' for ch in chars] + \
           list_urls + ([SITE + '/most-valuable/'] if mv_chars else []) + [f'{SITE}/character/{ch["slug"]}/most-valuable/' for ch in mv_chars] + \
           [f'{SITE}/set/{set_slug(s)}/' for s in sets] + \
           [f'{SITE}/card/{slug(c)}/' for s in sets for c in by_set[s['id']]]
    lm = lastmods(urls)
    changed += write(LASTMOD, json.dumps(lm, indent=0, sort_keys=True) + '\n')
    changed += write(os.path.join(ROOT, 'sitemap.xml'),
                     '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                     + ''.join(f'<url><loc>{e(u)}</loc><lastmod>{lm[u][1]}</lastmod></url>\n' for u in urls) + '</urlset>\n')
    changed += write(os.path.join(ROOT, 'robots.txt'),
                     f'User-agent: *\nAllow: /\nDisallow: /admin/\n\nSitemap: {SITE}/sitemap.xml\n')
    print(f'{len(keep_c)} card pages, {len(keep_s)} set pages, {changed} files written, {removed} stale folders removed')


if __name__ == '__main__':
    sys.exit(main())
