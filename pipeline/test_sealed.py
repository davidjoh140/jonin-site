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
    assert pid("Naruto CCG Series 12 booster pack sealed") is None              # strict: needs the set name
    assert sealed.match("Naruto CCG Series 12 booster pack sealed", P, SETS, photo=True)[0]["id"] == "12-booster-pack"
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
    assert apid("Naruto Path to Hokage booster pack silver and gold sealed") is None                  # both arts: a pair
    assert apid("Naruto Path to Hokage Booster Pack Art Set (2 Packs) sealed") is None                # pair: singles only
    assert apid("A New Chronicle - Set 12 - Blister Booster Pack x1 - Sakura Art - Naruto CCG Sealed") == "12-blister-pack-sakura"
    assert apid("A New Chronicle Blister Booster Pack Naruto Art Naruto CCG Sealed") == "12-blister-pack-naruto"
    assert apid("2009 Naruto CCG A New Chronicle (Set 12) 1st Edition Blister Booster Pack Sealed") == "12-blister-pack"
    assert apid("Naruto A New Chronicle TCG CCG Blister Booster Pack Box 15 Packs sealed") == "12-blister-box"
    assert apid("Naruto CCG A New Chronicle Booster Packs in Blister SET OF 2") is None
    assert apid("Naruto CCG A New Chronicle 3 Pack Blister factory sealed") == "12-blister-3pack"       # hidden slot still matches
    assert apid("Naruto CCG A New Chronicle 3 Booster Blister factory sealed") == "12-blister-3pack"
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


def test_strict_exact_items():
    """Real wrong matches from the live listings (Nov 27) stay out; real single items still match."""
    SS = SETS + [{"id": "2", "name": "Coils of the Snake", "kind": "Main"}, {"id": "28", "name": "Ultimate Ninja Storm 3", "kind": "Main"},
                 {"id": "17", "name": "Will of Fire", "kind": "Main"}, {"id": "8", "name": "Battle of Destiny", "kind": "Main"}]
    PP = P + ARTS + [{"id": f"{s}-booster-{k}", "set_id": s, "kind": f"booster_{k}", "match_words": []} for s in ("2", "28", "17", "8") for k in ("pack", "box")] \
        + [{"id": "tp3-pack", "set_id": "TP3", "kind": "tournament_pack", "match_words": []}]
    SS += [{"id": "TP3", "name": "Tournament Pack 3", "kind": "Tournament pack"}]
    m = lambda t: (sealed.match(t, PP, SS) or [{}])[0].get("id")
    for bad in ["Naruto Smriti CCG Earth Scroll Series 2 Collector Box 5 Booster Packs Sealed New",
                "Naruto Uzumaki 9 Tails Cloak 1646 S28 Extended Art Display CARD NOT INCLUDED",
                "NARUTO Card Game Series 2 Le Spire del Serpente Bustina Pack Panini BANDAI",
                "Naruto CCG The Path to Hokage – 10 Factory-Sealed Booster Packs",
                "The Chosen Booster Pack - Naruto CCG - 2 SASUKE Packs!",
                "Bandai Naruto CCG The Chosen Booster pack 2008 Naruto and Sasuke Sealed!",
                "Naruto Will of Fire 30 Pack Trading Card Booster Box Anime CCG TCG New HY-1602",
                "Naruto CCG Naruto Uzumaki Ultimate Battle Tins Chibi Foil Promo PR 072 NM",
                "Naruto CCG Sasuke Uchiha 1st Edition Tournament Pack 2 Chibi Vintage Bandai",
                "Naruto The Path to Hokage, Starter Deck, Sasuke edition. Set Box & 50Cards Only",
                "Naruto CCG Card Game The Chosen TIDAL WAVE  Deck INCOMPLETE*READ*",
                "Bandai Naruto CCG Ultimate Ninja Storm 3 2 Booster Packs Sealed Blister French",
                "Bandai Naruto CCG Coils of the Snake Booster Pack English 10 Cards"]:      # doesn't say sealed/new
        assert m(bad) is None, bad
    assert m("2006 Bandai Naruto CCG The Path To Hokage (Set 1) Factory Sealed Booster Pack") == "1-booster-pack"
    assert m("2006 BANDAI NARUTO COILS OF THE SNAKE BOOSTER BOX (24 PACKS) NEW SEALED U.S.") == "2-booster-box"
    assert m("Naruto CCG Battle of Destiny Booster Pack Factory Sealed Bandai - Sasuke Art") == "8-booster-pack"
    assert m("Naruto Chibi Tournament Series 3 Booster Box - Factory Sealed 24 Packs") is None   # a box of them, not one pack
    assert m("Bandai 2011 Naruto Chibi Tournament Series 3 Booster Box - New, Factory Sealed") is None
    assert m("Naruto - Chibi Tournament Series 3 - Booster Pack -Sealed - Bandai") == "tp3-pack"


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

