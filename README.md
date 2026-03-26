# Multi-Lender Mortgage Rate Lookup

> Compare mortgage rates across **10 lenders** and **2 national benchmarks** in a single command. All major banks, credit unions, and online lenders — scraped in parallel, ranked lowest to highest, with day-over-day market tracking.

![Python](https://img.shields.io/badge/python-3.10+-blue)
![Lenders](https://img.shields.io/badge/lenders-10-brightgreen)
![Benchmarks](https://img.shields.io/badge/benchmarks-2-blue)
![Schedule](https://img.shields.io/badge/runs-daily-orange)
![License](https://img.shields.io/badge/license-MIT-green)

---

## The Problem

Shopping for the best mortgage rate means opening a dozen bank websites, entering your info on each one, waiting for JavaScript to load, and manually comparing numbers. Every. Single. Day.

## The Solution

One command. 10 lenders. 2 national benchmarks. Sorted best to worst. Typically completes in 30-90 seconds depending on network speed and lender response times.

The script hits every lender simultaneously using stealth browser automation, extracts the current rate and APR, compares them against Freddie Mac and Mortgage News Daily national averages, tracks how rates moved since yesterday, and gives you a clean ranked report you can pipe to Discord, Slack, email, or any automation pipeline.

---

## How We Beat Anti-Bot Protection

Major banks don't want you scraping their rate pages. They use JavaScript-rendered SPAs, Cloudflare protection, bot detection fingerprinting, and rate-limiting to block automated access. A simple `requests.get()` or even a standard headless browser will get blocked, served empty pages, or fed placeholder text like `X.XXX%`.

**How this tool gets through:**

| Challenge | How We Solve It |
|-----------|----------------|
| JavaScript-rendered rates | **patchright** — a stealth-patched Chromium that renders full JS like a real browser |
| Bot detection fingerprinting | patchright spoofs browser fingerprints (WebGL, canvas, navigator properties) to look like a real user |
| Rate-limiting / IP blocking | Batches of 4 lenders at a time with retry logic — never hammers a single site |
| ZIP code gates (Chase) | Auto-detects ZIP input fields, fills them, and clicks "See Rates" before extracting |
| Session-dependent rates (BofA) | Uses specific promo URLs that serve rates on first load without multi-step navigation |
| Cloudflare challenges | patchright bypasses standard Cloudflare browser checks without needing API keys |

Every lender required a different approach to crack. The URLs, wait times, and extraction patterns in this script are the result of testing each bank individually until we found what works.

**If a lender stops working:** Bank websites change their structure regularly. If a lender starts returning empty results, use `--headed` mode to open a visible browser and see what changed. Then update the URL or regex pattern accordingly.

---

## What Gets Tracked

### 10 Lenders

| # | Lender | Type |
|---|--------|------|
| 1 | **Bank of America** | Big 4 Bank |
| 2 | **Wells Fargo** | Big 4 Bank |
| 3 | **Chase** | Big 4 Bank |
| 4 | **Citi** | Big 4 Bank |
| 5 | **Navy Federal Credit Union** | Credit Union |
| 6 | **SoFi** | Online Lender |
| 7 | **US Bank** | National Bank |
| 8 | **Guaranteed Rate** | Online Lender |
| 9 | **Truist** | National Bank |
| 10 | **Mr. Cooper** | Largest Servicer |

All 10 lenders are fully automated — no manual browser intervention needed.

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
MORTGAGE RATE COMPARISON — Mar 25, 2026
   10 lenders tracked + 2 benchmarks | 10 reporting now

--- 30-YEAR FIXED -----------------------------------------------

  [BEST] Navy Federal CU         5.625%                     BEST
     Wells Fargo             5.750%  (5.968% APR)
     SoFi                    5.990%
     Freddie Mac (natl avg)  6.220%  ·················· benchmark
     Guaranteed Rate         6.250%  (6.547% APR)
     Truist                  6.350%  (6.510% APR)
     Chase                   6.375%  (6.481% APR)
     US Bank                 6.375%  (6.504% APR)
     Bank of America         6.500%  (6.738% APR)
     MND Index               6.480%  ·················· benchmark
     Citi                    6.625%  (6.750% APR)
     Mr. Cooper              6.750%  (6.820% APR)

  Avg: 6.330%  |  vs yesterday: down 0.010%

--- 15-YEAR FIXED -----------------------------------------------

  [BEST] Navy Federal CU         5.250%                     BEST
     SoFi                    5.375%
     US Bank                 5.490%  (5.760% APR)
     Guaranteed Rate         5.500%  (5.919% APR)
     Freddie Mac (natl avg)  5.540%  ·················· benchmark
     Wells Fargo             5.625%  (5.874% APR)
     Truist                  5.700%  (5.980% APR)
     Bank of America         5.750%  (6.134% APR)
     Chase                   5.875%  (6.012% APR)
     Citi                    5.875%  (6.050% APR)

  Avg: 5.628%  |  vs yesterday: down 0.015%
```

---

## Getting Started

### Install

> **Note:** On Windows, use `python` instead of `python3`. On macOS/Linux, either works.

```bash
git clone https://github.com/seang1121/Multi-Lender-Mortgage-Rate-Lookup.git
cd Multi-Lender-Mortgage-Rate-Lookup

# Create a virtual environment (recommended)
python -m venv venv

# Activate it:
# Windows (PowerShell):  venv\Scripts\Activate.ps1
# Windows (Git Bash):    source venv/Scripts/activate
# macOS / Linux:         source venv/bin/activate

pip install -r requirements.txt
python -m patchright install chromium
```

### Configure

Set your ZIP code in `config.json`:

```json
{
  "zip_code": "90210"
}
```

Or pass it on the command line (overrides config.json):

```bash
python mortgage_rate_report.py --zip 90210
```

If neither is set, defaults to `12540` (LaGrangeville, NY).

### Run

```bash
# Headless mode — scrapes all 10 lenders + 2 benchmarks
python mortgage_rate_report.py

# Headed mode — visible browser, useful for debugging
python mortgage_rate_report.py --headed

# Override ZIP code
python mortgage_rate_report.py --zip 10001
```

---

## Run It as an Agent, Bot, or Scheduled Task

The script outputs clean text to stdout. Pipe it anywhere.

### Daily cron job (macOS/Linux)
```bash
0 8 * * * cd /path/to/Multi-Lender-Mortgage-Rate-Lookup && python mortgage_rate_report.py >> rates.log 2>&1
```

### Windows Task Scheduler
```powershell
schtasks /create /tn "MortgageRates" /tr "python C:\path\to\mortgage_rate_report.py" /sc daily /st 08:00
```

### Discord bot
```python
import subprocess

output = subprocess.run(
    ["python", "mortgage_rate_report.py"],
    capture_output=True, text=True
)
send_to_discord(channel_id, output.stdout)
```

### Slack webhook
```bash
python mortgage_rate_report.py | curl -X POST -H 'Content-type: application/json' \
  -d "{\"text\": \"$(cat -)\"}" https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### AI agent integration
Your agent runs the script, reads the output, and delivers it however you want — Discord, Telegram, email, SMS. The script handles all the scraping and formatting. Your agent just schedules and delivers.

```python
result = run_command("python mortgage_rate_report.py")
post_to_channel(result)
```

### Rate history for analysis
90 days of rate data stored at `data/mortgage_rates_history.json`. Use it for trend analysis, charting, or feeding into financial models.

---

## Headless vs Headed Mode

| Mode | Command | When to use |
|------|---------|-------------|
| **Headless** (default) | `python mortgage_rate_report.py` | Daily automation, cron jobs, servers. All 10 lenders work headless. |
| **Headed** | `python mortgage_rate_report.py --headed` | Debugging. Opens a visible browser so you can watch what each bank page is doing. Use this when a lender stops returning data — you'll see exactly what changed. |

---

## How It Works

```
                mortgage_rate_report.py
                        |
          asyncio.gather() — all in parallel
                        |
        +---------------+---------------+
        |               |               |
   patchright       patchright       urllib
   (stealth)       (stealth)       (CSV API)
        |               |               |
   BofA, WF,          MND          Freddie Mac
  Chase, Citi,       Index           PMMS
  Navy Fed, SoFi,
  USB, Guaranteed
  Rate, Truist,
  Mr. Cooper
```

**All 10 lenders** are scraped simultaneously with patchright — a stealth Chromium browser engine that bypasses bot detection. Each lender gets its own browser context, running in parallel batches of 4 via `asyncio.gather()`.

**Freddie Mac** is fetched via direct CSV API — no browser needed.

**Mortgage News Daily** is fetched via plain HTML with urllib — no browser needed.

---

## Tech Stack

| Component | What | Why |
|-----------|------|-----|
| Python 3.10+ | Core language | Async support, modern syntax |
| patchright | Stealth Chromium | Bypasses bot detection on bank sites |
| asyncio | Parallelism | All lenders scraped simultaneously |
| Freddie Mac CSV | Benchmark API | No browser needed, direct data |
| JSON | Storage | 90-day rolling rate history |

---

## Project Structure

```
Multi-Lender-Mortgage-Rate-Lookup/
├── mortgage_rate_report.py    # Multi-lender parallel scraper
├── config.json                # Your ZIP code
├── requirements.txt           # Python dependencies
├── CLAUDE.md                  # Project brain for AI agents
├── data/                      # Rate history (auto-created, gitignored)
└── README.md
```

---

## Troubleshooting

**patchright install fails or Chromium won't download**
- Make sure you ran `python -m patchright install chromium` after installing requirements
- On corporate networks, proxy settings may block the download. Set `HTTPS_PROXY` env var if needed
- Try running as administrator/sudo if you get permission errors

**SSL errors (`CERTIFICATE_VERIFY_FAILED`)**
- Common on macOS. Run: `pip install certifi` and ensure your Python is using updated CA certs
- On Windows, this is rare but can happen behind corporate firewalls

**All lenders return empty results**
- Some lenders rate-limit or block cloud IP ranges. Try again after a few minutes
- Use `--headed` mode to see what the browser is actually loading
- Check your internet connection and ensure no VPN is interfering

**`python3` not found (Windows)**
- Use `python` instead of `python3` on Windows
- Make sure Python is in your PATH: `python --version` should print your version

**Emoji not rendering in terminal**
- The report uses emoji characters. Most modern terminals support them
- If your terminal shows garbled text, redirect output to a file: `python mortgage_rate_report.py > report.txt`

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
