-- Applied to Supabase on 2026-11-26 (migration card_attributes). Kept here as the record.
-- Card details read off the scans (element, turn cost, hand cost, village). Each value is a guess from the scan
-- reader until David approves it on /admin/ (Card details). Only approved values reach cards.json and the site filters.
--   guess  what the scan reader read; conf its confidence (0-1); sure = the reader's own "safe to bulk approve" flag
--   value  the approved value (David can change it); status pending | approved | skipped ("can't tell")
--   box    where on the 500x700 scan the value was read {x,y,w,h}, so the review screen can zoom in on it
create table if not exists public.card_attrs (
  card_id text not null references public.cards(id) on delete cascade,
  field text not null check (field in ('element','turn_cost','hand_cost','village')),
  guess text,
  conf real,
  sure boolean not null default false,
  value text,
  status text not null default 'pending' check (status in ('pending','approved','skipped')),
  box jsonb,
  read_at timestamptz not null default now(),
  reviewed_at timestamptz,
  primary key (card_id, field)
);
alter table public.card_attrs enable row level security;   -- no public policies: admin RPCs and the service key only

-- admin_card_attrs(field): every row for one field with the card's name, set and scan, for the review screen.
create or replace function public.admin_card_attrs(p_field text)
returns table(card_id text, set_id text, number text, name text, type text, guess text, conf real, sure boolean,
              value text, status text, box jsonb)
language plpgsql stable security definer set search_path = public as $$
begin
  if not public.is_admin() then raise exception 'not allowed'; end if;
  return query
  select a.card_id, c.set_id, c.number, c.name, c.type, a.guess, a.conf, a.sure, a.value, a.status, a.box
  from public.card_attrs a join public.cards c on c.id = a.card_id
  where a.field = p_field
  order by c.sort nulls last, c.id;
end $$;

-- admin_card_attr_set(card, field, value, status): approve (with the guess or a corrected value), skip, or reopen one.
create or replace function public.admin_card_attr_set(p_card text, p_field text, p_value text, p_status text)
returns void language plpgsql security definer set search_path = public as $$
begin
  if not public.is_admin() then raise exception 'not allowed'; end if;
  update public.card_attrs
     set value = case when p_status = 'approved' then p_value else null end,
         status = p_status, reviewed_at = now()
   where card_id = p_card and field = p_field;
end $$;

-- admin_card_attr_approve_sure(field, set or null): approve every pending row the reader marked sure, with its guess.
create or replace function public.admin_card_attr_approve_sure(p_field text, p_set text default null)
returns int language plpgsql security definer set search_path = public as $$
declare n int;
begin
  if not public.is_admin() then raise exception 'not allowed'; end if;
  update public.card_attrs a
     set value = a.guess, status = 'approved', reviewed_at = now()
    from public.cards c
   where c.id = a.card_id and a.field = p_field and a.status = 'pending' and a.sure and a.guess is not null
     and (p_set is null or c.set_id = p_set);
  get diagnostics n = row_count;
  return n;
end $$;

revoke all on function public.admin_card_attrs(text) from public, anon;
revoke all on function public.admin_card_attr_set(text, text, text, text) from public, anon;
revoke all on function public.admin_card_attr_approve_sure(text, text) from public, anon;
grant execute on function public.admin_card_attrs(text) to authenticated;
grant execute on function public.admin_card_attr_set(text, text, text, text) to authenticated;
grant execute on function public.admin_card_attr_approve_sure(text, text) to authenticated;
