-- Sold-listing photos -> card scans (applied 2026-11-26 through the Supabase connector; kept here as the record).
-- Approved sales for a printing with no public scan are queued; the fetch-sale-photos edge function downloads
-- each photo (base64) every 2 minutes; David cuts/approves them in the Buying Desk (Scans -> From sold listings),
-- which stages the cut in scan_uploads (doc_id 'sale:<sale id>') for drain-scan-uploads to publish.
create table if not exists sale_scan_queue (
  sale_id bigint primary key references sales(id) on delete cascade,
  card_id text not null references cards(id),
  printing text,
  edition text,
  image_url text not null,
  photo_b64 text,
  status text not null default 'pending' check (status in ('pending','fetched','used','skipped','superseded','error')),
  error text,
  tries int not null default 0,
  created_at timestamptz default now(),
  decided_at timestamptz
);
alter table sale_scan_queue enable row level security;  -- service role / connector only
create index if not exists sale_scan_queue_status on sale_scan_queue(status);

-- eBay photo address at a fixed size (works for both i.ebayimg.com URL styles)
create or replace function ebay_photo_url(u text, size int default 1200) returns text language sql immutable as $$
  select case
    when u ~ 'i\.ebayimg\.com/images/g/[^/]+/' then 'https://i.ebayimg.com/images/g/'||substring(u from 'images/g/([^/]+)/')||'/s-l'||size||'.jpg'
    when u ~ 'i\.ebayimg\.com/00/s/[^/]+/z/[^/]+/' then 'https://i.ebayimg.com/images/g/'||substring(u from '/z/([^/]+)/')||'/s-l'||size||'.jpg'
    else u end $$;

-- printings (card + printing + edition) with no public scan and nothing staged for upload
create or replace view printings_without_scan as
select k.id card_id, p.printing, e.edition
from cards k
cross join lateral unnest(k.printings) p(printing)
cross join lateral unnest(case when coalesce(array_length(k.editions,1),0)=0 then array[''] else k.editions end) e(edition)
where not exists (select 1 from scans s where s.card_id=k.id and s.public and s.printing=p.printing and coalesce(s.edition,'')=coalesce(e.edition,''))
  and not exists (select 1 from scan_uploads u where u.card_id=k.id and u.printing=p.printing and coalesce(u.edition,'')=coalesce(e.edition,''));

create or replace function queue_sale_scans() returns int language plpgsql security definer set search_path=public as $$
declare n int;
begin
  insert into sale_scan_queue(sale_id, card_id, printing, edition, image_url)
  select s.id, s.card_id, s.printing, coalesce(s.edition,''), ebay_photo_url(s.image_url)
  from sales s
  join printings_without_scan w on w.card_id=s.card_id and w.printing=s.printing and coalesce(w.edition,'')=coalesce(s.edition,'')
  where s.status='approved' and coalesce(s.image_url,'')<>''
  on conflict (sale_id) do nothing;
  get diagnostics n = row_count;
  -- a printing that got a scan some other way doesn't need its waiting photos any more
  update sale_scan_queue q set status='superseded', photo_b64=null, decided_at=now()
  where q.status in ('pending','fetched','error')
    and not exists (select 1 from printings_without_scan w where w.card_id=q.card_id and w.printing=q.printing and coalesce(w.edition,'')=coalesce(q.edition,''));
  return n;
end $$;

-- "Needs a scan" list: printings with approved sales but no scan and no usable photo left to cut
create or replace view scans_wanted as
select w.card_id, w.printing, nullif(w.edition,'') edition, k.name, k.number, k.set_id, st.name set_name, k.sort,
  count(s.id)::int sales, max(s.price) top_price, max(s.sold_at) last_sold,
  case when count(s.id) filter (where coalesce(s.image_url,'')<>'')=0 then 'No photo on the sales'
       when exists (select 1 from sale_scan_queue q where q.card_id=w.card_id and q.printing=w.printing and coalesce(q.edition,'')=coalesce(w.edition,'') and q.status='skipped') then 'Photos skipped'
       else 'Photo couldn''t be downloaded' end reason
from printings_without_scan w
join cards k on k.id=w.card_id
join sets st on st.id=k.set_id
join sales s on s.card_id=w.card_id and s.printing=w.printing and coalesce(s.edition,'')=coalesce(w.edition,'') and s.status='approved'
where not exists (select 1 from sale_scan_queue q where q.card_id=w.card_id and q.printing=w.printing and coalesce(q.edition,'')=coalesce(w.edition,'') and q.status in ('pending','fetched'))
group by w.card_id, w.printing, w.edition, k.name, k.number, k.set_id, st.name, k.sort;

create or replace function kick_sale_photos() returns void language plpgsql security definer set search_path=public as $$
begin
  perform queue_sale_scans();
  if exists (select 1 from sale_scan_queue where status='pending' and tries < 3) then
    perform net.http_post(
      url := 'https://cfzpayanhvvqtkuqfgof.supabase.co/functions/v1/fetch-sale-photos',
      headers := jsonb_build_object('Content-Type','application/json',
                 'x-drain-token', (select value from app_secrets where name='drain_token')),
      body := '{}'::jsonb, timeout_milliseconds := 120000);
  end if;
end $$;

select cron.schedule('sale-photos', '*/2 * * * *', 'select public.kick_sale_photos()');
