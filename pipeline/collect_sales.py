"""Record Naruto CCG sold prices from eBay into Supabase (sales), and rebuild the free price ranges.

How it works (runs every 15 minutes from GitHub Actions):
  1. Every run re-reads auctions ending soon, so we know their bid right before the end.
  2. About once an hour it re-reads every Naruto listing (Buy It Now and auctions).
  3. Each listing is matched to one exact card version: card + printing + edition + grade.
  4. When a listing ends it is "settled":
       - with EBAY_REFRESH_TOKEN set, eBay's own record says whether it sold and for how much;
       - without it, an auction with bids counts at the last bid we saw, and a Buy It Now that
         vanished is not counted (it may have been pulled, not sold).
  5. Confident sales go straight into the public range; the rest wait in `sales` as pending.

Env: SUPABASE_URL, SUPABASE_SERVICE_KEY, EBAY_CLIENT_ID, EBAY_CLIENT_SECRET,
     EBAY_REFRESH_TOKEN (optional, a user token for eBay's Trading API GetItem).
"""
import os
import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

import requests

import prices
import settings as cfg
import supa
from find_scans import EBAY, Budget, OutOfCalls, big, ebay_token
from match import Matcher

TRADING = "https://api.ebay.com/ws/api.dll"
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
    hit = matcher.match(title, cfg.LOT_WORDS)
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
    notes = [reason] + (["assumed Normal"] if ap else []) + (["assumed Unlimited"] if ae else [])
    return {"external_id": f"ebay:{it['itemId']}", "card_id": card["id"], "title": title,
            "price": float(price.get("value") or 0), "currency": "USD", "grader": grader, "grade": grade,
            "printing": printing, "edition": edition, "kind": "AUCTION" if auction else "FIXED_PRICE",
            "bids": it.get("bidCount") or 0, "best_offer": "BEST_OFFER" in opts,
            "ends_at": it.get("itemEndDate"), "source": "eBay", "url": it.get("itemWebUrl"),
            "image_url": big((it.get("image") or {}).get("imageUrl")) or None,
            "confidence": conf, "match_reason": ", ".join(notes), "seen_at": iso(t), "state": "active"}


def user_token():
    rt = os.environ.get("EBAY_REFRESH_TOKEN")
    if not rt:
        return None
    r = requests.post(f"{EBAY}/identity/v1/oauth2/token",
                      auth=(os.environ["EBAY_CLIENT_ID"], os.environ["EBAY_CLIENT_SECRET"]),
                      data={"grant_type": "refresh_token", "refresh_token": rt,
                            "scope": "https://api.ebay.com/oauth/api_scope"}, timeout=30)
    r.raise_for_status()
    return r.json()["access_token"]


def ebay_record(utok, external_id):
    """eBay's own record of a finished listing via Trading API GetItem (works up to 90 days after it ends)."""
    legacy = external_id.split("|")[1] if "|" in external_id else external_id.split(":")[-1]
    body = (f'<?xml version="1.0" encoding="utf-8"?><GetItemRequest xmlns="urn:ebay:apis:eBLBaseComponents">'
            f'<ItemID>{legacy}</ItemID><DetailLevel>ReturnAll</DetailLevel></GetItemRequest>')
    r = requests.post(TRADING, data=body.encode(), timeout=60, headers={
        "X-EBAY-API-CALL-NAME": "GetItem", "X-EBAY-API-SITEID": "0", "X-EBAY-API-COMPATIBILITY-LEVEL": "1349",
        "X-EBAY-API-IAF-TOKEN": utok, "Content-Type": "text/xml"})
    if r.status_code != 200:
        return None
    x = ET.fromstring(r.content)
    item = x.find("e:Item", NS)
    if item is None:
        return None
    st = item.find("e:SellingStatus", NS)
    if st is None or st.findtext("e:ListingStatus", default="", namespaces=NS) == "Active":
        return None                     # not finished yet
    qty = int(st.findtext("e:QuantitySold", default="0", namespaces=NS) or 0)
    price = float(st.findtext("e:CurrentPrice", default="0", namespaces=NS) or 0)
    bo = item.findtext("e:BestOfferDetails/e:BestOfferEnabled", default="false", namespaces=NS) == "true"
    auction = item.findtext("e:ListingType", default="", namespaces=NS) == "Chinese"
    return {"sold": qty > 0, "price": price, "qty_sold": qty, "best_offer_accepted": bo and not auction}


def last_full_sweep():
    rows = supa.select("pipeline_runs", {"select": "started_at,stats", "job": "eq.collect_sales",
                                         "error": "is.null", "order": "started_at.desc", "limit": "50"})
    for r in rows:
        if (r.get("stats") or {}).get("full"):
            return datetime.fromisoformat(r["started_at"].replace("Z", "+00:00"))
    return None


def main():
    with supa.Run("collect_sales") as run:
        t = now()
        stats = run.stats = {"full": False, "seen": 0, "matched": 0, "ended": 0, "sold": 0, "approved": 0,
                             "pending": 0, "unsold": 0, "gone": 0, "confirmed_by_ebay": 0}
        matcher = Matcher(supa.select("cards"), supa.select("sets"))
        tok = ebay_token()
        budget = Budget(cfg.SALES_MAX_CALLS_PER_RUN)
        rows, seen_ids = {}, set()
        last = last_full_sweep()
        full = last is None or t - last >= timedelta(minutes=cfg.SALES_FULL_SWEEP_MINUTES - 5)
        window = f"buyingOptions:{{AUCTION}},itemEndDate:[{iso(t)}..{iso(t + timedelta(minutes=cfg.SALES_ENDING_WINDOW_MINUTES))}]"
        try:
            for q in cfg.SALES_QUERIES:                       # 1. auctions ending soon
                for it in search(tok, q, budget, 2, window):
                    stats["seen"] += 1
                    row = to_listing(it, matcher, t)
                    if row:
                        rows[row["external_id"]] = row
            if full:                                          # 2. everything, about hourly
                for q in cfg.SALES_QUERIES:
                    for it in search(tok, q, budget, cfg.SALES_PAGES_PER_QUERY):
                        stats["seen"] += 1
                        seen_ids.add(f"ebay:{it['itemId']}")
                        row = to_listing(it, matcher, t)
                        if row:
                            rows[row["external_id"]] = row
                stats["full"] = True
        except OutOfCalls:
            stats["stopped"] = "call budget used up"
            full = stats["full"] = False                      # an incomplete sweep can't say what vanished
        stats["matched"] = len(rows)
        batch = list(rows.values())
        for i in range(0, len(batch), 500):
            supa.upsert("listings", batch[i:i + 500], "external_id")

        # 3. settle listings that ended
        active = supa.select("listings", {"select": "*", "state": "eq.active"})
        ended = []
        for li in active:
            ends = datetime.fromisoformat(li["ends_at"].replace("Z", "+00:00")) if li.get("ends_at") else None
            if li["kind"] == "AUCTION" and ends and ends < t - timedelta(minutes=2):
                ended.append(li)
            elif li["kind"] != "AUCTION" and ((ends and ends < t) or (full and li["external_id"] not in seen_ids)):
                ended.append(li)
        utok = None
        try:
            utok = user_token()
        except Exception as e:
            print("eBay user token failed, settling without it:", e)
        for li in ended[:cfg.SALES_MAX_SETTLE_PER_RUN]:
            stats["ended"] += 1
            rec = None
            if utok:
                try:
                    rec = ebay_record(utok, li["external_id"])
                    time.sleep(0.2)
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
                                               "match_reason", "external_id")}
                row.update(sale, source="eBay")
                supa.insert("sales", [row], ignore_duplicates=True, returning=False)
                stats[sale["status"]] += 1
            supa.update("listings", {"external_id": li["external_id"]}, {"state": state})
        stats["ranges"] = supa.rpc("refresh_price_ranges")
        print(stats)


if __name__ == "__main__":
    main()
