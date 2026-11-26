-- Applied to Supabase on 2026-11-26 (migrations collection_condition_columns, cond_estimates_and_comps_functions,
-- price_ranges_also_refresh_cond_estimates). Kept here as the record.
-- Card condition in collections (David, 2026-11-26):
--   collection_items.conds = one condition per have copy (NM / LP / MP / HP / DMG), in order. New copies start NM;
--   missing entries count as NM. Slabs have no condition (the grade covers it).
--   price_estimates_cond = Premium RAW estimate per version split by condition, from approved price-check sales whose
--   condition is known (same newest-weighted rule as price_estimates). refresh_price_ranges() rebuilds it.
--   PLACEHOLDER: a condition with no sales falls back to the version's all-conditions estimate, labelled on the site.
--   member_card_comps(card_id) = member_card_sales plus each sale's condition, so collection copies link to matching comps.
alter table public.collection_items add column if not exists conds text[];
alter table public.collection_items add constraint collection_items_conds_check
  check (conds is null or (cardinality(conds) <= 999 and conds <@ array['NM','LP','MP','HP','DMG']::text[]));
create table if not exists public.price_estimates_cond (
  card_id text not null references public.cards(id) on delete cascade,
  printing text not null, edition text not null, condition text not null,
  estimate numeric, sales_count int, last_sold_at timestamptz, last_price numeric,
  primary key (card_id, printing, edition, condition));
alter table public.price_estimates_cond enable row level security;
create policy "members read cond estimates" on public.price_estimates_cond for select to authenticated
  using (exists (select 1 from public.memberships m where m.user_id = auth.uid() and m.active and (m.until is null or m.until > now())));
grant select on public.price_estimates_cond to authenticated;
-- refresh_price_estimates_cond(half_life_days default 30): rebuilds price_estimates_cond (see Supabase for the body).
-- member_card_comps(p_card_id): members only; returns version, grader, grade, price, sold_at, sale_type, url, condition.
-- refresh_price_ranges(): now also calls refresh_price_estimates_cond() after refresh_price_estimates().
