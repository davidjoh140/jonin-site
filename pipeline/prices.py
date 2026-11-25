"""Pure helpers for sold prices: read grade / printing / edition from a listing title, and decide
what a finished listing counts as. No network here, so it is all unit-tested."""
import re
from datetime import datetime, timedelta, timezone

import settings as cfg

GRADERS = {"PSA": "PSA", "BGS": "BGS", "BECKETT": "BGS", "CGC": "CGC", "SGC": "SGC", "TAG": "TAG", "ACE": "ACE"}
GRADE_RE = re.compile(r"\b(PSA|BGS|BECKETT|CGC|SGC|TAG|ACE)\s*(?:GRADED\s*)?(?:GEM\s*MINT|GEM\s*MT|PRISTINE|"
                      r"MINT|NM-?MT|NM|BLACK\s*LABEL)?\s*(10|[1-9](?:\.5)?)(?![0-9.])")
NOT_GRADED = re.compile(r"\b(PSA|BGS|CGC|SGC|TAG)\s*(READY|CANDIDATE|WORTHY|\?)|\bNOT\s+GRADED\b|\bUNGRADED\b|"
                        r"\b(PSA|BGS|CGC)\s*10\s*(READY|CANDIDATE|WORTHY)")
# Specific foil words first; "foil" alone only counts when the card has one foil kind.
FOIL_WORDS = [(r"DIAMOND[\s-]*SPIRAL|\bSPIRAL\b", "Diamond-spiral foil"),
              (r"CHECKER", "Diamond-checkered foil"),
              (r"\bDIAMOND\b", "Diamond foil"),
              (r"\bWAV(E|Y)\b", "Wavy foil"),
              (r"SUPER\s*RARE\s*FOIL", "Super Rare foil")]
NON_FOIL = re.compile(r"\bNON[\s-]?(FOIL|HOLO)\b")
UNKNOWN = "?"          # stored when a title doesn't say; such sales wait for review
ANY_FOIL = re.compile(r"\b(FOIL|HOLO|HOLOGRAPHIC|FULL\s*ART|PRISM|SHINY)\b")


def parse_grade(title):
    """('PSA', '10') for a graded card, ('Raw', '') otherwise."""
    t = title.upper()
    if NOT_GRADED.search(t):
        return "Raw", ""
    m = GRADE_RE.search(t)
    if not m:
        return "Raw", ""
    grader = GRADERS[m.group(1)]
    if grader == "BGS" and re.search(r"BLACK\s*LABEL", t) and m.group(2) == "10":
        return "BGS", "10 Black Label"
    return grader, m.group(2)


def parse_printing(title, card, printing_from_matcher=""):
    """(printing, assumed). UNKNOWN when the title can't tell which version it is."""
    opts = card.get("printings") or []
    t = title.upper()
    if len(opts) == 1:
        # checklist says this card only comes non-foil but the title says foil: let David check it
        if opts[0] == "Normal" and ANY_FOIL.search(t) and not NON_FOIL.search(t):
            return UNKNOWN, False
        return opts[0], False
    if NON_FOIL.search(t) and "Normal" in opts:
        return "Normal", False
    for pat, p in FOIL_WORDS:
        if re.search(pat, t) and p in opts:
            return p, False
    if ANY_FOIL.search(t):
        foils = [p for p in opts if p != "Normal" and "Starter" not in p]
        if len(foils) == 1:
            return foils[0], False
        return UNKNOWN, False     # "foil" but the card has several foil kinds
    if printing_from_matcher in opts:
        return printing_from_matcher, False
    if cfg.ASSUME_NORMAL_IF_NO_FOIL and "Normal" in opts:
        return "Normal", True
    return UNKNOWN, False


def parse_edition(title, card):
    """(edition, assumed). Cards printed in only one edition (or none) get it for free."""
    eds = [e for e in (card.get("editions") or []) if e]
    if not eds:
        return "", False
    if len(eds) == 1:
        return eds[0], False
    t = title.upper()
    if re.search(r"\b1ST\b|FIRST\s+ED", t) and "1st Edition" in eds:
        return "1st Edition", False
    if re.search(r"\bUNLIMITED\b|\bUNL\b", t) and "Unlimited" in eds:
        return "Unlimited", False
    if cfg.ASSUME_UNLIMITED_IF_NO_1ST and "Unlimited" in eds:
        return "Unlimited", True
    return UNKNOWN, False


def skip_title(title):
    t = " " + title.lower() + " "
    return any(w in t for w in cfg.SALES_SKIP_WORDS)


def _dt(s):
    if isinstance(s, datetime):
        return s
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def settle(listing, ebay=None, now=None):
    """Decide what an ended listing counts as.

    listing: a listings row (kind, price, bids, ends_at, seen_at, confidence, printing, edition, best_offer)
    ebay: eBay's own record of the finished listing if we could look it up
          {"sold": bool, "price": float, "qty_sold": int, "best_offer_accepted": bool|None} or None
    Returns (state, sale) where sale is None or the fields for a sales row.
    """
    now = now or datetime.now(timezone.utc)
    ends = _dt(listing["ends_at"]) if listing.get("ends_at") else None
    sale = None
    if ebay is not None:
        if not ebay.get("sold"):
            return "unsold", None
        price, basis = ebay.get("price"), "final"
        stype = "auction" if listing.get("kind") == "AUCTION" else "buy_it_now"
        if ebay.get("best_offer_accepted"):
            stype, basis = "best_offer", "listed"   # eBay hides the accepted offer amount
        sale = {"price": price, "sale_type": stype, "price_basis": basis, "sold_at": (ends or now).isoformat()}
    elif listing.get("kind") == "AUCTION":
        if not listing.get("bids"):
            return "unsold", None
        sale = {"price": listing["price"], "sale_type": "auction", "price_basis": "last_seen_bid",
                "sold_at": (ends or now).isoformat()}
    else:
        # A Buy It Now that disappeared: sold or pulled, we can't tell from search alone.
        # It goes to David's review at its listed price; he checks the listing and OKs or vetoes it.
        return "gone", {"price": listing["price"], "sale_type": "buy_it_now", "price_basis": "unconfirmed",
                        "sold_at": now.isoformat(), "status": "pending"}
    ok = cfg.SALES_AUTO_APPROVE_CONFIDENCE is not None \
        and (listing.get("confidence") or 0) >= cfg.SALES_AUTO_APPROVE_CONFIDENCE \
        and UNKNOWN not in (listing.get("printing"), listing.get("edition")) \
        and sale["price_basis"] not in ("listed", "unconfirmed")
    if ok and sale["price_basis"] == "last_seen_bid":
        seen = _dt(listing["seen_at"]) if listing.get("seen_at") else None
        ok = bool(ends and seen and ends - seen <= timedelta(minutes=cfg.LAST_SEEN_MAX_MINUTES_BEFORE_END))
    sale["status"] = "approved" if ok else "pending"
    return "sold", sale
