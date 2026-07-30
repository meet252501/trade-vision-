import yfinance as yf
import pandas as pd
from local_test_agent import YOLO_BASKET, decide

print("Downloading Forex Data for the last 60 days (1-hour intervals)...")
data = yf.download(YOLO_BASKET, period="60d", interval="1h")

# Reformat for the agent
history = {}
for ticker in YOLO_BASKET:
    df = data['Close'][ticker].dropna()
    history[ticker] = [{'close': val} for val in df.values]

cash = 1000.0 # Start with $1,000 real money
LEVERAGE = 50.0 # 50x Forex Leverage
tradeable_equity = cash * LEVERAGE 

portfolio_state = {'positions': [], 'last_prices': {}}
market_state = {}

print(f"\nStarting Balance: ${cash:,.2f} (Buying Power: ${tradeable_equity:,.2f})")

winning_trades = 0
losing_trades = 0

# Simulate trading hour by hour
total_steps = min(len(history[ticker]) for ticker in YOLO_BASKET)
start_step = 24 

for step in range(start_step, total_steps):
    # Build market state up to this hour
    for ticker in YOLO_BASKET:
        market_state[ticker] = history[ticker][:step]
        portfolio_state['last_prices'][ticker] = history[ticker][step-1]['close']
        
    # The agent thinks it has LEVERAGE amount of cash
    orders = decide(market_state, portfolio_state, tradeable_equity)
    
    # Process orders 
    for o in orders:
        t = o['ticker']
        price = portfolio_state['last_prices'][t]
        qty = o['quantity']
        
        if o['side'] == 'buy':
            cost = qty * price
            if tradeable_equity >= cost:
                tradeable_equity -= cost
                existing = next((p for p in portfolio_state['positions'] if p['ticker'] == t), None)
                if existing:
                    existing['quantity'] += qty
                else:
                    portfolio_state['positions'].append({'ticker': t, 'quantity': qty, 'entry_price': price})
                    
        elif o['side'] == 'sell':
            existing = next((p for p in portfolio_state['positions'] if p['ticker'] == t), None)
            if existing and existing['quantity'] >= qty:
                # Calculate profit/loss for win rate
                trade_profit = (price - existing['entry_price']) * qty
                if trade_profit > 0:
                    winning_trades += 1
                else:
                    losing_trades += 1
                    
                tradeable_equity += qty * price
                existing['quantity'] -= qty
                if existing['quantity'] == 0:
                    portfolio_state['positions'].remove(existing)

# Calculate Final Equity
current_equity = (tradeable_equity / LEVERAGE) + sum(p['quantity'] * portfolio_state['last_prices'][p['ticker']] / LEVERAGE for p in portfolio_state['positions'])
profit = current_equity - 1000.0
win_rate = (winning_trades / (winning_trades + losing_trades)) * 100 if (winning_trades + losing_trades) > 0 else 0

print(f"Ending Balance:   ${current_equity:,.2f}")
print(f"Total Profit:     ${profit:,.2f} (in 60 days of trading)")
print(f"Win Rate:         {win_rate:.1f}% ({winning_trades} wins, {losing_trades} losses)\n")
print("Positions Held:")
for p in portfolio_state['positions']:
    t = p['ticker']
    price = portfolio_state['last_prices'][t]
    val = p['quantity'] * price
    print(f"- {t}: {p['quantity']} units (${val:,.2f})")
print(f"- CASH: ${cash:,.2f}")
