// Stages finished card scans (already cut, webp) into scan_uploads so drain-scan-uploads publishes them within a minute.
// Claude pushes cut scans to the jonin-site repo's `scan-drop` branch (drop/*.webp), then calls this through
// stage_scans_from_drop(items). Only fetches from raw.githubusercontent.com/davidjoh140/jonin-site/.
// Body: {items:[{doc_id, card_id, printing, edition, source, asset, url}]}. doc_id = Card Index doc id (card~variant slug).
// Auth: x-drain-token must match app_secrets.drain_token.
import { createClient } from "npm:@supabase/supabase-js@2";

const sb = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, {
  auth: { persistSession: false },
});
const OK_PREFIX = "https://raw.githubusercontent.com/davidjoh140/jonin-site/";

function b64(buf: Uint8Array) {
  let s = "";
  for (let i = 0; i < buf.length; i += 0x8000) s += String.fromCharCode(...buf.subarray(i, i + 0x8000));
  return btoa(s);
}

Deno.serve(async (req) => {
  const { data: sec } = await sb.from("app_secrets").select("value").eq("name", "drain_token").single();
  if (!sec || req.headers.get("x-drain-token") !== sec.value) return new Response("no", { status: 401 });
  const { items } = await req.json().catch(() => ({ items: [] }));
  const out: unknown[] = [];
  for (const it of (items || []).slice(0, 40)) {
    try {
      if (!it.url?.startsWith(OK_PREFIX)) throw new Error("url not allowed");
      if (!it.doc_id || !it.card_id || !it.printing || !it.asset) throw new Error("missing fields");
      const r = await fetch(it.url);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const buf = new Uint8Array(await r.arrayBuffer());
      if (buf.length > 1_500_000) throw new Error("too big");
      const row = { doc_id: it.doc_id, card_id: it.card_id, printing: it.printing, edition: it.edition ?? null,
        source: it.source || "Online", asset: it.asset, b64: b64(buf), error: null };
      const up = await sb.from("scan_uploads").upsert(row, { onConflict: "doc_id" });
      if (up.error) throw new Error(up.error.message);
      out.push({ doc_id: it.doc_id, ok: true });
    } catch (e) {
      out.push({ doc_id: it?.doc_id, ok: false, error: String((e as Error).message || e) });
    }
  }
  return new Response(JSON.stringify(out), { headers: { "Content-Type": "application/json" } });
});
