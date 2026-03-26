"""
mortgage_rate_report.py — Multi-lender mortgage rate comparison
Scrapes multiple lender sites in parallel using patchright (stealth Chromium).
Freddie Mac via direct CSV API (no browser needed).

Usage: python3 mortgage_rate_report.py
"""

import asyncio
import json
import os
import re
import ssl
import sys
import urllib.request
from datetime import datetime

ZIP_CODE = "32224"
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
HISTORY_FILE = os.path.join(DATA_DIR, "mortgage_rates_history.json")
WAIT_MS = 10000


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

        # Pattern 3: "rate in XXXXX is X.XXX% (X.XXX% APR)" (Better.com)
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
    """Freddie Mac PMMS — free CSV endpoint."""
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
            results.append({"lender": "Natl Avg (Freddie Mac)", "product": "30yr", "rate": float(last[1]), "apr": None})
        if len(last) >= 4 and last[3]:
            results.append({"lender": "Natl Avg (Freddie Mac)", "product": "15yr", "rate": float(last[3]), "apr": None})
        return "Freddie Mac", results
    except Exception:
        return "Freddie Mac", []


# ─── TIER 2: BROWSER SCRAPING (patchright) ───────────────────────────────────

# These 7 sources are confirmed working with headless patchright
BROWSER_SOURCES = [
    ("Bank of America", "https://promotions.bankofamerica.com/homeloans/homebuying-hub/home-loan-options?subCampCode=41490&dmcode=18099675931"),
    ("Wells Fargo", "https://www.wellsfargo.com/mortgage/rates/"),
    ("Navy Federal CU", "https://www.navyfederal.org/loans-cards/mortgage/mortgage-rates/"),
    ("SoFi", "https://www.sofi.com/home-loans/mortgage-rates/"),
    ("US Bank", "https://www.usbank.com/home-loans/mortgage/mortgage-rates.html"),
    ("Guaranteed Rate", "https://www.rate.com/mortgage-rates"),
    ("MND Index", "https://www.mortgagenewsdaily.com/mortgage-rates"),
]

# LendingTree needs special parsing
LENDINGTREE_URL = "https://www.lendingtree.com/home/mortgage/rates/"

# These lenders block headless browsers — not scrapable without a real browser session
BLOCKED_LENDERS = ["Chase", "Rocket Mortgage", "Citi", "LoanDepot", "PenFed CU", "TD Bank", "Mr. Cooper", "PNC"]


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


async def scrape_lendingtree(browser):
    """Parse LendingTree for averages + FHA/VA rates."""
    try:
        ctx = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            locale="en-US",
        )
        page = await ctx.new_page()
        await page.goto(LENDINGTREE_URL, timeout=15000, wait_until="domcontentloaded")
        await page.wait_for_timeout(WAIT_MS)
        text = await page.inner_text("body")
        await ctx.close()

        results = []
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        for i, line in enumerate(lines):
            for label, product in [
                ("30-year fixed rate", "30yr"), ("15-year fixed rate", "15yr"),
                ("FHA 30-year fixed rate", "FHA 30yr"), ("VA 30-year fixed rate", "VA 30yr"),
            ]:
                if line.lower() == label.lower() and i + 2 < len(lines):
                    rate_m = re.match(r'(\d\.\d{2,3})%', lines[i + 1])
                    apr_m = re.match(r'(\d\.\d{2,3})%', lines[i + 2])
                    if rate_m:
                        results.append({
                            "lender": "LendingTree Avg", "product": product,
                            "rate": float(rate_m.group(1)),
                            "apr": float(apr_m.group(1)) if apr_m else None,
                        })
        return "LendingTree", results
    except Exception:
        try:
            await ctx.close()
        except Exception:
            pass
        return "LendingTree", []


async def scrape_all_browser():
    """Scrape all browser sources in parallel."""
    from patchright.async_api import async_playwright

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)

        tasks = [scrape_lender(browser, name, url) for name, url in BROWSER_SOURCES]
        tasks.append(scrape_lendingtree(browser))
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


# ─── MAIN ────────────────────────────────────────────────────────────────────

def main():
    total = len(BROWSER_SOURCES) + 2  # +Freddie Mac +LendingTree
    print(f"Scraping {total} sources in parallel for ZIP {ZIP_CODE}...\n")

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

    lender_count = len(set(r["lender"] for r in unique))

    # History
    history = load_history()
    last_rates = history[-1].get("rates", {}) if history else {}

    # Report
    today = datetime.now().strftime("%b %d, %Y")
    lines = [
        f"MORTGAGE RATE COMPARISON — {today}",
        f"ZIP {ZIP_CODE} | {lender_count} lenders from {len(successes)} sources",
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
        lines.append(f"--- {label} ---")

        for i, r in enumerate(product_rates):
            rate_str = f"{r['rate']:.3f}%"
            apr_str = f"  (APR {r['apr']:.3f}%)" if r.get("apr") else ""
            tag = " << BEST" if i == 0 and len(product_rates) > 1 else ""
            lines.append(f"  {r['lender']:28s} {rate_str}{apr_str}{tag}")

        prev = last_rates.get(product, [])
        if prev and product_rates:
            curr_avg = sum(r["rate"] for r in product_rates) / len(product_rates)
            prev_avg = sum(r["rate"] for r in prev) / len(prev)
            diff = curr_avg - prev_avg
            if abs(diff) >= 0.005:
                arrow = "UP" if diff > 0 else "DOWN"
                lines.append(f"  vs last: avg {arrow} {abs(diff):.3f}%")

        lines.append("")

    # Show what needs OpenClaw browser
    script_failures = [f for f in failures if f not in ("Freddie Mac",)]
    needs_browser = BLOCKED_LENDERS + script_failures
    if needs_browser:
        lines.append(f"Need browser check: {', '.join(needs_browser)}")

    print("\n".join(lines))

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
