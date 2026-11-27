-- Set intel (2026-11-27): confirmed facts about a set, shown in the "Set intel" section of /set/<id>/.
-- Comes from the Jonin Hub intel feed: an item David locks that names a set gets a row here (id = the Hub item id, e.g. i068).
-- Only status 'live' ships to the site (export_cards.py -> pipeline/set_intel.json -> build_pages.py).
create table if not exists public.set_intel (
  id          text primary key,
  set_id      text not null references public.sets(id) on update cascade,
  field       text not null default 'Notes',      -- section heading on the page, e.g. 'Rarity & print run', '1st Edition'
  topic       text not null,                       -- short title
  detail      text not null,                       -- the confirmed fact, in Jonin's words
  source_name text,                                -- e.g. ICv2
  source_url  text,
  noted_on    date,
  status      text not null default 'live' check (status in ('live', 'hidden')),
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);
create index if not exists set_intel_set on public.set_intel (set_id) where status = 'live';
alter table public.set_intel enable row level security;
drop policy if exists "public read live set intel" on public.set_intel;
create policy "public read live set intel" on public.set_intel for select using (status = 'live');
