"""
SMA Crossover Strategy
=======================
Buy when SMA-50 crosses above SMA-200 (golden cross).
Sell when SMA-50 crosses below SMA-200 (death cross).
Simple, few trades, good for trending markets.
"""

import numpy as np


def decide(market_state: dict, portfolio_state: dict, cash: float) -> list[dict]:
    orders = []
    
    universe = list(market_state.keys())
    if not universe:
        return []

    for ticker in universe:
        bars = market_state.get(ticker, [])
        if len(bars) < 201:  # Need at least 200+1 bars for crossover detection
            continue

        closes = [b['close'] for b in bars]
        
        # Calculate current SMAs
        sma50_now = np.mean(closes[-50:])
        sma200_now = np.mean(closes[-200:])
        
        # Calculate previous day SMAs
        sma50_prev = np.mean(closes[-51:-1])
        sma200_prev = np.mean(closes[-201:-1])
        
        price = closes[-1]
        
        # Check if we hold this ticker
        held_qty = 0
        for pos in portfolio_state.get('positions', []):
            if pos['ticker'] == ticker:
                held_qty = pos['quantity']
                break
        
        # ─── Golden Cross: SMA-50 crosses above SMA-200 ───
        if sma50_prev <= sma200_prev and sma50_now > sma200_now:
            if held_qty == 0:
                # Calculate position size (equal weight across universe)
                equity = cash + sum(
                    p['quantity'] * portfolio_state.get('last_prices', {}).get(p['ticker'], 0)
                    for p in portfolio_state.get('positions', [])
                )
                target_val = equity * 0.25  # Max 25% per position
                qty = int(target_val / price)
                if qty > 0 and cash >= qty * price:
                    orders.append({
                        'ticker': ticker,
                        'side': 'buy',
                        'quantity': qty
                    })
                    cash -= qty * price
        
        # ─── Death Cross: SMA-50 crosses below SMA-200 ───
        elif sma50_prev >= sma200_prev and sma50_now < sma200_now:
            if held_qty > 0:
                orders.append({
                    'ticker': ticker,
                    'side': 'sell',
                    'quantity': held_qty
                })

    return orders
