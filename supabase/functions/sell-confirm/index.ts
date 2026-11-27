// Sends a seller a confirmation email after they submit jonin.cards/sell.
// Called by the sell page with {id, email}. Only sends once per lead, only for
// leads made in the last 15 minutes, and only to the email on the lead.
// Needs the RESEND_API_KEY secret; without it, it does nothing.
import { createClient } from "jsr:@supabase/supabase-js@2";

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};
const json = (b: unknown, s = 200) =>
  new Response(JSON.stringify(b), { status: s, headers: { ...cors, "Content-Type": "application/json" } });
const esc = (s: string) =>
  String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]!));

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  let body: { id?: number; email?: string };
  try { body = await req.json(); } catch { return json({ sent: false, reason: "bad request" }, 400); }
  const id = Number(body.id), email = String(body.email ?? "").trim().toLowerCase();
  if (!id || !email) return json({ sent: false, reason: "bad request" }, 400);

  const key = Deno.env.get("RESEND_API_KEY");
  if (!key) return json({ sent: false, reason: "not configured" });

  const db = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!);
  // Claim the lead atomically so it can only ever send once.
  const { data: lead } = await db.from("sell_leads")
    .update({ confirm_sent_at: new Date().toISOString() })
    .eq("id", id).eq("email", email).is("confirm_sent_at", null)
    .gt("created_at", new Date(Date.now() - 15 * 60 * 1000).toISOString())
    .select("name,email,card_count,has_foils,handoff,photos,town").maybeSingle();
  if (!lead) return json({ sent: false, reason: "not found" });

  const first = String(lead.name).split(/\s+/)[0];
  const photos = (lead.photos ?? []).length;
  const rows: [string, string][] = [];
  if (lead.card_count) rows.push(["Cards", lead.card_count]);
  if (lead.has_foils) rows.push(["Shiny/foil", lead.has_foils]);
  rows.push(["Photos", String(photos)]);
  if (lead.handoff) rows.push(["Pickup or ship", lead.handoff]);
  if (lead.town) rows.push(["Town/ZIP", lead.town]);

  const text = `Hi ${first},

We got your cards. We'll look through everything and reach out soon.
Your offer may come from Jonin or a trusted buyer.

What you sent:
${rows.map(([k, v]) => `- ${k}: ${v}`).join("\n")}

Questions or more photos? Just reply to this email.

Jonin
jonin.cards`;

  const html = `<div style="font-family:Arial,sans-serif;font-size:15px;line-height:1.5;color:#222;max-width:520px">
<p>Hi ${esc(first)},</p>
<p><b>We got your cards.</b> We'll look through everything and reach out soon.<br>Your offer may come from Jonin or a trusted buyer.</p>
<p style="margin-bottom:4px"><b>What you sent</b></p>
<table style="border-collapse:collapse;font-size:14px">${rows.map(([k, v]) =>
    `<tr><td style="padding:2px 14px 2px 0;color:#777">${esc(k)}</td><td style="padding:2px 0">${esc(v)}</td></tr>`).join("")}</table>
<p>Questions or more photos? Just reply to this email.</p>
<p>Jonin<br><a href="https://jonin.cards" style="color:#E8743B">jonin.cards</a></p></div>`;

  const r = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: { Authorization: `Bearer ${key}`, "Content-Type": "application/json" },
    body: JSON.stringify({
      from: "Jonin <buy@jonin.cards>",
      to: [lead.email],
      reply_to: "buy@jonin.cards",
      subject: "We got your cards - Jonin",
      text, html,
    }),
  });
  if (!r.ok) {
    // Release the claim so a retry can send.
    await db.from("sell_leads").update({ confirm_sent_at: null }).eq("id", id);
    return json({ sent: false, reason: "send failed", detail: (await r.text()).slice(0, 300) }, 502);
  }
  return json({ sent: true });
});
