import os
import sys
import tempfile
import unittest
from unittest import mock

import scraper


class PathResolutionTests(unittest.TestCase):
    def test_csv_filename_is_next_to_scraper_script(self):
        ticker = "SPY"
        expected = os.path.join(os.path.dirname(os.path.abspath(scraper.__file__)), f"{ticker}_stock_data.csv")
        self.assertEqual(scraper.get_csv_filename(ticker), expected)

    def test_main_writes_csv_next_to_script_from_other_cwd(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_filename = scraper.get_csv_filename("SPY")
            if os.path.exists(csv_filename):
                os.remove(csv_filename)

            sample_row = {
                "Timestamp": "2026-07-13 15:55:00 EDT",
                "Current Price": 748.22,
                "Ticker": "SPY",
                "Open": 747.7,
                "High": 748.26,
                "Low": 747.56,
                "Close": 748.22,
                "Volume": 0.0,
                "RSI": 44.96,
                "SMA10": 747.59,
                "SMA50": 748.23,
                "SMA200": 750.96,
            }

            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                with mock.patch.object(scraper, "get_stock_data", return_value=sample_row):
                    scraper.main("SPY")
            finally:
                os.chdir(original_cwd)

            self.assertTrue(os.path.exists(csv_filename))
            self.assertFalse(os.path.exists(os.path.join(temp_dir, "SPY_stock_data.csv")))

            if os.path.exists(csv_filename):
                os.remove(csv_filename)


if __name__ == "__main__":
    unittest.main()
