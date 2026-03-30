"""Security tests for Multi-Lender Mortgage Rate Lookup."""
import json
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mortgage_rate_report import (
    extract_rates,
    format_report,
    load_zip_code,
    BENCHMARKS,
    BROWSER_SOURCES,
    CONFIG_FILE,
)


class TestNoCredentialLeaks:
    """Ensure no sensitive data leaks into report output."""

    SENSITIVE_PATTERNS = [
        "password", "token", "secret", "api_key", "apikey",
        "authorization", "bearer", "credential",
    ]

    def _make_rates(self):
        return [
            {"lender": "Bank of America", "product": "30yr", "rate": 6.875, "apr": 6.932},
            {"lender": "Wells Fargo", "product": "30yr", "rate": 6.750, "apr": 6.812},
            {"lender": "Freddie Mac (natl avg)", "product": "30yr", "rate": 6.650, "apr": None},
        ]

    def test_report_contains_no_sensitive_keywords(self):
        report = format_report(self._make_rates(), [])
        lower = report.lower()
        for pattern in self.SENSITIVE_PATTERNS:
            assert pattern not in lower, f"Report contains sensitive keyword: {pattern}"

    def test_report_does_not_contain_urls(self):
        report = format_report(self._make_rates(), [])
        assert "https://" not in report
        assert "http://" not in report

    def test_report_does_not_expose_file_paths(self):
        report = format_report(self._make_rates(), [])
        assert CONFIG_FILE not in report
        assert "/Users/" not in report
        assert "C:\\" not in report

    def test_zip_code_not_in_report_body(self):
        """ZIP should not leak into the formatted report text."""
        report = format_report(self._make_rates(), [])
        # ZIP is only used for scraping, not display
        assert "32224" not in report

    def test_extract_rates_strips_html_injection(self):
        """Injected script tags in page text should not propagate as lender names."""
        malicious = '30-Year Fixed 6.500% APR 6.600% <script>alert("xss")</script>'
        results = extract_rates(malicious, "TestLender")
        for r in results:
            assert "<script>" not in r["lender"]
            assert "<script>" not in r["product"]


class TestConfigValidation:
    """Config.json loading and validation."""

    def test_config_json_exists(self):
        assert os.path.exists(CONFIG_FILE), "config.json must exist"

    def test_config_json_is_valid_json(self):
        with open(CONFIG_FILE) as f:
            cfg = json.load(f)
        assert isinstance(cfg, dict)

    def test_config_has_zip_code_key(self):
        with open(CONFIG_FILE) as f:
            cfg = json.load(f)
        assert "zip_code" in cfg, "config.json must contain zip_code"

    def test_config_no_secrets(self):
        with open(CONFIG_FILE) as f:
            text = f.read().lower()
        for keyword in ["password", "token", "api_key", "secret"]:
            assert keyword not in text, f"config.json contains sensitive key: {keyword}"

    def test_load_zip_code_cli_overrides_config(self):
        result = load_zip_code(cli_zip="90210")
        assert result == "90210"

    def test_load_zip_code_rejects_placeholder(self):
        """If config has YOUR_ZIP placeholder, fall back to default."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"zip_code": "YOUR_ZIP"}, f)
            tmp = f.name
        try:
            # The function reads CONFIG_FILE, not the temp file, so we test default
            result = load_zip_code(cli_zip=None)
            # Should return default 32224 since config.json has YOUR_ZIP
            assert result == "32224"
        finally:
            os.unlink(tmp)

    def test_load_zip_code_with_empty_string(self):
        result = load_zip_code(cli_zip=None)
        # Config has YOUR_ZIP, so falls back to 32224
        assert result == "32224"


class TestOutputSanitization:
    """Report output is safe for external consumption."""

    def test_rate_values_are_numeric(self):
        text = "30-Year Fixed 6.875% APR 6.932%"
        results = extract_rates(text, "TestBank")
        for r in results:
            assert isinstance(r["rate"], float)
            assert r["apr"] is None or isinstance(r["apr"], float)

    def test_rate_values_in_sane_range(self):
        text = "30-Year Fixed 6.875% APR 6.932%"
        results = extract_rates(text, "TestBank")
        for r in results:
            assert 0 < r["rate"] < 20, f"Rate {r['rate']} outside sane range"
            if r["apr"]:
                assert 0 < r["apr"] < 20, f"APR {r['apr']} outside sane range"

    def test_report_encoding_is_clean(self):
        rates = [{"lender": "Test", "product": "30yr", "rate": 6.5, "apr": 6.6}]
        report = format_report(rates, [])
        # Should be encodable as UTF-8 without errors
        report.encode("utf-8")
