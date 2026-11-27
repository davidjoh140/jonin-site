-- Daily battle (David, 2026-11-27): a classic 1v1 between two random characters each day; visitors vote who would win
-- and earn scrolls for it. PLACEHOLDERS for David:
--   * 5 scrolls per daily vote (xp_rules 'daily_battle')
--   * a new battle at midnight New York time
--   * signing in is needed to vote (that's how the scrolls are tracked); signed-out visitors see the matchup
--   * results show after you vote; a vote can't be changed
--   * the same pair won't come back within 60 days
create table if not exists public.battle_characters (slug text primary key, label text not null);
insert into public.battle_characters(slug,label) values
  ('naruto','Naruto'),('sasuke','Sasuke'),('kakashi','Kakashi'),('itachi','Itachi'),('gaara','Gaara'),('sakura','Sakura'),('hinata','Hinata'),('jiraiya','Jiraiya'),('minato','Minato'),('madara','Madara'),('obito','Obito'),('pain','Pain'),('shikamaru','Shikamaru'),('rock-lee','Rock Lee'),('neji','Neji'),('orochimaru','Orochimaru'),('tsunade','Tsunade'),('deidara','Deidara'),('might-guy','Might Guy'),('killer-bee','Killer Bee'),('ino','Ino'),('choji','Choji'),('temari','Temari'),('kiba','Kiba'),('tenten','Tenten'),('shino','Shino'),('kabuto','Kabuto'),('kisame','Kisame'),('kankuro','Kankuro'),('haku','Haku'),('zabuza','Zabuza'),('asuma','Asuma'),('sai','Sai'),('third-hokage','Third Hokage'),('sasori','Sasori'),('hidan','Hidan'),('kakuzu','Kakuzu'),('konohamaru','Konohamaru'),('iruka','Iruka'),('yamato','Yamato')
on conflict (slug) do update set label = excluded.label;   -- the 40 characters in public/chars.json
alter table public.battle_characters enable row level security;
drop policy if exists "battle chars: read" on public.battle_characters;
create policy "battle chars: read" on public.battle_characters for select to anon, authenticated using (true);
grant select on public.battle_characters to anon, authenticated;

create table if not exists public.daily_battles (day date primary key, a text not null, b text not null, created_at timestamptz default now());
create table if not exists public.battle_votes (
  day date not null references public.daily_battles(day) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  pick text not null, created_at timestamptz default now(),
  primary key (day, user_id));
alter table public.daily_battles enable row level security;
alter table public.battle_votes enable row level security;   -- no direct access; everything goes through the functions below

create or replace function public.battle_day() returns date language sql stable as $$ select (now() at time zone 'America/New_York')::date $$;

-- Today's matchup (made on first visit of the day), vote counts once you've voted, and your pick.
create or replace function public.today_battle() returns jsonb
language plpgsql security definer set search_path = public as $$
declare d date := battle_day(); r daily_battles; me text; ca int; cb int;
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
  if auth.uid() is not null then select pick into me from battle_votes where day = d and user_id = auth.uid(); end if;
  select count(*) filter (where pick = r.a), count(*) filter (where pick = r.b) into ca, cb from battle_votes where day = d;
  return jsonb_build_object('day', d,
    'a', (select jsonb_build_object('slug', slug, 'label', label) from battle_characters where slug = r.a),
    'b', (select jsonb_build_object('slug', slug, 'label', label) from battle_characters where slug = r.b),
    'mine', me, 'signed_in', auth.uid() is not null,
    'votes', case when me is not null then jsonb_build_object('a', ca, 'b', cb) end,
    'total', ca + cb,
    'scrolls', (xp_rules()->>'daily_battle')::int,
    'yesterday', (select jsonb_build_object('a', y.a, 'b', y.b,
                    'va', (select count(*) from battle_votes v where v.day = y.day and v.pick = y.a),
                    'vb', (select count(*) from battle_votes v where v.day = y.day and v.pick = y.b))
                  from daily_battles y where y.day = d - 1));
end $$;
grant execute on function public.today_battle() to anon, authenticated;

create or replace function public.vote_battle(p_pick text) returns jsonb
language plpgsql security definer set search_path = public as $$
declare d date := battle_day(); r daily_battles;
begin
  if auth.uid() is null then raise exception 'sign in to vote'; end if;
  select * into r from daily_battles where day = d;
  if not found or p_pick not in (r.a, r.b) then raise exception 'not today''s battle'; end if;
  insert into battle_votes(day, user_id, pick) values (d, auth.uid(), p_pick) on conflict do nothing;
  insert into xp_events(user_id, kind, ref) values (auth.uid(), 'battle', d::text) on conflict do nothing;
  return today_battle();
end $$;
revoke all on function public.vote_battle(text) from public, anon;
grant execute on function public.vote_battle(text) to authenticated;

-- Scrolls: add daily_battle to the rules and count battle votes in everyone's total.
create or replace function public.xp_rules() returns jsonb language sql immutable as $$
  select jsonb_build_object('vote_character', 5, 'feedback_accepted', 25, 'invite_signup', 50, 'cards_100', 50, 'daily_battle', 5)
$$;
create or replace function public.user_xp(p_user uuid) returns jsonb
language sql stable security definer set search_path to 'public' as $function$
  with r as (select public.xp_rules() j),
  v as (select coalesce(array_agg(ref order by ref), '{}') chars from public.xp_events where user_id = p_user and kind = 'vote'),
  f as (select count(*)::int n from public.feedback where review = 'accepted' and credit_user = p_user),
  i as (select (public.invite_counts(p_user)->>'counted')::int n),
  m as (select exists (select 1 from public.xp_events where user_id = p_user and kind = 'milestone' and ref = 'cards_100') got),
  b as (select count(*)::int n from public.xp_events where user_id = p_user and kind = 'battle'),
  t as (select cardinality(v.chars) * (r.j->>'vote_character')::int + f.n * (r.j->>'feedback_accepted')::int
               + i.n * (r.j->>'invite_signup')::int + (case when m.got then (r.j->>'cards_100')::int else 0 end)
               + b.n * (r.j->>'daily_battle')::int xp,
               v.chars, f.n fn, i.n inv, m.got, b.n bn
        from r, v, f, i, m, b)
  select jsonb_build_object('xp', t.xp, 'points', t.xp, 'voted', to_jsonb(t.chars), 'feedback', t.fn, 'invites', t.inv,
                            'cards', public.logged_card_count(p_user), 'cards_100', t.got, 'battles', t.bn, 'rules', r.j)
         || public.xp_rank(t.xp)
  from t, r
$function$;
revoke all on function public.user_xp(uuid) from public, anon, authenticated;
