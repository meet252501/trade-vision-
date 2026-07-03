# omni_bot/predict_future.py
import yfinance as yf
import numpy as np
import time
from config import ALL_ASSETS, BB_PERIOD
from master_agent import decide

def generate_future_market(days=114):
    print(f"Downloading last {days} days to analyze market physics on hourly interval...")
    data = yf.download(ALL_ASSETS, period=f"{days}d", interval="1h")
    
    synthetic_history = {}
    
    for ticker in ALL_ASSETS:
        df = data['Close'][ticker].dropna()
        if len(df) < 10:
            print(f"Skipping {ticker}, not enough data.")
            continue
            
        prices = df.values
        returns = np.diff(prices) / prices[:-1]
        
        mu = np.mean(returns)
        sigma = np.std(returns)
        
        # We need to simulate the same number of hours into the future
        future_steps = len(df)
        
        # Monte Carlo Simulation (Geometric Brownian Motion)
        future_prices = [prices[-1]] 
        for _ in range(future_steps):
            # Z is a random normal variable
            Z = np.random.normal(0, 1)
            # Drift and shock
            drift = mu - (0.5 * sigma**2)
            shock = sigma * Z
            next_price = future_prices[-1] * np.exp(drift + shock)
            future_prices.append(next_price)
            
        # Format for the bot (prepending some real history so indicators can warm up)
        # We need at least BB_PERIOD of real history to avoid cold starts
        warmup = prices[-BB_PERIOD:]
        combined_prices = list(warmup) + future_prices[1:]
        
        synthetic_history[ticker] = [{'close': float(p)} for p in combined_prices]
        
    return synthetic_history

def run_predictive_test(days=114, initial_cash=50.0, leverage=50.0):
    print("==================================================================")
    print("          OMNI-BOT FUTURE PREDICTION (MONTE CARLO)                ")
    print("==================================================================")
    
    history = generate_future_market(days)
    
    cash = initial_cash
    tradeable_equity = cash * leverage 
    portfolio_state = {'positions': [], 'last_prices': {}}
    market_state = {}
    
    print(f"\n[OMNI-BOT] Generating {days} days into the future...")
    print(f"[OMNI-BOT] Starting Balance: ${cash:,.2f} (Buying Power: ${tradeable_equity:,.2f})")
    
    winning_trades = 0
    losing_trades = 0
    
    min_steps = min(len(history[t]) for t in history)
    start_step = BB_PERIOD + 1 
    
    start_time = time.time()
    
    for step in range(start_step, min_steps):
        current_eq = (tradeable_equity / leverage) + sum(p['quantity'] * portfolio_state['last_prices'].get(p['ticker'], 0) / leverage for p in portfolio_state['positions'])
        portfolio_state['total_equity'] = current_eq * leverage
        
        for ticker in history:
            market_state[ticker] = history[ticker][:step]
            portfolio_state['last_prices'][ticker] = history[ticker][step-1]['close']
            
        orders = decide(market_state, portfolio_state, tradeable_equity)
        
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
                        total_qty = existing['quantity'] + qty
                        existing['entry_price'] = ((existing['entry_price'] * existing['quantity']) + (price * qty)) / total_qty
                        existing['quantity'] = total_qty
                    else:
                        portfolio_state['positions'].append({'ticker': t, 'quantity': qty, 'entry_price': price})
                        
            elif o['side'] == 'sell':
                existing = next((p for p in portfolio_state['positions'] if p['ticker'] == t), None)
                if existing and existing['quantity'] >= qty:
                    trade_profit = (price - existing['entry_price']) * qty
                    if trade_profit > 0: winning_trades += 1
                    else: losing_trades += 1
                        
                    tradeable_equity += qty * price
                    existing['quantity'] -= qty
                    if existing['quantity'] == 0:
                        portfolio_state['positions'].remove(existing)
    
    end_time = time.time()
    
    current_equity = (tradeable_equity / leverage) + sum(p['quantity'] * portfolio_state['last_prices'][p['ticker']] / leverage for p in portfolio_state['positions'])
    profit = current_equity - initial_cash
    win_rate = (winning_trades / (winning_trades + losing_trades)) * 100 if (winning_trades + losing_trades) > 0 else 0
    
    print("\n========================================")
    print("OCTOBER 25, 2026 PREDICTION RESULTS")
    print("========================================")
    print(f"Ending Balance:   ${current_equity:,.2f}")
    print(f"Total Profit:     ${profit:,.2f} (in {days} days)")
    print(f"Win Rate:         {win_rate:.1f}% ({winning_trades} wins, {losing_trades} losses)")
    print(f"Sim Time:         {(end_time - start_time):.2f} seconds")
    print("Positions Held at End:")
    if not portfolio_state['positions']:
        print(" - None (All flat in cash)")
    else:
        for p in portfolio_state['positions']:
            t = p['ticker']
            price = portfolio_state['last_prices'][t]
            profit_pct = (price / p['entry_price']) - 1
            print(f" - {t}: {p['quantity']} units | Unrealized: {profit_pct*100:.2f}%")

if __name__ == "__main__":
    np.random.seed(42) # Set seed for reproducible future simulation
    run_predictive_test(days=114, initial_cash=50.0, leverage=50.0)
