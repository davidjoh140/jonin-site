-- 002: scan pipeline + keeping every copy of the card list in step with Supabase.
-- Run once in the Supabase SQL editor, after schema.sql and seed.sql, then run 003_backfill.sql.
-- Safe to re-run.
--
-- Rule this migration sets up: Supabase is the only master card list.
--   * public/cards.json (jonin.cards) is generated from it by pipeline/export_cards.py.
--   * The Card Index and Buying Desk read it from Supabase through the Supabase connector.
--   * Scrapers can only attach images to cards that exist here (foreign keys).

-- Columns needed so cards.json can be rebuilt from Supabase exactly.
alter table sets  add column if not exists source text;        -- where the set's data came from, e.g. RetroTCG
alter table cards add column if not exists rarity_code text;   -- C, U, R, SR, UR, P, F ('' = unknown); drives site colours/filters
alter table cards add column if not exists sort int;           -- display order
create index if not exists cards_sort_idx on cards(sort);

-- Every image the scrapers find lands here first, waiting for David's yes / no.
create table if not exists scan_candidates (
  id bigint generated always as identity primary key,
  card_id text not null references cards(id) on update cascade,
  printing text,                    -- e.g. 'Diamond foil' (guessed from the listing; David can correct)
  edition text,                     -- '1st Edition' | 'Unlimited' | '' (unknown)
  source text not null,             -- 'eBay listing' | 'PSA' | 'Online' (same names as the Card Index)
  quality text not null,            -- 'placeholder' (seller photo) | 'slab' (PSA image) | 'clean'
  source_ref text not null unique,  -- 'ebay:<itemId>' / 'psa:<cert>:front' so nothing is found twice
  source_url text,                  -- listing or cert page
  credit text,
  image_path text,                  -- full-size copy in Supabase Storage, bucket 'scans'
  thumb_b64 text,                   -- small JPEG (base64) so the claude.ai review screens can show it
  confidence numeric,               -- 0..1 match confidence
  match_reason text,
  status text not null default 'pending' check (status in ('pending','approved','rejected')),
  review_note text,
  reviewed_at timestamptz,
  created_at timestamptz default now()
);
create index if not exists scan_candidates_status_idx on scan_candidates(status, card_id);

-- Approved images become public scans for jonin.cards.
alter table scans add column if not exists quality text;
alter table scans add column if not exists candidate_id bigint references scan_candidates(id);
create unique index if not exists scans_candidate_uidx on scans(candidate_id) where candidate_id is not null;

-- Approving a candidate (from the review screen) creates the public scan in one step.
create or replace function scan_candidate_approved() returns trigger language plpgsql as $$
begin
  if new.status = 'approved' and old.status is distinct from 'approved' and new.image_path is not null then
    insert into scans(card_id, printing, edition, image_url, source, credit, public, quality, candidate_id)
    values (new.card_id, new.printing, new.edition,
            'storage:scans/' || new.image_path, new.source, new.credit, true, new.quality, new.id)
    on conflict do nothing;
  elsif new.status <> 'approved' and old.status = 'approved' then
    delete from scans where candidate_id = new.id;
  end if;
  new.reviewed_at := case when new.status <> old.status then now() else new.reviewed_at end;
  return new;
end $$;
drop trigger if exists scan_candidate_approved on scan_candidates;
create trigger scan_candidate_approved before update on scan_candidates
  for each row execute function scan_candidate_approved();
-- (the BEFORE trigger inserts with candidate_id = new.id, which already exists on update)

-- Checklist changes proposed from RetroTCG (or anywhere else) wait here; nothing edits cards directly.
create table if not exists checklist_changes (
  id bigint generated always as identity primary key,
  source text not null,             -- 'RetroTCG'
  change text not null check (change in ('add_card','update_card','add_set','missing_here')),
  card_id text,
  set_id text,
  proposed jsonb,                   -- the row as the source has it
  current jsonb,                    -- the row as Supabase has it
  status text not null default 'pending' check (status in ('pending','applied','rejected')),
  created_at timestamptz default now(),
  unique (source, change, card_id, set_id)
);

-- One row per scraper / export run, so the Buying Desk can show what ran and what broke.
create table if not exists pipeline_runs (
  id bigint generated always as identity primary key,
  job text not null,
  started_at timestamptz default now(),
  finished_at timestamptz,
  stats jsonb default '{}'::jsonb,
  error text
);

-- Bump this whenever the card list changes, so every copy can tell it is stale.
create table if not exists checklist_version (id int primary key default 1 check (id = 1), version bigint not null default 1, changed_at timestamptz default now());
insert into checklist_version(id) values (1) on conflict do nothing;
create or replace function bump_checklist_version() returns trigger language plpgsql as $$
begin update checklist_version set version = version + 1, changed_at = now() where id = 1; return null; end $$;
drop trigger if exists bump_sets on sets;
create trigger bump_sets after insert or update or delete on sets for each statement execute function bump_checklist_version();
drop trigger if exists bump_cards on cards;
create trigger bump_cards after insert or update or delete on cards for each statement execute function bump_checklist_version();

-- Private by default: only the service key (GitHub Actions) and David's connector see these.
alter table scan_candidates enable row level security;
alter table checklist_changes enable row level security;
alter table pipeline_runs enable row level security;
alter table checklist_version enable row level security;
drop policy if exists "public read checklist version" on checklist_version;
create policy "public read checklist version" on checklist_version for select using (true);

-- Storage bucket for scan images (Supabase only; skipped on plain Postgres).
do $$ begin
  if exists (select 1 from information_schema.tables where table_schema = 'storage' and table_name = 'buckets') then
    insert into storage.buckets (id, name, public) values ('scans', 'scans', true) on conflict (id) do nothing;
  end if;
end $$;
