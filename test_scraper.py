import sys
import types
import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

sys.modules.setdefault("pandas", types.SimpleNamespace())
sys.modules.setdefault("yfinance", types.SimpleNamespace())

import scraper


class TimestampConversionTest(unittest.TestCase):
    def test_preserves_timezone_aware_eastern_timestamp(self):
        timestamp = datetime(2026, 6, 24, 16, 0, tzinfo=ZoneInfo("America/New_York"))

        self.assertEqual(scraper.get_est_timestamp(timestamp), "2026-06-24 16:00:00 EDT")

    def test_treats_naive_timestamp_as_utc(self):
        timestamp = datetime(2026, 6, 24, 16, 0)

        self.assertEqual(scraper.get_est_timestamp(timestamp), "2026-06-24 12:00:00 EDT")


if __name__ == "__main__":
    unittest.main()
