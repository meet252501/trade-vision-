# Omni-Bot v3.0

Omni-Bot is a market-agnostic, multi-timeframe algorithmic trading engine built for resilience. It is decoupled from any specific broker and currently utilizes MetaTrader 5 via an adapter architecture.

## 🚀 Features
- **Multi-Strategy Engine**: Runs Momentum on Equities/Crypto and Mean Reversion on Forex.
- **Macro Filters**: Blocks long trades during bear markets (evaluates SPY and BTC-USD 60-day moving averages).
- **Absolute Risk Management**:
  - Automatically scales position sizes based on real-time volatility (ATR).
  - Enforces a 25% Absolute Floor circuit breaker (halts all trading if the account drops 25%).
  - Takes dynamic 50% partial profits at +2 ATR.
- **State Persistence**: Serializes its internal memory to `omni_state.json` so it perfectly remembers scale-outs and drawdowns across reboots.
- **Live Notifications**: Integrated with Telegram for real-time trade and emergency alerts.
- **Structured Logging**: All actions are permanently recorded in `omni_bot_activity.log`.

## ⚙️ Configuration
All parameters are centralized in `config.py`.
1. **Timeframe**: Set `TIMEFRAME = '1D'` (or `'1H'`, `'4H'`).
2. **Telegram**: Paste your `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`, and set `ENABLE_TELEGRAM = True`.

## 🛠️ Installation
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Ensure you have the MetaTrader 5 terminal open and logged in.
3. Run the live trading daemon:
   ```bash
   python live_trader.py
   ```

## 🧪 Testing
To verify the logic on historical data or run the stress-test Gauntlet:
```bash
python omni_backtest.py
python stress_test.py
```
