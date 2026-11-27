-- Sell form v2 (Nov 27, 2026): proper location (country + state/ZIP or city), what they're selling,
-- language, and a rough value range so the Hub can sort leads. Foil question dropped from the form
-- (column kept for old leads). Local pickup is only allowed for US sellers in NJ/NY/PA.
alter table sell_leads
  add column if not exists country text,
  add column if not exists state text,
  add column if not exists postal text,
  add column if not exists city text,
  add column if not exists selling text[] not null default '{}',
  add column if not exists language text,
  add column if not exists value_range text;

-- Sort order for value ranges (higher = bigger lead). "Not sure" and blank sort with the small ones.
create or replace function sell_value_rank(v text) returns int language sql immutable as $$
  select case v when '$10,000+' then 5 when '$2,000–10,000' then 4 when '$500–2,000' then 3
                when '$100–500' then 2 when 'Under $100' then 1 else 0 end $$;

alter table sell_leads add column if not exists value_rank int generated always as (sell_value_rank(value_range)) stored;

create or replace function public.submit_sell_lead(p jsonb)
 returns bigint language plpgsql security definer set search_path to 'public'
as $function$
declare v_id bigint; v_email text := lower(trim(p->>'email')); v_photos text[]; v_sell text[];
  v_country text := nullif(left(trim(coalesce(p->>'country','')),60),'');
  v_state text := nullif(upper(left(trim(coalesce(p->>'state','')),40)),'');
  v_postal text := nullif(left(trim(coalesce(p->>'postal','')),20),'');
  v_city text := nullif(left(trim(coalesce(p->>'city','')),80),'');
  v_handoff text := left(p->>'handoff',60); v_town text;
begin
  if coalesce(trim(p->>'name'),'')='' or v_email !~ '^[^@\s]+@[^@\s]+\.[^@\s]+$' then
    raise exception 'Please add your name and a valid email.';
  end if;
  if (select count(*) from sell_leads where lower(email)=v_email and created_at > now()-interval '1 day') >= 3 then
    raise exception 'We already have your submission. We''ll be in touch soon.';
  end if;
  select coalesce(array_agg(x),'{}') into v_photos from (
    select x from jsonb_array_elements_text(coalesce(p->'photos','[]'::jsonb)) x
    where x like 'https://cfzpayanhvvqtkuqfgof.supabase.co/storage/v1/object/public/sell-photos/%' limit 20) s;
  select coalesce(array_agg(x),'{}') into v_sell from (
    select x from jsonb_array_elements_text(coalesce(p->'selling','[]'::jsonb)) x
    where x in ('Singles','Graded slabs','Sealed')) s;
  -- Pickup only for US sellers in NJ/NY/PA; everyone else ships.
  if v_country is not null and not (v_country = 'United States' and v_state in ('NJ','NY','PA')) then
    v_handoff := 'Ship';
  end if;
  -- Old one-line location, kept so older tools still read something sensible.
  v_town := coalesce(nullif(p->>'town',''), case when v_country = 'United States'
              then concat_ws(' ', v_state, v_postal)
              else concat_ws(', ', v_city, v_country) end);
  insert into sell_leads(name,email,phone,town,country,state,postal,city,card_count,has_foils,about,handoff,
                         selling,language,value_range,photos,user_id,page)
  values (left(trim(p->>'name'),120), left(v_email,200), left(p->>'phone',40), left(v_town,80),
          v_country, v_state, v_postal, v_city,
          left(p->>'card_count',40), left(p->>'has_foils',20), left(p->>'about',4000), v_handoff,
          v_sell, left(p->>'language',30), left(p->>'value_range',30),
          v_photos, auth.uid(), left(p->>'page',200))
  returning id into v_id;
  return v_id;
end $function$;

-- Existing leads: fill in country from what we know.
update sell_leads set country='Italy', postal='04019' where id=1 and country is null;
update sell_leads set country='United States', state='CA', postal='95826' where id=2 and country is null;
