// Jonin email template — one shared look for every email sent from a jonin.cards address.
//
// Usage:
//   import { joninEmail, h, p, button, details, cardAlert } from "../_shared/jonin-email.ts";
//   const { from, html, text } = joninEmail("buy", {
//     subject: "We got your cards - Jonin",
//     preheader: "We'll look through everything and reach out soon.",
//     blocks: [h("Hi David,"), p("We got your cards..."), details({ Cards: "100–500" })],
//   });
//
// Senders (who signs, which links show):
//   david  -> David Johannesson <david@jonin.cards>  personal emails, member emails, announcements
//   buy    -> Jonin <buy@jonin.cards>                 seller confirmations, offers, buying follow-ups
//   alerts -> Jonin Club <alerts@jonin.cards>         price / listing / Alt Art alerts
//
// Images are hosted at https://jonin.cards/email/ so they load in Gmail, Apple Mail and Outlook
// without attachments.

export type Sender = "david" | "buy" | "alerts";

const SITE = "https://jonin.cards";
const IMG = `${SITE}/email`;

export const COLORS = {
  ink: "#141019",      // headings
  text: "#2a1e1a",     // body text
  muted: "#6e5a4e",    // secondary text
  faint: "#b8aea6",    // footer
  red: "#b5121b",      // Akatsuki red: buttons, links
  orange: "#f57c00",   // Naruto orange: accents
  cream: "#fff8ef",    // card background
  line: "#eadbc7",     // borders
  page: "#f4ede4",     // outside the card
};

export const LINKS = {
  site: SITE,
  sell: `${SITE}/sell`,
  club: `${SITE}/club`,
  instagram: "https://www.instagram.com/jonin.cards/",
  // PLACEHOLDER: this is the founders invite from the founding-member email. Swap for a members invite if needed.
  discord: "https://discord.gg/BarT4ePfHx",
  // PLACEHOLDER: no alert-settings page yet, so this points at the Club page.
  manageAlerts: `${SITE}/club`,
};

type Profile = {
  from: string;
  header: string;
  name: string;
  title: string;      // line under the name
  lines: string[];    // extra small lines under the title
  links: [string, string][];
  footer: string;     // default "why you got this" line
};

export const SENDERS: Record<Sender, Profile> = {
  david: {
    from: "David Johannesson <david@jonin.cards>",
    header: `${IMG}/header-david.png`,
    name: "David Johannesson",
    title: "Founder, Jonin", // PLACEHOLDER title — change to whatever David wants
    lines: ["The original Bandai Naruto CCG, and what your cards are worth."],
    links: [["jonin.cards", LINKS.site], ["Instagram", LINKS.instagram], ["Sell your cards", LINKS.sell]],
    footer: "You're getting this because you have an account at jonin.cards.",
  },
  buy: {
    from: "Jonin <buy@jonin.cards>",
    header: `${IMG}/header-buy.png`,
    name: "Jonin Buying",
    title: "Sell to Jonin or a trusted buyer",
    lines: ["Local pickup in NJ · NY · PA, or ship to us."],
    links: [["Get an offer", LINKS.sell], ["jonin.cards", LINKS.site], ["Instagram", LINKS.instagram]],
    footer: "You're getting this because you asked Jonin for an offer at jonin.cards/sell. Reply any time with questions or more photos.",
  },
  alerts: {
    from: "Jonin Club <alerts@jonin.cards>",
    header: `${IMG}/header-alerts.png`,
    name: "Jonin Club Alerts",
    title: "Fast alerts for the original Bandai Naruto CCG",
    lines: ["Questions? Email david@jonin.cards."],
    links: [["Manage alerts", LINKS.manageAlerts], ["Jonin Club", LINKS.club], ["Discord", LINKS.discord]],
    footer: "You're getting this because you turned on email alerts in Jonin Club.",
  },
};

// ---------- building blocks (each returns { html, text }) ----------

export type Block = { html: string; text: string };

export const esc = (s: unknown) =>
  String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

const row = (inner: string, pad = "0 32px 16px") => `<tr><td style="padding:${pad}">${inner}</td></tr>`;

/** Big heading, e.g. "Hey Tim, you're in." */
export const h = (t: string): Block => ({
  html: row(`<p style="margin:0;font-size:22px;line-height:1.3;font-weight:700;color:${COLORS.ink}">${esc(t)}</p>`, "4px 32px 12px"),
  text: t,
});

/** Paragraph. Pass trusted HTML with raw=true (e.g. inline <b> or links). */
export const p = (t: string, raw = false): Block => ({
  html: row(`<p style="margin:0;font-size:16px;line-height:1.55;color:${COLORS.text}">${raw ? t : esc(t)}</p>`),
  text: raw ? t.replace(/<[^>]+>/g, "") : t,
});

/** Bullet list with a bold lead per item. */
export const list = (items: [string, string][]): Block => ({
  html: row(`<table width="100%" cellpadding="0" cellspacing="0" role="presentation">${items.map(([b, t]) =>
    `<tr><td style="width:18px;vertical-align:top;padding:3px 0;color:${COLORS.orange};font-size:16px;line-height:1.5">●</td>` +
    `<td style="padding:3px 0;font-size:15px;line-height:1.5;color:${COLORS.text}"><b style="color:${COLORS.ink}">${esc(b)}</b>${t ? ` ${esc(t)}` : ""}</td></tr>`
  ).join("")}</table>`),
  text: items.map(([b, t]) => `- ${b}${t ? ` ${t}` : ""}`).join("\n"),
});

/** Bulletproof button (works in Outlook). */
export const button = (label: string, href: string, color = COLORS.red): Block => ({
  html: row(`<table cellpadding="0" cellspacing="0" role="presentation"><tr><td bgcolor="${color}" style="border-radius:10px;background:${color}">` +
    `<a href="${esc(href)}" style="display:inline-block;padding:14px 28px;font-size:16px;font-weight:700;color:#fff8ef;text-decoration:none;border-radius:10px">${esc(label)} →</a>` +
    `</td></tr></table>`, "8px 32px 20px"),
  text: `${label}: ${href}`,
});

/** Key/value recap box, e.g. what a seller submitted. */
export const details = (title: string, kv: Record<string, string>): Block => ({
  html: row(`<table width="100%" cellpadding="0" cellspacing="0" role="presentation" style="background:#ffffff;border:1px solid ${COLORS.line};border-radius:12px">` +
    `<tr><td colspan="2" style="padding:14px 18px 6px;font-size:12px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:${COLORS.orange}">${esc(title)}</td></tr>` +
    Object.entries(kv).map(([k, v]) =>
      `<tr><td style="padding:5px 18px;font-size:14px;color:${COLORS.muted};width:40%">${esc(k)}</td><td style="padding:5px 18px;font-size:14px;color:${COLORS.ink};font-weight:600">${esc(v)}</td></tr>`
    ).join("") + `<tr><td colspan="2" style="height:10px"></td></tr></table>`),
  text: `${title}:\n` + Object.entries(kv).map(([k, v]) => `- ${k}: ${v}`).join("\n"),
});

/** Listing alert card: photo, card name, price, version, button. */
export const cardAlert = (a: { name: string; price: string; version?: string; note?: string; image?: string; href: string; badge?: string }): Block => ({
  html: row(`<table width="100%" cellpadding="0" cellspacing="0" role="presentation" style="background:#ffffff;border:1px solid ${COLORS.line};border-radius:14px">` +
    `<tr>${a.image ? `<td style="width:120px;padding:14px;vertical-align:top"><img src="${esc(a.image)}" width="120" alt="" style="display:block;width:120px;height:auto;border-radius:8px;border:0"></td>` : ""}` +
    `<td style="padding:16px 18px 16px ${a.image ? "4px" : "18px"};vertical-align:top">` +
    (a.badge ? `<span style="display:inline-block;white-space:nowrap;padding:3px 10px;border-radius:20px;background:${COLORS.orange};color:#fff8ef;font-size:11px;font-weight:700;letter-spacing:.06em;text-transform:uppercase">${esc(a.badge)}</span>` : "") +
    `<p style="margin:8px 0 2px;font-size:18px;font-weight:700;color:${COLORS.ink};line-height:1.3">${esc(a.name)}</p>` +
    (a.version ? `<p style="margin:0;font-size:14px;color:${COLORS.muted}">${esc(a.version)}</p>` : "") +
    `<p style="margin:10px 0 0;font-size:26px;font-weight:800;color:${COLORS.red}">${esc(a.price)}</p>` +
    (a.note ? `<p style="margin:4px 0 0;font-size:13px;color:${COLORS.muted}">${esc(a.note)}</p>` : "") +
    `<table cellpadding="0" cellspacing="0" role="presentation" style="margin-top:12px"><tr><td bgcolor="${COLORS.red}" style="border-radius:8px;background:${COLORS.red}"><a href="${esc(a.href)}" style="display:inline-block;padding:10px 18px;font-size:14px;font-weight:700;color:#fff8ef;text-decoration:none">View listing →</a></td></tr></table>` +
    `</td></tr></table>`),
  text: `${a.badge ? `[${a.badge}] ` : ""}${a.name}${a.version ? ` (${a.version})` : ""} — ${a.price}${a.note ? `\n${a.note}` : ""}\nView listing: ${a.href}`,
});

/** Callout strip, e.g. an offer. */
export const callout = (title: string, body: string): Block => ({
  html: row(`<table width="100%" cellpadding="0" cellspacing="0" role="presentation" style="background:${COLORS.ink};border-radius:12px"><tr><td style="padding:16px 20px;border-left:5px solid ${COLORS.orange};border-radius:12px">` +
    `<p style="margin:0 0 4px;font-size:12px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:${COLORS.orange}">${esc(title)}</p>` +
    `<p style="margin:0;font-size:15px;line-height:1.5;color:#fff8ef">${esc(body)}</p></td></tr></table>`),
  text: `${title.toUpperCase()}: ${body}`,
});

// ---------- signature + shell ----------

function signature(s: Profile): Block {
  const links = s.links.map(([l, u]) =>
    `<a href="${esc(u)}" style="color:${COLORS.red};text-decoration:none;font-weight:600">${esc(l)}</a>`).join(`<span style="color:${COLORS.line}">&nbsp;&nbsp;|&nbsp;&nbsp;</span>`);
  const html = `<tr><td style="padding:8px 32px 26px"><table cellpadding="0" cellspacing="0" role="presentation" style="border-top:1px solid ${COLORS.line};width:100%"><tr>` +
    `<td style="width:56px;padding:18px 14px 0 0;vertical-align:top"><a href="${SITE}"><img src="${IMG}/mark.png" width="56" height="56" alt="Jonin" style="display:block;border:0;border-radius:12px"></a></td>` +
    `<td style="padding:18px 0 0;vertical-align:top;font-size:14px;line-height:1.5;color:${COLORS.muted}">` +
    `<div style="font-size:16px;font-weight:700;color:${COLORS.ink}">${esc(s.name)}</div>` +
    `<div style="color:${COLORS.orange};font-weight:600">${esc(s.title)}</div>` +
    s.lines.map((l) => `<div>${esc(l)}</div>`).join("") +
    `<div style="margin-top:6px">${links}</div></td></tr></table></td></tr>`;
  const text = `${s.name}\n${s.title}\n${s.lines.join("\n")}\n${s.links.map(([l, u]) => `${l}: ${u}`).join("\n")}`;
  return { html, text };
}

export function joninEmail(sender: Sender, opts: { subject: string; preheader?: string; blocks: Block[]; footer?: string }) {
  const s = SENDERS[sender];
  const sig = signature(s);
  const footer = opts.footer ?? s.footer;
  const html = `<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light"><title>${esc(opts.subject)}</title></head>` +
    `<body style="margin:0;padding:0;background:${COLORS.page}">` +
    (opts.preheader ? `<div style="display:none;max-height:0;overflow:hidden;opacity:0">${esc(opts.preheader)}</div>` : "") +
    `<table width="100%" cellpadding="0" cellspacing="0" role="presentation" style="background:${COLORS.page}"><tr><td align="center" style="padding:24px 10px">` +
    `<table width="100%" cellpadding="0" cellspacing="0" role="presentation" style="max-width:560px;background:${COLORS.cream};border:1px solid ${COLORS.line};border-radius:16px;overflow:hidden;font-family:Inter,'Segoe UI',Helvetica,Arial,sans-serif">` +
    `<tr><td style="padding:0"><a href="${SITE}"><img src="${s.header}" width="560" alt="Jonin" style="display:block;width:100%;max-width:560px;height:auto;border:0"></a></td></tr>` +
    `<tr><td style="height:22px;font-size:0;line-height:0">&nbsp;</td></tr>` +
    opts.blocks.map((b) => b.html).join("") +
    sig.html +
    `</table>` +
    `<p style="max-width:540px;margin:14px auto 0;font-family:Inter,Helvetica,Arial,sans-serif;font-size:12px;line-height:1.5;color:${COLORS.faint};text-align:center">${esc(footer)}<br>` +
    `<a href="${SITE}" style="color:${COLORS.faint}">jonin.cards</a> · <a href="${LINKS.instagram}" style="color:${COLORS.faint}">@jonin.cards</a></p>` +
    `</td></tr></table></body></html>`;
  const text = `${opts.blocks.map((b) => b.text).join("\n\n")}\n\n—\n${sig.text}\n\n${footer}`;
  return { from: s.from, subject: opts.subject, html, text };
}
