from datetime import datetime, timedelta, timezone

import collect_sales as cs
import prices
from test_match import M

T = datetime(2026, 11, 25, 18, 0, tzinfo=timezone.utc)
TWO = {"printings": ["Normal", "Flat foil"], "editions": ["1st Edition", "Unlimited"]}
MANY = {"printings": ["Normal", "Flat foil", "Diamond foil", "Wavy foil"], "editions": ["1st Edition", "Unlimited"]}


def test_grades():
    assert prices.parse_grade("Naruto N-019 PSA 10 Gem Mint") == ("PSA", "10")
    assert prices.parse_grade("PSA GEM MINT 10 Sasuke") == ("PSA", "10")
    assert prices.parse_grade("BGS 9.5 Gaara N-100") == ("BGS", "9.5")
    assert prices.parse_grade("Beckett 10 Black Label Itachi") == ("BGS", "10 Black Label")
    assert prices.parse_grade("CGC 9 Kakashi") == ("CGC", "9")
    assert prices.parse_grade("Naruto PSA 10 ready! N-019") == ("Raw", "")
    assert prices.parse_grade("Naruto N-019 1st edition NM") == ("Raw", "")
    assert prices.parse_grade("Naruto N-1002 holo") == ("Raw", "")


def test_printing():
    assert prices.parse_printing("Naruto N-001 non-foil", TWO) == ("Normal", False)
    assert prices.parse_printing("Naruto N-001 holo foil", TWO) == ("Flat foil", False)
    assert prices.parse_printing("Naruto N-001", TWO) == ("Normal", True)            # placeholder assumption
    assert prices.parse_printing("Naruto N-001 wavy foil", MANY) == ("Wavy foil", False)
    assert prices.parse_printing("Naruto N-001 flat foil", MANY) == ("Flat foil", False)
    SET9 = {"printings": ["Normal", "Prism foil", "Spiral foil"], "editions": ["1st Edition", "Unlimited"]}
    assert prices.parse_printing("Gaara N-400 prism foil", SET9) == ("Prism foil", False)
    assert prices.parse_printing("Gaara N-400 diamond spiral foil", SET9) == ("Spiral foil", False)
    assert prices.parse_printing("Gaara N-400 checkered foil", SET9) == ("Prism foil", False)
    assert prices.parse_printing("Naruto N-001 foil", MANY) == (prices.UNKNOWN, False)
    assert prices.parse_printing("anything", {"printings": ["Super Rare foil"]}) == ("Super Rare foil", False)
    assert prices.parse_printing("PR-063 Full Art Foil", {"printings": ["Normal"]}) == (prices.UNKNOWN, False)


def test_edition():
    assert prices.parse_edition("N-001 1st Edition", TWO) == ("1st Edition", False)
    assert prices.parse_edition("N-001 1st ed", TWO) == ("1st Edition", False)
    assert prices.parse_edition("N-001 unlimited", TWO) == ("Unlimited", False)
    assert prices.parse_edition("N-001", TWO) == ("Unlimited", True)
    assert prices.parse_edition("N-001", {"editions": []}) == ("", False)


def L(**k):
    base = {"kind": "AUCTION", "price": 42.0, "bids": 3, "ends_at": (T - timedelta(minutes=5)).isoformat(),
            "seen_at": (T - timedelta(minutes=12)).isoformat(), "confidence": 0.9, "printing": "Normal",
            "edition": "Unlimited"}
    base.update(k)
    return base


def test_nothing_auto_approved_by_default():
    assert prices.settle(L(), None, T)[1]["status"] == "pending"


def test_settle_auction_without_ebay_record(monkeypatch):
    monkeypatch.setattr(prices.cfg, "SALES_AUTO_APPROVE_CONFIDENCE", 0.85)
    state, sale = prices.settle(L(), None, T)
    assert state == "sold" and sale["price"] == 42.0 and sale["price_basis"] == "last_seen_bid"
    assert sale["status"] == "approved"
    # last bid seen too long before the end -> review
    _, sale = prices.settle(L(seen_at=(T - timedelta(hours=3)).isoformat()), None, T)
    assert sale["status"] == "pending"
    assert prices.settle(L(bids=0), None, T) == ("unsold", None)


def test_settle_with_ebay_record():
    state, sale = prices.settle(L(kind="FIXED_PRICE"), {"sold": True, "price": 55.0}, T)
    assert state == "sold" and sale["price_basis"] == "final" and sale["sale_type"] == "buy_it_now"
    _, sale = prices.settle(L(kind="FIXED_PRICE"), {"sold": True, "price": 55.0, "best_offer_accepted": True}, T)
    assert sale["sale_type"] == "best_offer" and sale["status"] == "pending"
    assert prices.settle(L(), {"sold": False}, T) == ("unsold", None)


def test_settle_unknown_version_waits(monkeypatch):
    monkeypatch.setattr(prices.cfg, "SALES_AUTO_APPROVE_CONFIDENCE", 0.85)
    _, sale = prices.settle(L(printing=prices.UNKNOWN), None, T)
    assert sale["status"] == "pending"
    _, sale = prices.settle(L(confidence=0.75), None, T)
    assert sale["status"] == "pending"


def test_buy_it_now_vanished_goes_to_review():
    state, sale = prices.settle(L(kind="FIXED_PRICE"), None, T)
    assert state == "gone" and sale["price_basis"] == "unconfirmed" and sale["status"] == "pending"


def item(title, **k):
    it = {"itemId": "v1|1234|0", "title": title, "price": {"value": "30.00", "currency": "USD"},
          "buyingOptions": ["FIXED_PRICE"], "itemWebUrl": "https://www.ebay.com/itm/1234",
          "image": {"imageUrl": "https://i.ebayimg.com/images/g/x/s-l225.jpg"}}
    it.update(k)
    return it


def test_to_listing():
    row = cs.to_listing(item("Naruto CCG Naruto Uzumaki N-001 1st Edition Path to Hokage Diamond Foil PSA 9"), M, T)
    assert row["card_id"] == "1:N-001" and row["printing"] == "Diamond foil" and row["edition"] == "1st Edition"
    assert (row["grader"], row["grade"]) == ("PSA", "9") and row["price"] == 30.0 and row["kind"] == "FIXED_PRICE"
    assert row["image_url"].endswith("s-l1600.jpg")
    a = cs.to_listing(item("Naruto CCG Naruto Uzumaki N-001 1st Edition Diamond Foil", buyingOptions=["AUCTION"],
                           currentBidPrice={"value": "12.50", "currency": "USD"}, bidCount=4), M, T)
    assert a["kind"] == "AUCTION" and a["price"] == 12.5 and a["bids"] == 4
    assert cs.to_listing(item("Naruto CCG N-001 Naruto Uzumaki proxy custom"), M, T) is None
    assert cs.to_listing(item("Naruto CCG lot of 50 cards N-001"), M, T) is None
    assert cs.to_listing(item("Naruto Uzumaki NRSA-PR-015 Naruto Kayou promo"), M, T) is None


def test_condition():
    pc = prices.parse_condition
    assert pc("Naruto CCG Minato N-1122 Lp 1st Edition Foil") == ("LP", "title")
    assert pc("Kakashi N-396 First Edition Near Mint") == ("NM", "title")
    assert pc("Neji N-513 Common 1st Edition Foil Played - LP/MP") == ("MP", "title")   # worst of two
    assert pc("Sasuke PR088 PSA 10 GEM MINT") == ("", "graded")
    assert pc("Naruto N-001 foil", "400015") == ("LP", "ebay")
    assert pc("Naruto N-001 foil", "400010") == ("NM", "ebay")
    assert pc("Naruto N-001 foil", None, "Card is in heavily played condition, see photos") == ("HP", "description")
    assert pc("Naruto N-001 foil", None, "Grading scale: NM, LP, MP, HP") == (prices.UNKNOWN, "")
    assert pc("Naruto N-001 foil") == (prices.UNKNOWN, "")
    assert pc("Hidden Lotus J-US005 Rare Unlimited Diamond Foil LP/MP Pi") == ("MP", "title")
