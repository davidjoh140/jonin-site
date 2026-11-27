-- Audit fixes (2026-11-27). Applied to Supabase as migration "audit_security_and_perf_fixes".
-- Also dropped one-time backup tables (copy saved by Claude): cards_removed, foil_fix_backup,
-- sales_bo_backup_20261126, promo_type_fix.

-- 1) Internal views: run with the caller's permissions and keep them off the public API.
alter view public.printings_without_scan set (security_invoker = true);
alter view public.scans_wanted set (security_invoker = true);
revoke select on public.printings_without_scan, public.scans_wanted from anon, authenticated;

-- 2) Admin functions signed-out visitors could still call (each already refuses non-admins).
revoke execute on function public.admin_giveaway_bonus(text) from anon, public;
revoke execute on function public.admin_giveaway_set(text,text,text,timestamptz,timestamptz) from anon, public;
revoke execute on function public.admin_giveaway_winner(text,text) from anon, public;
revoke execute on function public.admin_grant(text,timestamptz,text,text) from anon, public;
grant execute on function public.admin_giveaway_bonus(text), public.admin_giveaway_set(text,text,text,timestamptz,timestamptz),
  public.admin_giveaway_winner(text,text), public.admin_grant(text,timestamptz,text,text) to authenticated;

-- 3) Fixed search path on small helper functions.
do $$ declare r record; begin
  for r in select p.oid::regprocedure sig from pg_proc p join pg_namespace n on n.oid=p.pronamespace
    where n.nspname='public' and p.proname in ('xp_rules','ig_norm','feedback_rank','xp_rank','xp_ranks','handle_cooldown_days',
      'profile_reserved_handles','psa_daily_limit','psa_member_cap','ebay_photo_url','battle_day')
  loop execute format('alter function %s set search_path = public, pg_temp', r.sig); end loop; end $$;

-- 4) Row rules: check who you are once per request instead of once per row.
do $$ declare r record; q text; w text; s text; begin
  for r in select * from pg_policies where schemaname='public'
    and (qual ~ '(?<!SELECT )auth\.uid\(\)' or with_check ~ '(?<!SELECT )auth\.uid\(\)')
  loop
    q := regexp_replace(r.qual, '(?<!SELECT )auth\.uid\(\)', '(select auth.uid())', 'g');
    w := regexp_replace(r.with_check, '(?<!SELECT )auth\.uid\(\)', '(select auth.uid())', 'g');
    s := format('alter policy %I on public.%I', r.policyname, r.tablename);
    if q is not null then s := s || format(' using (%s)', q); end if;
    if w is not null then s := s || format(' with check (%s)', w); end if;
    execute s;
  end loop; end $$;

-- 5) Indexes on table links that had none.
create index if not exists alert_sends_listing_id_idx on public.alert_sends(listing_id);
create index if not exists alert_wants_user_id_idx on public.alert_wants(user_id);
create index if not exists battle_votes_user_id_idx on public.battle_votes(user_id);
create index if not exists card_list_items_card_id_idx on public.card_list_items(card_id);
create index if not exists card_votes_card_id_idx on public.card_votes(card_id);
create index if not exists collection_items_card_id_idx on public.collection_items(card_id);
create index if not exists feedback_files_card_id_idx on public.feedback_files(card_id);
create index if not exists listings_card_id_idx on public.listings(card_id);
create index if not exists messages_feedback_id_idx on public.messages(feedback_id);
create index if not exists sale_scan_queue_card_id_idx on public.sale_scan_queue(card_id);
create index if not exists scan_candidates_card_id_idx on public.scan_candidates(card_id);
create index if not exists scans_card_id_idx on public.scans(card_id);
