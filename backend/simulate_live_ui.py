import numpy as np
import time
import tkinter as tk
from tkinter import scrolledtext
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# --- CONFIGURATION ---
NUM_STOCKS = 100
NUM_DAYS = 1500
STARTING_EQUITY = 100000.0
TARGET_PROFIT = 500.0
TARGET_EQUITY = STARTING_EQUITY + TARGET_PROFIT

# Swarm Config
LOOKBACKS = [10, 21, 42]
SKIP_DAYS = 3
TOP_N = 2
MAX_POS = 0.40

class SimulationUI:
    def __init__(self, root):
        self.root = root
        self.root.title("TradeVision AI - Live Hard-Mode Simulation Matrix")
        self.root.geometry("1400x900")
        self.root.configure(bg="#0f172a")

        # --- PRE-GENERATE MARKET ---
        self.log("Initializing Matrix...")
        self.log("Generating 100 Synthetic Stocks with Geometric Brownian Motion...")
        self.log("Injecting 5%-20% unpredictable Flash Crashes...")
        
        np.random.seed(42)
        self.market_prices = np.zeros((NUM_DAYS, NUM_STOCKS))
        self.market_prices[0, :] = 100.0 
        for s in range(NUM_STOCKS):
            mu = np.random.uniform(-0.0005, 0.001)
            sigma = np.random.uniform(0.01, 0.05)
            for t in range(1, NUM_DAYS):
                shock = np.random.normal(0, 1)
                ret = mu + sigma * shock
                if np.random.random() < 0.01:
                    ret -= np.random.uniform(0.05, 0.20)
                self.market_prices[t, s] = self.market_prices[t-1, s] * (1 + ret)
                if self.market_prices[t, s] <= 0.1:
                    self.market_prices[t, s] = 0.1
        
        self.log("Market Matrix Generation Complete. Starting Gauntlet.")

        # --- SIMULATION STATE ---
        self.cash = STARTING_EQUITY
        self.positions = {}
        self.current_t = LOOKBACKS[-1] + SKIP_DAYS + 1
        self.equity_history = []
        self.time_history = []

        self.setup_ui()
        self.update_simulation()

    def log(self, msg):
        if not hasattr(self, 'console'): return
        self.console.insert(tk.END, f"{msg}\n")
        self.console.see(tk.END)

    def setup_ui(self):
        # Top Frame: Charts
        chart_frame = tk.Frame(self.root, bg="#0f172a")
        chart_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.fig, (self.ax_equity, self.ax_market) = plt.subplots(2, 1, figsize=(10, 6), facecolor='#0f172a')
        self.fig.tight_layout(pad=3.0)

        # Style Axes
        for ax in [self.ax_equity, self.ax_market]:
            ax.set_facecolor('#1e293b')
            ax.tick_params(colors='white')
            for spine in ax.spines.values():
                spine.set_color('#334155')

        self.ax_equity.set_title(f"Agent Equity (Target: ${TARGET_EQUITY:,.2f})", color='white')
        self.ax_market.set_title("Market Matrix (100 Stocks)", color='white')

        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Bottom Frame: Console
        console_frame = tk.Frame(self.root, bg="#0f172a", height=200)
        console_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=20)
        
        lbl = tk.Label(console_frame, text="Agent Terminal Logs", bg="#0f172a", fg="#94a3b8", font=("Consolas", 12))
        lbl.pack(anchor="w")

        self.console = scrolledtext.ScrolledText(console_frame, bg="#000000", fg="#10b981", font=("Consolas", 11), height=10)
        self.console.pack(fill=tk.X)

    def update_simulation(self):
        if self.current_t >= NUM_DAYS:
            self.log("SIMULATION FINISHED: End of Data.")
            return

        current_prices = self.market_prices[self.current_t, :]
        
        # 1. 2% Trailing Stop-Loss
        to_sell = []
        for s_idx, pos in self.positions.items():
            curr_price = current_prices[s_idx]
            if curr_price > pos['peak']:
                pos['peak'] = curr_price
            if curr_price < pos['peak'] * 0.98:
                to_sell.append(s_idx)
                
        for s_idx in to_sell:
            qty = self.positions[s_idx]['qty']
            self.cash += qty * current_prices[s_idx]
            self.log(f"[STOP LOSS] SIM_{s_idx} dropped 2%. Executed instant liquidation.")
            del self.positions[s_idx]
            
        current_equity = self.cash + sum(p['qty'] * current_prices[s_idx] for s_idx, p in self.positions.items())
        
        self.time_history.append(self.current_t)
        self.equity_history.append(current_equity)

        if self.current_t % 10 == 0:
            self.log(f"[Day {self.current_t}] Equity: ${current_equity:,.2f} | Open Positions: {len(self.positions)}")

        if current_equity >= TARGET_EQUITY:
            self.log(f"\n[!] GOAL ACHIEVED! Agent successfully survived the crashes and made $500!")
            self.log(f"Final Equity: ${current_equity:,.2f}")
            self.draw_charts()
            return

        if current_equity <= 0:
            self.log("\n[!] BANKRUPT. The Agent failed.")
            self.draw_charts()
            return

        # 2. Math Agent
        scores = {}
        for s in range(NUM_STOCKS):
            if s in self.positions: continue
            c = self.market_prices[:self.current_t, s]
            recent = c[-SKIP_DAYS-1]
            ret1 = (recent / c[-LOOKBACKS[0] - SKIP_DAYS]) - 1
            ret2 = (recent / c[-LOOKBACKS[1] - SKIP_DAYS]) - 1
            ret3 = (recent / c[-LOOKBACKS[2] - SKIP_DAYS]) - 1
            mom_score = (ret1 * 0.4) + (ret2 * 0.3) + (ret3 * 0.3)
            if mom_score > 0:
                scores[s] = mom_score
                
        raw_top = sorted(scores.keys(), key=lambda k: scores[k], reverse=True)[:TOP_N]
        
        # 3. Sentiment Agent
        final_allocations = []
        for s in raw_top:
            synthetic_sentiment = np.random.uniform(-1.0, 1.0)
            if synthetic_sentiment < -0.3:
                self.log(f"[VETO] Math Agent wanted SIM_{s}, but Fake News Engine detected fear.")
            else:
                final_allocations.append(s)
                
        # 4. Buy
        for s in final_allocations:
            if len(self.positions) >= 4: break
            alloc_cash = current_equity * MAX_POS
            if self.cash >= alloc_cash:
                qty = alloc_cash / current_prices[s]
                self.cash -= alloc_cash
                self.positions[s] = {'qty': qty, 'peak': current_prices[s]}
                self.log(f"[BUY] Swarm acquired SIM_{s} at ${current_prices[s]:.2f}")

        # Update visual charts every 5 days to keep it smooth
        if self.current_t % 5 == 0:
            self.draw_charts()

        self.current_t += 1
        # Loop exactly 1 day per second (1000ms). Adjust to 100ms if you want it faster.
        self.root.after(1000, self.update_simulation)

    def draw_charts(self):
        self.ax_equity.clear()
        self.ax_market.clear()

        # Re-apply styles
        self.ax_equity.set_facecolor('#1e293b')
        self.ax_market.set_facecolor('#1e293b')
        self.ax_equity.set_title(f"Agent Equity (Target: ${TARGET_EQUITY:,.2f})", color='white')
        self.ax_market.set_title("Market Matrix (100 Stocks)", color='white')
        self.ax_equity.tick_params(colors='white')
        self.ax_market.tick_params(colors='white')

        # Draw Equity
        self.ax_equity.plot(self.time_history, self.equity_history, color='#10b981', linewidth=2)
        self.ax_equity.axhline(TARGET_EQUITY, color='#ef4444', linestyle='--')

        # Draw Market Chaos (Just draw a sample of 10 stocks so it's not a complete blur)
        window_start = max(0, self.current_t - 100)
        for s in range(10):
            self.ax_market.plot(range(window_start, self.current_t), self.market_prices[window_start:self.current_t, s], alpha=0.5)

        self.canvas.draw()

if __name__ == "__main__":
    root = tk.Tk()
    app = SimulationUI(root)
    root.mainloop()
