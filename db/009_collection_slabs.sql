-- Slabs in collections: graded copies a member (or guest, moved in on signup) logs against a card.
create table public.collection_slabs (
  id bigint generated always as identity primary key,
  user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  card_id text not null,
  printing text not null default 'Normal',
  edition text not null default '',
  grader text not null check (grader in ('PSA','BGS','CGC','SGC','TAG','Other')),
  grade text not null check (char_length(grade) between 1 and 12),
  cert text check (cert is null or char_length(cert) <= 30),
  note text check (note is null or char_length(note) <= 200),
  created_at timestamptz not null default now()
);
create index collection_slabs_user on public.collection_slabs(user_id);
alter table public.collection_slabs enable row level security;
create policy "own slabs read" on public.collection_slabs for select using (user_id = auth.uid());
create policy "own slabs insert" on public.collection_slabs for insert with check (user_id = auth.uid());
create policy "own slabs update" on public.collection_slabs for update using (user_id = auth.uid()) with check (user_id = auth.uid());
create policy "own slabs delete" on public.collection_slabs for delete using (user_id = auth.uid());
grant select, insert, update, delete on public.collection_slabs to authenticated;
