"""Build static, indexable pages for jonin.cards from public/cards.json.

Writes:
  public/card/<set>-<number>/index.html   one page per card
  public/set/<set>/index.html             one page per set (card list)
  public/sitemap.xml, public/robots.txt
Output is deterministic (no timestamps), so the sync workflow only commits real changes.
Stale card/set folders (cards removed or renumbered) are deleted.
usage: python pipeline/build_pages.py
"""
import html, json, os, re, shutil, sys
from urllib.parse import quote

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'public')
SITE = 'https://jonin.cards'
e = lambda s: html.escape(str(s or ''), quote=True)

PSA_POP = 'https://www.psacard.com/pop/tcg-cards/'
PSA = json.loads(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'psa_sets.json')).read())
SOLD = 'https://www.ebay.com/sch/i.html?LH_Sold=1&LH_Complete=1&_sop=13&_nkw='
NOT_KO = ' -kayou -mythos -proxy -custom -orica -fan'


def slug(c):
    return (c['s'] + '-' + c['n']).lower()


def set_slug(s):
    return s['id'].lower()


def set_label(s):
    return 'Set ' + s['id'] if s.get('kind') == 'Main' else 'Promo' if s.get('kind') == 'Promo' else s['id']


def sold(q, kind):
    extra = ' (psa,bgs,cgc,sgc)' if kind == 'slab' else ' -psa -bgs -cgc -sgc'
    return SOLD + quote('naruto ' + q + extra + NOT_KO)


def card_q(c):
    m = re.search(r'\d+', c['n'])
    return '"' + re.sub(r'\s*\[.*\]', '', c['name']) + '" ' + (m.group(0) if m else '')


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
<link rel="stylesheet" href="/pages.css">
{ld}
</head>
<body>
<header><div class="hw"><a class="logo" href="/" aria-label="Jonin home"><span class="jc" aria-hidden="true"><i></i><i><b>J</b></i></span><span aria-hidden="true">ONIN</span></a>
<nav><a href="/">Cards</a><a href="/#sets">Sets</a><a href="/premium/">🔔 Alerts</a></nav></div></header>
<main>
'''
FOOT = '''</main>
<footer>Jonin is a fan-made database for the original Bandai Naruto Collectible Card Game (2006–2013). Not affiliated with Bandai, Shueisha or Masashi Kishimoto.</footer>
</body></html>
'''


def ld_json(obj):
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False).replace('</', '<\\/') + '</script>'


def card_page(c, s, prev, nxt):
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
    rows = [('Set', f'<a href="/set/{set_slug(s)}/">{e(s["name"])}</a> · {e(set_label(s))}{" · " + e(s["rel"]) if s.get("rel") else ""}'),
            ('Number', e(c['n'])), ('Rarity', e(c['r'])), ('Type', e(c['t'])),
            ('Editions', e(', '.join(eds) or '—')),
            ('Printings', ''.join(f'<span class="pv">{e(v)}</span>' for v in (c.get('v') or [])))]
    if c.get('note'):
        rows.append(('Note', e(c['note'])))
    ld = ld_json({'@context': 'https://schema.org', '@type': 'Thing', 'name': f"{c['name']} ({c['n']})",
                  'description': desc, 'url': url, **({'image': img} if img else {}),
                  'isPartOf': {'@type': 'CreativeWork', 'name': f"Naruto CCG · {s['name']}", 'url': f'{SITE}/set/{set_slug(s)}/'}})
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
<div class="links">
<a class="primary" href="/#card={quote(c['s'] + ':' + c['n'])}">Track it in your collection</a>
<a href="{e(sold(card_q(c), 'slab'))}" target="_blank" rel="noopener">eBay sold · slabs</a>
<a href="{e(sold(card_q(c), 'raw'))}" target="_blank" rel="noopener">eBay sold · raw</a>
{psa}
<a href="/premium/?card={quote(c['s'] + ':' + c['n'])}&amp;name={quote(c['name'])}">🔔 Alerts for this card</a>
</div>
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
        f'<a class="tile" href="/card/{slug(c)}/">'
        + (f'<img loading="lazy" src="{e(c["img"])}" alt="{e(c["name"])} {e(c["n"])}" width="750" height="1050">'
           if re.match(r'^https://', c.get('img') or '') else f'<span class="noimg sm"><b>{e(c["n"])}</b></span>')
        + f'<span class="tn">{e(c["n"])}</span><span class="tt">{e(c["name"])}</span></a>' for c in cards)
    sym = f'<img class="sym" src="{e(s["symbol"])}" alt="">' if s.get('symbol') else ''
    body = f'''<nav class="crumb"><a href="/">All cards</a> › <a href="/#sets">Sets</a> › {e(s["name"])}</nav>
<section class="sethead"><h1>{sym}{e(s["name"])}</h1>
<dl class="inline">{''.join(f'<dt>{k}</dt><dd>{v}</dd>' for k, v in facts)}</dl>
{f'<p class="note">{e(s["notes"])}</p>' if s.get('notes') else ''}
<p><a class="primary" href="/#set={quote(s['id'])}">Browse and filter this set</a></p></section>
<section class="grid">{grid}</section>
'''
    ld = ld_json({'@context': 'https://schema.org', '@type': 'CollectionPage', 'name': title, 'description': desc, 'url': url})
    return HEAD.format(title=e(title), desc=e(desc), url=url, img=e(SITE + '/og.png'), tw='summary_large_image', ld=ld) + body + FOOT


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    old = open(path, encoding='utf-8').read() if os.path.exists(path) else None
    if old != text:
        open(path, 'w', encoding='utf-8').write(text)
        return 1
    return 0


def main():
    d = json.load(open(os.path.join(ROOT, 'cards.json'), encoding='utf-8'))
    sets = d['sets']
    by_set = {s['id']: [] for s in sets}
    for c in d['cards']:
        if c['s'] in by_set:
            by_set[c['s']].append(c)
    changed, keep_c, keep_s = 0, set(), set()
    for s in sets:
        cs = by_set[s['id']]
        for i, c in enumerate(cs):
            keep_c.add(slug(c))
            changed += write(os.path.join(ROOT, 'card', slug(c), 'index.html'),
                             card_page(c, s, cs[i - 1] if i else None, cs[i + 1] if i + 1 < len(cs) else None))
        keep_s.add(set_slug(s))
        changed += write(os.path.join(ROOT, 'set', set_slug(s), 'index.html'), set_page(s, cs))
    removed = 0
    for sub, keep in (('card', keep_c), ('set', keep_s)):
        base = os.path.join(ROOT, sub)
        for name in sorted(os.listdir(base)) if os.path.isdir(base) else []:
            if name not in keep:
                shutil.rmtree(os.path.join(base, name))
                removed += 1
    urls = [SITE + '/'] + [f'{SITE}/set/{set_slug(s)}/' for s in sets] + \
           [f'{SITE}/card/{slug(c)}/' for s in sets for c in by_set[s['id']]]
    changed += write(os.path.join(ROOT, 'sitemap.xml'),
                     '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                     + ''.join(f'<url><loc>{e(u)}</loc></url>\n' for u in urls) + '</urlset>\n')
    changed += write(os.path.join(ROOT, 'robots.txt'),
                     f'User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n')
    print(f'{len(keep_c)} card pages, {len(keep_s)} set pages, {changed} files written, {removed} stale folders removed')


if __name__ == '__main__':
    sys.exit(main())
