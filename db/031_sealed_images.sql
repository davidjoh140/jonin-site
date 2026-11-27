-- Sealed product photos (2026-11-27). find_sealed_images.py queues eBay listing photos per product; David picks one in
-- Jonin Hub → Review → Sealed → Photos (status approved); find_sealed_images.py --mirror (Sync workflow) copies it to
-- R2 (img.jonin.cards/site/sealed/...) and sets products.image_url. No public access.
create table if not exists sealed_image_candidates (
  id bigint generated always as identity primary key,
  product_id text not null references products(id) on update cascade on delete cascade,
  image_url text not null,
  source_url text, title text, note text, thumb_b64 text,
  status text not null default 'pending' check (status in ('pending','approved','rejected')),
  r2_url text,
  created_at timestamptz not null default now(), reviewed_at timestamptz,
  unique (product_id, image_url)
);
create index if not exists sealed_image_candidates_status on sealed_image_candidates (status, product_id);
alter table sealed_image_candidates enable row level security;
revoke all on sealed_image_candidates from anon, authenticated;
