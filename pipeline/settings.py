"""Scan-finder settings. Everything marked PLACEHOLDER is a starting guess for David to change."""

# Which set to work on. Start with one set end to end; set to None for all sets.
SET_FILTER = "1"                      # PLACEHOLDER: set 1, The Path to Hokage, as the first test

# eBay searches. With SET_FILTER the set name is added to each search.
EBAY_QUERIES = ["naruto ccg", "naruto card game bandai"]   # PLACEHOLDER
EBAY_PAGES_PER_QUERY = 3              # PLACEHOLDER: 200 listings per page
EBAY_MAX_CALLS_PER_RUN = 200          # PLACEHOLDER: stays far under eBay's daily limit

# Listings whose title has any of these are skipped (photos show many cards).
LOT_WORDS = ["lot", "bundle", "collection", "you pick", "you choose", "choose your", "pick your",
             "set of", "playset", "binder", "bulk", "complete set", "x2", "x3", "x4", "deck"]  # PLACEHOLDER

# PSA: free API tier is 100 calls a day; each cert uses 2 (details + images).
PSA_MAX_CALLS_PER_RUN = 90            # PLACEHOLDER

# Matching
MIN_CONFIDENCE = 0.70                 # PLACEHOLDER: below this, a listing is ignored
AUTO_APPROVE_CONFIDENCE = None        # PLACEHOLDER: None = David reviews every image
MAX_PENDING_PER_CARD = 3              # PLACEHOLDER: stop queueing a card once it has 3 waiting

THUMB_WIDTH = 480                     # review-screen thumbnail width in px

# ---------------------------------------------------------------- sold prices (collect_sales.py)
# Everything here is a PLACEHOLDER for David to change.
SALES_QUERIES = ["naruto ccg", "naruto card game bandai", "naruto bandai card"]  # PLACEHOLDER
SALES_FULL_SWEEP_MINUTES = 60      # PLACEHOLDER: re-read every Naruto listing about once an hour
SALES_PAGES_PER_QUERY = 10         # PLACEHOLDER: 200 listings per page; must cover every result or vanished listings are not checked
SALES_ENDING_WINDOW_MINUTES = 30   # PLACEHOLDER: each run re-checks auctions ending within this window
SALES_MAX_CALLS_PER_RUN = 120      # PLACEHOLDER: eBay Browse calls per run (runs every 15 min)
SALES_MAX_SETTLE_PER_RUN = 150     # PLACEHOLDER: ended listings looked up per run

# Extra title words that mean "not a real single card" for prices.
SALES_SKIP_WORDS = ["kayou", "mythos", " 2x ", " 3x ", " 4x ", "proxy", "custom", "fan made", "fanmade", "orica", "reprint", "replica", "art card",
                    "sleeve", "playmat", "binder", "empty", "psa ready"]  # PLACEHOLDER

# What a title that doesn't say counts as.
ASSUME_NORMAL_IF_NO_FOIL = True    # PLACEHOLDER: no foil word in the title -> Normal printing
ASSUME_UNLIMITED_IF_NO_1ST = True  # PLACEHOLDER: no "1st Edition" in the title -> Unlimited

# Which recorded sales go straight into the public range; the rest wait for David's yes / no.
SALES_AUTO_APPROVE_CONFIDENCE = None   # David OKs every sale himself (None = nothing auto-approved)
# Without eBay's confirmed final price, an auction counts at its last bid we saw,
# but only if we saw it this close to the end (otherwise it waits for review).
LAST_SEEN_MAX_MINUTES_BEFORE_END = 20  # PLACEHOLDER
