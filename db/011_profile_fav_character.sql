-- Favorite character on a profile (character page slug). Shown on the shared collection; first in the Characters filter when signed in.
alter table public.profiles add column if not exists fav_character text
  check (fav_character is null or fav_character ~ '^[a-z0-9-]{1,40}$');
drop function if exists public.shared_profile(text);
create function public.shared_profile(slug text)
returns table(handle text, instagram text, fav_character text)
language sql stable security definer set search_path = public as $$
  select p.handle, p.instagram, p.fav_character from public.profiles p where p.share_slug = slug and p.sharing
$$;
grant execute on function public.shared_profile(text) to anon, authenticated;
