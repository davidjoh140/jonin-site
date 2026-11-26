-- Applied to Supabase on 2026-11-26 (migration xp_and_missions). Kept here as the record.
-- XP (David, 2026-11-26): feedback points become XP, and voting for a character's best cards also earns XP.
-- Missions page (/missions/) shows the ways to earn XP and your progress.
--
-- PLACEHOLDER numbers, David to set: xp_rules() and xp_rank() below.
--   Vote for at least one card on a character: 5 XP, once per character (40 characters = up to 200 XP).
--   Feedback note accepted: 25 XP each.
--   Ranks: Academy Student 0, Genin 25, Chunin 100, Jonin 300, Kage 750.
--
-- Vote XP is logged in xp_events the first time someone votes on a character and is kept even if they later
-- move or take back that vote, so un-voting and re-voting can't farm XP. Feedback XP stays counted live from
-- accepted notes, so Undo on the admin page still takes it back.

create table if not exists public.xp_events (
  user_id uuid not null references auth.users(id) on delete cascade,
  kind text not null,
  ref text not null,
  created_at timestamptz not null default now(),
  primary key (user_id, kind, ref)
);
alter table public.xp_events enable row level security;
drop policy if exists "xp: read own" on public.xp_events;
create policy "xp: read own" on public.xp_events for select to authenticated using (user_id = (select auth.uid()));
grant select on public.xp_events to authenticated;

-- XP per action. Change the numbers here to change the rules everywhere (site and Missions page read them).
create or replace function public.xp_rules() returns jsonb language sql immutable as $$
  select jsonb_build_object('vote_character', 5, 'feedback_accepted', 25)
$$;
grant execute on function public.xp_rules() to anon, authenticated;

create or replace function public.xp_rank(p_xp int) returns jsonb language sql immutable as $$
  select case
    when p_xp >= 750 then jsonb_build_object('rank','Kage','prev_at',750,'next',null,'next_at',null)
    when p_xp >= 300 then jsonb_build_object('rank','Jonin','prev_at',300,'next','Kage','next_at',750)
    when p_xp >= 100 then jsonb_build_object('rank','Chunin','prev_at',100,'next','Jonin','next_at',300)
    when p_xp >= 25  then jsonb_build_object('rank','Genin','prev_at',25,'next','Chunin','next_at',100)
    else jsonb_build_object('rank','Academy Student','prev_at',0,'next','Genin','next_at',25) end
$$;
-- The full ladder, for the Missions page.
create or replace function public.xp_ranks() returns jsonb language sql immutable as $$
  select jsonb_build_array(
    jsonb_build_object('rank','Academy Student','at',0), jsonb_build_object('rank','Genin','at',25),
    jsonb_build_object('rank','Chunin','at',100), jsonb_build_object('rank','Jonin','at',300),
    jsonb_build_object('rank','Kage','at',750))
$$;
grant execute on function public.xp_rank(int), public.xp_ranks() to anon, authenticated;

-- First vote on a character logs the XP.
create or replace function public.xp_on_vote() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  insert into public.xp_events(user_id, kind, ref) values (new.user_id, 'vote', new.character) on conflict do nothing;
  return new;
end $$;
drop trigger if exists xp_on_vote on public.card_votes;
create trigger xp_on_vote after insert on public.card_votes for each row execute function public.xp_on_vote();

-- Votes cast before XP existed count too.
insert into public.xp_events(user_id, kind, ref, created_at)
select user_id, 'vote', character, min(created_at) from public.card_votes group by user_id, character on conflict do nothing;

-- One person's XP, rank and mission progress.
create or replace function public.user_xp(p_user uuid) returns jsonb
language sql stable security definer set search_path = public as $$
  with r as (select public.xp_rules() j),
  v as (select coalesce(array_agg(ref order by ref), '{}') chars from public.xp_events where user_id = p_user and kind = 'vote'),
  f as (select count(*)::int n from public.feedback where review = 'accepted' and credit_user = p_user),
  t as (select cardinality(v.chars) * (r.j->>'vote_character')::int + f.n * (r.j->>'feedback_accepted')::int xp, v.chars, f.n
        from r, v, f)
  select jsonb_build_object('xp', t.xp, 'points', t.xp, 'voted', to_jsonb(t.chars), 'feedback', t.n, 'rules', r.j)
         || public.xp_rank(t.xp)
  from t, r
$$;
revoke all on function public.user_xp(uuid) from public, anon, authenticated;

create or replace function public.my_xp() returns jsonb
language sql stable security definer set search_path = public as $$ select public.user_xp(auth.uid()) $$;
revoke all on function public.my_xp() from public, anon;
grant execute on function public.my_xp() to authenticated;

-- Older names, still called by cached pages: now return XP.
create or replace function public.my_feedback_points() returns jsonb
language sql stable security definer set search_path = public as $$ select public.user_xp(auth.uid()) $$;
create or replace function public.feedback_points(p_user uuid) returns jsonb
language sql stable security definer set search_path = public as $$
  select jsonb_build_object('xp', x->'xp', 'points', x->'xp', 'rank', x->'rank', 'next', x->'next', 'next_at', x->'next_at', 'prev_at', x->'prev_at')
  from (select public.user_xp(p_user) x) s
$$;
create or replace function public.feedback_rank(p_points int) returns jsonb language sql immutable as $$ select public.xp_rank(p_points) $$;
