-- Jonin Club pricing (David, 2026-11-27): average sale price + an estimate that considers current listings.
-- Rule David chose: the sale-based estimate can't sit above the cheapest current Buy It Now listing of the SAME version
-- (card + printing + edition + grader + grade). Auctions don't count (their price isn't an ask).
-- Raw versions only count Near Mint listings, slabs any listing of the same grade, non-English listings never count
-- (a first run let damaged/played copies and a French card drag estimates down).
-- PLACEHOLDERS for David: those rules, listing match confidence >= 0.8; avg_price = plain average of every approved sale of that
-- version, all time; the condition estimates (price_estimates_cond) are not capped yet.
alter table price_estimates add column if not exists avg_price numeric;
alter table price_estimates add column if not exists sales_estimate numeric;   -- before the listing cap
alter table price_estimates add column if not exists listing_cap numeric;      -- cheapest matching listing, when it lowered the estimate

create or replace function public.refresh_price_estimates(half_life_days numeric default 30)
returns integer language plpgsql security definer set search_path to 'public' as $function$
declare n int;
begin
  delete from price_estimates where true;
  with base as (
    select s.*, coalesce(printing,'') pr, coalesce(edition,'') ed, coalesce(grader,'Raw') gr, coalesce(grade,'') gd,
           row_number() over (partition by card_id, coalesce(printing,''), coalesce(edition,''), coalesce(grader,'Raw'), coalesce(grade,'') order by sold_at desc) rn,
           count(*) filter (where sold_at > now() - interval '365 days')
             over (partition by card_id, coalesce(printing,''), coalesce(edition,''), coalesce(grader,'Raw'), coalesce(grade,'')) recent
    from sales s
    where status = 'approved' and card_id is not null and price > 0
      and coalesce(printing,'') <> '?' and coalesce(edition,'') <> '?'
  ), used as (
    select *, power(0.5, extract(epoch from (now() - sold_at)) / 86400.0 / half_life_days) w
    from base where (recent > 0 and sold_at > now() - interval '365 days') or (recent = 0 and rn <= 3)
  ), est as (
    select card_id, pr, ed, gr, gd,
           round((sum(price * w) / nullif(sum(w), 0))::numeric, 2) e,
           count(*) c, max(sold_at) ls, (array_agg(price order by sold_at desc))[1] lp
    from used group by 1,2,3,4,5
  ), av as (
    select card_id, pr, ed, gr, gd, round(avg(price)::numeric, 2) a from base group by 1,2,3,4,5
  ), ask as (
    select card_id, coalesce(printing,'') pr, coalesce(edition,'') ed, coalesce(nullif(grader,''),'Raw') gr, coalesce(grade,'') gd,
           min(price) p
    from listings
    where state = 'active' and kind = 'FIXED_PRICE' and price > 0 and coalesce(confidence,0) >= 0.8
      and (ends_at is null or ends_at > now()) and card_id is not null
      and (coalesce(nullif(grader,''),'Raw') <> 'Raw' or condition = 'NM')
      and title !~* '(french|fran[cç]ais|japanese|japan|german|deutsch|italian|spanish|espa[nñ]ol|korean|chinese)'
    group by 1,2,3,4,5
  )
  insert into price_estimates (card_id, printing, edition, grader, grade, estimate, sales_count, last_sold_at, last_price,
                               avg_price, sales_estimate, listing_cap)
  select est.card_id, est.pr, est.ed, est.gr, est.gd,
         least(est.e, coalesce(ask.p, est.e)), est.c, est.ls, est.lp,
         av.a, est.e, case when ask.p < est.e then ask.p end
  from est
  left join av using (card_id, pr, ed, gr, gd)
  left join ask using (card_id, pr, ed, gr, gd);
  get diagnostics n = row_count;
  return n;
end $function$;

select refresh_price_estimates();
