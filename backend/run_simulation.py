import numpy as np
import time

# --- CONFIGURATION ---
NUM_STOCKS = 100
NUM_DAYS = 1500
STARTING_EQUITY = 100000.0
TARGET_PROFIT = 500.0
TARGET_EQUITY = STARTING_EQUITY + TARGET_PROFIT

# Swarm Config
LOOKBACKS = [10, 21, 42]
SKIP_DAYS = 3
TOP_N = 2
MAX_POS = 0.40

print("=" * 55)
print("  TradeVision AI - SYNTHETIC HARD-MODE SIMULATION")
print("=" * 55)
print("Generating 100 Synthetic Stocks over 1,500 Days...")
print("Injecting Geometric Brownian Motion + Poisson Crashes...")

np.random.seed(42)

# Generate Synthetic Market (GBM + Jumps)
market_prices = np.zeros((NUM_DAYS, NUM_STOCKS))
market_prices[0, :] = 100.0 # Start all at $100

for s in range(NUM_STOCKS):
    mu = np.random.uniform(-0.0005, 0.001) # Slight upward or downward drift
    sigma = np.random.uniform(0.01, 0.05)  # Daily volatility
    
    # Generate prices
    for t in range(1, NUM_DAYS):
        # Normal GBM step
        shock = np.random.normal(0, 1)
        ret = mu + sigma * shock
        
        # Inject unpredictable massive Flash Crash (1% chance per day per stock)
        if np.random.random() < 0.01:
            ret -= np.random.uniform(0.05, 0.20) # 5% to 20% instant drop
            
        market_prices[t, s] = market_prices[t-1, s] * (1 + ret)
        
        # Prevent negative prices
        if market_prices[t, s] <= 0.1:
            market_prices[t, s] = 0.1

print("Market Generation Complete.\n")
print(f"Starting Gauntlet... Target: ${TARGET_EQUITY:,.2f}")

# --- SIMULATION STATE ---
cash = STARTING_EQUITY
positions = {} # {stock_idx: {'qty': X, 'peak': Y}}
day_count = 0

for t in range(LOOKBACKS[-1] + SKIP_DAYS + 1, NUM_DAYS):
    day_count += 1
    current_prices = market_prices[t, :]
    
    # 1. Update peaks and run 2% Trailing Stop-Loss
    to_sell = []
    for s_idx, pos in positions.items():
        curr_price = current_prices[s_idx]
        if curr_price > pos['peak']:
            pos['peak'] = curr_price
            
        # 2% Trailing Stop Loss trigger
        if curr_price < pos['peak'] * 0.98:
            to_sell.append(s_idx)
            
    # Execute Stop-Loss sells
    for s_idx in to_sell:
        qty = positions[s_idx]['qty']
        cash += qty * current_prices[s_idx]
        del positions[s_idx]
        
    # Calculate Current Equity
    current_equity = cash + sum(p['qty'] * current_prices[s_idx] for s_idx, p in positions.items())
    
    # Check Win/Loss Condition
    if current_equity >= TARGET_EQUITY:
        print("\n" + "="*50)
        print(f"[!] GOAL ACHIEVED! The Agent made $500!")
        print(f"Simulation Day : {t}")
        print(f"Final Equity   : ${current_equity:,.2f}")
        print("="*50)
        break
    
    if current_equity <= 0:
        print("\n[!] BANKRUPT. The Agent failed the simulation.")
        break
        
    if t % 50 == 0:
        print(f"[Day {t}] Equity: ${current_equity:,.2f} | Open Positions: {len(positions)}")

    # 2. Mathematical Scanner (Dual Momentum)
    scores = {}
    for s in range(NUM_STOCKS):
        if s in positions: continue # Don't buy more of what we have
        
        c = market_prices[:t, s]
        recent = c[-SKIP_DAYS-1]
        ret1 = (recent / c[-LOOKBACKS[0] - SKIP_DAYS]) - 1
        ret2 = (recent / c[-LOOKBACKS[1] - SKIP_DAYS]) - 1
        ret3 = (recent / c[-LOOKBACKS[2] - SKIP_DAYS]) - 1
        mom_score = (ret1 * 0.4) + (ret2 * 0.3) + (ret3 * 0.3)
        
        if mom_score > 0:
            scores[s] = mom_score
            
    # Micro-Filter: Only take top 2 stocks
    raw_top = sorted(scores.keys(), key=lambda k: scores[k], reverse=True)[:TOP_N]
    
    # 3. Synthetic Sentiment Swarm
    final_allocations = []
    for s in raw_top:
        # Generate fake sentiment (-1.0 to 1.0)
        synthetic_sentiment = np.random.uniform(-1.0, 1.0)
        
        if synthetic_sentiment < -0.3:
            pass # Veto!
        else:
            final_allocations.append(s)
            
    # 4. Execute BUYS (Equal weight for simplicity, max 40%)
    for s in final_allocations:
        if len(positions) >= 4: break # Max 4 positions globally
        
        alloc_cash = current_equity * MAX_POS
        if cash >= alloc_cash:
            qty = alloc_cash / current_prices[s]
            cash -= alloc_cash
            positions[s] = {'qty': qty, 'peak': current_prices[s]}

if current_equity < TARGET_EQUITY and current_equity > 0:
    print(f"\nSimulation ended after {NUM_DAYS} days. Target not reached. Final Equity: ${current_equity:,.2f}")
