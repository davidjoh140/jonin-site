"""Runs find_scans.main() against fake eBay / PSA / Supabase to check the whole flow."""
import io
import json
from pathlib import Path

from PIL import Image

import find_scans
import supa

J = json.loads((Path(__file__).resolve().parent.parent / "public" / "cards.json").read_text())
SETS = [{"id": s["id"], "name": s["name"], "code": s["code"]} for s in J["sets"]]
CARDS = [{"id": f"{c['s']}:{c['n']}", "set_id": c["s"], "number": c["n"], "name": c["name"],
          "printings": c["v"], "editions": [e for e in c["ed"] if e]} for c in J["cards"]]


class R:
    def __init__(self, data=None, status=200, content=b""):
        self._d, self.status_code, self.content = data, status, content

    def json(self):
        return self._d

    def raise_for_status(self):
        assert self.status_code < 400


def jpeg():
    b = io.BytesIO()
    Image.new("RGB", (750, 1050), "orange").save(b, "JPEG")
    return b.getvalue()


ITEMS = [
    {"itemId": "v1|1|0", "title": "Naruto CCG Naruto Uzumaki N-001 1st Edition Diamond Foil",
     "image": {"imageUrl": "https://i.ebayimg.com/images/g/a/s-l225.jpg"}, "itemWebUrl": "https://ebay.com/itm/1",
     "seller": {"username": "ninjashop"}},
    {"itemId": "v1|2|0", "title": "Naruto CCG Sasuke Uchiha N-002 PSA 10 Path to Hokage",
     "image": {"imageUrl": "https://i.ebayimg.com/images/g/b/s-l225.jpg"}, "itemWebUrl": "https://ebay.com/itm/2"},
    {"itemId": "v1|3|0", "title": "Naruto CCG lot of 100 cards N-003", "image": {"imageUrl": "x"}},
    {"itemId": "v1|4|0", "title": "Naruto CCG Gaara N-001", "image": {"imageUrl": "x"}},
]


def test_flow(monkeypatch):
    inserted, uploads, gets = [], [], []
    monkeypatch.setenv("EBAY_CLIENT_ID", "id")
    monkeypatch.setenv("EBAY_CLIENT_SECRET", "s")
    monkeypatch.setenv("PSA_TOKEN", "t")
    monkeypatch.setenv("SET_FILTER", "1")
    tables = {"sets": SETS, "cards": CARDS, "scan_candidates": [], "scans": [], }
    monkeypatch.setattr(supa, "select", lambda t, p=None: tables[t])
    monkeypatch.setattr(supa, "insert", lambda t, rows, **k: inserted.extend((t, r) for r in rows) or [{"id": 1}])
    monkeypatch.setattr(supa, "update", lambda *a: None)
    monkeypatch.setattr(supa, "upload", lambda b, p, d, **k: uploads.append(p))

    def get(url, params=None, headers=None, timeout=None):
        gets.append(url)
        if "item_summary/search" in url:
            return R({"itemSummaries": ITEMS if params["offset"] == 0 else []})
        if "/buy/browse/v1/item/" in url:
            return R({"localizedAspects": [{"name": "Professional Grader", "value": "Professional Sports Authenticator (PSA)"},
                                           {"name": "Certification Number", "value": "87654321"}]})
        if "GetByCertNumber" in url:
            return R({"PSACert": {"CardNumber": "N-002", "Subject": "SASUKE UCHIHA"}})
        if "GetImagesByCertNumber" in url:
            return R([{"IsFrontImage": True, "ImageURL": "https://psa.example/front.jpg"}])
        return R(content=jpeg())

    monkeypatch.setattr(find_scans.requests, "get", get)
    monkeypatch.setattr(find_scans.requests, "post", lambda *a, **k: R({"access_token": "tok"}))
    monkeypatch.setattr(find_scans.time, "sleep", lambda s: None)
    find_scans.main()
    cands = [r for t, r in inserted if t == "scan_candidates"]
    assert [(c["card_id"], c["source"], c["quality"]) for c in cands] == [
        ("1:N-001", "eBay listing", "placeholder"), ("1:N-002", "PSA", "slab")]
    assert cands[0]["printing"] == "Diamond foil" and cands[0]["edition"] == "1st Edition"
    assert cands[0]["thumb_b64"] and uploads[0].startswith("ebay/1_N-001/")
    assert "https://i.ebayimg.com/images/g/a/s-l1600.jpg" in gets
