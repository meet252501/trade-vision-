# omni_bot/validate_omni.py
from omni_backtest import run_backtest

print("=" * 60)
print("   OMNI-BOT v2.0 STRESS TEST (UPGRADED ARCHITECTURE)")
print("=" * 60)

# 1. COVID-19 Flash Crash
print("\n>>> REGIME 1: COVID-19 FLASH CRASH (Feb-Jul 2020)")
run_backtest(start_date="2020-02-01", end_date="2020-07-01", interval="1d", leverage=1.0, initial_cash=10000.0, label="COVID CRASH")

# 2. Crypto Winter
print("\n>>> REGIME 2: CRYPTO WINTER (Jan-Dec 2022)")
run_backtest(start_date="2022-01-01", end_date="2022-12-31", interval="1d", leverage=1.0, initial_cash=10000.0, label="CRYPTO WINTER")

# 3. Bull Market
print("\n>>> REGIME 3: BULL MARKET (Jan-Dec 2021)")
run_backtest(start_date="2021-01-01", end_date="2021-12-31", interval="1d", leverage=1.0, initial_cash=10000.0, label="BULL MARKET")

# 4. 5-Year Full Cycle
print("\n>>> REGIME 4: 5-YEAR FULL CYCLE (2019-2024)")
run_backtest(start_date="2019-01-01", end_date="2024-01-01", interval="1d", leverage=1.0, initial_cash=10000.0, label="5-YEAR FULL CYCLE")

# 5. Fast Sprint ($50 account with 50x leverage)
print("\n>>> REGIME 5: $50 FAST SPRINT (Last 30 Days, Hourly)")
run_backtest(period="30d", interval="1h", leverage=50.0, initial_cash=50.0, label="$50 FAST SPRINT")

print("\nAll stress tests completed.")
