-- Jonin card database schema (Supabase / Postgres)
create table if not exists sets (
  id text primary key,            -- '1'..'28', 'TP1', 'T1', 'P'
  name text not null,
  code text,
  kind text not null,             -- Main | Tournament pack | Tin | Promo
  released text,                  -- display string, e.g. 'Apr 28, 2006' or '2009 (approx.)'
  foils text[] default '{}',
  first_edition text,
  unlimited text,
  card_count int,
  rarity_counts jsonb default '{}'::jsonb,
  notes text,
  symbol_url text,
  sort int
);
create table if not exists cards (
  id text primary key,            -- '<set>:<number>'
  set_id text not null references sets(id),
  number text not null,
  name text not null,
  type text,                      -- Ninja | Jutsu | Mission | Client | Promo
  rarity text,
  printings text[] default '{}',  -- e.g. Normal, Diamond foil, Wavy foil
  editions text[] default '{}',
  note text,
  character text                  -- derived base character name
);
create index if not exists cards_set_idx on cards(set_id);
create index if not exists cards_name_idx on cards(lower(name));
create table if not exists scans (
  id bigint generated always as identity primary key,
  card_id text not null references cards(id),
  printing text,
  edition text,
  image_url text not null,
  source text,                    -- Own scan | Collector | PSA | Online | Other
  credit text,
  public boolean default false,   -- only approved scans show on the site
  created_at timestamptz default now()
);
create table if not exists sales (
  id bigint generated always as identity primary key,
  card_id text references cards(id),
  title text, price numeric, currency text default 'USD',
  grade text, sold_at timestamptz, source text, url text,
  created_at timestamptz default now()
);
create table if not exists listings (
  id bigint generated always as identity primary key,
  card_id text references cards(id),
  title text, price numeric, currency text default 'USD',
  grade text, kind text, ends_at timestamptz, source text, url text unique,
  seen_at timestamptz default now()
);
-- Security: public can read sets, cards and approved scans only. Sales/listings stay private.
alter table sets enable row level security;
alter table cards enable row level security;
alter table scans enable row level security;
alter table sales enable row level security;
alter table listings enable row level security;
drop policy if exists "public read sets" on sets;
create policy "public read sets" on sets for select using (true);
drop policy if exists "public read cards" on cards;
create policy "public read cards" on cards for select using (true);
drop policy if exists "public read approved scans" on scans;
create policy "public read approved scans" on scans for select using (public = true);
