# omni_bot/strategies/mean_reversion.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from config import (
    RSI_PERIOD, BB_PERIOD, BB_STD,
    RSI_OVERSOLD, RSI_OVERBOUGHT,
    BB_SQUEEZE_THRESHOLD, MR_STOP_LOSS
)

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss.replace(0, 1e-10)
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_indicators(history_df):
    df = history_df.copy()
    if len(df) < BB_PERIOD:
        df['rsi'] = 50
        df['bb_upper'] = df['close'] * 1.1
        df['bb_lower'] = df['close'] * 0.9
        df['sma'] = df['close']
        df['bb_width'] = 0.1
        return df

    df['rsi'] = calculate_rsi(df['close'], RSI_PERIOD)
    df['sma'] = df['close'].rolling(window=BB_PERIOD).mean()
    df['std'] = df['close'].rolling(window=BB_PERIOD).std()
    df['bb_upper'] = df['sma'] + (BB_STD * df['std'])
    df['bb_lower'] = df['sma'] - (BB_STD * df['std'])
    # Bollinger Band Width (for squeeze detection)
    df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['sma']
    return df

def is_squeeze(df):
    """
    Detects if the Bollinger Bands are in a "squeeze" (very narrow).
    During a squeeze, mean reversion signals are unreliable.
    """
    if len(df) < 2:
        return False
    current_width = df.iloc[-1].get('bb_width', 1.0)
    if pd.isna(current_width):
        return False
    return current_width < BB_SQUEEZE_THRESHOLD

def generate_signals(universe, market_state, portfolio_state, macro_regime=None):
    """
    Generates mean reversion buy/sell signals for range-bound assets (Forex).
    
    Upgrades (v2.0):
    - Uses Bollinger Bands to identify extremes
    - Combines RSI with BB for double-confirmation
    """
    signals = []
    
    if macro_regime is None:
        macro_regime = {'stocks': 'bull', 'crypto': 'bull'}
    
    # ═══════════════════════════════════════════════════
    # 1. EXIT LOGIC (Take Profit / Stop Loss)
    # ═══════════════════════════════════════════════════
    for pos in portfolio_state['positions']:
        ticker = pos['ticker']
        if ticker not in universe or ticker not in market_state: continue
        
        bars = market_state[ticker]
        if len(bars) < BB_PERIOD: continue
        
        df = pd.DataFrame(bars)
        df['close'] = df['close'].astype(float)
        df = calculate_indicators(df)
        
        current_price = df.iloc[-1]['close']
        sma = df.iloc[-1]['sma']
        bb_upper = df.iloc[-1]['bb_upper']
        bb_lower = df.iloc[-1]['bb_lower']
        
        entry_price = pos['entry_price']
        is_short = pos.get('is_short', False)
        
        if is_short:
            # Short position exit logic
            profit_pct = (entry_price / current_price) - 1  # Inverted for shorts
            
            # Take profit: Price dropped to lower Bollinger Band, or we have profit and price is back to SMA
            if current_price <= bb_lower or (profit_pct > 0.005 and current_price <= sma) or profit_pct < -MR_STOP_LOSS:
                signals.append({'ticker': ticker, 'signal': 'sell', 'score': 0})
        else:
            # Long position exit logic
            profit_pct = (current_price / entry_price) - 1
            
            # Take profit at upper BB, or if we have profit and price returned to SMA
            # Stop loss at configured threshold
            if current_price >= bb_upper or (profit_pct > 0.005 and current_price >= sma) or profit_pct < -MR_STOP_LOSS:
                signals.append({'ticker': ticker, 'signal': 'sell', 'score': 0})
            
    # ═══════════════════════════════════════════════════
    # 2. ENTRY LOGIC (Buy Oversold / Short Overbought)
    # ═══════════════════════════════════════════════════
    for ticker in universe:
        bars = market_state.get(ticker, [])
        if len(bars) < BB_PERIOD: continue
        
        df = pd.DataFrame(bars)
        df['close'] = df['close'].astype(float)
        df = calculate_indicators(df)
        
        # ── Squeeze Detection ──
        if is_squeeze(df):
            continue  # Bands are too narrow, signals are unreliable
        
        current_row = df.iloc[-1]
        current_price = current_row['close']
        rsi = current_row['rsi']
        bb_lower = current_row['bb_lower']
        bb_upper = current_row['bb_upper']
        
        if pd.isna(rsi) or pd.isna(bb_lower) or pd.isna(bb_upper):
            continue
        
        # ── BUY: Severely Oversold ──
        if rsi < RSI_OVERSOLD and current_price < bb_lower:
            score = 100 - rsi  # Lower RSI = higher score
            signals.append({'ticker': ticker, 'signal': 'buy', 'score': score})
        
        # ── SHORT: Severely Overbought (NEW!) ──
        elif rsi > RSI_OVERBOUGHT and current_price > bb_upper:
            score = rsi  # Higher RSI = higher score for shorts
            signals.append({'ticker': ticker, 'signal': 'short', 'score': score})
            
    # Sort by strongest signal
    signals.sort(key=lambda x: x['score'], reverse=True)
    
    return signals
