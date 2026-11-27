"""Record Naruto CCG sold prices from eBay into Supabase (sales), and rebuild the free price ranges.

How it works (runs every 15 minutes from GitHub Actions):
  1. Every run re-reads auctions ending soon, so we know their bid right before the end.
  2. About once an hour it re-reads every Naruto listing (Buy It Now and auctions).
  3. Each listing is matched to one exact card version: card + printing + edition + grade.
  4. When a listing ends it is "settled":
       - with EBAY_REFRESH_TOKEN set, eBay's own record says whether it sold and for how much;
       - without it, an auction with bids counts at the last bid we saw, and a Buy It Now that
         vanished is queued at its listed price as "unconfirmed" (it may have been pulled, not sold).
  5. Every sale waits in `sales` as pending until David OKs or vetoes it in the Buying Desk
     (settings.SALES_AUTO_APPROVE_CONFIDENCE = None). Only OK'd sales reach the public range.

Env: SUPABASE_URL, SUPABASE_SERVICE_KEY, EBAY_CLIENT_ID, EBAY_CLIENT_SECRET,
     EBAY_AUTH_TOKEN or EBAY_REFRESH_TOKEN (optional, a user token for eBay's Trading API GetItem).
"""
import os
import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

import requests

import prices
import sealed
import settings as cfg
import supa
from find_scans import EBAY, Budget, OutOfCalls, big, ebay_token, fetch_image
from match import Matcher

TRADING = "https://api.ebay.com/ws/api.dll"


class TokenError(Exception):
    pass
NS = {"e": "urn:ebay:apis:eBLBaseComponents"}


def now():
    return datetime.now(timezone.utc)


def iso(d):
    return d.strftime("%Y-%m-%dT%H:%M:%S.000Z")


def search(tok, q, budget, pages, flt=None):
    params = {"q": q, "limit": 200}
    if flt:
        params["filter"] = flt
    for p in range(pages):
        budget.spend()
        params["offset"] = p * 200
        r = requests.get(f"{EBAY}/buy/browse/v1/item_summary/search", params=params,
                         headers={"Authorization": f"Bearer {tok}", "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"}, timeout=60)
        r.raise_for_status()
        items = r.json().get("itemSummaries", [])
        yield from items
        if len(items) < 200:
            return


def to_listing(it, matcher, t):
    """A Browse item summary -> a listings row, or None if it isn't one clear single card."""
    title = it.get("title", "")
    if prices.skip_title(title):
        return None
    hit = matcher.match(title, cfg.LOT_WORDS, allow_bare=True)
    if not hit or hit[1] < cfg.MIN_CONFIDENCE:
        return None
    card, conf, reason, printing_m, _ = hit
    printing, ap = prices.parse_printing(title, card, printing_m)
    edition, ae = prices.parse_edition(title, card)
    grader, grade = prices.parse_grade(title)
    opts = it.get("buyingOptions") or []
    auction = "AUCTION" in opts
    price = (it.get("currentBidPrice") if auction else it.get("price")) or it.get("price") or {}
    if price.get("currency", "USD") != "USD":
        return None
    cond, csrc = it.get("_condition") or prices.parse_condition(title)
    notes = [reason] + (["assumed Normal"] if ap else []) + (["assumed Unlimited"] if ae else [])
    return {"external_id": f"ebay:{it['itemId']}", "card_id": card["id"], "title": title,
            "price": float(price.get("value") or 0), "currency": "USD", "grader": grader, "grade": grade,
            "printing": printing, "edition": edition, "kind": "AUCTION" if auction else "FIXED_PRICE",
            "bids": it.get("bidCount") or 0, "best_offer": "BEST_OFFER" in opts,
            "ends_at": it.get("itemEndDate"), "source": "eBay", "url": it.get("itemWebUrl"),
            "image_url": big((it.get("image") or {}).get("imageUrl")) or None,
            "confidence": conf, "match_reason": ", ".join(notes), "seen_at": iso(t), "state": "active",
            "condition": cond, "condition_source": csrc}


def user_token():
    """A token for Trading API GetItem: an Auth'n'Auth token (EBAY_AUTH_TOKEN, lasts ~18 months)
    or an OAuth refresh token (EBAY_REFRESH_TOKEN) exchanged for a short-lived access token."""
    if os.environ.get("EBAY_AUTH_TOKEN"):
        return ("authnauth", os.environ["EBAY_AUTH_TOKEN"])
    try:   # kept in Supabase app_secrets (no public access) when it can't be a GitHub secret
        row = supa.select("app_secrets", {"select": "value", "name": "eq.ebay_auth_token"})
        if row and row[0].get("value"):
            return ("authnauth", row[0]["value"])
    except Exception as e:
        print("could not read app_secrets:", e)
    rt = os.environ.get("EBAY_REFRESH_TOKEN")
    if not rt:
        return None
    r = requests.post(f"{EBAY}/identity/v1/oauth2/token",
                      auth=(os.environ["EBAY_CLIENT_ID"], os.environ["EBAY_CLIENT_SECRET"]),
                      data={"grant_type": "refresh_token", "refresh_token": rt,
                            "scope": "https://api.ebay.com/oauth/api_scope"}, timeout=30)
    r.raise_for_status()
    return ("oauth", r.json()["access_token"])


def ebay_record(utok, external_id):
    """eBay's own record of a finished listing via Trading API GetItem (works up to 90 days after it ends)."""
    got = ebay_item(utok, external_id)
    return got and got["record"]


def ebay_item(utok, external_id):
    """GetItem -> {"record": {...} or None while live, "summary": Browse-style item summary} or None."""
    legacy = external_id.split("|")[1] if "|" in external_id else external_id.split(":")[-1]
    kind, token = utok
    creds = (f"<RequesterCredentials><eBayAuthToken>{token}</eBayAuthToken></RequesterCredentials>"
             if kind == "authnauth" else "")
    body = (f'<?xml version="1.0" encoding="utf-8"?><GetItemRequest xmlns="urn:ebay:apis:eBLBaseComponents">'
            f'{creds}<ItemID>{legacy}</ItemID><DetailLevel>ReturnAll</DetailLevel></GetItemRequest>')
    headers = {"X-EBAY-API-CALL-NAME": "GetItem", "X-EBAY-API-SITEID": "0",
               "X-EBAY-API-COMPATIBILITY-LEVEL": "1349", "Content-Type": "text/xml"}
    if kind == "oauth":
        headers["X-EBAY-API-IAF-TOKEN"] = token
    else:
        headers["X-EBAY-API-APP-NAME"] = os.environ.get("EBAY_CLIENT_ID", "")
    r = requests.post(TRADING, data=body.encode(), timeout=60, headers=headers)
    if r.status_code != 200:
        return None
    x = ET.fromstring(r.content)
    err = x.find("e:Errors", NS)
    if err is not None and x.findtext("e:Ack", default="", namespaces=NS) == "Failure":
        code = err.findtext("e:ErrorCode", default="", namespaces=NS)
        if code in ("931", "932", "16110", "21916984", "21917053"):   # token invalid / expired / revoked
            raise TokenError(err.findtext("e:LongMessage", default=code, namespaces=NS))
        return None
    item = x.find("e:Item", NS)
    if item is None:
        return None
    f = lambda path, d="": item.findtext(path, default=d, namespaces=NS)
    st = item.find("e:SellingStatus", NS)
    qty = int(f("e:SellingStatus/e:QuantitySold", "0") or 0)
    price = float(f("e:SellingStatus/e:CurrentPrice", "0") or 0)
    cur = st.find("e:CurrentPrice", NS).get("currencyID", "USD") if st is not None and st.find("e:CurrentPrice", NS) is not None else "USD"
    bo = f("e:BestOfferDetails/e:BestOfferEnabled", "false") == "true"
    auction = f("e:ListingType") == "Chinese"
    pics = item.findall("e:PictureDetails/e:PictureURL", NS)
    summary = {"itemId": f"v1|{legacy}|0", "title": f("e:Title"), "itemEndDate": f("e:ListingDetails/e:EndTime") or None,
               "buyingOptions": ["AUCTION"] if auction else ["FIXED_PRICE"] + (["BEST_OFFER"] if bo else []),
               "bidCount": int(f("e:SellingStatus/e:BidCount", "0") or 0),
               ("currentBidPrice" if auction else "price"): {"value": str(price), "currency": cur},
               "itemWebUrl": f("e:ListingDetails/e:ViewItemURL") or f"https://www.ebay.com/itm/{legacy}",
               "image": {"imageUrl": pics[0].text if pics else ""}}
    desc = {}
    for d in item.findall("e:ConditionDescriptors/e:ConditionDescriptor", NS):
        desc[d.findtext("e:Name", default="", namespaces=NS)] = d.findtext("e:Value", default="", namespaces=NS)
    html = f("e:Description")
    text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", html)))[:5000]
    cond, src = prices.parse_condition(summary["title"], desc.get("40001"), text)
    summary["_condition"] = (cond, src)
    live = st is None or f("e:SellingStatus/e:ListingStatus") == "Active"
    record = None if live else {"sold": qty > 0, "price": price, "qty_sold": qty,
                                "best_offer_accepted": bo and not auction}
    return {"record": record, "summary": summary}


def fill_thumbs(limit=200, table="sales"):
    """Save a small copy of each waiting sale's listing photo, so the Buying Desk can show it
    (the Buying Desk page can't load images from eBay directly)."""
    rows = supa.select(table, {"select": "id,image_url", "status": "eq.pending", "thumb_b64": "is.null",
                                 "image_url": "not.is.null", "limit": str(limit)})
    done = 0
    for r in rows[:limit]:
        url = re.sub(r"\$_\d+\.(JPG|jpg|PNG|png)", r"$_57.\1", big(r["image_url"]))   # ask eBay for a larger copy
        try:
            _, thumb = fetch_image(url)
        except Exception as e:
            print("photo failed for sale", r["id"], e)
            thumb = ""                                # don't retry forever
        supa.update(table, {"id": r["id"]}, {"thumb_b64": thumb})
        done += 1
    return done


def last_full_sweep():
    rows = supa.select("pipeline_runs", {"select": "started_at,stats", "job": "eq.collect_sales",
                                         "error": "is.null", "order": "started_at.desc", "limit": "50"})
    for r in rows:
        if (r.get("stats") or {}).get("full"):
            return datetime.fromisoformat(r["started_at"].replace("Z", "+00:00"))
    return None


def settle_sealed(t, full, stats, utok):
    """Ended sealed listings -> pending sealed_sales (same rules as cards), then the sealed price ranges."""
    active = supa.select("sealed_listings", {"select": "*", "state": "eq.active"})
    can_vanish = full and stats.get("sealed_complete") and stats.get("complete")
    n = {"ended": 0, "sold": 0, "unsold": 0, "gone": 0}
    for li in active:
        ends = datetime.fromisoformat(li["ends_at"].replace("Z", "+00:00")) if li.get("ends_at") else None
        auction = li["kind"] == "AUCTION"
        if not ((auction and ends and ends < t - timedelta(minutes=2)) or
                (not auction and ((ends and ends < t) or (can_vanish and li["seen_at"] and
                 datetime.fromisoformat(li["seen_at"].replace("Z", "+00:00")) < t - timedelta(minutes=5))))):
            continue
        if n["ended"] >= 60:                                  # PLACEHOLDER: sealed lookups per run
            break
        n["ended"] += 1
        rec = None
        if utok:
            try:
                got = ebay_item(utok, li["external_id"])
                rec = got and got["record"]
                time.sleep(0.2)
            except Exception as e:
                print("GetItem failed for sealed", li["external_id"], e)
            if rec is None and not auction and not (ends and ends < t):
                continue                                      # still live, just missing from search
        state, sale = sealed.settle(li, rec, t)
        n[state] = n.get(state, 0) + 1
        if sale:
            supa.insert("sealed_sales", [sale], ignore_duplicates=True, returning=False)
        supa.update("sealed_listings", {"external_id": li["external_id"]}, {"state": state})
    n["thumbs"] = fill_thumbs(table="sealed_sales", limit=60)
    n["ranges"] = supa.rpc("refresh_sealed_prices")
    stats["sealed"] = n


def main():
    with supa.Run("collect_sales") as run:
        t = now()
        stats = run.stats = {"full": False, "seen": 0, "matched": 0, "ended": 0, "sold": 0, "approved": 0,
                             "pending": 0, "unsold": 0, "gone": 0, "confirmed_by_ebay": 0}
        matcher = Matcher(supa.select("cards"), supa.select("sets"))
        tok = ebay_token()
        budget = Budget(cfg.SALES_MAX_CALLS_PER_RUN)
        rows, seen_ids = {}, set()
        srows = {}                                            # sealed listings (sealed.py)
        try:
            products = supa.select("products")
            sets_all = supa.select("sets")
        except Exception as e:                                # sealed must never stop card prices
            print("sealed catalog failed to load:", e)
            products, sets_all = [], []

        def take(it):
            """Sealed product first, else a single card."""
            if products:
                try:
                    sr = sealed.to_listing(it, products, sets_all, iso(t))
                except Exception as e:
                    print("sealed match failed:", e)
                    sr = None
                if sr:
                    srows[sr["external_id"]] = sr
                    return
            row = to_listing(it, matcher, t)
            if row:
                rows[row["external_id"]] = row
        last = last_full_sweep()
        full = last is None or t - last >= timedelta(minutes=cfg.SALES_FULL_SWEEP_MINUTES - 5)
        window = f"buyingOptions:{{AUCTION}},itemEndDate:[{iso(t)}..{iso(t + timedelta(minutes=cfg.SALES_ENDING_WINDOW_MINUTES))}]"
        try:
            for q in cfg.SALES_QUERIES:                       # 1. auctions ending soon
                for it in search(tok, q, budget, 2, window):
                    stats["seen"] += 1
                    take(it)
            if full:                                          # 2. everything, about hourly
                complete = True
                for q in cfg.SALES_QUERIES:
                    got = 0
                    for it in search(tok, q, budget, cfg.SALES_PAGES_PER_QUERY):
                        got += 1
                        stats["seen"] += 1
                        seen_ids.add(f"ebay:{it['itemId']}")
                        take(it)
                    if got >= cfg.SALES_PAGES_PER_QUERY * 200:
                        complete = False              # more results than we read: can't tell what vanished
                sealed_complete = complete
                for q in (cfg.SEALED_QUERIES if products else []):   # sealed: a few narrow searches
                    got = 0
                    for it in search(tok, q, budget, cfg.SEALED_PAGES_PER_QUERY):
                        got += 1
                        stats["seen"] += 1
                        seen_ids.add(f"ebay:{it['itemId']}")
                        take(it)
                    if got >= cfg.SEALED_PAGES_PER_QUERY * 200:
                        sealed_complete = False
                stats["sealed_complete"] = sealed_complete
                stats["full"] = True
                stats["complete"] = complete
        except OutOfCalls:
            stats["stopped"] = "call budget used up"
            full = stats["full"] = False                      # an incomplete sweep can't say what vanished
        stats["matched"] = len(rows)
        stats["sealed_matched"] = len(srows)
        batch = list(rows.values())
        for i in range(0, len(batch), 500):
            supa.upsert_skipping_conflicts("listings", batch[i:i + 500], "external_id")
        try:
            sb = list(srows.values())
            for i in range(0, len(sb), 500):
                supa.upsert("sealed_listings", sb[i:i + 500], "external_id")
        except Exception as e:
            stats["sealed_error"] = f"listings: {e}"[:200]

        # 3. settle listings that ended
        active = supa.select("listings", {"select": "*", "state": "eq.active"})
        ended = []
        for li in active:
            ends = datetime.fromisoformat(li["ends_at"].replace("Z", "+00:00")) if li.get("ends_at") else None
            if li["kind"] == "AUCTION" and ends and ends < t - timedelta(minutes=2):
                ended.append(li)
            elif li["kind"] != "AUCTION" and ((ends and ends < t) or (full and stats.get("complete") and li["external_id"] not in seen_ids)):
                ended.append(li)
        utok = None
        try:
            utok = user_token()
        except Exception as e:
            print("eBay user token failed, settling without it:", e)
        if utok:                                              # quick check that eBay accepts the token
            probe = next((li for li in active if li["kind"] == "FIXED_PRICE"), None)
            try:
                if probe:
                    ebay_record(utok, probe["external_id"])
                stats["ebay_token"] = "ok"
            except TokenError as e:
                stats["ebay_token"] = f"rejected: {e}"[:200]
                utok = None
            except Exception as e:
                stats["ebay_token"] = f"check failed: {e}"[:200]
        else:
            stats["ebay_token"] = "none"
        for li in ended[:cfg.SALES_MAX_SETTLE_PER_RUN]:
            stats["ended"] += 1
            rec = None
            if utok:
                try:
                    got = ebay_item(utok, li["external_id"])
                    rec = got and got["record"]
                    if got and got["summary"].get("_condition"):
                        cond, csrc = got["summary"]["_condition"]
                        if cond != prices.UNKNOWN or not li.get("condition"):
                            li["condition"], li["condition_source"] = cond, csrc
                    time.sleep(0.2)
                except TokenError as e:
                    stats["ebay_token"] = f"rejected: {e}"[:200]
                    utok = None
                except Exception as e:
                    print("GetItem failed for", li["external_id"], e)
                if rec is None and li["kind"] != "AUCTION" and not (li.get("ends_at") and
                        datetime.fromisoformat(li["ends_at"].replace("Z", "+00:00")) < t):
                    continue                                  # still live on eBay, just missing from search
            state, sale = prices.settle(li, rec, t)
            if rec is not None:
                stats["confirmed_by_ebay"] += 1
            stats[state] += 1
            if sale:
                row = {k: li.get(k) for k in ("card_id", "title", "currency", "grader", "grade", "printing",
                                               "edition", "bids", "url", "image_url", "confidence",
                                               "match_reason", "external_id", "condition", "condition_source")}
                row.update(sale, source="eBay")
                supa.insert("sales", [row], ignore_duplicates=True, returning=False)
                stats[sale["status"]] += 1
            supa.update("listings", {"external_id": li["external_id"]}, {"state": state})
        try:
            settle_sealed(t, full, stats, utok)
        except Exception as e:                                # sealed must never stop card prices
            stats["sealed_error"] = f"settle: {e}"[:200]
        stats["thumbs"] = fill_thumbs()
        stats["ranges"] = supa.rpc("refresh_price_ranges")
        print(stats)


if __name__ == "__main__":
    main()
