-- Applied to Supabase on 2026-11-26 (migration scroll_leaderboard). Kept here as the record. /leaderboard/ reads this.
-- David (2026-11-26): only members who turned on sharing appear (sharing is off by default).
-- Scrolls leaderboard. PLACEHOLDERS, David to set: top 25; only members with at least 1 scroll; admin accounts
-- left off; ties share a place (the earlier member is listed first).
-- Shows name, picture, status badge, rank and scrolls only. Nothing from collections or slabs.
-- me_hidden: true when the signed-in member isn't sharing, so the page can tell them how to appear.
create or replace function public.scroll_leaderboard(p_limit int default 25) returns jsonb
language sql stable security definer set search_path = public as $$
  with s as (
    select p.id, p.handle, p.fav_character fav, p.avatar, p.created_at,
      p.share_slug slug,
      case when m.active and (m.until is null or m.until > now()) then case when m.founding then 'founding' else 'premium' end end badge,
      x->>'rank' rank, (x->>'xp')::int xp
    from public.profiles p
    left join public.memberships m on m.user_id = p.id
    cross join lateral (select public.user_xp(p.id) x) xx
    where p.sharing and not exists (select 1 from public.admins a where a.user_id = p.id)
  ),
  r as (select s.*, rank() over (order by xp desc) pos, row_number() over (order by xp desc, created_at) ord from s where xp > 0)
  select jsonb_build_object(
    'rows', coalesce((select jsonb_agg(jsonb_build_object('pos', pos, 'handle', handle, 'fav', fav, 'avatar', avatar, 'slug', slug,
                       'badge', badge, 'rank', rank, 'xp', xp, 'me', id = auth.uid()) order by ord)
                      from r where ord <= least(greatest(coalesce(p_limit, 25), 1), 100)), '[]'::jsonb),
    'total', (select count(*) from r),
    'me_hidden', exists (select 1 from public.profiles p where p.id = auth.uid() and not p.sharing),
    'me', (select jsonb_build_object('pos', pos, 'handle', handle, 'fav', fav, 'avatar', avatar, 'slug', slug, 'badge', badge,
                  'rank', rank, 'xp', xp, 'me', true, 'shown', ord <= least(greatest(coalesce(p_limit, 25), 1), 100))
           from r where id = auth.uid()))
$$;
revoke all on function public.scroll_leaderboard(int) from public;
grant execute on function public.scroll_leaderboard(int) to anon, authenticated;
