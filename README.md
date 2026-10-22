# XRP Tracker

An information-only tracker for XRP: a price snapshot and chart, recent news from established outlets, and community chatter and rumors. Every item is labeled by source type (Official / Mainstream / Crypto press / Community / Rumor) and reliability (High / Medium / Low / Unverified / Contradicted).

**Information only, not financial advice; rumors are labeled and unverified.**

Live site: https://houseteam2020.github.io/xrp-tracker/

## How it works

- `data.json` holds the snapshot: price data (CoinGecko public API), news items, claims and their checks.
- `template.html` is the page layout; `build.py` fills it from `data.json` and writes `index.html`.
- In the browser, the page tries to fetch the live XRP price from CoinGecko's public API and falls back to the embedded snapshot, labeling which one is shown.
- No cookies, trackers, analytics or secrets.

## Rebuild

```
python3 build.py                  # rebuild index.html from data.json
python3 build.py --refresh-price  # refresh the price snapshot and 90-day closes, then rebuild
```
