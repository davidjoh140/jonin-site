-- Applied to Supabase on 2026-11-26 (migration member_messages). Kept here as the record.
-- Direct messages between David (admin) and members, mainly to ask feedback senders follow-up questions.
-- One conversation per member. A message can point at the feedback note it is about (feedback_id).
-- Nobody reads or writes the table directly; everything goes through the functions below.
-- Rules (David approved 2026-11-26): members can only reply once David has messaged them (no cold DMs to him),
-- members can send one message every 10 seconds, messages are capped at 2000 characters.

create table if not exists public.messages (
  id bigint generated always as identity primary key,
  user_id uuid not null references auth.users(id) on delete cascade,   -- the member in the conversation
  from_admin boolean not null,
  body text not null check (char_length(body) between 1 and 2000),
  feedback_id bigint references public.feedback(id) on delete set null,
  created_at timestamptz not null default now(),
  read_at timestamptz                                                   -- when the other side opened it
);
create index if not exists messages_user_idx on public.messages(user_id, created_at);
alter table public.messages enable row level security;
revoke all on public.messages from anon, authenticated;

-- Who sent a feedback note (signed in, credited, or an account with the email they left).
create or replace function public.feedback_sender(p_feedback bigint) returns uuid
language sql stable security definer set search_path = public as $$
  select coalesce(f.user_id, f.credit_user,
    (select u.id from auth.users u where f.contact is not null and lower(u.email) = lower(trim(f.contact)) limit 1))
  from public.feedback f where f.id = p_feedback $$;
revoke all on function public.feedback_sender(bigint) from public, anon, authenticated;

-- Admin: send a message to a member (by user id, or to whoever sent a feedback note).
create or replace function public.admin_send_message(p_body text, p_user uuid default null, p_feedback bigint default null)
returns bigint language plpgsql security definer set search_path = public as $$
declare u uuid := p_user; nid bigint;
begin
  if not public.is_admin() then raise exception 'not allowed'; end if;
  if coalesce(trim(p_body),'') = '' then raise exception 'write a message first'; end if;
  if u is null and p_feedback is not null then u := public.feedback_sender(p_feedback); end if;
  if u is null then raise exception 'no account for this sender yet'; end if;
  insert into public.messages(user_id, from_admin, body, feedback_id) values (u, true, trim(p_body), p_feedback) returning id into nid;
  return nid;
end $$;

-- Admin: every conversation, newest first, with unread replies.
create or replace function public.admin_inbox() returns table(user_id uuid, email text, handle text, avatar text, fav_character text,
  last_body text, last_from_admin boolean, last_at timestamptz, unread int, total int)
language plpgsql stable security definer set search_path = public as $$
begin
  if not public.is_admin() then raise exception 'not allowed'; end if;
  return query
  select m.user_id, u.email::text, p.handle, p.avatar, p.fav_character,
    (array_agg(m.body order by m.created_at desc))[1], (array_agg(m.from_admin order by m.created_at desc))[1], max(m.created_at),
    count(*) filter (where not m.from_admin and m.read_at is null)::int, count(*)::int
  from public.messages m join auth.users u on u.id = m.user_id left join public.profiles p on p.id = m.user_id
  group by m.user_id, u.email, p.handle, p.avatar, p.fav_character order by max(m.created_at) desc;
end $$;

-- Admin: one conversation (by member, or by feedback note). Marks the member's messages read.
create or replace function public.admin_thread(p_user uuid default null, p_feedback bigint default null) returns jsonb
language plpgsql security definer set search_path = public as $$
declare u uuid := p_user; r jsonb;
begin
  if not public.is_admin() then raise exception 'not allowed'; end if;
  if u is null and p_feedback is not null then u := public.feedback_sender(p_feedback); end if;
  if u is null then return jsonb_build_object('user_id', null); end if;
  update public.messages set read_at = now() where user_id = u and not from_admin and read_at is null;
  select jsonb_build_object(
    'user_id', u,
    'email', (select email from auth.users where id = u),
    'handle', (select handle from public.profiles where id = u),
    'messages', coalesce((select jsonb_agg(jsonb_build_object('id', m.id, 'from_admin', m.from_admin, 'body', m.body,
        'feedback_id', m.feedback_id, 'created_at', m.created_at, 'read_at', m.read_at) order by m.created_at) from public.messages m where m.user_id = u), '[]'),
    'notes', coalesce((select jsonb_agg(jsonb_build_object('id', f.id, 'message', f.message, 'kind', f.kind, 'card_id', f.card_id, 'page', f.page,
        'created_at', f.created_at, 'review', f.review, 'proposal', f.proposal, 'proposal_question', f.proposal_question,
        'has_change', f.proposal_change is not null) order by f.created_at desc)
      from public.feedback f where public.feedback_sender(f.id) = u or f.id = p_feedback), '[]')
  ) into r;
  return r;
end $$;

-- Member: unread count for the header badge.
create or replace function public.my_unread_messages() returns int
language sql stable security definer set search_path = public as $$
  select count(*)::int from public.messages where user_id = auth.uid() and from_admin and read_at is null $$;

-- Member: their conversation with Jonin (marks David's messages read), plus the notes it refers to.
create or replace function public.my_messages() returns jsonb
language plpgsql security definer set search_path = public as $$
declare u uuid := auth.uid();
begin
  if u is null then raise exception 'sign in first'; end if;
  update public.messages set read_at = now() where user_id = u and from_admin and read_at is null;
  return jsonb_build_object(
    'messages', coalesce((select jsonb_agg(jsonb_build_object('id', m.id, 'from_admin', m.from_admin, 'body', m.body,
        'feedback_id', m.feedback_id, 'created_at', m.created_at) order by m.created_at) from public.messages m where m.user_id = u), '[]'),
    'notes', coalesce((select jsonb_object_agg(f.id::text, jsonb_build_object('message', left(f.message, 300), 'created_at', f.created_at))
      from public.feedback f where f.id in (select feedback_id from public.messages where user_id = u and feedback_id is not null)), '{}'));
end $$;

-- Member: reply. Only once David has messaged them; one message per 10 seconds.
create or replace function public.send_message(p_body text, p_feedback bigint default null) returns bigint
language plpgsql security definer set search_path = public as $$
declare u uuid := auth.uid(); fb bigint := p_feedback; nid bigint;
begin
  if u is null then raise exception 'sign in first'; end if;
  if coalesce(trim(p_body),'') = '' then raise exception 'write a message first'; end if;
  if char_length(trim(p_body)) > 2000 then raise exception 'keep it under 2000 characters'; end if;
  if not exists (select 1 from public.messages where user_id = u and from_admin) then raise exception 'no conversation yet'; end if;
  if exists (select 1 from public.messages where user_id = u and not from_admin and created_at > now() - interval '10 seconds') then
    raise exception 'wait a few seconds before sending again'; end if;
  -- reply goes with the note David last asked about, unless the member picked one of their own
  if fb is null or not exists (select 1 from public.messages where user_id = u and feedback_id = fb) then
    select feedback_id into fb from public.messages where user_id = u and from_admin order by created_at desc limit 1;
  end if;
  insert into public.messages(user_id, from_admin, body, feedback_id) values (u, false, trim(p_body), fb) returning id into nid;
  return nid;
end $$;

revoke all on function public.admin_send_message(text, uuid, bigint), public.admin_inbox(), public.admin_thread(uuid, bigint),
  public.my_unread_messages(), public.my_messages(), public.send_message(text, bigint) from public, anon;
grant execute on function public.admin_send_message(text, uuid, bigint), public.admin_inbox(), public.admin_thread(uuid, bigint),
  public.my_unread_messages(), public.my_messages(), public.send_message(text, bigint) to authenticated;

-- Admin: look up a member's id from their email (Accounts table and View profile only know emails).
create or replace function public.admin_user_id(p_email text) returns uuid
language plpgsql stable security definer set search_path = public as $$
begin
  if not public.is_admin() then raise exception 'not allowed'; end if;
  return (select id from auth.users where lower(email) = lower(trim(p_email)) limit 1);
end $$;
revoke all on function public.admin_user_id(text) from public, anon;
grant execute on function public.admin_user_id(text) to authenticated;

-- Admin: message counts per feedback note (for the note's "Conversation (n)" button).
create or replace function public.admin_note_message_counts() returns table(feedback_id bigint, n int, unread int)
language plpgsql stable security definer set search_path = public as $$
begin
  if not public.is_admin() then raise exception 'not allowed'; end if;
  return query select m.feedback_id, count(*)::int, count(*) filter (where not m.from_admin and m.read_at is null)::int
    from public.messages m where m.feedback_id is not null group by m.feedback_id;
end $$;
revoke all on function public.admin_note_message_counts() from public, anon;
grant execute on function public.admin_note_message_counts() to authenticated;
