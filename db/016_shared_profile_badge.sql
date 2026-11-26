-- Applied to Supabase on 2026-11-26 (migration shared_profile_badge). Kept here as the record.
-- Premium badge (David, 2026-11-26): shared_profile() now also returns badge = 'founding' | 'premium' | null
--   (active membership; founding wins), so shared lists show the member's badge.
drop function if exists public.shared_profile(text);
create function public.shared_profile(slug text)
returns table(handle text, instagram text, fav_character text, avatar text, badge text)
language sql stable security definer set search_path = public as $$
  select p.handle, p.instagram, p.fav_character, p.avatar,
    case when m.active and (m.until is null or m.until > now()) then case when m.founding then 'founding' else 'premium' end end
  from public.profiles p left join public.memberships m on m.user_id = p.id
  where p.share_slug = slug and p.sharing
$$;
revoke all on function public.shared_profile(text) from public;
grant execute on function public.shared_profile(text) to anon, authenticated;
