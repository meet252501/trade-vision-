"""
TradeVision V5 - Autonomous Live Runner
Continuously runs the trading agent until $500 profit is reached.
"""
import time
import sys
import os
import argparse

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from dotenv import load_dotenv
from alpaca.trading.client import TradingClient

load_dotenv()
API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

if not API_KEY or not SECRET_KEY:
    print("Error: Missing Alpaca API keys.")
    sys.exit(1)

client = TradingClient(API_KEY, SECRET_KEY, paper=True)

# Import agent and executor as modules so state persists
import agent
import executor

parser = argparse.ArgumentParser(description="TradeVision V5 Autonomous Agent")
parser.add_argument("--target", type=float, default=500.0, help="Target profit to stop trading")
args = parser.parse_args()

start_equity = float(client.get_account().equity)
TARGET_PROFIT = args.target

print("=" * 55)
print("  TradeVision V5 Autonomous Agent - LIVE")
print("=" * 55)
print(f"  Starting Equity : ${start_equity:,.2f}")
print(f"  Target Profit   : +${TARGET_PROFIT:,.2f}")
print(f"  Target Equity   : ${(start_equity + TARGET_PROFIT):,.2f}")
print(f"  API Key         : {API_KEY[:8]}...{API_KEY[-4:]}")
print(f"  Mode            : Paper Trading")
print("=" * 55)

# Force first rebalance
agent._state['last_rebal_day'] = -999

iteration = 1
while True:
    print(f"\n{'=' * 50}")
    print(f"[Iteration {iteration}] Scanning markets...")
    
    try:
        # Fetch portfolio and market state
        portfolio_state, cash = executor.fetch_portfolio_state()
        full_universe = set(agent.UNIVERSE + [p['ticker'] for p in portfolio_state['positions']])
        
        # Try to get latest quotes
        try:
            from alpaca.data.requests import StockLatestQuoteRequest, CryptoLatestQuoteRequest
            from alpaca.data.historical import CryptoHistoricalDataClient
            
            crypto_symbols = [s for s in full_universe if '/USD' in s]
            stock_symbols = [s for s in full_universe if '/USD' not in s]
            
            if stock_symbols:
                quote_req = StockLatestQuoteRequest(symbol_or_symbols=stock_symbols)
                quotes = executor.data_client.get_stock_latest_quote(quote_req)
                for sym, quote in quotes.items():
                    if float(quote.ask_price) > 0:
                        portfolio_state['last_prices'][sym] = float(quote.ask_price)
                        
            if crypto_symbols:
                crypto_client = CryptoHistoricalDataClient(API_KEY, SECRET_KEY)
                crypto_req = CryptoLatestQuoteRequest(symbol_or_symbols=crypto_symbols)
                crypto_quotes = crypto_client.get_crypto_latest_quote(crypto_req)
                for sym, quote in crypto_quotes.items():
                    if float(quote.ask_price) > 0:
                        portfolio_state['last_prices'][sym] = float(quote.ask_price)
                        
        except Exception as e:
            print(f"  [WARN] Could not fetch latest quotes: {e}")
        
        # Update peak equity
        total_pos_val = sum(
            p['quantity'] * portfolio_state['last_prices'].get(p['ticker'], 0)
            for p in portfolio_state['positions']
        )
        agent._state['peak_equity'] = cash + total_pos_val
        
        # Fetch market data and run agent
        market_state = executor.fetch_market_state(list(full_universe), portfolio_state['last_prices'])
        orders = agent.decide(market_state, portfolio_state, cash)
        
        # Execute orders
        executor.execute_orders(orders)
        
    except Exception as e:
        print(f"  [ERROR] Agent iteration failed: {e}")
    
    # Check current equity
    try:
        current_equity = float(client.get_account().equity)
        profit = current_equity - start_equity
        pct = (profit / start_equity) * 100
        
        progress = min(100, max(0, (profit / TARGET_PROFIT) * 100))
        bar_len = int(progress / 2)
        bar = "#" * bar_len + "-" * (50 - bar_len)
        
        print(f"\n  +------------------------------------------------------+")
        print(f"  | Equity: ${current_equity:>10,.2f}  |  P/L: {'+'if profit>=0 else ''}{profit:>8,.2f} ({pct:+.2f}%)")
        print(f"  | [{bar}] {progress:.0f}%")
        print(f"  +------------------------------------------------------+")
        
        if profit >= TARGET_PROFIT:
            print(f"\n  *** TARGET REACHED! +${profit:,.2f} profit! ***")
            break
    except Exception as e:
        print(f"  [WARN] Could not check equity: {e}")
    
    wait_secs = 120  # Check every 2 minutes
    print(f"\n  Waiting {wait_secs}s before next scan...")
    time.sleep(wait_secs)
    iteration += 1
