from datetime import datetime, timedelta, timezone

import sealed

SETS = [{"id": "1", "name": "The Path to Hokage", "kind": "Main"}, {"id": "9", "name": "The Chosen", "kind": "Main"},
        {"id": "25", "name": "Kage's Summit", "kind": "Main"}, {"id": "4", "name": "Revenge and Rebirth", "kind": "Main"},
        {"id": "12", "name": "A New Chronicle", "kind": "Main"}, {"id": "3", "name": "Curse of the Sand", "kind": "Main"},
        {"id": "T3", "name": "Ultimate Battle (tin)", "kind": "Tin"}, {"id": "TP1", "name": "Tournament Pack 1", "kind": "Tournament pack"}]
P = [{"id": f"{s}-booster-{k}", "set_id": s, "kind": f"booster_{k}", "match_words": []} for s in ("1", "9", "25", "4", "12", "3") for k in ("pack", "box")]
P += [{"id": "9-galeA", "set_id": "9", "kind": "theme", "match_words": ["gale force a"]},
      {"id": "9-tidal", "set_id": "9", "kind": "theme", "match_words": ["tidal wave"]},
      {"id": "3-gaara", "set_id": "3", "kind": "theme", "match_words": ["gaara"]},
      {"id": "3-naruto", "set_id": "3", "kind": "theme", "match_words": ["naruto"]},
      {"id": "1-starter", "set_id": "1", "kind": "starter", "match_words": []},
      {"id": "t3-tin", "set_id": "T3", "kind": "tin", "match_words": ["ultimate battle"]},
      {"id": "tp1-pack", "set_id": "TP1", "kind": "tournament_pack", "match_words": []}]


def pid(title):
    m = sealed.match(title, P, SETS)
    return m and m[0]["id"]


def test_packs_and_boxes():
    assert pid("Naruto CCG The Path to Hokage Booster Pack Sealed 1st Edition") == "1-booster-pack"
    assert pid("NARUTO CCG PATH TO HOKAGE BOOSTER BOX FACTORY SEALED") == "1-booster-box"
    assert pid("Naruto Kage Summit booster box sealed Bandai") == "25-booster-box"
    assert pid("Naruto CCG Revenge & Rebirth Booster Pack New") == "4-booster-pack"
    assert pid("Naruto CCG Series 12 booster pack sealed") == "12-booster-pack"
    assert pid("Naruto The Chosen sealed box") == "9-booster-box"


def test_decks():
    assert pid("Naruto CCG The Chosen Theme Deck Tidal Wave Sealed") == "9-tidal"
    assert pid("Naruto CCG The Chosen Theme Deck sealed") is None            # two decks, no name: can't tell
    assert pid("Naruto CCG Curse of the Sand Gaara theme deck sealed") == "3-gaara"
    assert pid("Naruto Path to Hokage starter deck sealed") == "1-starter"
    assert pid("Naruto CCG Ultimate Battle Tin Sealed") == "t3-tin"
    assert pid("Naruto CCG Tournament Pack 1 sealed") == "tp1-pack"


def test_not_sealed():
    assert pid("Naruto CCG Path to Hokage booster pack opened empty wrapper") is None
    assert pid("Naruto N-001 Path to Hokage pack fresh") is None
    assert pid("Lot of 5 Naruto Path to Hokage booster packs sealed") is None
    assert pid("3 packs Naruto Path to Hokage booster sealed") is None
    assert pid("Naruto Path to Hokage booster box break spot") is None
    assert pid("Naruto Kayou booster box sealed") is None
    assert pid("Naruto Japanese Bandai booster box sealed") is None
    assert pid("Naruto Card Game Bandai 2026 Booster Box sealed") is None   # the new game: no vintage set name
    assert pid("Pokemon Path to Hokage booster pack") is None


def test_edition():
    assert sealed.edition("Path to Hokage booster box 1st Edition") == "1st Edition"
    assert sealed.edition("Path to Hokage booster box First Ed sealed") == "1st Edition"
    assert sealed.edition("Path to Hokage unlimited booster box") == "Unlimited"
    assert sealed.edition("Path to Hokage booster box") == ""


def test_listing_and_settle():
    t = datetime(2026, 11, 27, 18, 0, tzinfo=timezone.utc)
    it = {"itemId": "v1|123|0", "title": "Naruto CCG Path to Hokage Booster Box Sealed 1st Edition",
          "buyingOptions": ["AUCTION"], "currentBidPrice": {"value": "1500", "currency": "USD"}, "bidCount": 4,
          "itemEndDate": (t - timedelta(minutes=10)).isoformat(), "itemWebUrl": "https://www.ebay.com/itm/123"}
    row = sealed.to_listing(it, P, SETS, t.isoformat())
    assert row["product_id"] == "1-booster-box" and row["edition"] == "1st Edition" and row["price"] == 1500
    state, sale = sealed.settle(row, None, t)
    assert state == "sold" and sale["status"] == "pending" and sale["price"] == 1500 and sale["product_id"] == "1-booster-box"
    state, sale = sealed.settle(dict(row, bids=0), None, t)
    assert state == "unsold" and sale is None


def test_naruto_deck():
    assert pid("Naruto CCG Curse of the Sand theme deck Naruto sealed") == "3-naruto"
    assert pid("Naruto CCG Curse of the Sand theme deck sealed") is None


def test_photo_rules():
    t = "Naruto CCG Path to Hokage booster box EMPTY no cards"
    assert pid(t) is None
    assert sealed.match(t, P, SETS, photo=True)[0]["id"] == "1-booster-box"
    assert sealed.match("Lot of 3 Naruto Path to Hokage booster box", P, SETS, photo=True) is None
