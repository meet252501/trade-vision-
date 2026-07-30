"""
TradeVision AI - MARKET CHAOS SIMULATOR (Crypto + Stocks)
========================================
Simulates the most brutal, unpredictable market conditions:
- Flash crashes (-30% in minutes)
- Pump & Dump schemes (+50% then -60%)
- Whale manipulation (sudden volume spikes)
- Dead cat bounces
- Slow bleeds
- Fake breakouts
- News-driven panic sells
- Liquidity gaps

Tests every filter: RSI, MACD, Bollinger Bands, Volume, Sentiment, Kelly Criterion
"""
import sys
import os
import time
import random
import math
import numpy as np
import datetime
import threading
import csv

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

try:
    import tkinter as tk
    from tkinter import ttk
    HAS_TK = True
except ImportError:
    HAS_TK = False

try:
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    import matplotlib.dates as mdates
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

# Import agent brain
import agent as brain

# ============================================================
# CRYPTO CHAOS ENGINE - Generates extreme market scenarios
# ============================================================
CRYPTO_UNIVERSE = [
    # --- CRYPTO (16 assets) ---
    ("BTC/USD", 105000, 0.04),
    ("ETH/USD", 4200, 0.05),
    ("SOL/USD", 180, 0.08),
    ("DOGE/USD", 0.45, 0.12),
    ("ADA/USD", 1.10, 0.07),
    ("AVAX/USD", 42, 0.09),
    ("LINK/USD", 22, 0.06),
    ("DOT/USD", 9.5, 0.07),
    ("SHIB/USD", 0.000035, 0.15),
    ("UNI/USD", 12.5, 0.08),
    ("MATIC/USD", 0.85, 0.09),
    ("XRP/USD", 2.80, 0.06),
    ("LTC/USD", 110, 0.05),
    ("AAVE/USD", 380, 0.07),
    ("ATOM/USD", 11.5, 0.08),
    ("NEAR/USD", 7.2, 0.09),
    # --- STOCKS (20 assets) ---
    ("AAPL", 215, 0.025),
    ("MSFT", 440, 0.022),
    ("NVDA", 135, 0.045),
    ("TSLA", 280, 0.06),
    ("AMZN", 195, 0.03),
    ("GOOG", 175, 0.025),
    ("META", 510, 0.035),
    ("AMD", 165, 0.05),
    ("NFLX", 950, 0.035),
    ("COIN", 260, 0.07),
    ("SPY", 560, 0.012),
    ("QQQ", 490, 0.015),
    ("XLE", 88, 0.025),
    ("GLD", 230, 0.01),
    ("PLTR", 28, 0.06),
    ("SMCI", 45, 0.09),
    ("ARM", 155, 0.055),
    ("MSTR", 380, 0.08),
    ("GME", 28, 0.12),
    ("AMC", 5.5, 0.15),
]

# Chaos event types
CHAOS_EVENTS = [
    "FLASH_CRASH",        # -15% to -80% instant drop
    "RUG_PULL",           # -90% to -99% instant drop (crypto goes to 0)
    "GOD_CANDLE",         # +300% to +500% instant pump
    "PUMP_AND_DUMP",      # +30-50% spike then -40-60% crash
    "WHALE_DUMP",         # Massive sell volume, -10-20% 
    "FAKE_BREAKOUT",      # +10% breakout then reversal -15%
    "DEAD_CAT_BOUNCE",    # Small recovery +5% then continued drop -10%
    "LIQUIDITY_GAP",      # Price gaps through stop losses
    "SLOW_BLEED",         # Gradual -1% per tick for many ticks
    "MEME_PUMP",          # Insane +100% pump on meme coins
    "NEWS_PANIC",         # Sudden -8% on fake news
    "ACCUMULATION",       # Sideways with increasing volume (before breakout)
    "EARNINGS_MISS",      # Stock drops -12% on bad earnings
    "SHORT_SQUEEZE",      # +25-40% squeeze on meme stocks
    "SECTOR_ROTATION",    # Gradual shift: some up, others down
    "FED_RATE_SHOCK",     # Everything drops -5% on surprise rate hike
    "GLOBAL_PANDEMIC_CRASH", # Everything drops -30% to -60% instantly
    "2008_LIQUIDITY_CRUNCH", # Crypto -80%, Stocks -40%, huge slippage incoming
    "BLACK_SWAN_EVENT",   # -95% drop on a major asset causing global panic
]


class CryptoMarketEngine:
    """Generates hyper-realistic crypto market data with chaos events."""
    
    def __init__(self, duration_minutes=20, ticks_per_minute=6):
        self.duration = duration_minutes
        self.ticks_per_minute = ticks_per_minute
        self.total_ticks = duration_minutes * ticks_per_minute
        self.tick = 0
        
        # Initialize all crypto prices
        self.cryptos = {}
        for symbol, start_price, base_vol in CRYPTO_UNIVERSE:
            # Generate 60 days of "history" for indicators
            history = self._generate_history(start_price, base_vol, 60)
            self.cryptos[symbol] = {
                'price': start_price,
                'base_vol': base_vol,
                'history': history,
                'volumes': [random.uniform(1e6, 5e7) for _ in range(60)],
                'trend': random.choice([-1, 0, 0, 1]),  # Slight bias
                'chaos_active': None,
                'chaos_remaining': 0,
                'chaos_data': {},
            }
        
        # Schedule chaos events
        self.scheduled_events = []
        self._schedule_chaos()
        
        # Stats
        self.events_log = []
        
    def _generate_history(self, price, vol, days):
        """Generate realistic historical price data."""
        prices = [price]
        for _ in range(days):
            ret = np.random.normal(0, vol / math.sqrt(252))
            prices.append(prices[-1] * (1 + ret))
        return prices
    
    def _schedule_chaos(self):
        """Pre-schedule chaos events throughout the simulation."""
        # Scale chaos events to be ABSOLUTELY BRUTAL (10x to 20x more frequent)
        num_events = max(20, int(self.duration * random.uniform(10.0, 20.0)))
        for _ in range(num_events):
            # Pick a random tick to trigger the event
            upper_bound = max(6, self.total_ticks - 10)
            tick = random.randint(5, upper_bound)
            event = random.choice(CHAOS_EVENTS)
            # Pick a random crypto (meme coins get more chaos)
            weights = [2 if c[2] > 0.10 else 1 for c in CRYPTO_UNIVERSE]
            target = random.choices(CRYPTO_UNIVERSE, weights=weights, k=1)[0][0]
            self.scheduled_events.append((tick, event, target))
        
        # Hardcode an instant disaster at tick 5 to stress test the agent!
        self.scheduled_events.append((5, "GLOBAL_PANDEMIC_CRASH", "SPY"))
        
        self.scheduled_events.sort(key=lambda x: x[0])
    
    def _apply_chaos(self, symbol, event):
        """Apply a chaos event to a specific crypto."""
        crypto = self.cryptos[symbol]
        
        if event == "FLASH_CRASH":
            drop = random.uniform(-0.60, -0.80) # UP TO 80% DROP!
            crypto['price'] *= (1 + drop)
            crypto['volumes'][-1] *= 10  # Volume explosion
            return f"FLASH CRASH on {symbol}: {drop*100:.1f}%"
            
        elif event == "RUG_PULL":
            drop = random.uniform(-0.90, -0.99) # 99% DROP! RUG PULLED!
            crypto['price'] *= (1 + drop)
            crypto['volumes'][-1] *= 50
            return f"RUG PULL on {symbol}: {drop*100:.1f}%! ITS GOING TO ZERO!"
            
        elif event == "GOD_CANDLE":
            pump = random.uniform(3.00, 5.00) # UP TO 500% PUMP
            crypto['price'] *= (1 + pump)
            crypto['volumes'][-1] *= 50
            return f"GOD CANDLE on {symbol}: +{pump*100:.0f}%!"
            
        elif event == "PUMP_AND_DUMP":
            crypto['chaos_active'] = "PUMP_PHASE"
            crypto['chaos_remaining'] = random.randint(3, 6)
            crypto['chaos_data'] = {'pump_pct': random.uniform(0.50, 2.00)} # Up to 200% PUMP
            return f"PUMP starting on {symbol}: Target +{crypto['chaos_data']['pump_pct']*100:.0f}%"
            
        elif event == "WHALE_DUMP":
            drop = random.uniform(-0.30, -0.50) # 50% WHALE DUMP
            crypto['price'] *= (1 + drop)
            crypto['volumes'][-1] *= 15
            return f"WHALE DUMP on {symbol}: {drop*100:.1f}%"
            
        elif event == "FAKE_BREAKOUT":
            crypto['chaos_active'] = "FAKE_BREAK_UP"
            crypto['chaos_remaining'] = 4
            crypto['chaos_data'] = {'phase': 'up'}
            return f"FAKE BREAKOUT starting on {symbol}"
            
        elif event == "DEAD_CAT_BOUNCE":
            crypto['chaos_active'] = "DEAD_CAT"
            crypto['chaos_remaining'] = 5
            crypto['chaos_data'] = {'phase': 'bounce'}
            return f"DEAD CAT BOUNCE on {symbol}"
            
        elif event == "LIQUIDITY_GAP":
            gap = random.uniform(-0.20, -0.40) # 40% GAP
            crypto['price'] *= (1 + gap)
            return f"LIQUIDITY GAP on {symbol}: {gap*100:.1f}% (skipped stop losses)"
            
        elif event == "SLOW_BLEED":
            crypto['chaos_active'] = "BLEEDING"
            crypto['chaos_remaining'] = random.randint(8, 15)
            return f"SLOW BLEED starting on {symbol}"
            
        elif event == "MEME_PUMP":
            pump = random.uniform(1.00, 3.00) # UP TO 300% PUMP
            crypto['price'] *= (1 + pump)
            crypto['volumes'][-1] *= 20
            return f"MEME PUMP on {symbol}: +{pump*100:.0f}%!"
            
        elif event == "NEWS_PANIC":
            drop = random.uniform(-0.25, -0.45) # 45% DROP
            crypto['price'] *= (1 + drop)
            crypto['volumes'][-1] *= 5
            return f"NEWS PANIC on {symbol}: {drop*100:.1f}%"
            
        elif event == "ACCUMULATION":
            crypto['chaos_active'] = "ACCUMULATING"
            crypto['chaos_remaining'] = random.randint(6, 12)
            return f"WHALE ACCUMULATION detected on {symbol}"
            
        elif event == "EARNINGS_MISS":
            if '/USD' not in symbol:
                drop = random.uniform(-0.25, -0.50) # 50% MISS
                crypto['price'] *= (1 + drop)
                crypto['volumes'][-1] *= 10
                return f"EARNINGS MISS on {symbol}: {drop*100:.1f}%"
            return ""
            
        elif event == "SHORT_SQUEEZE":
            if symbol in ["GME", "AMC", "MSTR", "COIN", "PLTR", "TSLA"]:
                crypto['chaos_active'] = "SQUEEZE_PHASE"
                crypto['chaos_remaining'] = random.randint(4, 8)
                crypto['chaos_data'] = {'pump_pct': random.uniform(0.60, 1.20)}
                return f"SHORT SQUEEZE starting on {symbol}!"
            return ""
            
        elif event == "SECTOR_ROTATION":
            crypto['chaos_active'] = "ROTATION"
            crypto['chaos_remaining'] = 10
            crypto['chaos_data'] = {'dir': random.choice([-1, 1])}
            return f"SECTOR ROTATION affecting {symbol}"

        elif event == "FED_RATE_SHOCK":
            for s, c in self.cryptos.items():
                c['price'] *= 0.95
            return f"FED RATE SHOCK! Entire market down 5%!"
            
        elif event == "GLOBAL_PANDEMIC_CRASH":
            for s, c in self.cryptos.items():
                drop = random.uniform(-0.30, -0.60)
                c['price'] *= (1 + drop)
                c['volumes'][-1] *= 5 # High volume panic
            return f"⚠️ GLOBAL PANDEMIC CRASH! ENTIRE MARKET DOWN 30-60%! ⚠️"
            
        elif event == "2008_LIQUIDITY_CRUNCH":
            for s, c in self.cryptos.items():
                if '/USD' in s:
                    c['price'] *= random.uniform(0.15, 0.25) # -75% to -85%
                else:
                    c['price'] *= random.uniform(0.55, 0.65) # -35% to -45%
                c['chaos_active'] = "LIQUIDITY_CRISIS"
                c['chaos_remaining'] = random.randint(15, 25)
            return f"🚨 2008 LIQUIDITY CRUNCH! EXTREME SLIPPAGE ENABLED GLOBALLY! 🚨"
            
        elif event == "BLACK_SWAN_EVENT":
            # Nuke the symbol, and drag everything else down with it
            crypto['price'] *= random.uniform(0.01, 0.05) # -95% to -99%
            for s, c in self.cryptos.items():
                if s != symbol:
                    c['price'] *= random.uniform(0.80, 0.90) # Everything else drops 10-20% in sympathy panic
            return f"🦢 BLACK SWAN EVENT! {symbol} IS DEAD (-95%). MARKET CONTAGION DETECTED! 🦢"
            
        return ""
    
    def step(self):
        """Advance one tick in the simulation."""
        self.tick += 1
        events_this_tick = []
        
        # Check for scheduled chaos events
        for tick, event, target in self.scheduled_events:
            if tick == self.tick:
                msg = self._apply_chaos(target, event)
                events_this_tick.append(msg)
                self.events_log.append((self.tick, msg))
        
        # Update all crypto prices
        for symbol, data in self.cryptos.items():
            # Base random walk
            vol = data['base_vol'] / math.sqrt(252 * self.ticks_per_minute)
            base_ret = np.random.normal(data['trend'] * 0.0001, vol)
            
            # Apply active chaos effects
            if data['chaos_active'] and data['chaos_remaining'] > 0:
                if data['chaos_active'] == "PUMP_PHASE":
                    pump_per_tick = data['chaos_data']['pump_pct'] / 5
                    base_ret += pump_per_tick
                    data['volumes'][-1] *= 3
                    data['chaos_remaining'] -= 1
                    if data['chaos_remaining'] <= 0:
                        # DUMP phase
                        dump = random.uniform(-0.40, -0.60)
                        data['price'] *= (1 + dump)
                        data['volumes'][-1] *= 10
                        events_this_tick.append(f"DUMP CRASH on {symbol}: {dump*100:.1f}%!")
                        self.events_log.append((self.tick, f"DUMP CRASH on {symbol}: {dump*100:.1f}%!"))
                        data['chaos_active'] = None
                        
                elif data['chaos_active'] == "FAKE_BREAK_UP":
                    if data['chaos_data']['phase'] == 'up':
                        base_ret += 0.03
                        data['chaos_remaining'] -= 1
                        if data['chaos_remaining'] <= 2:
                            data['chaos_data']['phase'] = 'reversal'
                    else:
                        base_ret -= 0.05
                        data['chaos_remaining'] -= 1
                        if data['chaos_remaining'] <= 0:
                            data['chaos_active'] = None
                            
                elif data['chaos_active'] == "DEAD_CAT":
                    if data['chaos_data']['phase'] == 'bounce':
                        base_ret += 0.015
                        data['chaos_remaining'] -= 1
                        if data['chaos_remaining'] <= 3:
                            data['chaos_data']['phase'] = 'resume_fall'
                    else:
                        base_ret -= 0.025
                        data['chaos_remaining'] -= 1
                        if data['chaos_remaining'] <= 0:
                            data['chaos_active'] = None
                            
                elif data['chaos_active'] == "BLEEDING":
                    base_ret -= random.uniform(0.005, 0.015)
                    data['chaos_remaining'] -= 1
                    if data['chaos_remaining'] <= 0:
                        data['chaos_active'] = None
                        
                elif data['chaos_active'] == "ACCUMULATING":
                    base_ret += random.uniform(-0.002, 0.003)  # Sideways
                    data['volumes'][-1] *= 1.5  # Rising volume
                    data['chaos_remaining'] -= 1
                    if data['chaos_remaining'] <= 0:
                        # Breakout!
                        breakout = random.uniform(0.08, 0.20)
                        data['price'] *= (1 + breakout)
                        events_this_tick.append(f"BREAKOUT on {symbol}: +{breakout*100:.1f}%!")
                        self.events_log.append((self.tick, f"BREAKOUT on {symbol}: +{breakout*100:.1f}%!"))
                        data['chaos_active'] = None
                        
                elif data['chaos_active'] == "SQUEEZE_PHASE":
                    pump_per_tick = data['chaos_data']['pump_pct'] / max(1, data['chaos_remaining'])
                    base_ret += pump_per_tick
                    data['volumes'][-1] *= 5
                    data['chaos_remaining'] -= 1
                    if data['chaos_remaining'] <= 0:
                        data['chaos_active'] = None
                        
                elif data['chaos_active'] == "ROTATION":
                    base_ret += data['chaos_data']['dir'] * random.uniform(0.005, 0.015)
                    data['chaos_remaining'] -= 1
                    if data['chaos_remaining'] <= 0:
                        data['chaos_active'] = None
            
            # Apply return
            data['price'] = max(data['price'] * (1 + base_ret), 0.0000001)
            data['history'].append(data['price'])
            
            # Generate volume
            base_volume = random.uniform(5e5, 5e7)
            data['volumes'].append(base_volume)
        
        return events_this_tick
    
    def get_market_state(self):
        """Convert current state to agent-compatible market_state dict."""
        market_state = {}
        for symbol, data in self.cryptos.items():
            bars = []
            for i in range(len(data['history'])):
                p = data['history'][i]
                v = data['volumes'][i] if i < len(data['volumes']) else 1e6
                bars.append({
                    'date': str(datetime.date.today() - datetime.timedelta(days=len(data['history'])-i)),
                    'open': p * random.uniform(0.998, 1.002),
                    'high': p * random.uniform(1.001, 1.02),
                    'low': p * random.uniform(0.98, 0.999),
                    'close': p,
                    'volume': v,
                })
            market_state[symbol] = bars
        return market_state
    
    def get_portfolio_state(self, positions, cash):
        """Build portfolio state dict."""
        last_prices = {s: d['price'] for s, d in self.cryptos.items()}
        pos_list = [{'ticker': t, 'quantity': q} for t, q in positions.items()]
        return {
            'positions': pos_list,
            'last_prices': last_prices,
        }


# ============================================================
# SIMULATION RUNNER WITH LIVE UI
# ============================================================
class CryptoSimulationUI:
    def __init__(self, duration_minutes=20):
        os.environ['SIMULATION'] = '1'
        self.duration = duration_minutes
        self.engine = CryptoMarketEngine(duration_minutes=duration_minutes)
        
        # Paper portfolio
        self.start_cash = 100000
        self.cash = self.start_cash
        self.positions = {}  # {symbol: quantity}
        self.equity_history = [self.start_cash]
        self.trade_log = []
        self.event_log = []
        
        # Agent state
        brain._state['day_count'] = 0
        brain._state['last_rebal_day'] = -999
        brain._state['peak_equity'] = self.start_cash
        brain._state['high_water_marks'] = {}
        brain._state['sold_cooldown'] = {}
        
        # Override agent universe
        brain.UNIVERSE = [c[0] for c in CRYPTO_UNIVERSE]
        
        # Stats
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.max_drawdown = 0
        self.peak_equity = self.start_cash
        
        if HAS_TK and HAS_MPL:
            self._build_ui()
        else:
            self._run_headless()
    
    def _build_ui(self):
        """Build the TKinter monitoring UI."""
        self.root = tk.Tk()
        self.root.title("TradeVision AI - CRYPTO CHAOS SIMULATOR")
        self.root.geometry("1400x900")
        self.root.configure(bg='#0a0a1a')
        
        # Style
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Dark.TFrame', background='#0a0a1a')
        style.configure('Dark.TLabel', background='#0a0a1a', foreground='#e0e0e0', font=('Consolas', 10))
        style.configure('Title.TLabel', background='#0a0a1a', foreground='#00ff88', font=('Consolas', 14, 'bold'))
        style.configure('Warn.TLabel', background='#0a0a1a', foreground='#ff4444', font=('Consolas', 10, 'bold'))
        style.configure('Good.TLabel', background='#0a0a1a', foreground='#00ff88', font=('Consolas', 10, 'bold'))
        
        # Top bar
        top = ttk.Frame(self.root, style='Dark.TFrame')
        top.pack(fill='x', padx=10, pady=5)
        ttk.Label(top, text="CRYPTO CHAOS SIMULATOR - STRESS TEST", style='Title.TLabel').pack(side='left')
        self.time_label = ttk.Label(top, text="Time: 00:00 / 20:00", style='Dark.TLabel')
        self.time_label.pack(side='right')
        
        # Main content
        main = ttk.Frame(self.root, style='Dark.TFrame')
        main.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Left panel: Charts
        left = ttk.Frame(main, style='Dark.TFrame')
        left.pack(side='left', fill='both', expand=True)
        
        self.fig = Figure(figsize=(9, 7), dpi=100, facecolor='#0a0a1a')
        self.fig.subplots_adjust(hspace=0.35)
        
        # Equity curve
        self.ax_equity = self.fig.add_subplot(311)
        self.ax_equity.set_facecolor('#111133')
        self.ax_equity.set_title('Portfolio Equity', color='#00ff88', fontsize=11)
        self.ax_equity.tick_params(colors='#888888')
        
        # Top 4 crypto prices
        self.ax_crypto = self.fig.add_subplot(312)
        self.ax_crypto.set_facecolor('#111133')
        self.ax_crypto.set_title('Crypto Prices (Normalized)', color='#00ccff', fontsize=11)
        self.ax_crypto.tick_params(colors='#888888')
        
        # Drawdown
        self.ax_dd = self.fig.add_subplot(313)
        self.ax_dd.set_facecolor('#111133')
        self.ax_dd.set_title('Drawdown %', color='#ff4444', fontsize=11)
        self.ax_dd.tick_params(colors='#888888')
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=left)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
        
        # Right panel: Stats + Events
        right = ttk.Frame(main, style='Dark.TFrame', width=380)
        right.pack(side='right', fill='y', padx=(10, 0))
        right.pack_propagate(False)
        
        # Stats
        stats_frame = ttk.Frame(right, style='Dark.TFrame')
        stats_frame.pack(fill='x', pady=5)
        ttk.Label(stats_frame, text="=== AGENT STATS ===", style='Title.TLabel').pack()
        
        self.lbl_equity = ttk.Label(stats_frame, text="Equity: $100,000.00", style='Dark.TLabel')
        self.lbl_equity.pack(anchor='w', padx=5)
        self.lbl_pnl = ttk.Label(stats_frame, text="P/L: $0.00 (0.00%)", style='Good.TLabel')
        self.lbl_pnl.pack(anchor='w', padx=5)
        self.lbl_trades = ttk.Label(stats_frame, text="Trades: 0 (W:0 L:0)", style='Dark.TLabel')
        self.lbl_trades.pack(anchor='w', padx=5)
        self.lbl_winrate = ttk.Label(stats_frame, text="Win Rate: N/A", style='Dark.TLabel')
        self.lbl_winrate.pack(anchor='w', padx=5)
        self.lbl_drawdown = ttk.Label(stats_frame, text="Max Drawdown: 0.00%", style='Dark.TLabel')
        self.lbl_drawdown.pack(anchor='w', padx=5)
        self.lbl_positions = ttk.Label(stats_frame, text="Positions: None", style='Dark.TLabel')
        self.lbl_positions.pack(anchor='w', padx=5)
        self.lbl_cash = ttk.Label(stats_frame, text="Cash: $100,000.00", style='Dark.TLabel')
        self.lbl_cash.pack(anchor='w', padx=5)
        self.lbl_chaos = ttk.Label(stats_frame, text="Chaos Events: 0", style='Warn.TLabel')
        self.lbl_chaos.pack(anchor='w', padx=5)
        
        # Filters status
        ttk.Label(stats_frame, text="\n=== ACTIVE FILTERS ===", style='Title.TLabel').pack(anchor='w', padx=5)
        filters = ["RSI < 70", "MACD Bullish", "Volume Spike", "Bollinger Band", "Sentiment > -0.3", "Kelly Sizing"]
        for f in filters:
            ttk.Label(stats_frame, text=f"  [ON] {f}", style='Good.TLabel').pack(anchor='w', padx=5)
        
        # Event log
        ttk.Label(right, text="\n=== CHAOS EVENT LOG ===", style='Title.TLabel').pack(anchor='w', padx=5)
        
        self.event_text = tk.Text(right, bg='#111133', fg='#ff6666', font=('Consolas', 9),
                                  height=15, width=45, state='disabled', wrap='word')
        self.event_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Start simulation
        if '--headless' in sys.argv:
            self._run_headless()
        else:
            self.root.after(100, self._tick)
            self.root.mainloop()
    
    def _get_equity(self):
        """Calculate current total equity."""
        pos_value = sum(
            qty * self.engine.cryptos[sym]['price']
            for sym, qty in self.positions.items()
        )
        return self.cash + pos_value
    
    def _execute_sim_orders(self, orders):
        """Execute orders in the simulation with real-world friction (slippage & fees)."""
        fee_rate = 0.0015 # 0.15% exchange fee
        
        for order in orders:
            ticker = order['ticker']
            side = order['side']
            qty = float(order['quantity'])
            
            if qty <= 0.0001:
                continue
            
            crypto_data = self.engine.cryptos.get(ticker, {})
            price = crypto_data.get('price', 0)
            if price <= 0:
                continue
                
            # Dynamic Slippage Calculation
            base_slippage = random.uniform(0.0005, 0.005) # 0.05% to 0.5% normal slippage
            if crypto_data.get('chaos_active') or crypto_data.get('volumes', [1])[-1] > 5:
                # Extreme slippage during chaos events or volume spikes!
                base_slippage = random.uniform(0.01, 0.05) # 1% to 5% slippage
            
            if side == 'buy':
                exec_price = price * (1 + base_slippage) # Buy at a higher, worse price
                cost = qty * exec_price
                fee = cost * fee_rate
                
                if (cost + fee) > self.cash * 0.95:
                    qty = (self.cash * 0.90) / (exec_price * (1 + fee_rate))
                    cost = qty * exec_price
                    fee = cost * fee_rate
                    
                if (cost + fee) > 0 and (cost + fee) <= self.cash:
                    self.cash -= (cost + fee)
                    self.positions[ticker] = self.positions.get(ticker, 0) + qty
                    self.total_trades += 1
                    entry = {'side': 'BUY', 'ticker': ticker, 'qty': qty, 'price': exec_price, 'tick': self.engine.tick}
                    self.trade_log.append(entry)
                    
            elif side == 'sell':
                exec_price = price * (1 - base_slippage) # Sell at a lower, worse price
                if ticker in self.positions:
                    sell_qty = min(qty, self.positions[ticker])
                    revenue = sell_qty * exec_price
                    fee = revenue * fee_rate
                    self.cash += (revenue - fee)
                    self.positions[ticker] -= sell_qty
                    if self.positions[ticker] <= 0.0001:
                        del self.positions[ticker]
                    self.total_trades += 1
                    
                    # Track win/loss
                    buys = [t for t in self.trade_log if t['ticker'] == ticker and t['side'] == 'BUY']
                    if buys:
                        avg_buy = np.mean([b['price'] for b in buys])
                        if exec_price > avg_buy:
                            self.winning_trades += 1
                        else:
                            self.losing_trades += 1
                    
                    entry = {'side': 'SELL', 'ticker': ticker, 'qty': sell_qty, 'price': exec_price, 'tick': self.engine.tick}
                    self.trade_log.append(entry)
                    
            elif side == 'sell_short':
                exec_price = price * (1 - base_slippage) # Short at a lower, worse price
                req_margin = qty * exec_price
                fee = req_margin * fee_rate
                
                if (req_margin + fee) > self.cash * 0.95:
                    qty = (self.cash * 0.90) / (exec_price * (1 + fee_rate))
                    req_margin = qty * exec_price
                    fee = req_margin * fee_rate
                
                if req_margin > 0:
                    self.cash += req_margin # Receive cash from short sale
                    self.cash -= fee        # Pay trading fee
                    self.positions[ticker] = self.positions.get(ticker, 0) - qty # Negative quantity
                    self.total_trades += 1
                    self.trade_log.append({'side': 'SELL_SHORT', 'ticker': ticker, 'qty': qty, 'price': exec_price, 'tick': self.engine.tick})

            elif side == 'buy_to_cover':
                exec_price = price * (1 + base_slippage) # Cover at a higher, worse price
                if ticker in self.positions and self.positions[ticker] < -0.0001:
                    cover_qty = min(qty, abs(self.positions[ticker]))
                    cost = cover_qty * exec_price
                    fee = cost * fee_rate
                    self.cash -= (cost + fee) # Pay cash to buy back + fee
                    self.positions[ticker] += cover_qty
                    if abs(self.positions[ticker]) <= 0.0001:
                        del self.positions[ticker]
                    self.total_trades += 1
                    
                    # Track win/loss for short
                    shorts = [t for t in self.trade_log if t['ticker'] == ticker and t['side'] == 'SELL_SHORT']
                    if shorts:
                        avg_short = np.mean([s['price'] for s in shorts])
                        if exec_price < avg_short:
                            self.winning_trades += 1
                        else:
                            self.losing_trades += 1
                            
                    self.trade_log.append({'side': 'BUY_COVER', 'ticker': ticker, 'qty': cover_qty, 'price': exec_price, 'tick': self.engine.tick})
    
    def _tick(self):
        """One simulation tick."""
        if self.engine.tick >= self.engine.total_ticks:
            self._finish()
            return
        
        # Step the market
        events = self.engine.step()
        
        # Log events
        for e in events:
            self.event_log.append(e)
        
        # Run agent every 3 ticks (~30 seconds sim time)
        if self.engine.tick % 3 == 0:
            try:
                market_state = self.engine.get_market_state()
                portfolio_state = self.engine.get_portfolio_state(self.positions, self.cash)
                
                equity = self._get_equity()
                brain._state['peak_equity'] = max(brain._state['peak_equity'], equity)
                brain._state['day_count'] += 1
                
                orders = brain.decide(market_state, portfolio_state, self.cash)
                self._execute_sim_orders(orders)
            except Exception as e:
                import traceback
                print(f"Agent error: {e}")
                traceback.print_exc()
        
        # Track equity
        equity = self._get_equity()
        self.equity_history.append(equity)
        
        # Track drawdown
        if equity > self.peak_equity:
            self.peak_equity = equity
        dd = (self.peak_equity - equity) / self.peak_equity * 100
        if dd > self.max_drawdown:
            self.max_drawdown = dd
        
        # Update UI every 2 ticks
        if self.engine.tick % 2 == 0:
            self._update_ui()
        
        # Schedule next tick (speeds up over time for a 20min experience)
        delay = max(50, 1000 - self.engine.tick * 2)  # Start slow, speed up
        self.root.after(delay, self._tick)
    
    def _update_ui(self):
        """Update all UI elements."""
        equity = self._get_equity()
        pnl = equity - self.start_cash
        pct = (pnl / self.start_cash) * 100
        
        # Time
        elapsed_ticks = self.engine.tick
        total_ticks = self.engine.total_ticks
        elapsed_min = elapsed_ticks / self.engine.ticks_per_minute
        self.time_label.config(text=f"Tick: {elapsed_ticks}/{total_ticks} | Time: {elapsed_min:.1f}/{self.duration} min")
        
        # Stats
        self.lbl_equity.config(text=f"Equity: ${equity:,.2f}")
        
        pnl_style = 'Good.TLabel' if pnl >= 0 else 'Warn.TLabel'
        self.lbl_pnl.config(text=f"P/L: {'+'if pnl>=0 else ''}${pnl:,.2f} ({pct:+.2f}%)", style=pnl_style)
        self.lbl_trades.config(text=f"Trades: {self.total_trades} (W:{self.winning_trades} L:{self.losing_trades})")
        
        wr = (self.winning_trades / max(1, self.winning_trades + self.losing_trades)) * 100
        self.lbl_winrate.config(text=f"Win Rate: {wr:.0f}%")
        self.lbl_drawdown.config(text=f"Max Drawdown: {self.max_drawdown:.2f}%")
        
        pos_str = ", ".join([f"{s}: {q:.2f}" for s, q in self.positions.items()]) if self.positions else "None (Cash)"
        self.lbl_positions.config(text=f"Positions: {pos_str}")
        self.lbl_cash.config(text=f"Cash: ${self.cash:,.2f}")
        self.lbl_chaos.config(text=f"Chaos Events: {len(self.event_log)}")
        
        # Event log
        self.event_text.config(state='normal')
        self.event_text.delete('1.0', 'end')
        for e in self.event_log[-20:]:  # Last 20 events
            self.event_text.insert('end', f"{e}\n")
        self.event_text.config(state='disabled')
        self.event_text.see('end')
        
        # Charts
        self.ax_equity.clear()
        self.ax_equity.set_facecolor('#111133')
        self.ax_equity.set_title('Portfolio Equity', color='#00ff88', fontsize=11)
        self.ax_equity.plot(self.equity_history, color='#00ff88', linewidth=1.5)
        self.ax_equity.axhline(y=self.start_cash, color='#555555', linestyle='--', linewidth=0.8)
        self.ax_equity.fill_between(range(len(self.equity_history)), self.start_cash, self.equity_history,
                                     where=[e >= self.start_cash for e in self.equity_history],
                                     alpha=0.2, color='#00ff88')
        self.ax_equity.fill_between(range(len(self.equity_history)), self.start_cash, self.equity_history,
                                     where=[e < self.start_cash for e in self.equity_history],
                                     alpha=0.2, color='#ff4444')
        self.ax_equity.tick_params(colors='#888888')
        
        # Crypto prices (normalized to 100)
        self.ax_crypto.clear()
        self.ax_crypto.set_facecolor('#111133')
        self.ax_crypto.set_title('Top Crypto Prices (Normalized)', color='#00ccff', fontsize=11)
        colors = ['#ff6666', '#66ff66', '#6666ff', '#ffff66', '#ff66ff', '#66ffff']
        for i, (sym, data) in enumerate(list(self.engine.cryptos.items())[:6]):
            hist = data['history'][-100:]  # Last 100 ticks
            if len(hist) > 1:
                normalized = [p / hist[0] * 100 for p in hist]
                self.ax_crypto.plot(normalized, color=colors[i % len(colors)], linewidth=1, label=sym.split('/')[0])
        self.ax_crypto.axhline(y=100, color='#555555', linestyle='--', linewidth=0.8)
        self.ax_crypto.legend(loc='upper left', fontsize=7, facecolor='#111133', edgecolor='#333355', labelcolor='#cccccc')
        self.ax_crypto.tick_params(colors='#888888')
        
        # Drawdown chart
        self.ax_dd.clear()
        self.ax_dd.set_facecolor('#111133')
        self.ax_dd.set_title('Drawdown %', color='#ff4444', fontsize=11)
        dd_series = []
        peak = self.start_cash
        for e in self.equity_history:
            if e > peak:
                peak = e
            dd_series.append(-(peak - e) / peak * 100)
        self.ax_dd.fill_between(range(len(dd_series)), 0, dd_series, color='#ff4444', alpha=0.4)
        self.ax_dd.plot(dd_series, color='#ff4444', linewidth=1)
        self.ax_dd.tick_params(colors='#888888')
        
        self.canvas.draw_idle()
    
    def _finish(self):
        """Simulation complete."""
        equity = self._get_equity()
        pnl = equity - self.start_cash
        pct = (pnl / self.start_cash) * 100
        wr = (self.winning_trades / max(1, self.winning_trades + self.losing_trades)) * 100
        
        print("\n" + "=" * 60)
        print("  CRYPTO CHAOS SIMULATION - FINAL RESULTS")
        print("=" * 60)
        print(f"  Starting Capital:  ${self.start_cash:>12,.2f}")
        print(f"  Final Equity:      ${equity:>12,.2f}")
        print(f"  Profit/Loss:       ${pnl:>12,.2f} ({pct:+.2f}%)")
        print(f"  Total Trades:      {self.total_trades}")
        print(f"  Win Rate:          {wr:.0f}%")
        print(f"  Max Drawdown:      {self.max_drawdown:.2f}%")
        print(f"  Chaos Events:      {len(self.event_log)}")
        print("=" * 60)
        
        if pnl > 0:
            print("  VERDICT: AGENT SURVIVED THE CHAOS AND MADE PROFIT!")
        elif pnl > -5000:
            print("  VERDICT: AGENT SURVIVED WITH MINIMAL DAMAGE. GOOD DEFENSE!")
        else:
            print("  VERDICT: AGENT TOOK HEAVY LOSSES. NEEDS IMPROVEMENT.")
        print("=" * 60)
        
        # Save results
        results_file = os.path.join(os.path.dirname(__file__), 'backend', 'chaos_sim_results.csv')
        with open(results_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['tick', 'equity'])
            for i, eq in enumerate(self.equity_history):
                writer.writerow([i, f"{eq:.2f}"])
        
        # Update title
        result_color = '#00ff88' if pnl >= 0 else '#ff4444'
        self.time_label.config(text=f"SIMULATION COMPLETE | P/L: {'+'if pnl>=0 else ''}${pnl:,.2f} ({pct:+.2f}%)")
    
    def _run_headless(self):
        """Run without UI."""
        print("Running headless (no tkinter/matplotlib)...")
        while self.engine.tick < self.engine.total_ticks:
            events = self.engine.step()
            for e in events:
                print(f"  [CHAOS] {e}")
            
            if self.engine.tick % 3 == 0:
                try:
                    market_state = self.engine.get_market_state()
                    portfolio_state = self.engine.get_portfolio_state(self.positions, self.cash)
                    equity = self._get_equity()
                    brain._state['peak_equity'] = max(brain._state['peak_equity'], equity)
                    orders = brain.decide(market_state, portfolio_state, self.cash)
                    self._execute_sim_orders(orders)
                except:
                    pass
            
            equity = self._get_equity()
            self.equity_history.append(equity)
            if equity > self.peak_equity:
                self.peak_equity = equity
            dd = (self.peak_equity - equity) / self.peak_equity * 100
            if dd > self.max_drawdown:
                self.max_drawdown = dd
            
            if self.engine.tick % 12 == 0:
                pnl = equity - self.start_cash
                print(f"  [Tick {self.engine.tick}/{self.engine.total_ticks}] Equity: ${equity:,.2f} | P/L: ${pnl:+,.2f}")
        
        self._finish_headless()
    
    def _finish_headless(self):
        equity = self._get_equity()
        pnl = equity - self.start_cash
        pct = (pnl / self.start_cash) * 100
        print(f"\nFINAL: ${equity:,.2f} | P/L: ${pnl:+,.2f} ({pct:+.2f}%) | Trades: {self.total_trades} | MaxDD: {self.max_drawdown:.2f}%")


if __name__ == '__main__':
    print("=" * 60)
    print("  TradeVision AI - MARKET CHAOS SIMULATOR (36 Assets)")
    print("  Testing agent against the most brutal market conditions")
    print("=" * 60)
    
    duration = 20  # 20 minute simulation
    if len(sys.argv) > 1:
        try:
            duration = int(sys.argv[1])
        except:
            pass
    
    sim = CryptoSimulationUI(duration_minutes=duration)
