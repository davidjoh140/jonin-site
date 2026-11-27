from datetime import datetime, timedelta, timezone

import sealed

SETS = [{"id": "21", "name": "Shattered Truths", "kind": "Main"}, {"id": "15", "name": "Foretold Prophecy", "kind": "Main"},
        {"id": "1", "name": "The Path to Hokage", "kind": "Main"}, {"id": "9", "name": "The Chosen", "kind": "Main"},
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


ARTS = [{"id": "1-booster-pack-silver-naruto", "set_id": "1", "kind": "booster_pack", "parent_id": "1-booster-pack", "art": "Silver Naruto", "match_words": ["silver"]},
        {"id": "1-booster-pack-gold-naruto", "set_id": "1", "kind": "booster_pack", "parent_id": "1-booster-pack", "art": "Gold Naruto", "match_words": ["gold", "yellow"]},
        {"id": "4-booster-pack-sasuke", "set_id": "4", "kind": "booster_pack", "parent_id": "4-booster-pack", "art": "Sasuke", "match_words": ["sasuke"]},
        {"id": "12-blister-pack", "set_id": "12", "kind": "blister_pack", "match_words": []},
        {"id": "12-blister-pack-naruto", "set_id": "12", "kind": "blister_pack", "parent_id": "12-blister-pack", "art": "Naruto", "match_words": ["naruto art", "naruto pack art"]},
        {"id": "12-blister-pack-sakura", "set_id": "12", "kind": "blister_pack", "parent_id": "12-blister-pack", "art": "Sakura", "match_words": ["sakura"]},
        {"id": "12-blister-box", "set_id": "12", "kind": "blister_box", "match_words": []},
        {"id": "12-blister-3pack", "set_id": "12", "kind": "blister_3pack", "match_words": [], "public": False},
        {"id": "1-starter-naruto", "set_id": "1", "kind": "starter", "parent_id": "1-starter", "art": "Naruto", "match_words": ["naruto deck", "naruto starter", "uzumaki"]},
        {"id": "1-starter-sasuke", "set_id": "1", "kind": "starter", "parent_id": "1-starter", "art": "Sasuke", "match_words": ["sasuke"]}]


def apid(title):
    m = sealed.match(title, P + ARTS, SETS)
    return m and m[0]["id"]


def test_arts_blisters_and_decks():
    assert apid("Naruto CCG The Path to Hokage Booster Pack Silver Naruto Art Sealed") == "1-booster-pack-silver-naruto"
    assert apid("2006 Bandai Naruto Path To Hokage sealed booster pack yellow/gold cover art") == "1-booster-pack-gold-naruto"
    assert apid("2007 Naruto CCG Revenge and Rebirth Booster Pack [SASUKE ART] - New, Sealed") == "4-booster-pack-sasuke"
    assert apid("Naruto CCG The Path to Hokage Booster Pack Sealed 1st Edition") == "1-booster-pack"   # art not named
    assert apid("Naruto Path to Hokage booster pack silver and gold sealed") == "1-booster-pack"      # names both
    assert apid("Naruto Path to Hokage Booster Pack Art Set (2 Packs) sealed") is None                # pair: singles only
    assert apid("A New Chronicle - Set 12 - Blister Booster Pack x1 - Sakura Art - Naruto CCG Sealed") == "12-blister-pack-sakura"
    assert apid("A New Chronicle Blister Booster Pack Naruto Art Naruto CCG Sealed") == "12-blister-pack-naruto"
    assert apid("2009 Naruto CCG A New Chronicle (Set 12) 1st Edition Blister Booster Pack Sealed") == "12-blister-pack"
    assert apid("Naruto A New Chronicle TCG CCG Blister Booster Pack Box 15 Packs sealed") == "12-blister-box"
    assert apid("Naruto CCG A New Chronicle Booster Packs in Blister SET OF 2") is None
    assert apid("Naruto CCG A New Chronicle 3 Pack Blister factory sealed") == "12-blister-3pack"       # hidden slot still matches
    assert apid("Naruto CCG A New Chronicle 3 Booster Blister + promo sealed") == "12-blister-3pack"
    assert apid("Naruto CCG Path to Hokage Booster Box 24 Packs factory sealed") == "1-booster-box"     # box contents
    assert apid("Naruto A New Chronicle booster pack sealed") == "12-booster-pack"                    # loose pack, not blister
    assert apid("Naruto CCG TCG The Path to Hokage Sasuke Uchiha Starter Deck sealed") == "1-starter-sasuke"
    assert apid("Naruto CCG TCG The Path to Hokage Naruto Uzumaki Starter Deck sealed") == "1-starter-naruto"
    assert apid("Naruto Path to Hokage starter deck sealed") == "1-starter"                           # deck not named


def test_seller_spellings():
    ps = P + [{"id": "21-blister-pack", "set_id": "21", "kind": "blister_pack", "match_words": []},
              {"id": "15-fury", "set_id": "15", "kind": "theme", "match_words": ["spiral of the fury"]}]
    m = lambda t: (sealed.match(t, ps, SETS) or [{}])[0].get("id")
    assert m("Shattered Truth Blister Pack Sealed-Bandai Naruto Ccg") == "21-blister-pack"
    assert m("Naruto Shippuden CCG Foretold Prophecy Spiral of the Fury Starter Deck Sealed") == "15-fury"


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
