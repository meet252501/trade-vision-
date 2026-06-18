# TradeVision AI - Elite V3 Agent 🚀

TradeVision AI is an end-of-day algorithmic trading agent built for the **Builderr.ai Trading Agent Challenge**. It combines a Python-based trading engine (`agent.py`) with a modern React/TypeScript dashboard to visualize backtest results.

This project was built to maximize the **Calmar Ratio** (Return / Max Drawdown) while adhering to strict contest limitations (no margin, 30% max position limit, 50 trades/day max, and <5s execution time).

## 📊 Performance & Validation
Tested against 5 years of **real Yahoo Finance data** using a custom Python harness that exactly mimics the contest platform. 
* **Recovery Rally (2020-21)**: +27.17% Return | 5.67% MaxDD | **4.78 Calmar** 🏆
* **Bull Market 2023**: +12.29% Return | 6.38% MaxDD | **1.94 Calmar** 🥉
* **COVID Crash 2020**: +8.09% Return | 6.28% MaxDD | **1.28 Calmar** 🥉

Read the full algorithmic breakdown in [STRATEGY_DOC.md](./STRATEGY_DOC.md).

## 📁 Project Structure
* `/backend/` - Contains the contest-ready `agent.py`, the validation harness, and testing suites.
  * `agent.py`: The core algorithm submitted to the contest.
  * `validate_agent.py`: The offline test harness.
* `/tradevision-ai/` - The React/Vite web application dashboard.

## 🛠️ Installation & Setup

### 1. The Dashboard (Frontend)
The dashboard allows you to visualize backtest charts, scoreboard comparisons, and strategy logic.
```bash
cd tradevision-ai
npm install
npm run dev
```

### 2. The Agent & Validation Harness (Backend)
To run the local backtests and stress tests using real market data:
```bash
cd backend
python -m pip install -r requirements.txt

# Run the 5-year multi-regime validation
python validate_agent.py

# Run the Pytest stress tests (Flash crashes, Bear market triggers)
python -m pytest test_agent.py -v
```

## ⚖️ Contest Constraints Handled
- **Max Leverage (1.5x)**: The agent is purely long-only and does not use margin.
- **Max Position Size (30%)**: Target sizes are mathematically capped at 25%, providing a 5% safety buffer against price-drift.
- **Max Execution Time (5000ms)**: Heavily optimized NumPy arrays result in an average `decide()` execution time of **0.61ms**.
