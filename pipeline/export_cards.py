"""Rebuild public/cards.json from Supabase, so jonin.cards always shows the Supabase card list.

    python pipeline/export_cards.py            # write public/cards.json
    python pipeline/export_cards.py --check    # exit 1 if public/cards.json differs from Supabase

The file format is exactly what the site and the Card Index already read; approved scans add an
optional "img" field on a card (its best public image).
"""
import json
import re
import sys
from pathlib import Path

try:
    from settings import PRICE_BAND_CUTOFFS
except ImportError:
    from pipeline.settings import PRICE_BAND_CUTOFFS

OUT = Path(__file__).resolve().parent.parent / "public" / "cards.json"
QUALITY_RANK = {"clean": 3, "slab": 2, "placeholder": 1}
# Postgres jsonb doesn't keep key order, so rarity counts come out in one fixed order.
RARITY_ORDER = ["Common", "Uncommon", "Rare", "Super Rare", "Ultra Rare", "Starter", "Fixed", "Promo", "Unknown"]


def _rar(d):
    d = d or {}
    return {k: d[k] for k in sorted(d, key=lambda k: (RARITY_ORDER.index(k) if k in RARITY_ORDER else 99, k))}


def _s(v):
    return "" if v is None else v


def _num(v):
    f = float(v)
    return int(f) if f == int(f) else round(f, 2)


def price_rows(ranges):
    """price_ranges rows -> {card_id: [[printing, edition, grader, grade, low, high, sales, last_sold_date], ...]}
    Ordered: edition, printing as listed on the card, raw before graded, higher grades first."""
    out = {}
    for r in ranges:
        out.setdefault(r["card_id"], []).append(r)
    def key(r):
        try:
            g = -float(re.match(r"[\d.]+", r.get("grade") or "0").group(0))
        except (AttributeError, ValueError):
            g = 0
        return (r.get("edition") != "1st Edition", r.get("printing") or "", r.get("grader") != "Raw",
                r.get("grader") or "", g)
    return {cid: [[r.get("printing") or "", r.get("edition") or "", r.get("grader") or "Raw", r.get("grade") or "",
                   _num(r["low"]), _num(r["high"]), r["sales_count"], (r.get("last_sold_at") or "")[:10]]
                  for r in sorted(rows, key=key)] for cid, rows in out.items()}


def band_labels(cuts=PRICE_BAND_CUTOFFS):
    """Free price band names, cheapest first: Under $10, $10–50, ..., $200+."""
    m = lambda v: f"${v:,}"
    return ([f"Under {m(cuts[0])}"] + [f"{m(a)}–{a2}" for a, a2 in zip(cuts, [f"{b:,}" for b in cuts[1:]])]
            + [f"{m(cuts[-1])}+"])


def price_band(rows, cuts=PRICE_BAND_CUTOFFS):
    """Index into band_labels() for a card's highest recorded sale, or None with no sales."""
    if not rows:
        return None
    top = max(max(r[4], r[5]) for r in rows)
    return sum(1 for c in cuts if top >= c)


def version_label(sale):
    """'1st Edition · Full foil · PSA 10' for a sale (blank parts left out)."""
    gr = sale.get("grader") or "Raw"
    parts = [sale.get("edition") or "", sale.get("printing") or "",
             "Raw" if gr == "Raw" else f"{gr} {sale.get('grade') or ''}".strip()]
    return " · ".join(p for p in parts if p and p != "?")


def best_sales(sales):
    """{card_id: its highest approved sale row} (any version, eBay or private, all time)."""
    best = {}
    for x in sales:
        cid, price = x.get("card_id"), float(x.get("price") or 0)
        if not cid or price <= 0 or x.get("status") != "approved":
            continue
        if (x.get("printing") or "") == "?" or (x.get("edition") or "") == "?":
            continue
        k = (price, x.get("sold_at") or "", x.get("id") or 0)
        if cid not in best or k > best[cid][0]:
            best[cid] = (k, x)
    return {cid: v[1] for cid, v in best.items()}


def top_sales(sales, cuts=PRICE_BAND_CUTOFFS):
    """Highest approved sale per card -> {card_id: [rank, band, version, sold_date]}.
    rank 1 = the most expensive top sale on the site. Only the order and the band go public here;
    exact prices are added just for cards on a most-valuable page (see reveal_top_prices)."""
    best = {cid: ((float(x["price"]), x.get("sold_at") or "", x.get("id") or 0), x) for cid, x in best_sales(sales).items()}
    order = sorted(best, key=lambda cid: (-best[cid][0][0], cid))
    return {cid: [i + 1, sum(1 for c in cuts if best[cid][0][0] >= c), version_label(best[cid][1]),
                  (best[cid][1].get("sold_at") or "")[:10]] for i, cid in enumerate(order)}


def reveal_top_prices(data, sales):
    """Most-valuable pages show the exact top sale (David's call, 2026-11-25). Only the cards that make a
    character's top list get [price, ebay_url] appended to "top"; every other card's prices stay Premium."""
    import build_pages as bp
    from settings import MOST_VALUABLE_CHARACTERS
    best = best_sales(sales)
    shown = 0
    for ch in bp.load_chars():
        if ch["slug"] not in MOST_VALUABLE_CHARACTERS:
            continue
        cs = bp.char_cards(ch, data["cards"])
        if not bp.mv_live(cs):
            continue   # list isn't live yet, so its top prices stay Premium
        for c in bp.most_valuable(cs):
            x = best.get(c["s"] + ":" + c["n"])
            if x and len(c["top"]) == 4:
                url = x.get("url") or ""
                c["top"] += [_num(x["price"]), url if url.startswith("https://") else "", x.get("source") or ""]
                shown += 1
    return shown


ARTICLE_SALES = Path(__file__).resolve().parent / "article_sales.json"
VOTES = Path(__file__).resolve().parent / "votes.json"


def vote_tallies(rows):
    """{character: {voters, cards: [[card_id, votes], ...]}} plus "_all" across characters. Counts only, no user ids."""
    out, people = {}, {}
    for r in rows:
        ch, cid, uid = r.get("character"), r.get("card_id"), r.get("user_id")
        if not ch or not cid:
            continue
        for k in (ch, "_all"):
            t = out.setdefault(k, {})
            t[cid] = t.get(cid, 0) + 1
            people.setdefault(k, set()).add(uid)
    return {k: {"voters": len(people[k]), "cards": sorted(([c, n] for c, n in t.items()), key=lambda x: (-x[1], x[0]))}
            for k, t in sorted(out.items())}


def write_votes(rows):
    text = json.dumps(vote_tallies(rows), separators=(",", ":"), sort_keys=True) + "\n"
    if not VOTES.exists() or VOTES.read_text() != text:
        VOTES.write_text(text)


def article_sale_ids():
    """Sale IDs that articles use ({{sale 123}} in pipeline/articles/*.md). Only these sales are written out."""
    import re
    ids = set()
    for f in (Path(__file__).resolve().parent / "articles").glob("*.md"):
        for grp in re.findall(r"\{\{sales?\s+([^}]+)\}\}", f.read_text(encoding="utf-8")):
            ids.update(int(x) for x in re.findall(r"\d+", grp))
    return ids


def article_sales(sales, ids):
    """{sale id: {c, p, d, v, src, url}} for the sales articles show (approved only)."""
    out = {}
    for x in sales:
        if x.get("id") in ids and x.get("status") == "approved" and x.get("card_id"):
            url = x.get("url") or ""
            out[str(x["id"])] = {"c": x["card_id"], "p": _num(x["price"]), "d": (x.get("sold_at") or "")[:10],
                                 "v": version_label(x), "src": x.get("source") or "",
                                 "url": url if url.startswith("https://") else ""}
    return dict(sorted(out.items(), key=lambda kv: int(kv[0])))


def write_article_sales(sales):
    text = json.dumps(article_sales(sales, article_sale_ids()), indent=1, sort_keys=False) + "\n"
    if not ARTICLE_SALES.exists() or ARTICLE_SALES.read_text() != text:
        ARTICLE_SALES.write_text(text)


def build(sets, cards, scans=(), url_for=lambda p: p, products=(), version=None, ranges=(), sales=()):
    """Pure transform: Supabase rows -> the cards.json object (same key order as before).
    A card with recorded sales gets "pb": its free price band (see price_band); exact prices are Premium.
    "top": [rank, band, version, date] of its highest sale, for the most-valuable pages (see top_sales)."""
    best = {}
    for sc in scans:
        if not sc.get("public"):
            continue
        rank = (QUALITY_RANK.get(sc.get("quality") or "", 0), sc.get("printing") == "Normal", sc.get("id", 0))
        if sc["card_id"] not in best or rank > best[sc["card_id"]][0]:
            best[sc["card_id"]] = (rank, sc)
    out_sets = []
    for s in sorted(sets, key=lambda s: (s.get("sort") is None, s.get("sort"))):
        o = {"id": s["id"], "name": s["name"], "code": _s(s.get("code")), "rel": _s(s.get("released")),
             "foils": s.get("foils") or [], "first": _s(s.get("first_edition")), "unl": _s(s.get("unlimited")),
             "notes": _s(s.get("notes")), "count": s.get("card_count") or 0, "rar": _rar(s.get("rarity_counts")),
             "kind": s["kind"]}
        if s.get("source"):
            o["src"] = s["source"]
        if s.get("symbol_url"):
            o["symbol"] = s["symbol_url"]
        out_sets.append(o)
    pnames = {p["id"]: p["name"] for p in products}
    px = price_rows(ranges)
    tops = top_sales(sales)
    out_cards = []
    for c in sorted(cards, key=lambda c: (c.get("sort") is None, c.get("sort"), c["id"])):
        o = {"s": c["set_id"], "n": c["number"], "name": c["name"], "t": _s(c.get("type")),
             "r": _s(c.get("rarity")), "src": _s(c.get("rarity_code")),
             "v": c.get("printings") or [], "ed": c.get("editions") or [""]}
        if c.get("note"):
            o["note"] = c["note"]
        if c.get("starter_exclusive") and c.get("rarity") != "Starter":
            o["st"] = 1                      # starter-deck version of a booster rarity (Card Index shows "Starter <rarity>")
        if c.get("deck"):
            names = [pnames.get(d.strip(), d.strip()) for d in c["deck"].split(",") if d.strip()]
            o["deck"] = ", ".join(names)     # products it comes in (Supabase products table)
        if c["id"] in best:
            u = best[c["id"]][1]["image_url"]
            o["img"] = url_for(u[len("storage:scans/"):]) if u.startswith("storage:scans/") else u
        if c["id"] in px:
            o["pb"] = price_band(px[c["id"]])   # free price band only; exact prices stay in Supabase (Premium)
        if c["id"] in tops:
            o["top"] = tops[c["id"]]
        out_cards.append(o)
    out = {"sets": out_sets, "cards": out_cards, "bands": band_labels()}
    if version is not None:
        out["version"] = version             # Supabase checklist_version; the Card Index compares it to warn when stale
    return out


def dumps(obj):
    return json.dumps(obj, ensure_ascii=True, separators=(",", ":"))


MIRROR = OUT.parent / "img" / "scans"   # filled by mirror_images.py
SITE = "https://jonin.cards"


def image_url(path):
    """A scan's address: the copy on jonin.cards (Cloudflare Pages) when mirrored, else Supabase Storage."""
    if (MIRROR / path).is_file():
        return f"{SITE}/img/scans/{path}"
    import supa
    return supa.public_url("scans", path)


def main():
    import supa
    with supa.Run("export_cards") as run:
        sales = supa.select("sales", {"select": "id,card_id,price,sold_at,status,printing,edition,grader,grade,url,source",
                                      "status": "eq.approved"})
        data = build(supa.select("sets"), supa.select("cards"),
                     supa.select("scans", {"select": "*", "public": "eq.true"}),
                     image_url,
                     supa.select("products"),
                     (supa.select("checklist_version") or [{}])[0].get("version"),
                     supa.select("price_ranges"),
                     sales)
        revealed = reveal_top_prices(data, sales)
        write_article_sales(sales)
        write_votes(supa.select("card_votes", {"select": "character,card_id,user_id"}))
        text = dumps(data)
        run.stats = {"sets": len(data["sets"]), "cards": len(data["cards"]),
                     "with_image": sum(1 for c in data["cards"] if "img" in c),
                     "with_prices": sum(1 for c in data["cards"] if "pb" in c),
                     "with_top_sale": sum(1 for c in data["cards"] if "top" in c), "top_prices_shown": revealed}
        same = OUT.exists() and OUT.read_text() == text
        run.stats["changed"] = not same
        if "--check" in sys.argv:
            print("in sync" if same else "OUT OF SYNC: public/cards.json differs from Supabase")
            sys.exit(0 if same else 1)
        if not same:
            OUT.write_text(text)
        print(json.dumps(run.stats))


if __name__ == "__main__":
    main()
