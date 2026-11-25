# jonin.cards

Public card database for the original Bandai Naruto CCG (2006–2013).

- `public/` — the static site served at jonin.cards (Cloudflare Pages, build output directory `public`, no build command).
- `public/cards.json` — card data the site reads (sets, cards, printings). Exported from the Supabase back end.
- `db/schema.sql` — Supabase tables (sets, cards, scans, sales, listings) with public read access only for sets, cards and approved scans.
- `db/seed.sql` — initial import of all sets and cards.

## One card list, everywhere

Supabase is the only master card list. Nothing else is edited by hand.

- `pipeline/export_cards.py` rebuilds `public/cards.json` from Supabase. The **Sync card list** workflow runs it every 30 minutes and commits when something changed, so jonin.cards always matches Supabase. `--check` reports whether they differ.
- Scrapers read the card list from Supabase at the start of every run, and scan rows point at `cards.id` with foreign keys, so an image can only be attached to a card that exists.
- Checklist fixes (e.g. from RetroTCG) go into `checklist_changes` for review, never straight into a separate list.
- `checklist_version` goes up on every change to sets or cards, so any copy can tell it's stale.

## Scan pipeline

- `db/002_scan_pipeline.sql`, then `db/003_backfill.sql` (one time): adds `scan_candidates`, `checklist_changes`, `pipeline_runs`, the `scans` storage bucket, and the columns cards.json needs.
- `pipeline/find_scans.py` (**Find card scans** workflow, daily + on demand): searches eBay, pulls PSA slab images for graded listings with a cert number, matches each to a card, stores the image in Supabase Storage and queues it in `scan_candidates` as `pending`.
- Approving a candidate (`status = 'approved'`) creates the public scan automatically; un-approving removes it.
- Settings marked PLACEHOLDER in `pipeline/settings.py` are starting guesses to revisit.
- Don't re-run `db/seed.sql` once scans exist: it deletes every scan.

Repo secrets: `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `EBAY_CLIENT_ID`, `EBAY_CLIENT_SECRET`, `PSA_TOKEN`.

## Card Index sync (one copy of the card list)

- Supabase is the master. Card list edits (new cards, rarities, printings, decks) are made in Supabase only, never by hand in the Card Index or `public/cards.json`.
- `public/cards.json` is the export of Supabase. The Card Index artifact is republished with that exact same file, so the site and the Card Index are byte-for-byte identical.
- The export carries `version` (Supabase `checklist_version`). The Card Index compares it with Supabase on load and shows a banner when it has fallen behind.
- New Card Index scans are copied to `public/scans/<set>/<number>.webp` with a matching public row in `scans`.
