-- Applied to Supabase on 2026-11-26 (migration invite_scrolls). Kept here as the record.
-- Invites (David, 2026-11-26): members earn scrolls for inviting friends who sign up.
--
-- How it works:
--   Every profile gets a short invite_code. Invite link: https://jonin.cards/?invite=<code>
--   The site remembers the code in the visitor's browser (30 days). When they sign in for the first time
--   (Google, Discord or email), the site calls claim_invite(code) once.
--   claim_invite only accepts accounts created in the last 3 days, never your own code, and one inviter per account.
--
-- PLACEHOLDERS, David to set:
--   invite_signup scrolls: 50 per friend (in xp_rules()).
--   A friend only counts once they've added at least one card (have/want/slab) or cast a vote,
--   so empty throwaway accounts don't earn scrolls.
--   3-day window for a new account to claim an invite.

alter table public.profiles add column if not exists invite_code text;
update public.profiles set invite_code = substr(md5(gen_random_uuid()::text), 1, 7) where invite_code is null;
alter table public.profiles alter column invite_code set default substr(md5(gen_random_uuid()::text), 1, 7);
create unique index if not exists profiles_invite_code_key on public.profiles(invite_code);

create table if not exists public.invites (
  invitee uuid primary key references auth.users(id) on delete cascade,
  inviter uuid not null references auth.users(id) on delete cascade,
  code text not null,
  created_at timestamptz not null default now()
);
create index if not exists invites_inviter_idx on public.invites(inviter);
alter table public.invites enable row level security;
-- No direct access; everything goes through the functions below.

create or replace function public.claim_invite(p_code text) returns jsonb
language plpgsql security definer set search_path = public as $$
declare me uuid := auth.uid(); who uuid; made timestamptz;
begin
  if me is null then return jsonb_build_object('ok', false, 'why', 'signed_out'); end if;
  select id into who from public.profiles where invite_code = lower(trim(p_code));
  if who is null then return jsonb_build_object('ok', false, 'why', 'bad_code'); end if;
  if who = me then return jsonb_build_object('ok', false, 'why', 'own_code'); end if;
  select created_at into made from auth.users where id = me;
  if made < now() - interval '3 days' then return jsonb_build_object('ok', false, 'why', 'not_new'); end if;
  insert into public.invites(invitee, inviter, code) values (me, who, lower(trim(p_code))) on conflict do nothing;
  if not found then return jsonb_build_object('ok', false, 'why', 'already'); end if;
  return jsonb_build_object('ok', true);
end $$;
revoke all on function public.claim_invite(text) from public, anon;
grant execute on function public.claim_invite(text) to authenticated;

-- Friends who count: invited AND have added a card or voted.
create or replace function public.invite_counts(p_user uuid) returns jsonb
language sql stable security definer set search_path = public as $$
  select jsonb_build_object(
    'joined', count(*)::int,
    'counted', count(*) filter (where exists (select 1 from public.collection_items c where c.user_id = i.invitee)
                                   or exists (select 1 from public.collection_slabs s where s.user_id = i.invitee)
                                   or exists (select 1 from public.card_votes v where v.user_id = i.invitee))::int)
  from public.invites i where i.inviter = p_user
$$;
revoke all on function public.invite_counts(uuid) from public, anon, authenticated;

create or replace function public.my_invite() returns jsonb
language sql stable security definer set search_path = public as $$
  select jsonb_build_object('code', p.invite_code, 'scrolls_each', (public.xp_rules()->>'invite_signup')::int)
         || public.invite_counts(auth.uid())
  from public.profiles p where p.id = auth.uid()
$$;
revoke all on function public.my_invite() from public, anon;
grant execute on function public.my_invite() to authenticated;

create or replace function public.xp_rules() returns jsonb language sql immutable as $$
  select jsonb_build_object('vote_character', 5, 'feedback_accepted', 25, 'invite_signup', 50)
$$;

create or replace function public.user_xp(p_user uuid) returns jsonb
language sql stable security definer set search_path = public as $$
  with r as (select public.xp_rules() j),
  v as (select coalesce(array_agg(ref order by ref), '{}') chars from public.xp_events where user_id = p_user and kind = 'vote'),
  f as (select count(*)::int n from public.feedback where review = 'accepted' and credit_user = p_user),
  i as (select (public.invite_counts(p_user)->>'counted')::int n),
  t as (select cardinality(v.chars) * (r.j->>'vote_character')::int + f.n * (r.j->>'feedback_accepted')::int
               + i.n * (r.j->>'invite_signup')::int xp, v.chars, f.n fn, i.n inv
        from r, v, f, i)
  select jsonb_build_object('xp', t.xp, 'points', t.xp, 'voted', to_jsonb(t.chars), 'feedback', t.fn, 'invites', t.inv, 'rules', r.j)
         || public.xp_rank(t.xp)
  from t, r
$$;
revoke all on function public.user_xp(uuid) from public, anon, authenticated;
