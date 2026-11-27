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
            + (f'{len(priced)} of them have a recorded sale on Jonin, with typical copies selling for {money_span(sp)} depending on the card.'
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
            + (f'<p class="mt">Typical copies sell for {e(money_span(csp))} depending on the card.</p>' if csp else '')
            + f'<div class="grid">{"".join(tile_px(c, sets_by_id[c["s"]]) for c in mine[:YEAR_CHAR_CARDS])}</div>'
            + f'<p class="mt"><a href="/character/{e(ch["slug"])}/">Every {e(ch["name"])} card →</a>'
            + (f' · <a href="/character/{e(ch["slug"])}/most-valuable/">Most valuable {e(ch["name"])} cards →</a>' if ch.get('mv') else '')
            + '</p></section>')
        if csp:
            best = next((c for c in mine if c.get('pr')), None)
            qas.append((f'What is my {y} {ch["label"]} card worth?',
                        f'It depends which card you have. Bandai printed {len(mine)} {e(ch["name"])} card{"s" if len(mine) != 1 else ""} in {y}, '
                        f'and a typical copy of the ones with recorded sales goes for {e(money_span(csp))}, depending on which card it is. '
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
    title = 'What are my Naruto cards worth? How to price Naruto CCG cards | Jonin'
    desc = ('How to find what your original Bandai Naruto CCG cards (2006–2013) are worth: read the card, '
            'match the exact version, and compare real sold prices for raw and graded copies.')
    qas = [
        ('What are my Naruto cards worth?',
         'Most original Naruto CCG commons and uncommons sell for a few dollars. Super Rares, promos, 1st Editions, '
         'certain foils and graded copies of popular characters are worth the most. Look up your card to see what a typical copy sells for.'),
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
    sets_n = {}
    for c in cards:
        sets_n[c['s']] = sets_n.get(c['s'], 0) + 1
    ytiles = ''.join(
        f'<a class="ytile" href="/year/{y}/"><b>{y}</b><span>{len(ss)} set{"s" if len(ss) != 1 else ""}</span></a>'
        for y, ss in years.items())
    # 1. Read your card: a card diagram with the four things to check beside it
    card_svg = (
        '<svg class="cardsvg" viewBox="0 0 220 308" aria-hidden="true">'
        '<defs><linearGradient id="vgfoil" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
        '<stop offset=".45" stop-color="#fff" stop-opacity=".28"/><stop offset=".55" stop-color="#fff" stop-opacity="0"/></linearGradient></defs>'
        '<rect x="2" y="2" width="216" height="304" rx="14" class="c-edge"/>'
        '<rect x="14" y="14" width="192" height="26" rx="6" class="c-bar"/>'
        '<rect x="22" y="22" width="96" height="10" rx="5" class="c-ink"/>'
        '<rect x="14" y="48" width="192" height="138" rx="8" class="c-art"/>'
        '<circle cx="110" cy="112" r="34" class="c-face"/>'
        '<rect x="14" y="48" width="192" height="138" rx="8" fill="url(#vgfoil)"/>'
        '<rect x="14" y="196" width="192" height="64" rx="8" class="c-box"/>'
        '<rect x="24" y="208" width="150" height="7" rx="3.5" class="c-line"/><rect x="24" y="222" width="168" height="7" rx="3.5" class="c-line"/>'
        '<rect x="24" y="236" width="120" height="7" rx="3.5" class="c-line"/>'
        '<rect x="14" y="270" width="80" height="22" rx="6" class="c-tag"/><text x="54" y="285.5" class="c-tagt">N-934</text>'
        '<rect x="104" y="278" width="70" height="6" rx="3" class="c-line"/>'
        '<circle cx="184" cy="281" r="3.6" class="c-dot"/><circle cx="194" cy="281" r="3.6" class="c-dot"/><circle cx="204" cy="281" r="3.6" class="c-dot"/>'
        '</svg>')
    read = f"""<section class="vsec"><p class="eyebrow">Step 1</p><h2>Read your card</h2>
<p class="sub">Four things decide what a Naruto card is worth.</p>
<div class="anat">{card_svg}
<ol class="checks">
<li><b>Card number</b><span>Like N-934 or J-001. It tells you exactly which card you have.</span></li>
<li><b>Rarity dots</b><span>After the copyright line. <span class="rs rs-C">C</span> none · <span class="rs"><i></i></span> Uncommon · <span class="rs"><i></i><i></i></span> Rare · <span class="rs rs-SR"><i></i><i></i><i></i></span> Super Rare</span></li>
<li><b>Edition and foil</b><span>1st Edition or Unlimited, and normal or foil: <span class="fx f-flat"></span><span class="fx f-diamond"></span><span class="fx f-wavy"></span><span class="fx f-spiral"></span><span class="fx f-prism"></span> <a href="/articles/naruto-ccg-foil-types/">Foil types</a></span></li>
<li><b>Condition</b><span>Raw (ungraded) or graded, like a PSA 10. A high grade can be worth many times a raw copy.</span></li>
</ol></div></section>"""
    # 2. How to comp: search -> match the version -> compare sold prices
    comp = """<section class="vsec"><p class="eyebrow">Step 2</p><h2>How to price it</h2>
<p class="sub">Compare your card only with sales of the same card, version and condition.</p>
<div class="flow">
<div class="fstep"><span class="no">1</span><h3>Find the card</h3>
<div class="mock msearch"><span class="mag"></span>Sasuke N-934<span class="caret"></span></div>
<p>Search by name or number, or browse by set or year.</p></div>
<span class="farr" aria-hidden="true">→</span>
<div class="fstep"><span class="no">2</span><h3>Match your version</h3>
<div class="mock mchips"><span class="on">1st Edition</span><span>Unlimited</span><span class="on">Foil</span><span>Normal</span><span class="on">Raw · NM</span><span>PSA 10</span></div>
<p>A foil 1st Edition and a normal Unlimited are different prices.</p></div>
<span class="farr" aria-hidden="true">→</span>
<div class="fstep"><span class="no">3</span><h3>Check sold prices</h3>
<div class="mock msold"><div><span>Sold · 1st Ed · Foil · Raw</span><b>$•••</b></div><div><span>Sold · 1st Ed · Foil · Raw</span><b>$•••</b></div><div class="x"><span>Listed · PSA 10</span><b>skip</b></div></div>
<p>Use sold prices, not asking prices, and favor the most recent sales.</p></div>
</div>
<p class="btns"><a class="primary" href="/">Look up your card</a></p></section>"""
    faq = ('<section class="vsec"><p class="eyebrow">Questions</p><h2>Naruto card values, answered</h2><div class="faqs">'
           + ''.join(f'<details><summary>{e(q)}</summary><p>{a}</p></details>' for q, a in qas) + '</div></section>')
    body = f"""<div class="vg">
<nav class="crumb"><a href="/">All cards</a> › Card values</nav>
<section class="vhero"><p class="eyebrow">Naruto CCG card values</p><h1>What are my Naruto cards worth?</h1>
<p class="lede">Most original Bandai Naruto CCG cards sell for a few dollars. The money is in Super Rares, promos, 1st Editions, foils and graded copies of popular characters. Here's how to tell what yours is worth.</p></section>
{read}
{comp}
<section class="vsec"><p class="eyebrow">Browse</p><h2>Find your card by year</h2><div class="ytiles">{ytiles}</div></section>
<section class="vsec"><p class="eyebrow">For reference</p><h2>The most valuable Naruto cards</h2>
<div class="grid">{"".join(tile_px(c, sets_by_id[c["s"]]) for c in priced[:6])}</div>
<p class="more"><a href="/most-valuable/">See the full list →</a><a href="/price-guide/">Price guide →</a></p></section>
{faq}
<section class="vsell"><h2>Have Naruto cards to sell?</h2><p>Single cards, slabs or a whole collection.</p><p class="btns"><a class="primary" href="https://sell.jonin.cards">Get an offer</a></p></section>
</div>
"""
    img = next((c['img'] for c in priced if re.match(r'^https://', c.get('img') or '')), B.SITE + '/og.png')
    ld = B.ld_json({'@context': 'https://schema.org', '@graph': [
        {'@type': 'WebPage', 'name': title, 'description': desc, 'url': url}, faq_ld(qas),
        B.crumbs(('Naruto CCG cards', B.SITE + '/'), ('Card values', url))]})
    return B.HEAD.format(title=e(title), desc=e(desc), url=url, img=e(img), tw='summary_large_image', ld=ld) + body + B.FOOT
