"""
mortgage_rate_report.py — Multi-lender mortgage rate comparison

Compares 13 lenders + 2 national benchmarks.
  - 6 lenders automated via patchright stealth browser (headless)
  - 7 lenders anti-bot protected (use --headed to attempt with visible browser)
  - Freddie Mac PMMS via direct CSV API
  - Mortgage News Daily via urllib (no browser needed)

Reliability:
  - Parallel first pass (all automated lenders at once)
  - Sequential retry for any that fail (resource contention on parallel)
  - urllib fallback for MND and Freddie Mac (no browser needed)
  - 2 attempts per lender before marking as failed

Usage:
  python3 mortgage_rate_report.py            # headless, automated lenders only
  python3 mortgage_rate_report.py --headed   # visible browser, attempts ALL 13 lenders
"""

import argparse
import asyncio
import json
import os
import re
import ssl
import urllib.request
from datetime import datetime

ZIP_CODE = "32224"
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
HISTORY_FILE = os.path.join(DATA_DIR, "mortgage_rates_history.json")
WAIT_MS = 10000

BENCHMARKS = {"Freddie Mac (natl avg)", "MND Index"}


# ─── RATE EXTRACTION ────────────────────────────────────────────────────────

def extract_rates(text, lender):
    """Extract rate/APR pairs from page text."""
    results = []
    for label, product in [
        (r'30[- ]?[Yy]ear(?:\s*[Ff]ixed)?', "30yr"),
        (r'15[- ]?[Yy]ear(?:\s*[Ff]ixed)?', "15yr"),
        (r'(?:7/6|7/1|5/1)\s*(?:ARM|Adj)', "ARM"),
    ]:
        m = re.search(label + r'.*?(\d\.\d{2,3})%.*?(?:APR|apr)[:\s]*(\d\.\d{2,3})%', text, re.DOTALL | re.IGNORECASE)
        if m:
            results.append({"lender": lender, "product": product, "rate": float(m.group(1)), "apr": float(m.group(2))})
            continue

        m = re.search(label + r'[\t\s]+(\d\.\d{2,3})%[\t\s]+(\d\.\d{2,3})%', text, re.IGNORECASE)
        if m:
            results.append({"lender": lender, "product": product, "rate": float(m.group(1)), "apr": float(m.group(2))})
            continue

        m = re.search(label + r'.*?is\s+(\d\.\d{2,3})%\s*\((\d\.\d{2,3})%\s*APR\)', text, re.DOTALL | re.IGNORECASE)
        if m:
            results.append({"lender": lender, "product": product, "rate": float(m.group(1)), "apr": float(m.group(2))})
            continue

        m = re.search(label + r'[^\d]*?(\d\.\d{2,3})%', text, re.DOTALL | re.IGNORECASE)
        if m and 3.0 <= float(m.group(1)) <= 12.0:
            results.append({"lender": lender, "product": product, "rate": float(m.group(1)), "apr": None})
    return results


# ─── TIER 1: DIRECT APIs (no browser) ───────────────────────────────────────

def fetch_freddie_mac_csv():
    """Freddie Mac PMMS — national benchmark via free CSV endpoint."""
    try:
        ctx = ssl.create_default_context()
        req = urllib.request.Request(
            "https://www.freddiemac.com/pmms/docs/PMMS_history.csv",
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=10, context=ctx) as r:
            lines = r.read().decode().strip().split("\n")
        last = lines[-1].split(",")
        results = []
        if len(last) >= 2 and last[1]:
            results.append({"lender": "Freddie Mac (natl avg)", "product": "30yr", "rate": float(last[1]), "apr": None})
        if len(last) >= 4 and last[3]:
            results.append({"lender": "Freddie Mac (natl avg)", "product": "15yr", "rate": float(last[3]), "apr": None})
        return results
    except Exception:
        return []


def fetch_mnd_urllib():
    """Mortgage News Daily — daily index via plain HTML (no browser needed)."""
    try:
        ctx = ssl.create_default_context()
        req = urllib.request.Request(
            "https://www.mortgagenewsdaily.com/mortgage-rates",
            headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
        )
        with urllib.request.urlopen(req, timeout=10, context=ctx) as r:
            html = r.read().decode("utf-8", errors="replace")
        text = re.sub(r'<[^>]+>', ' ', html)
        return extract_rates(text, "MND Index")
    except Exception:
        return []


# ─── TIER 2: STEALTH BROWSER SCRAPING ────────────────────────────────────────

BROWSER_SOURCES = [
    ("Bank of America", "https://promotions.bankofamerica.com/homeloans/homebuying-hub/home-loan-options?subCampCode=41490&dmcode=18099675931"),
    ("Wells Fargo", "https://www.wellsfargo.com/mortgage/rates/"),
    ("Navy Federal CU", "https://www.navyfederal.org/loans-cards/mortgage/mortgage-rates/"),
    ("SoFi", "https://www.sofi.com/home-loans/mortgage-rates/"),
    ("US Bank", "https://www.usbank.com/home-loans/mortgage/mortgage-rates.html"),
    ("Guaranteed Rate", "https://www.rate.com/mortgage-rates"),
]

BROWSER_ASSISTED = ["Chase", "Rocket Mortgage", "Citi", "LoanDepot", "TD Bank", "Mr. Cooper", "PNC"]

# These require a visible browser (headed mode) to bypass anti-bot
HEADED_SOURCES = [
    ("Chase", "https://www.chase.com/personal/mortgage/mortgage-rates"),
    ("Rocket Mortgage", "https://www.rocketmortgage.com/mortgage-rates"),
    ("Citi", "https://online.citi.com/US/ag/mortgage/fixed-rate-mortgage"),
    ("LoanDepot", "https://www.loandepot.com/mortgage-rates"),
    ("TD Bank", "https://www.td.com/us/en/personal-banking/home-loans/mortgage-rates"),
    ("Mr. Cooper", "https://www.mrcooper.com/mortgage-rates"),
    ("PNC", "https://www.pnc.com/en/personal-banking/borrowing/home-lending/mortgage-rates.html"),
]


async def scrape_lender(browser, name, url):
    """Scrape a single lender with stealth browser."""
    try:
        ctx = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="en-US",
        )
        page = await ctx.new_page()
        await page.goto(url, timeout=20000, wait_until="domcontentloaded")
        await page.wait_for_timeout(WAIT_MS)
        text = await page.inner_text("body")
        await ctx.close()
        return name, extract_rates(text, name)
    except Exception:
        try:
            await ctx.close()
        except Exception:
            pass
        return name, []


async def scrape_all_browser(headed=False):
    """Scrape lenders — parallel first, retry failures, optionally include headed lenders."""
    from patchright.async_api import async_playwright

    sources = list(BROWSER_SOURCES)
    if headed:
        # In headed mode, also attempt the anti-bot protected lenders
        sources.extend(HEADED_SOURCES)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=not headed)

        # Pass 1: all in parallel (max 4 at a time in headed mode to avoid overload)
        if headed and len(sources) > 4:
            # Batch parallel to avoid overwhelming the machine
            final = []
            for batch_start in range(0, len(sources), 4):
                batch = sources[batch_start:batch_start + 4]
                tasks = [scrape_lender(browser, name, url) for name, url in batch]
                results = await asyncio.gather(*tasks)
                for (name, rates), (orig_name, orig_url) in zip(results, batch):
                    if rates:
                        final.append((name, rates))
                    else:
                        # Retry failed ones from this batch
                        retry_name, retry_rates = await scrape_lender(browser, orig_name, orig_url)
                        final.append((retry_name, retry_rates))
        else:
            tasks = [scrape_lender(browser, name, url) for name, url in sources]
            results = await asyncio.gather(*tasks)

            final = []
            retry_list = []
            for (name, rates), (orig_name, orig_url) in zip(results, sources):
                if rates:
                    final.append((name, rates))
                else:
                    retry_list.append((orig_name, orig_url))

            if retry_list:
                for name, url in retry_list:
                    retry_name, retry_rates = await scrape_lender(browser, name, url)
                    final.append((retry_name, retry_rates))

        await browser.close()
    return final


# ─── HISTORY ─────────────────────────────────────────────────────────────────

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE) as f:
            return json.load(f)
    return []


def save_history(history):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


# ─── REPORT FORMATTING ──────────────────────────────────────────────────────

def format_report(unique, successes, failures, history):
    """Build the formatted rate comparison report."""
    last_rates = history[-1].get("rates", {}) if history else {}

    lender_count = len(set(r["lender"] for r in unique if r["lender"] not in BENCHMARKS))
    benchmark_count = len(set(r["lender"] for r in unique if r["lender"] in BENCHMARKS))

    today = datetime.now().strftime("%b %d, %Y")
    lines = [
        f"MORTGAGE RATE COMPARISON \u2014 {today}",
        f"   {lender_count} lenders + {benchmark_count} benchmarks | sorted lowest to highest",
        "",
    ]

    for product in ["30yr", "15yr", "ARM", "FHA 30yr", "VA 30yr"]:
        product_rates = sorted(
            [r for r in unique if r["product"] == product],
            key=lambda r: r["rate"]
        )
        if not product_rates:
            continue

        label = {
            "30yr": "30-YEAR FIXED", "15yr": "15-YEAR FIXED", "ARM": "ARM",
            "FHA 30yr": "FHA 30-YEAR", "VA 30yr": "VA 30-YEAR",
        }.get(product, product)
        lines.append(f"--- {label} " + "-" * (48 - len(label)))
        lines.append("")

        for i, r in enumerate(product_rates):
            rate_str = f"{r['rate']:.3f}%"
            apr_str = f"  ({r['apr']:.3f}% APR)" if r.get("apr") else ""
            is_benchmark = r["lender"] in BENCHMARKS
            benchmark_tag = "  \u00B7\u00B7\u00B7\u00B7\u00B7\u00B7\u00B7\u00B7\u00B7\u00B7\u00B7\u00B7\u00B7\u00B7\u00B7\u00B7\u00B7\u00B7\u00B7\u00B7 benchmark" if is_benchmark else ""

            # Best = first non-benchmark lender
            is_best = (i == 0 and len(product_rates) > 1 and not is_benchmark)
            if not is_best and i > 0:
                # Check if this is the first non-benchmark
                prior_non_bench = [r2 for r2 in product_rates[:i] if r2["lender"] not in BENCHMARKS]
                if not prior_non_bench and not is_benchmark:
                    is_best = True

            if is_best:
                lines.append(f"  \U0001F3C6 {r['lender']:28s} {rate_str}{apr_str}{'':>20s} BEST")
            else:
                lines.append(f"     {r['lender']:28s} {rate_str}{apr_str}{benchmark_tag}")

        # Day-over-day
        prev = last_rates.get(product, [])
        if prev and product_rates:
            curr_avg = sum(r["rate"] for r in product_rates) / len(product_rates)
            prev_avg = sum(r["rate"] for r in prev) / len(prev)
            diff = curr_avg - prev_avg
            avg_str = f"{curr_avg:.3f}%"
            if abs(diff) >= 0.005:
                arrow = "\u25B2" if diff > 0 else "\u25BC"
                lines.append("")
                lines.append(f"  \U0001F4CA Avg: {avg_str}  |  vs yesterday: {arrow} {abs(diff):.3f}%")
            else:
                lines.append("")
                lines.append(f"  \U0001F4CA Avg: {avg_str}  |  vs yesterday: unchanged")

        lines.append("")

    # Browser-assisted lenders (only show if not already attempted)
    attempted = set(successes + failures)
    needs_browser = [l for l in BROWSER_ASSISTED if l not in attempted]
    script_failures = [f for f in failures if f not in ("Freddie Mac", "MND") and f not in BROWSER_ASSISTED]
    needs_browser.extend(script_failures)
    if needs_browser:
        lines.append(f"Need browser check: {', '.join(needs_browser)}")

    return "\n".join(lines)


# ─── MAIN ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Multi-lender mortgage rate comparison")
    parser.add_argument("--headed", action="store_true",
                        help="Run visible browser to attempt all 13 lenders (bypasses anti-bot on some sites)")
    args = parser.parse_args()

    browser_count = len(BROWSER_SOURCES) + (len(HEADED_SOURCES) if args.headed else 0)
    total = browser_count + 2  # + Freddie Mac + MND
    mode = "headed (visible browser)" if args.headed else "headless"
    print(f"Scraping {total} sources in {mode} mode...\n")

    all_rates = []
    successes = []
    failures = []

    # Tier 1: Direct APIs (no browser, instant)
    fm_rates = fetch_freddie_mac_csv()
    if fm_rates:
        all_rates.extend(fm_rates)
        successes.append("Freddie Mac")
    else:
        failures.append("Freddie Mac")

    mnd_rates = fetch_mnd_urllib()
    if mnd_rates:
        all_rates.extend(mnd_rates)
        successes.append("MND")
    else:
        failures.append("MND")

    # Tier 2: Browser scraping (parallel + sequential retry)
    browser_results = asyncio.run(scrape_all_browser(headed=args.headed))

    for name, rates in browser_results:
        if rates:
            all_rates.extend(rates)
            successes.append(name)
        else:
            failures.append(name)

    if not all_rates:
        print("No rates fetched from any source.")
        return

    # Deduplicate
    seen = set()
    unique = []
    for r in all_rates:
        key = (r["lender"], r["product"])
        if key not in seen:
            seen.add(key)
            unique.append(r)

    # History
    history = load_history()

    # Format and print
    report = format_report(unique, successes, failures, history)
    print(report)

    # Save history
    today_key = datetime.now().strftime("%Y-%m-%d")
    rates_by_product = {}
    for product in ["30yr", "15yr", "ARM", "FHA 30yr", "VA 30yr"]:
        pr = [r for r in unique if r["product"] == product]
        if pr:
            rates_by_product[product] = [
                {"lender": r["lender"], "rate": r["rate"], "apr": r.get("apr")}
                for r in pr
            ]

    if history and history[-1].get("date") == today_key:
        history[-1]["rates"] = rates_by_product
    else:
        history.append({"date": today_key, "rates": rates_by_product})

    history = history[-90:]
    save_history(history)


if __name__ == "__main__":
    main()
