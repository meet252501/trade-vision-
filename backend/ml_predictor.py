import os
import sys
import json
import warnings
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dotenv import load_dotenv
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data.enums import DataFeed
from sklearn.ensemble import RandomForestClassifier

warnings.filterwarnings('ignore')
load_dotenv()

API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

def compute_rsi(data, window=14):
    diff = data.diff(1)
    gain = diff.where(diff > 0, 0.0)
    loss = -diff.where(diff < 0, 0.0)
    avg_gain = gain.rolling(window=window, min_periods=1).mean()
    avg_loss = loss.rolling(window=window, min_periods=1).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def run_ml(ticker):
    try:
        client = StockHistoricalDataClient(API_KEY, SECRET_KEY)
        req = StockBarsRequest(
            symbol_or_symbols=ticker,
            timeframe=TimeFrame.Day,
            start=datetime.now() - timedelta(days=365),
            end=datetime.now(),
            feed=DataFeed.IEX
        )
        bars = client.get_stock_bars(req)
        
        if bars.df.empty:
            print(json.dumps({"error": "No data"}))
            return
            
        df = bars.df.reset_index()
        if 'symbol' in df.columns:
            df = df[df['symbol'] == ticker]
            
        # Feature Engineering
        df['SMA_20'] = df['close'].rolling(window=20).mean()
        df['SMA_50'] = df['close'].rolling(window=50).mean()
        df['RSI'] = compute_rsi(df['close'], 14)
        
        # Target: 1 if next day goes UP, 0 if DOWN
        df['Target'] = (df['close'].shift(-1) > df['close']).astype(int)
        
        df = df.dropna()
        
        if len(df) < 50:
            print(json.dumps({"error": "Not enough data for ML"}))
            return
            
        features = ['close', 'SMA_20', 'SMA_50', 'RSI']
        X = df[features]
        y = df['Target']
        
        # Train Random Forest
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X[:-1], y[:-1]) # Train on all but the last day
        
        # Predict the latest day
        latest_features = X.iloc[-1:]
        prob = model.predict_proba(latest_features)[0]
        prediction = int(model.predict(latest_features)[0])
        
        # Generate Historical Markers for the Chart
        # We will backtest the model on the last 30 days to generate visual BUY/SELL markers
        markers = []
        recent_df = df.tail(30)
        for idx, row in recent_df.iterrows():
            f = pd.DataFrame([row[features]], columns=features)
            pred = model.predict(f)[0]
            date_str = row['timestamp'].strftime('%Y-%m-%d')
            if pred == 1:
                markers.append({
                    "time": date_str,
                    "position": "belowBar",
                    "color": "#22c55e",
                    "shape": "arrowUp",
                    "text": "ML BUY"
                })
            else:
                markers.append({
                    "time": date_str,
                    "position": "aboveBar",
                    "color": "#ef4444",
                    "shape": "arrowDown",
                    "text": "ML SELL"
                })

        output = {
            "ticker": ticker,
            "prediction": "UP" if prediction == 1 else "DOWN",
            "probability_up": float(prob[1]),
            "probability_down": float(prob[0]),
            "markers": markers
        }
        
        print(json.dumps(output))
        
    except Exception as e:
        print(json.dumps({"error": str(e)}))

if __name__ == "__main__":
    ticker = sys.argv[1] if len(sys.argv) > 1 else "SPY"
    run_ml(ticker)
