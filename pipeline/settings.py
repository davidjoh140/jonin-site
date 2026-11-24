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
