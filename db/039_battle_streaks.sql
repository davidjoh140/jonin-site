-- Battle streaks (David, 2026-11-27): voting in the daily battle on consecutive days builds a streak; hitting a
-- milestone pays bonus scrolls once per streak run. PLACEHOLDERS for David: 3 days = +10, 7 days = +25, 30 days = +100
-- (xp_rules streak_3 / streak_7 / streak_30). Missing a day resets the streak to 0.

-- Current streak: consecutive voted days ending today (or yesterday, so it isn't shown as broken before you vote today).
create or replace function public.battle_streak(p_user uuid) returns int
language plpgsql stable security definer set search_path = public as $$
declare dd date := battle_day(); n int := 0;
begin
  if not exists (select 1 from battle_votes where user_id = p_user and day = dd) then dd := dd - 1; end if;
  while exists (select 1 from battle_votes where user_id = p_user and day = dd) loop
    n := n + 1; dd := dd - 1;
  end loop;
  return n;
end $$;
revoke all on function public.battle_streak(uuid) from public, anon, authenticated;

create or replace function public.xp_rules() returns jsonb language sql immutable as $$
  select jsonb_build_object('vote_character', 5, 'feedback_accepted', 25, 'invite_signup', 50, 'cards_100', 50, 'daily_battle', 5,
                            'streak_3', 10, 'streak_7', 25, 'streak_30', 100)
$$;

create or replace function public.vote_battle(p_pick text) returns jsonb
language plpgsql security definer set search_path = public as $$
declare d date := battle_day(); r daily_battles; n int;
begin
  if auth.uid() is null then raise exception 'sign in to vote'; end if;
  select * into r from daily_battles where day = d;
  if not found or p_pick not in (r.a, r.b) then raise exception 'not today''s battle'; end if;
  insert into battle_votes(day, user_id, pick) values (d, auth.uid(), p_pick) on conflict do nothing;
  insert into xp_events(user_id, kind, ref) values (auth.uid(), 'battle', d::text) on conflict do nothing;
  n := battle_streak(auth.uid());
  if n in (3, 7, 30) then
    insert into xp_events(user_id, kind, ref) values (auth.uid(), 'streak_' || n, d::text) on conflict do nothing;
  end if;
  return today_battle();
end $$;
revoke all on function public.vote_battle(text) from public, anon;
grant execute on function public.vote_battle(text) to authenticated;

-- today_battle(): adds your streak and the next milestone.
create or replace function public.today_battle() returns jsonb
language plpgsql security definer set search_path = public as $$
declare d date := battle_day(); r daily_battles; me text; ca int; cb int; st int := 0;
begin
  select * into r from daily_battles where day = d;
  if not found then
    insert into daily_battles(day, a, b)
    select d, x.slug, y.slug
    from battle_characters x join battle_characters y on x.slug < y.slug
    where not exists (select 1 from daily_battles p where p.day > d - 60
                        and ((p.a = x.slug and p.b = y.slug) or (p.a = y.slug and p.b = x.slug)))
    order by random() limit 1
    on conflict (day) do nothing;
    select * into r from daily_battles where day = d;
  end if;
  if auth.uid() is not null then
    select pick into me from battle_votes where day = d and user_id = auth.uid();
    st := battle_streak(auth.uid());
  end if;
  select count(*) filter (where pick = r.a), count(*) filter (where pick = r.b) into ca, cb from battle_votes where day = d;
  return jsonb_build_object('day', d,
    'a', (select jsonb_build_object('slug', slug, 'label', label) from battle_characters where slug = r.a),
    'b', (select jsonb_build_object('slug', slug, 'label', label) from battle_characters where slug = r.b),
    'mine', me, 'signed_in', auth.uid() is not null,
    'votes', case when me is not null then jsonb_build_object('a', ca, 'b', cb) end,
    'total', ca + cb,
    'scrolls', (xp_rules()->>'daily_battle')::int,
    'streak', st,
    'next', (select jsonb_build_object('days', m, 'scrolls', (xp_rules()->>('streak_' || m))::int)
             from unnest(array[3, 7, 30]) m where m > st order by m limit 1),
    'yesterday', (select jsonb_build_object('a', y.a, 'b', y.b,
                    'va', (select count(*) from battle_votes v where v.day = y.day and v.pick = y.a),
                    'vb', (select count(*) from battle_votes v where v.day = y.day and v.pick = y.b))
                  from daily_battles y where y.day = d - 1));
end $$;
grant execute on function public.today_battle() to anon, authenticated;

-- Scroll totals: count streak bonuses.
create or replace function public.user_xp(p_user uuid) returns jsonb
language sql stable security definer set search_path to 'public' as $function$
  with r as (select public.xp_rules() j),
  v as (select coalesce(array_agg(ref order by ref), '{}') chars from public.xp_events where user_id = p_user and kind = 'vote'),
  f as (select count(*)::int n from public.feedback where review = 'accepted' and credit_user = p_user),
  i as (select (public.invite_counts(p_user)->>'counted')::int n),
  m as (select exists (select 1 from public.xp_events where user_id = p_user and kind = 'milestone' and ref = 'cards_100') got),
  b as (select count(*) filter (where kind = 'battle')::int n,
               coalesce(sum(case kind when 'streak_3' then 1 else 0 end), 0)::int s3,
               coalesce(sum(case kind when 'streak_7' then 1 else 0 end), 0)::int s7,
               coalesce(sum(case kind when 'streak_30' then 1 else 0 end), 0)::int s30
        from public.xp_events where user_id = p_user and kind in ('battle', 'streak_3', 'streak_7', 'streak_30')),
  t as (select cardinality(v.chars) * (r.j->>'vote_character')::int + f.n * (r.j->>'feedback_accepted')::int
               + i.n * (r.j->>'invite_signup')::int + (case when m.got then (r.j->>'cards_100')::int else 0 end)
               + b.n * (r.j->>'daily_battle')::int + b.s3 * (r.j->>'streak_3')::int + b.s7 * (r.j->>'streak_7')::int
               + b.s30 * (r.j->>'streak_30')::int xp,
               v.chars, f.n fn, i.n inv, m.got, b.n bn
        from r, v, f, i, m, b)
  select jsonb_build_object('xp', t.xp, 'points', t.xp, 'voted', to_jsonb(t.chars), 'feedback', t.fn, 'invites', t.inv,
                            'cards', public.logged_card_count(p_user), 'cards_100', t.got, 'battles', t.bn,
                            'streak', public.battle_streak(p_user), 'rules', r.j)
         || public.xp_rank(t.xp)
  from t, r
$function$;
revoke all on function public.user_xp(uuid) from public, anon, authenticated;
