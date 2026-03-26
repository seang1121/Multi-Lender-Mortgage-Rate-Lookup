# Multi-Lender Mortgage Rate Lookup

**Compare mortgage rates across 15 lenders in seconds. One command. All the major banks, credit unions, and online lenders — scraped in parallel, sorted by lowest rate, with day-over-day tracking.**

![Python](https://img.shields.io/badge/python-3.10+-blue)
![Lenders](https://img.shields.io/badge/lenders-15-brightgreen)
![Schedule](https://img.shields.io/badge/schedule-daily-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## Why This Exists

Shopping for mortgage rates means opening 10+ bank websites, entering your info on each one, and manually comparing. This tool does all of that in one command — hits every lender simultaneously, extracts rates, sorts them, and tells you who has the best deal today.

Built for anyone who wants to track the mortgage market daily without lifting a finger.

---

## 15 Lenders Tracked

### Automated Scraping (runs without intervention)
| Lender | Type | Products |
|--------|------|----------|
| Bank of America | Big 4 Bank | 30yr, 15yr |
| Wells Fargo | Big 4 Bank | 30yr, 15yr |
| Navy Federal Credit Union | Credit Union | 30yr, 15yr |
| SoFi | Online Lender | 30yr, 15yr |
| US Bank | National Bank | 30yr, 15yr |
| Guaranteed Rate | Online Lender | 30yr, 15yr |
| Mortgage News Daily | Market Index | 30yr, 15yr |
| Freddie Mac PMMS | National Benchmark | 30yr, 15yr |

### Browser-Assisted (anti-bot protected — needs a real browser session)
| Lender | Type | Products |
|--------|------|----------|
| Chase | Big 4 Bank | 30yr, 15yr, ARM |
| Rocket Mortgage | #1 Online Lender | 30yr, 15yr, ARM |
| Citi | Big 4 Bank | 30yr, 15yr |
| LoanDepot | Online Lender | 30yr, 15yr |
| TD Bank | National Bank | 30yr, 15yr |
| Mr. Cooper | Largest Servicer | 30yr, 15yr |
| PNC | National Bank | 30yr, 15yr |

---

## Sample Output

```
MORTGAGE RATE COMPARISON
Mar 25, 2026 | 15 lenders

--- 30-YEAR FIXED -----------------------------------------------

  *  Navy Federal CU         5.625%                     BEST
     Wells Fargo             5.750%  (5.968% APR)
     SoFi                    5.990%
     Freddie Mac (natl avg)  6.220%
     Guaranteed Rate         6.250%  (6.547% APR)
     Chase                   6.375%  (6.481% APR)
     US Bank                 6.375%  (6.504% APR)
     Bank of America         6.500%  (6.738% APR)
     Rocket Mortgage         6.500%  (6.621% APR)
     Citi                    6.625%  (6.750% APR)
     LoanDepot               6.500%  (6.680% APR)
     TD Bank                 6.625%  (6.712% APR)
     Mr. Cooper              6.750%  (6.820% APR)
     PNC                     6.625%  (6.790% APR)
     MND Index               6.480%

     Avg: 6.330%  |  vs yesterday: DOWN 0.010%

--- 15-YEAR FIXED -----------------------------------------------

  *  Navy Federal CU         5.250%                     BEST
     SoFi                    5.375%
     US Bank                 5.490%  (5.760% APR)
     Guaranteed Rate         5.500%  (5.919% APR)
     Freddie Mac (natl avg)  5.540%
     Wells Fargo             5.625%  (5.874% APR)
     Bank of America         5.750%  (6.134% APR)
     ...

     Avg: 5.628%  |  vs yesterday: DOWN 0.015%
```

---

## Quick Start

```bash
git clone https://github.com/seang1121/Multi-Lender-Mortgage-Rate-Lookup.git
cd Multi-Lender-Mortgage-Rate-Lookup
pip install -r requirements.txt
python -m patchright install chromium
```

Run it:

```bash
python3 mortgage_rate_report.py
```

---

## Use It as an Agent or Plugin

This tool outputs clean text to stdout — pipe it anywhere.

### Daily cron job
```bash
0 8 * * * cd /path/to/Multi-Lender-Mortgage-Rate-Lookup && python3 mortgage_rate_report.py >> rates.log 2>&1
```

### Discord bot integration
```python
import subprocess
output = subprocess.run(["python3", "mortgage_rate_report.py"], capture_output=True, text=True)
send_to_discord(channel_id, output.stdout)
```

### Slack webhook
```bash
python3 mortgage_rate_report.py | curl -X POST -d @- https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### AI agent automation
Have your agent run the script on a schedule and post the results. The script handles scraping, comparison, and formatting — your agent just delivers it.

```python
# Example: scheduled agent runs daily, posts to your channel
result = run_command("python3 mortgage_rate_report.py")
post_to_channel(result)
```

### JSON history for analysis
Rate history is stored at `data/mortgage_rates_history.json` — 90-day rolling window. Use it for trend analysis, charting, or feeding into other tools.

---

## Configuration

Edit `config.json`:

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

## How It Works

```
mortgage_rate_report.py
        |
   asyncio.gather()  ──  all lenders hit in parallel
        |
   ┌────┴────────────────────────┐
   |                             |
   patchright (stealth)       urllib (API)
   |                             |
   BofA, Wells Fargo,        Freddie Mac
   Navy Federal, SoFi,       PMMS CSV
   US Bank, Guaranteed
   Rate, MND
   |
   Browser fallback
   (for anti-bot sites)
   |
   Chase, Rocket, Citi,
   LoanDepot, TD, PNC,
   Mr. Cooper
```

All automated lenders are scraped simultaneously using patchright — a stealth Chromium engine that bypasses bot detection. Anti-bot protected banks (Chase, Rocket, etc.) can be supplemented by a real browser session via your automation agent.

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.10+ |
| Browser | patchright (stealth Chromium) |
| Scraping | scrapling, patchright async |
| Benchmark | Freddie Mac PMMS CSV API |
| Storage | JSON (90-day rolling history) |
| Parallelism | asyncio.gather() |

---

## Project Structure

| File | Purpose |
|------|---------|
| `mortgage_rate_report.py` | Multi-lender parallel scraper |
| `mortgage_tracker.py` | Legacy single-lender tracker |
| `config.json` | ZIP code and alert settings |
| `data/` | Rate history (gitignored) |
| `requirements.txt` | Dependencies |

---

## Contributing

Pull requests welcome. If you find a working URL or API endpoint for any of the browser-assisted lenders, open an issue — that's the fastest way to improve coverage.

---

## Disclaimer

For informational purposes only. Rates are scraped from public pages and may not match actual lender quotes. Always verify directly with lenders before making financial decisions.

## License

MIT
