"""
Volatility Targeting Strategy
==============================
Sizes each position inversely to its recent volatility.
Targets a fixed portfolio volatility (default 10% annualized).
Cap leverage at 1.5x (Builderr.ai rule).

This is how professional risk managers allocate.
"""

import numpy as np


def decide(market_state: dict, portfolio_state: dict, cash: float) -> list[dict]:
    orders = []
    
    TARGET_VOL = 0.10      # 10% annualized target volatility
    MAX_LEVERAGE = 1.50     # Builderr.ai leverage cap
    LOOKBACK = 20           # 20-day rolling vol
    
    universe = ['SPY', 'QQQ', 'IWM', 'XLK', 'XLF', 'XLE', 'XLV', 'GLD']
    
    # ─── Risk-Off: SPY below SMA-200 ───
    spy_bars = market_state.get('SPY', [])
    if len(spy_bars) < 200:
        return []
    
    spy_closes = [b['close'] for b in spy_bars]
    spy_sma200 = np.mean(spy_closes[-200:])
    
    if spy_closes[-1] < spy_sma200:
        # Liquidate all positions
        for pos in portfolio_state.get('positions', []):
            orders.append({
                'ticker': pos['ticker'],
                'side': 'sell',
                'quantity': pos['quantity']
            })
        return orders
    
    # ─── Calculate target weights based on inverse volatility ───
    equity = cash + sum(
        pos['quantity'] * portfolio_state.get('last_prices', {}).get(pos['ticker'], 0)
        for pos in portfolio_state.get('positions', [])
    )
    
    vol_scores = {}
    for ticker in universe:
        bars = market_state.get(ticker, [])
        if len(bars) < LOOKBACK + 1:
            continue
        
        closes = np.array([b['close'] for b in bars[-(LOOKBACK + 1):]])
        daily_returns = np.diff(closes) / closes[:-1]
        current_vol = daily_returns.std() * np.sqrt(252)  # Annualized
        
        if current_vol > 0:
            vol_scores[ticker] = current_vol
    
    if not vol_scores:
        return []
    
    # Inverse vol weights: lower vol = higher allocation
    inv_vols = {t: 1.0 / v for t, v in vol_scores.items()}
    total_inv_vol = sum(inv_vols.values())
    
    raw_weights = {t: iv / total_inv_vol for t, iv in inv_vols.items()}
    
    # Scale to target portfolio vol
    # Portfolio vol ≈ weighted average of individual vols (simplified)
    portfolio_vol = sum(raw_weights[t] * vol_scores[t] for t in raw_weights)
    scale_factor = TARGET_VOL / portfolio_vol if portfolio_vol > 0 else 1.0
    scale_factor = min(scale_factor, MAX_LEVERAGE)  # Cap at 1.5x
    
    target_weights = {t: w * scale_factor for t, w in raw_weights.items()}
    
    # ─── Rebalance: sell what's overweight, buy what's underweight ───
    current_holdings = {}
    for pos in portfolio_state.get('positions', []):
        price = portfolio_state.get('last_prices', {}).get(pos['ticker'], 0)
        current_holdings[pos['ticker']] = {
            'quantity': pos['quantity'],
            'value': pos['quantity'] * price,
            'weight': (pos['quantity'] * price) / equity if equity > 0 else 0,
        }
    
    # Sell positions not in target or overweight
    for pos in portfolio_state.get('positions', []):
        ticker = pos['ticker']
        if ticker not in target_weights:
            orders.append({
                'ticker': ticker,
                'side': 'sell',
                'quantity': pos['quantity']
            })
    
    # Buy/rebalance target positions
    for ticker, target_w in target_weights.items():
        price = portfolio_state.get('last_prices', {}).get(ticker, 0)
        if price <= 0:
            continue
        
        target_value = equity * target_w
        target_qty = int(target_value / price)
        
        current_qty = 0
        if ticker in current_holdings:
            current_qty = current_holdings[ticker]['quantity']
        
        diff = target_qty - current_qty
        
        if diff > 5:  # Buy threshold to avoid tiny trades
            cost = diff * price
            if cost <= cash:
                orders.append({
                    'ticker': ticker,
                    'side': 'buy',
                    'quantity': diff
                })
                cash -= cost
        elif diff < -5:  # Sell threshold
            orders.append({
                'ticker': ticker,
                'side': 'sell',
                'quantity': abs(diff)
            })
    
    return orders
