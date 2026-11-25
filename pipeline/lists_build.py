"""Card lists for jonin.cards, built by build_pages.py.

  /lists/                               hub: every list type, with each character's lists
  /most-popular/                        most-voted cards overall + each character's popular list
  /character/<slug>/most-popular/       a character's most-voted cards
(/most-valuable/ and /character/<slug>/most-valuable/ are built in build_pages.py.)

Votes come from pipeline/votes.json (export_cards.py, from Supabase card_votes): only counts, never who voted.
A popular list goes live once VOTE_MIN_VOTERS people have voted for that character (David confirmed 5),
the same rule as the live Top 3 on character pages. Until then the page doesn't exist and isn't linked.
"""
import json, os, re, shutil

from settings import VOTE_MIN_VOTERS, POPULAR_TOP

VOTES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'votes.json')
B = None


def setup(build_pages):
    global B
    B = build_pages


def load_votes():
    return json.load(open(VOTES_FILE, encoding='utf-8')) if os.path.exists(VOTES_FILE) else {}


def popular_ranked(v, cards_by_key, top=POPULAR_TOP):
    """[(card, votes)] most-voted first, for a character's (or the overall) tally, if it has enough voters."""
    if not v or v.get('voters', 0) < VOTE_MIN_VOTERS:
        return []
    return [(cards_by_key[k], n) for k, n in v.get('cards', []) if k in cards_by_key and n > 0][:top]


def art(c, eager=False):
    e = B.e
    return (f'<img loading="{"eager" if eager else "lazy"}" src="{e(c["img"])}" alt="{e(c["name"])} {e(c["n"])} Naruto CCG card" width="750" height="1050">'
            if re.match(r'^https://', c.get('img') or '') else f'<span class="noimg sm"><b>{e(c["n"])}</b></span>')


def pop_page(ch, ranked, voters, sets_by_id, pop_chars):
    e, SITE = B.e, B.SITE
    url = f'{SITE}/character/{ch["slug"]}/most-popular/'
    n = len(ranked)
    title = f"Most popular {ch['name']} cards in the Naruto CCG (top {n}) | Jonin"
    lead = ranked[0][0]
    desc = (f"The {n} most popular {ch['name']} cards in the original Bandai Naruto CCG, voted by {voters} collectors. "
            f"#1: {lead['name']} {lead['n']} ({sets_by_id[lead['s']]['name']}).")
    rows = ''.join(
        f'<li class="mvrow"><span class="mvn">{i + 1}</span><a class="mvart" href="/card/{B.slug(c)}/">{art(c, i == 0)}</a>'
        f'<div class="mvinfo"><h2><a href="/card/{B.slug(c)}/">{e(c["name"])}</a></h2>'
        f'<p class="mt"><span class="stag">{B.sym_img(sets_by_id[c["s"]])}{e(sets_by_id[c["s"]]["name"])}</span> · {e(c["n"])} · {e(c["r"])}</p>'
        f'<dl><dt>Votes</dt><dd><b class="band">{v}</b></dd></dl></div></li>' for i, (c, v) in enumerate(ranked))
    others = ''.join(f'<a class="chip" href="/character/{o["slug"]}/most-popular/"><img src="/chars/{o["slug"]}.webp" alt="" width="24" height="24" loading="lazy">{e(o["label"])}</a>'
                     for o in pop_chars if o is not ch)
    body = (f'<nav class="crumb"><a href="/">All cards</a> › <a href="/characters/">Characters</a> › <a href="/character/{ch["slug"]}/">{e(ch["name"])}</a> › <a href="/most-popular/">Most popular</a></nav>\n'
            f'<section class="sethead charhead"><h1><img class="face" src="/chars/{ch["slug"]}.webp" alt="" width="56" height="56">Most popular {e(ch["name"])} cards</h1>\n'
            f'<p class="lede">The {e(ch["name"])} cards collectors like most, ranked by votes on Jonin. {voters} people have voted so far. Every signed-in collector gets 3 votes per character.</p>\n'
            f'<p class="btns"><a class="primary" href="/character/{ch["slug"]}/#vote-top">⭐ Cast your votes</a>'
            + (f'<a class="ghostbtn" href="/character/{ch["slug"]}/most-valuable/">💰 Most valuable {e(ch["label"])} cards</a>' if ch.get('mv') else '')
            + f'</p></section>\n<ol class="mvlist">{rows}</ol>\n'
            + (f'<section class="others"><h2>Most popular cards of other characters</h2><div class="chips">{others}</div></section>\n' if others else '')
            + '<p class="btns" style="margin-top:22px"><a class="ghostbtn" href="/lists/">All Naruto CCG lists</a></p>\n')
    img = next((c['img'] for c, _ in ranked if re.match(r'^https://', c.get('img') or '')), SITE + '/og.png')
    ld = B.ld_json({'@context': 'https://schema.org', '@graph': [
        {'@type': 'ItemList', 'name': title, 'description': desc, 'url': url, 'numberOfItems': n,
         'itemListOrder': 'https://schema.org/ItemListOrderDescending',
         'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'name': f"{c['name']} {c['n']}",
                              'url': f'{SITE}/card/{B.slug(c)}/'} for i, (c, _) in enumerate(ranked)]},
        B.crumbs(('Naruto CCG cards', SITE + '/'), ('Characters', SITE + '/characters/'),
                 (ch['name'], f'{SITE}/character/{ch["slug"]}/'), ('Most popular', url))]})
    return B.HEAD.format(title=e(title), desc=e(desc), url=url, img=e(img), tw='summary_large_image', ld=ld) + body + B.FOOT


def mini(c, i, sets_by_id, extra):
    e = B.e
    return (f'<a class="mvmini" href="/card/{B.slug(c)}/"><span class="mvn">{i + 1}</span>{art(c)}'
            f'<b>{e(c["name"])}</b><span class="mt">{e(c["n"])} · {e(sets_by_id[c["s"]]["name"])}</span><span class="band">{extra}</span></a>')


def pop_index(overall, all_voters, pop_chars, pop_ranked, chars, sets_by_id):
    e, SITE = B.e, B.SITE
    url = f'{SITE}/most-popular/'
    title = 'Most popular Naruto CCG cards: the best cards in the Naruto card game, voted by collectors | Jonin'
    desc = ('The best and coolest cards in the original Bandai Naruto CCG, voted by collectors on Jonin. '
            'An overall top list plus the most popular cards for each character.')
    vt = lambda n: f'{n} vote{"s" if n != 1 else ""}'
    over = (f'<section class="mvlistcard"><h2>Most popular across the whole game<span>{all_voters} collectors voted</span></h2>'
            f'<div class="mvminis">{"".join(mini(c, i, sets_by_id, vt(v)) for i, (c, v) in enumerate(overall[:6]))}</div></section>') if overall else ''
    blocks = ''.join(
        f'<section class="mvlistcard"><h2><a href="/character/{ch["slug"]}/most-popular/"><img class="face" src="/chars/{ch["slug"]}.webp" alt="" width="44" height="44">'
        f'Most popular {e(ch["name"])} cards</a><span>Top {len(pop_ranked[ch["slug"]])}</span></h2>'
        f'<div class="mvminis">{"".join(mini(c, i, sets_by_id, vt(v)) for i, (c, v) in enumerate(pop_ranked[ch["slug"]][:3]))}</div>'
        f'<p class="btns"><a class="primary" href="/character/{ch["slug"]}/most-popular/">See the full list →</a></p></section>' for ch in pop_chars)
    vote_chips = ''.join(f'<a class="chip" href="/character/{c["slug"]}/#vote-top"><img src="/chars/{c["slug"]}.webp" alt="" width="24" height="24" loading="lazy">{e(c["label"])}</a>' for c in chars)
    empty = '' if (over or blocks) else (f'<p class="lede">Voting is open. A character\'s list shows here once {VOTE_MIN_VOTERS} collectors have voted for their cards.</p>')
    body = (f'<nav class="crumb"><a href="/">All cards</a> › <a href="/lists/">Lists</a> › Most popular</nav>\n'
            f'<section class="sethead"><h1>Most popular Naruto CCG cards</h1>\n'
            f'<p class="lede">The best cards in the whole original Bandai Naruto card game (2006–2013), as voted by collectors: one list across every character, then a list for each character. Every signed-in collector gets 3 votes per character, and the lists update as votes come in.</p></section>\n'
            f'{empty}{over}{blocks}\n'
            f'<section class="others"><h2>Vote for your favorites<span>Pick a character</span></h2><div class="chips">{vote_chips}</div></section>\n')
    ld = B.ld_json({'@context': 'https://schema.org', '@graph': [
        {'@type': 'ItemList', 'name': title, 'description': desc, 'url': url, 'numberOfItems': len(pop_chars),
         'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'name': f"Most popular {ch['name']} cards",
                              'url': f'{SITE}/character/{ch["slug"]}/most-popular/'} for i, ch in enumerate(pop_chars)]},
        B.crumbs(('Naruto CCG cards', SITE + '/'), ('Lists', SITE + '/lists/'), ('Most popular', url))]})
    page = B.HEAD.format(title=e(title), desc=e(desc), url=url, img=e(SITE + '/og.png'), tw='summary_large_image', ld=ld) + body + B.FOOT
    if not (over or blocks):   # nothing to rank yet: keep it out of search until the first list is live
        page = page.replace('<meta charset="utf-8">', '<meta charset="utf-8">\n<meta name="robots" content="noindex">', 1)
    return page


def lists_index(mv_chars, pop_chars, popular_live):
    e, SITE = B.e, B.SITE
    url = f'{SITE}/lists/'
    title = 'Naruto CCG card lists: the most valuable and most popular cards in the Naruto card game | Jonin'
    desc = ('Every Naruto card list on Jonin: the most expensive cards by highest sale and the most popular cards voted by '
            'collectors, for the original Bandai Naruto CCG.')
    chip = lambda c, path: f'<a class="chip" href="/character/{c["slug"]}/{path}/"><img src="/chars/{c["slug"]}.webp" alt="" width="24" height="24" loading="lazy">{e(c["name"])}</a>'
    sec = lambda href, h, p, chips, more: (
        f'<section class="mvlistcard"><h2><a href="{href}">{h}</a></h2><p class="mt" style="margin:-6px 0 12px">{p}</p>'
        f'{f"<p class=mt style=margin:0 0 8px>By character</p><div class=chips>{chips}</div>" if chips else ""}{more}'
        f'<p class="btns" style="margin-top:12px"><a class="primary" href="{href}">Open the list →</a></p></section>')
    body = (f'<nav class="crumb"><a href="/">All cards</a> › Lists</nav>\n'
            f'<section class="sethead"><h1>Naruto CCG card lists</h1>\n'
            f'<p class="lede">Ranked lists for the whole original Bandai Naruto card game (2006–2013), not just Naruto himself: the most expensive cards by highest recorded sale, and the most popular cards voted by collectors, with a list for each character.</p></section>\n'
            + sec('/most-valuable/', '💰 Most valuable cards in the Naruto CCG', 'The most expensive cards in the game, ranked by the highest price each has sold for, with a top list per character. Updates as new sales come in.',
                  ''.join(chip(c, 'most-valuable') for c in mv_chars), '')
            + sec('/most-popular/', '⭐ Most popular cards in the Naruto CCG', 'Cards from across the game, ranked by collector votes, overall and per character. Every signed-in collector gets 3 votes per character.',
                  ''.join(chip(c, 'most-popular') for c in pop_chars),
                  '' if popular_live else f'<p class="mt">Voting is open. Lists appear once {VOTE_MIN_VOTERS} collectors have voted for a character.</p>'))
    ld = B.ld_json({'@context': 'https://schema.org', '@graph': [
        {'@type': 'CollectionPage', 'name': title, 'description': desc, 'url': url},
        B.crumbs(('Naruto CCG cards', SITE + '/'), ('Lists', url))]})
    return B.HEAD.format(title=e(title), desc=e(desc), url=url, img=e(SITE + '/og.png'), tw='summary_large_image', ld=ld) + body + B.FOOT


def build(chars, cards_by_key, sets_by_id, mv_chars):
    """Writes the popular pages and both hubs. Returns (files changed, urls for the sitemap)."""
    votes = load_votes()
    pop_ranked = {}
    for ch in chars:
        r = popular_ranked(votes.get(ch['slug']), cards_by_key)
        ch['pop'] = bool(r)
        if r:
            pop_ranked[ch['slug']] = r
    pop_chars = [ch for ch in chars if ch.get('pop')]
    overall = popular_ranked(votes.get('_all'), cards_by_key, 10)
    changed, urls = 0, [B.SITE + '/lists/']
    for ch in chars:
        d = os.path.join(B.ROOT, 'character', ch['slug'], 'most-popular')
        if ch.get('pop'):
            changed += B.write(os.path.join(d, 'index.html'),
                               pop_page(ch, pop_ranked[ch['slug']], votes[ch['slug']]['voters'], sets_by_id, pop_chars))
            urls.append(f'{B.SITE}/character/{ch["slug"]}/most-popular/')
        elif os.path.isdir(d):
            shutil.rmtree(d)
    live = bool(overall or pop_chars)
    changed += B.write(os.path.join(B.ROOT, 'most-popular', 'index.html'),
                       pop_index(overall, votes.get('_all', {}).get('voters', 0), pop_chars, pop_ranked, chars, sets_by_id))
    if live:
        urls.insert(1, B.SITE + '/most-popular/')
    changed += B.write(os.path.join(B.ROOT, 'lists', 'index.html'), lists_index(mv_chars, pop_chars, live))
    return changed, urls
