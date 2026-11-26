// PSA cert lookup for jonin.cards (2026-11-26). Deployed to Supabase as Edge Function 'psa-lookup' (verify_jwt off; checks the JWT itself).
// Member call: POST {cert, card_id} with their Supabase JWT -> grade, PSA label, slab photos, and whether it matches card_id.
//   Results are cached per cert in psa_certs, so each cert costs PSA calls once. Members come first on PSA's
//   100 calls/day (psa_take with no reserve); over the limit the cert is queued and looked up later.
// Queue call: POST {drain:true} with x-drain-token (pg_cron job 'psa-queue', hourly) works through pending slabs.
// PSA token: Edge Function secret PSA_TOKEN (Supabase dashboard → Edge Functions → Secrets), same value as the GitHub secret.
import { createClient } from "npm:@supabase/supabase-js@2";

const sb = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
const PSA = "https://api.psacard.com/publicapi";
const CORS = { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type", "Access-Control-Allow-Methods": "POST, OPTIONS" };
const json = (o: unknown, status = 200) => new Response(JSON.stringify(o), { status, headers: { ...CORS, "Content-Type": "application/json" } });
const STOP = new Set(["THE", "OF", "A", "AN", "AND", "TO", "NO", "JUTSU", "STYLE", "NARUTO"]);
const words = (s: string) => (String(s || "").toUpperCase().match(/[A-Z0-9']+/g) || []).filter((w) => !STOP.has(w));
const key = (n: string) => String(n || "").toUpperCase().replace(/[^A-Z0-9]/g, "").replace(/(?<=[A-Z])0+(?=\d)/g, "").replace(/^0+(?=\d)/, "");
const digits = (n: string) => (String(n || "").match(/\d+/g) || []).join("").replace(/^0+/, "");

// Tolerate a pasted "bearer " prefix, quotes or whitespace around the token.
const clean = (t: string) => String(t || "").trim().replace(/^["']|["']$/g, "").replace(/^bearer\s+/i, "").trim();
let TOK = clean(Deno.env.get("PSA_TOKEN") || "");
async function psaToken() {
  if (!TOK) {
    const { data } = await sb.from("app_secrets").select("value").eq("name", "psa_token").maybeSingle();
    TOK = clean(data?.value || "");
  }
  return TOK;
}

async function fetchCert(cert: string) {
  const tok = await psaToken();
  if (!tok) throw new Error("PSA token not set");
  const h = { Authorization: `bearer ${tok}` };
  const r = await fetch(`${PSA}/cert/GetByCertNumber/${cert}`, { headers: h });
  if (r.status === 404) return { status: "not_found" };
  if (!r.ok) throw new Error(`PSA ${r.status} (token ${tok.length} chars): ${(await r.text()).slice(0, 200)}`);
  const info = (await r.json())?.PSACert;
  if (!info || !info.CertNumber) return { status: "not_found" };
  const ri = await fetch(`${PSA}/cert/GetImagesByCertNumber/${cert}`, { headers: h });
  const imgs = ri.ok ? await ri.json() : [];
  const front = (imgs || []).find((i: any) => i.IsFrontImage)?.ImageURL || null;
  const back = (imgs || []).find((i: any) => i.IsFrontImage === false)?.ImageURL || null;
  return { status: "ok", info, front, back };
}

// Which card in the list this cert is: same number (dashes/zeros ignored; digits-only PSA numbers compare digits) and a shared name word.
async function matchCard(info: any, prefer?: string) {
  const d = digits(info.CardNumber);
  if (!d) return null;
  const { data } = await sb.from("cards").select("id,number,name").ilike("number", `%${d}%`).limit(200);
  const subj = new Set(words(info.Subject));
  const pnum = String(info.CardNumber || "");
  const hits = (data || []).filter((c: any) => {
    const numOk = /[A-Za-z]/.test(pnum) ? key(c.number) === key(pnum) : digits(c.number) === d;
    return numOk && words(c.name).some((w) => subj.has(w));
  });
  if (prefer && hits.some((c: any) => c.id === prefer)) return prefer;
  return hits[0]?.id || null;
}

async function lookup(cert: string, prefer?: string) {
  try {
    const res: any = await fetchCert(cert);
    let row: any = { cert, status: res.status, fetched_at: new Date().toISOString() };
    if (res.status === "ok") {
      const i = res.info, m = String(i.CardGrade || "").match(/(\d+(?:\.5)?)\s*$/);
      row = { ...row, card_id: await matchCard(i, prefer), grade: m ? m[1] : null, grade_label: i.CardGrade || null,
        subject: i.Subject || null, card_number: i.CardNumber || null, year: i.Year || null, brand: i.Brand || null,
        variety: i.Variety || null, front: res.front, back: res.back, info: i };
    }
    await sb.from("psa_certs").upsert(row);
    return row;
  } catch (e) {
    const row = { cert, status: "error", info: { error: String((e as Error).message || e) }, fetched_at: new Date().toISOString() };
    await sb.from("psa_certs").upsert(row);
    return row;
  }
}

const out = (r: any, card_id?: string) => r.status === "ok"
  ? { status: "ok", grade: r.grade, grade_label: r.grade_label, subject: r.subject, card_number: r.card_number, year: r.year,
      brand: r.brand, variety: r.variety, front: r.front, back: r.back, match: !!card_id && r.card_id === card_id, matched_card_id: r.card_id }
  : r.status === "not_found" ? { status: "not_found" } : { status: "queued" };

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: CORS });
  const body = await req.json().catch(() => ({}));

  if (body.drain) {
    const { data: sec } = await sb.from("app_secrets").select("value").eq("name", "drain_token").single();
    if (!sec || req.headers.get("x-drain-token") !== sec.value) return json({ error: "no" }, 401);
    if (!(await psaToken())) return json({ done: 0, reason: "no token yet" });
    const { data: certs } = await sb.rpc("psa_pending_certs", { p_limit: 20 });
    let done = 0;
    for (const cert of (certs || []) as string[]) {
      const { data: ok } = await sb.rpc("psa_take", { p_calls: 2, p_reserve: 0 });
      if (!ok) break;
      await lookup(cert); done++;
    }
    return json({ done });
  }

  const jwt = (req.headers.get("Authorization") || "").replace(/^Bearer\s+/i, "");
  const { data: u } = await sb.auth.getUser(jwt);
  if (!u?.user) return json({ error: "Sign in to look up a cert." }, 401);
  const cert = String(body.cert || "").replace(/\D/g, "");
  const card_id = body.card_id ? String(body.card_id) : undefined;
  if (!/^\d{6,10}$/.test(cert)) return json({ status: "bad_cert" });

  const { data: cached } = await sb.from("psa_certs").select("*").eq("cert", cert).maybeSingle();
  if (cached && cached.status !== "error") {
    if (cached.status === "ok" && card_id && !cached.card_id) {
      // cached with no card match yet: try again against this card (no PSA call needed)
      const m = await matchCard(cached.info, card_id);
      if (m) { await sb.from("psa_certs").update({ card_id: m }).eq("cert", cert); cached.card_id = m; }
    }
    return json(out(cached, card_id));
  }
  if (!(await psaToken())) return json({ status: "queued", reason: "no_token" });

  const since = new Date(Date.now() - 864e5).toISOString();
  const { count } = await sb.from("psa_requests").select("id", { count: "exact", head: true }).eq("user_id", u.user.id).gte("at", since);
  const { data: cap } = await sb.rpc("psa_member_cap");
  if ((count || 0) >= (cap || 10)) return json({ status: "queued", reason: "daily_cap" });
  const { data: ok } = await sb.rpc("psa_take", { p_calls: 2, p_reserve: 0 });
  if (!ok) return json({ status: "queued", reason: "psa_limit" });
  await sb.from("psa_requests").insert({ user_id: u.user.id, cert });
  return json(out(await lookup(cert, card_id), card_id));
});
