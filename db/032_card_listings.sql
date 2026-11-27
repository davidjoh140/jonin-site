-- Active eBay listings for one card, free for everyone on card pages ("For sale now", 2026-11-26).
-- The listings table itself stays private; this function exposes only active, not-yet-ended listings,
-- cheapest first (David's call). Limit 50 is a PLACEHOLDER.
create or replace function public.card_listings(p_card_id text)
returns table(title text, price numeric, kind text, ends_at timestamptz, best_offer boolean, bids integer,
              printing text, edition text, grader text, grade text, item_id text, image_url text)
language sql stable security definer set search_path = public as $$
  select l.title, l.price, l.kind, l.ends_at, coalesce(l.best_offer,false), coalesce(l.bids,0),
         coalesce(l.printing,''), coalesce(l.edition,''), coalesce(nullif(l.grader,''),'Raw'), coalesce(l.grade,''),
         substring(l.url from '/itm/(?:[^/?]*/)?(\d{9,13})'),
         case when l.image_url ~ '^https://i\.ebayimg\.com/' then l.image_url end
  from listings l
  where l.card_id = p_card_id and l.state = 'active' and l.price > 0
    and (l.ends_at is null or l.ends_at > now())
    and l.url ~ '^https://(www\.)?ebay\.com/itm/'
  order by l.price asc
  limit 50;
$$;
revoke all on function public.card_listings(text) from public;
grant execute on function public.card_listings(text) to anon, authenticated;
