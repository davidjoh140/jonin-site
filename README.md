# jonin.cards

Public card database for the original Bandai Naruto CCG (2006–2013).

- `public/` — the static site served at jonin.cards (Cloudflare Pages, build output directory `public`, no build command).
- `public/cards.json` — card data the site reads (sets, cards, printings). Exported from the Supabase back end.
- `db/schema.sql` — Supabase tables (sets, cards, scans, sales, listings) with public read access only for sets, cards and approved scans.
- `db/seed.sql` — initial import of all sets and cards.

## One card list, everywhere

Supabase is the only master card list. Nothing else is edited by hand.

- `pipeline/export_cards.py` rebuilds `public/cards.json` from Supabase. The **Sync card list** workflow runs it every 15 minutes (when GitHub's schedule fires) and on every push, and commits when something changed, so jonin.cards always matches Supabase. `--check` reports whether they differ.
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
- Scans flow on their own: when David (admin) has the Card Index open, it sends every scan that Supabase doesn't have yet (or whose image changed) into the `scan_uploads` staging table, resized to 500px webp, through the Supabase connector. It re-checks every 10 minutes while open.
- The `drain-scan-uploads` Edge Function, called every minute by pg_cron (`kick_scan_drain()`), moves staged images into the public `scans` Storage bucket (`ci/<set>/<number>_<printing>-<edition>-<asset>.webp`) and upserts the `scans` row by `ci_doc` (the Card Index doc id). `pipeline/drain_uploads.py` does the same from GitHub Actions as a backup. Rows that fail keep an `error` and stay staged.
- jonin.cards reads images live from the `site_card_images` view (one best public image per card) with the publishable key, so a new scan shows within a minute or two. `cards.json` still carries `img` as the fallback.
- Older scans (the first 255) live in `public/scans/<set>/<number>.webp`.

## Rarity from the dots

Main-set rarities follow the dots after the copyright line: none = Common, one = Uncommon, two = Rare, three = Super Rare. The 749 cards changed on 2026-11-25 are kept in `rarity_dot_fix` (with `old_rarity`) so the change can be reviewed or undone.

Red dots mean a starter/theme deck printing. Those cards are marked `starter_exclusive`; cards with no other rarity get `Starter` (code F), cards that also have a booster rarity keep it (shown as "Starter <rarity>").

## Most valuable pages

- `/character/<slug>/most-valuable/` for the characters in `MOST_VALUABLE_CHARACTERS` (`pipeline/settings.py`; Naruto, Sasuke, Itachi to start). Top `MOST_VALUABLE_TOP` (5) cards.
- Ranked by each card's single highest approved sale (eBay or private, any version, all time). One spot per card, so a card and its foil can't both appear.
- `export_cards.py` adds `"top": [rank, band, version, date]` to each card with sales. Cards that make a most-valuable list also get `[price, ebay_url]` appended: those pages show the exact top sale (and link it). Every other card's exact prices stay Premium.
- Rebuilt by the Sync workflow every ~15 minutes, so the lists update on their own.
- Private sales (not on eBay) are added from `/admin/` → Private sales (`db/009_private_sales.sql`).

## Accounts and the signup prompts

- Signed-out visitors can mark haves, wants and slabs right away. It's kept in their browser (`localStorage` key `jonin_guest_v1`) and moves into their account the first time they sign in or sign up (counts merge by taking the higher number).
- Prompts: a dismissible band above the homepage grid, a "Saved on this device only" note in each card's collection box and on My collection, a one-time toast after their first mark, and "Sign up to save" in the header.
- Slabs: `collection_slabs` (`db/009_collection_slabs.sql`) — grader, grade, optional cert, per printing/edition. Private to the owner; not part of shared lists yet.
- Votes: tapping Vote while signed out opens signup and casts that vote once they're in (stored in `jonin_pending_vote` for 24h, so it also survives the email-confirm link).

## Cards tracked ticker

- Small pill under the homepage title: "N cards tracked by N collectors". Every have, want and slab saved to an account adds 1.
- Reads `cards_tracked()` (`db/017_cards_tracked.sql`) with the publishable key; rolls the digits up on first load and re-checks every 30s while the tab is open.
## Card lists (My lists)

- Members make their own named card lists (`card_lists`, `card_list_items`; `db/017_card_lists.sql`). Private to the owner (RLS).
- Card panel: a Lists row under Your collection with one chip per list (tap to add/remove) and + New list (creating from a card adds that card).
- My collection: a Lists tab (also `/#lists` and "My lists" in the profile menu) with every list, and each list's cards, Rename, Copy list, Delete.
- PLACEHOLDERS to revisit: lists hold whole cards (no printing/edition), members only, 50 lists / 1,000 cards per list.
- Sharing later: `visibility` and `share_slug` already exist on `card_lists`.

## Invites (scrolls for inviting friends)

- Every profile has an `invite_code`; the link is `https://jonin.cards/?invite=<code>` (`db/019_invites.sql`).
- `acct.js` (on every page) remembers the code for 30 days and calls `claim_invite` once the visitor is signed in. Only accounts made in the last 3 days can claim, never your own code, one inviter per account.
- Missions page has an Invite friends card (link, copy/share, count); profile menu links to it.
- PLACEHOLDERS for David: 50 scrolls per friend (`xp_rules()`), a friend counts once they add a card/slab or vote, 3-day claim window.

## Card condition in collections

- Every have copy has a condition (NM / LP / MP / HP / DMG). New copies start as NM; the card's collection box shows one picker per copy (`collection_items.conds`, `db/020_collection_condition.sql`; guests keep it in `jonin_guest_v1`).
- Premium: each condition shows its own RAW estimate (`price_estimates_cond`, built from approved price-check sales with that condition) and links to the matching sold comps (`member_card_comps`). Collection value and the export price each copy by its condition.
- PLACEHOLDER for David: a condition with no sales uses the version's all-conditions estimate, labelled "no LP sales yet, all-conditions estimate".
