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
