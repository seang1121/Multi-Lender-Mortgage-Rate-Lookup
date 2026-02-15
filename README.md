# 🏠 Mortgage Rate Tracker

![Python Version](https://img.shields.io/badge/python-3.7+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Maintenance](https://img.shields.io/badge/maintained-yes-brightgreen.svg)

**Daily mortgage rate tracking with historical logging and trend analysis**

Track 30-year and 15-year mortgage rates for your ZIP code, log them daily, and see day-to-day changes at a glance.

---

## 🎯 Key Features

✅ **Automatic Rate Fetching** - Pulls current rates from Bankrate API and Chase Bank
✅ **Historical Logging** - Saves every day's rates to track trends over time
✅ **Day-to-Day Comparison** - Shows if rates went up or down since yesterday
✅ **7-Day Trend Analysis** - View weekly rate movements
✅ **Change Alerts** - See percentage changes and exact differences
✅ **Multi-Source** - Falls back to alternate sources if primary fails

---

## 📊 What It Looks Like

```
================================================================================
📈 MORTGAGE RATE REPORT - ZIP 12540
📅 2026-02-15 08:05 AM
================================================================================

💰 CURRENT RATES
--------------------------------------------------------------------------------
30-Year Fixed: 5.875% (APR: 5.943%)
15-Year Fixed: 5.125% (APR: 5.218%)

📊 DAY-TO-DAY COMPARISON
--------------------------------------------------------------------------------
📉 DECREASED: -0.125% (-2.08%)
   Yesterday: 6.000%
   Today: 5.875%

📉 7-DAY TREND
--------------------------------------------------------------------------------
2026-02-09: 6.250%
2026-02-10: 6.125%
2026-02-11: 6.000%
2026-02-12: 5.875%
2026-02-13: 5.875%
2026-02-14: 6.000%
2026-02-15: 5.875%

7-Day Change: -0.375%

================================================================================
📊 Total logged entries: 45
================================================================================
```

---

## 🚀 Quick Start

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/seang1121/Mortgage-Rate-Tracker.git
   cd Mortgage-Rate-Tracker
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure your ZIP code:**
   Edit `config.json` and set your ZIP code:
   ```json
   {
     "zip_code": "12540"
   }
   ```

4. **Run the tracker:**
   ```bash
   python mortgage_tracker.py
   ```

---

## 📋 How It Works

### First Run
On your first run, the tracker will:
1. Fetch current mortgage rates for your ZIP code
2. Save them to `rates_history.json`
3. Display the current rates (no comparison yet)

### Daily Runs
Each subsequent run will:
1. Fetch today's rates
2. Compare with yesterday's rates
3. Show the difference (increased/decreased)
4. Display 7-day trend (if available)
5. Save today's data to history

### Rate Sources

The tracker tries multiple sources in order:
1. **Bankrate API** (Primary) - Most reliable, JSON API
2. **Chase Bank** (Fallback) - Direct from Chase website

If both fail, it displays your last known rates from history.

---

## ⚙️ Configuration

Edit `config.json` to customize:

```json
{
  "zip_code": "12540",
  "tracking": {
    "enabled": true,
    "daily_check_time": "08:05 AM EST",
    "alert_threshold": 0.125
  },
  "notification": {
    "enabled": false,
    "alert_on_drop": true,
    "minimum_change": 0.0625
  }
}
```

### Options

| Setting | Description |
|---------|-------------|
| `zip_code` | Your ZIP code for rate lookup |
| `daily_check_time` | Preferred time to check rates |
| `alert_threshold` | Minimum change to trigger alerts (%) |
| `alert_on_drop` | Alert when rates decrease |
| `minimum_change` | Minimum change worth noting |

---

## 🤖 Automate Daily Tracking

### Windows (Task Scheduler)

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger: Daily at 8:05 AM
4. Action: Start a program
   - Program: `python`
   - Arguments: `C:\path\to\mortgage_tracker.py`
   - Start in: `C:\path\to\mortgage-rate-tracker\`

### Linux/Mac (Cron)

Add to crontab:
```bash
5 8 * * * cd /path/to/mortgage-rate-tracker && python3 mortgage_tracker.py >> tracker.log 2>&1
```

This runs daily at 8:05 AM and logs output.

---

## 📁 Files Explained

| File | Purpose |
|------|---------|
| `mortgage_tracker.py` | Main script that fetches and logs rates |
| `config.json` | Your settings (ZIP code, preferences) |
| `rates_history.json` | Historical rate data (auto-generated) |
| `requirements.txt` | Python dependencies |
| `README.md` | This documentation |

---

## 📊 Understanding the Output

### Rate Change Indicators

| Symbol | Meaning |
|--------|---------|
| 📈 | Rates increased from yesterday |
| 📉 | Rates decreased from yesterday |
| ➡️  | No change from yesterday |

### Change Percentage

The tracker shows two values:
- **Absolute Change**: e.g., `-0.125%` (actual percentage point difference)
- **Relative Change**: e.g., `(-2.08%)` (percentage of change relative to yesterday's rate)

**Example:**
```
Yesterday: 6.000%
Today: 5.875%
Change: -0.125% (-2.08%)
```

Calculation: `(5.875 - 6.000) / 6.000 * 100 = -2.08%`

---

## 🎯 Use Cases

### 1. Rate Shopping
Check daily to catch when rates drop below your target.

### 2. Refinance Monitoring
Track if rates drop enough to make refinancing worth it.

### 3. Market Analysis
Study historical trends to understand rate movements.

### 4. Lock Decision
See if rates are trending up (lock now) or down (wait).

---

## 🔧 Troubleshooting

### "Unable to fetch rates from any source"

**Possible causes:**
- Network connectivity issues
- Source websites changed structure
- Rate limiting from too many requests

**Solutions:**
- Check your internet connection
- Wait 1 hour and try again
- Check if Bankrate or Chase websites are accessible

### "Rate already logged for [date]"

This is normal! The tracker only logs once per day to prevent duplicates.

### Empty history file

If `rates_history.json` gets deleted, it will be recreated on next run. Your historical data will be lost, but tracking will resume.

---

## 📈 Data Format

Historical data is stored in JSON:

```json
{
  "rates": [
    {
      "date": "2026-02-15",
      "timestamp": "2026-02-15T08:05:23",
      "zip_code": "12540",
      "30_year_rate": "5.875",
      "30_year_apr": "5.943",
      "15_year_rate": "5.125",
      "15_year_apr": "5.218"
    }
  ]
}
```

You can export this data to Excel/CSV for further analysis.

---

## 🤝 Contributing

Found a bug? Have a feature request?
- Open an issue on GitHub
- Submit a pull request

---

## 📜 License

MIT License - Free to use and modify

---

## ⚠️ Disclaimer

**This tool is for informational purposes only.**

- Rates shown are indicative and may not reflect actual quotes
- Always verify rates directly with lenders before making decisions
- Actual rates depend on credit score, down payment, and other factors
- This is not financial advice

---

## 🙏 Data Sources

- [Bankrate](https://www.bankrate.com) - Primary rate data
- [Chase Bank](https://www.chase.com/personal/mortgage/mortgage-rates) - Fallback source

---

**Built for smart homebuyers who want to track mortgage rates daily**

*Last updated: February 2026*
