# omni_bot/insane_sprint.py
from omni_backtest import run_backtest

print("==================================================================")
print("             100X CRYPTO FUTURES SPRINT (15-MIN CHARTS)           ")
print("==================================================================")
print("Goal: Attempt to achieve 2.2% daily return (12x the account in 4 months).")
print("Starting Cash: $100")
print("Broker Leverage: 100x (Crypto Futures Exchange)")
print("Duration: Last 30 Days (15-Minute Data)")
print("==================================================================")

# To achieve 2.2% per day, we must trade much faster (15-minute charts) 
# and use massive 100x leverage. We will isolate the test to CRYPTO.
import config
config.ALL_ASSETS = config.CRYPTO # Only trade crypto

run_backtest(period="30d", interval="15m", leverage=100.0, initial_cash=100.0, label="100X INSANE SPRINT")
