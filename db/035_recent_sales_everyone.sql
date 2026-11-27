-- Recent sales for everyone (David, 2026-11-27), to push affiliate-link purchases:
-- signed-out visitors see a card's last 5 approved sales, signed-in free members the last 10 (PLACEHOLDERS).
-- Current listings (card_listings) were already free for everyone. Jonin Club keeps every sale and estimates by version.
create or replace function public.recent_card_sales(p_card_id text)
returns table(printing text, edition text, grader text, grade text, price numeric, sold_at timestamptz, sale_type text, url text)
language sql stable security definer set search_path to 'public' as $$
  select coalesce(s.printing,''), coalesce(s.edition,''), coalesce(s.grader,'Raw'), coalesce(s.grade,''),
         s.price, s.sold_at, s.sale_type, case when s.url ~ '^https://' then s.url end
  from sales s
  where s.card_id = p_card_id and s.status = 'approved' and s.price > 0
  order by s.sold_at desc
  limit case when auth.uid() is null then 5 else 10 end;
$$;
grant execute on function public.recent_card_sales(text) to anon, authenticated;
