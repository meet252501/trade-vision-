import math
import statistics

# ■■ Configuration ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
YOLO_BASKET  = ["TQQQ", "SOXL", "UPRO", "TECL"] # 3x Leveraged ETFs
LOOKBACKS    = [3, 7]           # Fast: 3-tick, 7-tick momentum
TOP_N        = 2                # Hold top 2 strongest ETFs
MAX_POS      = 0.25             # 25% allocation * 2 = 50% cash used * 3x beta = 1.5x Leverage Limit

def decide(market_state: dict, portfolio_state: dict, cash: float, tradeable_equity: float = None) -> list:
    orders = []
    
    prices = portfolio_state.get('last_prices', {})
    positions = portfolio_state.get('positions', [])
    pos_map = {p['ticker']: p for p in positions}

    current_equity = cash + sum(p['quantity'] * prices.get(p['ticker'], 0) for p in positions)
    if tradeable_equity is None:
        tradeable_equity = current_equity

    # Score the YOLO basket
    scores = {}
    for ticker in YOLO_BASKET:
        bars = market_state.get(ticker, [])
        if not bars: continue
        c = [float(b['close']) for b in bars]
        if len(c) > LOOKBACKS[-1]:
            recent = c[-1]
            ret1 = (recent / c[-LOOKBACKS[0]]) - 1
            ret2 = (recent / c[-LOOKBACKS[1]]) - 1
            mom_score = (ret1 * 0.6) + (ret2 * 0.4)
            if mom_score > 0: # Only buy if momentum is positive
                scores[ticker] = mom_score
                
    # Select top N
    top_picks = sorted(scores.keys(), key=lambda k: scores[k], reverse=True)[:TOP_N]
    
    target_allocs = {}
    for t in top_picks:
        target_allocs[t] = MAX_POS

    # Sell what we shouldn't hold
    for t in list(pos_map.keys()):
        if t not in target_allocs:
            qty = pos_map[t]['quantity']
            if qty > 0 and not any(o['ticker'] == t for o in orders):
                orders.append({'ticker': t, 'side': 'sell', 'quantity': qty})
                
    # Buy to target allocations
    for ticker, target_pct in target_allocs.items():
        if ticker not in pos_map:
            price = prices.get(ticker, 0)
            if price > 0:
                target_val = tradeable_equity * target_pct
                target_val = min(target_val, cash)
                
                if target_val < 100: continue 
                
                qty = int(target_val / price)
                if qty > 0:
                    orders.append({'ticker': ticker, 'side': 'buy', 'quantity': qty})
                    cash -= (qty * price)

    return orders
