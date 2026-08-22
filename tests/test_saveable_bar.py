import importlib.util
import sys
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock

import pandas as pd
import pytz

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import scraper


def _make_bar_frame():
    eastern = pytz.timezone("US/Eastern")
    timestamps = [
        eastern.localize(datetime(2026, 8, 21, 10, 0)),
        eastern.localize(datetime(2026, 8, 21, 10, 5)),
        eastern.localize(datetime(2026, 8, 21, 10, 10)),
    ]
    return pd.DataFrame(
        {
            "Open": [100.0, 101.0, 102.0],
            "High": [100.5, 101.5, 102.5],
            "Low": [99.5, 100.5, 101.5],
            "Close": [100.2, 101.2, 102.2],
            "Volume": [1000, 1100, 1200],
        },
        index=pd.DatetimeIndex(timestamps),
    )


class GetSaveableRowTest(unittest.TestCase):
    def test_uses_previous_bar_while_latest_interval_is_still_forming(self):
        data = _make_bar_frame()
        now = data.index[-1] + pd.Timedelta(minutes=2)

        row = scraper.get_saveable_row(data, now=now)

        self.assertEqual(row.name, data.index[-2])
        self.assertEqual(row["Close"], 101.2)

    def test_uses_latest_bar_once_interval_has_completed(self):
        data = _make_bar_frame()
        now = data.index[-1] + pd.Timedelta(minutes=5)

        row = scraper.get_saveable_row(data, now=now)

        self.assertEqual(row.name, data.index[-1])
        self.assertEqual(row["Close"], 102.2)

    def test_returns_none_when_only_in_progress_bar_exists(self):
        data = _make_bar_frame().iloc[[-1]]
        now = data.index[-1] + pd.Timedelta(minutes=1)

        self.assertIsNone(scraper.get_saveable_row(data, now=now))


class MainDedupTest(unittest.TestCase):
    def test_skips_already_saved_completed_bar(self):
        saved = {
            "Timestamp": "2026-08-21 10:05:00 EDT",
            "Current Price": 101.2,
            "Ticker": "SPY",
            "Open": 101.0,
            "High": 101.5,
            "Low": 100.5,
            "Close": 101.2,
            "Volume": 1100,
            "RSI": 50.0,
            "SMA10": 100.0,
            "SMA50": 99.0,
            "SMA200": 98.0,
        }

        with mock.patch.object(scraper, "get_stock_data", return_value=saved), mock.patch.object(
            scraper,
            "get_latest_record_key",
            return_value=(saved["Timestamp"], saved["Ticker"]),
        ), mock.patch("builtins.open", mock.mock_open()) as mocked_open:
            scraper.main("SPY")

        mocked_open.assert_not_called()


if __name__ == "__main__":
    unittest.main()
