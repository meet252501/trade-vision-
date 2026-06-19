import os
import sys
import json
import warnings
from datetime import datetime, timedelta
from dotenv import load_dotenv
from alpaca.data.historical import StockHistoricalDataClient, CryptoHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, CryptoBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from alpaca.data.enums import DataFeed

warnings.filterwarnings('ignore')
load_dotenv()

API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

def fetch_candles(ticker, timeframe_str="1D"):
    try:
        is_crypto = '/USD' in ticker
        
        # Decide timeframe and lookback
        if timeframe_str == "15Min":
            tf = TimeFrame(15, TimeFrameUnit.Minute)
            lookback_days = 7
        elif timeframe_str == "1Min":
            tf = TimeFrame.Minute
            lookback_days = 2
        else:
            tf = TimeFrame.Day
            lookback_days = 100
            
        if is_crypto:
            client = CryptoHistoricalDataClient(API_KEY, SECRET_KEY)
            req = CryptoBarsRequest(
                symbol_or_symbols=ticker,
                timeframe=tf,
                start=datetime.now() - timedelta(days=lookback_days),
                end=datetime.now()
            )
            bars = client.get_crypto_bars(req)
        else:
            client = StockHistoricalDataClient(API_KEY, SECRET_KEY)
            req = StockBarsRequest(
                symbol_or_symbols=ticker,
                timeframe=tf,
                start=datetime.now() - timedelta(days=lookback_days),
                end=datetime.now(),
                feed=DataFeed.IEX
            )
            bars = client.get_stock_bars(req)
        
        if bars.df.empty:
            print(json.dumps([]))
            return
            
        df = bars.df.reset_index()
        if 'symbol' in df.columns:
            df = df[df['symbol'] == ticker]
            
        candles = []
        for idx, row in df.iterrows():
            # Crucial: Lightweight charts requires UNIX timestamp (in seconds) for intraday data
            candles.append({
                "time": int(row['timestamp'].timestamp()),
                "open": float(row['open']),
                "high": float(row['high']),
                "low": float(row['low']),
                "close": float(row['close'])
            })
            
        print(json.dumps(candles))
        
    except Exception as e:
        print(json.dumps({"error": str(e)}))

if __name__ == "__main__":
    ticker = sys.argv[1] if len(sys.argv) > 1 else "SPY"
    # Default to 15Min intraday for the charts to make them highly usable and active
    tf = sys.argv[2] if len(sys.argv) > 2 else "15Min" 
    fetch_candles(ticker, tf)
