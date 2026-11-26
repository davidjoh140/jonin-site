-- Applied to Supabase on 2026-11-26 (migration slab_privacy_prompt). Kept here as the record.
-- David 2026-11-26: when a member has their first slab, ask once whether their slabs are public or private.
--   profiles.slab_privacy_asked_at: set when they answer (Make public / Keep private / ×); null = not asked yet.
--   "Make public" sets show_slabs = true and sharing = true from the site.
alter table public.profiles add column if not exists slab_privacy_asked_at timestamptz;
grant update (slab_privacy_asked_at) on public.profiles to authenticated;
