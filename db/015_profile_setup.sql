-- Applied to Supabase on 2026-11-26 (migration profile_setup). Kept here as the record.
-- Setup page after sign-up (/welcome/, David 2026-11-26): favorite characters, a few questions, theme. Skippable.
-- fav_characters: up to 3 character slugs, first = main favorite (also written to fav_character, which the site already uses).
-- found_via / collector_types / email_updates: the setup questions (PLACEHOLDER wording, David to confirm).
-- theme: theme id from theme.js, so it follows them to other devices.
-- setup_done_at: set when they finish OR skip, so the page is only shown once.
alter table public.profiles
  add column if not exists fav_characters text[] not null default '{}',
  add column if not exists found_via text,
  add column if not exists collector_types text[] not null default '{}',
  add column if not exists email_updates boolean not null default false,
  add column if not exists theme text,
  add column if not exists setup_done_at timestamptz;
grant update (fav_characters, found_via, collector_types, email_updates, theme, setup_done_at) on public.profiles to authenticated;

-- Follow-up (migration admin_accounts_setup_answers): admin_accounts() also returns found_via, collector_types,
-- email_updates, fav_characters and setup_done_at, shown in the Accounts table on /admin/.
