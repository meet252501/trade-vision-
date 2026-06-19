import os
import json
import datetime
from dotenv import load_dotenv
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetPortfolioHistoryRequest

load_dotenv()

API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
PAPER = os.getenv("ALPACA_PAPER", "True") == "True"

def get_status():
    if not API_KEY or not SECRET_KEY:
        return {"error": "Missing Alpaca API keys in .env file"}
        
    try:
        client = TradingClient(API_KEY, SECRET_KEY, paper=PAPER)
        account = client.get_account()
        positions = client.get_all_positions()
        
        equity = float(account.equity)
        total_pnl = sum(float(p.unrealized_pl) for p in positions)
        
        # Fetch intraday portfolio history for the live graph
        req = GetPortfolioHistoryRequest(period="1D", timeframe="5Min")
        history = client.get_portfolio_history(req)
        equity_curve = []
        for ts, eq in zip(history.timestamp, history.equity):
            dt = datetime.datetime.fromtimestamp(ts)
            equity_curve.append({
                "time": dt.strftime("%H:%M"),
                "equity": float(eq) if eq is not None else 0
            })
        
        pos_data = []
        for p in positions:
            pos_data.append({
                "ticker": p.symbol,
                "qty": float(p.qty),
                "market_value": float(p.market_value),
                "unrealized_pl": float(p.unrealized_pl),
                "unrealized_plpc": float(p.unrealized_plpc)
            })
            
        return {
            "equity": equity,
            "cash": float(account.cash),
            "buying_power": float(account.buying_power),
            "total_unrealized_pnl": total_pnl,
            "total_profit_since_inception": equity - 100000.0, # Baseline for paper trading is 100k
            "equity_curve": equity_curve,
            "positions": pos_data
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    print(json.dumps(get_status()))
