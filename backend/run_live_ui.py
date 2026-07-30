import os
import sys
import time
import datetime
import threading

import tkinter as tk
from tkinter import ttk

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

# Alpaca API
from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient, CryptoHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest, CryptoLatestQuoteRequest

import agent
import executor

API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

class LiveExecutionUI:
    def __init__(self):
        self.trading_client = TradingClient(API_KEY, SECRET_KEY, paper=True)
        self.data_client = StockHistoricalDataClient(API_KEY, SECRET_KEY)
        self.crypto_client = CryptoHistoricalDataClient(API_KEY, SECRET_KEY)
        
        # Retry loop to handle Alpaca timeouts on startup
        import time
        for i in range(5):
            try:
                self.start_cash = float(self.trading_client.get_account().equity)
                break
            except Exception as e:
                print(f"Alpaca API timeout on startup. Retrying in 3s... ({i+1}/5)")
                time.sleep(3)
        else:
            self.start_cash = 100000.0 # Fallback
            
        self.cash = self.start_cash
        self.positions = {}
        self.equity_history = [self.start_cash]
        self.event_log = []
        
        # Stats
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.max_drawdown = 0
        self.peak_equity = self.start_cash
        self.current_equity = self.start_cash
        
        self.iteration = 0
        
        # Force agent state initialization
        agent._state['last_rebal_day'] = -999
        agent._state['peak_equity'] = self.start_cash
        
        self._build_ui()
        self.log_event("SYSTEM INITIALIZED. CONNECTING TO ALPACA PAPER TRADING...")
        
        # Start the background polling loop
        self._schedule_tick()
        self.root.mainloop()

    def _build_ui(self):
        """Build the TKinter monitoring UI."""
        self.root = tk.Tk()
        self.root.title("TradeVision AI - LIVE MARKET DASHBOARD")
        self.root.geometry("1400x900")
        self.root.configure(bg='#0a0a1a')
        
        # Style
        style = ttk.Style()
        style.theme_use('default')
        style.configure('TFrame', background='#0a0a1a')
        style.configure('TLabel', background='#0a0a1a', foreground='#00ff88', font=('Consolas', 10))
        style.configure('Title.TLabel', font=('Consolas', 12, 'bold'), foreground='#00ccff')
        style.configure('Good.TLabel', foreground='#00ff88', font=('Consolas', 10, 'bold'))
        style.configure('Bad.TLabel', foreground='#ff4444', font=('Consolas', 10, 'bold'))
        style.configure('Warn.TLabel', foreground='#ffaa00', font=('Consolas', 10, 'bold'))
        
        # Main layout
        top_bar = ttk.Frame(self.root)
        top_bar.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(top_bar, text="LIVE MARKET DASHBOARD - PAPER TRADING", style='Title.TLabel', font=('Consolas', 14, 'bold')).pack(side='left')
        self.lbl_status = ttk.Label(top_bar, text="STATUS: CONNECTED", style='Good.TLabel')
        self.lbl_status.pack(side='right')
        
        content = ttk.Frame(self.root)
        content.pack(fill='both', expand=True, padx=10, pady=5)
        
        left = ttk.Frame(content)
        left.pack(side='left', fill='both', expand=True)
        
        right = ttk.Frame(content, width=400)
        right.pack(side='right', fill='y', padx=(10, 0))
        right.pack_propagate(False)
        
        # Charts
        self.fig, (self.ax_equity, self.ax_dd) = plt.subplots(2, 1, figsize=(10, 8), facecolor='#0a0a1a', gridspec_kw={'height_ratios': [2, 1]})
        self.fig.subplots_adjust(hspace=0.3, left=0.08, right=0.98, top=0.92, bottom=0.08)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=left)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
        
        # Stats panel
        stats_frame = ttk.Frame(right)
        stats_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(stats_frame, text="=== AGENT STATS ===", style='Title.TLabel').pack(anchor='center')
        
        self.lbl_equity = ttk.Label(stats_frame, text=f"Equity: ${self.start_cash:,.2f}", font=('Consolas', 11, 'bold'))
        self.lbl_equity.pack(anchor='w', padx=5, pady=(5,0))
        
        self.lbl_pl = ttk.Label(stats_frame, text="P/L: $0.00 (0.00%)")
        self.lbl_pl.pack(anchor='w', padx=5)
        
        self.lbl_drawdown = ttk.Label(stats_frame, text="Max Drawdown: 0.00%")
        self.lbl_drawdown.pack(anchor='w', padx=5)
        
        self.lbl_positions = ttk.Label(stats_frame, text="Positions: None", wraplength=380)
        self.lbl_positions.pack(anchor='w', padx=5, pady=(5,0))
        
        self.lbl_cash = ttk.Label(stats_frame, text=f"Cash: ${self.start_cash:,.2f}")
        self.lbl_cash.pack(anchor='w', padx=5)
        
        # Configuration Panel
        config_frame = ttk.Frame(stats_frame)
        config_frame.pack(anchor='w', padx=5, pady=(10, 0))
        ttk.Label(config_frame, text="Trade Pool Limit ($): ", font=('Consolas', 10)).pack(side='left')
        self.entry_trade_pool = ttk.Entry(config_frame, width=15, font=('Consolas', 10), background='#111133')
        self.entry_trade_pool.insert(0, "10000.0")
        self.entry_trade_pool.pack(side='left')
        
        # Builderr Test Button
        btn_test = tk.Button(stats_frame, text="RUN BUILDERR CHALLENGE TEST", bg='#ffaa00', fg='#0a0a1a', font=('Consolas', 10, 'bold'), command=self._run_builderr_test)
        btn_test.pack(fill='x', padx=5, pady=10)
        
        # Event log
        ttk.Label(right, text="\n=== LIVE EVENT LOG ===", style='Title.TLabel').pack(anchor='w', padx=5)
        
        self.event_text = tk.Text(right, bg='#111133', fg='#ff6666', font=('Consolas', 9),
                                  height=30, width=45, state='disabled', wrap='word')
        self.event_text.pack(fill='both', expand=True, padx=5, pady=5)
        
    def log_event(self, text):
        self.event_log.append(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {text}")
        if len(self.event_log) > 100:
            self.event_log.pop(0)

    def _run_builderr_test(self):
        """Spawns a new window and runs preview.py from the builderr-template."""
        import subprocess
        
        top = tk.Toplevel(self.root)
        top.title("Builderr Admission Preview")
        top.geometry("900x600")
        top.configure(bg='#0a0a1a')
        
        lbl = ttk.Label(top, text="Running official preview.py simulator on your agent...", style='Title.TLabel')
        lbl.pack(pady=10)
        
        text_area = tk.Text(top, bg='#111133', fg='#00ff88', font=('Consolas', 10))
        text_area.pack(fill='both', expand=True, padx=10, pady=10)
        
        def run_test():
            try:
                # Resolve paths
                agent_path = os.path.abspath("backend/agent.py")
                cwd = os.path.abspath("builderr-template")
                
                cmd = [sys.executable, "preview.py", agent_path]
                
                # Execute and capture stdout in real-time
                process = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True)
                for line in process.stdout:
                    # Thread-safe insert
                    self.root.after(0, lambda l=line: [text_area.insert(tk.END, l), text_area.see(tk.END)])
                
                process.wait()
                if process.returncode == 0:
                    self.root.after(0, lambda: text_area.insert(tk.END, "\n[SYSTEM] TEST COMPLETED SUCCESSFULLY!\n"))
                else:
                    self.root.after(0, lambda: text_area.insert(tk.END, f"\n[SYSTEM] TEST FAILED with exit code {process.returncode}\n"))
                    
            except Exception as e:
                self.root.after(0, lambda e=e: text_area.insert(tk.END, f"\n[SYSTEM ERROR]: {str(e)}\n"))

        threading.Thread(target=run_test, daemon=True).start()
            
    def _schedule_tick(self):
        """Schedule the next API fetch in a background thread to prevent UI freezing."""
        threading.Thread(target=self._tick, daemon=True).start()
        # Schedule the next scan 60 seconds from now
        self.root.after(60000, self._schedule_tick)

    def _tick(self):
        self.iteration += 1
        self.log_event(f"SCANNING MARKET [Iteration {self.iteration}]...")
        
        try:
            # 1. Fetch State from Alpaca
            portfolio_state, self.cash = executor.fetch_portfolio_state()
            full_universe = set(agent.UNIVERSE + [p['ticker'] for p in portfolio_state['positions']])
            
            crypto_symbols = [s for s in full_universe if '/USD' in s]
            stock_symbols = [s for s in full_universe if '/USD' not in s]
            
            # Fetch Live Quotes
            if stock_symbols:
                quote_req = StockLatestQuoteRequest(symbol_or_symbols=stock_symbols)
                quotes = self.data_client.get_stock_latest_quote(quote_req)
                for sym, quote in quotes.items():
                    if float(quote.ask_price) > 0:
                        portfolio_state['last_prices'][sym] = float(quote.ask_price)
                        
            if crypto_symbols:
                crypto_req = CryptoLatestQuoteRequest(symbol_or_symbols=crypto_symbols)
                crypto_quotes = self.crypto_client.get_crypto_latest_quote(crypto_req)
                for sym, quote in crypto_quotes.items():
                    if float(quote.ask_price) > 0:
                        portfolio_state['last_prices'][sym] = float(quote.ask_price)

            # Update Peak Equity & State
            self.current_equity = float(self.trading_client.get_account().equity)
            self.equity_history.append(self.current_equity)
            
            if self.current_equity > self.peak_equity:
                self.peak_equity = self.current_equity
            
            agent._state['peak_equity'] = self.peak_equity
            
            # Calculate Drawdown
            dd = ((self.peak_equity - self.current_equity) / self.peak_equity) * 100
            if dd > self.max_drawdown:
                self.max_drawdown = dd
                
            # Log Circuit Breaker Activity
            if agent._state.get('circuit_breaker', 0) > 0:
                self.log_event(f"⚠️ CIRCUIT BREAKER ACTIVE: PANIC ALLOCATION MODE")
                
            # 2. Fetch Market Data & Run Agent
            market_state = executor.fetch_market_state(list(full_universe), portfolio_state['last_prices'])
            
            # Read dynamic trade pool from UI
            try:
                trade_pool = float(self.entry_trade_pool.get().replace(',', '').strip())
            except ValueError:
                trade_pool = 10000.0 # Fallback safe value
                
            orders = agent.decide(market_state, portfolio_state, self.cash, tradeable_equity=trade_pool)
            
            # Extract logs generated by agent
            for o in orders:
                self.log_event(f"ORDER: {o['side'].upper()} {o['quantity']:.4f} {o['ticker']}")
                
            # 3. Execute Orders
            if orders:
                executor.execute_orders(orders, portfolio_state)
                self.log_event(f"Executed {len(orders)} live orders.")
            else:
                self.log_event("No new orders generated.")

            self.positions = {p['ticker']: p['quantity'] for p in portfolio_state['positions']}

            # 4. Update UI (must run in main thread)
            self.root.after(0, self._update_charts)
            
        except Exception as e:
            self.log_event(f"ERROR: {str(e)}")
            self.root.after(0, self._update_charts)

    def _update_charts(self):
        profit = self.current_equity - self.start_cash
        pct = (profit / self.start_cash) * 100
        
        # Update text stats
        self.lbl_equity.config(text=f"Equity: ${self.current_equity:,.2f}")
        color = '#00ff88' if profit >= 0 else '#ff4444'
        self.lbl_pl.config(text=f"P/L: ${profit:,.2f} ({pct:+.2f}%)", foreground=color)
        self.lbl_drawdown.config(text=f"Max Drawdown: {self.max_drawdown:.2f}%")
        
        pos_str = ", ".join([f"{s}: {q:.2f}" for s, q in self.positions.items()]) if self.positions else "None (Cash)"
        self.lbl_positions.config(text=f"Positions: {pos_str}")
        self.lbl_cash.config(text=f"Cash: ${self.cash:,.2f}")
        
        # Event log
        self.event_text.config(state='normal')
        self.event_text.delete('1.0', 'end')
        for e in self.event_log[-30:]:
            self.event_text.insert('end', f"{e}\n")
        self.event_text.config(state='disabled')
        self.event_text.see('end')
        
        # Equity Chart
        self.ax_equity.clear()
        self.ax_equity.set_facecolor('#111133')
        self.ax_equity.set_title('Live Portfolio Equity', color='#00ff88', fontsize=11)
        self.ax_equity.plot(self.equity_history, color='#00ff88', linewidth=1.5)
        self.ax_equity.axhline(y=self.start_cash, color='#555555', linestyle='--', linewidth=0.8)
        self.ax_equity.fill_between(range(len(self.equity_history)), self.start_cash, self.equity_history,
                                     where=[e >= self.start_cash for e in self.equity_history],
                                     alpha=0.2, color='#00ff88')
        self.ax_equity.fill_between(range(len(self.equity_history)), self.start_cash, self.equity_history,
                                     where=[e < self.start_cash for e in self.equity_history],
                                     alpha=0.2, color='#ff4444')
        self.ax_equity.tick_params(colors='#888888')
        
        # Drawdown Chart
        self.ax_dd.clear()
        self.ax_dd.set_facecolor('#111133')
        self.ax_dd.set_title('Drawdown %', color='#ff4444', fontsize=11)
        
        dd_hist = []
        peak = self.start_cash
        for eq in self.equity_history:
            if eq > peak: peak = eq
            dd_hist.append(((eq - peak) / peak) * 100)
            
        self.ax_dd.plot(dd_hist, color='#ff4444', linewidth=1.5)
        self.ax_dd.fill_between(range(len(dd_hist)), -30, dd_hist, alpha=0.3, color='#ff4444')
        self.ax_dd.set_ylim(-30, 1)
        self.ax_dd.axhline(y=-25, color='#ff0000', linestyle='--', linewidth=1) # Circuit Breaker Line
        self.ax_dd.tick_params(colors='#888888')
        
        self.canvas.draw()

if __name__ == "__main__":
    if not API_KEY or not SECRET_KEY:
        print("Missing Alpaca API keys.")
        sys.exit(1)
        
    print("Launching Live Paper Trading Dashboard...")
    app = LiveExecutionUI()
