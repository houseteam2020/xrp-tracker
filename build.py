#!/usr/bin/env python3
"""Rebuild the XRP Tracker static site.

Usage:
  python3 build.py                  # rebuild index.html from data.json
  python3 build.py --refresh-price  # first refresh price snapshot + 90-day closes from CoinGecko, then rebuild

News, claims, confirmed bullets and calendar live in data.json and are edited by hand
(or regenerated) after checking sources. Only the price block is refreshed automatically.
Output: index.html next to this script. Push index.html + data.json to the repo to publish.
"""
import datetime, html, json, sys, urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
MT = ZoneInfo("America/Denver")
CG = "https://api.coingecko.com/api/v3"

def esc(s): return html.escape(str(s), quote=True)

def fmt_mt(dt): return dt.astimezone(MT).strftime("%a %b %-d, %Y, %-I:%M %p %Z")

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "xrp-tracker-build/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def refresh_price(data):
    s = get(f"{CG}/simple/price?ids=ripple&vs_currencies=usd&include_24hr_change=true&include_market_cap=true&include_24hr_vol=true&include_last_updated_at=true")["ripple"]
    mc = get(f"{CG}/coins/ripple/market_chart?vs_currency=usd&days=90&interval=daily")["prices"]
    closes = []
    for t, v in mc[:-1]:  # 00:00 UTC points = prior day's close; last point is "now"
        day = datetime.datetime.fromtimestamp(t / 1000, datetime.timezone.utc) - datetime.timedelta(days=1)
        closes.append([day.strftime("%Y-%m-%d"), round(v, 4)])
    latest = mc[-1][1]
    def chg(n): return round((latest / closes[-n][1] - 1) * 100, 1)
    vals = [c[1] for c in closes]
    hi_i, lo_i = vals.index(max(vals)), vals.index(min(vals))
    d = lambda iso: datetime.date.fromisoformat(iso).strftime("%b %-d")
    now = datetime.datetime.now(datetime.timezone.utc)
    snap = data["snapshot"]
    snap.update({
        "fetched_mt": fmt_mt(now), "last_updated_mt": fmt_mt(now),
        "price": round(s["usd"], 4), "latest_point": round(latest, 4),
        "change_24h_pct": round(s["usd_24h_change"], 2),
        "market_cap_usd": s["usd_market_cap"], "volume_24h_usd": s["usd_24h_vol"],
        "change_7d_pct": chg(7), "change_30d_pct": chg(30), "change_90d_pct": chg(len(closes)),
        "range_90d": f"${min(vals):.2f} ({d(closes[lo_i][0])}) to ${max(vals):.2f} ({d(closes[hi_i][0])})",
        "cross_check": snap.get("cross_check_auto", "not re-checked in this refresh"),
    })
    data["closes"] = closes
    (HERE / "data.json").write_text(json.dumps(data, indent=1, ensure_ascii=False))

def pct(v): return ("+" if v >= 0 else "−") + f"{abs(v):.2f}%".replace(".00%", "%") if isinstance(v, (int, float)) else str(v)
def pct1(v): return ("+" if v >= 0 else "−") + f"{abs(v):.1f}%"
def money(v): return f"${v/1e9:.2f}B"

def pill(text, kind):
    cls = f"pill r-{esc(text)}" if kind == "rel" else "pill"
    return f'<span class="{cls}">{esc(text)}</span>'

def build(data):
    s = data["snapshot"]
    news = sorted(data["news"], key=lambda n: n["date"], reverse=True)
    news_html = "".join(
        f'<li>{pill(n["type"],"type")}{pill(n["reliability"],"rel")}<span class="muted">{esc(n["outlet"])} · {esc(datetime.date.fromisoformat(n["date"]).strftime("%b %-d, %Y"))}</span>'
        f'<div class="item-title"><a href="{esc(n["url"])}" rel="noopener noreferrer">{esc(n["headline"])}</a></div>'
        f'<div>{esc(n["summary"])}</div></li>' for n in news)
    claims_html = "".join(
        f'<li>{pill(c["type"],"type")}{pill(c["reliability"],"rel")}<span class="muted">{esc(c["who"])} · {esc(c["date"])}</span>'
        f'<div class="item-title claim-title">{esc(c["claim"])}</div>'
        f'<div><strong>Check:</strong> {esc(c["check"])}</div>'
        f'<div class="muted" style="margin-top:6px"><a href="{esc(c["post_url"])}" rel="noopener noreferrer">Original post</a>'
        + (f' · <a href="{esc(c["check_url"])}" rel="noopener noreferrer">{esc(c["check_title"])}</a>' if c.get("check_url") else "")
        + "</div></li>" for c in data["claims"])
    legend_html = "".join(f"<tr><td>{pill(l[0], l[1])}</td><td>{esc(l[2])}</td></tr>" for l in data["legend"])
    cal_html = "".join(f"<tr><td>{esc(a)}</td><td><strong>{esc(b)}</strong><br>{esc(c)}</td><td>{esc(d)}</td></tr>" for a, b, c, d in data["calendar"])
    dates = [n["date"] for n in data["news"]]
    f = lambda iso: datetime.date.fromisoformat(iso).strftime("%b %-d")
    repl = {
        "LAST_UPDATED": esc(s["last_updated_mt"]), "FETCHED": esc(s["fetched_mt"]),
        "CONFIRMED": "".join(f"<li>{esc(c)}</li>" for c in data["confirmed"]),
        "NOT_CONFIRMED": esc(data["not_confirmed"]),
        "PRICE": esc(f'{s["price"]:.4f}'.rstrip("0").rstrip(".")), "SOURCE": esc(s["source"]), "SOURCE_URL": esc(s["source_url"]),
        "CHG24": esc(pct(s["change_24h_pct"])), "CROSS": esc(s["cross_check"]),
        "MCAP": money(s["market_cap_usd"]), "VOL": money(s["volume_24h_usd"]), "RANGE": esc(s["range_90d"]),
        "CHGS": esc(f'{pct1(s["change_7d_pct"])} / {pct1(s["change_30d_pct"])} / {pct1(s["change_90d_pct"])}'),
        "LEGEND": legend_html, "NEWS": news_html, "CLAIMS": claims_html, "CALENDAR": cal_html,
        "NEWS_RANGE": esc(f"{f(min(dates))} to {f(max(dates))}, {max(dates)[:4]}"),
        "CLOSES_JSON": json.dumps(data["closes"]).replace("</", "<\\/"),
    }
    out = (HERE / "template.html").read_text()
    for k, v in repl.items():
        out = out.replace("{{" + k + "}}", v)
    assert "{{" not in out, "unfilled placeholder"
    (HERE / "index.html").write_text(out)
    print("wrote", HERE / "index.html")

if __name__ == "__main__":
    data = json.loads((HERE / "data.json").read_text())
    if "--refresh-price" in sys.argv:
        refresh_price(data)
    build(data)
