#!/usr/bin/env python3
"""
Mortgage Rate Tracker with Historical Logging
Tracks daily mortgage rates and shows trends over time
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import os
import sys

class MortgageRateTracker:
    def __init__(self, config_file="config.json", history_file="rates_history.json"):
        # Load configuration
        with open(config_file, 'r') as f:
            self.config = json.load(f)

        self.zip_code = self.config['zip_code']
        self.history_file = history_file
        self.history = self._load_history()

    def _load_history(self):
        """Load historical rate data"""
        if os.path.exists(self.history_file):
            with open(self.history_file, 'r') as f:
                return json.load(f)
        return {"rates": []}

    def _save_history(self):
        """Save historical rate data"""
        with open(self.history_file, 'w') as f:
            json.dump(self.history, f, indent=2)

    def fetch_chase_rates(self):
        """Fetch current mortgage rates from Chase"""
        url = f"https://www.chase.com/personal/mortgage/mortgage-rates"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
        }

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # Note: Chase's exact HTML structure may vary
            # This is a template - may need adjustment based on actual page structure
            rates = {}

            # Try to find rate tables
            rate_tables = soup.find_all('table', class_='rate-table')

            for table in rate_tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        product = cells[0].get_text().strip()
                        rate = cells[1].get_text().strip()

                        if '30' in product and 'year' in product.lower():
                            rates['30_year_rate'] = rate
                        elif '15' in product and 'year' in product.lower():
                            rates['15_year_rate'] = rate

            return rates if rates else None

        except Exception as e:
            print(f"⚠️  Error fetching Chase rates: {str(e)}")
            return None

    def fetch_bankrate_api(self):
        """Fetch rates from Bankrate API (more reliable)"""
        url = f"https://www.bankrate.com/funnel/mortgages/api/mortgage-rates/?zipCode={self.zip_code}"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            rates = {}

            # Parse Bankrate data structure
            if 'rates' in data:
                for rate_info in data['rates']:
                    term = rate_info.get('term', '')
                    rate = rate_info.get('rate', '')
                    apr = rate_info.get('apr', '')

                    if '30' in str(term):
                        rates['30_year_rate'] = rate
                        rates['30_year_apr'] = apr
                    elif '15' in str(term):
                        rates['15_year_rate'] = rate
                        rates['15_year_apr'] = apr

            return rates if rates else None

        except Exception as e:
            print(f"⚠️  Error fetching Bankrate data: {str(e)}")
            return None

    def fetch_current_rates(self):
        """Fetch current rates from available sources"""
        print(f"🔍 Fetching current mortgage rates for ZIP {self.zip_code}...")

        # Try Bankrate API first (more reliable)
        rates = self.fetch_bankrate_api()

        # If Bankrate fails, try Chase
        if not rates:
            print("   Trying Chase as fallback...")
            rates = self.fetch_chase_rates()

        if not rates:
            print("❌ Unable to fetch rates from any source")
            return None

        return rates

    def log_rate(self, rates):
        """Log today's rate to history"""
        today = datetime.now().strftime('%Y-%m-%d')

        # Check if we already have today's rate
        for entry in self.history['rates']:
            if entry['date'] == today:
                print(f"ℹ️  Rate already logged for {today}")
                return False

        # Add new rate entry
        rate_entry = {
            'date': today,
            'timestamp': datetime.now().isoformat(),
            'zip_code': self.zip_code,
            **rates
        }

        self.history['rates'].append(rate_entry)
        self._save_history()

        print(f"✅ Logged rates for {today}")
        return True

    def get_rate_change(self):
        """Calculate rate change from yesterday"""
        if len(self.history['rates']) < 2:
            return None

        # Sort by date (most recent first)
        sorted_rates = sorted(self.history['rates'], key=lambda x: x['date'], reverse=True)

        today_rate = sorted_rates[0]
        yesterday_rate = sorted_rates[1]

        # Calculate change for 30-year rate
        today_30yr = float(today_rate.get('30_year_rate', 0))
        yesterday_30yr = float(yesterday_rate.get('30_year_rate', 0))

        change = today_30yr - yesterday_30yr

        return {
            'today': today_rate,
            'yesterday': yesterday_rate,
            'change': change,
            'change_percent': (change / yesterday_30yr * 100) if yesterday_30yr > 0 else 0
        }

    def display_report(self):
        """Display current rates and comparison"""
        if not self.history['rates']:
            print("📊 No rate history found. Run the tracker to log your first rate!")
            return

        # Get most recent rate
        latest = sorted(self.history['rates'], key=lambda x: x['date'], reverse=True)[0]

        print("\n" + "=" * 80)
        print(f"📈 MORTGAGE RATE REPORT - ZIP {self.zip_code}")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %I:%M %p')}")
        print("=" * 80 + "\n")

        # Current rates
        print("💰 CURRENT RATES")
        print("-" * 80)
        if '30_year_rate' in latest:
            print(f"30-Year Fixed: {latest['30_year_rate']}%", end="")
            if '30_year_apr' in latest:
                print(f" (APR: {latest['30_year_apr']}%)")
            else:
                print()

        if '15_year_rate' in latest:
            print(f"15-Year Fixed: {latest['15_year_rate']}%", end="")
            if '15_year_apr' in latest:
                print(f" (APR: {latest['15_year_apr']}%)")
            else:
                print()

        print()

        # Day-to-day comparison
        if len(self.history['rates']) >= 2:
            change_data = self.get_rate_change()

            print("📊 DAY-TO-DAY COMPARISON")
            print("-" * 80)

            change = change_data['change']
            change_pct = change_data['change_percent']

            if change > 0:
                print(f"📈 INCREASED: +{change:.3f}% ({change_pct:+.2f}%)")
                print(f"   Yesterday: {change_data['yesterday']['30_year_rate']}%")
                print(f"   Today: {change_data['today']['30_year_rate']}%")
            elif change < 0:
                print(f"📉 DECREASED: {change:.3f}% ({change_pct:+.2f}%)")
                print(f"   Yesterday: {change_data['yesterday']['30_year_rate']}%")
                print(f"   Today: {change_data['today']['30_year_rate']}%")
            else:
                print(f"➡️  NO CHANGE: {change_data['today']['30_year_rate']}%")

            print()

        # Historical trend
        if len(self.history['rates']) >= 7:
            print("📉 7-DAY TREND")
            print("-" * 80)

            recent_7 = sorted(self.history['rates'], key=lambda x: x['date'], reverse=True)[:7]

            for entry in reversed(recent_7):
                rate = entry.get('30_year_rate', 'N/A')
                print(f"{entry['date']}: {rate}%")

            # Calculate 7-day change
            oldest_7 = recent_7[-1]
            newest_7 = recent_7[0]

            old_rate = float(oldest_7.get('30_year_rate', 0))
            new_rate = float(newest_7.get('30_year_rate', 0))
            week_change = new_rate - old_rate

            print(f"\n7-Day Change: {week_change:+.3f}%")
            print()

        print("=" * 80)
        print(f"📊 Total logged entries: {len(self.history['rates'])}")
        print("=" * 80 + "\n")

def main():
    tracker = MortgageRateTracker()

    # Fetch current rates
    rates = tracker.fetch_current_rates()

    if rates:
        # Log the rate
        tracker.log_rate(rates)

        # Display report
        tracker.display_report()
    else:
        print("\n⚠️  Unable to fetch current rates. Displaying last known data:\n")
        tracker.display_report()

if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print("   Make sure config.json exists in the same directory.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)
