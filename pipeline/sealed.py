"""Sealed Naruto CCG product matching (booster packs and boxes, theme and starter decks, tins, tournament packs).

collect_sales.py hands every eBay listing it reads to `to_listing` first. A listing that is one clear sealed
product becomes a `sealed_listings` row (and is not treated as a card); when it ends it is settled the same way
as cards and waits in `sealed_sales` for David's OK in Jonin Hub → Sealed.

Every rule below marked PLACEHOLDER is a starting guess for David to change.
"""
import re

import prices
import settings as cfg

KIND_LABEL = {"booster_pack": "Booster pack", "booster_box": "Booster box", "theme": "Theme deck",
              "starter": "Starter deck", "tin": "Tin", "tournament_pack": "Tournament pack"}

# A title with any of these is not one sealed item. PLACEHOLDER
SKIP = ["opened", "open box", "empty", "resealed", "re-sealed", "unsealed", "no cards", "wrapper", "wrappers",
        "box only", "tin only", "case only", "pulls", "pulled", "pack fresh", "from pack", "art card",
        "japanese", "japan", "kayou", "mythos", "boruto", "proxy", "custom", "replica", "reprint", "lot",
        "bundle", "case of", "sealed case", "deck box", "storage box", "playmat", "sleeves", "binder",
        "you pick", "choose", "booster box break", "break", "rip", "repack", "mystery"]
SKIP_RE = re.compile(r"\b(?:" + "|".join(re.escape(w) for w in SKIP) + r")\b")
# More than one of something ("3 packs", "x2", "2x") -> skip. PLACEHOLDER: multiples aren't split into a per-item price
MULTI = re.compile(r"\b(?:[2-9]|\d{2,})\s*(?:x\b|packs\b|boosters\b|boxes\b|tins\b|decks\b)|\bx\s*[2-9]\b|\b[2-9]x\b")
# A single card's number in the title means it's a card listing ("N-001", "#123", "J-12")
CARD_NUMBER = re.compile(r"\b[NJMCP]-?\s?\d{2,4}\b|#\s?\d{2,4}\b|\bPR-?\d+", re.I)


def norm(s):
    s = (s or "").lower().replace("&", " and ").replace("’", "'")
    s = re.sub(r"'s\b", "", s)                      # Kage's Summit -> kage summit
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return " " + re.sub(r"\s+", " ", s).strip() + " "


def set_keys(sets):
    """[(normalized set name, set id)] longest first, 'the' dropped ('The Chosen' -> 'chosen')."""
    out = []
    for s in sets:
        if s.get("kind") != "Main":
            continue
        n = norm(s["name"]).replace(" the ", " ").strip()
        out.append((" " + n + " ", s["id"]))
    return sorted(out, key=lambda x: -len(x[0]))


def find_set(t, keys):
    """t: norm(title) with 'the' dropped. Set by name, else 'series 12' / 'set 12' / 's12'."""
    for k, sid in keys:
        if k in t:
            return sid, "set name"
    m = re.search(r" (?:series|set|s) ?(\d{1,2}) ", t)
    if m and any(sid == m.group(1) for _, sid in keys):
        return m.group(1), "series number"
    return None, ""


def find_kind(t):
    """(kind, inferred?) from the title words. PLACEHOLDER: a bare 'box' is a booster box; a bare 'booster' is a pack."""
    if " tournament pack " in t:
        return "tournament_pack", False
    if re.search(r" tins? ", t):
        return "tin", False
    if " theme deck " in t:
        return "theme", False
    if " starter deck " in t or " starter " in t:
        return "starter", False
    if " booster box " in t or " display " in t:
        return "booster_box", False
    if " booster pack " in t:
        return "booster_pack", False
    if " box " in t:
        return "booster_box", True
    if " pack " in t or " booster " in t:
        return "booster_pack", True
    if " deck " in t:
        return "deck", True
    return None, False


def edition(title):
    """'1st Edition', 'Unlimited' or '' (title doesn't say). PLACEHOLDER: not assumed Unlimited like cards are."""
    t = " " + title.lower() + " "
    if re.search(r"\b(1st|first)\s*(ed\b|edition|ed\.)|\b1st\b", t):
        return "1st Edition"
    if "unlimited" in t:
        return "Unlimited"
    return ""


# For photos only (find_sealed_images.py): an opened or empty box still shows the right box art. PLACEHOLDER
PHOTO_SKIP_RE = re.compile(r"\b(?:japanese|japan|kayou|mythos|boruto|proxy|custom|replica|reprint|lot|bundle|break|"
                           r"mystery|repack|you pick|choose|pulls|pulled|wrapper|wrappers|binder|playmat|sleeves)\b")


def match(title, products, sets, photo=False):
    """One sealed product for a listing title -> (product, confidence, reason) or None.
    photo=True: looser rules for finding a product photo (opened/empty items allowed)."""
    low = " " + (title or "").lower() + " "
    if not re.search(r"naruto", low):
        return None
    if photo:
        if PHOTO_SKIP_RE.search(low) or MULTI.search(low):
            return None
    elif SKIP_RE.search(low) or any(w in low for w in cfg.SALES_SKIP_WORDS) or MULTI.search(low):
        return None
    if CARD_NUMBER.search(title or ""):
        return None
    t = norm(title).replace(" the ", " ")
    kind, inferred = find_kind(t)
    if not kind:
        return None
    by_kind = lambda k: [p for p in products if p["kind"] == k and p.get("public", True)]
    if kind == "tin":
        for p in by_kind("tin"):
            for w in p.get("match_words") or []:
                if norm(w).replace(" the ", " ") in t:
                    return p, 0.9, f"tin name '{w}'"
        return None
    if kind == "tournament_pack":
        m = re.search(r" (?:tp|tournament pack) ?(\d) ", t)
        p = next((p for p in by_kind("tournament_pack") if m and p["set_id"] == f"TP{m.group(1)}"), None)
        return (p, 0.9, f"tournament pack {m.group(1)}") if p else None
    sid, how = find_set(t, set_keys(sets))
    if not sid:
        return None
    if kind == "deck":
        decks = [p for p in products if p["set_id"] == sid and p["kind"] in ("theme", "starter")]
        kinds = {p["kind"] for p in decks}
        if len(kinds) != 1:
            return None
        kind = kinds.pop()
    cands = [p for p in by_kind(kind) if p["set_id"] == sid]
    if len(cands) > 1:                              # several decks in one set: the deck's own name decides
        bare = t.replace(" naruto ", " ", 1)        # the brand word isn't the Naruto deck's name
        named = [p for p in cands if any(norm(w) in bare for w in p.get("match_words") or [])]
        if len(named) != 1:
            return None
        cands = named
        how += f", deck name '{named[0]['match_words'][0]}'"
    if not cands:
        return None
    conf = 0.75 if inferred else 0.9
    sealed_word = re.search(r"\b(sealed|factory sealed|new)\b", low)
    if not sealed_word:
        conf -= 0.1
    reason = f"{how}, {KIND_LABEL.get(kind, kind).lower()}" + ("" if not inferred else " (guessed from 'box'/'pack')") \
        + ("" if sealed_word else ", title doesn't say sealed")
    return cands[0], round(conf, 2), reason


def to_listing(it, products, sets, iso_now):
    """A Browse item summary -> a sealed_listings row, or None if it isn't one clear sealed product."""
    title = it.get("title", "")
    hit = match(title, products, sets)
    if not hit or hit[1] < cfg.SEALED_MIN_CONFIDENCE:
        return None
    p, conf, reason = hit
    opts = it.get("buyingOptions") or []
    auction = "AUCTION" in opts
    price = (it.get("currentBidPrice") if auction else it.get("price")) or it.get("price") or {}
    if price.get("currency", "USD") != "USD":
        return None
    ed = edition(title)
    return {"external_id": f"ebay:{it['itemId']}", "product_id": p["id"], "title": title,
            "price": float(price.get("value") or 0), "currency": "USD", "edition": ed,
            "kind": "AUCTION" if auction else "FIXED_PRICE", "bids": it.get("bidCount") or 0,
            "best_offer": "BEST_OFFER" in opts, "ends_at": it.get("itemEndDate"), "source": "eBay",
            "url": it.get("itemWebUrl"), "image_url": ((it.get("image") or {}).get("imageUrl")) or None,
            "confidence": conf, "match_reason": reason + ("" if ed else ", edition not stated"),
            "seen_at": iso_now, "state": "active"}


def settle(li, rec, t):
    """prices.settle for a sealed listing (no printing to check). -> (state, sale row or None)."""
    state, sale = prices.settle(dict(li, printing="", edition=li.get("edition") or ""), rec, t)
    if not sale:
        return state, None
    row = {k: li.get(k) for k in ("product_id", "title", "currency", "edition", "bids", "url", "image_url",
                                   "confidence", "match_reason", "external_id")}
    row.update(sale, source="eBay")
    row["status"] = "pending"                      # David OKs every sealed sale (no auto-approve)
    return state, row
