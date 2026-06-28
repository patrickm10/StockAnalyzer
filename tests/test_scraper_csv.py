import csv
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRAPER_PATH = REPO_ROOT / 'scraper.py'


def load_scraper_module():
    sys.modules.setdefault('yfinance', types.SimpleNamespace(download=None))
    sys.modules.setdefault('pandas', types.SimpleNamespace())
    sys.modules.setdefault('pytz', types.SimpleNamespace(timezone=lambda name: None))

    spec = importlib.util.spec_from_file_location('scraper', SCRAPER_PATH)
    scraper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(scraper)
    return scraper


class ScraperCsvTests(unittest.TestCase):
    def setUp(self):
        self.scraper = load_scraper_module()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.previous_cwd = os.getcwd()
        os.chdir(self.temp_dir.name)
        self.addCleanup(lambda: os.chdir(self.previous_cwd))

    def stock_row(self, timestamp):
        return {
            'Timestamp': timestamp,
            'Current Price': 609.42,
            'Ticker': 'SPY',
            'Open': 609.0,
            'High': 610.0,
            'Low': 608.0,
            'Close': 609.42,
            'Volume': 1000,
            'RSI': 55.5,
            'SMA10': 608.1,
            'SMA50': 607.2,
            'SMA200': 600.3,
        }

    def read_rows(self):
        with open('SPY_stock_data.csv', newline='') as file:
            return list(csv.DictReader(file))

    def test_duplicate_latest_timestamp_is_not_appended(self):
        with patch.object(self.scraper, 'get_stock_data', return_value=self.stock_row('2025-02-14 08:15:00 EST')):
            self.scraper.main('SPY')
            self.scraper.main('SPY')

        rows = self.read_rows()
        self.assertEqual(1, len(rows))
        self.assertEqual('2025-02-14 08:15:00 EST', rows[0]['Timestamp'])

    def test_new_timestamp_is_appended(self):
        rows_to_return = [
            self.stock_row('2025-02-14 08:15:00 EST'),
            self.stock_row('2025-02-14 08:20:00 EST'),
        ]

        with patch.object(self.scraper, 'get_stock_data', side_effect=rows_to_return):
            self.scraper.main('SPY')
            self.scraper.main('SPY')

        rows = self.read_rows()
        self.assertEqual(2, len(rows))
        self.assertEqual('2025-02-14 08:15:00 EST', rows[0]['Timestamp'])
        self.assertEqual('2025-02-14 08:20:00 EST', rows[1]['Timestamp'])


if __name__ == '__main__':
    unittest.main()
