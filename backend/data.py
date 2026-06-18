"""
data.py — Price Data Fetcher
=============================
Fetches OHLCV price data using yfinance.
Provides both date-range and period-based fetching.
"""

import yfinance as yf
import pandas as pd


def fetch_prices(tickers: list, start: str = None,
                 end: str = None, period: str = '1y') -> dict:
    """
    Fetch OHLCV price data for a list of tickers.
    
    Args:
        tickers: List of ticker symbols
        start: Start date string (YYYY-MM-DD)
        end: End date string (YYYY-MM-DD)
        period: yfinance period string (e.g. '1y', '6mo', '3mo')
    
    Returns:
        dict of {ticker: list of bar dicts} where each bar has
        keys: ts, open, high, low, close, volume
    """
    result = {}
    for ticker in tickers:
        try:
            if start and end:
                df = yf.download(ticker, start=start, end=end,
                                 auto_adjust=True, progress=False)
            else:
                df = yf.download(ticker, period=period,
                                 auto_adjust=True, progress=False)
            
            if df.empty:
                continue

            # Flatten multi-level columns if present
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            bars = []
            for ts, row in df.iterrows():
                bars.append({
                    'ts':     str(ts.date()),
                    'open':   round(float(row['Open']), 2),
                    'high':   round(float(row['High']), 2),
                    'low':    round(float(row['Low']),  2),
                    'close':  round(float(row['Close']), 2),
                    'volume': int(row['Volume']),
                })
            result[ticker] = bars
        except Exception as e:
            result[ticker] = {'error': str(e)}
    return result


def fetch_prices_as_df(tickers: list, start: str, end: str) -> dict:
    """
    Fetch prices and return as pandas DataFrames (for backtesting).
    
    Returns:
        dict of {ticker: DataFrame with OHLCV columns}
    """
    result = {}
    for ticker in tickers:
        try:
            df = yf.download(ticker, start=start, end=end,
                             auto_adjust=True, progress=False)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            if not df.empty:
                result[ticker] = df
        except Exception:
            pass
    return result
