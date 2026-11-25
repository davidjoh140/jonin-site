-- Profile picture: one of the crops of the member's favorite character.
-- face = /chars/<fav>.webp, portrait = /theme-faces/<fav>.webp (8 characters), action = /char-art/<fav>.webp
alter table public.profiles add column if not exists avatar text
  check (avatar is null or avatar in ('face','portrait','action'));
drop function if exists public.shared_profile(text);
create function public.shared_profile(slug text)
returns table(handle text, instagram text, fav_character text, avatar text)
language sql stable security definer set search_path = public as $$
  select p.handle, p.instagram, p.fav_character, p.avatar from public.profiles p where p.share_slug = slug and p.sharing
$$;
grant execute on function public.shared_profile(text) to anon, authenticated;
