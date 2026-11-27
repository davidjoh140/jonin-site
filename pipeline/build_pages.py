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
# eBay Partner Network tracking (campaign 5339262225); customid tells card-page clicks apart in EPN reports.
EPN = '&mkevt=1&mkcid=1&mkrid=711-53200-19255-0&campid=5339262225&toolid=10001&customid=jonin-card-page'


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
IG_HEADER = '<a class="igf" href="https://www.instagram.com/jonin.cards/" target="_blank" rel="noopener" aria-label="Follow Jonin on Instagram"><svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="5.5" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="12" cy="12" r="4.2" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="17.3" cy="6.7" r="1.3" fill="currentColor"/></svg><span>Follow<span class="h"> @jonin.cards</span></span></a><a class="sell" href="https://sell.jonin.cards">Sell to Jonin</a><span class="acct" id="acct" data-auto></span><script src="/acct.js?v={acctv}"></script>'
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
<link rel="stylesheet" href="/pages.css?v={cssv}"><link rel="stylesheet" href="/themes.css?v=2"><link rel="stylesheet" href="/prem.css?v={premv}"><script src="/theme.js?v=7"></script>
{ld}
</head>
<body>
<header><div class="hw"><a class="logo" href="/" aria-label="Jonin home"><span class="jc" aria-hidden="true"><i></i><i><b>J</b></i></span><span aria-hidden="true">ONIN</span></a>
<nav><a href="/">Cards</a><a href="/#sets">Sets</a><a href="/characters/">Characters</a><a href="/lists/">Lists</a><a href="/news/">News</a><a href="/articles/">Articles</a><div class="pn"><a class="pnb" href="/club/"><svg class="lk" viewBox="0 0 14 17" aria-hidden="true"><defs><linearGradient id="lkn" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#FFE99A"/><stop offset=".45" stop-color="#F2C14E"/><stop offset="1" stop-color="#B07A1C"/></linearGradient></defs><g class="lift"><path class="sh" d="M4 8.5V5.5a3 3 0 0 1 6 0v3" fill="none" stroke="#E0B045" stroke-width="2.1" stroke-linecap="round"/></g><g class="bd"><rect x="1" y="8" width="12" height="9" rx="2.2" fill="url(#lkn)" stroke="#8C5F14" stroke-width=".6"/><circle cx="7" cy="11.7" r="1.35" fill="#5C3D0A"/><rect x="6.4" y="12" width="1.2" height="2.6" rx=".55" fill="#5C3D0A"/></g></svg>Jonin Club</a><div class="pdd"><div class="scr"><i class="rod"></i><div class="paper"><div class="in"><div class="pad"><h4>What Jonin Club unlocks</h4><ul><li>Exact prices by edition, foil and grade</li><li>Every sold listing, linked to the sale</li><li>Price estimates and sort by market value</li><li>Alerts for the cards you&#39;re hunting</li><li>Alt Art /20 sniper: a ping the moment a limited alt art is listed</li><li>Buy and sell posts from the Naruto CCG marketplaces</li><li>Your collection value, a spreadsheet export and a Jonin Club badge</li></ul><a class="go" href="/club/">See Jonin Club →</a></div></div></div><i class="rod"></i></div></div></div></nav>{igh}</div></header>
<main>
'''
FOOT = '''</main>
<footer>{igf}Jonin is a fan-made database for the original Bandai Naruto Collectible Card Game (2006–2013). Not affiliated with Bandai, Shueisha or Masashi Kishimoto. Some eBay links are affiliate links: Jonin may earn a small commission at no cost to you. <a href="/privacy/">Privacy</a> · <a href="/terms/">Terms</a></footer>
<script src="/feedback.js?v={fbv}" defer></script>
</body></html>
'''.replace('{igf}', IG_FOOT)


def newbie(where):
    """'New to Jonin?' box for first-time visitors, who mostly land on card, character and set pages from Google.
    theme.js hides it for signed-in members. PLACEHOLDER copy for David to edit."""
    return (f'<aside class="newbie" data-newbie hidden><div><b>New to Jonin?</b> '
            'A free database of every card in the original Bandai Naruto CCG (2006–2013). '
            'Make a free account to track your collection and slabs, see your set completion and vote for the coolest cards.</div>'
            f'<p class="btns"><a class="primary" href="/#signup" data-jt="signup-click" data-jt-from="{where}">Sign up free</a>'
            '<a class="ghostbtn" href="/#sets">Browse every set</a></p></aside>\n')


def ld_json(obj):
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False).replace('</', '<\\/') + '</script>'


def crumbs(*items):
    """BreadcrumbList structured data: items are (name, url) pairs, last one is the page itself."""
    return {'@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': i + 1, 'name': n, 'item': u} for i, (n, u) in enumerate(items)]}


def money(v):
    return '$' + (f'{round(v):,}' if v >= 100 else (f'{v:.2f}'.removesuffix('.00')))


SETS_BY_ID = {}
BANDS = ['Under $10', '$10–50', '$50–200', '$200+']   # replaced by cards.json "bands" in main()


def price_block(c):
    """Free "Market price": one price band for the whole card. Exact prices by edition, foil and grade,
    and every sold listing, are Jonin Club only."""
    pb = c.get('pb')
    lock = (f'<a class="pxt" href="/club/?card={quote(c["s"] + ":" + c["n"])}&amp;name={quote(c["name"])}" '
            'aria-label="See exact prices and sold listings with Jonin Club">'
            '<div class="rows" aria-hidden="true"><div><span>1st Edition · Foil · PSA 9</span><b>$000.00</b></div><div><span>Unlimited · Raw · NM</span><b>$00.00</b></div><div><span>1st Edition · Raw · LP</span><b>$00.00</b></div></div><span class="cta"><span><svg class="lk" viewBox="0 0 14 17" aria-hidden="true"><defs><linearGradient id="lkt" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#FFE99A"/><stop offset=".45" stop-color="#F2C14E"/><stop offset="1" stop-color="#B07A1C"/></linearGradient></defs><g class="lift"><path class="sh" d="M4 8.5V5.5a3 3 0 0 1 6 0v3" fill="none" stroke="#E0B045" stroke-width="2.1" stroke-linecap="round"/></g><g class="bd"><rect x="1" y="8" width="12" height="9" rx="2.2" fill="url(#lkt)" stroke="#8C5F14" stroke-width=".6"/><circle cx="7" cy="11.7" r="1.35" fill="#5C3D0A"/><rect x="6.4" y="12" width="1.2" height="2.6" rx=".55" fill="#5C3D0A"/></g></svg>Exact prices &amp; sold listings</span><small>Every sale by edition, foil and grade</small></span>' '</a>')
    guide = '<p class="mt pgl"><a href="/price-guide/">Naruto CCG price guide →</a></p>'
    if pb is None or not 0 <= pb < len(BANDS):
        return f'<section class="px"><h3>Market price</h3>{lock}{guide}</section>'
    return (f'<section class="px"><h3>Market price<span>across all versions</span></h3>'
            f'<p class="band">{e(BANDS[pb])}</p>{lock}{guide}</section>')


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from settings import MOST_VALUABLE_CHARACTERS, MOST_VALUABLE_TOP, MOST_VALUABLE_MIN_CARDS, CHARACTER_EXTRA_NAMES
import articles_build as AB
import lists_build as LB
featured_in = lambda c: AB.featured_in(c)

NOTES = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'character_notes.json')
RANK = {'Alt Art /20': -1, 'Super Rare': 0, 'Promo': 1, 'Rare': 2, 'Uncommon': 3, 'Starter': 4, 'Common': 5}


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


def card_alt(c, s):
    """Image description for Google Images: name, number, set, rarity and year, e.g.
    'Kakashi Hatake N-011 Naruto CCG card, The Path to Hokage (Uncommon, Bandai 2006)'."""
    y = year(s.get('rel'))
    bits = ', '.join(x for x in (c.get('r') if c.get('r') not in (None, '', 'Unknown') else '', ('Bandai ' + y) if y else 'Bandai') if x)
    return f"{c['name']} {c['n']} Naruto CCG card, {s['name']} ({bits})"


def tile(c, s):
    img = (f'<img loading="lazy" src="{e(c["img"])}" alt="{e(card_alt(c, s))}" width="750" height="1050">'
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
    rar = ', '.join(f'{rc[r]} {r}{"s" if rc[r] > 1 and r not in ("Common", "Uncommon", "Alt Art /20") else ""}'
                    for r in sorted(rc, key=lambda r: RANK.get(r, 9)) if r != 'Unknown')
    title = f"{ch['name']} Naruto cards: all {n} Bandai Naruto CCG cards | Jonin"
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
    key = sorted([c for c in cs if c['r'] in ('Alt Art /20', 'Super Rare', 'Promo')],
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
{newbie('character')}<section class="votetop" id="vote-top" data-character="{ch['slug']}" data-name="{e(ch['label'])}"><h2>Coolest {e(ch['label'])} cards<span>Top 3, voted by collectors</span></h2>
<p class="mt vxp">Your first vote on {e(ch['label'])} earns scrolls. <a href="/missions/">See all missions</a></p><p class="vbar" id="vote-bar"></p><p class="vnote" id="vote-note"></p><div class="grid" id="vote-grid"></div><p class="vtoast" id="vote-toast" role="status" hidden></p></section>
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


_SLAB_TILES = None


def slab_tiles():
    """pipeline/slab_tiles.json: which sale photos were flattened (slab_tiles.py)."""
    global _SLAB_TILES
    if _SLAB_TILES is None:
        p = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'slab_tiles.json')
        _SLAB_TILES = json.load(open(p)) if os.path.isfile(p) else {}
    return _SLAB_TILES


def sale_photo(c):
    """Photo of the copy that set the card's top sale (its slab), when we have one. Slab photos where no
    slab could be cleanly cropped and flattened ('noslab'), or that David hasn't OK'd yet ('check'), aren't used,
    so lists stay uniform: the card scan shows instead."""
    t = c.get('top') or []
    ph = t[7] if len(t) > 7 and re.match(r'^https://', t[7] or '') else ''
    if ph and slab_tiles().get(ph.rsplit('/', 1)[-1], {}).get('status') in ('noslab', 'check'):
        return ''
    return ph


def mv_art(c, eager=False):
    """Most-valuable lists show the actual sold copy (the slab) when we have its photo, else the card scan."""
    load = 'eager' if eager else 'lazy'
    ph, ver = sale_photo(c), c['top'][2] if c.get('top') else ''
    if ph:
        return (f'<img class="slab" loading="{load}" src="{e(ph)}" alt="{e(c["name"])} {e(c["n"])} {e(ver)} Naruto card, the copy that sold" '
                f'width="600" height="1000">')
    if re.match(r'^https://', c.get('img') or ''):
        return f'<img loading="{load}" src="{e(c["img"])}" alt="{e(c["name"])} {e(c["n"])} Naruto CCG card" width="750" height="1050">'
    return f'<span class="noimg sm"><b>{e(c["n"])}</b></span>'


def recent_html(c):
    """Other recent sales of a top-list card (newest first), under its top sale."""
    rs = c.get('rs') or []
    if not rs:
        return ''
    li = ''.join(f'<li><b>{money(p)}</b><span>{e(v) or "—"}</span><span class="mt">{e(d)}{AB.sale_link(u, src)}</span></li>'
                 for p, v, d, u, src in rs)
    return f'<div class="mvrs"><h3>Recent sales</h3><ul>{li}</ul></div>'


def slab_ld(c, name_for):
    """ImageObject for Google Images: the photo of the copy that set the card's top sale."""
    ph = sale_photo(c)
    if not ph:
        return None
    t = c['top']
    price = f" for {money(t[4])}" if len(t) > 4 and t[4] else ''
    return {'@type': 'ImageObject', 'contentUrl': ph, 'url': ph, 'name': name_for,
            'caption': f"{c['name']} {c['n']} {t[2]} Naruto CCG card that sold{price}" + (f" on {t[3]}" if t[3] else ''),
            'creditText': 'Seller photo from the sold listing'}


def mv_badges(c, ranks, pops=None):
    """Card page "appears in" badges, each linking to its list: '#2 most valuable Sasuke card', '#1 most popular Gaara card'
    (collector votes), and articles the card is featured in. Plus the photo of the copy that set its top sale."""
    arts = AB.FEATURED.get(c['s'] + ':' + c['n']) or []
    if not ranks and not pops and not arts:
        return ''
    out = ''.join(f'<a class="mvbadge" href="/character/{ch["slug"]}/most-valuable/">🏆 #{r} most valuable {e(ch["label"])} card</a>'
                  for ch, r in ranks or [])
    out += ''.join((f'<a class="mvbadge" href="/most-popular/">⭐ #{r} most popular Naruto CCG card</a>' if ch is None else
                    f'<a class="mvbadge" href="/character/{ch["slug"]}/most-popular/">⭐ #{r} most popular {e(ch["label"])} card</a>')
                   for ch, r in pops or [])
    out += ''.join(f'<a class="mvbadge art" href="/articles/{sl}/">📰 {e(t)}</a>' for sl, t in arts)
    ph, t = sale_photo(c), c.get('top') or []
    if ph and len(t) > 4 and t[4]:
        out += (f'<figure class="soldslab"><img loading="lazy" src="{e(ph)}" alt="{e(c["name"])} {e(c["n"])} {e(t[2])} Naruto card that sold for {money(t[4])}" width="600" height="1000">'
                f'<figcaption>Its record sale: <b>{money(t[4])}</b> · {e(t[2])}{" · " + e(t[3]) if t[3] else ""}</figcaption></figure>')
    return f'<div class="mvbadges">{out}</div>'


def mv_page(ch, ranked, sets_by_id, mv_chars):
    url = f'{SITE}/character/{ch["slug"]}/most-valuable/'
    n = len(ranked)
    title = f"Most valuable {ch['name']} Naruto cards: top {n} by sale price | Jonin"
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
        img = mv_art(c, eager=i == 0)
        lock = f'/club/?card={quote(c["s"] + ":" + c["n"])}&amp;name={quote(c["name"])}'
        band = ('$' + f'{price:,.2f}'.removesuffix('.00')) if price else (e(BANDS[b]) if 0 <= b < len(BANDS) else '—')
        src = AB.sale_link(sale_url, c['top'][6] if len(c['top']) > 6 else '').removeprefix(' · ') if price else ''
        rows.append(
            f'<li class="mvrow"><span class="mvn">{i + 1}</span><a class="mvart" href="/card/{slug(c)}/">{img}</a>'
            f'<div class="mvinfo"><h2><a href="/card/{slug(c)}/">{e(c["name"])}</a></h2>'
            f'<p class="mt"><span class="stag">{sym_img(s)}{e(s["name"])}</span> · {e(c["n"])} · {e(c["r"])}</p>'
            f'<dl><dt>Top sale</dt><dd><b class="band">{band}</b></dd><dt>Version</dt><dd>{e(ver) or "—"}</dd>'
            f'<dt>Sold</dt><dd>{e(sold_on) or "—"}{" · " + src if src else ""}</dd></dl>'
            f'{recent_html(c)}'
            f'<a class="pxlock" href="{lock}"><span>🔒 Every sale of this card, by edition, foil and grade</span><b>Jonin Club →</b></a></div></li>')
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
    img = next((sale_photo(c) for c in ranked if sale_photo(c)), '') or next((c['img'] for c in ranked if re.match(r'^https://', c.get('img') or '')), SITE + '/og.png')
    ld = ld_json({'@context': 'https://schema.org', '@graph': [
        {'@type': 'ItemList', 'name': title, 'description': desc, 'url': url, 'numberOfItems': n,
         'itemListOrder': 'https://schema.org/ItemListOrderDescending',
         'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'name': f"{c['name']} {c['n']}",
                              'url': f'{SITE}/card/{slug(c)}/'} for i, c in enumerate(ranked)]},
        crumbs(('Naruto CCG cards', SITE + '/'), ('Characters', SITE + '/characters/'),
               (ch['name'], f'{SITE}/character/{ch["slug"]}/'), ('Most valuable', url))]
        + [x for x in (slab_ld(c, f"#{i + 1} most valuable {ch['name']} card: {c['name']} {c['n']}") for i, c in enumerate(ranked)) if x]})
    return HEAD.format(title=e(title), desc=e(desc), url=url, img=e(img), tw='summary_large_image', ld=ld) + body + FOOT


def mv_index(mv_chars, ranked, sets_by_id):
    """/most-valuable/: every character's most-valuable list on one page (a list of lists), for search."""
    url = f'{SITE}/most-valuable/'
    names = ', '.join(c['label'] for c in mv_chars)
    title = 'Most valuable Naruto cards: the most expensive Bandai Naruto CCG cards ever sold | Jonin'
    desc = (f'The most valuable and most expensive Naruto cards in the original Bandai Naruto CCG, ranked by highest recorded sale. '
            f'Top {MOST_VALUABLE_TOP} lists for {names}, updated as new sales come in.')

    def price(c):
        p = c['top'][4] if len(c['top']) > 4 else None
        return ('$' + f'{p:,.2f}'.removesuffix('.00')) if p else (e(BANDS[c['top'][1]]) if 0 <= c['top'][1] < len(BANDS) else '')

    def mini(c, i):
        img = mv_art(c)
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
            '<section class="sethead"><h1>Most valuable Naruto CCG cards</h1>\n'
            '<p class="lede">The most valuable and most expensive cards in the whole original Bandai Naruto card game (2006–2013), with one list per character, '
            'ranked by the highest price each card has sold for. Lists update on their own as new sales come in.</p></section>\n'
            + ''.join(blocks)
            + '\n<p class="mt" style="margin-top:22px">More characters are coming. <a href="/price-guide/">Naruto CCG price guide</a> · <a href="/characters/">Browse every character</a> · <a href="/most-popular/">Most popular cards</a> · <a href="/lists/">All card lists</a>.</p>\n')
    img = next((sale_photo(c) for ch in mv_chars for c in ranked[ch['slug']] if sale_photo(c)), '') or \
        next((c['img'] for ch in mv_chars for c in ranked[ch['slug']] if re.match(r'^https://', c.get('img') or '')), SITE + '/og.png')
    ld = ld_json({'@context': 'https://schema.org', '@graph': [
        {'@type': 'ItemList', 'name': title, 'description': desc, 'url': url, 'numberOfItems': len(mv_chars),
         'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'name': f"Most valuable {ch['name']} cards",
                              'url': f'{SITE}/character/{ch["slug"]}/most-valuable/'} for i, ch in enumerate(mv_chars)]},
        crumbs(('Naruto CCG cards', SITE + '/'), ('Lists', SITE + '/lists/'), ('Most valuable', url))]
        + [x for ch in mv_chars for i, c in enumerate(ranked[ch['slug']][:3])
           if (x := slab_ld(c, f"#{i + 1} most valuable {ch['name']} card: {c['name']} {c['n']}"))]})
    return HEAD.format(title=e(title), desc=e(desc), url=url, img=e(img), tw='summary_large_image', ld=ld) + body + FOOT


def price_guide(cards, sets, sets_by_id, mv_chars):
    """/price-guide/: every card with a recorded sale, grouped by its free price band (highest band first).
    Free-tier rules hold: only the band shows here; exact prices by edition, foil and grade stay Jonin Club only."""
    url = f'{SITE}/price-guide/'
    priced = [c for c in cards if c.get('pb') is not None and 0 <= c['pb'] < len(BANDS)]
    order = lambda c: (c['top'][0] if c.get('top') else 10 ** 6, RANK.get(c['r'], 9))
    n = len(priced)
    title = 'Naruto CCG price guide: Bandai Naruto card values from real sales | Jonin'
    desc = (f'Price guide for the original Bandai Naruto CCG (2006–2013): {n} cards priced from real sold listings, '
            'grouped by value. What makes a Naruto card valuable, and the most expensive cards ever sold.')
    blocks = []
    for b in range(len(BANDS) - 1, -1, -1):
        cs = sorted([c for c in priced if c['pb'] == b], key=order)
        if cs:
            blocks.append(f'<section class="cgroup" id="band-{b}"><h2>{e(BANDS[b])}<span>{len(cs)} card{"s" if len(cs) != 1 else ""}</span></h2>'
                          f'<div class="grid">{"".join(tile(c, sets_by_id[c["s"]]) for c in cs)}</div></section>')
    jump = ''.join(f'<a class="chip" href="#band-{b}">{e(BANDS[b])}</a>' for b in range(len(BANDS) - 1, -1, -1)
                   if any(c['pb'] == b for c in priced))
    mv = ''.join(f'<a class="chip" href="/character/{o["slug"]}/most-valuable/"><img src="/chars/{o["slug"]}.webp" alt="" width="24" height="24" loading="lazy">{e(o["label"])}</a>'
                 for o in mv_chars)
    setchips = ''.join(f'<a class="chip" href="/set/{set_slug(x)}/">{sym_img(x)}{e(x["name"])}</a>' for x in sets)
    body = f'''<nav class="crumb"><a href="/">All cards</a> › <a href="/lists/">Lists</a> › Price guide</nav>
<section class="sethead"><h1>Naruto CCG price guide</h1>
<p class="lede">What original Bandai Naruto CCG cards (2006–2013) are worth, from real sold listings. Every sale is checked by hand before it counts. {n} cards have a recorded sale so far, and the guide updates on its own as new sales come in.</p>
<p class="mt">Each card's price range is based on its highest recorded sale across every version. <a href="/club/">Jonin Club</a> shows exact prices by edition, foil and grade, with every sold listing.</p>
<div class="chips">{jump}</div></section>
<section class="mvlistcard"><h2>What makes a Naruto CCG card valuable</h2>
<p><b>Rarity.</b> Look for the dots after the copyright line: none is Common, one Uncommon, two Rare and three Super Rare. Super Rares and promos are the cards most collectors chase.</p>
<p><b>Edition.</b> The same card can be 1st Edition or Unlimited. Check the card page for which editions each card was printed in.</p>
<p><b>Foil.</b> Many cards came in more than one finish: flat foil, diamond, wavy, spiral or prism. The same card can sell for very different prices depending on its foil.</p>
<p><b>Grade and condition.</b> Graded copies, especially PSA 10s, can sell for many times the price of a raw copy.</p></section>
{"".join(blocks)}
{f'<section class="others"><h2>Most valuable cards by character</h2><div class="chips">{mv}</div><p class="btns" style="margin-top:12px"><a class="primary" href="/most-valuable/">💰 Most valuable Naruto cards</a></p></section>' if mv else ''}
<section class="others"><h2>Card lists by set</h2><div class="chips">{setchips}</div></section>
'''
    img = next((c['img'] for c in sorted(priced, key=order) if re.match(r'^https://', c.get('img') or '')), SITE + '/og.png')
    ld = ld_json({'@context': 'https://schema.org', '@graph': [
        {'@type': 'CollectionPage', 'name': title, 'description': desc, 'url': url},
        crumbs(('Naruto CCG cards', SITE + '/'), ('Lists', SITE + '/lists/'), ('Price guide', url))]})
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


def missions_page(chars):
    """/missions/: ways to earn scrolls and rank up. Static shell; /missions.js fills in the signed-in member's progress
    and the scroll amounts from Supabase (xp_rules, xp_ranks), so changing the rules there updates this page."""
    url = f'{SITE}/missions/'
    title = 'Missions: earn scrolls and rank up | Jonin'
    desc = 'Earn scrolls on Jonin by voting for the coolest Naruto CCG cards for every character and sending feedback we use. Rank up from Academy Student to Kage.'
    chips = ''.join(f'<a class="chip mch" data-ch="{c["slug"]}" href="/character/{c["slug"]}/#vote-top"><img src="/chars/{c["slug"]}.webp" alt="" width="24" height="24" loading="lazy">{e(c["label"])}<i class="mok" aria-hidden="true">✓</i></a>' for c in chars)
    body = f'''<nav class="crumb"><a href="/">All cards</a> › Missions</nav>
<section class="sethead"><h1>Missions</h1>
<p class="lede">Earn scrolls and rank up from Academy Student to Kage. Your rank shows on your profile next to your name.</p>
<p class="btns"><a class="ghostbtn" href="/leaderboard/">📜 See the leaderboard</a></p></section>
<section class="mhero" id="mhero"><p class="mt">Loading your rank…</p></section>
<section class="mlist">
<article class="mcard" id="m-inv"><div class="mtop"><h2>Invite friends</h2><span class="mxp" data-xp="invite_signup">+📜</span></div>
<p class="mt">Share your invite link. When a friend signs up through it and adds a card to their collection or casts a vote, you earn scrolls.</p>
<div class="minv"><p class="mt" style="margin:0">Sign in to get your invite link.</p></div></article>
<article class="mcard" id="m-vote"><div class="mtop"><h2>Vote for every character's coolest cards</h2><span class="mxp" data-xp="vote_character">+📜</span></div>
<p class="mt">Open a character and vote for up to 3 of their best cards. Your first vote on each character earns scrolls, once per character. Moving a vote later keeps your scrolls.</p>
<div class="mprog"><span class="mbar"><i style="width:0%"></i></span><b class="mcount">0 / {len(chars)}</b></div>
<div class="chips mchips">{chips}</div></article>
<article class="mcard" id="m-cards"><div class="mtop"><h2>Log 100 cards</h2><span class="mxp" data-xp="cards_100">+📜</span></div>
<p class="mt">Add 100 different cards to your collection (haves and slabs count). It's a one-time thank-you for helping build the database.</p>
<div class="mprog"><span class="mbar"><i style="width:0%"></i></span><b class="mcount">0 / 100</b></div></article>
<article class="mcard" id="m-fb"><div class="mtop"><h2>Send feedback we use</h2><span class="mxp" data-xp="feedback_accepted">+📜</span></div>
<p class="mt">Spotted a wrong card, a missing foil or a bug? Send a note from any page. Every note that leads to a fix earns scrolls. Sign in first, or leave the email you signed up with, so it's credited to you.</p>
<div class="mprog"><b class="mfb">0 notes used so far</b></div>
<p class="btns"><button type="button" class="primary" data-fb data-fbname="Missions page">💬 Send feedback</button></p></article>
</section>
<section class="mcard mranks"><h2>Ranks</h2><ol id="mladder"></ol></section>
<script src="/missions.js?v={file_version('missions.js')}" defer></script>
'''
    ld = ld_json({'@context': 'https://schema.org', '@graph': [
        {'@type': 'WebPage', 'name': title, 'description': desc, 'url': url},
        crumbs(('Naruto CCG cards', SITE + '/'), ('Missions', url))]})
    return HEAD.format(title=e(title), desc=e(desc), url=url, img=e(SITE + '/og.png'), tw='summary_large_image', ld=ld) + body + FOOT


def leaderboard_page():
    """/leaderboard/: members ranked by scrolls. Static shell; /leaderboard.js reads scroll_leaderboard() from Supabase
    (db/029_scroll_leaderboard.sql). Rules (David approved 2026-11-26): top 25, members with 1+ scroll, ties share a place."""
    url = f'{SITE}/leaderboard/'
    title = 'Scrolls leaderboard: top Jonin members | Jonin'
    desc = 'The Jonin members with the most scrolls. Earn scrolls by voting for the coolest Naruto CCG cards, inviting friends and sending feedback, and climb from Academy Student to Kage.'
    body = f'''<nav class="crumb"><a href="/">All cards</a> › <a href="/missions/">Missions</a> › Leaderboard</nav>
<section class="sethead"><h1>📜 Scrolls leaderboard</h1>
<p class="lede">The members who have earned the most scrolls. <a href="/missions/">Do missions</a> to climb the board.</p></section>
<section class="lbx" id="lbx"><p class="lbe mt">Loading the leaderboard…</p></section>
<p class="mt" id="lbfoot"></p>
<script src="/leaderboard.js?v={file_version('leaderboard.js')}" defer></script>
'''
    ld = ld_json({'@context': 'https://schema.org', '@graph': [
        {'@type': 'WebPage', 'name': title, 'description': desc, 'url': url},
        crumbs(('Naruto CCG cards', SITE + '/'), ('Missions', SITE + '/missions/'), ('Leaderboard', url))]})
    return HEAD.format(title=e(title), desc=e(desc), url=url, img=e(SITE + '/og.png'), tw='summary_large_image', ld=ld) + body + FOOT


def giveaway_page():
    """/giveaway/: the current Instagram giveaway. Static shell; /giveaway.js reads the giveaway (prize, dates) from the
    Supabase giveaways table and checks the signed-in member's bonus entries (my_giveaway_status).
    Entry rules (David, 2026-11-26): Instagram entry (follow, like, tag a friend; each tag 1 entry, max 3) plus a
    site bonus for a free account with a linked Instagram and a card vote. Amounts live in the giveaways row."""
    url = f'{SITE}/giveaway/'
    title = 'Giveaway: win a sealed Naruto CCG pack | Jonin'
    desc = 'Win a sealed Bandai Naruto CCG pack from Jonin. Enter on Instagram, then link your Instagram on a free jonin.cards account and vote for a card for bonus entries.'
    body = '''<nav class="crumb"><a href="/">All cards</a> › Giveaway</nav>
<section class="sethead"><h1 id="gtitle">Win a sealed Naruto CCG pack</h1>
<p class="lede" id="gwhen">Free to enter. US only, 18+.</p></section>
<section class="mcard ghero" id="gprize"><p class="mt">Loading the giveaway…</p></section>
<section class="mlist">
<article class="mcard"><div class="mtop"><h2>1 · Enter on Instagram</h2><span class="mxp">Up to 3 entries</span></div>
<ol class="gsteps"><li>Follow <a href="https://www.instagram.com/jonin.cards/" target="_blank" rel="noopener">@jonin.cards</a></li><li>Like the giveaway post</li><li>Tag a friend who collects Naruto cards in the comments. Each friend you tag is 1 entry, up to <b data-g="max_tag_entries">3</b>.</li></ol>
<p class="btns"><a class="primary" href="https://www.instagram.com/jonin.cards/" target="_blank" rel="noopener">Open @jonin.cards</a></p></article>
<article class="mcard" id="gbonus"><div class="mtop"><h2>2 · Get bonus entries on jonin.cards</h2><span class="mxp">+<b data-g="bonus_entries">5</b> entries</span></div>
<p class="mt">Make a free account, add your Instagram handle and vote for your favorite card on any character. That's how we match your bonus to your Instagram entry.</p>
<div class="gchk" id="gchk"><p class="mt" style="margin:0">Checking your account…</p></div></article>
</section>
<section class="mcard grules"><h2>Rules</h2>
<ul class="mt"><li>Free to enter. No purchase necessary.</li><li>Open to US residents 18 and older.</li><li>Runs <span id="grun">for 7 days</span>. The winner is drawn at random, live on our Instagram stories, and announced on @jonin.cards.</li><li>To win you must follow @jonin.cards and have entered on the giveaway post. Bonus entries only count if the Instagram handle on your jonin.cards account matches your entry.</li><li>The winner is messaged on Instagram and has 72 hours to reply, or a new winner is drawn.</li><li>One prize. Shipped free within the US.</li><li>This giveaway is not sponsored, endorsed or run by Instagram or Meta. Not affiliated with Bandai.</li></ul></section>
<script src="/giveaway.js?v=''' + file_version('giveaway.js') + '''" defer></script>
'''
    ld = ld_json({'@context': 'https://schema.org', '@graph': [
        {'@type': 'WebPage', 'name': title, 'description': desc, 'url': url},
        crumbs(('Naruto CCG cards', SITE + '/'), ('Giveaway', url))]})
    return HEAD.format(title=e(title), desc=e(desc), url=url, img=e(SITE + '/og.png'), tw='summary_large_image', ld=ld) + body + FOOT


def file_version(name):
    return hashlib.sha1(open(os.path.join(ROOT, name), 'rb').read()).hexdigest()[:8]


def css_version():
    # Changes whenever pages.css changes, so browsers and Cloudflare never serve a stale copy.
    return hashlib.sha1(open(os.path.join(ROOT, 'pages.css'), 'rb').read()).hexdigest()[:8]


def related_rows(c, s, set_cards, char_lists, chars_by_name, skip=()):
    """'More <character> cards' and 'More from <set>' rows under a card page, so one card leads to the next.
    Best-selling cards first, then rarity; 6 per row."""
    skip_ids = {id(x) for x in skip}
    pick = lambda xs: sorted([x for x in xs if x is not c and id(x) not in skip_ids], key=lambda x: (x['top'][0] if x.get('top') else 10 ** 6, RANK.get(x['r'], 9), x['n']))[:6]
    out, seen = [], set()
    for x in re.split(r'\s*&\s*', c['name']):
        ch = char_of(x, chars_by_name)
        if not ch or ch['slug'] in seen:
            continue
        seen.add(ch['slug'])
        cs = pick(char_lists.get(ch['slug'], []))
        if cs:
            out.append(f'<section class="cgroup related"><h2><a href="/character/{ch["slug"]}/">More {e(ch["label"])} cards</a>'
                       f'<span>{len(char_lists[ch["slug"]])} in all</span></h2><div class="grid">{"".join(tile(x, SETS_BY_ID[x["s"]]) for x in cs)}</div>'
                       f'<p class="btns"><a class="ghostbtn" href="/character/{ch["slug"]}/">All {e(ch["label"])} cards →</a></p></section>')
    cs = pick(set_cards)
    if cs:
        out.append(f'<section class="cgroup related"><h2><a href="/set/{set_slug(s)}/">More from {e(s["name"])}</a><span>{len(set_cards)} cards</span></h2>'
                   f'<div class="grid">{"".join(tile(x, s) for x in cs)}</div>'
                   f'<p class="btns"><a class="ghostbtn" href="/set/{set_slug(s)}/">Full {e(s["name"])} card list →</a></p></section>')
    return '\n'.join(out)


def quick_links(c, s, set_cards, char_lists, chars_by_name):
    """Right under the card name: one-tap links to the character's and set's pages, so the next click is on the first screen."""
    out, seen = [], set()
    for x in re.split(r'\s*&\s*', c['name']):
        ch = char_of(x, chars_by_name)
        if ch and ch['slug'] not in seen and char_lists.get(ch['slug']):
            seen.add(ch['slug'])
            out.append(f'<a class="qlink" href="/character/{ch["slug"]}/" data-jt="quick-link" data-jt-to="character">'
                       f'<img src="/chars/{ch["slug"]}.webp" alt="" width="22" height="22">All {len(char_lists[ch["slug"]])} {e(ch["label"])} cards →</a>')
    out.append(f'<a class="qlink" href="/set/{set_slug(s)}/" data-jt="quick-link" data-jt-to="set">{sym_img(s)}{e(s["name"])}: {len(set_cards)} cards →</a>')
    return f'<p class="qlinks">{"".join(out)}</p>'


def near_top(c, s, set_cards, char_lists, chars_by_name):
    """A small 4-card row near the top of the card page (the first character's best cards, or the set's for jutsu and other
    cards with no character). Returns (html, cards shown) so the bottom rows don't repeat them."""
    for x in re.split(r'\s*&\s*', c['name']):
        ch = char_of(x, chars_by_name)
        if ch and char_lists.get(ch['slug']):
            pool, title, href = char_lists[ch['slug']], f'More {e(ch["label"])} cards', f'/character/{ch["slug"]}/'
            break
    else:
        pool, title, href = set_cards, f'More from {e(s["name"])}', f'/set/{set_slug(s)}/'
    cs = sorted([x for x in pool if x is not c], key=lambda x: (x['top'][0] if x.get('top') else 10 ** 6, RANK.get(x['r'], 9), x['n']))[:4]
    if not cs:
        return '', []
    return (f'<section class="neartop"><h3><a href="{href}" data-jt="near-top" data-jt-to="all">{title} →</a></h3><div class="ntgrid">'
            + ''.join(f'<a href="/card/{slug(x)}/" data-jt="near-top" data-jt-to="card">'
                      + (f'<img loading="lazy" src="{e(x["img"])}" alt="{e(card_alt(x, SETS_BY_ID[x["s"]]))}" width="750" height="1050">'
                         if re.match(r'^https://', x.get('img') or '') else f'<span class="noimg sm"><b>{e(x["n"])}</b></span>')
                      + f'<span>{e(x["name"])}</span></a>' for x in cs) + '</div></section>\n'), cs


def card_page(c, s, prev, nxt, chars_by_name=None, set_cards=(), char_lists=None, ranks=None, pops=None):
    img = c.get('img') if re.match(r'^https://', c.get('img') or '') else ''
    url = f'{SITE}/card/{slug(c)}/'
    eds = [x for x in (c.get('ed') or []) if x]
    title = f"{c['name']} {c['n']} · {s['name']} · Naruto CCG card value | Jonin"
    desc = (f"{c['name']} ({c['n']}) from {s['name']}"
            f"{' (' + s['rel'] + ')' if s.get('rel') else ''}: {c['r']} {c['t']} card in the Bandai Naruto CCG. "
            f"Printings: {', '.join(c.get('v') or [])}{'; ' + ' and '.join(eds) if eds else ''}."
            + (f" Market price: {BANDS[c['pb']]}." if c.get('pb') is not None and 0 <= c['pb'] < len(BANDS) else '')
            + " eBay sold prices for raw and PSA graded copies.")
    psa = (f'<a href="{e(PSA_POP + PSA[c["s"]])}" target="_blank" rel="noopener">PSA pop report · {e(set_label(s))}</a>'
           if c['s'] in PSA else '<a href="https://www.psacard.com/pop/tcg-cards" target="_blank" rel="noopener">PSA pop report</a>')
    art = (f'<img src="{e(img)}" alt="{e(card_alt(c, s))}" width="750" height="1050">'
           if img else f'<div class="noimg"><b>{e(c["n"])}</b><span>{e(c["t"])} · scan coming soon</span></div>')
    rows = [('Set', f'<a class="stag" href="/set/{set_slug(s)}/">{sym_img(s)}{e(s["name"])}</a> · {e(set_label(s))}{" · " + e(s["rel"]) if s.get("rel") else ""}'),
            ('Number', e(c['n'])), ('Rarity', e(c['r'])), ('Type', e(c['t'])),
            *[(k, e(str(c[f]))) for k, f in (('Element', 'el'), ('Turn cost', 'tc'), ('Hand cost', 'hc'), ('Village', 'vil'))
              if c.get(f) not in (None, '')],   # approved scan details (cards.json el/tc/hc/vil), same as the old popup showed
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
         'description': desc, 'url': url, **({'image': [x for x in (img, sale_photo(c) if ranks else '') if x]} if img or (ranks and sale_photo(c)) else {}),
         'isPartOf': {'@type': 'CreativeWork', 'name': f"Naruto CCG · {s['name']}", 'url': f'{SITE}/set/{set_slug(s)}/'}},
        crumbs(('Naruto CCG cards', SITE + '/'), (s['name'], f'{SITE}/set/{set_slug(s)}/'), (f"{c['name']} {c['n']}", url))]})
    nav = ''.join([
        f'<a class="pn" href="/card/{slug(prev)}/" rel="prev">‹ {e(prev["n"])} {e(prev["name"])}</a>' if prev else '<span></span>',
        f'<a class="pn" href="/card/{slug(nxt)}/" rel="next">{e(nxt["n"])} {e(nxt["name"])} ›</a>' if nxt else '<span></span>'])
    nt_html, nt_cards = near_top(c, s, set_cards, char_lists or {}, chars_by_name or {})
    body = f'''<nav class="crumb"><a href="/">All cards</a> › <a href="/set/{set_slug(s)}/">{e(s["name"])}</a> › {e(c["n"])}</nav>
<article class="cardpage">
<div class="side"><div class="art" data-card="{e(c["s"] + ":" + c["n"])}" data-alt="{e(card_alt(c, s))}">{art}</div><script src="/card-art.js?v={file_version('card-art.js')}" defer></script>
<section class="coll" id="coll" data-card="{e(c["s"] + ":" + c["n"])}" data-name="{e(c["name"] + " · " + c["n"])}"><h4>Your collection</h4><p class="mt">Mark what you have and want, add slabs. No account needed to start.</p><button type="button" class="primary" data-collgo data-jt="track-click">＋ Add to your collection</button></section><script src="/card-coll.js?v={file_version('card-coll.js')}" defer></script></div>
<div class="info">
<div class="cnav">{f'<a href="/card/{slug(prev)}/" aria-label="Previous card: {e(prev["name"])} {e(prev["n"])}" data-key="prev">‹</a>' if prev else ''}{f'<a href="/card/{slug(nxt)}/" aria-label="Next card: {e(nxt["name"])} {e(nxt["n"])}" data-key="next">›</a>' if nxt else ''}</div>
<h1>{e(c["name"])}</h1>
<p class="mt">{e(s["name"])} · {e(c["n"])} · {e(c["r"])}</p>
{quick_links(c, s, set_cards, char_lists or {}, chars_by_name or {})}
{mv_badges(c, ranks, pops)}<dl>{''.join(f'<dt>{k}</dt><dd>{v}</dd>' for k, v in rows)}</dl>
{('<script src="/card-votes.js?v=' + file_version('card-votes.js') + '" defer></script>') if cl else ''}
<div class="links">
<a href="{e(sold(card_q(c), 'slab'))}" target="_blank" rel="sponsored noopener" data-jt="ebay-click" data-jt-kind="slab">eBay sold · slabs</a>
<a href="{e(sold(card_q(c), 'raw'))}" target="_blank" rel="sponsored noopener" data-jt="ebay-click" data-jt-kind="raw">eBay sold · raw</a>
{psa}
<a href="/club/?card={quote(c['s'] + ':' + c['n'])}&amp;name={quote(c['name'])}" data-jt="alerts-click">🔔 Alerts for this card</a>
</div>
<button type="button" class="fbcard" data-fb data-fbcard>✎ Something wrong or missing on this card? Tell us</button>
{newbie('card')}
</div>
</article>
<div class="market">{price_block(c)}</div>
{nt_html}
<nav class="prevnext">{nav}</nav>
{related_rows(c, s, set_cards, char_lists or {}, chars_by_name or {}, nt_cards)}
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
        + (f'<img loading="lazy" src="{e(c["img"])}" alt="{e(card_alt(c, s))}" width="750" height="1050">'
           if re.match(r'^https://', c.get('img') or '') else f'<span class="noimg sm"><b>{e(c["n"])}</b></span>')
        + f'<span class="tt">{e(c["name"])}</span><span class="tn stag">{sym_img(s)}{e(s["name"])}</span><span class="tn">{e(c["n"])}</span></a>' for c in cards)
    sym = f'<img class="sym" src="{e(s["symbol"])}?v={SYMV}" alt="">' if s.get('symbol') else ''
    body = f'''<nav class="crumb"><a href="/">All cards</a> › <a href="/#sets">Sets</a> › {e(s["name"])}</nav>
<section class="sethead"><h1>{sym}{e(s["name"])}</h1>
<dl class="inline">{''.join(f'<dt>{k}</dt><dd>{v}</dd>' for k, v in facts)}</dl>
{f'<p class="note">{e(s["notes"])}</p>' if s.get('notes') else ''}
<p><a class="primary" href="/#set={quote(s['id'])}">Browse and filter this set</a></p></section>
{newbie('set')}<section class="spx" id="set-progress" data-set="{e(s['id'])}" data-total="{len(cards)}" data-prints="{sum(max(1, len(c.get('v') or [])) * max(1, len([x for x in (c.get('ed') or []) if x])) for c in cards)}" aria-live="polite"></section>
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
    global HEAD, FOOT
    FOOT = FOOT.replace('{fbv}', file_version('feedback.js'))
    HEAD = HEAD.replace('{igh}', IG_HEADER).replace('{cssv}', css_version()).replace('{premv}', file_version('prem.css')).replace('{fbv}', file_version('feedback.js')).replace('{acctv}', file_version('acct.js'))
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
    global SETS_BY_ID
    SETS_BY_ID = {x['id']: x for x in sets}
    char_lists = {ch['slug']: char_cards(ch, d['cards']) for ch in chars}
    ranked = {}
    for ch in chars:
        if MOST_VALUABLE_CHARACTERS == 'all' or ch['slug'] in MOST_VALUABLE_CHARACTERS:
            cs = char_cards(ch, d['cards'])
            ranked[ch['slug']] = most_valuable(cs)
            ch['mv'] = bool(ranked[ch['slug']]) and mv_live(cs)
    mv_chars = [ch for ch in chars if ch.get('mv')]
    mv_ranks = {}    # card key -> [(character, rank)] for the card-page badges
    for ch in mv_chars:
        for i, c in enumerate(ranked[ch['slug']]):
            mv_ranks.setdefault(c['s'] + ':' + c['n'], []).append((ch, i + 1))
    pop_ranks = {}   # card key -> [(character or None for overall, rank)] from collector votes
    votes = LB.load_votes()
    for ch in chars:
        for i, (c, _n) in enumerate(LB.popular_ranked(votes.get(ch['slug']), cards_by_key)):
            pop_ranks.setdefault(c['s'] + ':' + c['n'], []).append((ch, i + 1))
    for i, (c, _n) in enumerate(LB.popular_ranked(votes.get('_all'), cards_by_key, 10)):
        pop_ranks.setdefault(c['s'] + ':' + c['n'], []).insert(0, (None, i + 1))
    changed, keep_c, keep_s = 0, set(), set()
    for s in sets:
        cs = by_set[s['id']]
        for i, c in enumerate(cs):
            keep_c.add(slug(c))
            changed += write(os.path.join(ROOT, 'card', slug(c), 'index.html'),
                             card_page(c, s, cs[i - 1] if i else None, cs[i + 1] if i + 1 < len(cs) else None, chars_by_name, cs, char_lists,
                                       mv_ranks.get(c['s'] + ':' + c['n']), pop_ranks.get(c['s'] + ':' + c['n'])))
        keep_s.add(set_slug(s))
        changed += write(os.path.join(ROOT, 'set', set_slug(s), 'index.html'), set_page(s, cs))
    sets_by_id = {x['id']: x for x in sets}
    notes = json.load(open(NOTES, encoding='utf-8')) if os.path.exists(NOTES) else {}
    keep_ch, counts = set(), {}
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
    changed += write(os.path.join(ROOT, 'missions', 'index.html'), missions_page(chars))
    changed += write(os.path.join(ROOT, 'giveaway', 'index.html'), giveaway_page())
    changed += write(os.path.join(ROOT, 'leaderboard', 'index.html'), leaderboard_page())
    # Character list for the /welcome/ setup page (same order as the homepage sidebar).
    changed += write(os.path.join(ROOT, 'chars.json'), json.dumps([{'slug': ch['slug'], 'label': ch['label'], 'cards': counts[ch['slug']]} for ch in chars], ensure_ascii=False) + '\n')
    mvidx = os.path.join(ROOT, 'most-valuable')
    if mv_chars:
        changed += write(os.path.join(mvidx, 'index.html'), mv_index(mv_chars, ranked, sets_by_id))
    elif os.path.isdir(mvidx):
        shutil.rmtree(mvidx)
    changed += write(os.path.join(ROOT, 'price-guide', 'index.html'), price_guide(d['cards'], sets, sets_by_id, mv_chars))
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
    urls = [SITE + '/'] + ([SITE + '/news/'] + [f"{SITE}/news/{a['slug']}/" for a in arts] if arts else []) + [SITE + '/characters/', SITE + '/missions/', SITE + '/leaderboard/', SITE + '/giveaway/', SITE + '/articles/'] + [f'{SITE}/articles/{a["slug"]}/' for a in articles if not a['draft']] + [f'{SITE}/character/{ch["slug"]}/' for ch in chars] + \
           list_urls + [SITE + '/price-guide/'] + ([SITE + '/most-valuable/'] if mv_chars else []) + [f'{SITE}/character/{ch["slug"]}/most-valuable/' for ch in mv_chars] + \
           [f'{SITE}/set/{set_slug(s)}/' for s in sets] + \
           [f'{SITE}/card/{slug(c)}/' for s in sets for c in by_set[s['id']]]
    page_imgs = {f'{SITE}/card/{slug(c)}/': [c['img']] for c in d['cards'] if re.match(r'^https://jonin\.cards/', c.get('img') or '')}
    for k, rs in mv_ranks.items():          # slab photos: on the card's page and on every list it's in
        ph = sale_photo(cards_by_key[k])
        if ph:
            page_imgs.setdefault(f'{SITE}/card/{slug(cards_by_key[k])}/', []).append(ph)
            for ch, r in rs:
                page_imgs.setdefault(f'{SITE}/character/{ch["slug"]}/most-valuable/', []).append(ph)
                if r <= 3:
                    page_imgs.setdefault(f'{SITE}/most-valuable/', []).append(ph)
    img_tag = lambda u: ''.join(f'<image:image><image:loc>{e(x)}</image:loc></image:image>' for x in dict.fromkeys(page_imgs.get(u, [])))
    lm = lastmods(urls)
    changed += write(LASTMOD, json.dumps(lm, indent=0, sort_keys=True) + '\n')
    changed += write(os.path.join(ROOT, 'sitemap.xml'),
                     '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n'
                     + ''.join(f'<url><loc>{e(u)}</loc><lastmod>{lm[u][1]}</lastmod>{img_tag(u)}</url>\n' for u in urls) + '</urlset>\n')
    changed += write(os.path.join(ROOT, 'robots.txt'),
                     f'User-agent: *\nAllow: /\nDisallow: /admin/\n\nSitemap: {SITE}/sitemap.xml\n')
    print(f'{len(keep_c)} card pages, {len(keep_s)} set pages, {changed} files written, {removed} stale folders removed')


if __name__ == '__main__':
    sys.exit(main())
