import time
import traceback
import logging
import sys
from datetime import datetime
from config import ALL_ASSETS
import master_agent
from exchanges.mt5_adapter import MT5Adapter

# Configure professional logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    handlers=[
        logging.FileHandler("omni_bot_activity.log", mode='a'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("OmniBot")

# Instantiate the exchange adapter
exchange = MT5Adapter()

# Bot State Persistence
bot_state = {
    'trade_count': 0
}

def run_bot_cycle():
    """Executes a single iteration of the trading loop."""
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Waking up Omni-Bot v3.0...")
    
    # ── 1. Fetch State via Adapter ──
    try:
        portfolio_state = exchange.get_portfolio_state()
        market_state, last_prices = exchange.fetch_live_data(ALL_ASSETS)
        portfolio_state['last_prices'] = last_prices
    except Exception as e:
        print(f"Error fetching data: {e}")
        return False
        
    print(f"Current Equity: ${portfolio_state['total_equity']:,.2f}")
    print(f"Open Positions: {len(portfolio_state['positions'])}")
    
    # ── 2. Master Agent Decision ──
    try:
        orders = master_agent.decide(market_state, portfolio_state, portfolio_state['total_equity'])
    except Exception as e:
        if "CIRCUIT BREAKER" in str(e):
            print(f"🚨🚨 {e} 🚨🚨")
            print("Trading halted by risk management system.")
            return False
        print(f"Agent decision failed: {e}")
        traceback.print_exc()
        return False
        
    # ── 3. Execute Orders via Adapter ──
    if orders:
        print(f"Master Agent generated {len(orders)} orders.")
        exchange.execute_orders(orders)
    else:
        print("Master Agent: No trades to execute at this time.")
    
    return True

if __name__ == "__main__":
    print("=====================================")
    print("  OMNI-BOT v3.0 UNIVERSAL ENGINE")
    print("=====================================")
    
    if not exchange.initialize():
        print("Failed to initialize Exchange Adapter.")
        exit(1)
        
    master_agent.load_state()
        
    # Run continuously (Checking every hour for 1D/1H signals)
    try:
        while True:
            if not run_bot_cycle():
                print("Bot cycle failed or circuit breaker triggered. Stopping loop.")
                break
                
            master_agent.save_state()
            
            print("Cycle complete. Sleeping for 1 hour until next bar...")
            time.sleep(3600)  # Wait 1 hour between checks
    except KeyboardInterrupt:
        print("Bot stopped by user.")
    finally:
        master_agent.save_state()
        exchange.shutdown()
