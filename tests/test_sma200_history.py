import unittest
from datetime import datetime

import pandas as pd
import pytz

import scraper


def _make_price_frame(bar_count: int) -> pd.DataFrame:
    eastern = pytz.timezone("US/Eastern")
    start = eastern.localize(datetime(2026, 8, 1, 9, 30))
    timestamps = pd.date_range(start=start, periods=bar_count, freq="5min")
    closes = pd.Series(range(100, 100 + bar_count), index=timestamps, dtype=float)
    return pd.DataFrame(
        {
            "Open": closes,
            "High": closes + 0.5,
            "Low": closes - 0.5,
            "Close": closes,
            "Volume": 1_000,
        },
        index=timestamps,
    )


class Sma200HistoryTest(unittest.TestCase):
    def test_two_day_history_is_insufficient_for_sma200(self):
        data = _make_price_frame(199)
        sma200 = scraper.calculate_sma(data, window=scraper.SMA200_WINDOW)
        self.assertTrue(pd.isna(sma200.iloc[-1]))

    def test_extended_history_produces_valid_sma200(self):
        data = _make_price_frame(250)
        sma200 = scraper.calculate_sma(data, window=scraper.SMA200_WINDOW)
        self.assertFalse(pd.isna(sma200.iloc[-1]))

    def test_lookback_period_covers_sma200_window(self):
        # 60 days of 5-minute bars is well above the 200 bars SMA200 requires.
        self.assertEqual(scraper.LOOKBACK_PERIOD, "60d")
        self.assertGreaterEqual(scraper.SMA200_WINDOW, 200)


if __name__ == "__main__":
    unittest.main()
