import sys
import os
import json
import numpy as np

# Ensure we can import from the omni_bot directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from master_agent import decide, reset_state
from config import MACRO_EQUITY_TICKER, MACRO_CRYPTO_TICKER

def print_result(name, passed, details=""):
    status = "PASS" if passed else "FAIL"
    print(f"{status} | {name}")
    if details:
        print(f"       -> {details}")

def test_flash_crash():
    reset_state()
    market_state = {MACRO_EQUITY_TICKER: [{'close': 100}] * 65}
    
    # Establish peak equity at $10,000
    port_state = {'positions': [], 'last_prices': {}, 'real_equity': 10000, 'total_equity': 10000}
    decide(market_state, port_state, 10000)
    
    # Suffer a massive 30% flash crash down to $7,000
    port_state['real_equity'] = 7000
    port_state['total_equity'] = 7000
    
    try:
        orders = decide(market_state, port_state, 7000)
        # Should return an empty list because the circuit breaker tripped
        passed = len(orders) == 0
        details = "Bot correctly halted trading." if passed else f"Bot tried to trade: {orders}"
        print_result("Flash Crash (30% Drop)", passed, details)
    except Exception as e:
        print_result("Flash Crash (30% Drop)", False, f"Crashed with error: {e}")

def test_macro_bear_market():
    reset_state()
    
    # Create 60 bars of SPY trending heavily downward
    spy_bars = [{'close': 200 - i} for i in range(65)] 
    
    # Create 60 bars of AAPL trending heavily upward (should trigger a buy signal if isolated)
    aapl_bars = [
        {'close': 100 + i, 'high': 100 + i, 'low': 99 + i, 'open': 99 + i, 'volume': 1000} 
        for i in range(65)
    ]
    
    market_state = {
        MACRO_EQUITY_TICKER: spy_bars,
        'AAPL': aapl_bars
    }
    
    port_state = {'positions': [], 'last_prices': {'AAPL': 165}, 'real_equity': 10000, 'total_equity': 10000}
    
    orders = decide(market_state, port_state, 10000)
    
    # The bot should refuse to buy AAPL because SPY is in a bear market
    buy_orders = [o for o in orders if o['side'] == 'buy' and o['ticker'] == 'AAPL']
    passed = len(buy_orders) == 0
    details = "Bot refused AAPL momentum due to SPY bear market." if passed else f"Bot bought AAPL against the trend!"
    print_result("Macro Bear Market Filter", passed, details)

def test_whipsaw_market():
    reset_state()
    
    # Create SPY bull market
    spy_bars = [{'close': 100 + i} for i in range(65)]
    
    # Create AAPL choppy market (price alternates up and down, net zero trend)
    aapl_bars = []
    for i in range(65):
        price = 150 + (10 if i % 2 == 0 else -10)
        aapl_bars.append({'close': price, 'high': price+5, 'low': price-5, 'open': price, 'volume': 1000})
        
    market_state = {
        MACRO_EQUITY_TICKER: spy_bars,
        'AAPL': aapl_bars
    }
    
    port_state = {'positions': [], 'last_prices': {'AAPL': 160}, 'real_equity': 10000, 'total_equity': 10000}
    
    orders = decide(market_state, port_state, 10000)
    
    # The bot should refuse to trade AAPL because ADX is too low (whipsaw)
    buy_orders = [o for o in orders if o['side'] == 'buy' and o['ticker'] == 'AAPL']
    passed = len(buy_orders) == 0
    details = "Bot rejected trade due to low ADX/choppy market." if passed else "Bot bought into a whipsaw!"
    print_result("Low Volatility Whipsaw", passed, details)

def test_garbage_data():
    reset_state()
    
    # Simulate API returning empty lists, missing keys, and None values
    market_state = {
        MACRO_EQUITY_TICKER: [],
        'AAPL': None,
        'TSLA': [{'close': np.nan}],
        'MSFT': [{'wrong_key': 100}]
    }
    
    port_state = {'positions': [], 'last_prices': {}, 'real_equity': 10000, 'total_equity': 10000}
    
    try:
        orders = decide(market_state, port_state, 10000)
        passed = True
        details = "Bot survived garbage data without crashing."
    except Exception as e:
        passed = False
        details = f"Bot crashed with error: {e}"
        
    print_result("Garbage Data Integrity", passed, details)

if __name__ == "__main__":
    print("\n" + "="*50)
    print("  OMNI-BOT STRESS TEST GAUNTLET")
    print("="*50 + "\n")
    
    test_flash_crash()
    test_macro_bear_market()
    test_whipsaw_market()
    test_garbage_data()
    
    print("\n" + "="*50)
    print("  GAUNTLET COMPLETE")
    print("="*50 + "\n")
