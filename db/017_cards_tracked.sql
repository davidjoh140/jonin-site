-- Applied to Supabase on 2026-11-26 (migration cards_tracked_ticker). Kept here as the record.
-- cards_tracked(): public totals for the homepage ticker. No per-user data.
--   cards      = every have and want copy saved to an account (sum of qty) + slabs that don't already count as a have
--   collectors = number of accounts
-- PLACEHOLDER choices to revisit with David: it's a live count (goes down if someone removes cards), admin/test
-- accounts are included, and cards marked by signed-out visitors (kept in their browser only) aren't counted.
create or replace function public.cards_tracked() returns json
language sql stable security definer set search_path = public, auth as $$
  select json_build_object(
    'cards', coalesce((select sum(qty) from public.collection_items where qty > 0), 0)
             + (select count(*) from public.collection_slabs where not counted),
    'collectors', (select count(*) from auth.users))
$$;
revoke all on function public.cards_tracked() from public;
grant execute on function public.cards_tracked() to anon, authenticated;
