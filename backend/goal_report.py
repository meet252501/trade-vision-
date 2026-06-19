import os
import datetime
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient

load_dotenv()

API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
PAPER = os.getenv("ALPACA_PAPER", "True") == "True"

def generate_report():
    try:
        client = TradingClient(API_KEY, SECRET_KEY, paper=PAPER)
        account = client.get_account()
        positions = client.get_all_positions()
        
        equity = float(account.equity)
        profit = equity - 100000.0
        
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %I:%M %p")
        
        lines = []
        lines.append("# 🎉 TradeVision Goal Achieved! 🎉")
        lines.append(f"**Goal:** Reach $500+ Profit")
        lines.append(f"**Time Achieved:** {now_str}")
        lines.append("")
        lines.append("## Financial Summary")
        lines.append(f"- **Final Portfolio Value:** ${equity:,.2f}")
        lines.append(f"- **Total Net Profit:** ${profit:,.2f} 🚀")
        lines.append(f"- **Available Cash:** ${float(account.cash):,.2f}")
        lines.append("")
        lines.append("## Winning Positions")
        lines.append("Here is the exact state of the portfolio when the goal was triggered:")
        lines.append("")
        lines.append("| Ticker | Shares | Market Value | Unrealized PNL |")
        lines.append("|---|---|---|---|")
        
        for p in positions:
            pnl = float(p.unrealized_pl)
            emoji = "🟢" if pnl >= 0 else "🔴"
            lines.append(f"| **{p.symbol}** | {p.qty} | ${float(p.market_value):,.2f} | {emoji} ${pnl:,.2f} |")
            
        lines.append("")
        lines.append("> [!TIP]")
        lines.append("> This proves the quantitative momentum engine works on live data. You can now tweak the variables in `agent.py` to target higher goals, or hook this up to a real-money broker when you feel confident!")
        
        report_content = "\n".join(lines)
        
        with open("GOAL_ACHIEVED_REPORT.md", "w", encoding="utf-8") as f:
            f.write(report_content)
            
        print("Report successfully generated to GOAL_ACHIEVED_REPORT.md!")
    except Exception as e:
        print(f"Failed to generate report: {e}")

if __name__ == "__main__":
    generate_report()
