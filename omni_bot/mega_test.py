# omni_bot/mega_test.py
# ═══════════════════════════════════════════════════════════════════
# OMNI-BOT v2.0 — MEGA STRESS TEST SUITE
# Tests: 10 Market Regimes + Edge Cases + Spread Sensitivity
# ═══════════════════════════════════════════════════════════════════
from omni_backtest import run_backtest
import sys

results = []

def capture_result(label, **kwargs):
    """Run a backtest and capture the result for final summary."""
    print(f"\n>>> {label}")
    run_backtest(label=label, **kwargs)

print("=" * 70)
print("   OMNI-BOT v2.0 MEGA STRESS TEST — 10 REGIMES + EDGE CASES")
print("=" * 70)

# ═══════════════════════════════════════════════════════════════════
# PART 1: MARKET REGIME TESTS (10 different market conditions)
# ═══════════════════════════════════════════════════════════════════

# 1. COVID-19 Flash Crash (V-shaped recovery)
capture_result("COVID CRASH (Feb-Jul 2020)",
    start_date="2020-02-01", end_date="2020-07-01", interval="1d",
    leverage=1.0, initial_cash=10000.0)

# 2. Crypto Winter (prolonged bear market)
capture_result("CRYPTO WINTER (Jan-Dec 2022)",
    start_date="2022-01-01", end_date="2022-12-31", interval="1d",
    leverage=1.0, initial_cash=10000.0)

# 3. Strong Bull Market (everything goes up)
capture_result("BULL MARKET (Jan-Dec 2021)",
    start_date="2021-01-01", end_date="2021-12-31", interval="1d",
    leverage=1.0, initial_cash=10000.0)

# 4. 5-Year Full Cycle (bull + bear + recovery)
capture_result("5-YEAR FULL CYCLE (2019-2024)",
    start_date="2019-01-01", end_date="2024-01-01", interval="1d",
    leverage=1.0, initial_cash=10000.0)

# 5. The $50 Fast Sprint (your actual live scenario)
capture_result("$50 FAST SPRINT (30d Hourly)",
    period="30d", interval="1h",
    leverage=50.0, initial_cash=50.0)

# 6. SIDEWAYS CHOP — 2015 (flat, choppy, zero trend)
# 2015 was notoriously flat — tests if the bot avoids overtrading
capture_result("SIDEWAYS CHOP (Jan-Dec 2015)",
    start_date="2015-01-01", end_date="2015-12-31", interval="1d",
    leverage=1.0, initial_cash=10000.0)

# 7. INTEREST RATE HIKE SHOCK (2018 Q4 sell-off)
capture_result("RATE HIKE SHOCK (Sep-Dec 2018)",
    start_date="2018-09-01", end_date="2018-12-31", interval="1d",
    leverage=1.0, initial_cash=10000.0)

# 8. POST-COVID RECOVERY (Jul 2020 - Jan 2021, strong trend)
capture_result("POST-COVID RECOVERY (Jul 2020 - Jan 2021)",
    start_date="2020-07-01", end_date="2021-01-01", interval="1d",
    leverage=1.0, initial_cash=10000.0)

# 9. 2023 AI RALLY (strong tech, narrow breadth)
capture_result("AI RALLY (Jan-Dec 2023)",
    start_date="2023-01-01", end_date="2023-12-31", interval="1d",
    leverage=1.0, initial_cash=10000.0)

# 10. RECENT 90 DAYS (most current market — final reality check)
capture_result("RECENT 90 DAYS (Daily)",
    period="90d", interval="1d",
    leverage=1.0, initial_cash=10000.0)

# ═══════════════════════════════════════════════════════════════════
# PART 2: EDGE CASE TESTS
# ═══════════════════════════════════════════════════════════════════

# 11. Tiny Account — Can the bot survive on just $25?
capture_result("MICRO ACCOUNT $25 (30d Hourly)",
    period="30d", interval="1h",
    leverage=50.0, initial_cash=25.0)

# 12. Large Account — Does it scale up without breaking?
capture_result("LARGE ACCOUNT $100K (2021-2023)",
    start_date="2021-01-01", end_date="2023-12-31", interval="1d",
    leverage=1.0, initial_cash=100000.0)

# 13. Very Short Period — 7 days of hourly data
capture_result("ULTRA SHORT (7d Hourly)",
    period="7d", interval="1h",
    leverage=50.0, initial_cash=50.0)

print("\n" + "=" * 70)
print("   ALL 13 MEGA TESTS COMPLETED")
print("=" * 70)
