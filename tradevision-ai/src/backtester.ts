import { StrategyConfig, PriceBar, BacktestResponse, EquityCurvePoint, DrawdownPoint, Trade, MetricSet } from "./types";

// Supported Universe
const UNIVERSE_BASE_PRICES: Record<string, { base: number; drift: number; vol: number }> = {
  SPY: { base: 380, drift: 0.12, vol: 0.15 },
  QQQ: { base: 260, drift: 0.18, vol: 0.22 },
  IWM: { base: 175, drift: 0.05, vol: 0.18 },
  XLK: { base: 120, drift: 0.22, vol: 0.24 },
  XLF: { base: 32, drift: 0.06, vol: 0.16 },
  XLE: { base: 82, drift: 0.04, vol: 0.25 },
  XLV: { base: 128, drift: 0.07, vol: 0.13 },
  GLD: { base: 172, drift: 0.09, vol: 0.12 },
  TLT: { base: 102, drift: -0.05, vol: 0.14 },
};


/**
 * Fetch real prices from Yahoo Finance API, fallback to synthetic data if requested or errors
 */
export async function getPricesForTicker(ticker: string, start: Date, end: Date): Promise<PriceBar[]> {
  const period1 = Math.floor(start.getTime() / 1000);
  const period2 = Math.floor(end.getTime() / 1000);
  
  try {
    const url = `https://query1.finance.yahoo.com/v8/finance/chart/${ticker}?period1=${period1}&period2=${period2}&interval=1d`;
    console.log(`[BACKTEST ENGINE] Fetching Yahoo Data: ${ticker}`);
    
    const response = await fetch(url, {
      headers: {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP Error ${response.status}`);
    }

    const data = await response.json() as any;
    const result = data?.chart?.result?.[0];
    if (!result) {
      throw new Error("No result block found in Yahoo response");
    }

    const timestamp = result.timestamp || [];
    const quote = result.indicators?.quote?.[0] || {};
    const close = quote.close || [];
    const open = quote.open || [];
    const high = quote.high || [];
    const low = quote.low || [];
    const volume = quote.volume || [];

    const bars: PriceBar[] = [];
    for (let i = 0; i < timestamp.length; i++) {
      const dateStr = new Date(timestamp[i] * 1000).toISOString().split("T")[0];
      if (close[i] !== null && close[i] !== undefined) {
        bars.push({
          ts: dateStr,
          open: open[i] || close[i],
          high: high[i] || close[i],
          low: low[i] || close[i],
          close: close[i],
          volume: volume[i] || 0,
        });
      }
    }

    if (bars.length === 0) {
      throw new Error("No non-null data points found");
    }

    return bars;

  } catch (err: any) {
    console.error(`[BACKTEST ENGINE] Failed to fetch real data for ${ticker}: ${err.message || err}`);
    throw err;
  }
}

/**
 * Standard deviation utility helper
 */
function findStdDev(values: number[]): number {
  if (values.length <= 1) return 0;
  const mean = values.reduce((s, x) => s + x, 0) / values.length;
  const variance = values.reduce((s, x) => s + Math.pow(x - mean, 2), 0) / (values.length - 1);
  return Math.sqrt(variance);
}

/**
 * Downside standard deviation helper (for Sortino Ratio)
 */
function findDownsideStdDev(values: number[]): number {
  const negatives = values.filter(x => x < 0);
  if (negatives.length <= 1) return 0.0001;
  const variance = negatives.reduce((s, x) => s + Math.pow(x, 2), 0) / negatives.length;
  return Math.sqrt(variance);
}

/**
 * Perform Strategy Backtest
 */
export async function runSimulation(
  config: StrategyConfig,
  initialCash: number,
  startDateStr: string,
  endDateStr: string
): Promise<BacktestResponse> {
  const start = new Date(startDateStr);
  const end = new Date(endDateStr);

  // We need to fetch somewhat of a buffer of prices for lookback (at least 200 days prior to start)
  const bufferStart = new Date(start);
  bufferStart.setDate(bufferStart.getDate() - 365); // Fetch 1 year prior for SMAs & lookback

  const universe = config.tickers && config.tickers.length > 0 ? config.tickers : ["SPY", "QQQ", "IWM", "XLK", "XLF"];
  
  // Benchmark (SPY) price history
  const benchmarkPrices = await getPricesForTicker("SPY", bufferStart, end);
  
  // Asset prices cache
  const fullPriceCache: Record<string, PriceBar[]> = {};
  for (const sym of universe) {
    fullPriceCache[sym] = await getPricesForTicker(sym, bufferStart, end);
  }

  // Align dates
  const benchmarkTradingDays = benchmarkPrices.filter(p => new Date(p.ts) >= start);
  const allTradingDates = benchmarkTradingDays.map(p => p.ts);

  if (allTradingDates.length === 0) {
    throw new Error("No trading days found in specified date range.");
  }

  // Pre-calculate index references for performance speed
  const assetPriceMap: Record<string, Record<string, PriceBar>> = {};
  for (const sym of universe) {
    assetPriceMap[sym] = {};
    for (const bar of fullPriceCache[sym]) {
      assetPriceMap[sym][bar.ts] = bar;
    }
  }

  const benchmarkPriceMap: Record<string, PriceBar> = {};
  for (const bar of benchmarkPrices) {
    benchmarkPriceMap[bar.ts] = bar;
  }

  // Initialize Portfolio State
  let cash = initialCash;
  const holdings: Record<string, { qty: number; entryPrice: number }> = {};
  
  const equityCurve: EquityCurvePoint[] = [];
  const drawdownCurve: DrawdownPoint[] = [];
  const trades: Trade[] = [];

  const dailyPortfolioReturns: number[] = [];
  let peakValue = initialCash;
  let maxDrawdown = 0;
  let previousValue = initialCash;

  // V2 State tracking
  let isRiskOff = false;          // Hysteresis state
  let lastRebalDay = -999;        // Track last rebalance
  let portfolioPeak = initialCash; // For conditional rebalance

  // V2 Constants
  const LOOKBACKS = [63, 126, 252]; // Multi-lookback blend
  const SKIP_DAYS = 21;             // Skip-month effect
  const HYSTERESIS = 0.01;          // 1% buffer band
  const EMERGENCY_DD = 0.05;        // 5% emergency exit threshold
  const PORT_DD_TRIG = 0.03;        // 3% portfolio drawdown trigger
  const MOM_WEIGHTS = [0.40, 0.35, 0.25]; // Rank-proportional weights

  // Track initial asset prices for benchmarks
  const firstTradingDate = allTradingDates[0];
  const benchmarkStartPrice = benchmarkPriceMap[firstTradingDate]?.close || 400;

  // Standard Backtest Simulation Inner Loop
  for (let idx = 0; idx < allTradingDates.length; idx++) {
    const today = allTradingDates[idx];
    
    // Core parameters from configuration
    const topN = config.top_n || 3;
    const maxPosSize = (config.max_pos_size || 30) / 100;
    const isSmaFilterOn = config.sma_filter;

    if (config.strategy === "Dual Momentum") {
      // ═══════════════════════════════════════════════════════
      // V2 UPGRADED DUAL MOMENTUM STRATEGY
      // ═══════════════════════════════════════════════════════
      
      const benchmarkIndexInFull = benchmarkPrices.findIndex(p => p.ts === today);

      // ── STEP 1: SPY RISK-OFF WITH HYSTERESIS ──
      let riskOffTriggered = false;
      if (isSmaFilterOn && benchmarkIndexInFull >= 200) {
        const spyPast200 = benchmarkPrices.slice(benchmarkIndexInFull - 200 + 1, benchmarkIndexInFull + 1);
        const spySma200 = spyPast200.reduce((s, x) => s + x.close, 0) / 200;
        const currentSpyClose = benchmarkPrices[benchmarkIndexInFull].close;

        if (isRiskOff) {
          // Currently risk-off: need price above SMA+buffer AND SMA-50 golden cross
          const aboveWithBuffer = currentSpyClose > spySma200 * (1 + HYSTERESIS);
          let sma50Confirm = true;
          if (benchmarkIndexInFull >= 50) {
            const spyPast50 = benchmarkPrices.slice(benchmarkIndexInFull - 50 + 1, benchmarkIndexInFull + 1);
            const spySma50 = spyPast50.reduce((s, x) => s + x.close, 0) / 50;
            sma50Confirm = spySma50 > spySma200;
          }
          if (aboveWithBuffer && sma50Confirm) {
            isRiskOff = false;
          } else {
            riskOffTriggered = true;
          }
        } else {
          // Currently risk-on: trigger risk-off with buffer below SMA-200
          if (currentSpyClose < spySma200 * (1 - HYSTERESIS)) {
            isRiskOff = true;
            riskOffTriggered = true;
          }
        }
      }

      if (riskOffTriggered) {
        // Liquidate ALL positions
        for (const sym of Object.keys(holdings)) {
          const bar = assetPriceMap[sym][today];
          if (bar && holdings[sym].qty > 0) {
            const sellPrice = bar.close;
            const value = holdings[sym].qty * sellPrice;
            const pnl = (sellPrice - holdings[sym].entryPrice) * holdings[sym].qty;
            cash += value;
            trades.push({ date: today + " 16:00", ticker: sym, side: "sell", qty: holdings[sym].qty, price: sellPrice, value, pnl });
            delete holdings[sym];
          }
        }
        // Skip to daily MTM (no further strategy logic today)
      } else {
        // ── STEP 2: EMERGENCY INTRA-MONTH EXITS ──
        let emergencyExits = false;
        for (const sym of Object.keys(holdings)) {
          const bar = assetPriceMap[sym][today];
          if (bar && holdings[sym].entryPrice > 0) {
            const lossPct = (bar.close - holdings[sym].entryPrice) / holdings[sym].entryPrice;
            if (lossPct < -EMERGENCY_DD) {
              const value = holdings[sym].qty * bar.close;
              const pnl = (bar.close - holdings[sym].entryPrice) * holdings[sym].qty;
              cash += value;
              trades.push({ date: today + " 11:00", ticker: sym, side: "sell", qty: holdings[sym].qty, price: bar.close, value, pnl });
              delete holdings[sym];
              emergencyExits = true;
            }
          }
        }

        // ── STEP 3: DETERMINE IF REBALANCE IS NEEDED ──
        const daysSinceRebal = idx - lastRebalDay;
        const isScheduledRebal = daysSinceRebal >= 21 || idx === 0;
        
        // Conditional rebalance: portfolio drawdown > 3%
        const currentPortValue = cash + Object.entries(holdings).reduce((s, [sym, h]) => s + h.qty * (assetPriceMap[sym][today]?.close || h.entryPrice), 0);
        if (currentPortValue > portfolioPeak) portfolioPeak = currentPortValue;
        const portDD = portfolioPeak > 0 ? (portfolioPeak - currentPortValue) / portfolioPeak : 0;
        const isEmergencyRebal = portDD > PORT_DD_TRIG && daysSinceRebal >= 5;

        if ((isScheduledRebal || isEmergencyRebal) && !emergencyExits) {
          lastRebalDay = idx;

          // ── STEP 4: MULTI-LOOKBACK MOMENTUM SCORING ──
          const momentumRankings: { ticker: string; momentum: number; vol: number }[] = [];

          for (const sym of universe) {
            const pricesInFull = fullPriceCache[sym];
            const todayIndexInFull = pricesInFull.findIndex(p => p.ts === today);
            
            if (todayIndexInFull < Math.max(...LOOKBACKS) + SKIP_DAYS + 5) continue;

            // Multi-lookback blended momentum (skip last 21 days)
            const momScores: number[] = [];
            for (const lb of LOOKBACKS) {
              if (todayIndexInFull >= lb + SKIP_DAYS) {
                const recentPrice = pricesInFull[todayIndexInFull - SKIP_DAYS].close;
                const lookbackPrice = pricesInFull[todayIndexInFull - lb - SKIP_DAYS].close;
                if (lookbackPrice > 0) {
                  momScores.push((recentPrice - lookbackPrice) / lookbackPrice);
                }
              }
            }
            if (momScores.length === 0) continue;
            const avgMomentum = momScores.reduce((s, x) => s + x, 0) / momScores.length;

            // Absolute momentum filter
            if (avgMomentum <= 0) continue;

            // 20-day volatility
            if (todayIndexInFull >= 21) {
              const past21 = pricesInFull.slice(todayIndexInFull - 21 + 1, todayIndexInFull + 1);
              const rets: number[] = [];
              for (let pi = 1; pi < past21.length; pi++) {
                rets.push((past21[pi].close - past21[pi - 1].close) / past21[pi - 1].close);
              }
              const vol = findStdDev(rets) * Math.sqrt(252);
              if (vol > 0.001) {
                momentumRankings.push({ ticker: sym, momentum: avgMomentum, vol });
              }
            }
          }

          // ── STEP 5: SELECT TOP N ──
          momentumRankings.sort((a, b) => b.momentum - a.momentum);
          const targetAssets = momentumRankings.slice(0, topN);

          if (targetAssets.length === 0) {
            // No positive momentum — go to cash
            for (const sym of Object.keys(holdings)) {
              const bar = assetPriceMap[sym][today];
              if (bar && holdings[sym].qty > 0) {
                cash += holdings[sym].qty * bar.close;
                const pnl = (bar.close - holdings[sym].entryPrice) * holdings[sym].qty;
                trades.push({ date: today + " 16:00", ticker: sym, side: "sell", qty: holdings[sym].qty, price: bar.close, value: holdings[sym].qty * bar.close, pnl });
                delete holdings[sym];
              }
            }
          } else {
            const targetTickers = targetAssets.map(x => x.ticker);

            // Liquidate holdings not in target
            for (const sym of Object.keys(holdings)) {
              if (!targetTickers.includes(sym)) {
                const bar = assetPriceMap[sym][today];
                if (bar) {
                  const pnl = (bar.close - holdings[sym].entryPrice) * holdings[sym].qty;
                  cash += holdings[sym].qty * bar.close;
                  trades.push({ date: today + " 16:00", ticker: sym, side: "sell", qty: holdings[sym].qty, price: bar.close, value: holdings[sym].qty * bar.close, pnl });
                  delete holdings[sym];
                }
              }
            }

            // ── STEP 6: MOMENTUM-WEIGHTED + VOL-ADJUSTED SIZING ──
            const totalPortValue2 = cash + Object.entries(holdings).reduce((s, [sym, h]) => s + h.qty * (assetPriceMap[sym][today]?.close || h.entryPrice), 0);
            
            // Rank weights (40/35/25) blended with inverse vol weights
            const invVols: Record<string, number> = {};
            let totalInv = 0;
            for (const ta of targetAssets) {
              const iv = 1.0 / ta.vol;
              invVols[ta.ticker] = iv;
              totalInv += iv;
            }

            const finalWeights: Record<string, number> = {};
            for (let ti = 0; ti < targetAssets.length; ti++) {
              const t = targetAssets[ti].ticker;
              const rankW = ti < MOM_WEIGHTS.length ? MOM_WEIGHTS[ti] : 1.0 / targetAssets.length;
              const volW = invVols[t] / totalInv;
              finalWeights[t] = Math.min(0.5 * rankW + 0.5 * volW, maxPosSize);
            }

            // Normalize
            const totalW = Object.values(finalWeights).reduce((s, w) => s + w, 0);
            if (totalW > 0) {
              for (const t of Object.keys(finalWeights)) {
                finalWeights[t] = finalWeights[t] / totalW;
                // Apply vol scalar (target 10% portfolio vol)
                const portVolEst = targetAssets.reduce((s, ta) => s + (finalWeights[ta.ticker] || 0) * ta.vol, 0);
                const volScalar = portVolEst > 0 ? Math.min(0.10 / portVolEst, 1.5) : 1.0;
                finalWeights[t] = Math.min(finalWeights[t] * volScalar, maxPosSize);
              }
            }

            // Execute buys
            for (const ta of targetAssets) {
              const sym = ta.ticker;
              const bar = assetPriceMap[sym][today];
              if (!bar) continue;
              
              const targetDollars = totalPortValue2 * (finalWeights[sym] || 0);
              const currentHold = holdings[sym];
              const currentVal = currentHold ? currentHold.qty * bar.close : 0;

              if (currentVal === 0) {
                const qtyToBuy = Math.floor(targetDollars / bar.close);
                if (qtyToBuy > 0 && cash >= qtyToBuy * bar.close) {
                  cash -= qtyToBuy * bar.close;
                  holdings[sym] = { qty: qtyToBuy, entryPrice: bar.close };
                  trades.push({ date: today + " 09:30", ticker: sym, side: "buy", qty: qtyToBuy, price: bar.close, value: qtyToBuy * bar.close, pnl: 0 });
                }
              } else if (Math.abs(currentVal - targetDollars) / totalPortValue2 > 0.05) {
                const desiredQty = Math.floor(targetDollars / bar.close);
                const deltaQty = desiredQty - currentHold.qty;
                if (deltaQty > 0 && cash >= deltaQty * bar.close) {
                  cash -= deltaQty * bar.close;
                  const newQty = currentHold.qty + deltaQty;
                  const newEntry = ((currentHold.qty * currentHold.entryPrice) + (deltaQty * bar.close)) / newQty;
                  holdings[sym] = { qty: newQty, entryPrice: newEntry };
                  trades.push({ date: today + " 10:15", ticker: sym, side: "buy", qty: deltaQty, price: bar.close, value: deltaQty * bar.close, pnl: 0 });
                } else if (deltaQty < 0) {
                  const absDelta = Math.abs(deltaQty);
                  cash += absDelta * bar.close;
                  const pnl = (bar.close - currentHold.entryPrice) * absDelta;
                  holdings[sym] = { qty: currentHold.qty - absDelta, entryPrice: currentHold.entryPrice };
                  trades.push({ date: today + " 14:30", ticker: sym, side: "sell", qty: absDelta, price: bar.close, value: absDelta * bar.close, pnl });
                }
              }
            }

            portfolioPeak = cash + Object.entries(holdings).reduce((s, [sym, h]) => s + h.qty * (assetPriceMap[sym][today]?.close || h.entryPrice), 0);
          }
        }
      }

    } else if (config.strategy === "SMA Crossover") {
      // 2. SMA CROSSOVER STRATEGY: run golden cross (SMA-50 > SMA-200) for active assets
      // Standard monthly/weekly check on signal is common to prevent overtrading, but on each day we can update state
      for (const sym of universe) {
        const pricesInFull = fullPriceCache[sym];
        const todayIndexInFull = pricesInFull.findIndex(p => p.ts === today);
        
        if (todayIndexInFull >= 200) {
          const past50 = pricesInFull.slice(todayIndexInFull - 50 + 1, todayIndexInFull + 1);
          const sma50 = past50.reduce((s, x) => s + x.close, 0) / 50;
          
          const past200 = pricesInFull.slice(todayIndexInFull - 200 + 1, todayIndexInFull + 1);
          const sma200 = past200.reduce((s, x) => s + x.close, 0) / 200;
          
          const bar = assetPriceMap[sym][today];
          if (!bar) continue;
          
          const isGoldenCross = sma50 > sma200;
          const currentHold = holdings[sym];
          
          if (isGoldenCross && !currentHold) {
            // Golden Cross: Buy
            const allocationDollars = (cash + Object.entries(holdings).reduce((sum, [s, h]) => sum + h.qty * (assetPriceMap[s][today]?.close || h.entryPrice), 0)) / universe.length;
            const qtyToBuy = Math.floor((allocationDollars * 0.95) / bar.close); // Buffer
            if (qtyToBuy > 0 && cash >= qtyToBuy * bar.close) {
              cash -= qtyToBuy * bar.close;
              holdings[sym] = { qty: qtyToBuy, entryPrice: bar.close };
              trades.push({
                date: today + " 09:30",
                ticker: sym,
                side: "buy",
                qty: qtyToBuy,
                price: bar.close,
                value: qtyToBuy * bar.close,
                pnl: 0,
              });
            }
          } else if (!isGoldenCross && currentHold) {
            // Death Cross: Liquidate Position
            const sellPrice = bar.close;
            const value = currentHold.qty * sellPrice;
            const pnl = (sellPrice - currentHold.entryPrice) * currentHold.qty;
            cash += value;
            trades.push({
              date: today + " 15:45",
              ticker: sym,
              side: "sell",
              qty: currentHold.qty,
              price: sellPrice,
              value,
              pnl,
            });
            delete holdings[sym];
          }
        }
      }

    } else if (config.strategy === "Volatility Target" && (idx % 21 === 0 || idx === 0)) {
      // 3. VOLATILITY TARGET STRATEGY
      // Rebalance inversely to 20-day historical volatility
      const targetVolAnnual = 0.10; // Annualized 10%
      const targetVolDaily = targetVolAnnual / Math.sqrt(252);
      
      const vols: Record<string, number> = {};
      let totalInverseVol = 0;

      for (const sym of universe) {
        const pricesInFull = fullPriceCache[sym];
        const todayIndexInFull = pricesInFull.findIndex(p => p.ts === today);
        
        if (todayIndexInFull >= 21) {
          const past21 = pricesInFull.slice(todayIndexInFull - 21 + 1, todayIndexInFull + 1);
          const returns21: number[] = [];
          for (let pIdx = 1; pIdx < past21.length; pIdx++) {
            returns21.push((past21[pIdx].close - past21[pIdx - 1].close) / past21[pIdx - 1].close);
          }
          const assetDailyVol = findStdDev(returns21) || 0.01;
          vols[sym] = assetDailyVol;
          totalInverseVol += 1.0 / assetDailyVol;
        } else {
          vols[sym] = 0.015; // default estimate
          totalInverseVol += 1.0 / 0.015;
        }
      }

      // Calculate portfolio size
      const totalPortValue = cash + Object.entries(holdings).reduce((sum, [sym, h]) => {
        const pr = assetPriceMap[sym][today]?.close || h.entryPrice;
        return sum + h.qty * pr;
      }, 0);

      // Distribute targets. Target weight for each is targetVolDaily / assetVol
      // Combined max leverage 1.5x
      const targetWeights: Record<string, number> = {};
      let totalWeight = 0;
      for (const sym of universe) {
        const wt = targetVolDaily / vols[sym];
        targetWeights[sym] = wt;
        totalWeight += wt;
      }

      // Cap leverage total at 1.5
      if (totalWeight > 1.5) {
        const scale = 1.5 / totalWeight;
        for (const sym of universe) {
          targetWeights[sym] *= scale;
        }
      }

      // Execute Trades to Match Target Weights
      for (const sym of universe) {
        const targetDollars = totalPortValue * targetWeights[sym];
        const bar = assetPriceMap[sym][today];
        if (!bar) continue;

        const currentHold = holdings[sym];
        const currentVal = currentHold ? currentHold.qty * bar.close : 0;
        const desiredQty = Math.floor(targetDollars / bar.close);
        
        if (!currentHold && desiredQty > 0) {
          // Open long
          const value = desiredQty * bar.close;
          if (cash >= value) {
            cash -= value;
            holdings[sym] = { qty: desiredQty, entryPrice: bar.close };
            trades.push({
              date: today + " 09:30",
              ticker: sym,
              side: "buy",
              qty: desiredQty,
              price: bar.close,
              value,
              pnl: 0,
            });
          }
        } else if (currentHold) {
          const deltaQty = desiredQty - currentHold.qty;
          if (deltaQty > 10 || deltaQty < -10) { // rebalance buffer threshold
            if (deltaQty > 0 && cash >= deltaQty * bar.close) {
              cash -= deltaQty * bar.close;
              const newQty = currentHold.qty + deltaQty;
              const newEntry = ((currentHold.qty * currentHold.entryPrice) + (deltaQty * bar.close)) / newQty;
              holdings[sym] = { qty: newQty, entryPrice: newEntry };
              trades.push({
                date: today + " 10:45",
                ticker: sym,
                side: "buy",
                qty: deltaQty,
                price: bar.close,
                value: deltaQty * bar.close,
                pnl: 0,
              });
            } else if (deltaQty < 0) {
              const absQty = Math.abs(deltaQty);
              cash += absQty * bar.close;
              const pnl = (bar.close - currentHold.entryPrice) * absQty;
              holdings[sym] = { qty: currentHold.qty - absQty, entryPrice: currentHold.entryPrice };
              trades.push({
                date: today + " 14:15",
                ticker: sym,
                side: "sell",
                qty: absQty,
                price: bar.close,
                value: absQty * bar.close,
                pnl,
              });
              if (holdings[sym].qty === 0) {
                delete holdings[sym];
              }
            }
          }
        }
      }
    }

    // Daily Mark-to-Market calculation
    let heldAssetsValue = 0;
    for (const sym of Object.keys(holdings)) {
      const todayPrice = assetPriceMap[sym][today]?.close || holdings[sym].entryPrice;
      heldAssetsValue += holdings[sym].qty * todayPrice;
    }

    const currentPortValue = cash + heldAssetsValue;
    const dailyReturn = (currentPortValue - previousValue) / previousValue;
    dailyPortfolioReturns.push(dailyReturn);

    // Track running peak and drawdowns
    if (currentPortValue > peakValue) {
      peakValue = currentPortValue;
    }
    const currentDrawdown = ((peakValue - currentPortValue) / peakValue) * 100;
    if (currentDrawdown > maxDrawdown) {
      maxDrawdown = currentDrawdown;
    }

    // Calculate benchmark benchmark performance
    const spyTodayPrice = benchmarkPriceMap[today]?.close || benchmarkPrices[benchmarkPrices.length - 1].close;
    const benchmarkVal = initialCash * (spyTodayPrice / benchmarkStartPrice);

    equityCurve.push({
      date: today,
      strategy: currentPortValue,
      benchmark: benchmarkVal,
    });

    drawdownCurve.push({
      date: today,
      drawdown: -currentDrawdown, // negative representation
    });

    previousValue = currentPortValue;
  }

  // Backtest Ended. Compile performance analytics metrics.
  const finalValue = equityCurve[equityCurve.length - 1].strategy;
  const totalReturnPct = ((finalValue - initialCash) / initialCash) * 100;

  const years = allTradingDates.length / 252;
  const annReturnPct = (Math.pow(finalValue / initialCash, years > 0 ? 1 / years : 1) - 1) * 100;

  // Volatility
  const volPct = (findStdDev(dailyPortfolioReturns) * Math.sqrt(252)) * 100;
  
  // Downside Vol (for Sortino)
  const downsideVolPct = (findDownsideStdDev(dailyPortfolioReturns) * Math.sqrt(252)) * 100;

  // Sharpe (assuming risk free rate of 2%)
  const rf = 2.0;
  const sharpeRatio = volPct > 0 ? (annReturnPct - rf) / volPct : 0;
  
  // Sortino
  const sortinoRatio = downsideVolPct > 0 ? (annReturnPct - rf) / downsideVolPct : 0;

  // Calmar
  const calmarRatio = maxDrawdown > 0 ? annReturnPct / maxDrawdown : annReturnPct / 0.1;

  // Win Rate & profit factor from trades
  const closedTrades = trades.filter(t => t.pnl !== 0);
  const winTrades = closedTrades.filter(t => t.pnl > 0);
  const winRatePct = closedTrades.length > 0 ? (winTrades.length / closedTrades.length) * 100 : 50.0;

  const grossProfit = winTrades.reduce((s, t) => s + t.pnl, 0);
  const grossLoss = Math.abs(closedTrades.filter(t => t.pnl < 0).reduce((s, t) => s + t.pnl, 0));
  const profitFactor = grossLoss > 0 ? grossProfit / grossLoss : grossProfit > 0 ? 9.99 : 1.0;

  const metrics: MetricSet = {
    total_return_pct: Number(totalReturnPct.toFixed(2)),
    ann_return_pct: Number(annReturnPct.toFixed(2)),
    max_drawdown_pct: Number(maxDrawdown.toFixed(2)),
    calmar_ratio: Number(calmarRatio.toFixed(2)),
    sharpe_ratio: Number(sharpeRatio.toFixed(2)),
    sortino_ratio: Number(sortinoRatio.toFixed(2)),
    win_rate_pct: Number(winRatePct.toFixed(2)),
    profit_factor: Number(profitFactor.toFixed(2)),
    volatility_pct: Number(volPct.toFixed(2)),
  };

  return {
    equity_curve: equityCurve,
    drawdown_series: drawdownCurve,
    trades: trades.reverse(), // Sort recent trades first
    metrics,
  };
}
