-- Sealed product database and prices (2026-11-27).
-- products: the one master list of sealed items (booster packs and boxes, theme and starter decks, tins,
--   tournament packs). It already held the decks cards come in (cards.json "deck"); this adds what the
--   /sealed/ pages need. Rows with confirmed = false are PLACEHOLDERS for David to check.
-- sealed_listings: eBay listings for sealed items being watched until they end (like listings).
-- sealed_sales: one row per sold sealed item, pending until David OKs or vetoes it in Jonin Hub → Sealed.
-- sealed_price_ranges: per product + edition, rebuilt by refresh_sealed_prices() from approved sales only.
-- None of the sealed tables are readable with the publishable key: export_cards.py (service key) writes
-- what the site shows into public/sealed.json.

alter table products
  add column if not exists slug text,
  add column if not exists released text,
  add column if not exists contents text,          -- e.g. "24 packs of 10 cards" (to confirm per product)
  add column if not exists msrp numeric,
  add column if not exists image_url text,
  add column if not exists match_words text[] not null default '{}',   -- extra title words that point to this product
  add column if not exists sort int not null default 0,
  add column if not exists public boolean not null default true,
  add column if not exists updated_at timestamptz not null default now();

-- slugs for the decks that were already here, e.g. "11-blazing" -> "approaching-wind-theme-deck-blazing-flame"
update products set slug = trim(both '-' from regexp_replace(lower(replace(name, ':', '')), '[^a-z0-9]+', '-', 'g'))
 where slug is null;

-- deck names on their own ("Blazing Flame") help match titles that skip the set name
update products set match_words = array[lower(trim(split_part(name, ':', 2)))]
 where kind in ('theme','starter') and position(':' in name) > 0 and match_words = '{}';

-- PLACEHOLDER catalog: one booster pack and one booster box for every main set, the four tins and the four
-- tournament packs. Contents, MSRP and release left blank until David confirms them.
insert into products (id, set_id, name, kind, confirmed, note, slug, released, sort)
select s.id || '-booster-pack', s.id, s.name || ' booster pack', 'booster_pack', false,
       'Placeholder: pack contents to confirm', trim(both '-' from regexp_replace(lower(s.name), '[^a-z0-9]+', '-', 'g')) || '-booster-pack',
       s.released, s.sort * 10 + 1
  from sets s where s.kind = 'Main'
on conflict (id) do nothing;

insert into products (id, set_id, name, kind, confirmed, note, slug, released, sort)
select s.id || '-booster-box', s.id, s.name || ' booster box', 'booster_box', false,
       'Placeholder: packs per box to confirm', trim(both '-' from regexp_replace(lower(s.name), '[^a-z0-9]+', '-', 'g')) || '-booster-box',
       s.released, s.sort * 10 + 2
  from sets s where s.kind = 'Main'
on conflict (id) do nothing;

insert into products (id, set_id, name, kind, confirmed, note, slug, released, sort, match_words)
select lower(s.id) || '-tin', s.id, regexp_replace(s.name, '\s*\(tin\)\s*$', '', 'i') || ' tin', 'tin', false,
       'Placeholder: tin contents to confirm', trim(both '-' from regexp_replace(lower(regexp_replace(s.name, '\s*\(tin\)\s*$', '', 'i')), '[^a-z0-9]+', '-', 'g')) || '-tin',
       s.released, s.sort * 10, array[lower(regexp_replace(s.name, '\s*\(tin\)\s*$', '', 'i'))]
  from sets s where s.kind = 'Tin'
on conflict (id) do nothing;

insert into products (id, set_id, name, kind, confirmed, note, slug, released, sort)
select lower(s.id) || '-pack', s.id, s.name, 'tournament_pack', false,
       'Placeholder: given out at tournaments; contents to confirm', 'tournament-pack-' || substr(lower(s.id), 3),
       s.released, s.sort * 10
  from sets s where s.kind = 'Tournament pack'
on conflict (id) do nothing;

-- decks sort right after their set's boxes
update products p set sort = s.sort * 10 + 3 from sets s where s.id = p.set_id and p.kind in ('theme','starter') and p.sort = 0;

create unique index if not exists products_slug_key on products (slug);

-- ---------------------------------------------------------------- listings + sales
create table if not exists sealed_listings (
  id bigint generated always as identity primary key,
  external_id text not null unique,
  product_id text not null references products(id) on update cascade,
  title text, price numeric, currency text default 'USD', edition text default '',
  kind text, bids int default 0, best_offer boolean default false, ends_at timestamptz,
  source text default 'eBay', url text, image_url text, confidence numeric, match_reason text,
  seen_at timestamptz, first_seen_at timestamptz default now(), state text not null default 'active'
);
create index if not exists sealed_listings_state on sealed_listings (state, product_id);

create table if not exists sealed_sales (
  id bigint generated always as identity primary key,
  external_id text unique,                      -- null for sales David adds by hand
  product_id text not null references products(id) on update cascade,
  title text, price numeric not null, currency text default 'USD', edition text default '',
  sold_at timestamptz not null default now(), source text default 'eBay', url text, image_url text, thumb_b64 text,
  sale_type text, price_basis text, bids int, confidence numeric, match_reason text,
  status text not null default 'pending' check (status in ('pending','approved','rejected')),
  reviewed_at timestamptz, review_note text, created_at timestamptz not null default now()
);
create index if not exists sealed_sales_status on sealed_sales (status, product_id);

create table if not exists sealed_price_ranges (
  product_id text not null references products(id) on update cascade on delete cascade,
  edition text not null default '',
  low numeric, high numeric, avg_price numeric, last_price numeric,
  sales_count int, last_sold_at timestamptz, updated_at timestamptz default now(),
  primary key (product_id, edition)
);

alter table sealed_listings enable row level security;
alter table sealed_sales enable row level security;
alter table sealed_price_ranges enable row level security;
revoke all on sealed_listings, sealed_sales, sealed_price_ranges from anon, authenticated;

-- Same window as card ranges: sales from the last 180 days, or the 3 newest if none are that recent.
-- 4+ sales use the middle half (25th–75th percentile) so one odd sale doesn't stretch the range.
create or replace function refresh_sealed_prices() returns int
language plpgsql security definer set search_path = public as $$
declare n int;
begin
  delete from sealed_price_ranges where true;
  with ranked as (
    select s.*, row_number() over (partition by product_id, coalesce(edition,'') order by sold_at desc) rn,
           count(*) filter (where sold_at > now() - interval '180 days') over (partition by product_id, coalesce(edition,'')) recent
      from sealed_sales s where status = 'approved' and price > 0
  ), used as (
    select * from ranked where (recent > 0 and sold_at > now() - interval '180 days') or (recent = 0 and rn <= 3)
  )
  insert into sealed_price_ranges (product_id, edition, low, high, avg_price, last_price, sales_count, last_sold_at)
  select product_id, coalesce(edition,''),
         round((case when count(*) >= 4 then percentile_cont(0.25) within group (order by price::float8) else min(price)::float8 end)::numeric, 2),
         round((case when count(*) >= 4 then percentile_cont(0.75) within group (order by price::float8) else max(price)::float8 end)::numeric, 2),
         round(avg(price), 2),
         (array_agg(price order by sold_at desc))[1],
         count(*), max(sold_at)
    from used group by 1, 2;
  get diagnostics n = row_count;
  return n;
end $$;
revoke execute on function refresh_sealed_prices() from anon, authenticated;

-- Follow-up (same day, applied with execute_sql): slugs without the apostrophe split ("heros-ascension", not
-- "hero-s-ascension"), and deck-name words for the four Dream Legacy starters and the Myoboku deck.
update products set slug = trim(both '-' from regexp_replace(lower(replace(replace(replace(name, ':', ''), '''', ''), '’', '')), '[^a-z0-9]+', '-', 'g')), updated_at = now()
 where slug like '%-s-%' or slug ~ '-s$';
update products set match_words = array[lower(right(name, 3))] where id in ('5-a1','5-a2','5-b1','5-b2');
update products set match_words = array['myoboku'] where id = '27-myoboku';
