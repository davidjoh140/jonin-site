"""One-off backlog: queue sales eBay already completed, from item numbers in backfill_ids.txt.

For each item eBay's GetItem gives the title, sold status, final price and end time. Items that
match one exact card version are saved like any tracked listing and settled, so they land in
`sales` as pending for David's OK in the Buying Desk. Already-recorded items are skipped.

Env: SUPABASE_URL, SUPABASE_SERVICE_KEY, EBAY_CLIENT_ID (+ the eBay token in app_secrets or env).
"""
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import prices
import supa
from collect_sales import TokenError, ebay_item, iso, to_listing, user_token
from match import Matcher


def ids():
    text = (Path(__file__).parent / "backfill_ids.txt").read_text()
    lines = [l for l in text.splitlines() if not l.startswith("#")]
    return list(dict.fromkeys(re.findall(r"\b\d{9,16}\b", " ".join(lines))))


def main():
    with supa.Run("backfill_sales") as run:
        t = datetime.now(timezone.utc)
        stats = run.stats = {"ids": 0, "skipped_known": 0, "not_found": 0, "no_match": 0, "still_live": 0,
                             "unsold": 0, "queued": 0}
        utok = user_token()
        if not utok:
            raise SystemExit("no eBay token")
        matcher = Matcher(supa.select("cards"), supa.select("sets"))
        known = {r["external_id"] for r in supa.select("sales", {"select": "external_id"}) if r.get("external_id")}
        todo = ids()
        stats["ids"] = len(todo)
        for legacy in todo:
            ext = f"ebay:v1|{legacy}|0"
            if ext in known:
                stats["skipped_known"] += 1
                continue
            try:
                got = ebay_item(utok, ext)
            except TokenError as e:
                stats["stopped"] = f"eBay token rejected: {e}"[:200]
                break
            time.sleep(0.2)
            if not got:
                stats["not_found"] += 1
                continue
            row = to_listing(got["summary"], matcher, t)
            if not row:
                stats["no_match"] += 1
                continue
            if got["record"] is None:
                stats["still_live"] += 1
                continue
            row["seen_at"] = iso(t)
            state, sale = prices.settle(row, got["record"], t)
            row["state"] = state
            supa.upsert("listings", [row], "external_id")
            if not sale:
                stats["unsold"] += 1
                continue
            out = {k: row.get(k) for k in ("card_id", "title", "currency", "grader", "grade", "printing", "edition",
                                            "bids", "url", "image_url", "confidence", "match_reason", "external_id")}
            out.update(sale, source="eBay", status="pending")
            supa.insert("sales", [out], ignore_duplicates=True, returning=False)
            stats["queued"] += 1
        print(stats)


if __name__ == "__main__":
    main()
