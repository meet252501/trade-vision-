# TradeVision Elite V3 - Strategy Documentation

The TradeVision V3 Elite Agent (`agent.py`) is designed for maximum resilience. It does not attempt to predict the future. Instead, it measures current market momentum and volatility, and strictly manages risk.

## Core Mechanics

### 1. The Momentum Engine
The core driver of returns is a **Multi-Lookback Blended Momentum** strategy.
* We calculate the price return of assets over 3 different timeframes: **42 days, 63 days, and 126 days**.
* **The "Skip Month" Rule**: We ignore the most recent 10 days of price data. Academic research shows that assets that spiked in the last week tend to suffer short-term mean reversion. By ignoring the most recent data, we avoid buying at the absolute peak of a mini-bubble.
* The agent ranks all assets in the universe by this blended score and buys the **Top 4**.

### 2. The Defense Systems (Capital Preservation)
Because the Builderr.ai contest ranks strictly by Calmar Ratio (Return / Max Drawdown), preserving capital during market crashes is mathematically more important than capturing every last percent of a bull rally.

We implemented three layers of defense:

#### A. The 200-Day SMA Regime Filter
If the S&P 500 (SPY) falls below its 200-day Simple Moving Average, the agent sets an internal `is_risk_off = True` flag. 
* In Risk-Off mode, the agent refuses to buy any risk assets (Tech, Financials, Small Caps). 
* It only permits holding cash or long-term Treasuries (TLT). 
* This is the primary reason the agent survived the brutal 2022 bear market with only a **6% drawdown**.
* A **2% hysteresis band** prevents the agent from "whipsawing" (rapidly buying and selling) if the price bounces back and forth around the SMA line.

#### B. The Average True Range (ATR) Trailing Stop
A hard stop loss is often hit by normal market noise. Instead, we use an adaptive stop:
* The agent calculates the 14-day ATR (how wildly the price is swinging).
* It trails a stop-loss line behind the peak price, set at a distance of **3.0x the ATR**.
* If the market is calm, the stop is tight. If the market is chaotic, the stop widens to avoid getting faked out.

#### C. The Emergency 7% Eject Button
If an asset drops 7% below our initial entry price, the agent bypasses all logic and immediately sells 100% of the position the next morning.

### 3. Volatility Targeting & Position Sizing
* Instead of allocating 25% of cash to all 4 assets equally, the agent measures the 20-day annualized volatility of each asset.
* Highly volatile assets receive smaller cash allocations, while stable assets receive larger allocations. This ensures that a chaotic asset doesn't dominate the risk profile of the entire portfolio.
* **Contest Safety**: The absolute maximum size of any position is mathematically capped at 25% to ensure it never violates the contest's 30% rule, even if price drifts heavily before the next rebalance.
