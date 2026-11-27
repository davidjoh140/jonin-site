// Sends a seller a confirmation email after they submit jonin.cards/sell.
// Called by the sell page with {id, email}. Only sends once per lead, only for
// leads made in the last 15 minutes, and only to the email on the lead.
// Needs the RESEND_API_KEY secret; without it, it does nothing.
import { createClient } from "jsr:@supabase/supabase-js@2";
import { joninEmail, h, p, details } from "../_shared/jonin-email.ts";

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};
const json = (b: unknown, s = 200) =>
  new Response(JSON.stringify(b), { status: s, headers: { ...cors, "Content-Type": "application/json" } });

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
    .select("name,email,card_count,has_foils,handoff,photos,town,country,state,postal,city,selling,language,value_range").maybeSingle();
  if (!lead) return json({ sent: false, reason: "not found" });

  const first = String(lead.name).split(/\s+/)[0];
  const photos = (lead.photos ?? []).length;
  const rows: [string, string][] = [];
  const where = lead.country
    ? (lead.country === "United States" ? [lead.state, lead.postal].filter(Boolean).join(" ") : [lead.city, lead.country].filter(Boolean).join(", "))
    : lead.town;
  if (where) rows.push(["Location", where]);
  if ((lead.selling ?? []).length) rows.push(["Selling", lead.selling.join(", ")]);
  if (lead.language) rows.push(["Language", lead.language]);
  if (lead.card_count) rows.push(["Cards", lead.card_count]);
  if (lead.value_range) rows.push(["Rough value", lead.value_range]);
  else if (lead.has_foils) rows.push(["Shiny/foil", lead.has_foils]);
  rows.push(["Photos", String(photos)]);
  if (lead.handoff) rows.push(["Pickup or ship", lead.handoff]);

  // Shared Jonin template (../_shared/jonin-email.ts): buy@ banner + Jonin Buying signature.
  const mail = joninEmail("buy", {
    subject: "We got your cards - Jonin",
    preheader: "We'll look through everything and reach out soon.",
    blocks: [
      h(`Hi ${first}, we got your cards.`),
      p("We'll look through everything and reach out soon. Your offer may come from Jonin or a trusted buyer."),
      details("What you sent", Object.fromEntries(rows)),
      p("Questions or more photos? Just reply to this email."),
    ],
  });

  const r = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: { Authorization: `Bearer ${key}`, "Content-Type": "application/json" },
    body: JSON.stringify({
      from: mail.from,
      to: [lead.email],
      reply_to: "buy@jonin.cards",
      subject: mail.subject,
      text: mail.text, html: mail.html,
    }),
  });
  if (!r.ok) {
    // Release the claim so a retry can send.
    await db.from("sell_leads").update({ confirm_sent_at: null }).eq("id", id);
    return json({ sent: false, reason: "send failed", detail: (await r.text()).slice(0, 300) }, 502);
  }
  return json({ sent: true });
});
