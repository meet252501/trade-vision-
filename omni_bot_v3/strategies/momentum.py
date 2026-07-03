# omni_bot/strategies/momentum.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from config import (
    MOMENTUM_LOOKBACK_FAST, MOMENTUM_LOOKBACK_MID, 
    MOMENTUM_LOOKBACK_SLOW, MOMENTUM_LOOKBACK_TREND, MOMENTUM_LOOKBACK_MACRO,
    VOLUME_LOOKBACK, ADX_PERIOD, CRYPTO_ADX_THRESHOLD, EQUITY_ADX_THRESHOLD,
    CRYPTO_RECOVERY_ADX, EQUITY_RECOVERY_ADX, STOCKS, CRYPTO, LEVERAGED_ETFS
)

def calculate_adx(prices, period=ADX_PERIOD):
    """
    Simplified ADX (Average Directional Index).
    Measures trend strength: ADX > 20 = trending, ADX < 20 = choppy.
    Uses close-to-close since we don't have high/low data.
    """
    if len(prices) < period * 2:
        return None
    
    # Calculate directional movement from close prices
    up_moves = []
    down_moves = []
    tr_list = []
    
    for i in range(1, len(prices)):
        diff = prices[i] - prices[i-1]
        tr = abs(diff)
        tr_list.append(tr)
        
        if diff > 0:
            up_moves.append(diff)
            down_moves.append(0)
        else:
            up_moves.append(0)
            down_moves.append(abs(diff))
    
    if len(tr_list) < period:
        return None
    
    # Smoothed averages
    smoothed_up = np.mean(up_moves[-period:])
    smoothed_down = np.mean(down_moves[-period:])
    smoothed_tr = np.mean(tr_list[-period:])
    
    if smoothed_tr == 0:
        return 0
    
    di_plus = (smoothed_up / smoothed_tr) * 100
    di_minus = (smoothed_down / smoothed_tr) * 100
    
    di_sum = di_plus + di_minus
    if di_sum == 0:
        return 0
    
    dx = abs(di_plus - di_minus) / di_sum * 100
    return dx

def check_volume_confirmation(bars, lookback=VOLUME_LOOKBACK):
    """
    Returns True if the current volume is above the moving average.
    If volume data is not available, returns True (don't block the trade).
    """
    if len(bars) < lookback:
        return True
    
    volumes = []
    for b in bars[-lookback:]:
        vol = b.get('volume', None)
        if vol is not None:
            volumes.append(float(vol))
    
    if len(volumes) < lookback // 2:
        return True  # Not enough volume data, don't block
    
    avg_volume = np.mean(volumes[:-1]) if len(volumes) > 1 else 0
    current_volume = volumes[-1] if volumes else 0
    
    return current_volume > avg_volume * 0.8  # Allow 80% of average (not too strict)

def generate_signals(universe, market_state, portfolio_state, in_recovery=False, macro_regime=None):
    """
    Generates momentum-based buy/sell/short signals.
    In recovery mode, requires a higher ADX to enter trades.
    Uses macro_regime to block long trades during bear markets.
    """
    signals = []
    
    if macro_regime is None:
        macro_regime = {'stocks': 'bull', 'crypto': 'bull'}
    
    # ═══════════════════════════════════════════════════
    # 1. SELL SIGNALS (Exit Logic)
    # ═══════════════════════════════════════════════════
    for pos in portfolio_state['positions']:
        ticker = pos['ticker']
        if ticker not in universe or ticker not in market_state: 
            continue
            
        bars = market_state[ticker]
        if len(bars) < MOMENTUM_LOOKBACK_TREND: continue
        
        current_price = float(bars[-1]['close'])
        is_short = pos.get('is_short', False)
        
        # Dynamic trailing stop based on asset volatility
        leveraged_etfs = ['TQQQ', 'UPRO', 'SOXL']
        crypto_tickers = ['BTC-USD', 'ETH-USD', 'SOL-USD']
        
        if ticker in leveraged_etfs: base_stop_pct = 0.12
        elif ticker in crypto_tickers: base_stop_pct = 0.10
        else: base_stop_pct = 0.05
        
        # Track best price (high-water mark for longs, low-water mark for shorts)
        if ticker not in portfolio_state.get('best_prices', {}):
            portfolio_state.setdefault('best_prices', {})[ticker] = current_price
            
        best_price = portfolio_state['best_prices'][ticker]
        entry_price = pos['entry_price']
        
        if not is_short:
            # LONG POSITION EXIT
            if current_price > best_price:
                portfolio_state['best_prices'][ticker] = current_price
                best_price = current_price
                
            # Profit-Locking: If up by 1x risk (base_stop_pct), tighten the stop to half distance
            profit_pct = (best_price - entry_price) / entry_price
            stop_pct = base_stop_pct * 0.5 if profit_pct > base_stop_pct else base_stop_pct
                
            if current_price < best_price * (1 - stop_pct):
                signals.append({'ticker': ticker, 'signal': 'sell', 'score': 0})
                continue
        else:
            # SHORT POSITION EXIT
            if current_price < best_price:
                portfolio_state['best_prices'][ticker] = current_price
                best_price = current_price
                
            # Profit-Locking: If short is up by 1x risk
            profit_pct = (entry_price - best_price) / entry_price
            stop_pct = base_stop_pct * 0.5 if profit_pct > base_stop_pct else base_stop_pct
                
            if current_price > best_price * (1 + stop_pct):
                signals.append({'ticker': ticker, 'signal': 'sell', 'score': 0})
                continue
                
        # TIME-BASED STALE TRADE EXIT
        # Momentum trades should move fast. If held for 10 bars without at least 1% profit, cut it.
        current_step = len(bars)
        entry_step = pos.get('entry_step', current_step)
        bars_held = current_step - entry_step
        
        if bars_held >= 10:
            if not is_short and current_price < entry_price * 1.01:
                signals.append({'ticker': ticker, 'signal': 'sell', 'score': 0})
                continue
            elif is_short and current_price > entry_price * 0.99:
                signals.append({'ticker': ticker, 'signal': 'sell', 'score': 0})
                continue
            
        # Check if momentum has completely reversed across MULTIPLE timeframes
        prices = [float(b['close']) for b in bars]
        fast_ret = (prices[-1] / prices[-MOMENTUM_LOOKBACK_FAST]) - 1
        mid_ret = (prices[-1] / prices[-MOMENTUM_LOOKBACK_MID]) - 1
        slow_ret = (prices[-1] / prices[-MOMENTUM_LOOKBACK_SLOW]) - 1
        
        if not is_short:
            # Sell LONG if BOTH fast AND mid AND slow are all negative (strong reversal)
            if fast_ret < 0 and mid_ret < 0 and slow_ret < 0:
                signals.append({'ticker': ticker, 'signal': 'sell', 'score': 0})
        else:
            # Sell SHORT if BOTH fast AND mid AND slow are all positive (strong reversal)
            if fast_ret > 0 and mid_ret > 0 and slow_ret > 0:
                signals.append({'ticker': ticker, 'signal': 'sell', 'score': 0})

    # ═══════════════════════════════════════════════════
    # 2. BUY SIGNALS (Entry Logic)
    # ═══════════════════════════════════════════════════
    buy_candidates = []
    for ticker in universe:
        bars = market_state.get(ticker, [])
        if len(bars) < MOMENTUM_LOOKBACK_TREND + 1: continue
        
        prices = [float(b['close']) for b in bars]
        
        # ── ADX Filter: Is the market actually trending? ──
        adx = calculate_adx(prices)
        is_crypto = ticker in CRYPTO
        
        # Dynamic Threshold Selection based on Asset Class
        if is_crypto:
            current_adx_threshold = CRYPTO_RECOVERY_ADX if in_recovery else CRYPTO_ADX_THRESHOLD
        else:
            current_adx_threshold = EQUITY_RECOVERY_ADX if in_recovery else EQUITY_ADX_THRESHOLD
            
        if adx is not None and adx < current_adx_threshold:
            continue  # Market is too choppy, skip momentum trades
        
        # ── Volume Confirmation ──
        if not check_volume_confirmation(bars):
            continue  # Volume is too low, likely a fake-out
        
        # ── Multi-timeframe Momentum ──
        fast_ret = (prices[-1] / prices[-MOMENTUM_LOOKBACK_FAST]) - 1
        mid_ret = (prices[-1] / prices[-MOMENTUM_LOOKBACK_MID]) - 1
        slow_ret = (prices[-1] / prices[-MOMENTUM_LOOKBACK_SLOW]) - 1
        trend_ret = (prices[-1] / prices[-MOMENTUM_LOOKBACK_TREND]) - 1
        
        # Macro trend (use the longest available data up to MACRO lookback)
        macro_idx = min(MOMENTUM_LOOKBACK_MACRO, len(prices) - 1)
        macro_ret = (prices[-1] / prices[-macro_idx]) - 1 if macro_idx > 0 else 0
        
        # Determine the macro trend for this specific ticker
        macro_is_bear = (is_crypto and macro_regime.get('crypto') == 'bear') or \
                        (not is_crypto and macro_regime.get('stocks') == 'bear')
        
        # BUY LOGIC: Fast, mid, AND slow must all be positive for a strict entry
        if not macro_is_bear and fast_ret > 0 and mid_ret > 0 and slow_ret > 0:
            # Weighted score with bonuses for deeper confirmation
            score = (fast_ret * 0.40) + (mid_ret * 0.30) + (slow_ret * 0.20)
            if trend_ret > 0: score += trend_ret * 0.10
            if score > 0:
                buy_candidates.append({'ticker': ticker, 'signal': 'buy', 'score': score})
                
        # SHORT SELLING LOGIC: If all timeframes are heavily negative, we short!
        # Exclude 3x Leveraged ETFs from shorting due to massive borrowing costs and volatility drag
        if ticker not in LEVERAGED_ETFS:
            # MACRO TREND FILTER: Only short if the macro trend is strictly negative! 
            # This prevents shorting during brief pullbacks in a massive bull market.
            if fast_ret < 0 and mid_ret < 0 and slow_ret < 0 and macro_ret < 0:
                # Calculate negative score (invert so we can sort by most negative)
                score = (abs(fast_ret) * 0.40) + (abs(mid_ret) * 0.30) + (abs(slow_ret) * 0.20)
                if trend_ret < 0: score += abs(trend_ret) * 0.10
                if score > 0:
                    buy_candidates.append({'ticker': ticker, 'signal': 'short', 'score': score})
            
    # Sort by strongest multi-timeframe momentum (either up or down)
    buy_candidates.sort(key=lambda x: x['score'], reverse=True)
    signals.extend(buy_candidates)
    
    return signals
