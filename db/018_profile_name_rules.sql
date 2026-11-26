-- Applied to Supabase on 2026-11-26 (migration profile_name_rules). Kept here as the record.
-- Profile name rules, enforced by the database so they hold no matter how the change is sent:
--   * "David" and "david" are the same name (case-insensitive unique index).
--   * Cooldown: after changing your name you wait handle_cooldown_days() before changing it again.
--     Your first change is free, so people with an auto-made name (from their email) can fix it right away.
--   * Protected names can't be taken (exact match, any capitals): profile_reserved_handles().
--   * Admins (is_admin()) and the service role skip the cooldown and protected list.
-- PLACEHOLDER settings, David to set: 30-day cooldown and the protected list below.

create unique index if not exists profiles_handle_lower_key on public.profiles (lower(handle));

alter table public.profiles add column if not exists handle_changed_at timestamptz;

create or replace function public.handle_cooldown_days() returns int
language sql immutable as $$ select 30 $$;

create or replace function public.profile_reserved_handles() returns text[]
language sql immutable as $$
  select array['jonin','joninofficial','jonin_official','joninteam','jonin_team','joninsupport','jonin_support',
               'admin','administrator','mod','moderator','staff','support','help','official','team','owner',
               'system','root','null','undefined','anonymous','everyone','premium','founder','founding',
               'bandai','shueisha','kishimoto','masashi_kishimoto']
$$;

-- When a name can be changed next (null = now). Lets the site show the date.
create or replace function public.my_handle_next_change() returns timestamptz
language sql stable security definer set search_path = public as $$
  select case when p.handle_changed_at is null then null
              when p.handle_changed_at + make_interval(days => public.handle_cooldown_days()) <= now() then null
              else p.handle_changed_at + make_interval(days => public.handle_cooldown_days()) end
  from public.profiles p where p.id = auth.uid()
$$;
grant execute on function public.my_handle_next_change() to authenticated;

create or replace function public.profiles_handle_rules() returns trigger
language plpgsql security definer set search_path = public as $$
declare privileged boolean := auth.uid() is null or coalesce(public.is_admin(), false);
begin
  if tg_op = 'INSERT' then
    -- sign-up (runs without auth.uid()): never fail, just swap out protected names
    if new.handle is not null and lower(new.handle) = any(public.profile_reserved_handles()) then
      new.handle := left(new.handle, 18) || (floor(random() * 9000) + 1000)::int::text;
    end if;
    return new;
  end if;
  if new.handle is distinct from old.handle then
    if not privileged then
      if new.handle is not null and lower(new.handle) = any(public.profile_reserved_handles()) then
        raise exception 'That name is reserved' using errcode = 'P0001', hint = 'reserved';
      end if;
      if old.handle_changed_at is not null
         and old.handle_changed_at + make_interval(days => public.handle_cooldown_days()) > now() then
        raise exception 'You can change your name again on %', to_char(old.handle_changed_at + make_interval(days => public.handle_cooldown_days()), 'Mon DD')
          using errcode = 'P0001', hint = 'cooldown';
      end if;
    end if;
    new.handle_changed_at := now();
  elsif not privileged then
    new.handle_changed_at := old.handle_changed_at;  -- can't be reset from the browser
  end if;
  return new;
end $$;

drop trigger if exists profiles_handle_rules on public.profiles;
create trigger profiles_handle_rules before insert or update on public.profiles
  for each row execute function public.profiles_handle_rules();
