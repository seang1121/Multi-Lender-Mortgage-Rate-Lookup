# Mortgage Rate Tracker

**Real-time multi-lender mortgage rate comparison — 9 lenders scraped in parallel.**

![Python](https://img.shields.io/badge/python-3.10+-blue)
![Lenders](https://img.shields.io/badge/lenders-9-green)
![Status](https://img.shields.io/badge/status-active-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)

## What It Does

Scrapes **9 mortgage lenders simultaneously** using stealth browser automation, compares 30-year and 15-year fixed rates side by side, tracks day-over-day movement, and stores 90 days of history. Finds you the lowest rate in seconds.

## Lenders Tracked

| Lender | Type | Products | APR |
|--------|------|----------|-----|
| **Bank of America** | Big 4 Bank | 30yr, 15yr | Yes |
| **Wells Fargo** | Big 4 Bank | 30yr, 15yr | Yes |
| **Navy Federal Credit Union** | Credit Union | 30yr, 15yr | Yes |
| **SoFi** | Online Lender | 30yr, 15yr | Yes |
| **US Bank** | National Bank | 30yr, 15yr | Yes |
| **Guaranteed Rate** | Online Lender | 30yr, 15yr | Yes |
| **LendingTree** | Aggregator | 30yr, 15yr, FHA, VA | Yes |
| **MND (Mortgage News Daily)** | Daily Index | 30yr, 15yr | -- |
| **Freddie Mac PMMS** | National Benchmark | 30yr, 15yr | -- |

## Sample Output

```
MORTGAGE RATE COMPARISON — Mar 25, 2026
ZIP 32224 | 7 lenders from 7 sources

--- 30-YEAR FIXED ---
  Navy Federal CU              5.625%                   << BEST
  Wells Fargo                  5.750%  (APR 5.968%)
  SoFi                         5.990%
  LendingTree Avg              6.200%  (APR 6.340%)
  Natl Avg (Freddie Mac)       6.220%
  Guaranteed Rate              6.250%  (APR 6.547%)
  US Bank                      6.375%  (APR 6.504%)
  vs last: avg DOWN 0.010%

--- 15-YEAR FIXED ---
  Navy Federal CU              5.250%                   << BEST
  LendingTree Avg              5.350%  (APR 5.580%)
  SoFi                         5.375%
  US Bank                      5.490%  (APR 5.760%)
  Guaranteed Rate              5.500%  (APR 5.919%)
  Natl Avg (Freddie Mac)       5.540%
  Wells Fargo                  5.625%  (APR 5.874%)

--- FHA 30-YEAR ---
  LendingTree Avg              5.790%  (APR 6.440%)

--- VA 30-YEAR ---
  LendingTree Avg              5.650%  (APR 5.820%)
```

## Features

- **Parallel scraping** — all 9 lenders hit simultaneously, full report in ~30 seconds
- **Stealth browser** — patchright (patched Chromium) bypasses anti-bot detection
- **4 product types** — 30-year fixed, 15-year fixed, FHA, VA
- **Day-over-day tracking** — shows avg rate movement vs last check
- **90-day history** — stored locally in JSON, auto-rotates
- **Best rate flagged** — lowest rate per product marked `<< BEST`
- **Sorted low to high** — best deals always on top
- **Freddie Mac direct API** — national benchmark via CSV endpoint (no browser needed)
- **Schedulable** — cron-ready, outputs to stdout for piping to Discord/Slack/email

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.10+ |
| Browser Engine | patchright (stealth Chromium) |
| Scraping | scrapling, patchright async API |
| Benchmark API | Freddie Mac PMMS (CSV) |
| Data | JSON file storage (90-day rolling) |
| Parallelism | asyncio.gather() |

## Quick Start

```bash
git clone https://github.com/seang1121/Multi-Lender-Mortgage-Rate-Lookup.git
cd Multi-Lender-Mortgage-Rate-Lookup
pip install -r requirements.txt
python -m patchright install chromium
```

Run the multi-lender comparison:

```bash
python3 mortgage_rate_report.py
```

Or run the legacy single-lender tracker:

```bash
python3 mortgage_tracker.py
```

## Configuration

Edit `config.json` to set your ZIP code:

```json
{
  "zip_code": "32224"
}
```

| Setting | Description |
|---------|-------------|
| `zip_code` | Your ZIP code for rate lookup |
| `daily_check_time` | Preferred time to check rates |
| `alert_threshold` | Minimum change to trigger alerts (%) |
| `lenders` | List of active lenders |

## Project Structure

| File | Purpose |
|------|---------|
| `mortgage_rate_report.py` | Multi-lender parallel scraper (primary) |
| `mortgage_tracker.py` | Legacy single-lender tracker |
| `config.json` | Settings (ZIP code, lenders, alerts) |
| `data/mortgage_rates_history.json` | Auto-generated rate history (gitignored) |
| `requirements.txt` | Python dependencies |

## Automation

Schedule with cron to run Mon/Wed/Fri at 9am:

```bash
0 9 * * 1,3,5 cd /path/to/Multi-Lender-Mortgage-Rate-Lookup && python3 mortgage_rate_report.py >> tracker.log 2>&1
```

## Architecture

```
                    mortgage_rate_report.py
                           |
              asyncio.gather() — all parallel
                    /      |      \
            patchright   patchright  urllib
            (stealth)   (stealth)   (CSV API)
               |           |          |
          BofA, WF,    LendingTree  Freddie Mac
         Navy Fed,     (averages)    PMMS
        SoFi, USB,
       Guaranteed Rate,
            MND
```

## Disclaimer

This tool is for informational purposes only. Rates shown are indicative and may not reflect actual lender quotes. Always verify rates directly with lenders before making financial decisions.

## License

MIT
