# omni_bot/fast_sprint.py
from omni_backtest import run_backtest

print("==================================================================")
print("             OMNI-BOT FAST SPRINT (DAY TRADING TEST)              ")
print("==================================================================")
print("Goal: Prove the bot can make fast daily returns on a tiny account.")
print("Starting Cash: $100")
print("Broker Leverage: 50x (Simulating a standard Forex/Crypto Margin Account)")
print("Duration: Last 30 Days (Hourly Data)")
print("==================================================================")

# We use 50x leverage on a $100 account (Buying Power = $5,000)
# We test over the last 30 days using hourly data
run_backtest(period="30d", interval="1h", leverage=50.0, initial_cash=100.0, label="30-DAY FAST SPRINT")
