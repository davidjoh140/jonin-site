-- 3-pack blister slots (David 2026-11-27): one hidden slot per main set. The Find sealed photos run looks for 3-pack
-- blister photos; when David picks one in Jonin Hub (Review -> Sealed -> Photos), the slot goes on the site.
insert into products (id, set_id, name, kind, confirmed, note, slug, match_words, sort, contents, public)
select s.id || '-blister-3pack', s.id, s.name || ' 3-pack blister', 'blister_3pack', false,
       'Slot: goes on the site when David picks a photo (3-pack blisters, David 2026-11-27)',
       trim(both '-' from regexp_replace(lower(replace(replace(s.name, '''', ''), '&', 'and')), '[^a-z0-9]+', '-', 'g')) || '-3-pack-blister',
       '{}', (select sort from products where id = s.id || '-booster-pack'), '3 booster packs in a retail blister', false
  from sets s where s.kind = 'Main'
on conflict (id) do nothing;
