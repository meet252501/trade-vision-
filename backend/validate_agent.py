"""
validate_agent.py — Comprehensive V3 Agent Validation Harness
===============================================================
Tests agent.py against REAL Yahoo Finance data across multiple
market regimes to verify contest-readiness.

Tests:
  1. Bull market:  2023-01-01 → 2023-12-31
  2. Bear market:  2022-01-01 → 2022-12-31
  3. COVID crash:  2020-01-01 → 2020-12-31
  4. Recovery:     2020-06-01 → 2021-06-01
  5. Full cycle:   2019-01-01 → 2024-01-01
  6. Constraint validation (leverage, position size, execution time)

Usage: python validate_agent.py
"""

import sys
import os
import time
import importlib
import copy
import traceback

# Add parent for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np

# Import our modules
from data import fetch_prices
from metrics import calc_metrics

# ═══════════════════════════════════════════════════════
#  CONFIGURATION
# ═══════════════════════════════════════════════════════
UNIVERSE = ['SPY', 'QQQ', 'IWM', 'XLK', 'XLF', 'XLE', 'XLV', 'GLD', 'TLT']
INITIAL_CASH = 100000

# Contest constraints
MAX_LEVERAGE = 1.5
MAX_POS_PCT  = 0.30
MAX_EXEC_TIME_SEC = 5.0
MAX_TRADES_PER_DAY = 50

SCENARIOS = [
    # (name, data_start, test_start, test_end)
    # data_start is 18 months before test_start to warm up lookbacks
    ("Bull 2023",      "2021-07-01", "2023-01-01", "2023-12-31"),
    ("Bear 2022",      "2020-07-01", "2022-01-01", "2022-12-31"),
    ("COVID Crash",    "2018-07-01", "2020-01-01", "2020-12-31"),
    ("Recovery Rally", "2019-01-01", "2020-06-01", "2021-06-01"),
    ("Full Cycle 5Y",  "2017-01-01", "2019-01-01", "2024-01-01"),
]

# ═══════════════════════════════════════════════════════
#  AGENT LOADER (fresh state per scenario)
# ═══════════════════════════════════════════════════════
def load_agent_fresh():
    """Reimport agent.py with fresh state each time."""
    # Remove cached module
    if 'agent' in sys.modules:
        del sys.modules['agent']
    
    import agent
    # Reset mutable state
    agent._state = {
        'day_count': 0,
        'is_risk_off': False,
        'last_rebal_day': -999,
        'peak_equity': 0,
        'entry_prices': {},
        'trail_highs': {},
    }
    return agent.decide


# ═══════════════════════════════════════════════════════
#  CORE SIMULATION (mirrors Builderr.ai engine)
# ═══════════════════════════════════════════════════════
def simulate(prices_raw, decide_fn, initial_cash):
    """
    Run the agent through historical data, mimicking the Builderr.ai
    evaluation loop exactly.
    """
    # Build aligned date index
    all_dates = set()
    ticker_bars = {}
    
    for ticker, bars in prices_raw.items():
        if isinstance(bars, dict) and 'error' in bars:
            continue
        ticker_bars[ticker] = {b['ts']: b for b in bars}
        all_dates.update(b['ts'] for b in bars)
    
    if not all_dates:
        return None
    
    sorted_dates = sorted(all_dates)
    
    cash = initial_cash
    positions = {}
    equity_curve = []
    trades = []
    constraint_violations = []
    exec_times = []
    
    for day_idx, date in enumerate(sorted_dates):
        # Build market_state (all history up to today)
        market_state = {}
        last_prices = {}
        
        for ticker, bars_by_date in ticker_bars.items():
            historical_bars = []
            for d in sorted_dates[:day_idx + 1]:
                if d in bars_by_date:
                    historical_bars.append(bars_by_date[d])
            if historical_bars:
                market_state[ticker] = historical_bars
                last_prices[ticker] = historical_bars[-1]['close']
        
        # Build portfolio_state
        position_list = [
            {'ticker': t, 'quantity': p['quantity'], 'avg_price': p['avg_price']}
            for t, p in positions.items()
        ]
        portfolio_state = {
            'positions': position_list,
            'last_prices': last_prices,
        }
        
        # ─── Call decide() and time it ───
        t0 = time.perf_counter()
        try:
            orders = decide_fn(market_state, portfolio_state, cash)
        except Exception as e:
            orders = []
            constraint_violations.append(f"[{date}] decide() CRASHED: {e}")
        elapsed = time.perf_counter() - t0
        exec_times.append(elapsed)
        
        # ─── Constraint: execution time ───
        if elapsed > MAX_EXEC_TIME_SEC:
            constraint_violations.append(
                f"[{date}] Execution time {elapsed:.2f}s > {MAX_EXEC_TIME_SEC}s limit"
            )
        
        # ─── Constraint: max trades per day ───
        if len(orders) > MAX_TRADES_PER_DAY:
            constraint_violations.append(
                f"[{date}] {len(orders)} trades > {MAX_TRADES_PER_DAY} limit"
            )
        
        # ─── Execute orders ───
        day_trades = 0
        for order in (orders or []):
            ticker = order.get('ticker', '')
            side = order.get('side', '')
            qty = order.get('quantity', 0)
            price = last_prices.get(ticker, 0)
            
            if price <= 0 or qty <= 0:
                continue
            
            if side == 'buy':
                cost = qty * price
                if cost <= cash:
                    cash -= cost
                    if ticker in positions:
                        old = positions[ticker]
                        total_qty = old['quantity'] + qty
                        avg = (old['quantity'] * old['avg_price'] + cost) / total_qty
                        positions[ticker] = {'quantity': total_qty, 'avg_price': avg}
                    else:
                        positions[ticker] = {'quantity': qty, 'avg_price': price}
                    day_trades += 1
            
            elif side == 'sell':
                if ticker in positions:
                    actual_qty = min(qty, positions[ticker]['quantity'])
                    revenue = actual_qty * price
                    cash += revenue
                    positions[ticker]['quantity'] -= actual_qty
                    if positions[ticker]['quantity'] <= 0:
                        del positions[ticker]
                    day_trades += 1
        
        # ─── Calculate portfolio value ───
        portfolio_value = cash
        for ticker, pos in positions.items():
            portfolio_value += pos['quantity'] * last_prices.get(ticker, 0)
        
        # ─── Constraint: position size & leverage ───
        if portfolio_value > 0:
            for ticker, pos in positions.items():
                pos_val = pos['quantity'] * last_prices.get(ticker, 0)
                pos_pct = pos_val / portfolio_value
                if pos_pct > MAX_POS_PCT + 0.01:  # Small tolerance
                    constraint_violations.append(
                        f"[{date}] {ticker} position {pos_pct:.1%} > {MAX_POS_PCT:.0%} limit"
                    )
            
            total_invested = portfolio_value - cash
            leverage = total_invested / portfolio_value if portfolio_value > 0 else 0
            if leverage > MAX_LEVERAGE + 0.01:
                constraint_violations.append(
                    f"[{date}] Leverage {leverage:.2f}x > {MAX_LEVERAGE}x limit"
                )
        
        equity_curve.append(round(portfolio_value, 2))
        trades.append(day_trades)
    
    return {
        'equity_curve': equity_curve,
        'dates': sorted_dates,
        'total_trades': sum(trades),
        'constraint_violations': constraint_violations,
        'exec_times': exec_times,
        'final_cash': cash,
        'final_positions': positions,
    }


# ═══════════════════════════════════════════════════════
#  MAIN VALIDATION
# ═══════════════════════════════════════════════════════
def run_validation():
    print("=" * 70)
    print("  TradeVision AI — V3 Elite Agent Validation Harness")
    print("  Testing against REAL Yahoo Finance historical data")
    print("=" * 70)
    print()
    
    results = []
    all_violations = []
    
    for scenario_name, data_start, test_start, test_end in SCENARIOS:
        print(f"━━━ {scenario_name} ({test_start} → {test_end}) ━━━")
        print(f"  Fetching real market data from Yahoo Finance...")
        print(f"  (Data warmup from {data_start} for lookback history)")
        
        # Fetch real data — starting from data_start to give lookback warmup
        try:
            prices_raw = fetch_prices(UNIVERSE, start=data_start, end=test_end)
        except Exception as e:
            print(f"  ❌ Data fetch FAILED: {e}")
            print()
            continue
        
        # Count available tickers
        valid_tickers = [t for t, v in prices_raw.items() if not isinstance(v, dict) or 'error' not in v]
        total_bars = sum(len(v) for v in prices_raw.values() if isinstance(v, list))
        print(f"  Loaded {len(valid_tickers)}/{len(UNIVERSE)} tickers ({total_bars} total bars)")
        
        if len(valid_tickers) < 3:
            print(f"  ❌ Insufficient data — skipping")
            print()
            continue
        
        # Load fresh agent
        decide_fn = load_agent_fresh()
        
        # Run simulation
        print(f"  Running {scenario_name} simulation...")
        sim = simulate(prices_raw, decide_fn, INITIAL_CASH)
        
        if sim is None:
            print(f"  ❌ Simulation returned no results")
            print()
            continue
        
        # Slice results to only the TEST period (exclude warmup)
        test_indices = [i for i, d in enumerate(sim['dates']) if d >= test_start]
        if not test_indices:
            print(f"  ❌ No test-period dates found")
            print()
            continue
        
        test_equity = [sim['equity_curve'][i] for i in test_indices]
        test_exec = [sim['exec_times'][i] for i in test_indices]
        
        # Compute metrics on test period only
        metrics = calc_metrics(test_equity)
        
        # Execution time stats
        exec_arr = np.array(test_exec)
        avg_exec = exec_arr.mean() * 1000  # Convert to ms
        max_exec = exec_arr.max() * 1000
        p99_exec = np.percentile(exec_arr, 99) * 1000
        
        # Results
        print(f"  ┌─────────────────────────────────────────┐")
        print(f"  │ Total Return:    {metrics['total_return_pct']:>+8.2f}%              │")
        print(f"  │ Ann. Return:     {metrics['ann_return_pct']:>+8.2f}%              │")
        print(f"  │ Max Drawdown:    {metrics['max_drawdown_pct']:>8.2f}%              │")
        print(f"  │ Calmar Ratio:    {metrics['calmar_ratio']:>8.3f}               │")
        print(f"  │ Sharpe Ratio:    {metrics['sharpe_ratio']:>8.3f}               │")
        print(f"  │ Sortino Ratio:   {metrics['sortino_ratio']:>8.3f}               │")
        print(f"  │ Win Rate:        {metrics['win_rate_pct']:>8.2f}%              │")
        print(f"  │ Profit Factor:   {metrics['profit_factor']:>8.3f}               │")
        print(f"  │ Volatility:      {metrics['volatility_pct']:>8.2f}%              │")
        print(f"  │ Total Trades:    {sim['total_trades']:>8d}               │")
        print(f"  │ Avg Exec Time:   {avg_exec:>7.2f}ms               │")
        print(f"  │ Max Exec Time:   {max_exec:>7.2f}ms               │")
        print(f"  │ P99 Exec Time:   {p99_exec:>7.2f}ms               │")
        print(f"  └─────────────────────────────────────────┘")
        
        # Constraint violations
        violations = sim['constraint_violations']
        if violations:
            print(f"  ⚠️  {len(violations)} CONSTRAINT VIOLATIONS:")
            for v in violations[:5]:
                print(f"     → {v}")
            if len(violations) > 5:
                print(f"     ... and {len(violations) - 5} more")
            all_violations.extend(violations)
        else:
            print(f"  ✅ All contest constraints satisfied")
        
        # Grade the Calmar
        calmar = metrics['calmar_ratio']
        if calmar >= 4.0:
            grade = "🏆 ELITE"
        elif calmar >= 3.0:
            grade = "🥇 EXCELLENT"
        elif calmar >= 2.0:
            grade = "🥈 STRONG"
        elif calmar >= 1.0:
            grade = "🥉 GOOD"
        elif calmar >= 0:
            grade = "⚡ ACCEPTABLE"
        else:
            grade = "❌ NEGATIVE"
        print(f"  Grade: {grade} (Calmar {calmar:.3f})")
        
        results.append({
            'scenario': scenario_name,
            'metrics': metrics,
            'violations': len(violations),
            'trades': sim['total_trades'],
            'exec_ms': avg_exec,
        })
        print()
    
    # ═══════════════════════════════════════════════════
    #  FINAL SCOREBOARD
    # ═══════════════════════════════════════════════════
    if results:
        print("=" * 70)
        print("  FINAL SCOREBOARD")
        print("=" * 70)
        print(f"  {'Scenario':<18} {'Return':>9} {'MaxDD':>8} {'Calmar':>8} {'Sharpe':>8} {'Trades':>7}")
        print(f"  {'─' * 18} {'─' * 9} {'─' * 8} {'─' * 8} {'─' * 8} {'─' * 7}")
        
        calmars = []
        for r in results:
            m = r['metrics']
            print(f"  {r['scenario']:<18} {m['total_return_pct']:>+8.2f}% {m['max_drawdown_pct']:>7.2f}% {m['calmar_ratio']:>8.3f} {m['sharpe_ratio']:>8.3f} {r['trades']:>7d}")
            calmars.append(m['calmar_ratio'])
        
        print(f"  {'─' * 18} {'─' * 9} {'─' * 8} {'─' * 8} {'─' * 8} {'─' * 7}")
        avg_calmar = np.mean(calmars)
        min_calmar = min(calmars)
        print(f"  {'AVG Calmar:':<18} {'':>9} {'':>8} {avg_calmar:>8.3f}")
        print(f"  {'WORST Calmar:':<18} {'':>9} {'':>8} {min_calmar:>8.3f}")
        print()
        
        # Overall verdict
        total_violations = sum(r['violations'] for r in results)
        if total_violations == 0:
            print("  ✅ CONTEST CONSTRAINTS: ALL PASSED")
        else:
            print(f"  ⚠️  CONTEST CONSTRAINTS: {total_violations} VIOLATIONS FOUND")
        
        if avg_calmar >= 3.0 and min_calmar >= 1.0 and total_violations == 0:
            print("  🏆 VERDICT: READY FOR SUBMISSION")
        elif avg_calmar >= 1.5 and min_calmar >= 0 and total_violations == 0:
            print("  🥈 VERDICT: COMPETITIVE — consider further optimization")
        elif total_violations > 0:
            print("  ❌ VERDICT: FIX CONSTRAINT VIOLATIONS before submitting")
        else:
            print("  ⚡ VERDICT: NEEDS WORK — review strategy parameters")
        
        print()
    else:
        print("❌ No scenarios completed. Check your internet connection and yfinance install.")
    
    print("=" * 70)


if __name__ == "__main__":
    run_validation()
