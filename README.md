# jonin.cards

Public card database for the original Bandai Naruto CCG (2006–2013).

- `public/` — the static site served at jonin.cards (Cloudflare Pages, build output directory `public`, no build command).
- `public/cards.json` — card data the site reads (sets, cards, printings). Exported from the Supabase back end.
- `db/schema.sql` — Supabase tables (sets, cards, scans, sales, listings) with public read access only for sets, cards and approved scans.
- `db/seed.sql` — initial import of all sets and cards.

## Homepage code

The homepage's app code is in `public/home.js` (moved out of `index.html` on 2026-11-27 so browsers keep it between
visits). Edit it there. `build_pages.py` updates the `?v=` on its `<script>` tag in `index.html` whenever the file
changes. Small inline scripts that must run early (embed detection, the character list `QUICK`, which build_pages.py
reads) stay in `index.html`.

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

## Scans from sold listings

- `db/026_sale_scan_queue.sql`: every approved sale for a printing with no public scan goes into `sale_scan_queue`. pg_cron (`sale-photos`, every 2 min) runs `kick_sale_photos()`, which queues new ones and calls the `fetch-sale-photos` Edge Function (`supabase/functions/`) to download each photo as base64.
- David cuts each photo in the Buying Desk (Scans → From sold listings): auto-found corners, drag to fix, **Use as scan** stages it in `scan_uploads` (`doc_id` `sale:<sale id>`, source `eBay listing`) for `drain-scan-uploads`. A later Card Index scan replaces it.
- Printings with sales but no usable photo (none, skipped, or failed to download) show in the `scans_wanted` view ("Needs a scan" list).
- Card pages load the newest image live from `site_card_images` (`public/card-art.js`), so a new scan shows within a minute or two instead of waiting for the next page rebuild.

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
- A condition with no sales of that version shows no price yet, and those copies count as unpriced in collection value (David, 2026-11-26).

## Public profiles

- `/#u=<share_slug>` is a member's public profile: avatar, name, badge, favorite character, scroll rank, member since, Instagram, haves and wants.
- Slabs show there only if the member turns on **Show my slabs** on My collection (`profiles.show_slabs`, off by default). Grader and grade only, never cert numbers (`shared_slabs`, `db/022_public_profiles.sql`).
- Members get "See my profile as others do" next to their share link.
- PLACEHOLDER for David: `profiles.sharing` (haves/wants by link) is still ON by default for new accounts.
- Admin: `/admin/` → Accounts → **View profile** shows any account's slabs (with certs and a PSA link), haves, wants and lists, whether or not they share.

## PSA cert lookup

- Typing a PSA cert in "+ Add a slab" calls the `psa-lookup` Edge Function (`supabase/functions/psa-lookup/index.ts`): it fills in the grade, says whether the cert matches the card, and shows PSA's slab photo. Saved slabs get ✓ PSA verified / ⚠ different card / pending, and the slab photo replaces the card scan on the Slabs tab, public profile and `/admin/`.
- Verification is done in Supabase (trigger `slab_apply_psa` from the `psa_certs` cache), so members can't fake it. Each cert costs PSA calls once.
- PSA free limit: 100 calls/day, 2 per cert, shared with the scanner. Members first (David, 2026-11-26): members take calls with no reserve; the scanner leaves `PSA_MEMBER_RESERVE` (20) for them. Over the limit, the cert is queued and the hourly `psa-queue` job looks it up later.
- Needs the Edge Function secret `PSA_TOKEN` (Supabase → Edge Functions → Secrets). Until it's set, certs just queue.
- PLACEHOLDERS: 10 new cert lookups per member per day; scanner reserve 20 calls; day resets at UTC midnight.

## Last seen

- `acct.js` (every page) calls `touch_seen()` for signed-in members, at most every 5 minutes, setting `profiles.last_seen_at` (`db/024_last_seen.sql`). `/admin/` → Accounts shows "Last seen" (falls back to the last sign-in) plus "Active last 24 hours / 7 days".

## Messages (David ↔ members)

- `db/025_messages.sql`: one private conversation per member in `messages`, only reachable through functions (no direct table access).
- `/admin/` → **Messages**: every conversation with unread replies. Start one from a feedback note (💬 Message sender, which fills in Claude's drafted question for that note) or from Accounts / View profile (💬 Message). Senders with no account get an "Email them instead" link.
- A member's reply about a note has **Use in fix**: it sends their answer to Claude as an Alter on that note, and Accept (in the conversation or in Feedback) then applies the fix to the cards.
- Members: red dot on the profile button, **Messages** in the profile menu (in `acct.js`), reply box once David has written. `jonin.cards/#messages` opens it.
- Rules (David approved 2026-11-26): members can't start a conversation themselves, one member message per 10 seconds, 2000 characters max, unread checked every minute.

## Scroll nudges (getting members to vote and earn scrolls)

- Profile menu: a **Next mission** line under the rank card. Order: vote on their favorite character, then the next character they haven't voted on (most cards first), then Log 100 cards, then Invite a friend. Links straight to the character's vote box.
- One-time **"Earn scrolls, rank up"** popup (in `acct.js`) for members who've voted on fewer than 3 characters: their rank, every way to earn with the amounts from `xp_rules`, and a "Vote on <favorite>'s cards" button.
- Character pages (`vote.js`): "📜 Your first vote on <character> earns +5 scrolls" in the vote box, and a floating "▲ Vote for <character>'s coolest cards" button while the vote box is off screen, until they've voted there. Signed-out visitors see it too.
- PLACEHOLDERS for David: popup shows 4 seconds after a page opens, only under 3 characters voted, at most 3 times per member, "Later" waits 7 days.
- Umami events: scrolls-intro, scrolls-intro-click, vote-pill.

## Scrolls leaderboard

- `/leaderboard/` ranks members by scrolls (`scroll_leaderboard()`, `db/029_scroll_leaderboard.sql`; page script `public/leaderboard.js`). Linked from Missions and the profile menu.
- Only members who turned on profile sharing appear (David, 2026-11-26). Shows name, picture, status badge, rank and scrolls, and links to their public profile. Nothing from collections. Admin accounts (David's) are included.
- Signed-in members outside the top get their own row pinned at the bottom; members not sharing get a note on how to join the board.
- Setup (`/welcome/`, step 2) asks "Make your profile public?" — Public or Keep it private (default private). It sets `profiles.sharing`.
- Rules (David approved 2026-11-26): top 25, members need 1+ scroll, ties share a place (earlier member listed first).

## Sealed products (/sealed/)

- `db/030_sealed.sql`: `products` is the one sealed catalog (it already held the decks cards come in). Added booster pack + booster box per main set, the 4 tins and 4 tournament packs, all `confirmed = false` until David checks contents, MSRP and release. `match_words` are extra title words for matching (deck names).
- `sealed_listings` / `sealed_sales` / `sealed_price_ranges`: no public access. `collect_sales.py` hands every eBay listing to `pipeline/sealed.py` first; one clear sealed item becomes a sealed listing (not a card). Ended listings settle like cards and wait as pending in `sealed_sales` until David OKs them in **Jonin Hub → Sealed**. `refresh_sealed_prices()` rebuilds the ranges.
- Ranges: per product + edition, last 180 days (or 3 newest), middle half once there are 4+ sales. A title with no edition stays "Edition not stated" (not assumed Unlimited like cards).
- `export_cards.py` writes `pipeline/sealed.json` (`sealed_export.py`); `build_pages.py` builds `/sealed/` and `/sealed/<slug>/` from it (`sealed_pages.py`). Free for everyone: range per edition, last 5 sold, what's listed now (affiliate links).
- PLACEHOLDERS for David (`settings.py` SEALED_*, `sealed.py` SKIP): the 6 sealed eBay searches (1 page each, hourly), skip words (opened, resealed, lots, breaks, Japanese…), multiples skipped rather than split per item, a bare "box" = booster box and bare "pack" = booster pack, 0.65 minimum match.
- Photos: **Find sealed photos** workflow (`find_sealed_images.py`, run by hand or Mondays) queues up to 4 eBay listing photos per item with no photo in `sealed_image_candidates` (`db/031_sealed_images.sql`). David picks one in Jonin Hub → Review → Sealed → Photos; the Sync workflow (`--mirror`) copies it to R2 (`img.jonin.cards/site/sealed/`) and sets `products.image_url`. Shown as "Seller photo from an eBay listing".
## Search (Google) basics
- Brand markup: `public/index.html` has an Organization + WebSite JSON-LD block so Google treats "Jonin" as the site name and ties the social accounts to it. Add new profiles (Reddit, Discord, TikTok…) to its `sameAs` list.
- Sitemap dates: `<lastmod>` only moves when a page's own content changes — title, meta description, and the visible text/image alt text inside `<main>` (`content_fingerprint` in `pipeline/build_pages.py`). Header/footer, scripts, CSS classes and image URLs don't count, so site-wide tweaks don't re-date every page.

## Sealed: pack arts, blisters, sealed collections (2026-11-27)
- `db/042_sealed_arts.sql`: `products.parent_id` + `products.art`. Each set's booster pack has two arts (David); each art is its own entry under the set-level pack (`1-booster-pack-silver-naruto` under `1-booster-pack`). Same for blister packs, and for starter decks that come in several versions (Path to Hokage Naruto / Sasuke, Quest for Power A-1…B-2).
- Kinds: `booster_pack` = loose pack, `blister_pack` = one pack in a retail blister, `blister_box` = a box of blisters (12 or 15).
- Matching (`sealed.py`): a title that names exactly one art/deck (its `match_words`) goes to that entry; one naming none (or both) goes to the set-level entry, which is the "any art" price (David). "Art set" pairs are skipped (singles only). A box's own pack count ("24 Packs", "15 Packs") no longer counts as a multi-item lot.
- PLACEHOLDERS: every entry from 042 is unconfirmed research. David checks them in **Jonin Hub → Sealed → Sealed catalog**, where name, art and title words are editable. Art names for sets 3, 5 (one), 15, 17, 18, 22, 24, 25, 27, 28 still to come. Diamond/wavy foils have nothing to do with pack art (David).
- Photos: `sealed_photo.py` cuts every picked sealed photo out of its background and cleans it (rembg + hole fill + outline fill so white art and silver crimps survive). The Sync workflow installs rembg only when a picked photo is waiting. `split(img, n)` splits side-by-side items by hand (the first Path to Hokage photo: silver + gold). Hand-cleaned photos live in `public/img/sealed/`.
- Collecting: `collection_sealed` (private per member, like `collection_items`); `public/sealed-coll.js` puts a Have (count) / Want box on every sealed page. PLACEHOLDER: no edition picker yet, and sealed isn't in My collection or collection value yet.
- Per-set template (David 2026-11-27, `db/044_sealed_set_slots.sql`): every main set gets a booster box, two booster pack art slots, a set-level blister + two blister art slots, theme decks as the set has them, and set extras (3-pack blisters: kind `blister_3pack`) as David names them. Unnamed slots and unconfirmed blisters are hidden (`public = false`) until David names them and ticks On site in Jonin Hub → Cards → Sealed catalog. Hidden entries still collect sales, so a sale shows an item exists.
