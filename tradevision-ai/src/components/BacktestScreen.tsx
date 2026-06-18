import React, { useState, useEffect, useMemo } from "react";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { Play, TrendingUp, ShieldAlert, CheckCircle, RefreshCw, Layers, Calendar, DollarSign, Database, Loader2, Trophy, BarChart3 } from "lucide-react";
import { BacktestResponse, StrategyType, Trade } from "../types";

// Strategy color map for consistent theming
const STRATEGY_COLORS: Record<string, string> = {
  "Dual Momentum": "#6366F1",
  "SMA Crossover": "#22D3EE",
  "Volatility Target": "#F59E0B",
};

export default function BacktestScreen() {
  const [strategy, setStrategy] = useState<StrategyType>("Dual Momentum");
  const [startDate, setStartDate] = useState("2023-01-01");
  const [endDate, setEndDate] = useState("2023-12-31");
  const [initialCash, setInitialCash] = useState("100000");
  
  const [loading, setLoading] = useState(false);
  const [resultsMap, setResultsMap] = useState<Record<string, BacktestResponse>>({});
  const [errorStr, setErrorStr] = useState<string | null>(null);

  // Trigger default backtest simulation on initial load
  useEffect(() => {
    executeBacktest();
  }, []);

  const executeBacktest = async () => {
    try {
      setLoading(true);
      setErrorStr(null);
      
      const parsedCash = Number(initialCash.replace(/[^0-9.]/g, "")) || 100000;
      const commonBody = {
        tickers: ["SPY", "QQQ", "IWM", "XLK", "XLF", "XLE", "XLV", "GLD", "TLT"],
        start_date: startDate,
        end_date: endDate,
        initial_cash: parsedCash,
      };
      
      // Run all 3 strategies in parallel for comparison
      const strategies: StrategyType[] = ["Dual Momentum", "SMA Crossover", "Volatility Target"];
      
      const promises = strategies.map(strat => 
        fetch("/api/backtest", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ ...commonBody, strategy: strat }),
        }).then(res => {
          if (!res.ok) throw new Error(`HTTP error ${res.status}`);
          return res.json() as Promise<BacktestResponse>;
        })
      );

      const [dualMom, smaCross, volTarget] = await Promise.all(promises);
      
      setResultsMap({
        "Dual Momentum": dualMom,
        "SMA Crossover": smaCross,
        "Volatility Target": volTarget,
      });
    } catch (err: any) {
      console.error("Backtest execution failure:", err);
      setErrorStr(err.message || "Something went wrong during strategy backtesting");
    } finally {
      setLoading(false);
    }
  };

  // Merge all 3 equity curves into one dataset for the overlay chart
  const mergedChartData = useMemo(() => {
    const dualMomData = resultsMap["Dual Momentum"]?.equity_curve || [];
    const smaCrossData = resultsMap["SMA Crossover"]?.equity_curve || [];
    const volTargetData = resultsMap["Volatility Target"]?.equity_curve || [];
    
    if (dualMomData.length === 0) return [];
    
    return dualMomData.map((d, i) => ({
      date: d.date,
      benchmark: d.benchmark,
      dualMomentum: d.strategy,
      smaCrossover: smaCrossData[i]?.strategy ?? d.benchmark,
      volTarget: volTargetData[i]?.strategy ?? d.benchmark,
    }));
  }, [resultsMap]);

  // Find the best strategy by Calmar
  const bestStrategy = useMemo(() => {
    let best = { name: "", calmar: -Infinity };
    for (const [name, res] of Object.entries(resultsMap) as [string, BacktestResponse][]) {
      if (res.metrics.calmar_ratio > best.calmar) {
        best = { name, calmar: res.metrics.calmar_ratio };
      }
    }
    return best.name;
  }, [resultsMap]);

  // Active result (selected strategy)
  const activeResult = resultsMap[strategy];

  const CustomEquityTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-[#171f33] border border-[#334155] rounded-lg p-3 shadow-xl text-xs font-mono">
          <p className="text-[#94A3B8] mb-1">{payload[0]?.payload?.date}</p>
          <div className="space-y-1">
            {[
              { key: "dualMomentum", label: "Dual Momentum", color: "#6366F1" },
              { key: "smaCrossover", label: "SMA Crossover", color: "#22D3EE" },
              { key: "volTarget", label: "Vol Target", color: "#F59E0B" },
              { key: "benchmark", label: "Benchmark", color: "#94A3B8" },
            ].map(({ key, label, color }) => {
              const entry = payload.find((p: any) => p.dataKey === key);
              return entry ? (
                <div key={key} className="flex justify-between gap-4">
                  <span style={{ color }}>{label}:</span>
                  <span style={{ color }} className="font-bold">
                    ${entry.value?.toLocaleString(undefined, { minimumFractionDigits: 2 }) || "0.00"}
                  </span>
                </div>
              ) : null;
            })}
          </div>
        </div>
      );
    }
    return null;
  };

  const CustomDrawdownTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-[#171f33] border border-[#334155] rounded-lg p-3 shadow-xl text-xs font-mono text-center">
          <p className="text-[#94A3B8] mb-1">{payload[0].payload.date}</p>
          <p className="text-[#F87171] font-bold">Drawdown: {payload[0].value.toFixed(2)}%</p>
        </div>
      );
    }
    return null;
  };

  // Helper: Calmar badge color
  const calmarBadge = (val: number) => {
    if (val >= 3.0) return { text: "Elite", cls: "text-[#10B981] bg-[#10B981]/15 border-[#10B981]/30" };
    if (val >= 2.0) return { text: "Strong", cls: "text-[#22D3EE] bg-[#22D3EE]/15 border-[#22D3EE]/30" };
    if (val >= 1.0) return { text: "Good", cls: "text-[#F59E0B] bg-[#F59E0B]/15 border-[#F59E0B]/30" };
    return { text: "Weak", cls: "text-[#F87171] bg-[#F87171]/15 border-[#F87171]/30" };
  };

  return (
    <div className="space-y-6">
      
      {/* Simulation Configuration Controller */}
      <div className="bg-[#1e293b]/85 border border-[#334155] rounded-xl p-5 shadow-lg grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-12 gap-4 items-end backdrop-blur-md relative overflow-hidden">
        <div className="col-span-1 sm:col-span-2 xl:col-span-4 w-full">
          <label className="block text-[10px] font-mono uppercase tracking-wide text-[#94A3B8] mb-1.5 select-none">
            Algorithmic Strategy
          </label>
          <select 
            value={strategy}
            onChange={(e) => setStrategy(e.target.value as StrategyType)}
            className="w-full bg-[#0b1326] border border-[#334155] rounded-lg text-sm text-[#e2e8f0] focus:ring-1 focus:ring-[#22D3EE] h-10 px-3 outline-none"
          >
            <option value="Dual Momentum">Dual Momentum (Rank returns &amp; Filter SPY SMA-200)</option>
            <option value="SMA Crossover">SMA Crossover (Golden Cross / Death Cross)</option>
            <option value="Volatility Target">Volatility Target (Inverse-volatility leverage 1.5x)</option>
          </select>
        </div>

        <div className="col-span-1 sm:col-span-1 xl:col-span-2 w-full">
          <label className="block text-[10px] font-mono uppercase tracking-wide text-[#94A3B8] mb-1.5 select-none font-sans">
            Start Date
          </label>
          <div className="relative w-full">
            <Calendar className="w-4 h-4 text-[#94A3B8] absolute left-3 top-3 pointer-events-none" />
            <input 
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-full bg-[#0b1326] border border-[#334155] rounded-lg text-sm text-[#e2e8f0] focus:ring-1 focus:ring-[#22D3EE] h-10 pl-9 pr-3 outline-none font-mono"
            />
          </div>
        </div>

        <div className="col-span-1 sm:col-span-1 xl:col-span-2 w-full">
          <label className="block text-[10px] font-mono uppercase tracking-wide text-[#94A3B8] mb-1.5 select-none font-sans">
            End Date
          </label>
          <div className="relative w-full">
            <Calendar className="w-4 h-4 text-[#94A3B8] absolute left-3 top-3 pointer-events-none" />
            <input 
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="w-full bg-[#0b1326] border border-[#334155] rounded-lg text-sm text-[#e2e8f0] focus:ring-1 focus:ring-[#22D3EE] h-10 pl-9 pr-3 outline-none font-mono"
            />
          </div>
        </div>

        <div className="col-span-1 sm:col-span-1 xl:col-span-2 w-full">
          <label className="block text-[10px] font-mono uppercase tracking-wide text-[#94A3B8] mb-1.5 select-none font-sans">
            Initial Capital
          </label>
          <div className="relative w-full">
            <DollarSign className="w-4 h-4 text-[#94A3B8] absolute left-3 top-3 pointer-events-none" />
            <input 
              type="text"
              value={initialCash}
              onChange={(e) => setInitialCash(e.target.value)}
              className="w-full bg-[#0b1326] border border-[#334155] rounded-lg text-sm text-[#e2e8f0] focus:ring-1 focus:ring-[#22D3EE] h-10 pl-8 pr-3 outline-none font-mono text-right"
              placeholder="$100,000"
            />
          </div>
        </div>

        <div className="col-span-1 sm:col-span-1 xl:col-span-2 w-full">
          <button 
            onClick={executeBacktest}
            disabled={loading}
            className="w-full bg-gradient-to-r from-[#6366F1] to-[#22D3EE] text-white h-10 rounded-lg text-xs font-bold font-mono uppercase tracking-wider hover:opacity-95 active:scale-95 transition-all shadow-[0_0_15px_rgba(99,102,241,0.25)] flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Simulating...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-white" />
                <span>RUN BACKTEST</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Error state diagnostics */}
      {errorStr && (
        <div className="bg-[#93000a]/10 border border-[#93000a]/30 rounded-xl p-4 flex items-center gap-3 text-sm text-[#ffbad3]">
          <ShieldAlert className="w-5 h-5 text-[#ffbad3]" />
          <span>Error processing backtest: {errorStr}</span>
        </div>
      )}

      {/* Shimmer loading loader */}
      {loading ? (
        <div className="space-y-6">
          <div className="grid grid-cols-2 lg:grid-cols-6 gap-3">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="bg-[#1e293b]/50 border border-[#334155] h-[90px] rounded-xl animate-pulse"></div>
            ))}
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
            <div className="lg:col-span-8 bg-[#1e293b]/50 border border-[#334155] h-64 rounded-xl animate-pulse"></div>
            <div className="lg:col-span-4 bg-[#1e293b]/50 border border-[#334155] h-64 rounded-xl animate-pulse"></div>
          </div>
        </div>
      ) : activeResult ? (
        <>
          {/* Key Metrics Grid (2x3 or 1x6) */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            
            <div className="bg-[#1e293b]/85 border border-[#334155] rounded-xl p-4 flex flex-col justify-between shadow-md">
              <span className="text-[#94A3B8] text-[9px] font-mono uppercase tracking-wider">Total Return</span>
              <span className={`text-xl font-bold font-mono mt-2 tracking-tight ${activeResult.metrics.total_return_pct >= 0 ? "text-[#10B981]" : "text-[#F87171]"}`}>
                {activeResult.metrics.total_return_pct >= 0 ? "+" : ""}{activeResult.metrics.total_return_pct}%
              </span>
            </div>

            <div className="bg-[#1e293b]/85 border border-[#334155] rounded-xl p-4 flex flex-col justify-between shadow-md">
              <span className="text-[#94A3B8] text-[9px] font-mono uppercase tracking-wider">Ann. Return</span>
              <span className={`text-xl font-bold font-mono mt-2 tracking-tight ${activeResult.metrics.ann_return_pct >= 0 ? "text-[#10B981]" : "text-[#F87171]"}`}>
                {activeResult.metrics.ann_return_pct >= 0 ? "+" : ""}{activeResult.metrics.ann_return_pct}%
              </span>
            </div>

            <div className="bg-[#1e293b]/85 border border-[#334155] rounded-xl p-4 flex flex-col justify-between shadow-md">
              <span className="text-[#94A3B8] text-[9px] font-mono uppercase tracking-wider">Max Drawdown</span>
              <span className="text-xl font-bold font-mono mt-2 tracking-tight text-[#F87171]">
                -{Math.abs(activeResult.metrics.max_drawdown_pct)}%
              </span>
            </div>

            <div className="bg-[#1e293b]/85 border border-[#334155] rounded-xl p-4 flex flex-col justify-between shadow-md">
              <span className="text-[#94A3B8] text-[9px] font-mono uppercase tracking-wider">Calmar Ratio</span>
              <div className="flex items-baseline gap-2 mt-2">
                <span className="text-xl font-bold font-mono tracking-tight text-white">
                  {activeResult.metrics.calmar_ratio}
                </span>
                <span className={`text-[9px] font-mono font-bold px-1.5 py-0.5 rounded border ${calmarBadge(activeResult.metrics.calmar_ratio).cls}`}>
                  {calmarBadge(activeResult.metrics.calmar_ratio).text}
                </span>
              </div>
            </div>

            <div className="bg-[#1e293b]/85 border border-[#334155] rounded-xl p-4 flex flex-col justify-between shadow-md">
              <span className="text-[#94A3B8] text-[9px] font-mono uppercase tracking-wider">Sharpe / Sortino</span>
              <div className="flex items-baseline gap-1.5 mt-2">
                <span className="text-xl font-bold font-mono tracking-tight text-white">
                  {activeResult.metrics.sharpe_ratio}
                </span>
                <span className="text-[10px] font-mono text-[#94A3B8]">/</span>
                <span className="text-sm font-bold font-mono tracking-tight text-[#A78BFA]">
                  {activeResult.metrics.sortino_ratio}
                </span>
              </div>
            </div>

            <div className="bg-[#1e293b]/85 border border-[#334155] rounded-xl p-4 flex flex-col justify-between shadow-md">
              <span className="text-[#94A3B8] text-[9px] font-mono uppercase tracking-wider">Win Rate</span>
              <div className="flex items-baseline gap-2 mt-2">
                <span className="text-xl font-bold font-mono tracking-tight text-[#22D3EE]">
                  {activeResult.metrics.win_rate_pct}%
                </span>
                <span className="text-[10px] font-mono text-[#94A3B8]">
                  {activeResult.trades.length} trades
                </span>
              </div>
            </div>

          </div>

          {/* ═══ NEW: Strategy Comparison Scoreboard ═══ */}
          {Object.keys(resultsMap).length === 3 && (
            <div className="bg-[#1e293b]/80 border border-[#334155] rounded-xl overflow-hidden shadow-lg">
              <div className="p-4 border-b border-[#334155] flex items-center gap-2">
                <Trophy className="w-4 h-4 text-[#F59E0B]" />
                <span className="text-xs font-bold text-white uppercase tracking-wider font-mono">Strategy Comparison Scoreboard</span>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse min-w-[600px]">
                  <thead>
                    <tr className="bg-[#0b1326] border-b border-[#334155] text-[9px] font-mono uppercase text-[#94A3B8]">
                      <th className="p-3">Strategy</th>
                      <th className="p-3 text-right">Return</th>
                      <th className="p-3 text-right">Max DD</th>
                      <th className="p-3 text-right">Calmar</th>
                      <th className="p-3 text-right">Sharpe</th>
                      <th className="p-3 text-right">Sortino</th>
                      <th className="p-3 text-right">Win Rate</th>
                      <th className="p-3 text-right">Trades</th>
                    </tr>
                  </thead>
                  <tbody className="font-mono text-xs">
                    {(["Dual Momentum", "SMA Crossover", "Volatility Target"] as StrategyType[]).map((name) => {
                      const r = resultsMap[name];
                      if (!r) return null;
                      const isBest = name === bestStrategy;
                      const isActive = name === strategy;
                      return (
                        <tr 
                          key={name}
                          onClick={() => setStrategy(name)}
                          className={`border-b border-[#334155]/30 cursor-pointer transition-colors ${
                            isActive ? "bg-[#6366F1]/10" : "hover:bg-[#6366F1]/5"
                          }`}
                        >
                          <td className="p-3 flex items-center gap-2">
                            <span className="w-2 h-2 rounded-full" style={{ backgroundColor: STRATEGY_COLORS[name] }}></span>
                            <span className={`font-bold ${isActive ? "text-white" : "text-[#94A3B8]"}`}>{name}</span>
                            {isBest && <span className="text-[8px] bg-[#F59E0B]/20 text-[#F59E0B] px-1.5 py-0.5 rounded font-bold border border-[#F59E0B]/30">BEST</span>}
                          </td>
                          <td className={`p-3 text-right font-bold ${r.metrics.total_return_pct >= 0 ? "text-[#10B981]" : "text-[#F87171]"}`}>
                            {r.metrics.total_return_pct >= 0 ? "+" : ""}{r.metrics.total_return_pct}%
                          </td>
                          <td className="p-3 text-right text-[#F87171]">-{Math.abs(r.metrics.max_drawdown_pct)}%</td>
                          <td className="p-3 text-right">
                            <span className={`font-bold px-1.5 py-0.5 rounded text-[10px] ${calmarBadge(r.metrics.calmar_ratio).cls}`}>
                              {r.metrics.calmar_ratio}
                            </span>
                          </td>
                          <td className="p-3 text-right text-white">{r.metrics.sharpe_ratio}</td>
                          <td className="p-3 text-right text-[#A78BFA]">{r.metrics.sortino_ratio}</td>
                          <td className="p-3 text-right text-[#22D3EE]">{r.metrics.win_rate_pct}%</td>
                          <td className="p-3 text-right text-[#94A3B8]">{r.trades.length}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
            
            {/* Equity Curve line chart — overlay of all 3 strategies */}
            <div className="bg-[#1e293b]/80 border border-[#334155] rounded-xl p-5 lg:col-span-8 flex flex-col h-[320px] shadow-lg">
              <div className="pb-3 mb-4 border-b border-[#334155] flex justify-between items-center">
                <span className="text-xs font-bold text-white uppercase tracking-wider font-mono">Performance Equity Curve Comparison</span>
                <div className="flex gap-3 text-[9px] font-mono text-[#94A3B8] flex-wrap justify-end">
                  {[
                    { name: "Dual Momentum", color: "#6366F1" },
                    { name: "SMA Cross", color: "#22D3EE" },
                    { name: "Vol Target", color: "#F59E0B" },
                    { name: "Benchmark", color: "#94A3B8", dashed: true },
                  ].map(({ name, color, dashed }) => (
                    <div key={name} className="flex items-center gap-1.5">
                      <span 
                        className={`w-2.5 h-0.5 ${dashed ? "border-t border-dashed" : ""}`} 
                        style={dashed ? { borderColor: color } : { backgroundColor: color }}
                      ></span>
                      <span className={strategy.startsWith(name.split(" ")[0]) ? "text-white font-bold" : ""}>{name}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex-1 w-full h-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={mergedChartData} margin={{ top: 5, right: 5, left: -25, bottom: 0 }}>
                    <defs>
                      <linearGradient id="eqFill1" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#6366F1" stopOpacity={0.2} />
                        <stop offset="95%" stopColor="#6366F1" stopOpacity={0.0} />
                      </linearGradient>
                      <linearGradient id="eqFill2" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#22D3EE" stopOpacity={0.15} />
                        <stop offset="95%" stopColor="#22D3EE" stopOpacity={0.0} />
                      </linearGradient>
                      <linearGradient id="eqFill3" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#F59E0B" stopOpacity={0.15} />
                        <stop offset="95%" stopColor="#F59E0B" stopOpacity={0.0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#2d3449" vertical={false} />
                    <XAxis 
                      dataKey="date" 
                      stroke="#464554" 
                      tickLine={false} 
                      axisLine={false}
                      tick={{ fill: "#94A3B8", fontSize: 9, fontFamily: "monospace" }} 
                    />
                    <YAxis 
                      stroke="#464554" 
                      tickLine={false} 
                      axisLine={false}
                      domain={['dataMin - 5000', 'dataMax + 5000']}
                      tickFormatter={(v) => `$${Math.round(v / 1000)}k`}
                      tick={{ fill: "#94A3B8", fontSize: 9, fontFamily: "monospace" }}
                    />
                    <Tooltip content={<CustomEquityTooltip />} />
                    <Area type="monotone" dataKey="dualMomentum" stroke="#6366F1" strokeWidth={strategy === "Dual Momentum" ? 3 : 1.5} fillOpacity={1} fill="url(#eqFill1)" dot={false} activeDot={{ r: 4 }} />
                    <Area type="monotone" dataKey="smaCrossover" stroke="#22D3EE" strokeWidth={strategy === "SMA Crossover" ? 3 : 1.5} fillOpacity={1} fill="url(#eqFill2)" dot={false} activeDot={false} />
                    <Area type="monotone" dataKey="volTarget" stroke="#F59E0B" strokeWidth={strategy === "Volatility Target" ? 3 : 1.5} fillOpacity={1} fill="url(#eqFill3)" dot={false} activeDot={false} />
                    <Area type="monotone" dataKey="benchmark" stroke="#464554" strokeWidth={1.5} strokeDasharray="4 4" fill="none" dot={false} activeDot={false} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Drawdown chart */}
            <div className="bg-[#1e293b]/80 border border-[#334155] rounded-xl p-5 lg:col-span-4 flex flex-col h-[320px] shadow-lg text-xs leading-none">
              <div className="pb-3 mb-4 border-b border-[#334155]">
                <span className="text-xs font-bold text-white uppercase tracking-wider font-mono">Simulated Drawdown %</span>
              </div>
              <div className="flex-1 w-full h-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={activeResult.drawdown_series} margin={{ top: 5, right: 5, left: -25, bottom: 0 }}>
                    <defs>
                      <linearGradient id="ddFill" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#F87171" stopOpacity={0.2} />
                        <stop offset="95%" stopColor="#F87171" stopOpacity={0.0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#2d3449" vertical={false} />
                    <XAxis 
                      dataKey="date" 
                      stroke="#464554" 
                      tickLine={false} 
                      axisLine={false}
                      tick={{ fill: "#94A3B8", fontSize: 9, fontFamily: "monospace" }} 
                    />
                    <YAxis 
                      stroke="#464554" 
                      tickLine={false} 
                      axisLine={false}
                      tickFormatter={(v) => `${v}%`}
                      tick={{ fill: "#94A3B8", fontSize: 9, fontFamily: "monospace" }}
                    />
                    <Tooltip content={<CustomDrawdownTooltip />} />
                    <Area type="monotone" dataKey="drawdown" stroke="#F87171" strokeWidth={1.5} fillOpacity={1} fill="url(#ddFill)" dot={false} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

          </div>

          {/* Trade History logs table */}
          <div className="bg-[#1e293b]/80 border border-[#334155] rounded-xl p-0 overflow-hidden shadow-lg">
            <div className="p-4 border-b border-[#334155] flex justify-between items-center">
              <h3 className="text-xs font-bold text-white uppercase tracking-wider font-mono">Execution Transaction History</h3>
              <span className="bg-[#0b1326] border border-[#334155] text-[#94A3B8] px-2.5 py-1 rounded text-[10px] font-mono">
                {activeResult.trades.length} Simulated trades
              </span>
            </div>
            
            {activeResult.trades.length === 0 ? (
              <div className="p-8 text-center text-[#94A3B8] font-mono text-xs">
                No trades were triggered during this backtest run. Lookback filters were not met.
              </div>
            ) : (
              <div className="w-full overflow-x-auto max-h-72 overflow-y-auto">
                <table className="w-full text-left border-collapse min-w-[700px]">
                  <thead>
                    <tr className="bg-[#0b1326] border-b border-[#334155] text-[10px] font-mono uppercase text-[#94A3B8]">
                      <th className="p-3 select-none">Execution Date</th>
                      <th className="p-3 select-none">Asset</th>
                      <th className="p-3 select-none">Action</th>
                      <th className="p-3 select-none text-right">Qty</th>
                      <th className="p-3 select-none text-right">Execution Price</th>
                      <th className="p-3 select-none text-right">Value</th>
                      <th className="p-3 select-none text-right">P&amp;L</th>
                    </tr>
                  </thead>
                  <tbody className="font-mono text-xs text-white">
                    {activeResult.trades.map((t, idx) => (
                      <tr 
                        key={idx} 
                        className="border-b border-[#334155]/30 hover:bg-[#6366F1]/5 transition-colors"
                      >
                        <td className="p-3 text-[#94A3B8]">{t.date}</td>
                        <td className="p-3 font-bold">{t.ticker}</td>
                        <td className="p-3">
                          <span className={`inline-block text-[9px] font-bold px-2 py-0.5 rounded border border-opacity-30 ${
                            t.side === "buy" 
                              ? "bg-[#10B981]/15 text-[#10B981] border-[#10B981]" 
                              : "bg-[#F87171]/15 text-[#F87171] border-[#F87171]"
                          }`}>
                            {t.side.toUpperCase()}
                          </span>
                        </td>
                        <td className="p-3 text-right">{t.qty.toLocaleString()}</td>
                        <td className="p-3 text-right">${t.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                        <td className="p-3 text-right">${t.value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                        <td className={`p-3 text-right font-medium ${t.pnl > 0 ? "text-[#10B981]" : t.pnl < 0 ? "text-[#F87171]" : "text-[#94A3B8]"}`}>
                          {t.pnl > 0 ? `+$${t.pnl.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : t.pnl < 0 ? `-$${Math.abs(t.pnl).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : "-"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      ) : (
        <div className="bg-[#1e293b]/60 border border-[#334155] rounded-xl p-12 text-center text-[#94A3B8] font-mono text-sm max-w-md mx-auto">
          No simulation calculations are currently loaded. Use the configuration panel above to run a backtest.
        </div>
      )}

    </div>
  );
}
