import React, { useEffect, useState } from "react";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from "recharts";
import { TrendingUp, AlertTriangle, ArrowUpRight, ArrowDownRight, RefreshCw, Layers, PlayCircle, StopCircle } from "lucide-react";
import LiveCandleChart from "./LiveCandleChart";

interface DashboardScreenProps {
  setTab: (tab: string) => void;
  onRunBacktest: () => void;
}

export default function DashboardScreen({ setTab, onRunBacktest }: DashboardScreenProps) {
  const [liveData, setLiveData] = useState<any>(null);
  const [backtestData, setBacktestData] = useState<any>(null);
  const [alpacaData, setAlpacaData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [selectedRange, setSelectedRange] = useState("1M");
  
  // Agent Control State
  const [agentRunning, setAgentRunning] = useState(false);
  const [agentTarget, setAgentTarget] = useState(500);
  const [agentPid, setAgentPid] = useState<number | null>(null);

  useEffect(() => {
    fetchAllData();
  }, []);

  const fetchAllData = async () => {
    try {
      setLoading(true);
      const [liveRes, btRes, alpacaRes] = await Promise.all([
        fetch("/api/simulate/live", { method: "POST" }).then(r => r.ok ? r.json() : null).catch(() => null),
        fetch("/api/backtest", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            strategy: "Dual Momentum",
            tickers: ["SPY", "QQQ", "IWM", "XLK", "GLD"],
            start_date: "2023-01-01",
            end_date: "2024-06-01",
            initial_cash: 100000
          })
        }).then(r => r.ok ? r.json() : null).catch(() => null),
        fetch("/api/alpaca/portfolio").then(r => r.ok ? r.json() : null).catch(() => null)
      ]);
      setLiveData(liveRes);
      setBacktestData(btRes);
      setAlpacaData(alpacaRes);
      
      const statusRes = await fetch("/api/agent/status").then(r => r.ok ? r.json() : null).catch(() => null);
      if (statusRes) {
        setAgentRunning(statusRes.running);
        if (statusRes.running) {
          setAgentTarget(statusRes.target);
          setAgentPid(statusRes.pid);
        }
      }
    } catch (err) {
      console.error("Failed to load data:", err);
    } finally {
      setLoading(false);
    }
  };

  const toggleAgent = async () => {
    if (agentRunning) {
      // Stop it
      const res = await fetch("/api/agent/stop", { method: "POST" });
      if (res.ok) {
        setAgentRunning(false);
        setAgentPid(null);
      }
    } else {
      // Start it
      const res = await fetch("/api/agent/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target: agentTarget })
      });
      if (res.ok) {
        const data = await res.json();
        setAgentRunning(true);
        setAgentPid(data.pid);
      }
    }
  };

  // Use real live Alpaca equity curve if available, then backtest
  const chartData = alpacaData?.equity_curve?.length > 0
    ? alpacaData.equity_curve.map((p: any) => ({
        date: p.time,
        strategy: Math.round(p.equity),
        benchmark: 100000,
      }))
    : backtestData?.equity_curve?.length > 0
    ? backtestData.equity_curve.map((p: any) => ({
        date: p.date?.slice(5) || p.date,
        strategy: Math.round(p.strategy),
        benchmark: Math.round(p.benchmark),
      }))
    : [];

  const m = backtestData?.metrics || {};
  const finalEquity = alpacaData?.equity ?? (chartData.length > 0 ? chartData[chartData.length - 1].strategy : 0);
  const totalReturnPct = alpacaData ? ((alpacaData.equity - 100000) / 100000 * 100) : (m.total_return_pct ?? 0);
  const calmar = m.calmar_ratio ?? 0;
  const maxDD = m.max_drawdown_pct ?? 0;
  const winRate = m.win_rate_pct ?? 0;
  const nTrades = backtestData?.trades?.length ?? 0;
  const cashValue = alpacaData?.cash ?? 0;
  const investedValue = finalEquity - cashValue;

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-[#171f33] border border-[#334155] rounded-lg p-3 shadow-xl">
          <p className="font-mono text-[10px] text-[#94A3B8] mb-1">{payload[0].payload.date}</p>
          <div className="space-y-1 text-xs">
            <div className="flex justify-between gap-4 font-mono">
              <span className="text-white">Strategy:</span>
              <span className="text-[#6366F1] font-bold">${payload[0].value.toLocaleString()}</span>
            </div>
            <div className="flex justify-between gap-4 font-mono">
              <span className="text-[#94A3B8]">Benchmark:</span>
              <span className="text-[#94A3B8] font-bold">${payload[1].value.toLocaleString()}</span>
            </div>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="space-y-6">

      {/* Agent Control Panel */}
      <div className={`border rounded-xl p-6 relative overflow-hidden backdrop-blur-md shadow-lg transition-all ${agentRunning ? "bg-[#10B981]/10 border-[#10B981]/50" : "bg-[#1e293b]/80 border-[#334155]"}`}>
        {agentRunning && <div className="absolute top-0 left-0 w-full h-1 bg-[#10B981] animate-pulse"></div>}
        <div className="flex flex-col md:flex-row justify-between items-center gap-6">
          
          <div>
            <div className="flex items-center gap-2 mb-1">
              <h2 className="text-xl font-extrabold text-white tracking-tight">Autonomous Agent</h2>
              {agentRunning ? (
                <span className="bg-[#10B981]/20 text-[#10B981] px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase animate-pulse flex items-center gap-1.5">
                  <div className="w-1.5 h-1.5 bg-[#10B981] rounded-full"></div> LIVE (PID: {agentPid})
                </span>
              ) : (
                <span className="bg-[#94A3B8]/20 text-[#94A3B8] px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase">OFFLINE</span>
              )}
            </div>
            <p className="text-xs text-[#94A3B8] font-mono">
              Controls the background Python execution engine.
            </p>
          </div>

          <div className="flex items-center gap-4 w-full md:w-auto">
            <div className="flex flex-col">
              <label className="text-[10px] font-bold font-mono text-[#94A3B8] uppercase mb-1">Target Profit ($)</label>
              <input 
                type="number" 
                value={agentTarget} 
                onChange={(e) => setAgentTarget(Number(e.target.value))}
                disabled={agentRunning}
                className="w-24 bg-[#0b1326] border border-[#334155] rounded px-3 py-2 text-white font-mono text-sm focus:outline-none focus:border-[#6366F1] disabled:opacity-50"
              />
            </div>
            
            <button 
              onClick={toggleAgent}
              className={`flex-1 md:flex-none mt-5 px-6 py-2 rounded-lg font-bold font-mono text-xs uppercase tracking-wider flex items-center justify-center gap-2 transition-transform active:scale-95 ${
                agentRunning 
                  ? "bg-[#EF4444]/20 text-[#EF4444] hover:bg-[#EF4444]/30 border border-[#EF4444]/50" 
                  : "bg-gradient-to-r from-[#6366F1] to-[#22D3EE] text-white shadow-[0_0_15px_rgba(99,102,241,0.3)] hover:opacity-90"
              }`}
            >
              {agentRunning ? (
                <><StopCircle className="w-4 h-4" /> STOP AGENT</>
              ) : (
                <><PlayCircle className="w-4 h-4" /> START AGENT</>
              )}
            </button>
          </div>
          
        </div>
      </div>
      
      {/* Alpaca Live Card */}
      {alpacaData && !alpacaData.error && (
        <div className="bg-[#1e293b]/80 border border-[#22D3EE]/50 rounded-xl p-6 relative overflow-hidden backdrop-blur-md shadow-[0_0_15px_rgba(34,211,238,0.15)] group">
          <div className="absolute top-4 right-4 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-[#10B981] animate-pulse shadow-[0_0_8px_#10B981]"></span>
            <span className="text-[9px] font-mono text-[#10B981] tracking-widest uppercase">ALPACA LIVE PAPER</span>
          </div>
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-4">
            <div>
              <span className="text-[#94A3B8] text-[10px] uppercase font-mono tracking-wider">
                Live Account Value
              </span>
              <h1 className="text-3xl font-extrabold text-white font-mono mt-1 tracking-tight">
                ${alpacaData.equity?.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}
              </h1>
            </div>
            <div className={`flex items-center gap-1.5 ${alpacaData.total_profit_since_inception >= 0 ? 'bg-[#10B981]/15 border-[#10B981]/30 text-[#10B981]' : 'bg-[#EF4444]/15 border-[#EF4444]/30 text-[#EF4444]'} border text-sm font-mono font-bold px-3 py-1.5 rounded-md`}>
              <span>{alpacaData.total_profit_since_inception >= 0 ? '+' : ''}${alpacaData.total_profit_since_inception?.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})} PNL</span>
            </div>
          </div>
          
          {alpacaData.positions && alpacaData.positions.length > 0 && (
            <div>
              <span className="text-[#94A3B8] text-[10px] uppercase font-mono tracking-wider mb-2 block">Live Positions</span>
              <div className="flex gap-3 flex-wrap">
                {alpacaData.positions.map((p: any) => (
                  <div key={p.ticker} className="bg-[#0b1326]/60 border border-[#334155] p-2 px-4 rounded-lg text-center flex items-center gap-3">
                    <div className="text-sm font-bold text-white font-mono">{p.ticker}</div>
                    <div className="text-xs text-[#94A3B8]">{p.qty} sh</div>
                    <div className={`text-xs font-mono ${p.unrealized_pl >= 0 ? 'text-[#10B981]' : 'text-[#EF4444]'}`}>
                      {p.unrealized_pl >= 0 ? '+' : ''}${p.unrealized_pl.toFixed(2)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Top row: Portfolio Summary & Daily Signal */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        
        {/* Total portfolio value bento panel */}
        <div className="lg:col-span-8 bg-[#1e293b]/80 border border-[#334155] rounded-xl p-6 relative overflow-hidden backdrop-blur-md flex flex-col justify-center min-h-[140px] shadow-lg group">
          <div className="absolute -top-10 -right-10 w-40 h-40 bg-[#6366F1]/10 rounded-full blur-3xl pointer-events-none group-hover:scale-110 transition-transform"></div>
          <div className="flex justify-between items-start mb-2">
            <div>
              <span className="text-[#94A3B8] text-[10px] uppercase font-mono tracking-wider">
                Total Portfolio Asset Value
              </span>
              <h1 className="text-3xl font-extrabold text-white font-mono mt-1 tracking-tight select-all">
                ${finalEquity.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}
              </h1>
            </div>
            <div className="flex items-center gap-1.5 bg-[#10B981]/15 border border-[#10B981]/30 text-[#10B981] text-xs font-mono font-bold px-2.5 py-1 rounded-md">
              <TrendingUp className="w-3.5 h-3.5" />
              <span>{totalReturnPct >= 0 ? '+' : ''}{totalReturnPct.toFixed(1)}% DRIFT</span>
            </div>
          </div>
          <div className="text-[11px] font-mono text-[#94A3B8] mt-2 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[#10B981]"></span>
            <span>Cash: ${cashValue > 0 ? cashValue.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2}) : '—'} ({finalEquity > 0 ? ((cashValue / finalEquity) * 100).toFixed(0) : 0}%)</span>
            <span className="text-[#334155]">|</span>
            <span>Invested: ${investedValue > 0 ? investedValue.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2}) : '—'} ({finalEquity > 0 ? ((investedValue / finalEquity) * 100).toFixed(0) : 0}%)</span>
          </div>
        </div>

        {/* Signal card showing today's conviction */}
        <div className="lg:col-span-4 bg-[#1e293b]/85 border border-[#6366F1]/40 rounded-xl p-6 relative overflow-hidden backdrop-blur-md shadow-lg">
          <div className="absolute top-4 right-4 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-[#22D3EE] animate-pulse shadow-[0_0_8px_#22D3EE]"></span>
            <span className="text-[9px] font-mono text-[#22D3EE] tracking-widest uppercase">TACTICAL LIVE</span>
          </div>
          
          <span className="text-[#94A3B8] text-[10px] uppercase font-mono tracking-wider">
            Today's Top Signal
          </span>
          
          {loading ? (
            <div className="space-y-2 mt-4">
              <div className="h-6 w-1/2 bg-[#2d3449] animate-pulse rounded"></div>
              <div className="h-4 w-full bg-[#2d3449] animate-pulse rounded"></div>
              <div className="h-4 w-5/6 bg-[#2d3449] animate-pulse rounded"></div>
            </div>
          ) : (
            <div className="mt-3 space-y-3">
              <div className="flex items-center gap-2">
                <span className="text-xl font-bold text-white tracking-tight">
                  {liveData?.action || "HOLD"} <span className="font-mono text-[#6366F1]">{liveData?.ticker || "—"}</span>
                </span>
                {liveData?.action === "BUY" && (
                  <span className="bg-[#10B981]/15 border border-[#10B981]/30 text-[#10B981] text-[10px] font-mono px-2 py-0.5 rounded-full font-bold">
                    BULLISH
                  </span>
                )}
                {liveData?.action === "SELL" && (
                  <span className="bg-[#EF4444]/15 border border-[#EF4444]/30 text-[#EF4444] text-[10px] font-mono px-2 py-0.5 rounded-full font-bold">
                    BEARISH
                  </span>
                )}
              </div>
              <p className="text-xs text-[#94A3B8] leading-relaxed line-clamp-3">
                {liveData?.reason || "Awaiting signal from AI engine..."}
              </p>
              <div className="flex gap-2 pt-1">
                <button 
                  onClick={() => setTab("signals")}
                  className="flex-1 text-[10px] font-bold py-2 bg-[#6366F1] hover:bg-[#6366F1]/90 text-white rounded-lg transition-colors text-center shadow-[0_0_12px_rgba(99,102,241,0.2)]"
                >
                  Analyze Signalling
                </button>
                <button 
                  onClick={onRunBacktest}
                  className="flex-1 text-[10px] font-bold py-2 border border-[#334155] hover:bg-[#1e293b] text-white rounded-lg transition-colors text-center"
                >
                  Backtest Params
                </button>
              </div>
            </div>
          )}
        </div>

      </div>

      {/* Main Interactive Equity Curve Grid */}
      <div className="bg-[#1e293b]/80 border border-[#334155] rounded-xl p-6 backdrop-blur-md shadow-lg">
        <div className="flex flex-wrap justify-between items-center mb-6 pb-4 border-b border-[#334155]">
          <div>
            <h3 className="text-sm font-bold text-white tracking-tight flex items-center gap-2">
              <Layers className="w-4 h-4 text-[#22D3EE]" />
              <span>Real-Time Market Execution Flow</span>
            </h3>
            <p className="text-[10px] text-[#94A3B8] font-mono mt-0.5">
              Live Interactive Candlestick Stream (Hardware Accelerated)
            </p>
          </div>
          <div className="flex gap-1.5 mt-2 sm:mt-0 bg-[#0b1326]/60 p-1 rounded-lg border border-[#334155]">
            {["1W", "1M", "YTD"].map((r) => (
              <button
                key={r}
                onClick={() => setSelectedRange(r)}
                className={`px-3 py-1 text-[10px] font-mono font-bold rounded-md transition-all ${
                  selectedRange === r
                    ? "bg-[#1e293b] text-white shadow-md border border-[#334155]"
                    : "text-[#94A3B8] hover:text-[#e2e8f0]"
                }`}
              >
                {r}
              </button>
            ))}
          </div>
        </div>

        <div className="h-[320px] w-full">
          <LiveCandleChart ticker={liveData?.ticker || "SPY"} />
        </div>
      </div>

      {/* Grid listing core performance metrics alongside holdings */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        
        {/* Metric 1 */}
        <div className="bg-[#1e293b]/80 border border-[#334155] rounded-xl p-5 flex flex-col justify-between h-[110px] backdrop-blur-md shadow-lg">
          <span className="text-[#94A3B8] text-[10px] font-mono uppercase tracking-wider">Calmar Ratio</span>
          <div className="flex items-baseline justify-between mt-2">
            <span className="text-2xl font-bold font-mono text-[#22D3EE] tracking-tight">{calmar.toFixed(2)}</span>
            <span className={`text-[10px] font-mono font-medium flex items-center px-1.5 py-0.5 rounded ${calmar >= 2.5 ? 'text-[#10B981] bg-[#10B981]/10' : calmar >= 1.5 ? 'text-[#F59E0B] bg-[#F59E0B]/10' : 'text-[#F87171] bg-[#F87171]/10'}`}>{calmar >= 2.5 ? 'Elite' : calmar >= 1.5 ? 'Good' : 'Low'}</span>
          </div>
          <p className="text-[10px] text-[#94A3B8] font-mono leading-relaxed truncate">Annualized Return / Max Drawdown</p>
        </div>

        {/* Metric 2 */}
        <div className="bg-[#1e293b]/80 border border-[#334155] rounded-xl p-5 flex flex-col justify-between h-[110px] backdrop-blur-md shadow-lg">
          <span className="text-[#94A3B8] text-[10px] font-mono uppercase tracking-wider">Portfolio Max Drawdown</span>
          <div className="flex items-baseline justify-between mt-2">
            <span className="text-2xl font-bold font-mono text-[#F87171] tracking-tight">-{maxDD.toFixed(1)}%</span>
            <span className={`text-[10px] font-mono font-medium flex items-center px-1.5 py-0.5 rounded ${maxDD <= 10 ? 'text-[#10B981] bg-[#10B981]/10' : maxDD <= 20 ? 'text-[#F59E0B] bg-[#F59E0B]/10' : 'text-[#F87171] bg-[#F87171]/10'}`}>{maxDD <= 10 ? 'Low Risk' : maxDD <= 20 ? 'Moderate' : 'High'}</span>
          </div>
          <p className="text-[10px] text-[#94A3B8] font-mono leading-relaxed truncate">Protected by SMA protective mandate</p>
        </div>

        {/* Metric 3 */}
        <div className="bg-[#1e293b]/80 border border-[#334155] rounded-xl p-5 flex flex-col justify-between h-[110px] backdrop-blur-md shadow-lg">
          <span className="text-[#94A3B8] text-[10px] font-mono uppercase tracking-wider">Trading Win Rate</span>
          <div className="flex items-baseline justify-between mt-2">
            <span className="text-2xl font-bold font-mono text-white tracking-tight">{winRate.toFixed(1)}%</span>
            <span className="text-[10px] text-[#e2e8f0] font-mono font-bold flex items-center bg-[#334155] px-1.5 py-0.5 rounded">{nTrades} Trades</span>
          </div>
          <p className="text-[10px] text-[#94A3B8] font-mono leading-relaxed truncate">Calculated across trailing closed positions</p>
        </div>

      </div>

      {/* Active Portfolio Positions section — dynamically from Alpaca */}
      <div className="bg-[#1e293b]/80 border border-[#334155] rounded-xl p-0 overflow-hidden backdrop-blur-md shadow-lg">
        <div className="p-4 border-b border-[#334155] flex justify-between items-center">
          <h3 className="text-xs font-bold text-white tracking-tight uppercase font-mono">Live Allocated Positions</h3>
          <span className="bg-[#0b1326] border border-[#334155] text-[#94A3B8] px-2.5 py-1 rounded text-[10px] font-mono">
            {alpacaData?.positions?.length ?? 0} positions
          </span>
        </div>
        <div className="w-full overflow-x-auto">
          <table className="w-full text-left border-collapse min-w-[500px]">
            <thead>
              <tr className="bg-[#0b1326] border-b border-[#334155]">
                <th className="p-4 text-[10px] font-mono uppercase text-[#94A3B8] tracking-wider select-none">Asset</th>
                <th className="p-4 text-[10px] font-mono uppercase text-[#94A3B8] tracking-wider text-right select-none">Shares</th>
                <th className="p-4 text-[10px] font-mono uppercase text-[#94A3B8] tracking-wider text-right select-none">Market Value</th>
                <th className="p-4 text-[10px] font-mono uppercase text-[#94A3B8] tracking-wider text-right select-none">Unrealized P&amp;L</th>
                <th className="p-4 text-[10px] font-mono uppercase text-[#94A3B8] tracking-wider text-right select-none">Action</th>
              </tr>
            </thead>
            <tbody className="font-mono text-xs text-white">
              {alpacaData?.positions && alpacaData.positions.length > 0 ? (
                alpacaData.positions.map((pos: any) => (
                  <tr key={pos.ticker} className="border-b border-[#334155]/50 hover:bg-[#6366F1]/5 transition-colors group">
                    <td className="p-4 flex items-center gap-3">
                      <div className="w-7 h-7 rounded-full bg-[#6366F1]/10 text-[#6366F1] flex items-center justify-center font-bold text-[11px] border border-[#6366F1]/20">
                        {pos.ticker?.charAt(0)}
                      </div>
                      <span className="font-bold text-white">{pos.ticker}</span>
                    </td>
                    <td className="p-4 text-right text-[#94A3B8]">{pos.qty}</td>
                    <td className="p-4 text-right font-medium text-white">
                      ${pos.market_value?.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}
                    </td>
                    <td className="p-4 text-right">
                      <span className={`inline-block px-2.5 py-1 rounded-md border text-[10px] font-bold ${
                        pos.unrealized_pl >= 0 
                          ? 'bg-[#10B981]/15 text-[#10B981] border-[#10B981]/30' 
                          : 'bg-[#F87171]/15 text-[#F87171] border-[#F87171]/30'
                      }`}>
                        {pos.unrealized_pl >= 0 ? '+' : ''}${pos.unrealized_pl?.toFixed(2)} ({pos.unrealized_plpc ? (pos.unrealized_plpc * 100).toFixed(2) : '0.00'}%)
                      </span>
                    </td>
                    <td className="p-4 text-right text-xs">
                      <button onClick={onRunBacktest} className="text-[#94A3B8] group-hover:text-[#6366F1] transition-colors text-[10px] font-bold tracking-wider hover:underline">
                        Backtest {pos.ticker}
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5} className="p-8 text-center text-[#94A3B8]">
                    {loading ? (
                      <div className="flex items-center justify-center gap-2">
                        <RefreshCw className="w-4 h-4 animate-spin" />
                        <span>Loading live positions...</span>
                      </div>
                    ) : (
                      <span>No live positions — connect Alpaca to begin trading</span>
                    )}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
