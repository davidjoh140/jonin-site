-- Applied to Supabase on 2026-11-26 (migration admin_accounts). Kept here as the record.
-- admin_accounts() (owner only, is_admin()): one row per account — email, username, joined, last sign-in,
-- sign-in method, admin flag, founding flag + founder number (#1 = earliest non-admin founder), Premium status,
-- distinct cards marked as haves, slabs logged. Used by the Accounts section on /admin/.
create or replace function public.admin_accounts()
returns table(email text, handle text, created_at timestamptz, last_sign_in_at timestamptz, provider text,
              is_admin boolean, founding boolean, founder_no int, premium text, cards_have int, slabs int)
language plpgsql stable security definer set search_path = public, auth as $$
begin
  if not public.is_admin() then raise exception 'not allowed'; end if;
  return query
  with f as (
    select m.user_id, row_number() over (order by u2.created_at)::int as n
    from public.memberships m join auth.users u2 on u2.id = m.user_id
    where m.founding and not exists (select 1 from public.admins a where a.user_id = m.user_id)
  )
  select u.email::text, p.handle, u.created_at, u.last_sign_in_at,
         coalesce(u.raw_app_meta_data->>'provider', 'email'),
         exists (select 1 from public.admins a where a.user_id = u.id),
         coalesce(m.founding, false), f.n,
         case when m.user_id is null then 'none'
              when m.active and (m.until is null or m.until > now()) then 'active'
              when m.active then 'expired' else 'revoked' end,
         (select count(distinct ci.card_id)::int from public.collection_items ci where ci.user_id = u.id and ci.kind = 'have' and ci.qty > 0),
         (select count(*)::int from public.collection_slabs cs where cs.user_id = u.id)
  from auth.users u
  left join public.profiles p on p.id = u.id
  left join public.memberships m on m.user_id = u.id
  left join f on f.user_id = u.id
  order by u.created_at desc;
end $$;
revoke all on function public.admin_accounts() from public, anon;
grant execute on function public.admin_accounts() to authenticated;
