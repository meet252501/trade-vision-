"""
TradeVision AI — agent.py (V6 — MULTI-STRATEGY)
Supports Momentum, Mean Reversion, and Breakout strategies.
Fetches active strategy dynamically from UI backend.
"""
import numpy as np
import requests

# ■■ Configuration ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
UNIVERSE     = ['SPY', 'QQQ', 'IWM', 'XLK', 'XLF', 'XLE', 'XLV', 'GLD', 'TLT', 'SMH']
LOOKBACKS    = [10, 21, 42]     # Fast: 2-week, 1-month, 2-month momentum
SKIP_DAYS    = 3                # Skip most recent 3 days
LOOKBACK_VOL = 20               # 20-day volatility window
TOP_N        = 4                # Hold top 4 assets
MAX_POS      = 0.40             # Max 40% per position
TARGET_VOL   = 0.18             # Slightly higher target vol
SMA_LONG     = 200              # SPY SMA period for risk-off switch
SMA_SHORT    = 50               # SPY SMA-50 for re-entry confirmation
HYSTERESIS   = 0.02             # 2% buffer band around SMA-200
REBAL_DAYS   = 1                # Rebalance EVERY run

# Strategy specific
RSI_PERIOD   = 14
MACD_FAST, MACD_SLOW, MACD_SIGNAL = 12, 26, 9

_state = {
    'day_count': 0,
    'is_risk_off': False,
    'last_rebal_day': -999,
    'peak_equity': 0,
    'high_water_marks': {},
}

def compute_rsi(prices, period=14):
    if len(prices) < period + 1: return 50.0
    deltas = np.diff(prices[-(period + 1):])
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    avg_gain = np.mean(gains) if len(gains) > 0 else 0
    avg_loss = np.mean(losses) if len(losses) > 0 else 0.001
    rs = avg_gain / avg_loss if avg_loss > 0 else 100
    return 100 - (100 / (1 + rs))

def decide(market_state: dict, portfolio_state: dict, cash: float) -> list:
    orders = []
    _state['day_count'] += 1
    
    # Get active strategy from backend
    try:
        res = requests.get('http://127.0.0.1:3000/api/agent/strategy', timeout=2)
        strategy = res.json().get('active', 'momentum')
    except:
        strategy = 'momentum'
        
    print(f"  [AGENT] Active Strategy: {strategy.upper()}")

    prices = portfolio_state.get('last_prices', {})
    positions = portfolio_state.get('positions', [])
    pos_map = {p['ticker']: p for p in positions}

    def closes(ticker, n=None):
        bars = market_state.get(ticker, [])
        c = [b['close'] for b in bars]
        return c[-n:] if n else c

    current_equity = cash + sum(p['quantity'] * prices.get(p['ticker'], 0) for p in positions)

    # 1. Liquidate everything if Risk-Off (SPY below 200 SMA)
    spy_c = closes('SPY')
    if len(spy_c) >= SMA_LONG:
        sma200 = np.mean(spy_c[-SMA_LONG:])
        if spy_c[-1] < sma200 * (1 - HYSTERESIS):
            if positions:
                print("  [RISK] SPY below 200 SMA! Liquidating portfolio.")
                for p in positions:
                    orders.append({'ticker': p['ticker'], 'side': 'sell', 'quantity': p['quantity']})
                _state['high_water_marks'].clear()
            return orders

    # 2. Global Trailing Stop Loss (5%)
    for p in positions:
        t = p['ticker']
        curr_price = prices.get(t, 0)
        if curr_price > 0:
            if t not in _state['high_water_marks'] or curr_price > _state['high_water_marks'][t]:
                _state['high_water_marks'][t] = curr_price
            
            # If drops 5% below high water mark, stop out
            if curr_price < _state['high_water_marks'][t] * 0.95:
                print(f"  [STOP LOSS] {t} dropped 5% from peak. Executing stop-loss.")
                orders.append({'ticker': t, 'side': 'sell', 'quantity': p['quantity']})
                del _state['high_water_marks'][t]

    # Only rebalance every REBAL_DAYS
    if _state['day_count'] - _state['last_rebal_day'] < REBAL_DAYS:
        return orders

    # Close positions not meeting criteria or prepare target allocations
    target_allocs = {}

    if strategy == 'momentum':
        # Dual momentum logic
        scores = {}
        for ticker in UNIVERSE:
            c = closes(ticker)
            if len(c) > LOOKBACKS[-1] + SKIP_DAYS:
                recent = c[-SKIP_DAYS-1]
                ret1 = (recent / c[-LOOKBACKS[0] - SKIP_DAYS]) - 1
                ret2 = (recent / c[-LOOKBACKS[1] - SKIP_DAYS]) - 1
                ret3 = (recent / c[-LOOKBACKS[2] - SKIP_DAYS]) - 1
                mom_score = (ret1 * 0.4) + (ret2 * 0.3) + (ret3 * 0.3)
                
                # Filter out negative momentum
                if mom_score > 0:
                    scores[ticker] = mom_score
                    
        top_tickers = sorted(scores.keys(), key=lambda k: scores[k], reverse=True)[:TOP_N]
        
        # Inverse Volatility Position Sizing
        total_inv_vol = 0
        vols = {}
        for t in top_tickers:
            c_arr = np.array(closes(t))
            if len(c_arr) > 2:
                daily_rets = np.diff(c_arr) / c_arr[:-1]
                ann_vol = np.std(daily_rets) * np.sqrt(252)
                vols[t] = max(ann_vol, 0.05) # Floor to prevent div by zero
            else:
                vols[t] = 0.20
            total_inv_vol += (1.0 / vols[t])
            
        for t in top_tickers:
            # Weight = (1 / vol) / sum(1 / vol)
            # Max allocation is capped at MAX_POS
            raw_weight = (1.0 / vols[t]) / total_inv_vol
            target_allocs[t] = min(raw_weight, MAX_POS)
    elif strategy == 'mean_reversion':
        # Buy oversold (RSI < 30), Sell overbought (RSI > 70)
        # Sell existing overbought
        for p in positions:
            t = p['ticker']
            rsi = compute_rsi(closes(t))
            if rsi > 70:
                orders.append({'ticker': t, 'side': 'sell', 'quantity': p['quantity']})
                
        # Find oversold to buy
        for ticker in UNIVERSE:
            if ticker in pos_map: continue
            rsi = compute_rsi(closes(ticker))
            if rsi < 30:
                target_allocs[ticker] = MAX_POS
                
    elif strategy == 'breakout':
        # Buy 20-day high breakouts
        for p in positions:
            t = p['ticker']
            c = closes(t)
            if len(c) > 20:
                low_20 = min(c[-20:])
                if c[-1] < low_20 * 1.02: # Stop loss if we drop near 20 day low
                    orders.append({'ticker': t, 'side': 'sell', 'quantity': p['quantity']})
                    
        for ticker in UNIVERSE:
            if ticker in pos_map: continue
            c = closes(ticker)
            if len(c) > 20:
                high_20 = max(c[-21:-1]) # high of previous 20 days
                if c[-1] > high_20: # breakout!
                    target_allocs[ticker] = MAX_POS

    # Execute target allocations
    for t in list(pos_map.keys()):
        if t not in target_allocs and strategy == 'momentum':
            # Sell if not in top N (momentum)
            orders.append({'ticker': t, 'side': 'sell', 'quantity': pos_map[t]['quantity']})

    for ticker, target_pct in target_allocs.items():
        if ticker not in pos_map:
            price = prices.get(ticker)
            if price and price > 0:
                target_val = current_equity * target_pct
                qty = int(target_val / price)
                if qty > 0 and (qty * price) <= cash:
                    orders.append({'ticker': ticker, 'side': 'buy', 'quantity': qty})
                    cash -= (qty * price)

    if orders:
        _state['last_rebal_day'] = _state['day_count']

    return orders
