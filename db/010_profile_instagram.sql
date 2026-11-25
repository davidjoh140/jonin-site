-- Instagram handle on a profile, shown on the shared collection page.
alter table public.profiles add column if not exists instagram text
  check (instagram is null or instagram ~ '^[A-Za-z0-9._]{1,30}$');
create or replace function public.shared_profile(slug text)
returns table(handle text, instagram text)
language sql stable security definer set search_path = public as $$
  select p.handle, p.instagram from public.profiles p where p.share_slug = slug and p.sharing
$$;
grant execute on function public.shared_profile(text) to anon, authenticated;
