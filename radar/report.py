"""The AI market brief and the 2 PM HTML email (Gmail SMTP with an app password)."""
import html
import logging
import os
import smtplib
from email.message import EmailMessage

from .classify import gemini_json, resolve_model

log = logging.getLogger(__name__)
SITE = "https://databricks-stock-market-lakehouse.vercel.app"

BRIEF_PROMPT = """Write a 3-sentence market brief for an Indian retail investor at 2 PM IST.
They buy in delivery before the close and sell the next day once a stock is up 1%.
Use only these facts; no advice disclaimers, no markdown, no greeting.
Indices: {indices}
Today's top picks (score 0-100, reason): {picks}
Other notable headlines: {headlines}
Reply as JSON: {{"brief": "<3 sentences>"}}"""


def market_brief(run: dict, gemini_cfg: dict) -> str:
    picks = [c for c in run["candidates"] if c["is_pick"]]
    indices = "; ".join(f"{k} {v['change_pct']:+.2f}%" for k, v in run["indices"].items())
    fallback = (f"{len(picks)} stocks cleared the news, liquidity and momentum checks today"
                + (f", led by {picks[0]['name']} ({picks[0]['headline']})." if picks else "."))
    key = os.environ.get("GEMINI_API_KEY")
    model = key and resolve_model(gemini_cfg["model"], key)
    if not model:
        return fallback
    try:
        prompt = BRIEF_PROMPT.format(
            indices=indices,
            picks="; ".join(f"{c['symbol']} {c['score']:.0f} ({c['headline']})" for c in picks) or "none",
            headlines="; ".join(n["title"] for n in run["news"] if n["impact"] >= 2 and n["sentiment"] > 0)[:1500])
        return str(gemini_json(prompt, model, key)["brief"]).strip() or fallback
    except Exception as exc:
        log.warning("Brief generation failed: %s", exc)
        return fallback


def _row(c: dict, news_by_id: dict) -> str:
    e = html.escape
    items = [news_by_id[i] for i in c["news_ids"] if i in news_by_id][:2]
    links = "<br>".join(f'<a href="{e(n["url"])}" style="color:#2563eb">{e(n["title"][:110])}</a>'
                        f' <span style="color:#94a3b8">({e(n["outlet"])})</span>' for n in items)
    reach = f"{c['reach_rate'] * 100:.0f}%" if c.get("reach_rate") is not None else "-"
    color = "#16a34a" if (c["day_change_pct"] or 0) >= 0 else "#dc2626"
    return f"""<tr>
<td style="padding:10px 8px;border-bottom:1px solid #e2e8f0;vertical-align:top">
 <a href="{SITE}/stock/{e(c['symbol'])}" style="font-weight:700;color:#0f172a;text-decoration:none">{e(c['symbol'])}</a>
 <div style="color:#64748b;font-size:12px">{e(c['name'])}</div></td>
<td style="padding:10px 8px;border-bottom:1px solid #e2e8f0;vertical-align:top;text-align:right;white-space:nowrap">
 Rs {c['price']:,.2f}<div style="color:{color};font-size:12px">{c['day_change_pct']:+.2f}%</div></td>
<td style="padding:10px 8px;border-bottom:1px solid #e2e8f0;vertical-align:top;text-align:right;white-space:nowrap">
 <b>Rs {c['target_price']:,.2f}</b><div style="color:#64748b;font-size:12px">hit +1% on {reach} of days</div></td>
<td style="padding:10px 8px;border-bottom:1px solid #e2e8f0;vertical-align:top;text-align:center">
 <span style="background:#1e40af;color:#fff;border-radius:999px;padding:3px 9px;font-weight:700">{c['score']:.0f}</span></td>
<td style="padding:10px 8px;border-bottom:1px solid #e2e8f0;vertical-align:top;font-size:13px">{links}</td></tr>"""


def render_email(run: dict, record: dict) -> str:
    news_by_id = {n["id"]: n for n in run["news"]}
    picks = [c for c in run["candidates"] if c["is_pick"]]
    indices = " &nbsp;·&nbsp; ".join(
        f"{k} <b style='color:{'#16a34a' if v['change_pct'] >= 0 else '#dc2626'}'>{v['change_pct']:+.2f}%</b>"
        for k, v in run["indices"].items())
    rows = "".join(_row(c, news_by_id) for c in picks) or (
        '<tr><td colspan="5" style="padding:16px;color:#64748b">No stock passed all checks today. '
        "Sitting out is a valid trade.</td></tr>")
    track = (f"Last {record['days']} trading days: picks reached +1% next day "
             f"<b>{record['pick_hits']}/{record['picks']}</b> ({record['pick_hit_rate']}%)"
             + (f", other candidates {record['other_hit_rate']}%." if record["other_hit_rate"] is not None else ".")
             if record["picks"] else "Track record starts building from tomorrow.")
    return f"""<div style="font-family:Segoe UI,Arial,sans-serif;max-width:760px;margin:auto;color:#0f172a">
<div style="background:linear-gradient(135deg,#0b1f4b,#1e40af);color:#fff;padding:20px 22px;border-radius:14px 14px 0 0">
 <div style="font-size:12px;letter-spacing:1px;opacity:.8">NSE NEWS RADAR · {run['market_date']} · 2 PM</div>
 <div style="font-size:22px;font-weight:700;margin-top:4px">{len(picks)} stocks with fresh positive news</div>
 <div style="font-size:13px;margin-top:6px;opacity:.9">{indices}</div></div>
<div style="background:#eff6ff;padding:14px 22px;font-size:14px;line-height:1.5">{html.escape(run['brief'])}</div>
<table style="width:100%;border-collapse:collapse;font-size:14px">
<tr style="background:#f8fafc;color:#64748b;font-size:12px;text-align:left">
<th style="padding:8px">Stock</th><th style="padding:8px;text-align:right">Now</th>
<th style="padding:8px;text-align:right">+1% target</th><th style="padding:8px">Score</th><th style="padding:8px">Why</th></tr>
{rows}</table>
<div style="padding:14px 22px;font-size:13px;color:#334155;background:#f8fafc">{track}
 <br><a href="{SITE}" style="color:#2563eb">Open the dashboard</a> for charts, all news and the full track record.</div>
<div style="padding:10px 22px;font-size:11px;color:#94a3b8">Scores come from news, historical next-day reach,
 momentum and volume. They are signals, not guarantees; use a stop-loss.</div></div>"""


def send_email(run: dict, record: dict, test: bool = False) -> bool:
    user = (os.environ.get("GMAIL_USER") or "").strip()
    password = "".join((os.environ.get("GMAIL_APP_PASSWORD") or "").split())
    if not user or not password:
        log.info("Gmail secrets not set; skipping email")
        return False
    picks = [c["symbol"] for c in run["candidates"] if c["is_pick"]]
    msg = EmailMessage()
    msg["Subject"] = (("[TEST] " if test else "") + f"2 PM Radar {run['market_date']}: "
                      + (", ".join(picks) if picks else "no picks today"))
    msg["From"] = user
    msg["To"] = (os.environ.get("MAIL_TO") or "").strip() or user
    msg.set_content("Open this email in an HTML-capable client, or visit " + SITE)
    msg.add_alternative(render_email(run, record), subtype="html")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(user, password)
        smtp.send_message(msg)
    log.info("Email sent to %s", msg["To"])
    return True
