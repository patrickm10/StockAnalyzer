"""Tests for scraper column handling (yfinance MultiIndex → flat OHLCV)."""
import unittest
import pandas as pd

import scraper


class FlattenPriceColumnsTest(unittest.TestCase):
    def test_flattens_multiindex_single_ticker(self):
        idx = pd.date_range("2026-01-01", periods=2, freq="5min", tz="UTC")
        multi = pd.MultiIndex.from_tuples(
            [("Close", "SPY"), ("Open", "SPY"), ("High", "SPY"), ("Low", "SPY"), ("Volume", "SPY")],
            names=["Price", "Ticker"],
        )
        data = pd.DataFrame(
            [[1.0, 1.0, 1.0, 1.0, 100], [2.0, 2.0, 2.0, 2.0, 200]],
            index=idx,
            columns=multi,
        )
        flat = scraper._flatten_price_columns(data)
        self.assertListEqual(list(flat.columns), ["Close", "Open", "High", "Low", "Volume"])

    def test_leaves_simple_columns_unchanged(self):
        data = pd.DataFrame({"Close": [1.0], "Open": [1.0]})
        flat = scraper._flatten_price_columns(data)
        pd.testing.assert_frame_equal(flat, data)


if __name__ == "__main__":
    unittest.main()
