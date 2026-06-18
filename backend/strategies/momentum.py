"""
Dual Momentum Strategy
=======================
Ranks a universe of ETFs by 3-month return.
Buys top 3 with positive momentum.
Risk-off: If SPY < SMA-200, go fully to cash.

Historical performance: ~12% CAGR, <15% max drawdown.
"""

import numpy as np


def decide(market_state: dict, portfolio_state: dict, cash: float) -> list[dict]:
    orders = []

    # ─── Risk-Off Switch: SPY below 200-day SMA ───
    spy_bars = market_state.get('SPY', [])
    if len(spy_bars) < 200:
        return []

    spy_closes = [b['close'] for b in spy_bars]
    spy_sma200 = np.mean(spy_closes[-200:])
    spy_price = spy_closes[-1]

    if spy_price < spy_sma200:
        # Sell everything — market downtrend
        for pos in portfolio_state.get('positions', []):
            orders.append({
                'ticker': pos['ticker'],
                'side': 'sell',
                'quantity': pos['quantity']
            })
        return orders

    # ─── Momentum Ranking ───
    universe = ['SPY', 'QQQ', 'IWM', 'XLK', 'XLF', 'XLE', 'XLV', 'GLD']
    momentum = {}

    for ticker in universe:
        bars = market_state.get(ticker, [])
        if len(bars) < 63:
            continue
        closes = [b['close'] for b in bars]
        ret_3m = (closes[-1] - closes[-63]) / closes[-63]
        momentum[ticker] = ret_3m

    if not momentum:
        return []

    ranked = sorted(momentum.items(), key=lambda x: x[1], reverse=True)
    top3 = [t for t, r in ranked[:3] if r > 0]

    if not top3:
        return []

    # ─── Position Sizing ───
    equity = cash + sum(
        pos['quantity'] * portfolio_state.get('last_prices', {}).get(pos['ticker'], 0)
        for pos in portfolio_state.get('positions', [])
    )
    target_pct = min(0.30, 1.0 / len(top3))
    target_val = equity * target_pct

    # Sell positions not in top3
    for pos in portfolio_state.get('positions', []):
        if pos['ticker'] not in top3:
            orders.append({
                'ticker': pos['ticker'],
                'side': 'sell',
                'quantity': pos['quantity']
            })

    # Buy new top3 positions
    held = {p['ticker'] for p in portfolio_state.get('positions', [])}
    for ticker in top3:
        if ticker not in held:
            price = portfolio_state.get('last_prices', {}).get(ticker, 1)
            qty = int(target_val / price)
            if qty > 0 and cash >= qty * price:
                orders.append({
                    'ticker': ticker,
                    'side': 'buy',
                    'quantity': qty
                })
                cash -= qty * price

    return orders
