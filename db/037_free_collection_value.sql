-- Collection value free for every signed-in member (David, 2026-11-27). The spreadsheet export and badge stay Jonin Club.
-- Totals only: the per-card estimates behind them stay Club, so nobody can add a card just to read its price.
-- Same rules as the Club view in index.html (collValue/estCond/estFor):
--   haves: each copy priced by its condition estimate (price_estimates_cond, exact printing + edition, blank = Unlimited);
--     copies past the stored conditions count as NM; no estimate = unpriced.
--   slabs: same grader + grade + printing, exact edition first, else the most-sold edition (PLACEHOLDER fallback).
create or replace function public.my_collection_value()
returns table(raw numeric, raw_n int, raw_all int, slab numeric, slab_n int, slab_all int)
language sql stable security definer set search_path to 'public' as $$
  with me as (select auth.uid() uid),
  copies as (
    select ci.card_id, coalesce(ci.printing,'') pr, coalesce(nullif(ci.edition,''),'Unlimited') ed,
           coalesce(case when (ci.conds)[g] = any(array['NM','LP','MP','HP','DMG']) then (ci.conds)[g] end, 'NM') cond
    from collection_items ci, me, generate_series(1, greatest(ci.qty,0)) g
    where ci.user_id = me.uid and ci.kind = 'have'
  ),
  priced as (
    select c.*, (select e.estimate from price_estimates_cond e
                 where e.card_id = c.card_id and coalesce(e.printing,'') = c.pr
                   and coalesce(nullif(e.edition,''),'Unlimited') = c.ed and e.condition = c.cond limit 1) est
    from copies c
  ),
  slabs as (
    select s.id, (select e.estimate from price_estimates e
                  where e.card_id = s.card_id and e.printing = coalesce(s.printing,'') and coalesce(e.grader,'Raw') = coalesce(s.grader,'Raw')
                    and (coalesce(s.grader,'Raw') = 'Raw' or e.grade = coalesce(s.grade,''))
                  order by (coalesce(nullif(e.edition,''),'Unlimited') = coalesce(nullif(s.edition,''),'Unlimited')) desc, e.sales_count desc
                  limit 1) est
    from collection_slabs s, me where s.user_id = me.uid
  )
  select (select coalesce(sum(est),0) from priced), (select count(est)::int from priced), (select count(*)::int from priced),
         (select coalesce(sum(est),0) from slabs), (select count(est)::int from slabs), (select count(*)::int from slabs)
  where (select uid from me) is not null;
$$;
revoke all on function public.my_collection_value() from public, anon;
grant execute on function public.my_collection_value() to authenticated;
