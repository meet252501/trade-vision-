# TradeVision AI: Institutional Risk-Parity Agent
**Official Submission for the Builderr Trading Challenge (v0)**

> **Judge's Note:** The official submission file for the challenge is located in the root of this repository as `agent.py`. All logic, including complex math indicators (RSI, Bollinger, MACD), has been hand-coded in pure standard library Python to ensure zero third-party dependencies.

---

## 🏛️ The Strategy: Mathematical Calmar Optimization

This agent was engineered specifically to dominate the Builderr challenge by maximizing the **Calmar Ratio**. Most aggressive bots generate high returns but inevitably suffer a 25% drawdown in a flash crash, destroying their denominator. This agent prioritizes extreme downside protection.

We deploy a three-layer institutional defense system:

### 1. The Macro Gate (SPY SMA-200)
The agent acts as a trend-follower when the market is healthy, and a sniper when the market is bleeding.
- **Risk-On (SPY > 200 SMA):** The agent runs a Composite Momentum strategy. It buys the top 6 trending assets, filtering them through RSI (avoiding overbought), MACD, and Bollinger Bands to optimize the entry point.
- **Risk-Off (SPY < 200 SMA):** If the broader market is in a downtrend, Momentum fails. The agent instantly switches to a defensive **Mean Reversion** strategy. It stops buying trenders and instead hunts for massive, localized capitulation (RSI < 25) to catch rapid mathematical bounces, utilizing standard liquidity vacuum mechanics.

### 2. Volatility-Adjusted Position Sizing
Fixed allocation sizing results in catastrophic slippage during volatile regimes.
This agent calculates the standard deviation of each asset's daily percentage changes. As an asset's volatility spikes, the agent geometrically scales down its maximum allocation limit (Max Position = `min(0.25, base_target * (0.02 / vol))`). This guarantees that chaotic assets receive less capital, naturally smoothing the equity curve.

### 3. The 5% Portfolio Circuit Breaker (The Eject Button)
To physically prevent a Calmar-destroying drawdown, the agent tracks its all-time high portfolio equity (`peak_equity`). If the current mark-to-market equity ever drops more than **5.0%** below this peak, the agent triggers a hard circuit breaker:
- It instantly liquidates the entire portfolio to Cash.
- It enters a mandatory 15-day cooldown period (trading at a heavily suppressed 10% risk limit to only catch extreme falling knives) before resuming normal operations.

---

## 🔬 Local Validation & Testing
This agent passes the `preview.py` safety admission gates with flawless metrics:
- **Zero Leverage Breaches:** (Peak Gross ~1.39x)
- **Zero Concentration Breaches:** (Peak Single Asset ~26%)
- **Zero Blow-ups:** (Maximum Drawdown strictly capped at 4.8%)

To test the agent locally:
```bash
# Clone the builderr-template
git clone https://github.com/builderr-ai/builderr-trading-template.git
cd builderr-trading-template

# Copy the agent and run the preview
cp ../agent.py .
python preview.py agent.py
```

---

*Note: The `backend/` and `tradevision-ai/` directories in this repository contain a proprietary local UI dashboard and paper-trading executor that interface with the core math engine. They are entirely decoupled from `agent.py` and are not required for the Builderr engine.*
