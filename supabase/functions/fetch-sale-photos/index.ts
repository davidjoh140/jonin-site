// Downloads sold-listing photos (sale_scan_queue, status 'pending') so the Buying Desk can cut them into card
// scans. The Buying Desk page can't load eBay images itself (its sandbox blocks other sites), so the photo is
// stored as base64 in the queue row. Called by pg_cron through kick_sale_photos(). Auth: x-drain-token must
// match app_secrets.drain_token (same token as drain-scan-uploads).
import { createClient } from "npm:@supabase/supabase-js@2";

const sb = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, {
  auth: { persistSession: false },
});
const PER_CALL = 15;
const MAX_BYTES = 900_000;

function b64(buf: Uint8Array) {
  let s = "";
  for (let i = 0; i < buf.length; i += 0x8000) s += String.fromCharCode(...buf.subarray(i, i + 0x8000));
  return btoa(s);
}

async function get(url: string) {
  const r = await fetch(url, { headers: { "User-Agent": "jonin-cards/1.0" } });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  const type = r.headers.get("content-type") || "";
  if (!type.startsWith("image/")) throw new Error("not an image: " + type);
  const buf = new Uint8Array(await r.arrayBuffer());
  if (buf.length > MAX_BYTES) throw new Error("too big");
  return buf;
}

Deno.serve(async (req) => {
  const { data: sec } = await sb.from("app_secrets").select("value").eq("name", "drain_token").single();
  if (!sec || req.headers.get("x-drain-token") !== sec.value) return new Response("no", { status: 401 });
  const { data: rows, error } = await sb.from("sale_scan_queue").select("sale_id,image_url,tries")
    .eq("status", "pending").lt("tries", 3).order("created_at").limit(PER_CALL);
  if (error) return new Response(error.message, { status: 500 });
  let done = 0, failed = 0;
  for (const r of rows || []) {
    try {
      let buf: Uint8Array;
      try { buf = await get(r.image_url); }
      catch (_) { buf = await get(r.image_url.replace(/s-l\d+\.jpg$/, "s-l1000.jpg")); }
      const up = await sb.from("sale_scan_queue").update({ photo_b64: b64(buf), status: "fetched", error: null })
        .eq("sale_id", r.sale_id).eq("status", "pending");
      if (up.error) throw new Error(up.error.message);
      done++;
    } catch (e) {
      failed++;
      const tries = (r.tries || 0) + 1;
      await sb.from("sale_scan_queue").update({ tries, error: String((e as Error).message || e).slice(0, 300),
        status: tries >= 3 ? "error" : "pending" }).eq("sale_id", r.sale_id);
    }
  }
  return new Response(JSON.stringify({ done, failed }), { headers: { "Content-Type": "application/json" } });
});
