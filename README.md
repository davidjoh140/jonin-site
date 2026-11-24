# jonin.cards

Public card database for the original Bandai Naruto CCG (2006–2013).

- `public/` — the static site served at jonin.cards (Cloudflare Pages, build output directory `public`, no build command).
- `public/cards.json` — card data the site reads (sets, cards, printings). Exported from the Supabase back end.
- `db/schema.sql` — Supabase tables (sets, cards, scans, sales, listings) with public read access only for sets, cards and approved scans.
- `db/seed.sql` — initial import of all sets and cards.
