"""
mortgage_rate_report.py — Multi-lender mortgage rate comparison

Compares 13 lenders + 2 national benchmarks in parallel.
  - 6 lenders automated via patchright stealth browser
  - 7 lenders browser-assisted (anti-bot protected, listed for OpenClaw fallback)
  - Freddie Mac PMMS via direct CSV API
  - Mortgage News Daily via stealth browser

Usage: python3 mortgage_rate_report.py
"""

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

# Benchmark lender names — used to tag them in output
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
        # Pattern 1: label ... rate% ... APR ... apr%
        m = re.search(label + r'.*?(\d\.\d{2,3})%.*?(?:APR|apr)[:\s]*(\d\.\d{2,3})%', text, re.DOTALL | re.IGNORECASE)
        if m:
            results.append({"lender": lender, "product": product, "rate": float(m.group(1)), "apr": float(m.group(2))})
            continue

        # Pattern 2: tab-separated "30-year fixed\t6.500%\t6.738%" (BofA/Navy Federal)
        m = re.search(label + r'[\t\s]+(\d\.\d{2,3})%[\t\s]+(\d\.\d{2,3})%', text, re.IGNORECASE)
        if m:
            results.append({"lender": lender, "product": product, "rate": float(m.group(1)), "apr": float(m.group(2))})
            continue

        # Pattern 3: "rate in XXXXX is X.XXX% (X.XXX% APR)"
        m = re.search(label + r'.*?is\s+(\d\.\d{2,3})%\s*\((\d\.\d{2,3})%\s*APR\)', text, re.DOTALL | re.IGNORECASE)
        if m:
            results.append({"lender": lender, "product": product, "rate": float(m.group(1)), "apr": float(m.group(2))})
            continue

        # Pattern 4: rate only
        m = re.search(label + r'[^\d]*?(\d\.\d{2,3})%', text, re.DOTALL | re.IGNORECASE)
        if m and 3.0 <= float(m.group(1)) <= 12.0:
            results.append({"lender": lender, "product": product, "rate": float(m.group(1)), "apr": None})
    return results


# ─── TIER 1: DIRECT API ─────────────────────────────────────────────────────

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
        return "Freddie Mac", results
    except Exception:
        return "Freddie Mac", []


# ─── TIER 2: STEALTH BROWSER SCRAPING ────────────────────────────────────────

# Automated lenders (6 lenders + 1 benchmark)
BROWSER_SOURCES = [
    ("Bank of America", "https://promotions.bankofamerica.com/homeloans/homebuying-hub/home-loan-options?subCampCode=41490&dmcode=18099675931"),
    ("Wells Fargo", "https://www.wellsfargo.com/mortgage/rates/"),
    ("Navy Federal CU", "https://www.navyfederal.org/loans-cards/mortgage/mortgage-rates/"),
    ("SoFi", "https://www.sofi.com/home-loans/mortgage-rates/"),
    ("US Bank", "https://www.usbank.com/home-loans/mortgage/mortgage-rates.html"),
    ("Guaranteed Rate", "https://www.rate.com/mortgage-rates"),
    ("MND Index", "https://www.mortgagenewsdaily.com/mortgage-rates"),
]

# Browser-assisted lenders (anti-bot protected — OpenClaw browser handles these)
BROWSER_ASSISTED = ["Chase", "Rocket Mortgage", "Citi", "LoanDepot", "TD Bank", "Mr. Cooper", "PNC"]


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


async def scrape_all_browser():
    """Scrape all automated sources in parallel."""
    from patchright.async_api import async_playwright

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        tasks = [scrape_lender(browser, name, url) for name, url in BROWSER_SOURCES]
        results = await asyncio.gather(*tasks)
        await browser.close()
    return results


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
        f"MORTGAGE RATE COMPARISON — {today}",
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
            benchmark_tag = "  ·················· benchmark" if is_benchmark else ""
            best_tag = "BEST" if i == 0 and len(product_rates) > 1 and not is_benchmark else ""

            if best_tag:
                prefix = "  \U0001F3C6"  # trophy
                suffix = f"{'':>20s} {best_tag}"
            else:
                prefix = "    "
                suffix = benchmark_tag

            lines.append(f"{prefix} {r['lender']:28s} {rate_str}{apr_str}{suffix}")

        # Day-over-day
        prev = last_rates.get(product, [])
        if prev and product_rates:
            curr_avg = sum(r["rate"] for r in product_rates) / len(product_rates)
            prev_avg = sum(r["rate"] for r in prev) / len(prev)
            diff = curr_avg - prev_avg
            avg_str = f"{curr_avg:.3f}%"
            if abs(diff) >= 0.005:
                arrow = "\u25B2" if diff > 0 else "\u25BC"
                lines.append(f"")
                lines.append(f"  \U0001F4CA Avg: {avg_str}  |  vs yesterday: {arrow} {abs(diff):.3f}%")
            else:
                lines.append(f"")
                lines.append(f"  \U0001F4CA Avg: {avg_str}  |  vs yesterday: unchanged")

        lines.append("")

    # Browser-assisted lenders that need OpenClaw
    script_failures = [f for f in failures if f != "Freddie Mac"]
    needs_browser = BROWSER_ASSISTED + script_failures
    if needs_browser:
        lines.append(f"Need browser check: {', '.join(needs_browser)}")

    return "\n".join(lines)


# ─── MAIN ────────────────────────────────────────────────────────────────────

def main():
    total = len(BROWSER_SOURCES) + 1  # +Freddie Mac API
    print(f"Scraping {total} sources in parallel...\n")

    # Tier 1: Direct API
    fm_name, fm_rates = fetch_freddie_mac_csv()

    # Tier 2: Browser scraping
    browser_results = asyncio.run(scrape_all_browser())

    # Combine
    all_rates = list(fm_rates)
    successes = [fm_name] if fm_rates else []
    failures = [] if fm_rates else [fm_name]

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
