-- Applied to Supabase on 2026-11-26 (migration card_milestone_scrolls). Kept here as the record.
-- 100-card bonus (David, 2026-11-26): when a member logs 100 cards they get a small scroll bonus and a thank-you popup.
--
-- What counts: different cards in your collection, haves plus slabs (same count as the 25-card sell popup).
-- Wants don't count. The bonus is logged once in xp_events and kept even if cards are removed later,
-- so removing and re-adding can't farm it.
--
-- Set by David: cards_100 = 50 scrolls (in xp_rules()).

create or replace function public.xp_rules() returns jsonb language sql immutable as $$
  select jsonb_build_object('vote_character', 5, 'feedback_accepted', 25, 'invite_signup', 50, 'cards_100', 50)
$$;

-- Different cards a member has logged (haves with qty > 0, plus slabs).
create or replace function public.logged_card_count(p_user uuid) returns int
language sql stable security definer set search_path = public as $$
  select count(*)::int from (
    select card_id from public.collection_items where user_id = p_user and kind = 'have' and qty > 0
    union
    select card_id from public.collection_slabs where user_id = p_user) c
$$;
revoke all on function public.logged_card_count(uuid) from public, anon, authenticated;

-- Called by the site after a card is saved. Gives the bonus the first time the member is at 100+.
-- Returns new=true only on that first time, so the site shows the thank-you popup once.
create or replace function public.claim_card_milestone() returns jsonb
language plpgsql security definer set search_path = public as $$
declare me uuid := auth.uid(); n int;
begin
  if me is null then return jsonb_build_object('ok', false, 'why', 'signed_out'); end if;
  n := public.logged_card_count(me);
  if n < 100 then return jsonb_build_object('ok', false, 'why', 'not_yet', 'cards', n); end if;
  insert into public.xp_events(user_id, kind, ref) values (me, 'milestone', 'cards_100') on conflict do nothing;
  return jsonb_build_object('ok', true, 'new', found, 'cards', n, 'scrolls', (public.xp_rules()->>'cards_100')::int);
end $$;
revoke all on function public.claim_card_milestone() from public, anon;
grant execute on function public.claim_card_milestone() to authenticated;

create or replace function public.user_xp(p_user uuid) returns jsonb
language sql stable security definer set search_path = public as $$
  with r as (select public.xp_rules() j),
  v as (select coalesce(array_agg(ref order by ref), '{}') chars from public.xp_events where user_id = p_user and kind = 'vote'),
  f as (select count(*)::int n from public.feedback where review = 'accepted' and credit_user = p_user),
  i as (select (public.invite_counts(p_user)->>'counted')::int n),
  m as (select exists (select 1 from public.xp_events where user_id = p_user and kind = 'milestone' and ref = 'cards_100') got),
  t as (select cardinality(v.chars) * (r.j->>'vote_character')::int + f.n * (r.j->>'feedback_accepted')::int
               + i.n * (r.j->>'invite_signup')::int + (case when m.got then (r.j->>'cards_100')::int else 0 end) xp,
               v.chars, f.n fn, i.n inv, m.got
        from r, v, f, i, m)
  select jsonb_build_object('xp', t.xp, 'points', t.xp, 'voted', to_jsonb(t.chars), 'feedback', t.fn, 'invites', t.inv,
                            'cards', public.logged_card_count(p_user), 'cards_100', t.got, 'rules', r.j)
         || public.xp_rank(t.xp)
  from t, r
$$;
revoke all on function public.user_xp(uuid) from public, anon, authenticated;
