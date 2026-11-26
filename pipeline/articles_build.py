"""Articles for jonin.cards, built by build_pages.py.

Articles live in pipeline/articles/<slug>.md: a front-matter block, then the body in simple Markdown.
  ---
  title: ...            (required)
  description: ...      (search/social snippet)
  date: 2026-11-25      (publish date)
  cover: P:PR088        (card whose scan is the cover image; defaults to the first card mentioned)
  draft: true           (built at its URL but hidden: noindex, not listed, not in the sitemap, no "Featured in")
  ---
Body: blank-line paragraphs, ## / ### headings, "- " lists, **bold**, *italic*, [text](url).
Sales: {{sale 123}} on its own line = that exact sale (card scan, price, version, where/when, link). Sale IDs come
       from the "Add a sale" list on jonin.cards/admin; build reads them from pipeline/article_sales.json (export_cards.py).
Cards: {{card SET:NUM}} on its own line = a card block (scan, set, top sale, eBay sale link, card page);
       {{cards SET:NUM, SET:NUM}} on its own line = a row of card tiles; [[SET:NUM]] inline = a link to the card page.
"""
import datetime, html, os, re, shutil
from urllib.parse import quote

ARTICLES = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'articles')
INSTAGRAM = 'https://www.instagram.com/jonin.cards/'
FEATURED = {}   # "SET:NUM" -> [(slug, title)] of published articles that mention the card
SALES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'article_sales.json')
SALES = {}      # sale id (str) -> {c, p, d, v, src, url}


def load_sales():
    import json
    SALES.clear()
    if os.path.exists(SALES_FILE):
        SALES.update(json.load(open(SALES_FILE, encoding='utf-8')))
B = None        # build_pages module, set by setup()


def setup(build_pages):
    global B
    B = build_pages


def parse_article(path):
    raw = open(path, encoding='utf-8').read()
    m = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)$', raw, re.S)
    meta, body = {}, (m.group(2) if m else raw)
    if m:
        for line in m.group(1).splitlines():
            if ':' in line:
                k, v = line.split(':', 1)
                meta[k.strip().lower()] = v.strip()
    meta['slug'] = os.path.splitext(os.path.basename(path))[0]
    meta['draft'] = meta.get('draft', '').lower() in ('true', 'yes', '1')
    meta['body'] = body
    keys = []
    for kind, grp, inl in re.findall(r'\{\{(cards?|sales?)\s+([^}]+)\}\}|\[\[([^\]]+)\]\]', body):
        for k in (grp or inl).split(','):
            k = k.strip()
            if kind.startswith('sale'):
                k = SALES.get(k, {}).get('c', '')
            if k:
                keys.append(k)
    meta['refs'] = list(dict.fromkeys(keys))
    return meta


def load_articles():
    if not os.path.isdir(ARTICLES):
        return []
    arts = [parse_article(os.path.join(ARTICLES, f)) for f in sorted(os.listdir(ARTICLES)) if f.endswith('.md')]
    return sorted([a for a in arts if a.get('title')], key=lambda a: (a.get('date', ''), a['slug']), reverse=True)


def set_featured(arts, cards_by_key):
    FEATURED.clear()
    for a in arts:
        if not a['draft']:
            for k in a['refs']:
                if k in cards_by_key:
                    FEATURED.setdefault(k, []).append((a['slug'], a['title']))


def featured_in(c):
    arts = FEATURED.get(c['s'] + ':' + c['n'])
    if not arts:
        return ''
    return '<p class="featin">📰 Featured in ' + ' · '.join(
        f'<a href="/articles/{sl}/">{B.e(t)}</a>' for sl, t in arts) + '</p>'


def inline_md(t, cards_by_key):
    t = B.e(t).replace('&#x27;', "'")

    def cardlink(m):
        c = cards_by_key.get(html.unescape(m.group(1)).strip())
        return f'<a href="/card/{B.slug(c)}/">{B.e(c["name"])} {B.e(c["n"])}</a>' if c else m.group(0)
    t = re.sub(r'\[\[([^\]]+)\]\]', cardlink, t)
    t = re.sub(r'\[([^\]]+)\]\(([^)\s]+)\)', lambda m: f'<a href="{m.group(2)}"'
               + (' target="_blank" rel="noopener"' if m.group(2).startswith('http') else '') + f'>{m.group(1)}</a>', t)
    t = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', t)
    return re.sub(r'(?<![*\w])\*(?!\s)(.+?)\*', r'<i>\1</i>', t)


def sale_link(url, src):
    if not url:
        return ' · Private sale' if src in ('', 'Private') else ' · ' + B.e(src)
    ebay = 'ebay.com' in url
    href = url + (("&" if "?" in url else "?") + B.EPN.lstrip("&") if ebay else '')
    where = 'eBay' if ebay else (src if src and src not in ('Private', 'Other') else 'the sale')
    return (f' · <a href="{B.e(href)}" target="_blank" rel="{"sponsored " if ebay else ""}noopener">'
            f'See it on {B.e(where)} ↗</a>')


def sale_slab(sid):
    """Site path of the saved listing photo (the sold slab) for sale id sid, or '' (see export_cards.sale_photo)."""
    d = os.path.join(B.ROOT, 'img', 'sales')
    if not sid or not os.path.isdir(d):
        return ''
    for f in sorted(os.listdir(d)):
        if f == f'{sid}.jpg' or f.endswith(f'-{sid}.jpg'):
            return f'/img/sales/{f}'
    return ''


def card_block(c, s, sale=None):
    e = B.e
    slab = sale_slab(sale.get('id')) if sale else ''
    if slab:   # a {{sale}} block shows the actual copy that sold, when we have its photo
        img = (f'<img class="slab" loading="lazy" src="{e(slab)}" alt="{e(c["name"])} {e(c["n"])} {e(sale["v"])} '
               f'Naruto card, the copy that sold for {e(B.money(sale["p"]))}" width="600" height="1000">')
    else:
        img = (f'<img loading="lazy" src="{e(c["img"])}" alt="{e(c["name"])} {e(c["n"])} Naruto CCG card" width="750" height="1050">'
               if re.match(r'^https://', c.get('img') or '') else f'<span class="noimg sm"><b>{e(c["n"])}</b></span>')
    top = c.get('top') or []
    if sale:
        label, price, ver, day, url, src = 'Sold for', sale['p'], sale['v'], sale['d'], sale['url'], sale['src']
    else:
        label, price, ver, day = 'Top sale', (top[4] if len(top) > 4 else None), (top[2] if len(top) > 2 else ''), (top[3] if len(top) > 3 else '')
        url, src = (top[5] if len(top) > 5 else ''), (top[6] if len(top) > 6 else '')
    sale = ''
    if price:
        sale = (f'<dl><dt>{label}</dt><dd><b class="band">{e(B.money(price))}</b></dd>'
                f'<dt>Version</dt><dd>{e(ver) or "—"}</dd><dt>Sold</dt><dd>{e(day) or "—"}{sale_link(url, src)}</dd></dl>')
    card = B.slug(c)
    return (f'<figure class="acard"><a class="mvart" href="/card/{card}/">{img}</a><figcaption>'
            f'<h3><a href="/card/{card}/">{e(c["name"])}</a></h3>'
            f'<p class="mt"><span class="stag">{B.sym_img(s)}{e(s["name"])}</span> · {e(c["n"])} · {e(c["r"])}</p>{sale}'
            f'<p class="btns"><a class="ghostbtn" href="/card/{card}/">Card page</a>'
            f'<a class="ghostbtn" href="/club/?card={quote(c["s"] + ":" + c["n"])}&amp;name={quote(c["name"])}">🔔 Alerts</a></p>'
            f'</figcaption></figure>')


def article_body(a, cards_by_key, sets_by_id):
    out = []
    for block in re.split(r'\n\s*\n', a['body'].strip()):
        b = block.strip()
        m = re.fullmatch(r'\{\{(cards?|sales?)\s+([^}]+)\}\}', b)
        if m and m.group(1).startswith('sale'):
            for k in m.group(2).split(','):
                x = SALES.get(k.strip())
                if x and x['c'] in cards_by_key:
                    c = cards_by_key[x['c']]
                    out.append(card_block(c, sets_by_id[c['s']], dict(x, id=k.strip())))
        elif m:
            cs = [cards_by_key[k.strip()] for k in m.group(2).split(',') if k.strip() in cards_by_key]
            if m.group(1) == 'card':
                out += [card_block(c, sets_by_id[c['s']]) for c in cs]
            elif cs:
                out.append(f'<div class="grid">{"".join(B.tile(c, sets_by_id[c["s"]]) for c in cs)}</div>')
        elif b.startswith('### '):
            out.append(f'<h3>{inline_md(b[4:], cards_by_key)}</h3>')
        elif b.startswith('## '):
            out.append(f'<h2>{inline_md(b[3:], cards_by_key)}</h2>')
        elif all(l.strip().startswith('- ') for l in b.splitlines()):
            out.append('<ul>' + ''.join(f'<li>{inline_md(l.strip()[2:], cards_by_key)}</li>' for l in b.splitlines()) + '</ul>')
        else:
            out.append(f'<p>{inline_md(" ".join(b.splitlines()), cards_by_key)}</p>')
    return '\n'.join(out)


def nice_date(d):
    try:
        x = datetime.date.fromisoformat(d)
        return x.strftime('%b ') + str(x.day) + x.strftime(', %Y')
    except ValueError:
        return d


def share_row(url, title):
    u, t = quote(url, safe=''), quote(title, safe='')
    return ('<div class="share"><span>Share</span>'
            f'<a href="https://twitter.com/intent/tweet?url={u}&amp;text={t}" target="_blank" rel="noopener">X</a>'
            f'<a href="https://www.facebook.com/sharer/sharer.php?u={u}" target="_blank" rel="noopener">Facebook</a>'
            f'<a href="https://www.reddit.com/submit?url={u}&amp;title={t}" target="_blank" rel="noopener">Reddit</a>'
            f'<button type="button" data-copy="{B.e(url)}" onclick="navigator.clipboard.writeText(this.dataset.copy).then(()=>this.textContent=\'Copied ✓\')">Copy link</button>'
            f'<a class="igbtn" href="{INSTAGRAM}" target="_blank" rel="noopener">{B.IG_SVG}<span>Follow <b class="h">@jonin.cards</b></span></a></div>')


def cover_of(a, cards_by_key):
    return cards_by_key.get(a.get('cover', '')) or next((cards_by_key[k] for k in a['refs'] if k in cards_by_key), None)


def article_page(a, arts, cards_by_key, sets_by_id):
    e, SITE = B.e, B.SITE
    url = f'{SITE}/articles/{a["slug"]}/'
    title = a['title']
    desc = a.get('description') or title
    cover = cover_of(a, cards_by_key)
    img = cover['img'] if cover and re.match(r'^https://', cover.get('img') or '') else SITE + '/og.png'
    words = len(re.findall(r'\w+', re.sub(r'\{\{.*?\}\}|\[\[.*?\]\]', '', a['body'])))  # card/sale blocks not counted
    mentioned = [cards_by_key[k] for k in a['refs'] if k in cards_by_key]
    more = [x for x in arts if x is not a and not x['draft']][:4]
    more_html = ('<section class="others"><h2>More articles</h2><ul class="alist">'
                 + ''.join(f'<li><a href="/articles/{x["slug"]}/"><div><b>{e(x["title"])}</b><span>{e(nice_date(x.get("date", "")))}</span></div></a></li>' for x in more)
                 + '</ul></section>') if more else ''
    chips = ''.join(f'<a class="chip" href="/card/{B.slug(c)}/">{e(c["name"])} {e(c["n"])}</a>' for c in mentioned)
    chips_html = f'<section class="others"><h2>Cards in this article</h2><div class="chips">{chips}</div></section>' if chips else ''
    draft = '<p class="draftnote">Draft: only people with this link can see it. Not listed or indexed yet.</p>' if a['draft'] else ''
    body = (f'<nav class="crumb"><a href="/">All cards</a> › <a href="/articles/">Articles</a> › {e(title)}</nav>\n'
            f'<article class="post">\n{draft}<h1>{e(title)}</h1>\n'
            f'<p class="mt">{e(nice_date(a.get("date", "")))} · {max(1, round(words / 220))} min read</p>\n'
            f'{article_body(a, cards_by_key, sets_by_id)}\n'
            f'{share_row(url, title)}\n{chips_html}\n</article>\n{more_html}\n')
    ld = B.ld_json({'@context': 'https://schema.org', '@graph': [
        {'@type': 'Article', 'headline': title, 'description': desc, 'url': url, 'image': img,
         'datePublished': a.get('date', ''), 'author': {'@type': 'Organization', 'name': 'Jonin', 'url': SITE},
         'publisher': {'@type': 'Organization', 'name': 'Jonin', 'url': SITE, 'sameAs': [INSTAGRAM]},
         'mentions': [{'@type': 'Thing', 'name': f"{c['name']} ({c['n']})", 'url': f'{SITE}/card/{B.slug(c)}/'} for c in mentioned]},
        B.crumbs(('Naruto CCG cards', SITE + '/'), ('Articles', SITE + '/articles/'), (title, url))]})
    page = B.HEAD.format(title=e(title + ' | Jonin'), desc=e(desc), url=url, img=e(img), tw='summary_large_image', ld=ld) + body + B.FOOT
    page = page.replace('<meta property="og:type" content="website">', '<meta property="og:type" content="article">', 1)
    if a['draft']:
        page = page.replace('<meta charset="utf-8">', '<meta charset="utf-8">\n<meta name="robots" content="noindex">', 1)
    return page


def articles_index(arts, cards_by_key):
    e, SITE = B.e, B.SITE
    url = f'{SITE}/articles/'
    title = 'Naruto CCG articles: top sales and card deep dives | Jonin'
    desc = 'Articles on the original Bandai Naruto CCG: the biggest sales, the most valuable cards and the stories behind them.'

    def row(a):
        cover = cover_of(a, cards_by_key)
        img = (f'<img loading="lazy" src="{e(cover["img"])}" alt="" width="750" height="1050">'
               if cover and re.match(r'^https://', cover.get('img') or '') else '')
        return (f'<li><a href="/articles/{a["slug"]}/">{img}<div><b>{e(a["title"])}</b>'
                f'<span>{e(nice_date(a.get("date", "")))}</span><p>{e(a.get("description", ""))}</p></div></a></li>')
    items = ''.join(row(a) for a in arts if not a['draft']) or '<li class="empty">First article coming soon.</li>'
    body = (f'<nav class="crumb"><a href="/">All cards</a> › Articles</nav>\n'
            f'<section class="sethead"><h1>Articles</h1>\n'
            f'<p class="lede">Top sales, the most valuable cards, and the stories behind them.</p>\n'
            f'<p class="btns"><a class="igbtn" href="{INSTAGRAM}" target="_blank" rel="noopener">{B.IG_SVG}<span>Follow <b class="h">@jonin.cards</b></span></a></p></section>\n'
            f'<ul class="alist big">{items}</ul>\n')
    ld = B.ld_json({'@context': 'https://schema.org', '@graph': [
        {'@type': 'CollectionPage', 'name': title, 'description': desc, 'url': url},
        B.crumbs(('Naruto CCG cards', SITE + '/'), ('Articles', url))]})
    return B.HEAD.format(title=e(title), desc=e(desc), url=url, img=e(SITE + '/og.png'), tw='summary_large_image', ld=ld) + body + B.FOOT


def build_articles(arts, cards_by_key, sets_by_id):
    changed = 0
    base = os.path.join(B.ROOT, 'articles')
    for a in arts:
        changed += B.write(os.path.join(base, a['slug'], 'index.html'), article_page(a, arts, cards_by_key, sets_by_id))
    changed += B.write(os.path.join(base, 'index.html'), articles_index(arts, cards_by_key))
    keep = {a['slug'] for a in arts}
    for name in sorted(os.listdir(base)):
        if os.path.isdir(os.path.join(base, name)) and name not in keep:
            shutil.rmtree(os.path.join(base, name))
    return changed
