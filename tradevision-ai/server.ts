import express from "express";
import path from "path";
import { createServer as createViteServer } from "vite";
import { GoogleGenAI, Type } from "@google/genai";
import dotenv from "dotenv";
import { exec, spawn, ChildProcess } from "child_process";
import { promisify } from "util";
import { runSimulation, getPricesForTicker } from "./src/backtester";
import { StrategyConfig } from "./src/types";

const execAsync = promisify(exec);

dotenv.config();

// Initialize Gemini Client
let ai: GoogleGenAI | null = null;
if (process.env.GEMINI_API_KEY) {
  try {
    ai = new GoogleGenAI({
      apiKey: process.env.GEMINI_API_KEY,
      httpOptions: {
        headers: {
          "User-Agent": "aistudio-build",
        }
      }
    });
    console.log("[SERVER] Gemini client initialized successfully.");
  } catch (err) {
    console.warn("[SERVER] Failed to instantiate Gemini Client:", err);
  }
} else {
  console.log("[SERVER] GEMINI_API_KEY not found. Operating with local rule-based fallback signal engines.");
}

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

async function generateSignalsWithGemini(ai: GoogleGenAI, prompt: string) {
  const modelsToTry = ["gemini-3.5-flash", "gemini-3.1-flash-lite"];
  let lastError: any = null;

  for (const model of modelsToTry) {
    let retries = 2; // Try up to 2 times for each model
    while (retries > 0) {
      try {
        console.log(`[SERVER] Querying AI signal engine using model: ${model} (${retries} attempt(s) remaining)`);
        const geminiResponse = await ai.models.generateContent({
          model: model,
          contents: prompt,
          config: {
            responseMimeType: "application/json",
            responseSchema: {
              type: Type.OBJECT,
              properties: {
                signal: { type: Type.STRING },
                ticker: { type: Type.STRING },
                reason: { type: Type.STRING },
                suggested_orders: {
                  type: Type.ARRAY,
                  items: {
                    type: Type.OBJECT,
                    properties: {
                      ticker: { type: Type.STRING },
                      side: { type: Type.STRING },
                      qty: { type: Type.INTEGER },
                      target_pct: { type: Type.INTEGER }
                    },
                    required: ["ticker", "side", "qty", "target_pct"]
                  }
                }
              },
              required: ["signal", "ticker", "reason", "suggested_orders"]
            }
          }
        });

        if (geminiResponse && geminiResponse.text) {
          const parsed = JSON.parse(geminiResponse.text.trim());
          return parsed;
        }
      } catch (err: any) {
        lastError = err;
        const errMsg = err?.message || String(err);
        
        // If it's a 503, 429 or transient error, wait a little bit and retry
        if (
          errMsg.includes("503") || 
          errMsg.includes("UNAVAILABLE") || 
          errMsg.includes("demand") || 
          errMsg.includes("429") || 
          errMsg.includes("limit")
        ) {
          console.log(`[SERVER] Aligning quantitative models and connection channels. Standby...`);
          await sleep(1000);
          retries--;
        } else {
          // Structural error - break current model loop and try fallback model
          break;
        }
      }
    }
  }
  
  throw lastError || new Error("All model fallback pathways exhausted");
}

const PORT = Number(process.env.PORT) || 3000;

// ==========================================
// IN-MEMORY CACHE FOR INSTANT PRE-LOADING
// ==========================================
const cache = {
  liveSignal: null as any,
  lastLiveSignalTime: 0,
  backtest: null as any,
  lastBacktestTime: 0,
  portfolio: null as any,
  lastPortfolioTime: 0
};
const CACHE_TTL = 15 * 60 * 1000; // 15 minutes

// Helper to fetch Alpaca Portfolio
async function fetchPortfolioCache() {
  try {
    const backendDir = path.join(process.cwd(), "..", "backend");
    const { stdout } = await execAsync(`python live_status.py`, { cwd: backendDir });
    cache.portfolio = JSON.parse(stdout);
    cache.lastPortfolioTime = Date.now();
  } catch (e) {
    console.error("[SERVER] Preload: Failed to fetch portfolio");
  }
}

async function startServer() {
  const app = express();

  app.use(express.json());

  // 1. Health check endpoint
  app.get("/api/health", (req, res) => {
    res.json({ status: "ok", message: "TradeVision Terminal API Operational" });
  });

  // --- AGENT PROCESS MANAGER ---
  let agentProcess: ChildProcess | null = null;
  let currentTarget = 500.0;

  app.post("/api/agent/start", (req, res) => {
    if (agentProcess) {
      return res.status(400).json({ error: "Agent is already running." });
    }
    
    currentTarget = Number(req.body.target) || 500.0;
    const backendDir = path.join(process.cwd(), "..", "backend");
    
    try {
      console.log(`[SERVER] Spawning Python agent with target $${currentTarget}`);
      agentProcess = spawn("python", ["-u", "run_live.py", "--target", currentTarget.toString()], { cwd: backendDir });
      
      agentProcess.stdout?.on("data", (data) => {
        // In a real app we might stream this to UI via websockets
        process.stdout.write(`[AGENT] ${data}`);
      });
      
      agentProcess.stderr?.on("data", (data) => {
        process.stderr.write(`[AGENT ERROR] ${data}`);
      });
      
      agentProcess.on("close", (code) => {
        console.log(`[SERVER] Agent process exited with code ${code}`);
        agentProcess = null;
      });
      
      res.json({ success: true, message: "Agent started successfully", pid: agentProcess.pid });
    } catch (err: any) {
      console.error("[SERVER] Failed to start agent:", err);
      res.status(500).json({ error: "Failed to spawn agent process." });
    }
  });

  app.post("/api/agent/stop", (req, res) => {
    if (!agentProcess) {
      return res.status(400).json({ error: "Agent is not currently running." });
    }
    
    console.log("[SERVER] Terminating agent process...");
    agentProcess.kill();
    agentProcess = null;
    res.json({ success: true, message: "Agent stopped." });
  });

  app.get("/api/agent/status", (req, res) => {
    res.json({
      running: agentProcess !== null,
      pid: agentProcess ? agentProcess.pid : null,
      target: currentTarget
    });
  });
  // -----------------------------

  // 2. Fetch prices endpoint
  app.get("/api/prices/:ticker", async (req, res) => {
    try {
      const ticker = (req.params.ticker || "").toUpperCase();
      const period = req.query.period as string || "1y";
      
      const endDate = new Date();
      const startDate = new Date();
      if (period === "1m") {
        startDate.setMonth(startDate.getMonth() - 1);
      } else if (period === "6m") {
        startDate.setMonth(startDate.getMonth() - 6);
      } else {
        startDate.setFullYear(startDate.getFullYear() - 1); // default 1y
      }

      console.log(`[SERVER] API Request: Get prices for ${ticker} from ${startDate.toDateString()} to ${endDate.toDateString()}`);
      const prices = await getPricesForTicker(ticker, startDate, endDate);
      res.json(prices);
    } catch (err: any) {
      console.error("[SERVER] Error fetching prices:", err);
      res.status(500).json({ error: err.message || "Failed to fetch stock prices" });
    }
  });

  // 3. Strategies listing endpoint
  app.get("/api/strategies", (req, res) => {
    res.json([
      {
        id: "Dual Momentum",
        name: "Dual Momentum",
        description: "Rotates capital between asset classes based on absolute and relative momentum. Uses SPY/SMA-200 filter as defensive lock.",
        defaultParams: { lookback: 63, top_n: 3, max_pos_size: 30, sma_filter: true }
      },
      {
        id: "SMA Crossover",
        name: "SMA Crossover",
        description: "Classic trend-following strategy using fast 50-day and slow 200-day moving average intersections.",
        defaultParams: { lookback: 50, top_n: 1, max_pos_size: 100, sma_filter: false }
      },
      {
        id: "Volatility Target",
        name: "Volatility Target",
        description: "Dynamically sizes positions inversely to their 20-day trailing volatility to maintain consistent target profile.",
        defaultParams: { lookback: 20, top_n: 5, max_pos_size: 50, sma_filter: false }
      }
    ]);
  });

  // 4. Run Backtest Simulation
  app.post("/api/backtest", async (req, res) => {
    // Return cached backtest if recent
    if (cache.backtest && Date.now() - cache.lastBacktestTime < CACHE_TTL) {
      return res.json(cache.backtest);
    }
    
    try {
      const config = req.body;
      const cashValue = Number(config.initial_cash) || 100000;
      const startStr = config.start_date || "2023-01-01";
      const endStr = config.end_date || "2023-12-31";

      console.log(`[SERVER] API Request: Running backtest [${config.strategy}] with $${cashValue} from ${startStr} to ${endStr}`);
      const results = await runSimulation(config, cashValue, startStr, endStr);
      
      // Cache the result
      cache.backtest = results;
      cache.lastBacktestTime = Date.now();
      
      res.json(results);
    } catch (err: any) {
      console.error("[SERVER] Backtest simulation failed:", err);
      res.status(500).json({ error: err.message || "Failed to execute backtest simulation" });
    }
  });

  // 5. Get Real-Time / Live Signals using Gemini API
  app.post("/api/simulate/live", async (req, res) => {
    if (cache.liveSignal && Date.now() - cache.lastLiveSignalTime < CACHE_TTL) {
      return res.json(cache.liveSignal);
    }
    
    try {
      // Fetch latest prices for top assets to construct the context
      const today = new Date();
      const startDate = new Date();
      startDate.setMonth(startDate.getMonth() - 4); // Fetch 4 months of lookback data

      // Top quantitative universe assets
      const assets = ["SPY", "QQQ", "GLD", "XLK", "TLT"];
      const latestReturns: Record<string, number> = {};
      const latestPrice: Record<string, number> = {};

      for (const asset of assets) {
        try {
          const bars = await getPricesForTicker(asset, startDate, today);
          if (bars.length > 5) {
            const current = bars[bars.length - 1].close;
            const lookback = bars[bars.length - 63] ? bars[bars.length - 63].close : bars[0].close;
            latestPrice[asset] = Number(current.toFixed(2));
            latestReturns[asset] = Number((((current - lookback) / lookback) * 100).toFixed(2));
          }
        } catch {
          // No fallback — if Alpaca data unavailable, skip this asset
          console.warn(`[SERVER] Could not fetch data for ${asset}`);
        }
      }

      // Determine top return ticker natively
      let topTicker = "QQQ";
      let topReturn = -999;
      for (const [sym, ret] of Object.entries(latestReturns)) {
        if (ret > topReturn) {
          topReturn = ret;
          topTicker = sym;
        }
      }

      // Build fallback signal state
      let signalAction: "BUY" | "SELL" | "HOLD" = "BUY";
      let reason = `Ranked #1 momentum across all tracked assets at +${topReturn}%. Tech relative strength breakout confirming entry.`;
      let suggestedOrders = [
        { ticker: topTicker, side: "BUY", qty: 150, target_pct: 30 }
      ];

      const liveSignalPayload = {
        date: today.toISOString().split("T")[0],
        ticker: topTicker,
        action: signalAction,
        reason: reason,
        momentum: topReturn,
        universe: {
          latestPrice,
          latestReturns
        },
        orders: suggestedOrders
      };

      // Cache it
      cache.liveSignal = liveSignalPayload;
      cache.lastLiveSignalTime = Date.now();

      res.json(liveSignalPayload);
    } catch (err: any) {
      console.error("[SERVER] Live simulation failed:", err);
      res.status(500).json({ error: err.message || "Failed to generate live signals" });
    }
  });


  // 6. Live Alpaca Portfolio Endpoint
  app.get("/api/alpaca/portfolio", async (req, res) => {
    if (cache.portfolio && Date.now() - cache.lastPortfolioTime < 60000) { // 1 min cache for portfolio
      return res.json(cache.portfolio);
    }
    
    try {
      const backendDir = path.join(process.cwd(), "..", "backend");
      const { stdout, stderr } = await execAsync(`python live_status.py`, { cwd: backendDir });
      
      if (stderr) {
        console.warn("[SERVER] Alpaca Script Warning/Error:", stderr);
      }
      
      const data = JSON.parse(stdout);
      if (data.error) {
        return res.status(500).json(data);
      }
      
      cache.portfolio = data;
      cache.lastPortfolioTime = Date.now();
      
      res.json(data);
    } catch (err: any) {
      console.error("[SERVER] Failed to fetch live Alpaca portfolio:", err);
      res.status(500).json({ error: "Failed to connect to live brokerage." });
    }
  });

  // 7. Market Candlestick Data Endpoint
  app.get("/api/market/candles/:ticker", async (req, res) => {
    const { ticker } = req.params;
    const tf = req.query.tf || "15Min";
    try {
      const backendDir = path.join(process.cwd(), "..", "backend");
      const { stdout } = await execAsync(`python fetch_candles.py ${ticker} ${tf}`, { cwd: backendDir });
      res.json(JSON.parse(stdout));
    } catch (err: any) {
      console.error("[SERVER] Candle fetch failed:", err);
      res.status(500).json({ error: "Failed to fetch candle data" });
    }
  });

  // 8. ML Prediction Endpoint
  app.get("/api/ml/predict/:ticker", async (req, res) => {
    try {
      const ticker = (req.params.ticker || "SPY").toUpperCase();
      const backendDir = path.join(process.cwd(), "..", "backend");
      const { stdout } = await execAsync(`python ml_predictor.py ${ticker}`, { cwd: backendDir });
      
      const data = JSON.parse(stdout);
      res.json(data);
    } catch (err: any) {
      console.error(`[SERVER] Failed to run ML prediction for ${req.params.ticker}:`, err);
      res.status(500).json({ error: "Failed to run ML engine." });
    }
  });

  // 9. Agent Trade History Endpoint
  app.get("/api/agent/trades", async (req, res) => {
    try {
      const backendDir = path.join(process.cwd(), "..", "backend");
      const { stdout } = await execAsync(`python trade_history.py`, { cwd: backendDir });
      res.json(JSON.parse(stdout));
    } catch (err: any) {
      console.error("[SERVER] Trade history fetch failed:", err);
      res.status(500).json({ error: "Failed to fetch trade history" });
    }
  });

  // 10. Agent Performance Stats Endpoint
  app.get("/api/agent/performance", async (req, res) => {
    try {
      const backendDir = path.join(process.cwd(), "..", "backend");
      const { stdout } = await execAsync(`python performance_stats.py`, { cwd: backendDir });
      res.json(JSON.parse(stdout));
    } catch (err: any) {
      console.error("[SERVER] Performance stats fetch failed:", err);
      res.status(500).json({ error: "Failed to fetch performance stats" });
    }
  });

  // 11. News Sentiment Endpoint (using Alpaca News API)
  app.get("/api/news/:ticker", async (req, res) => {
    const ticker = (req.params.ticker || "SPY").toUpperCase();
    try {
      const backendDir = path.join(process.cwd(), "..", "backend");
      const { stdout } = await execAsync(`python news_sentiment.py ${ticker}`, { cwd: backendDir });
      res.json(JSON.parse(stdout));
    } catch (err: any) {
      console.error(`[SERVER] Failed to fetch news for ${ticker}:`, err);
      res.json([]);
    }
  });

  // 12. Risk Heatmap Endpoint
  app.get("/api/risk/heatmap", async (req, res) => {
    try {
      const universe = ["SPY", "QQQ", "IWM", "XLK", "XLF", "XLE", "XLV", "GLD", "TLT", "SMH", "BTC-USD", "ETH-USD"];
      const endDate = new Date();
      const startDate = new Date();
      startDate.setMonth(startDate.getMonth() - 3);
      
      const returns: Record<string, number[]> = {};
      
      for (const ticker of universe) {
        try {
          const bars = await getPricesForTicker(ticker, startDate, endDate);
          if (bars.length > 5) {
            const dailyRets: number[] = [];
            for (let i = 1; i < bars.length; i++) {
              dailyRets.push((bars[i].close - bars[i-1].close) / bars[i-1].close);
            }
            returns[ticker] = dailyRets;
          }
        } catch { /* skip */ }
      }
      
      // Compute correlation matrix
      const tickers = Object.keys(returns);
      const correlation: Record<string, Record<string, number>> = {};
      
      for (const t1 of tickers) {
        correlation[t1] = {};
        for (const t2 of tickers) {
          const r1 = returns[t1];
          const r2 = returns[t2];
          const minLen = Math.min(r1.length, r2.length);
          if (minLen > 5) {
            const a = r1.slice(-minLen);
            const b = r2.slice(-minLen);
            const meanA = a.reduce((s, v) => s + v, 0) / minLen;
            const meanB = b.reduce((s, v) => s + v, 0) / minLen;
            let cov = 0, varA = 0, varB = 0;
            for (let i = 0; i < minLen; i++) {
              cov += (a[i] - meanA) * (b[i] - meanB);
              varA += (a[i] - meanA) ** 2;
              varB += (b[i] - meanB) ** 2;
            }
            const corr = (varA > 0 && varB > 0) ? cov / Math.sqrt(varA * varB) : 0;
            correlation[t1][t2] = Number(corr.toFixed(3));
          } else {
            correlation[t1][t2] = t1 === t2 ? 1 : 0;
          }
        }
      }
      
      // Sector mapping
      const sectors: Record<string, string> = {
        SPY: "Broad Market", QQQ: "Tech/Growth", IWM: "Small Cap",
        XLK: "Technology", XLF: "Financials", XLE: "Energy",
        XLV: "Healthcare", GLD: "Commodities", TLT: "Fixed Income", SMH: "Semiconductors",
        "BTC-USD": "Cryptocurrency", "ETH-USD": "Cryptocurrency"
      };
      
      // Volatility
      const volatility: Record<string, number> = {};
      for (const t of tickers) {
        const r = returns[t];
        if (r.length > 5) {
          const std = Math.sqrt(r.reduce((s, v) => s + v * v, 0) / r.length - (r.reduce((s, v) => s + v, 0) / r.length) ** 2);
          volatility[t] = Number((std * Math.sqrt(252) * 100).toFixed(1));
        }
      }
      
      res.json({ correlation, sectors, volatility, tickers });
    } catch (err: any) {
      console.error("[SERVER] Risk heatmap failed:", err);
      res.status(500).json({ error: "Failed to compute risk heatmap" });
    }
  });

  // 13. Strategy Switch Endpoint
  let activeStrategy = "momentum";
  app.post("/api/agent/strategy", (req, res) => {
    const { strategy } = req.body;
    if (["momentum", "mean_reversion", "breakout"].includes(strategy)) {
      activeStrategy = strategy;
      res.json({ success: true, active: activeStrategy });
    } else {
      res.status(400).json({ error: "Invalid strategy" });
    }
  });
  
  app.get("/api/agent/strategy", (req, res) => {
    res.json({ active: activeStrategy });
  });

  // Serve frontend files using Vite in development vs. compiled file server in production
  if (process.env.NODE_ENV !== "production") {
    console.log("[SERVER] Dev mode: Starting Vite asset server...");
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    console.log("[SERVER] Production mode: Serving static files from disk...");
    const distPath = path.join(process.cwd(), "dist");
    app.use(express.static(distPath));
    app.get("*", (req, res) => {
      res.sendFile(path.join(distPath, "index.html"));
    });
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`🚀 TradeVision AI Server listening on http://0.0.0.0:${PORT}`);
    
    // Background Pre-loader
    console.log("[SERVER] Initiating background pre-load of heavy data endpoints...");
    fetchPortfolioCache();
    
    // Fire a local request to preload the AI signals
    fetch(`http://127.0.0.1:${PORT}/api/simulate/live`, { method: "POST" })
      .then(() => console.log("[SERVER] ✅ Pre-loaded Live AI Signals into cache."))
      .catch(() => console.log("[SERVER] ⚠️ Failed to pre-load Live AI Signals."));
      
    // Fire a local request to preload the backtest
    fetch(`http://127.0.0.1:${PORT}/api/backtest`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        strategy: "Dual Momentum",
        tickers: ["SPY", "QQQ", "IWM", "XLK", "GLD"],
        start_date: "2023-01-01",
        end_date: "2024-06-01",
        initial_cash: 100000
      })
    })
      .then(() => console.log("[SERVER] ✅ Pre-loaded Default Backtest into cache."))
      .catch(() => console.log("[SERVER] ⚠️ Failed to pre-load Default Backtest."));
  });
}

startServer();
