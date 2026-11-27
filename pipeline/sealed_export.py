"""Sealed products -> pipeline/sealed.json for the /sealed/ pages (sealed_pages.py).

Called from export_cards.py with the service key; the sealed tables themselves aren't readable from the site.
Free for everyone (same as cards, David 2026-11-27): the price range per edition, the last five sold, and what's
listed now (cheapest first, affiliate links).
"""
import json
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(__file__).resolve().parent / "sealed.json"
RECENT = 5           # last sold shown on each product page (same five as card pages for free visitors)
LIVE = 12            # PLACEHOLDER: current listings kept per product


def build(products, sets, ranges, sales, listings, now=None):
    now = (now or datetime.now(timezone.utc)).isoformat()
    set_name = {s["id"]: s["name"] for s in sets}
    set_sort = {s["id"]: s.get("sort", 99) for s in sets}
    rng, sold, live = {}, {}, {}
    for r in ranges:
        rng.setdefault(r["product_id"], []).append(
            {"ed": r.get("edition") or "", "low": float(r["low"]), "high": float(r["high"]),
             "avg": float(r["avg_price"]) if r.get("avg_price") is not None else None,
             "n": r["sales_count"], "last": (r.get("last_sold_at") or "")[:10]})
    for s in sorted(sales, key=lambda x: (x.get("sold_at") or ""), reverse=True):
        sold.setdefault(s["product_id"], []).append(
            [float(s["price"]), s.get("edition") or "", (s.get("sold_at") or "")[:10], s.get("url") or "",
             s.get("source") or "eBay", s.get("image_url") or ""])
    for li in sorted(listings, key=lambda x: float(x.get("price") or 0)):
        if not li.get("price") or (li.get("ends_at") and li["ends_at"] < now):
            continue                                  # ended, waiting to be settled
        live.setdefault(li["product_id"], []).append(
            {"t": li.get("title") or "", "p": float(li["price"]), "ed": li.get("edition") or "",
             "k": li.get("kind"), "b": li.get("bids") or 0, "bo": bool(li.get("best_offer")),
             "end": li.get("ends_at"), "u": li.get("url") or "", "img": li.get("image_url") or ""})
    out = []
    for p in sorted(products, key=lambda p: (set_sort.get(p["set_id"], 99), p.get("sort") or 0, p["name"])):
        if not p.get("public", True) or not p.get("slug"):
            continue
        ss, ll = sold.get(p["id"], []), live.get(p["id"], [])
        img = p.get("image_url") or ""
        credit = "Seller photo" if "/site/sealed/" in img else ""     # picked in the Hub from an eBay listing
        if not img:
            img = next((x[5] for x in ss if x[5]), "") or next((x["img"] for x in ll if x["img"]), "")
            credit = "Seller photo" if img else ""
        out.append({"id": p["id"], "slug": p["slug"], "name": p["name"], "kind": p["kind"], "set": p["set_id"],
                    "set_name": set_name.get(p["set_id"], ""), "released": p.get("released") or "",
                    "contents": p.get("contents") or "", "msrp": float(p["msrp"]) if p.get("msrp") is not None else None,
                    "confirmed": bool(p.get("confirmed")), "img": img, "credit": credit,
                    "ranges": sorted(rng.get(p["id"], []), key=lambda r: r["ed"]),
                    "recent": [x[:5] for x in ss[:RECENT]], "live": ll[:LIVE], "live_n": len(ll)})
    return {"products": out}


def write(products, sets, ranges, sales, listings):
    data = build(products, sets, ranges, sales, listings)
    text = json.dumps(data, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n"
    if not OUT.exists() or OUT.read_text() != text:
        OUT.write_text(text)
    return len(data["products"])
