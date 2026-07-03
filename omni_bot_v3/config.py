# omni_bot/config.py

# ═══════════════════════════════════════════════════════
# UNIVERSES
# ═══════════════════════════════════════════════════════

STOCKS = [
    "SPY", "QQQ", "IWM",  # Major Indices
    "TLT", "GLD",         # Bonds, Gold
    "TQQQ", "UPRO", "SOXL" # 3x Leveraged (High Beta)
]

CRYPTO = [
    "BTC-USD", "ETH-USD", "SOL-USD"
]

FOREX = [
    "EURUSD=X", "GBPUSD=X", "USDJPY=X"
]

ALL_ASSETS = STOCKS + CRYPTO + FOREX

# ═══════════════════════════════════════════════════════
# SYSTEM SETTINGS
# ═══════════════════════════════════════════════════════

MAX_PORTFOLIO_POSITIONS = 3    # Don't hold more than 3 things at once
MAX_ALLOCATION_PER_TRADE = 0.33 # Each trade gets 33% of buying power

# ═══════════════════════════════════════════════════════
# RISK MANAGEMENT (NEW)
# ═══════════════════════════════════════════════════════

MAX_DRAWDOWN_PCT = 0.12        # If account drops 12% from peak, go 100% cash
ABSOLUTE_FLOOR_PCT = 0.25      # HARD STOP: If account drops 25% from INITIAL capital, STOP forever
COOLDOWN_BARS = 24             # After drawdown triggers, wait 24 bars before trading again
ATR_PERIOD = 14                # Average True Range period for volatility sizing
ATR_RISK_MULTIPLIER = 1.5     # Risk 1.5x ATR per trade for stop-loss sizing
CORRELATION_THRESHOLD = 0.80   # Don't buy two assets with > 80% correlation
RECOVERY_ALLOC_MULT = 0.50     # After drawdown, trade at 50% normal size until new peak
RECOVERY_ADX_THRESHOLD = 35    # After drawdown, require stronger trend before re-entering

# ═══════════════════════════════════════════════════════
# SPREAD / SLIPPAGE COSTS (per trade, one-way)
# ═══════════════════════════════════════════════════════

SPREAD_COSTS = {
    # Stocks & ETFs: ~0.05% average spread + slippage
    "SPY": 0.0003, "QQQ": 0.0003, "IWM": 0.0005,
    "TLT": 0.0005, "GLD": 0.0005,
    "TQQQ": 0.0008, "UPRO": 0.0008, "SOXL": 0.001,
    # Crypto: ~0.1% taker fee on most exchanges
    "BTC-USD": 0.001, "ETH-USD": 0.001, "SOL-USD": 0.0015,
    # Forex: ~0.01-0.03% spread on major pairs
    "EURUSD=X": 0.0001, "GBPUSD=X": 0.00015, "USDJPY=X": 0.00015,
}
DEFAULT_SPREAD = 0.001  # Fallback: 0.1%

# ═══════════════════════════════════════════════════════
# NOTIFICATIONS (TELEGRAM)
# ═══════════════════════════════════════════════════════

TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE"
TELEGRAM_CHAT_ID = "YOUR_TELEGRAM_CHAT_ID_HERE"
ENABLE_TELEGRAM = False  # Set to True to enable live notifications

# ═══════════════════════════════════════════════════════
# STRATEGY SETTINGS
# ═══════════════════════════════════════════════════════

# Core Timings & Macro
TIMEFRAME = '1D'               # The bot operates on Daily Bars by default
MACRO_EQUITY_TICKER = "SPY"    # The benchmark used to determine Equity Bull/Bear market
MACRO_CRYPTO_TICKER = "BTC-USD" # The benchmark used to determine Crypto Bull/Bear market
LEVERAGED_ETFS = ["TQQQ", "UPRO", "SOXL"] # Highly volatile ETFs blocked from shorting
SCALE_OUT_ATR_MULTIPLIER = 2.0 # Take partial profits at +2 ATR
CATASTROPHIC_SL_PCT = 0.15     # Absolute broker-side stop loss
CATASTROPHIC_TP_PCT = 0.50     # Absolute broker-side take profit

# Momentum (Stocks & Crypto)
MOMENTUM_LOOKBACK_FAST = 3
MOMENTUM_LOOKBACK_MID = 7
MOMENTUM_LOOKBACK_SLOW = 14    # NEW: Extended lookback for trend confirmation
MOMENTUM_LOOKBACK_TREND = 21   # NEW: Macro trend filter
MOMENTUM_LOOKBACK_MACRO = 60   # NEW: Global trend filter to prevent shorting in bull markets
VOLUME_LOOKBACK = 20           # NEW: Volume moving average period
ADX_PERIOD = 14                # NEW: ADX period to detect trending vs choppy
CRYPTO_ADX_THRESHOLD = 30      # Crypto is wild, needs higher trend confirmation
EQUITY_ADX_THRESHOLD = 20      # Equities trend slower, lower threshold
CRYPTO_RECOVERY_ADX = 40       # Much stricter entry when in drawdown
EQUITY_RECOVERY_ADX = 30
# Mean Reversion (Forex)
RSI_PERIOD = 14
BB_PERIOD = 20
BB_STD = 2.0
RSI_OVERSOLD = 30              # NEW: Explicit threshold
RSI_OVERBOUGHT = 70            # NEW: For short-selling
BB_SQUEEZE_THRESHOLD = 0.001   # NEW: Don't trade when bands are too narrow
MR_STOP_LOSS = 0.03            # NEW: 3% stop loss for mean reversion
