"""
TradeVision AI — trade_history.py
Fetches all recent orders from Alpaca and computes per-trade P/L.
Returns JSON array of trades with status, fill price, P/L, etc.
"""
import json
import sys
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

load_dotenv()

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetOrdersRequest
from alpaca.trading.enums import QueryOrderStatus

API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

try:
    client = TradingClient(API_KEY, SECRET_KEY, paper=True)
    
    req = GetOrdersRequest(
        status=QueryOrderStatus.ALL,
        limit=50,
        after=datetime.now() - timedelta(days=30)
    )
    orders = client.get_orders(req)
    
    trades = []
    for o in orders:
        filled_price = float(o.filled_avg_price) if o.filled_avg_price else None
        filled_qty = int(o.filled_qty) if o.filled_qty else 0
        
        trade = {
            "id": str(o.id)[:8],
            "symbol": o.symbol,
            "side": str(o.side).split(".")[-1].upper(),
            "qty": int(o.qty) if o.qty else 0,
            "filled_qty": filled_qty,
            "type": str(o.type).split(".")[-1],
            "status": str(o.status).split(".")[-1].lower(),
            "limit_price": float(o.limit_price) if o.limit_price else None,
            "filled_price": filled_price,
            "submitted_at": o.submitted_at.isoformat() if o.submitted_at else None,
            "filled_at": o.filled_at.isoformat() if o.filled_at else None,
            "notional": round(filled_price * filled_qty, 2) if filled_price and filled_qty else None,
        }
        trades.append(trade)
    
    print(json.dumps(trades))

except Exception as e:
    print(json.dumps({"error": str(e)}))
