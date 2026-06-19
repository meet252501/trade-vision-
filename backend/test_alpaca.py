from alpaca.trading.client import TradingClient
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

client = TradingClient(API_KEY, SECRET_KEY, paper=True)
try:
    history = client.get_portfolio_history()
    print("Success! Keys:", dir(history))
except Exception as e:
    print("Error:", e)
