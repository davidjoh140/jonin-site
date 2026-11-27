"""Load the scan reader's card details (pipeline/card_attrs.json) into Supabase card_attrs.

Rows arrive as `pending` guesses for David to approve on /admin/ (Card details). A row David already approved or
skipped is never touched again; only new rows and still-pending rows whose guess changed are sent, so this is cheap to
run on every sync. Needs SUPABASE_URL and SUPABASE_SERVICE_KEY.
"""
import json
import pathlib

FILE = pathlib.Path(__file__).with_name("card_attrs.json")


def to_send(rows, existing, card_ids):
    """The rows worth sending: card exists, and the row is new or still pending with a different guess/sure flag."""
    out = []
    for card_id, field, guess, conf, sure, box in rows:
        if card_id not in card_ids:
            continue
        cur = existing.get((card_id, field))
        if cur and (cur["status"] != "pending" or (cur["guess"] == guess and bool(cur["sure"]) == bool(sure))):
            continue
        out.append({"card_id": card_id, "field": field, "guess": guess, "conf": conf, "sure": bool(sure),
                    "box": {"x": box[0], "y": box[1], "w": box[2], "h": box[3]}, "status": "pending"})
    return out


def main():
    import supa
    if not FILE.exists():
        print("no card_attrs.json")
        return
    rows = json.loads(FILE.read_text())["rows"]
    with supa.Run("load_card_attrs") as run:
        card_ids = {c["id"] for c in supa.select("cards", {"select": "id"})}
        existing = {(r["card_id"], r["field"]): r
                    for r in supa.select("card_attrs", {"select": "card_id,field,guess,sure,status"})}
        send = to_send(rows, existing, card_ids)
        for i in range(0, len(send), 500):
            supa.upsert("card_attrs", send[i:i + 500], "card_id,field")
        run.stats = {"rows": len(rows), "sent": len(send)}
        print(json.dumps(run.stats))


if __name__ == "__main__":
    main()
