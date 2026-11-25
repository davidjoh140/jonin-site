"""Move Card Index scan images from the scan_uploads staging table into Storage + the scans table.

The Card Index page (claude.ai artifact) can't reach Storage directly, so it writes each scan image
as base64 into scan_uploads through the Supabase connector. This job (run by the sync-cards workflow)
uploads each one to the public 'scans' bucket, upserts its scans row (keyed by ci_doc = Card Index
doc id) and deletes the staging row. Rows whose card isn't in the card list keep an error and stay.
"""
import base64
import re

import requests

import supa

BATCH = 25


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")


def path_for(row):
    set_id, number = row["card_id"].split(":", 1)
    return f"ci/{slug(set_id)}/{slug(number)}~{slug(row['printing'])}-{slug(row.get('edition'))}-{row['asset'][:8]}.webp"


def staged_ids():
    return [r["doc_id"] for r in supa.select("scan_uploads", {"select": "doc_id", "error": "is.null"})]


def fetch(ids):
    inn = ",".join('"%s"' % i.replace('"', '') for i in ids)
    r = requests.get(f"{supa.URL}/rest/v1/scan_uploads", params={"select": "*", "doc_id": f"in.({inn})"},
                     headers=supa._h(), timeout=120)
    r.raise_for_status()
    return r.json()


def upsert_scan(row, path):
    rec = {"card_id": row["card_id"], "printing": row["printing"], "edition": row.get("edition"),
           "image_url": f"storage:scans/{path}", "source": f"card-index:{row.get('source') or 'Online'}",
           "public": True, "quality": "clean", "ci_doc": row["doc_id"], "ci_asset": row["asset"]}
    r = requests.post(f"{supa.URL}/rest/v1/scans", params={"on_conflict": "ci_doc"}, json=[rec],
                      headers=supa._h({"Content-Type": "application/json",
                                       "Prefer": "resolution=merge-duplicates,return=minimal"}), timeout=60)
    return r


def delete(doc_id):
    requests.delete(f"{supa.URL}/rest/v1/scan_uploads", params={"doc_id": f"eq.{doc_id}"},
                    headers=supa._h(), timeout=60).raise_for_status()


def main():
    with supa.Run("drain_uploads") as run:
        ids = staged_ids()
        done = failed = 0
        for i in range(0, len(ids), BATCH):
            for row in fetch(ids[i:i + BATCH]):
                try:
                    path = path_for(row)
                    supa.upload("scans", path, base64.b64decode(row["b64"]), "image/webp")
                    r = upsert_scan(row, path)
                    if r.status_code >= 300:
                        raise RuntimeError(f"scans upsert {r.status_code}: {r.text[:200]}")
                    delete(row["doc_id"])
                    done += 1
                except Exception as e:
                    failed += 1
                    supa.update("scan_uploads", {"doc_id": row["doc_id"]}, {"error": str(e)[:500]})
        run.stats.update(staged=len(ids), done=done, failed=failed)
        print(f"drained {done}, failed {failed}, of {len(ids)}")


if __name__ == "__main__":
    main()
