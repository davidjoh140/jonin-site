// Copies files David attached to feedback notes (private bucket 'feedback-files', rows in feedback_files) into
// feedback_files.b64, so Claude can read them through the database and cut them into card scans.
// Only files with status 'new' and no b64 yet; up to 8 MB each. Called by kick_feedback_files().
// Auth: x-drain-token must match app_secrets.drain_token (same token as drain-scan-uploads / fetch-sale-photos).
import { createClient } from "npm:@supabase/supabase-js@2";

const sb = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, {
  auth: { persistSession: false },
});
const MAX_BYTES = 8_000_000;

function b64(buf: Uint8Array) {
  let s = "";
  for (let i = 0; i < buf.length; i += 0x8000) s += String.fromCharCode(...buf.subarray(i, i + 0x8000));
  return btoa(s);
}

Deno.serve(async (req) => {
  const { data: sec } = await sb.from("app_secrets").select("value").eq("name", "drain_token").single();
  if (!sec || req.headers.get("x-drain-token") !== sec.value) return new Response("no", { status: 401 });
  const { data: rows, error } = await sb.from("feedback_files").select("id,path")
    .eq("status", "new").is("b64", null).is("b64_error", null).order("created_at").limit(10);
  if (error) return new Response(error.message, { status: 500 });
  let done = 0, failed = 0;
  for (const r of rows || []) {
    try {
      const { data, error: e } = await sb.storage.from("feedback-files").download(r.path);
      if (e || !data) throw new Error(e?.message || "download failed");
      const buf = new Uint8Array(await data.arrayBuffer());
      if (buf.length > MAX_BYTES) throw new Error("too big (over 8 MB)");
      const up = await sb.from("feedback_files").update({ b64: b64(buf) }).eq("id", r.id);
      if (up.error) throw new Error(up.error.message);
      done++;
    } catch (e) {
      failed++;
      await sb.from("feedback_files").update({ b64_error: String((e as Error).message || e).slice(0, 300) }).eq("id", r.id);
    }
  }
  return new Response(JSON.stringify({ done, failed }), { headers: { "Content-Type": "application/json" } });
});
