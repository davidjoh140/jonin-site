from export_cards import top_sales, version_label


def sale(i, card, price, **kw):
    return dict(id=i, card_id=card, price=price, status=kw.pop("status", "approved"), sold_at="2026-11-25T00:00:00",
                printing=kw.get("printing", "Normal"), edition=kw.get("edition", "Unlimited"),
                grader=kw.get("grader", "Raw"), grade=kw.get("grade", ""))


def test_one_spot_per_card_using_its_best_sale():
    t = top_sales([sale(1, "A", 50), sale(2, "A", 400, printing="Diamond foil"), sale(3, "B", 100)])
    assert t["A"][0] == 1 and t["A"][2] == "Unlimited · Diamond foil · Raw"
    assert t["B"][0] == 2


def test_skips_unapproved_and_unknown_versions():
    t = top_sales([sale(1, "A", 900, status="pending"), sale(2, "A", 900, printing="?"), sale(3, "A", 10)])
    assert t["A"][0] == 1 and t["A"][1] == 1   # band of the $10 sale


def test_version_label_graded():
    assert version_label({"edition": "1st Edition", "printing": "Flat foil", "grader": "PSA", "grade": "10"}) == \
        "1st Edition · Flat foil · PSA 10"


def test_attrs_only_approved():
    import export_cards as ec
    rows = [{"card_id": "1:N-1", "field": "element", "value": "Fire", "status": "approved"},
            {"card_id": "1:N-1", "field": "turn_cost", "value": "3", "status": "approved"},
            {"card_id": "1:N-1", "field": "village", "value": "Leaf", "status": "pending"},
            {"card_id": "1:N-2", "field": "hand_cost", "value": "x", "status": "approved"}]
    assert ec.attr_map(rows) == {"1:N-1": {"el": "Fire", "tc": 3}}


def test_load_skips_reviewed():
    import load_card_attrs as la
    rows = [["1:N-1", "element", "Fire", 0.99, True, [1, 2, 3, 4]],
            ["1:N-2", "element", "Water", 0.5, False, [1, 2, 3, 4]],
            ["1:N-3", "element", "Wind", 0.9, True, [1, 2, 3, 4]],
            ["9:X", "element", "Wind", 0.9, True, [1, 2, 3, 4]]]
    existing = {("1:N-1", "element"): {"status": "approved", "guess": "Earth", "sure": True},
                ("1:N-2", "element"): {"status": "pending", "guess": "Water", "sure": False}}
    sent = la.to_send(rows, existing, {"1:N-1", "1:N-2", "1:N-3"})
    assert [r["card_id"] for r in sent] == ["1:N-3"]


def test_price_range_typical_raw_copy():
    from export_cards import price_range
    s = lambda p, g="Raw", st="approved": {"price": p, "grader": g, "status": st, "printing": "Normal", "edition": "1st Edition"}
    # raw only, middle half of 8 sales: drops the $3 low and the $400 high
    assert price_range([s(p) for p in (3, 12, 14, 15, 18, 20, 22, 400)] + [s(5000, "PSA")]) == ([12, 22], "raw")
    assert price_range([s(13.5), s(22)]) == ([13, 22], "raw")
    assert price_range([s(1247, "PSA")]) == ([1200, 1200], "graded")
    assert price_range([s(50, st="pending")]) is None
