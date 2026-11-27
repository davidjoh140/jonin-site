"""Search pages for "what are my Naruto cards worth" and "what is my 2009 Sasuke worth":
/what-are-my-naruto-cards-worth/ (guide) and /year/<yyyy>/ (every set, top cards and characters from one year).
Free-tier rules hold: only rounded price ranges (cards.json "pr") and bands show; exact prices stay Jonin Club only."""
import re

B = None   # build_pages module, set by setup()
GUIDE_SLUG = 'what-are-my-naruto-cards-worth'
YEAR_CHARS = 8          # PLACEHOLDER: characters with their own section on each year page (homepage order)
YEAR_TOP = 12           # PLACEHOLDER: top cards shown per year
YEAR_CHAR_CARDS = 8     # PLACEHOLDER: cards shown per character section


def setup(mod):
    global B
    B = mod


def e(x):
    return B.e(x)


def top_order(c):
    return (c['top'][0] if c.get('top') else 10 ** 6, B.RANK.get(c['r'], 9))


def tile_px(c, s):
    """Card tile with its free price range under it."""
    t = B.tile(c, s)
    rt = B.range_text(c)
    if not rt and c.get('pb') is not None and 0 <= c['pb'] < len(B.BANDS):
        rt = B.BANDS[c['pb']]
    return t[:-4] + (f'<span class="tn tpx">{e(rt)}</span>' if rt else '') + '</a>'


def span_of(cs):
    """Low and high free price across a group of cards, or None."""
    prs = [c['pr'] for c in cs if c.get('pr')]
    return (min(p[0] for p in prs), max(p[1] for p in prs)) if prs else None


def money_span(sp):
    a, b = sp
    return f'about {B.money(a)}' if a == b else f'{B.money(a)}–{B.money(b)}'


def years_of(sets):
    """{year: [sets released that year]} in set order (Main sets, tournament packs, tins; promos have no single year)."""
    out = {}
    for s in sets:
        y = B.set_year(s)
        if y:
            out.setdefault(y, []).append(s)
    return dict(sorted(out.items()))


def year_chips(years, current=None):
    return ''.join(f'<a class="chip{" on" if y == current else ""}" href="/year/{y}/">{y}</a>' for y in years)


def faq_ld(qas):
    return {'@type': 'FAQPage', 'mainEntity': [
        {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': re.sub(r'<[^>]+>', '', a)}} for q, a in qas]}


def faq_html(qas):
    return ('<section class="mvlistcard faq"><h2>Questions</h2>'
            + ''.join(f'<h3>{e(q)}</h3><p>{a}</p>' for q, a in qas) + '</section>')


def year_page(y, ysets, cards, years, chars, sets_by_id):
    url = f'{B.SITE}/year/{y}/'
    ids = {s['id'] for s in ysets}
    cs = [c for c in cards if c['s'] in ids]
    priced = sorted([c for c in cs if c.get('pb') is not None], key=top_order)
    main = [s for s in ysets if s.get('kind') == 'Main']
    names = ', '.join(s['name'] for s in ysets)
    title = f'{y} Naruto CCG cards: values, sets and most valuable {y} Naruto cards | Jonin'
    desc = (f'Every Bandai Naruto CCG card released in {y}: {len(cs)} cards from {names}. '
            f'What {y} Naruto cards are worth, from real sales, and the most valuable {y} Naruto, Sasuke and Itachi cards.')
    sp = span_of(cs)
    lede = (f'Bandai released {len(ysets)} Naruto CCG product{"s" if len(ysets) != 1 else ""} in {y}'
            + (f', including {len(main)} main set{"s" if len(main) != 1 else ""}' if main and len(main) != len(ysets) else '')
            + f': {len(cs)} cards in all. '
            + (f'{len(priced)} of them have a recorded sale on Jonin, selling for {money_span(sp)} depending on the card, edition, foil and grade.'
               if sp else 'Prices fill in as sales are recorded.'))
    setrows = ''.join(f'<a class="chip" href="/set/{B.set_slug(s)}/">{B.sym_img(s)}{e(s["name"])}'
                      f'{" · " + e(s["rel"]) if s.get("rel") else ""}</a>' for s in ysets)
    top = (f'<section class="cgroup"><h2>Most valuable {y} Naruto cards<span>by highest recorded sale</span></h2>'
           f'<div class="grid">{"".join(tile_px(c, sets_by_id[c["s"]]) for c in priced[:YEAR_TOP])}</div></section>') if priced else ''
    sections, qas = [], []
    for ch in chars:
        if len(sections) >= YEAR_CHARS:
            break
        mine = sorted(B.char_cards(ch, cs), key=top_order)
        if not mine:
            continue
        csp = span_of(mine)
        sections.append(
            f'<section class="cgroup" id="{e(ch["slug"])}"><h2>{y} {e(ch["name"])} cards<span>{len(mine)} card{"s" if len(mine) != 1 else ""}</span></h2>'
            + (f'<p class="mt">Selling for {e(money_span(csp))} depending on the card, edition, foil and grade.</p>' if csp else '')
            + f'<div class="grid">{"".join(tile_px(c, sets_by_id[c["s"]]) for c in mine[:YEAR_CHAR_CARDS])}</div>'
            + f'<p class="mt"><a href="/character/{e(ch["slug"])}/">Every {e(ch["name"])} card →</a>'
            + (f' · <a href="/character/{e(ch["slug"])}/most-valuable/">Most valuable {e(ch["name"])} cards →</a>' if ch.get('mv') else '')
            + '</p></section>')
        if csp:
            best = next((c for c in mine if c.get('pr')), None)
            qas.append((f'What is my {y} {ch["label"]} card worth?',
                        f'It depends which card you have. Bandai printed {len(mine)} {e(ch["name"])} card{"s" if len(mine) != 1 else ""} in {y}, '
                        f'and the ones with recorded sales go for {e(money_span(csp))}, depending on the card, edition, foil and grade. '
                        + (f'The highest seller so far is <a href="/card/{B.slug(best)}/">{e(best["name"])} {e(best["n"])}</a> '
                           f'({e(B.range_text(best))}). ' if best else '')
                        + 'Find your exact card in the list above to see its price.'))
    qas.append((f'Are {y} Naruto cards worth anything?',
                f'Most commons and uncommons sell for a few dollars. Super Rares, promos and graded copies of popular characters '
                f'are where the value is. See <a href="/{GUIDE_SLUG}/">what your Naruto cards are worth</a> for how to check yours.'))
    body = f'''<nav class="crumb"><a href="/">All cards</a> › <a href="/{GUIDE_SLUG}/">Card values</a> › {y}</nav>
<section class="sethead"><h1>{y} Naruto CCG cards</h1>
<p class="lede">{e(lede)}</p>
<p class="mt"><a href="/club/">Jonin Club</a> shows exact prices by edition, foil and grade, with every sold listing.</p>
<div class="chips">{setrows}</div>
<div class="chips yrs">{year_chips(years, y)}</div></section>
{top}
{"".join(sections)}
{faq_html(qas)}
<section class="others"><h2>Naruto CCG cards by year</h2><div class="chips">{year_chips(years, y)}</div>
<p class="btns" style="margin-top:12px"><a class="primary" href="/{GUIDE_SLUG}/">What are my Naruto cards worth?</a><a class="ghostbtn" href="/price-guide/">Price guide</a><a class="ghostbtn" href="https://sell.jonin.cards">Sell to Jonin</a></p></section>
'''
    img = next((c['img'] for c in priced if re.match(r'^https://', c.get('img') or '')), B.SITE + '/og.png')
    ld = B.ld_json({'@context': 'https://schema.org', '@graph': [
        {'@type': 'CollectionPage', 'name': title, 'description': desc, 'url': url}, faq_ld(qas),
        B.crumbs(('Naruto CCG cards', B.SITE + '/'), ('Card values', f'{B.SITE}/{GUIDE_SLUG}/'), (y, url))]})
    return B.HEAD.format(title=e(title), desc=e(desc), url=url, img=e(img), tw='summary_large_image', ld=ld) + body + B.FOOT


def guide_page(cards, years, mv_chars, sets_by_id):
    url = f'{B.SITE}/{GUIDE_SLUG}/'
    priced = sorted([c for c in cards if c.get('pb') is not None and 0 <= c['pb'] < len(B.BANDS)], key=top_order)
    n = len(priced)
    hi = sum(1 for c in priced if c['pb'] == len(B.BANDS) - 1)
    lo = sum(1 for c in priced if c['pb'] == 0)
    title = 'What are my Naruto cards worth? Naruto CCG card values from real sales | Jonin'
    desc = ('How to find what your original Bandai Naruto CCG cards (2006–2013) are worth: identify the set, rarity, '
            'edition and foil, then look up real sold prices for raw and graded copies.')
    yrs = year_chips(years)
    mv = ''.join(f'<a class="chip" href="/character/{o["slug"]}/most-valuable/"><img src="/chars/{o["slug"]}.webp" alt="" width="24" height="24" loading="lazy">{e(o["label"])}</a>'
                 for o in mv_chars)
    qas = [
        ('What are my Naruto cards worth?',
         f'Most original Naruto CCG commons and uncommons sell for a few dollars. Super Rares, promos, 1st Editions, '
         f'certain foils and graded copies of popular characters are worth the most. Of the {n} cards with a recorded sale on Jonin, '
         f'{hi} have sold for {e(B.BANDS[-1])} and {lo} have never sold for more than {e(B.BANDS[0].replace("Under ", ""))}.'),
        ('What is the most valuable Naruto card?',
         'See <a href="/most-valuable/">the most valuable Naruto cards</a>, ranked by the highest real sale and updated as new sales come in.'),
        ('Is my Sasuke card worth money?',
         'It depends which Sasuke card it is. Look it up in <a href="/character/sasuke/">every Sasuke card</a>, or see '
         '<a href="/character/sasuke/most-valuable/">the most valuable Sasuke cards</a>.'),
        ('Are Kayou Naruto cards covered?',
         'No. Jonin covers the original Bandai Naruto CCG (2006–2013). Kayou and other newer Naruto cards are different products.'),
        ('Can I sell my Naruto cards to Jonin?',
         'Yes. <a href="https://sell.jonin.cards">Get an offer</a> for single cards, slabs or a whole collection.'),
    ]
    steps = f'''<section class="mvlistcard"><h2>How to tell what your Naruto card is worth</h2>
<p><b>1. Check it's the original Bandai game.</b> Jonin covers the Bandai Naruto CCG, printed 2006–2013. Newer Naruto cards, like Kayou, are a different product.</p>
<p><b>2. Find the card number and set.</b> Every card has a number like N-934 or J-001. Match it in its set, or start from the year it came out: {yrs}</p>
<p><b>3. Check the rarity.</b> Look for the dots after the copyright line: none is Common, one Uncommon, two Rare and three Super Rare. Super Rares and promos are the cards most collectors chase.</p>
<p><b>4. Check the edition and foil.</b> The same card can be 1st Edition or Unlimited, and many came in more than one finish: flat foil, diamond, wavy, spiral or prism (<a href="/articles/naruto-ccg-foil-types/">foil types explained</a>). Each version sells for a different price.</p>
<p><b>5. Check condition and grading.</b> Graded copies, especially PSA 10s, can sell for many times the price of a raw copy. Every card page links its PSA pop report and eBay sold listings for raw and graded copies.</p>
<p><b>6. Look up the price.</b> Each card page shows what it sells for, from real sales checked by hand. <a href="/club/">Jonin Club</a> breaks that down by edition, foil and grade, with every sold listing.</p>
</section>'''
    body = f'''<nav class="crumb"><a href="/">All cards</a> › Card values</nav>
<section class="sethead"><h1>What are my Naruto cards worth?</h1>
<p class="lede">Most original Bandai Naruto CCG cards sell for a few dollars. The money is in Super Rares, promos, 1st Editions, certain foils and graded copies of popular characters. {n} cards have a recorded sale on Jonin so far, and {hi} of them have sold for {e(B.BANDS[-1])}.</p>
<p class="btns"><a class="primary" href="/">Look up your card</a><a class="ghostbtn" href="https://sell.jonin.cards">Get an offer</a></p></section>
{steps}
<section class="cgroup"><h2>The most valuable Naruto cards<span>by highest recorded sale</span></h2>
<div class="grid">{"".join(tile_px(c, sets_by_id[c["s"]]) for c in priced[:12])}</div>
<p class="mt"><a href="/most-valuable/">See the full list →</a> · <a href="/price-guide/">Every priced card →</a></p></section>
{f'<section class="others"><h2>Most valuable cards by character</h2><div class="chips">{mv}</div></section>' if mv else ''}
<section class="others"><h2>Naruto CCG cards by year</h2><div class="chips">{yrs}</div></section>
{faq_html(qas)}
'''
    img = next((c['img'] for c in priced if re.match(r'^https://', c.get('img') or '')), B.SITE + '/og.png')
    ld = B.ld_json({'@context': 'https://schema.org', '@graph': [
        {'@type': 'WebPage', 'name': title, 'description': desc, 'url': url}, faq_ld(qas),
        B.crumbs(('Naruto CCG cards', B.SITE + '/'), ('Card values', url))]})
    return B.HEAD.format(title=e(title), desc=e(desc), url=url, img=e(img), tw='summary_large_image', ld=ld) + body + B.FOOT
