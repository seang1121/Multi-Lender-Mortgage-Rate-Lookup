# Mortgage Rate Tracker

**Daily mortgage rate tracking with historical logging and trend analysis.**

![Python](https://img.shields.io/badge/python-3.7+-blue)
![Status](https://img.shields.io/badge/status-maintained-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## What It Does

Monitors 30-year and 15-year fixed mortgage rates for a given ZIP code, logs them daily to a JSON history file, and displays day-over-day and 7-day trend comparisons. Falls back across multiple data sources (Bankrate API, Chase Bank) to ensure reliable fetches.

## Features

- Automatic rate fetching from Bankrate API with Chase Bank fallback
- Historical logging to `rates_history.json` with deduplication
- Day-to-day comparison showing rate direction and magnitude
- 7-day trend analysis with absolute and relative change metrics
- Configurable alert thresholds and notification preferences
- Schedulable via Windows Task Scheduler or cron

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.7+ |
| HTTP | requests |
| Parsing | BeautifulSoup4, lxml |
| Data | JSON file storage |

## Quick Start

```bash
git clone https://github.com/seang1121/Mortgage-Rate-Tracker.git
cd Mortgage-Rate-Tracker
pip install -r requirements.txt
```

Edit `config.json` with your ZIP code:

```json
{
  "zip_code": "12540"
}
```

Run the tracker:

```bash
python mortgage_tracker.py
```

## Configuration

Edit `config.json` to customize behavior:

| Setting | Description |
|---------|-------------|
| `zip_code` | Your ZIP code for rate lookup |
| `daily_check_time` | Preferred time to check rates |
| `alert_threshold` | Minimum change to trigger alerts (%) |
| `alert_on_drop` | Alert when rates decrease |
| `minimum_change` | Minimum change worth noting |

## Sample Output

```
================================================================================
MORTGAGE RATE REPORT - ZIP 12540
2026-02-15 08:05 AM
================================================================================

CURRENT RATES
30-Year Fixed: 5.875% (APR: 5.943%)
15-Year Fixed: 5.125% (APR: 5.218%)

DAY-TO-DAY COMPARISON
DECREASED: -0.125% (-2.08%)

7-DAY TREND
2026-02-09: 6.250% ... 2026-02-15: 5.875%
7-Day Change: -0.375%
================================================================================
```

## Project Structure

| File | Purpose |
|------|---------|
| `mortgage_tracker.py` | Main script — fetches, compares, and logs rates |
| `config.json` | Settings (ZIP code, alert preferences) |
| `rates_history.json` | Auto-generated historical rate data |
| `requirements.txt` | Python dependencies |

## Automation

**Windows Task Scheduler:** Daily trigger at 8:05 AM, action runs `python mortgage_tracker.py`.

**Linux/Mac cron:**
```bash
5 8 * * * cd /path/to/mortgage-rate-tracker && python3 mortgage_tracker.py >> tracker.log 2>&1
```

## Disclaimer

This tool is for informational purposes only. Rates shown are indicative and may not reflect actual lender quotes. Always verify rates directly with lenders before making financial decisions.

## License

MIT
