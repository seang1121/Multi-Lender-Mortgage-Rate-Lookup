# Multi-Lender Mortgage Rate Lookup

## What This Does
Scrapes mortgage rates from 13 lenders + 2 national benchmarks (Freddie Mac, Mortgage News Daily), ranks them lowest to highest, tracks day-over-day changes, outputs a clean text report.

## Quick Start
```bash
python -m venv venv && source venv/Scripts/activate  # Windows Git Bash
pip install -r requirements.txt
python -m patchright install chromium
python mortgage_rate_report.py --zip 32224
```

## Architecture

### Three Tiers of Data Fetching
1. **Tier 1 — Direct APIs (no browser):** Freddie Mac CSV endpoint + Mortgage News Daily HTML via `urllib`. Fastest, most reliable.
2. **Tier 2 — Stealth browser (headless):** 6 automated lenders via `patchright` (stealth Chromium). Parallel batches of 4, sequential retry on failure.
3. **Tier 3 — Headed browser:** 7 anti-bot lenders (Chase, Rocket, Citi, etc.) only scraped with `--headed` flag. Requires a display.

### ZIP Code Resolution
Priority order: `--zip` CLI flag > `config.json` `zip_code` field > hardcoded default `32224`

### Retry Logic
- Batches of `BATCH_SIZE=4` lenders in parallel
- Failed lenders retry sequentially up to `MAX_RETRIES=3` times
- Wait increases per attempt: 8s, 12s, 15s (`WAIT_SCHEDULE`)

### Rate Extraction
`extract_rates()` uses regex patterns to find rate/APR pairs for 30yr, 15yr, ARM, FHA, VA products from raw page text. Rates validated to be between 3.0% and 12.0%.

## File Map
| File | Purpose |
|------|---------|
| `mortgage_rate_report.py` | Main script — scraping, formatting, history |
| `config.json` | User ZIP code config |
| `requirements.txt` | Single dep: patchright |
| `data/mortgage_rates_history.json` | 90-day rolling rate history (auto-created, gitignored) |

## Conventions
- **Only external dep is patchright.** Everything else is stdlib (`asyncio`, `urllib`, `json`, `re`, `ssl`, `argparse`).
- **No database.** History is a JSON file capped at 90 entries.
- **Output is plain text to stdout.** Designed to be piped to Discord/Slack/email/any automation.

## Known Limitations
- Anti-bot lenders (Chase, Rocket, Citi, LoanDepot, TD Bank, Mr. Cooper, PNC) require `--headed` mode with a display
- "30 seconds" runtime is happy-path only. With retries and headed mode, expect 1-3 minutes.
- Lender page structures change without notice — regex extraction may need updating
- Emoji in output may not render in all terminals
