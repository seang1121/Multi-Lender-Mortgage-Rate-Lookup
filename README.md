# Multi-Lender Mortgage Rate Lookup

> Compare mortgage rates across **13 lenders** and **2 national benchmarks** in a single command. All major banks, credit unions, and online lenders — scraped in parallel, ranked lowest to highest, with day-over-day market tracking.

![Python](https://img.shields.io/badge/python-3.10+-blue)
![Lenders](https://img.shields.io/badge/lenders-13-brightgreen)
![Benchmarks](https://img.shields.io/badge/benchmarks-2-blue)
![Schedule](https://img.shields.io/badge/runs-daily-orange)
![License](https://img.shields.io/badge/license-MIT-green)

---

## The Problem

Shopping for the best mortgage rate means opening a dozen bank websites, entering your info on each one, waiting for JavaScript to load, and manually comparing numbers. Every. Single. Day.

## The Solution

One command. 13 lenders. 2 national benchmarks. Sorted best to worst. In under 30 seconds.

The script hits every lender simultaneously using stealth browser automation, extracts the current rate and APR, compares them against Freddie Mac and Mortgage News Daily national averages, tracks how rates moved since yesterday, and gives you a clean ranked report you can pipe to Discord, Slack, email, or any automation pipeline.

---

## What Gets Tracked

### 13 Lenders

| # | Lender | Type | Method |
|---|--------|------|--------|
| 1 | **Bank of America** | Big 4 Bank | Automated |
| 2 | **Wells Fargo** | Big 4 Bank | Automated |
| 3 | **Chase** | Big 4 Bank | Browser-assisted |
| 4 | **Citi** | Big 4 Bank | Browser-assisted |
| 5 | **Navy Federal Credit Union** | Credit Union | Automated |
| 6 | **SoFi** | Online Lender | Automated |
| 7 | **Rocket Mortgage** | #1 Online Lender | Browser-assisted |
| 8 | **US Bank** | National Bank | Automated |
| 9 | **Guaranteed Rate** | Online Lender | Automated |
| 10 | **LoanDepot** | Online Lender | Browser-assisted |
| 11 | **TD Bank** | National Bank | Browser-assisted |
| 12 | **Mr. Cooper** | Largest Servicer | Browser-assisted |
| 13 | **PNC** | National Bank | Browser-assisted |

> **Automated** = stealth browser scrapes the rate without intervention.
> **Browser-assisted** = site has anti-bot protection; your automation agent checks it via real browser.

### 2 National Benchmarks

| Source | Description | Frequency |
|--------|-------------|-----------|
| **Freddie Mac PMMS** | Official national average from the Primary Mortgage Market Survey — the industry gold standard | Weekly |
| **Mortgage News Daily** | Real-time daily rate index tracked by mortgage professionals nationwide | Daily |

Every lender's rate is displayed alongside these benchmarks so you can immediately see who's above or below the national average.

### Products Compared

- 30-Year Fixed (rate + APR)
- 15-Year Fixed (rate + APR)
- FHA 30-Year (where available)
- VA 30-Year (where available)
- ARM (where available)

---

## Sample Output

```
🏠 MORTGAGE RATE COMPARISON — Mar 25, 2026
   13 lenders + 2 benchmarks | sorted lowest to highest

--- 30-YEAR FIXED -----------------------------------------------

  🏆 Navy Federal CU         5.625%                     BEST
     Wells Fargo             5.750%  (5.968% APR)
     SoFi                    5.990%
     Freddie Mac (natl avg)  6.220%  ·················· benchmark
     Guaranteed Rate         6.250%  (6.547% APR)
     Chase                   6.375%  (6.481% APR)
     US Bank                 6.375%  (6.504% APR)
     Bank of America         6.500%  (6.738% APR)
     Rocket Mortgage         6.500%  (6.621% APR)
     MND Index               6.480%  ·················· benchmark
     LoanDepot               6.500%  (6.680% APR)
     Citi                    6.625%  (6.750% APR)
     TD Bank                 6.625%  (6.712% APR)
     PNC                     6.625%  (6.790% APR)
     Mr. Cooper              6.750%  (6.820% APR)

  📊 Avg: 6.330%  |  vs yesterday: ▼ 0.010%

--- 15-YEAR FIXED -----------------------------------------------

  🏆 Navy Federal CU         5.250%                     BEST
     SoFi                    5.375%
     US Bank                 5.490%  (5.760% APR)
     Guaranteed Rate         5.500%  (5.919% APR)
     Freddie Mac (natl avg)  5.540%  ·················· benchmark
     Wells Fargo             5.625%  (5.874% APR)
     Bank of America         5.750%  (6.134% APR)
     Chase                   5.875%  (6.012% APR)
     Rocket Mortgage         5.750%  (5.890% APR)
     Citi                    5.875%  (6.050% APR)
     PNC                     5.875%  (6.010% APR)

  📊 Avg: 5.628%  |  vs yesterday: ▼ 0.015%
```

---

## Getting Started

### Install

```bash
git clone https://github.com/seang1121/Multi-Lender-Mortgage-Rate-Lookup.git
cd Multi-Lender-Mortgage-Rate-Lookup
pip install -r requirements.txt
python -m patchright install chromium
```

### Run

```bash
python3 mortgage_rate_report.py
```

### Configure

Set your ZIP code in `config.json`:

```json
{
  "zip_code": "YOUR_ZIP",
  "tracking": {
    "daily_check_time": "08:00 AM EST",
    "alert_threshold": 0.125
  }
}
```

---

## Run It as an Agent, Bot, or Scheduled Task

The script outputs clean text to stdout. Pipe it anywhere.

### Daily cron job (runs every morning)
```bash
0 8 * * * cd /path/to/Multi-Lender-Mortgage-Rate-Lookup && python3 mortgage_rate_report.py >> rates.log 2>&1
```

### Discord bot
```python
import subprocess

output = subprocess.run(
    ["python3", "mortgage_rate_report.py"],
    capture_output=True, text=True
)
send_to_discord(channel_id, output.stdout)
```

### Slack webhook
```bash
python3 mortgage_rate_report.py | curl -X POST -H 'Content-type: application/json' \
  -d "{\"text\": \"$(cat -)\"}" https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### AI agent integration
Your agent runs the script, reads the output, and delivers it however you want — Discord, Telegram, email, SMS. The script handles all the scraping and formatting. Your agent just schedules and delivers.

```python
result = run_command("python3 mortgage_rate_report.py")
post_to_channel(result)
```

### Rate history for analysis
90 days of rate data stored at `data/mortgage_rates_history.json`. Use it for trend analysis, charting, or feeding into financial models.

---

## How It Works

```
                mortgage_rate_report.py
                        |
          asyncio.gather() — all in parallel
                        |
        ┌───────────────┼───────────────┐
        |               |               |
   patchright       patchright       urllib
   (stealth)       (stealth)       (CSV API)
        |               |               |
   BofA, WF,          MND          Freddie Mac
  Navy Fed,          Index           PMMS
  SoFi, USB,
 Guaranteed Rate
        |
  Browser fallback
  (anti-bot sites)
        |
   Chase, Rocket,
  Citi, LoanDepot,
 TD, Mr. Cooper, PNC
```

**Automated lenders** are scraped simultaneously with patchright — a stealth Chromium browser engine that bypasses bot detection. Each lender gets its own browser context, all running in parallel via `asyncio.gather()`.

**Freddie Mac** is fetched via direct CSV API — no browser needed.

**Anti-bot protected banks** (Chase, Rocket, Citi, etc.) block headless browsers. These are designed to be supplemented by your automation agent using a real browser session.

---

## Tech Stack

| Component | What | Why |
|-----------|------|-----|
| Python 3.10+ | Core language | Async support, modern syntax |
| patchright | Stealth Chromium | Bypasses bot detection on bank sites |
| scrapling | Scraping framework | Browser fingerprint spoofing |
| asyncio | Parallelism | All lenders scraped simultaneously |
| Freddie Mac CSV | Benchmark API | No browser needed, direct data |
| JSON | Storage | 90-day rolling rate history |

---

## Project Structure

```
Multi-Lender-Mortgage-Rate-Lookup/
├── mortgage_rate_report.py    # Multi-lender parallel scraper (primary)
├── mortgage_tracker.py        # Legacy single-lender tracker
├── config.json                # Your ZIP code and settings
├── requirements.txt           # Python dependencies
├── data/                      # Rate history (gitignored)
└── README.md
```

---

## Roadmap

- **MCP Server** — Wrap as a Model Context Protocol server so any AI agent can call `get_rates(zip_code)` and get structured rate data back. Plug into Claude, ChatGPT, or any MCP-compatible platform as a live tool.
- **More lenders** — Community-sourced URLs and API endpoints for anti-bot protected banks
- **Rate alerts** — Notifications when rates drop below your target
- **Historical charts** — Visualize 90-day rate trends per lender
- **Multi-ZIP support** — Compare rates across different markets simultaneously

---

## Contributing

Pull requests welcome. The fastest way to improve coverage:

- Found a working URL or API endpoint for a browser-assisted lender? **Open an issue.**
- Built an integration (Discord bot, Slack app, Home Assistant)? **Share it.**
- Have a lender we're missing? **Submit a PR.**

---

## Disclaimer

For informational purposes only. Rates are scraped from publicly available pages and may not match actual lender quotes. Always verify directly with lenders before making financial decisions.

## License

MIT
