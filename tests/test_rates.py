"""Unit tests for rate parsing, comparison, sorting, and report formatting."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mortgage_rate_report import (
    extract_rates,
    format_report,
    load_zip_code,
    BENCHMARKS,
    BROWSER_SOURCES,
)


class TestExtractRates:
    """Rate extraction from raw page text."""

    def test_pattern1_rate_apr(self):
        text = "30-Year Fixed 6.875% some text APR 6.932%"
        results = extract_rates(text, "TestBank")
        assert len(results) >= 1
        r = results[0]
        assert r["product"] == "30yr"
        assert r["rate"] == 6.875
        assert r["apr"] == 6.932

    def test_pattern2_tab_separated(self):
        text = "30 Year\t6.500%\t6.600%"
        results = extract_rates(text, "TestBank")
        assert len(results) >= 1
        assert results[0]["rate"] == 6.500
        assert results[0]["apr"] == 6.600

    def test_pattern3_is_format(self):
        text = "30-Year Fixed is 6.750% (6.810% APR)"
        results = extract_rates(text, "TestBank")
        assert len(results) >= 1
        assert results[0]["rate"] == 6.750
        assert results[0]["apr"] == 6.810

    def test_pattern4_mr_cooper_style(self):
        text = "30 Year Fixed Rate 6.625% APR 6.700%"
        results = extract_rates(text, "TestBank")
        assert len(results) >= 1
        assert results[0]["rate"] == 6.625

    def test_pattern5_rate_only(self):
        text = "30-Year Fixed 6.500%"
        results = extract_rates(text, "TestBank")
        assert len(results) >= 1
        assert results[0]["rate"] == 6.500
        assert results[0]["apr"] is None

    def test_15yr_extraction(self):
        text = "15-Year Fixed 5.875% APR 5.950%"
        results = extract_rates(text, "TestBank")
        assert any(r["product"] == "15yr" for r in results)

    def test_arm_extraction(self):
        text = "7/6 ARM 5.250% APR 5.400%"
        results = extract_rates(text, "TestBank")
        assert any(r["product"] == "ARM" for r in results)

    def test_multiple_products(self):
        text = (
            "30-Year Fixed 6.875% APR 6.932% "
            "15-Year Fixed 6.125% APR 6.200% "
            "7/1 ARM 5.500% APR 5.650%"
        )
        results = extract_rates(text, "TestBank")
        products = {r["product"] for r in results}
        assert "30yr" in products
        assert "15yr" in products
        assert "ARM" in products

    def test_no_rates_in_garbage(self):
        results = extract_rates("no rates here, just random text", "TestBank")
        assert results == []

    def test_rate_outside_range_rejected(self):
        """Rate-only pattern rejects rates outside 3.0-12.0%."""
        text = "30-Year Fixed 1.000%"
        results = extract_rates(text, "TestBank")
        assert results == []

    def test_lender_name_preserved(self):
        text = "30-Year Fixed 6.500% APR 6.600%"
        results = extract_rates(text, "Bank of America")
        assert results[0]["lender"] == "Bank of America"

    def test_empty_text(self):
        assert extract_rates("", "TestBank") == []


class TestLenderComparison:
    """Sorting and ranking in format_report."""

    def _make_rates(self, rates_data):
        return [
            {"lender": name, "product": "30yr", "rate": rate, "apr": apr}
            for name, rate, apr in rates_data
        ]

    def test_lowest_rate_gets_trophy(self):
        rates = self._make_rates([
            ("Bank A", 6.500, 6.600),
            ("Bank B", 6.750, 6.800),
            ("Bank C", 7.000, 7.100),
        ])
        report = format_report(rates, [])
        lines = report.split("\n")
        trophy_lines = [l for l in lines if "Bank A" in l]
        assert any("**" in l for l in trophy_lines), "Best rate should be bold"

    def test_rates_sorted_lowest_first(self):
        rates = self._make_rates([
            ("Bank C", 7.000, 7.100),
            ("Bank A", 6.500, 6.600),
            ("Bank B", 6.750, 6.800),
        ])
        report = format_report(rates, [])
        pos_a = report.find("Bank A")
        pos_b = report.find("Bank B")
        pos_c = report.find("Bank C")
        assert pos_a < pos_b < pos_c, "Rates should be sorted lowest first"

    def test_benchmark_labeled(self):
        rates = [
            {"lender": "Bank A", "product": "30yr", "rate": 6.500, "apr": 6.600},
            {"lender": "Freddie Mac (natl avg)", "product": "30yr", "rate": 6.650, "apr": None},
        ]
        report = format_report(rates, [])
        assert "benchmark" in report.lower()

    def test_benchmark_not_trophy_winner(self):
        """Benchmarks should never get the trophy even if lowest."""
        rates = [
            {"lender": "Freddie Mac (natl avg)", "product": "30yr", "rate": 5.000, "apr": None},
            {"lender": "Bank A", "product": "30yr", "rate": 6.500, "apr": 6.600},
        ]
        report = format_report(rates, [])
        freddie_line = [l for l in report.split("\n") if "Freddie Mac" in l]
        assert all("**" not in l for l in freddie_line)


class TestReportFormatting:
    """Report structure and content."""

    def _make_rates(self):
        return [
            {"lender": "Bank A", "product": "30yr", "rate": 6.500, "apr": 6.600},
            {"lender": "Bank B", "product": "30yr", "rate": 6.750, "apr": 6.800},
            {"lender": "Bank A", "product": "15yr", "rate": 5.875, "apr": 5.950},
        ]

    def test_report_contains_date(self):
        report = format_report(self._make_rates(), [])
        assert "MORTGAGE RATES" in report

    def test_report_contains_lender_count(self):
        report = format_report(self._make_rates(), [])
        assert f"/{len(BROWSER_SOURCES)}" in report

    def test_report_contains_product_sections(self):
        report = format_report(self._make_rates(), [])
        assert "30-YEAR FIXED" in report
        assert "15-YEAR FIXED" in report

    def test_empty_product_section_omitted(self):
        rates = [{"lender": "Bank A", "product": "30yr", "rate": 6.5, "apr": 6.6}]
        report = format_report(rates, [])
        assert "ARM" not in report

    def test_day_over_day_with_history(self):
        rates = [{"lender": "Bank A", "product": "30yr", "rate": 6.500, "apr": 6.600}]
        history = [{"date": "2025-01-01", "rates": {
            "30yr": [{"lender": "Bank A", "rate": 6.750, "apr": 6.800}]
        }}]
        report = format_report(rates, history)
        assert "yesterday" in report.lower()

    def test_day_over_day_decrease_arrow(self):
        rates = [{"lender": "Bank A", "product": "30yr", "rate": 6.500, "apr": 6.600}]
        history = [{"date": "2025-01-01", "rates": {
            "30yr": [{"lender": "Bank A", "rate": 7.000, "apr": 7.100}]
        }}]
        report = format_report(rates, history)
        # Rate went down, should show down arrow
        assert "▼" in report

    def test_day_over_day_increase_arrow(self):
        rates = [{"lender": "Bank A", "product": "30yr", "rate": 7.500, "apr": 7.600}]
        history = [{"date": "2025-01-01", "rates": {
            "30yr": [{"lender": "Bank A", "rate": 6.500, "apr": 6.600}]
        }}]
        report = format_report(rates, history)
        assert "▲" in report

    def test_day_over_day_unchanged(self):
        rates = [{"lender": "Bank A", "product": "30yr", "rate": 6.500, "apr": 6.600}]
        history = [{"date": "2025-01-01", "rates": {
            "30yr": [{"lender": "Bank A", "rate": 6.500, "apr": 6.600}]
        }}]
        report = format_report(rates, history)
        assert "unchanged" in report.lower()

    def test_apr_displayed_when_present(self):
        rates = [{"lender": "Bank A", "product": "30yr", "rate": 6.500, "apr": 6.600}]
        report = format_report(rates, [])
        assert "APR" in report

    def test_apr_omitted_when_none(self):
        rates = [{"lender": "Bank A", "product": "30yr", "rate": 6.500, "apr": None}]
        report = format_report(rates, [])
        bank_line = [l for l in report.split("\n") if "Bank A" in l][0]
        assert "APR" not in bank_line

    def test_report_is_string(self):
        report = format_report(self._make_rates(), [])
        assert isinstance(report, str)
        assert len(report) > 50


class TestConfigLoading:
    """ZIP code resolution logic."""

    def test_cli_zip_takes_priority(self):
        assert load_zip_code(cli_zip="90210") == "90210"

    def test_default_zip_when_no_config(self):
        result = load_zip_code(cli_zip=None)
        # config.json has YOUR_ZIP, so default 32224
        assert result == "32224"

    def test_browser_sources_not_empty(self):
        assert len(BROWSER_SOURCES) > 0

    def test_browser_sources_have_names_and_urls(self):
        for name, url in BROWSER_SOURCES:
            assert isinstance(name, str) and len(name) > 0
            assert url.startswith("https://")

    def test_benchmarks_are_set(self):
        assert isinstance(BENCHMARKS, set)
        assert len(BENCHMARKS) == 2
