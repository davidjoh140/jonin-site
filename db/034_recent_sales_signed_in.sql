-- Free signed-in members see a card's most recent approved sales (David, 2026-11-27).
-- The free price range stays as before. Jonin Club keeps estimates by exact version and every sale.
-- Signed-out visitors get none of these rows (anon can't call it, and auth.uid() must be set).
create or replace function public.recent_card_sales(p_card_id text)
returns table(printing text, edition text, grader text, grade text, price numeric, sold_at timestamptz, sale_type text, url text)
language sql stable security definer set search_path to 'public' as $$
  select coalesce(s.printing,''), coalesce(s.edition,''), coalesce(s.grader,'Raw'), coalesce(s.grade,''),
         s.price, s.sold_at, s.sale_type, case when s.url ~ '^https://' then s.url end
  from sales s
  where s.card_id = p_card_id and s.status = 'approved' and s.price > 0 and auth.uid() is not null
  order by s.sold_at desc
  limit 10; -- PLACEHOLDER: how many recent sales free members see
$$;
revoke all on function public.recent_card_sales(text) from public, anon;
grant execute on function public.recent_card_sales(text) to authenticated;
