import os
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient

load_dotenv()

API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
PAPER = os.getenv("ALPACA_PAPER", "True") == "True"

if not API_KEY or not SECRET_KEY:
    print("Error: Missing API keys.")
    exit(1)

client = TradingClient(API_KEY, SECRET_KEY, paper=PAPER)

print("Fetching current positions...")
positions = client.get_all_positions()

if not positions:
    print("No open positions found. You are already 100% in cash.")
else:
    print(f"Found {len(positions)} open positions. Sending market SELL orders to liquidate...")
    # Close all positions at market price
    client.close_all_positions(cancel_orders=True)
    print("All positions have been successfully liquidated. Agent is safely shut down.")
