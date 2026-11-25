import json
from pathlib import Path

import export_cards
from match import Matcher, norm_num
from settings import LOT_WORDS

ROOT = Path(__file__).resolve().parent.parent
J = json.loads((ROOT / "public" / "cards.json").read_text())
SETS = [{"id": s["id"], "name": s["name"], "code": s["code"]} for s in J["sets"]]
CARDS = [{"id": f"{c['s']}:{c['n']}", "set_id": c["s"], "number": c["n"], "name": c["name"],
          "printings": c["v"], "editions": [e for e in c["ed"] if e]} for c in J["cards"]]
M = Matcher(CARDS, SETS)


def m(title):
    r = M.match(title, LOT_WORDS)
    return r and (r[0]["id"], r[1], r[3], r[4])


def test_norm():
    assert norm_num("naruto n064 kakashi") == "N-064"
    assert norm_num("J 1002") == "J-1002"
    assert norm_num("N-US-12") == "N-US-012"
    assert norm_num("PR US 5") == "PRUS005"


def test_basic_match():
    cid, conf, printing, ed = m("Naruto CCG Naruto Uzumaki N-001 1st Edition Path to Hokage Diamond Foil")
    assert cid == "1:N-001" and conf >= 0.85 and printing == "Diamond foil" and ed == "1st Edition"


def test_wrong_name_rejected():
    assert m("Naruto CCG Gaara N-001 rare") is None


def test_lots_and_multi_card_skipped():
    assert m("Naruto CCG lot of 50 cards N-001") is None
    assert m("Naruto CCG N-001 Naruto Uzumaki + N-002 Sasuke Uchiha") is None


def test_grades_not_numbers():
    assert norm_num("PSA 10 GEM MINT CGC 9") is None


def test_export_keeps_format():
    sets = [{"id": "1", "name": "X", "code": None, "released": None, "foils": [], "first_edition": "Yes",
             "unlimited": "Yes", "notes": None, "card_count": 1, "rarity_counts": {"Rare": 1, "Common": 2},
             "kind": "Main", "sort": 0, "source": "RetroTCG"}]
    cards = [{"id": "1:N-001", "set_id": "1", "number": "N-001", "name": "A", "type": "Ninja", "rarity": "Rare",
              "rarity_code": "R", "printings": ["Normal"], "editions": [], "note": None, "sort": 0}]
    scans = [{"id": 1, "card_id": "1:N-001", "public": True, "quality": "placeholder", "printing": "Normal",
              "image_url": "storage:scans/ebay/1_N-001/9.jpg"},
             {"id": 2, "card_id": "1:N-001", "public": True, "quality": "slab", "printing": "Normal",
              "image_url": "storage:scans/psa/1.jpg"},
             {"id": 3, "card_id": "1:N-001", "public": False, "quality": "clean", "image_url": "x"}]
    out = export_cards.build(sets, cards, scans, lambda p: "U/" + p)
    assert out["sets"][0]["rar"] == {"Common": 2, "Rare": 1} and out["sets"][0]["code"] == ""
    assert out["cards"][0]["ed"] == [""] and out["cards"][0]["img"] == "U/psa/1.jpg"
    assert list(out["cards"][0]) == ["s", "n", "name", "t", "r", "src", "v", "ed", "img"]


def test_bare_number_needs_full_name():
    r = M.match("Naruto CCG The Third Hokage 968 S19 1st Edition Super Rare Foil", LOT_WORDS, allow_bare=True)
    assert r and r[0]["id"] == "19:N-968" and r[4] == "1st Edition"
    assert M.match("Naruto CCG 2006 Bandai Kakashi Hatake card", LOT_WORDS, allow_bare=True) is None
    assert M.match("Naruto CCG The Third Hokage 968", LOT_WORDS) is None     # off unless asked
