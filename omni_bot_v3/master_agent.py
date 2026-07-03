# omni_bot/master_agent.py
import numpy as np
from config import (
    STOCKS, CRYPTO, FOREX, ALL_ASSETS,
    MAX_ALLOCATION_PER_TRADE, MAX_PORTFOLIO_POSITIONS,
    MAX_DRAWDOWN_PCT, ABSOLUTE_FLOOR_PCT, COOLDOWN_BARS,
    ATR_PERIOD, ATR_RISK_MULTIPLIER,
    CORRELATION_THRESHOLD, SPREAD_COSTS, DEFAULT_SPREAD,
    RECOVERY_ALLOC_MULT, RECOVERY_ADX_THRESHOLD,
    MACRO_EQUITY_TICKER, MACRO_CRYPTO_TICKER, SCALE_OUT_ATR_MULTIPLIER
)
from strategies import momentum, mean_reversion
from notifier import send_telegram_message
import logging

logger = logging.getLogger("OmniBot")

# ═══════════════════════════════════════════════════════
# PERSISTENT STATE (survives across ticks)
# ═══════════════════════════════════════════════════════
_state = {
    'peak_equity': 0,
    'initial_equity': 0,        # Track starting capital for absolute floor
    'cooldown_remaining': 0,
    'trade_count': 0,
    'in_recovery': False,        # True after a drawdown trigger, until new peak
    'permanently_halted': False,  # True if absolute floor is breached
    'drawdown_count': 0,         # Track how many times circuit breaker has fired
}

def reset_state():
    """Reset internal state between backtest runs."""
    global _state
    _state = {
        'peak_equity': 0,
        'initial_equity': 0,
        'cooldown_remaining': 0,
        'trade_count': 0,
        'in_recovery': False,
        'permanently_halted': False,
        'drawdown_count': 0,
    }

def save_state(filepath="omni_state.json"):
    """Saves the current internal state to disk for persistence across restarts."""
    import json
    try:
        with open(filepath, 'w') as f:
            json.dump(_state, f, indent=4)
    except Exception as e:
        logger.error(f"Failed to save state to {filepath}: {e}")

def load_state(filepath="omni_state.json"):
    """Loads the internal state from disk, if it exists."""
    import json
    import os
    global _state
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r') as f:
                loaded_state = json.load(f)
                _state.update(loaded_state)
            logger.info(f"Successfully loaded Omni-Bot state from {filepath}")
        except Exception as e:
            logger.error(f"Failed to load state from {filepath}: {e}")

def get_spread_cost(ticker):
    """Returns the one-way spread/slippage cost for a ticker."""
    return SPREAD_COSTS.get(ticker, DEFAULT_SPREAD)

def calculate_atr(bars, period=ATR_PERIOD):
    """Calculate Average True Range from price bars."""
    if len(bars) < period + 1:
        return None
    closes = [float(b['close']) for b in bars]
    # Simplified ATR using close-to-close (we don't have high/low)
    returns = [abs(closes[i] - closes[i-1]) for i in range(1, len(closes))]
    if len(returns) < period:
        return None
    atr = np.mean(returns[-period:])
    return atr

def check_correlation(ticker_a, ticker_b, market_state, lookback=20):
    """Check if two assets are too correlated to hold simultaneously."""
    bars_a = market_state.get(ticker_a, [])
    bars_b = market_state.get(ticker_b, [])
    
    if len(bars_a) < lookback or len(bars_b) < lookback:
        return 0.0  # Not enough data, assume uncorrelated
    
    prices_a = [float(b['close']) for b in bars_a[-lookback:]]
    prices_b = [float(b['close']) for b in bars_b[-lookback:]]
    
    # Calculate returns
    returns_a = [(prices_a[i] / prices_a[i-1]) - 1 for i in range(1, len(prices_a))]
    returns_b = [(prices_b[i] / prices_b[i-1]) - 1 for i in range(1, len(prices_b))]
    
    if len(returns_a) < 5 or len(returns_b) < 5:
        return 0.0
    
    # Pearson correlation
    corr = np.corrcoef(returns_a, returns_b)[0, 1]
    return abs(corr) if not np.isnan(corr) else 0.0

def calculate_volatility_adjusted_size(ticker, market_state, base_allocation, buying_power):
    """
    Adjusts position size based on how volatile the asset is.
    More volatile = smaller position. Less volatile = larger position.
    """
    bars = market_state.get(ticker, [])
    atr = calculate_atr(bars)
    
    if atr is None or atr == 0:
        return base_allocation  # Fallback to normal sizing
    
    price = float(bars[-1]['close'])
    atr_pct = atr / price  # ATR as percentage of price
    
    # Normalize: if ATR% is "average" (1%), use full allocation
    # If ATR% is higher, shrink. If lower, grow (but cap at 1.5x).
    avg_atr_pct = 0.01  # 1% is roughly average daily volatility
    volatility_ratio = avg_atr_pct / max(atr_pct, 0.0001)
    volatility_ratio = min(max(volatility_ratio, 0.5), 1.5)  # Clamp between 0.5x and 1.5x
    
    adjusted = base_allocation * volatility_ratio
    return min(adjusted, buying_power)

def decide(market_state, portfolio_state, buying_power):
    """
    The Omni-Bot Master Brain (v2.0 - Upgraded).
    
    New features:
    - Max Drawdown Circuit Breaker
    - Cooldown timer after drawdown
    - Volatility-adjusted position sizing (ATR-based)
    - Correlation filter (diversification enforcement)
    - Spread cost awareness
    """
    global _state
    orders = []
    
    # ═══════════════════════════════════════════════════
    # DRAWDOWN CIRCUIT BREAKER (v3.0 — Triple Protection)
    # ═══════════════════════════════════════════════════
    # Use real (un-leveraged) equity for drawdown calculation
    current_equity = portfolio_state.get('real_equity', portfolio_state.get('total_equity', buying_power))
    
    # Initialize initial equity on first call
    if _state['initial_equity'] == 0:
        _state['initial_equity'] = current_equity
    
    # ── PROTECTION 1: Absolute Floor ──
    # If we've lost more than 25% of INITIAL capital, STOP FOREVER. No recovery attempt.
    if _state['initial_equity'] > 0:
        total_loss = 1 - (current_equity / _state['initial_equity'])
        if total_loss >= ABSOLUTE_FLOOR_PCT:
            if not _state['permanently_halted']:
                _state['permanently_halted'] = True
                # Liquidate everything
                for pos in portfolio_state['positions']:
                    orders.append({'ticker': pos['ticker'], 'side': 'sell', 'quantity': pos['quantity']})
                return orders
    
    # If permanently halted, do nothing ever again
    if _state['permanently_halted']:
        return []
    
    # Track peak equity (high-water mark for the entire account)
    if current_equity > _state['peak_equity']:
        _state['peak_equity'] = current_equity
        # If we hit a new peak, exit recovery mode
        if _state['in_recovery']:
            _state['in_recovery'] = False
    
    # ── PROTECTION 2: Rolling Circuit Breaker ──
    if _state['peak_equity'] > 0:
        drawdown = 1 - (current_equity / _state['peak_equity'])
        if drawdown >= MAX_DRAWDOWN_PCT:
            if _state['drawdown_count'] == 0:
                msg = f"⚠️ <b>DRAWDOWN TRIGGERED</b>\nMax Drawdown of {MAX_DRAWDOWN_PCT*100}% exceeded! Entering {COOLDOWN_BARS} bar cooldown."
                logger.warning(msg)
                send_telegram_message(msg)
            
            # EMERGENCY: Liquidate everything and go to cash
            for pos in portfolio_state['positions']:
                t = pos['ticker']
                side = 'cover' if pos.get('is_short', False) else 'sell'
                orders.append({'ticker': t, 'side': side, 'quantity': pos['quantity']})
                logger.info(f"Liquidating {t} due to drawdown.")

            _state['cooldown_remaining'] = COOLDOWN_BARS
            _state['peak_equity'] = current_equity  # Reset peak so we can trade again after cooldown
            _state['in_recovery'] = True  # Enter recovery mode — trade smaller
            _state['drawdown_count'] += 1
            return orders
    
    # Check cooldown timer
    if _state['cooldown_remaining'] > 0:
        _state['cooldown_remaining'] -= 1
        return []  # Do nothing, we are in cooldown
    
    # ═══════════════════════════════════════════════════
    # ── PROTECTION 4: Scaling Out (Take Partial Profit) ──
    # ═══════════════════════════════════════════════════
    if 'scaled_out' not in _state:
        _state['scaled_out'] = {}
        
    for pos in portfolio_state['positions']:
        t = pos['ticker']
        if t not in _state['scaled_out']:
            _state['scaled_out'][t] = False
            
        if not _state['scaled_out'][t] and t in market_state:
            # Check if profit target is hit (+2 ATR)
            bars = market_state[t]
            atr = calculate_atr(bars)
            if atr and atr > 0:
                current_price = bars[-1]['close']
                entry_price = pos['entry_price']
                
                profit_target = entry_price + (SCALE_OUT_ATR_MULTIPLIER * atr) if not pos.get('is_short', False) else entry_price - (SCALE_OUT_ATR_MULTIPLIER * atr)
                
                # Check if target reached
                if (not pos.get('is_short', False) and current_price >= profit_target) or \
                   (pos.get('is_short', False) and current_price <= profit_target):
                    # Target hit! Scale out 50%
                    scale_qty = pos['quantity'] / 2
                    exit_side = 'cover_half' if pos.get('is_short', False) else 'sell_half'
                    orders.append({'ticker': t, 'side': exit_side, 'quantity': scale_qty})
                    _state['scaled_out'][t] = True
                    
                    msg = f"💰 <b>SCALE OUT</b>\nTaking 50% profit on <b>{t}</b> at {SCALE_OUT_ATR_MULTIPLIER}x ATR."
                    logger.info(msg)
                    send_telegram_message(msg)

    # ═══════════════════════════════════════════════════
    # ── PROTECTION 5: Macro Regime Trend Filter ──
    # ═══════════════════════════════════════════════════
    macro_regime = {'stocks': 'bull', 'crypto': 'bull'}
    
    # Check Equities Macro Trend
    if MACRO_EQUITY_TICKER in market_state and len(market_state[MACRO_EQUITY_TICKER]) >= 60:
        spy_closes = [b['close'] for b in market_state[MACRO_EQUITY_TICKER]]
        spy_sma60 = np.mean(spy_closes[-60:])
        if spy_closes[-1] < spy_sma60:
            macro_regime['stocks'] = 'bear'
            
    # Check Crypto Macro Trend
    if MACRO_CRYPTO_TICKER in market_state and len(market_state[MACRO_CRYPTO_TICKER]) >= 60:
        btc_closes = [b['close'] for b in market_state[MACRO_CRYPTO_TICKER]]
        btc_sma60 = np.mean(btc_closes[-60:])
        if btc_closes[-1] < btc_sma60:
            macro_regime['crypto'] = 'bear'

    # ═══════════════════════════════════════════════════
    # GENERATE SIGNALS FROM STRATEGIES
    # ═══════════════════════════════════════════════════
    all_signals = []
    
    # Route Stocks and Crypto to the Momentum Strategy
    mom_universe = STOCKS + CRYPTO
    mom_signals = momentum.generate_signals(mom_universe, market_state, portfolio_state, in_recovery=_state['in_recovery'], macro_regime=macro_regime)
    all_signals.extend(mom_signals)
    
    # Route Forex to the Mean Reversion Strategy
    mr_signals = mean_reversion.generate_signals(FOREX, market_state, portfolio_state, macro_regime=macro_regime)
    all_signals.extend(mr_signals)
    
    # ═══════════════════════════════════════════════════
    # PROCESS SIGNALS INTO ORDERS
    # ═══════════════════════════════════════════════════
    current_holdings = [p['ticker'] for p in portfolio_state['positions']]
    
    # Clean up scaled_out state for positions that are no longer held
    for t in list(_state['scaled_out'].keys()):
        if t not in current_holdings:
            del _state['scaled_out'][t]
    
    # ── PROTECTION 3: Recovery Mode Scaling ──
    # If in recovery, reduce position size and limit max holdings
    alloc_mult = RECOVERY_ALLOC_MULT if _state['in_recovery'] else 1.0
    max_positions = MAX_PORTFOLIO_POSITIONS - 1 if _state['in_recovery'] else MAX_PORTFOLIO_POSITIONS
    max_positions = max(max_positions, 1)  # Always allow at least 1 position
    
    # Process Sells First (always honor exit signals)
    sells = [s for s in all_signals if s['signal'] == 'sell']
    for s in sells:
        t = s['ticker']
        if t in current_holdings and not any(o['ticker'] == t for o in orders):
            pos = next((p for p in portfolio_state['positions'] if p['ticker'] == t), None)
            if pos:
                # If we are long, we sell to close. If we are short, we buy (cover) to close.
                exit_side = 'cover' if pos.get('is_short', False) else 'sell'
                orders.append({'ticker': t, 'side': exit_side, 'quantity': pos['quantity']})
                current_holdings.remove(t)
                if t in _state['scaled_out']:
                    del _state['scaled_out'][t]
    
    # Process Short signals (with recovery scaling)
    shorts = [s for s in all_signals if s['signal'] == 'short']
    for s in shorts:
        t = s['ticker']
        if t not in current_holdings and not any(o['ticker'] == t for o in orders):
            price = portfolio_state['last_prices'].get(t)
            if not price or price <= 0:
                continue
            
            if len(current_holdings) >= max_positions:
                break
                
            base_val = portfolio_state.get('total_equity', buying_power) * MAX_ALLOCATION_PER_TRADE * alloc_mult
            target_val = calculate_volatility_adjusted_size(t, market_state, base_val, buying_power)
            
            if target_val > 10:
                qty = round(target_val / price, 5)
                if qty > 0:
                    orders.append({'ticker': t, 'side': 'short', 'quantity': qty})
                    buying_power -= (qty * price)
                    current_holdings.append(t)
    
    # Process Buys (Ranked by score, with correlation + volatility filters + recovery scaling)
    buys = [s for s in all_signals if s['signal'] == 'buy']
    buys.sort(key=lambda x: x['score'], reverse=True)
    
    for b in buys:
        t = b['ticker']
        
        if len(current_holdings) >= max_positions:
            break
            
        if t in current_holdings:
            continue
            
        # ── Correlation Filter ──
        # Don't buy if this asset is too correlated with something we already hold
        too_correlated = False
        for held in current_holdings:
            corr = check_correlation(t, held, market_state)
            if corr > CORRELATION_THRESHOLD:
                too_correlated = True
                break
        if too_correlated:
            continue
            
        price = portfolio_state['last_prices'].get(t)
        if not price or price <= 0:
            continue
            
        # ── Volatility-Adjusted Position Sizing (with recovery scaling) ──
        base_val = portfolio_state.get('total_equity', buying_power) * MAX_ALLOCATION_PER_TRADE * alloc_mult
        target_val = calculate_volatility_adjusted_size(t, market_state, base_val, buying_power)
        target_val = min(target_val, buying_power)
        
        if target_val > 10:
            if t in FOREX or t in CRYPTO:
                qty = round(target_val / price, 5)
            else:
                qty = int(target_val / price)
                
            if qty > 0:
                orders.append({'ticker': t, 'side': 'buy', 'quantity': qty})
                buying_power -= (qty * price)
                current_holdings.append(t)
                _state['trade_count'] += 1
                msg = f"🔔 <b>NEW TRADE</b>\n{side.upper()} <b>{t}</b>\nScore: {score:.2f}\nQty: {qty:.4f}"
            logger.info(msg)
            send_telegram_message(msg)
            
    return orders
