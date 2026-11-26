-- Founding members (David, 2026-11-26): the first 20 sign-ups get Premium free, forever.
-- memberships.founding already existed. Owner/admin accounts don't use up a spot.
-- founding_spots_left(): public count for the site's offer text.
-- grant_founding_member(): on every new auth.users row, gives a founding membership while spots remain.
-- The two people who signed up before the offer (2026-11-26) were backfilled as founders #1 and #2.

create or replace function public.founding_spots_left() returns int
language sql stable security definer set search_path = public as $$
  select greatest(0, 20 - (select count(*) from public.memberships where founding))::int
$$;
revoke all on function public.founding_spots_left() from public;
grant execute on function public.founding_spots_left() to anon, authenticated;

create or replace function public.grant_founding_member() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  perform pg_advisory_xact_lock(hashtext('jonin_founding'));
  if (select count(*) from public.memberships where founding) < 20 then
    insert into public.memberships(user_id, tier, founding, active, since, until, source, note)
      values (new.id, 'premium', true, true, now(), null, 'founding', 'Founding member')
      on conflict (user_id) do update set founding = true, active = true, until = null;
  end if;
  return new;
end $$;
revoke all on function public.grant_founding_member() from public, anon, authenticated;

drop trigger if exists on_signup_founding_member on auth.users;
create trigger on_signup_founding_member after insert on auth.users
  for each row execute function public.grant_founding_member();

insert into public.memberships(user_id, tier, founding, active, since, until, source, note)
select u.id, 'premium', true, true, now(), null, 'founding', 'Founding member (signed up before the offer)'
from auth.users u
where not exists (select 1 from public.admins a where a.user_id = u.id)
on conflict (user_id) do update set founding = true, active = true, until = null;

-- Follow-up (migration founding_members_skip_admins): the owner test account already had founding = true,
-- so spots are counted by founding_count(), which skips admins. 18 spots left after the backfill.
create or replace function public.founding_count() returns int
language sql stable security definer set search_path = public as $$
  select count(*)::int from public.memberships m
  where m.founding and not exists (select 1 from public.admins a where a.user_id = m.user_id)
$$;
revoke all on function public.founding_count() from public, anon, authenticated;
create or replace function public.founding_spots_left() returns int
language sql stable security definer set search_path = public as $$
  select greatest(0, 20 - public.founding_count())::int
$$;
-- grant_founding_member() now checks public.founding_count() < 20 (same body otherwise).
