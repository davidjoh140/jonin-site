-- Applied to Supabase on 2026-11-26 (migration admin_grant_tier_and_upgrade_notice). Kept here as the record.
-- David 2026-11-26: give Jonin Club or Founding member from /admin/ in one step; the member sees a one-time popup
-- next time they open jonin.cards signed in.
--   memberships.upgrade_notice: 'premium' | 'founding' | null. Set by admin_grant (and by claim_premium_invite when an
--     invited email signs up); cleared by dismiss_upgrade_notice() as soon as acct.js shows the popup.
--   admin_grant(p_email, p_until, p_note, p_tier default 'premium'): p_tier 'founding' sets founding = true and no end date.
--     Giving Jonin Club to someone who is already founding never removes founding.
--   premium_invites.founding: carries Founding over for emails with no account yet.
-- Note: manual founding grants count toward founding_count(), which the site uses for "founding spots left".

alter table public.memberships add column if not exists upgrade_notice text;
alter table public.premium_invites add column if not exists founding boolean not null default false;

drop function if exists public.admin_grant(text, timestamptz, text);
create function public.admin_grant(p_email text, p_until timestamptz default null, p_note text default null, p_tier text default 'premium')
returns text language plpgsql security definer set search_path = public, auth as $$
declare uid uuid; e text := lower(trim(p_email)); fnd boolean := lower(coalesce(p_tier,'premium')) = 'founding';
begin
  if not public.is_admin() then raise exception 'not allowed'; end if;
  if lower(coalesce(p_tier,'premium')) not in ('premium','founding') then raise exception 'tier must be premium or founding'; end if;
  if e is null or e !~ '^[^@\s]+@[^@\s]+\.[^@\s]+$' then raise exception 'enter a valid email'; end if;
  select id into uid from auth.users where lower(email) = e;
  if uid is null then
    insert into public.premium_invites(email, until, note, founding) values (e, case when fnd then null else p_until end, p_note, fnd)
      on conflict (email) do update set until = excluded.until, note = excluded.note, founding = excluded.founding,
        claimed_at = null, claimed_by = null, created_at = now();
    return 'invited';
  end if;
  insert into public.memberships(user_id, tier, founding, active, since, until, source, note, upgrade_notice)
    values (uid, 'premium', fnd, true, now(), case when fnd then null else p_until end, 'free', p_note, case when fnd then 'founding' else 'premium' end)
    on conflict (user_id) do update set active = true,
      founding = public.memberships.founding or fnd,
      until = case when public.memberships.founding or fnd then null else excluded.until end,
      source = 'free',
      note = coalesce(excluded.note, public.memberships.note),
      since = case when public.memberships.active then public.memberships.since else now() end,
      upgrade_notice = case when public.memberships.founding or fnd then 'founding' else 'premium' end;
  return 'granted';
end $$;
revoke all on function public.admin_grant(text, timestamptz, text, text) from public;
grant execute on function public.admin_grant(text, timestamptz, text, text) to authenticated;

create or replace function public.claim_premium_invite()
returns trigger language plpgsql security definer set search_path = public as $$
declare i public.premium_invites;
begin
  select * into i from public.premium_invites where email = lower(new.email) and claimed_at is null;
  if found then
    insert into public.memberships(user_id, tier, founding, active, since, until, source, note, upgrade_notice)
      values (new.id, i.tier, i.founding, true, now(), i.until, 'free', i.note, case when i.founding then 'founding' else 'premium' end)
      on conflict (user_id) do update set active = true, founding = public.memberships.founding or i.founding,
        until = case when public.memberships.founding or i.founding then null else excluded.until end, source = 'free',
        upgrade_notice = case when public.memberships.founding or i.founding then 'founding' else 'premium' end;
    update public.premium_invites set claimed_at = now(), claimed_by = new.id where email = i.email;
  end if;
  return new;
end $$;

create or replace function public.my_upgrade_notice()
returns text language sql stable security definer set search_path = public as $$
  select m.upgrade_notice from public.memberships m
  where m.user_id = auth.uid() and m.active and (m.until is null or m.until > now())
$$;
create or replace function public.dismiss_upgrade_notice()
returns void language sql security definer set search_path = public as $$
  update public.memberships set upgrade_notice = null where user_id = auth.uid()
$$;
revoke all on function public.my_upgrade_notice() from public;
revoke all on function public.dismiss_upgrade_notice() from public;
grant execute on function public.my_upgrade_notice() to authenticated;
grant execute on function public.dismiss_upgrade_notice() to authenticated;
