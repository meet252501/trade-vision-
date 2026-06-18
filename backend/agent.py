"""
TradeVision AI — agent.py (V3 — ELITE)
Strategy: Dual Momentum + Volatility Targeting + SPY Risk-Off
         + Multi-Lookback + Hysteresis + Skip-Month + Emergency Exits
         + ATR Trailing Stop + Momentum Acceleration + Vol Regime

Author: Meet | June 2026
Targets: Calmar > 4.0 | Max Drawdown < 8% | Ann Return > 18%

V3 UPGRADES (from web research):
  9. ATR-based trailing stop (adapts to market volatility)
  10. Momentum acceleration filter (reject decelerating trends)
  11. Volatility regime sizing (reduce exposure in high-vol regimes)
"""
import numpy as np

# ■■ Configuration ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
UNIVERSE     = ['SPY', 'QQQ', 'IWM', 'XLK', 'XLF', 'XLE', 'XLV', 'GLD', 'TLT', 'SMH']
LOOKBACKS    = [42, 63, 126]   # 2-month, 3-month, 6-month momentum blend (faster)
SKIP_DAYS    = 10              # Skip most recent 10 days (reduced from 21)
LOOKBACK_VOL = 20              # 20-day volatility window
TOP_N        = 4               # Hold top N assets (broader diversification)
MAX_POS      = 0.25            # Max 25% per position (gives 5% buffer against 30% rule)
TARGET_VOL   = 0.15            # Target 15% annualized portfolio volatility
SMA_LONG     = 200             # SPY SMA period for risk-off switch
SMA_SHORT    = 50              # SPY SMA-50 for re-entry confirmation
HYSTERESIS   = 0.02            # 2% buffer band around SMA-200 (wider to prevent whipsaw)
REBAL_DAYS   = 15              # Rebalance every ~15 trading days (bi-monthly)
EMERGENCY_DD = 0.07            # Emergency exit if position drops 7% from entry
PORT_DD_TRIG = 0.04            # Force rebalance if portfolio drawdown > 4%
ATR_PERIOD   = 14              # ATR lookback for trailing stop
ATR_MULT     = 3.0             # ATR multiplier for trail distance (wider = fewer false exits)
VOL_HIGH_THR = 0.30            # If SPY 20d vol > 30% ann, we're in high-vol regime
MOM_ACCEL_LB = 21              # Compare recent 21d mom vs prior 21d mom

# Momentum weight distribution for top N (rank-proportional)
MOM_WEIGHTS  = [0.35, 0.28, 0.22, 0.15]  # #1→35%, #2→28%, #3→22%, #4→15%

# ■■ State (persists across calls via mutable default) ■■■■■■■■
_state = {
    'day_count': 0,
    'is_risk_off': False,      # Track regime to apply hysteresis
    'last_rebal_day': -999,    # Track last rebalance day
    'peak_equity': 0,          # Track portfolio peak for DD detection
    'entry_prices': {},        # Track entry prices for emergency exits
    'trail_highs': {},         # ATR trailing stop: track per-ticker highs
}


def decide(market_state: dict, portfolio_state: dict, cash: float) -> list:
    """
    Called once per trading day by Builderr.ai engine.
    Returns list of orders: [{'ticker': str, 'side': 'buy'|'sell', 'quantity': int}]
    """
    orders = []
    _state['day_count'] += 1
    day = _state['day_count']

    prices = portfolio_state.get('last_prices', {})
    positions = portfolio_state.get('positions', [])
    pos_map = {p['ticker']: p for p in positions}

    # ■■ Helper: get close series ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
    def closes(ticker, n=None):
        bars = market_state.get(ticker, [])
        c = [b['close'] for b in bars]
        return c[-n:] if n else c

    # ■■ Equity calculation ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
    def equity():
        pos_val = sum(p['quantity'] * prices.get(p['ticker'], 0) for p in positions)
        return cash + pos_val

    current_equity = equity()

    # Track portfolio peak for conditional rebalance
    if current_equity > _state['peak_equity']:
        _state['peak_equity'] = current_equity

    # ■■ STEP 1: SPY RISK-OFF SWITCH (with hysteresis) ■■■■■■■■■
    # Uses 1% buffer band to prevent whipsaw around SMA-200
    spy_c = closes('SPY')
    risk_off_triggered = False

    if len(spy_c) >= SMA_LONG:
        sma200 = np.mean(spy_c[-SMA_LONG:])
        current_spy = spy_c[-1]

        if _state['is_risk_off']:
            # Currently risk-off: need BOTH conditions to go risk-on again
            # 1) SPY must be above SMA-200 by hysteresis margin
            # 2) SMA-50 must also be above SMA-200 (dual confirmation)
            above_with_buffer = current_spy > sma200 * (1 + HYSTERESIS)

            sma50_confirm = True
            if len(spy_c) >= SMA_SHORT:
                sma50 = np.mean(spy_c[-SMA_SHORT:])
                sma50_confirm = sma50 > sma200  # Golden cross confirmation

            if above_with_buffer and sma50_confirm:
                _state['is_risk_off'] = False
                # Will enter positions at next rebalance
            else:
                risk_off_triggered = True
        else:
            # Currently risk-on: trigger risk-off with buffer below SMA-200
            if current_spy < sma200 * (1 - HYSTERESIS):
                _state['is_risk_off'] = True
                risk_off_triggered = True

    if risk_off_triggered:
        # Market is in downtrend — liquidate ALL positions
        for pos in positions:
            orders.append({
                'ticker': pos['ticker'],
                'side': 'sell',
                'quantity': pos['quantity']
            })
        _state['entry_prices'] = {}
        _state['peak_equity'] = cash  # Reset peak after liquidation
        return orders

    # ■■ STEP 2: ATR TRAILING STOP + EMERGENCY EXITS ■■■■■■■■■■■
    # Combines fixed 5% stop with adaptive ATR trail (from web research)
    for pos in positions:
        ticker = pos['ticker']
        current_price = prices.get(ticker, 0)
        entry_price = _state['entry_prices'].get(ticker, current_price)

        if entry_price > 0 and current_price > 0:
            # Track per-position high watermark for trailing stop
            prev_high = _state['trail_highs'].get(ticker, current_price)
            if current_price > prev_high:
                _state['trail_highs'][ticker] = current_price
                prev_high = current_price

            # ATR-based trailing stop (adaptive to volatility)
            c = closes(ticker)
            atr_stop_hit = False
            if len(c) >= ATR_PERIOD + 1:
                # Calculate ATR (average true range)
                highs = [b.get('high', b['close']) for b in market_state.get(ticker, [])]
                lows = [b.get('low', b['close']) for b in market_state.get(ticker, [])]
                closes_arr = c
                if len(highs) >= ATR_PERIOD + 1 and len(lows) >= ATR_PERIOD + 1:
                    true_ranges = []
                    for i in range(-ATR_PERIOD, 0):
                        h = highs[i] if i < len(highs) else closes_arr[i]
                        l = lows[i] if i < len(lows) else closes_arr[i]
                        prev_c = closes_arr[i - 1]
                        tr = max(h - l, abs(h - prev_c), abs(l - prev_c))
                        true_ranges.append(tr)
                    if true_ranges:
                        atr = np.mean(true_ranges)
                        trail_level = prev_high - (atr * ATR_MULT)
                        if current_price < trail_level:
                            atr_stop_hit = True

            # Fixed emergency exit (5% from entry) OR ATR trail hit
            loss_pct = (current_price - entry_price) / entry_price
            if loss_pct < -EMERGENCY_DD or atr_stop_hit:
                orders.append({
                    'ticker': ticker,
                    'side': 'sell',
                    'quantity': pos['quantity']
                })
                _state['entry_prices'].pop(ticker, None)
                _state['trail_highs'].pop(ticker, None)

    # If emergency exits happened, return those orders now
    if orders:
        return orders

    # ■■ STEP 3: DETERMINE IF REBALANCE IS NEEDED ■■■■■■■■■■■■■
    days_since_rebal = day - _state['last_rebal_day']
    is_scheduled_rebal = days_since_rebal >= REBAL_DAYS

    # Conditional rebalance: portfolio drawdown > 3% from peak
    portfolio_dd = 0
    if _state['peak_equity'] > 0:
        portfolio_dd = (_state['peak_equity'] - current_equity) / _state['peak_equity']
    is_emergency_rebal = portfolio_dd > PORT_DD_TRIG and days_since_rebal >= 5

    if not (is_scheduled_rebal or is_emergency_rebal):
        return []  # Not rebalance time — do nothing

    _state['last_rebal_day'] = day

    # ■■ STEP 4: MULTI-LOOKBACK MOMENTUM SCORING ■■■■■■■■■■■■■■
    # Blend 3-month, 6-month, and 12-month momentum (skip last month)
    momentum = {}
    volatility = {}

    for ticker in UNIVERSE:
        c = closes(ticker)

        # Need enough data for longest lookback + skip period
        if len(c) < max(LOOKBACKS) + SKIP_DAYS + 5:
            continue

        # Multi-lookback blended momentum (skip last 21 days)
        mom_scores = []
        for lb in LOOKBACKS:
            if len(c) >= lb + SKIP_DAYS:
                # Skip-month: compare price 21 days ago vs (lookback + 21) days ago
                recent_price = c[-(SKIP_DAYS + 1)]     # Price 21 trading days ago
                lookback_price = c[-(lb + SKIP_DAYS)]   # Price (lookback + 21) days ago
                if lookback_price > 0:
                    ret = (recent_price - lookback_price) / lookback_price
                    mom_scores.append(ret)

        if not mom_scores:
            continue

        # Average of all lookback returns (blended momentum)
        avg_momentum = np.mean(mom_scores)

        # Absolute momentum filter: only positive momentum (beats cash)
        if avg_momentum <= 0:
            continue

        # 20-day annualized volatility
        daily_rets = np.diff(c[-LOOKBACK_VOL - 1:]) / np.array(c[-LOOKBACK_VOL - 1:-1])
        if len(daily_rets) < LOOKBACK_VOL:
            continue
        ann_vol = float(np.std(daily_rets)) * np.sqrt(252)
        if ann_vol <= 0.001:
            continue

        momentum[ticker] = avg_momentum
        volatility[ticker] = ann_vol

    # ■■ STEP 4b: MOMENTUM ACCELERATION FILTER ■■■■■■■■■■■■■■■■■
    # Reject assets where momentum is decelerating (web research)
    filtered_momentum = {}
    for ticker, mom in momentum.items():
        c = closes(ticker)
        if len(c) >= 2 * MOM_ACCEL_LB + SKIP_DAYS:
            # Recent 21d momentum vs prior 21d momentum
            recent_end = c[-(SKIP_DAYS + 1)]
            recent_start = c[-(SKIP_DAYS + MOM_ACCEL_LB)]
            prior_end = c[-(SKIP_DAYS + MOM_ACCEL_LB)]
            prior_start = c[-(SKIP_DAYS + 2 * MOM_ACCEL_LB)]
            if recent_start > 0 and prior_start > 0:
                recent_mom = (recent_end - recent_start) / recent_start
                prior_mom = (prior_end - prior_start) / prior_start
                # Accept if recent momentum >= 50% of prior (not fully crashed)
                if recent_mom >= prior_mom * 0.5:
                    filtered_momentum[ticker] = mom
                # Still accept if overall momentum is very strong
                elif mom > 0.15:
                    filtered_momentum[ticker] = mom
            else:
                filtered_momentum[ticker] = mom
        else:
            filtered_momentum[ticker] = mom
    momentum = filtered_momentum if filtered_momentum else momentum

    # ■■ STEP 5: SELECT TOP N ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
    if not momentum:
        # No asset has positive blended momentum — go to cash
        for pos in positions:
            orders.append({
                'ticker': pos['ticker'],
                'side': 'sell',
                'quantity': pos['quantity']
            })
        _state['entry_prices'] = {}
        return orders

    ranked = sorted(momentum, key=momentum.get, reverse=True)
    top_n = ranked[:TOP_N]

    # ■■ STEP 6: MOMENTUM-WEIGHTED + VOL-ADJUSTED SIZING ■■■■■■■
    # Step A: Assign rank-based weights (40/35/25 for top 3)
    rank_weights = {}
    for i, t in enumerate(top_n):
        if i < len(MOM_WEIGHTS):
            rank_weights[t] = MOM_WEIGHTS[i]
        else:
            rank_weights[t] = 1.0 / len(top_n)

    # Step B: Adjust by inverse volatility
    inv_vols = {t: 1.0 / volatility[t] for t in top_n}
    total_inv = sum(inv_vols.values())
    vol_weights = {t: inv_vols[t] / total_inv for t in top_n}

    # Step C: Blend rank-weights with vol-weights (50/50)
    raw_weights = {t: 0.5 * rank_weights[t] + 0.5 * vol_weights[t] for t in top_n}

    # Normalize to sum to 1
    total_raw = sum(raw_weights.values())
    if total_raw > 0:
        raw_weights = {t: w / total_raw for t, w in raw_weights.items()}

    # Step D: Scale to target volatility
    port_vol_est = sum(raw_weights[t] * volatility[t] for t in top_n)
    vol_scalar = min(TARGET_VOL / port_vol_est, 1.5) if port_vol_est > 0 else 1.0

    # Step E: Volatility regime adjustment (from web research)
    # If SPY is in a high-vol regime, scale down exposure
    spy_vol_regime = 1.0
    if len(spy_c) >= LOOKBACK_VOL + 1:
        spy_rets = np.diff(spy_c[-LOOKBACK_VOL - 1:]) / np.array(spy_c[-LOOKBACK_VOL - 1:-1])
        spy_ann_vol = float(np.std(spy_rets)) * np.sqrt(252)
        if spy_ann_vol > VOL_HIGH_THR:
            # Scale down: if vol is 30% vs threshold 25%, factor = 25/30 = 0.83
            spy_vol_regime = min(VOL_HIGH_THR / spy_ann_vol, 1.0)

    # Step F: Final weights capped at MAX_POS, adjusted for vol regime
    final_weights = {t: min(raw_weights[t] * vol_scalar * spy_vol_regime, MAX_POS) for t in top_n}

    # ■■ STEP 7: SELL POSITIONS NOT IN TOP N ■■■■■■■■■■■■■■■■■■
    for pos in positions:
        if pos['ticker'] not in top_n:
            orders.append({
                'ticker': pos['ticker'],
                'side': 'sell',
                'quantity': pos['quantity']
            })
            _state['entry_prices'].pop(pos['ticker'], None)

    # ■■ STEP 8: BUY TOP N WITH CORRECT SIZING ■■■■■■■■■■■■■■■■
    total_equity = equity()

    for ticker in top_n:
        target_val = total_equity * final_weights[ticker]
        price = prices.get(ticker, 0)
        if price <= 0:
            continue

        target_qty = int(target_val / price)
        current_qty = pos_map.get(ticker, {}).get('quantity', 0)
        diff_qty = target_qty - current_qty

        if diff_qty > 0 and cash >= diff_qty * price:
            orders.append({
                'ticker': ticker,
                'side': 'buy',
                'quantity': diff_qty
            })
            cash -= diff_qty * price
            # Track entry price for emergency exit
            if ticker not in _state['entry_prices']:
                _state['entry_prices'][ticker] = price
            else:
                # Weighted average entry
                old_qty = current_qty
                old_entry = _state['entry_prices'][ticker]
                new_qty = old_qty + diff_qty
                if new_qty > 0:
                    _state['entry_prices'][ticker] = (
                        (old_qty * old_entry + diff_qty * price) / new_qty
                    )
        elif diff_qty < 0:
            orders.append({
                'ticker': ticker,
                'side': 'sell',
                'quantity': abs(diff_qty)
            })

    # Reset peak after rebalance
    _state['peak_equity'] = equity()

    return orders
