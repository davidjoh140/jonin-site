-- 003: one-time backfill of rarity codes, card order and set sources, matching the
-- public/cards.json that jonin.cards and the Card Index used on 2026-11-24. Run once after 002.
do $$
declare part text; body text; tok text; s text; a text; b text; pre text; num text; k int; i int := 0;
begin
  -- card order, written as set|number ranges (J-001~042 = J-001 through J-042)
  foreach part in array string_to_array('1|J-001~042,M-001~004,M-006~042,N-001~018,N-022~042;2|C-001~006,J-043~084,M-043~084,N-044~084;3|C-008~014,J-085~126,M-085~132,N-085~135;4|C-007,C-015~019,J-127~162,M-133~168,N-136~172;5|C-025~029,J-173~209,M-174~207,N-186~223;6|C-020~024,J-163~172,J-US-001~020,M-169~173,M-US-001~020,N-173~185,N-US-001~040;7|C-030~031,J-210~231,J-US-021~044,M-208~235,M-US-021~040,N-224~254,N-284~287,N-C-001~016,N-US-041~054;8|C-032~033,J-232~256,J-259~260,J-263~273,J-US-045~056,M-236~257,M-259~263,M-265~267,M-US-041~050,N-255~283,N-288~306,N-US-055~065;9|C-037,C-US-001,J-276~304,J-US-057~076,M-268~285,M-US-051~086,N-307~343,N-US-066~092;P|J-103,N-046,N-095,M-072,EX001~002,M621~623,PR001~018,PR018B,PR019~024,PR024B,PR025,PR025B,PR026,PR026B,PR027~062,PR066~068,PR075~076,PR083~088,PR092~093,PR095~096,PR100,PRUS001~015,PS001~004;10|C-034~036,C-038~042,J-257~258,J-261~262,J-274~275,J-305~341,J-US-077~094,M-264,M-286~321,M-US-087~111,N-344~388,N-US-093~124;11|C-043~046,J-342~386,M-322~363,N-389~460;12|J-387~449,M-364~411,N-461~521;13|C-047~048,J-450~495,M-412~454,N-522~589;14|J-496~540,M-455~499,N-590~644;15|C-032,C-049~051,J-032,J-067,J-332,J-386,J-437,J-537~538,J-541~601,M-051,M-118,M-193,M-209,M-272,M-356,M-412,M-500~549,M-US-077,M-US-086,N-102,N-144,N-198,N-260~261,N-303,N-320,N-384,N-409,N-479,N-512,N-547,N-555,N-571,N-575,N-615,N-617~619,N-622,N-625,N-645~708;16|C-052~055,J-602~644,M-585~620,N-709~783;17|C-056~059,J-020,J-066,J-645~695,J696A,J-US-059,M-391,M-585,M-624~664,N-005,N-038,N-074,N-187,N-242,N-332,N-430~431,N-436~438,N-493,N-657,N-784~863,N-US-004,N-US-069,N-US-121;18|J-706~742,M-670~698,N-883~948;19|J-743~772,M-699~722,N-1000~1006,N-949~999;20|J-773~801,M-723~748,N-1037~1101;21|J-802~826,M-749~775,N-1102~1169;22|J-839~864,M-788~816,N-1206~1269;23|J-865~889,M-817~846,N-1270~1334;24|J-895~920,M-855~883,N-1358~1422;25|J-921~945,M-884~913,N-1423~1487;26|J-946~971,M-914~942,N-1488~1552;27|C-060,J-1000~1001,J-972~999,M-943~975,N-1553~1620;28|J-1002~1033,M-976~998,N-1621~1685;TP1|J-696b,J-697~705,M-665~669,N-019b,N-024b,N-114b,N-122b,N-202b,N-209b,N-333b,N-336b,N-371b,N-382b,N-384b,N-451b,N-511b,N-547b,N-571b,N-595b,N-600b,N-622b,N-631b,N-640b,N-864~882,N-US-006b,N-US-015b,N-US-027b,N-US-035b,N-US-072b,N-US-106b;TP2|J-696b,J-697~705,M-665~669,N-1007~1036,N-864~882;TP3|J-827~838,M-776~787,N-1170~1205;TP4|C-019,C-032,C-048,C-059,J-021,J-214,J-268,J-462,J-890~894,J-US-065,M-080,M-092,M-847~854,N-1335~1357,N-320,N-365,N-424,N-454,N-488,N-560,N-595,N-635,N-657~658,N-675,N-711,PR-US-010b;T1|N-145,N-370,N-372,N-453,N-461,N-473,N-480,N-495,N-US-020,N-US-040;T2|N-086,N-146,N-168,N-224,N-311,N-324,N-531,N-567,N-US-005,PR-063~065;T3|PR-069~074;T4|PR-077~082', ';') loop
    s := split_part(part, '|', 1); body := substr(part, length(s) + 2);
    foreach tok in array string_to_array(body, ',') loop
      if position('~' in tok) > 0 then
        a := split_part(tok, '~', 1); b := split_part(tok, '~', 2);
        pre := substring(a from '^(.*?)\d+$'); num := substring(a from '(\d+)$');
        for k in num::int .. b::int loop
          update cards set sort = i where id = s || ':' || pre || lpad(k::text, length(num), '0'); i := i + 1;
        end loop;
      else
        update cards set sort = i where id = s || ':' || tok; i := i + 1;
      end if;
    end loop;
  end loop;
end $$;
update cards set rarity_code = case rarity when 'Common' then 'C' when 'Uncommon' then 'U' when 'Rare' then 'R' when 'Starter' then 'F' when 'Super Rare' then 'UR' when 'Promo' then 'P' when 'Ultra Rare' then 'UR' when 'Unknown' then '' else '' end;
update cards c set rarity_code = v.code from (values ('1:J-030','SR'),('1:J-036','SR'),('2:J-057','SR'),('2:J-073','SR'),('2:M-052','SR'),('2:M-080','SR'),('2:N-044','SR'),('2:N-058','SR'),('2:N-064','SR'),('2:N-082','SR'),('2:N-083','SR'),('2:N-084','SR'),('P:J-103','UR'),('P:N-046','C'),('P:N-095','UR'),('P:M-072','C')) v(id, code) where c.id = v.id;
update sets set source = 'RetroTCG' where id in ('10','11','12','13','14','15','16','17','18','19','20','21','22','23','24','25','26','27','28','TP1','TP2','TP3','TP4','T1','T2','T3','T4');
