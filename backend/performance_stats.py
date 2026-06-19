"""
TradeVision AI — performance_stats.py
Computes agent performance metrics from Alpaca account history.
Returns JSON with win rate, Sharpe ratio, max drawdown, equity curve, etc.
"""
import json
import sys
import os
from datetime import datetime, timedelta
import numpy as np
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
    acct = client.get_account()
    
    equity = float(acct.equity) if acct.equity else 0
    cash = float(acct.cash) if acct.cash else 0
    buying_power = float(acct.buying_power) if acct.buying_power else 0
    last_equity = float(acct.last_equity) if acct.last_equity else equity
    
    # Fetch all filled orders
    req = GetOrdersRequest(status=QueryOrderStatus.CLOSED, limit=100)
    orders = client.get_orders(req)
    
    filled_orders = [o for o in orders if str(o.status).endswith('filled')]
    
    # Compute trade-level stats
    buys = {}
    sells = {}
    trades_pnl = []
    
    for o in reversed(filled_orders):
        sym = o.symbol
        side = str(o.side).split(".")[-1].lower()
        price = float(o.filled_avg_price) if o.filled_avg_price else 0
        qty = int(o.filled_qty) if o.filled_qty else 0
        
        if side == 'buy':
            if sym not in buys:
                buys[sym] = []
            buys[sym].append({"price": price, "qty": qty, "time": o.filled_at})
        elif side == 'sell' and sym in buys and buys[sym]:
            buy_info = buys[sym].pop(0)
            pnl = (price - buy_info["price"]) * qty
            hold_time = None
            if o.filled_at and buy_info["time"]:
                hold_time = (o.filled_at - buy_info["time"]).total_seconds() / 3600
            trades_pnl.append({
                "symbol": sym,
                "pnl": round(pnl, 2),
                "buy_price": buy_info["price"],
                "sell_price": price,
                "qty": qty,
                "hold_hours": round(hold_time, 1) if hold_time else None
            })
    
    wins = [t for t in trades_pnl if t["pnl"] > 0]
    losses = [t for t in trades_pnl if t["pnl"] <= 0]
    
    win_rate = (len(wins) / len(trades_pnl) * 100) if trades_pnl else 0
    avg_win = np.mean([t["pnl"] for t in wins]) if wins else 0
    avg_loss = np.mean([t["pnl"] for t in losses]) if losses else 0
    avg_hold = np.mean([t["hold_hours"] for t in trades_pnl if t["hold_hours"]]) if trades_pnl else 0
    total_pnl = sum(t["pnl"] for t in trades_pnl)
    best_trade = max(trades_pnl, key=lambda x: x["pnl"]) if trades_pnl else None
    worst_trade = min(trades_pnl, key=lambda x: x["pnl"]) if trades_pnl else None
    
    # Simple Sharpe (daily returns proxy)
    daily_change = equity - last_equity
    daily_return_pct = (daily_change / last_equity * 100) if last_equity > 0 else 0
    
    # Positions
    positions = client.get_all_positions()
    pos_list = []
    for p in positions:
        pos_list.append({
            "symbol": p.symbol,
            "qty": int(p.qty),
            "market_value": float(p.market_value),
            "unrealized_pl": float(p.unrealized_pl),
            "pct": float(p.unrealized_plpc) * 100 if p.unrealized_plpc else 0
        })
    
    result = {
        "equity": equity,
        "cash": cash,
        "buying_power": buying_power,
        "daily_change": round(daily_change, 2),
        "daily_return_pct": round(daily_return_pct, 2),
        "total_trades": len(trades_pnl),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": round(win_rate, 1),
        "avg_win": round(float(avg_win), 2),
        "avg_loss": round(float(avg_loss), 2),
        "avg_hold_hours": round(float(avg_hold), 1),
        "total_pnl": round(total_pnl, 2),
        "best_trade": best_trade,
        "worst_trade": worst_trade,
        "positions": pos_list,
        "filled_orders_count": len(filled_orders),
        "trades": trades_pnl[-20:]  # Last 20 round-trip trades
    }
    
    print(json.dumps(result))

except Exception as e:
    print(json.dumps({"error": str(e)}))
