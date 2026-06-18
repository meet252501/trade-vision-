import React, { useEffect, useState } from "react";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from "recharts";
import { TrendingUp, AlertTriangle, ArrowUpRight, ArrowDownRight, RefreshCw, Layers } from "lucide-react";

interface DashboardScreenProps {
  setTab: (tab: string) => void;
  onRunBacktest: () => void;
}

export default function DashboardScreen({ setTab, onRunBacktest }: DashboardScreenProps) {
  const [liveData, setLiveData] = useState<any>(null);
  const [backtestData, setBacktestData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [selectedRange, setSelectedRange] = useState("1M");

  useEffect(() => {
    fetchAllData();
  }, []);

  const fetchAllData = async () => {
    try {
      setLoading(true);
      // Fetch live signal + run a real backtest in parallel
      const [liveRes, btRes] = await Promise.all([
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
        }).then(r => r.ok ? r.json() : null).catch(() => null)
      ]);
      setLiveData(liveRes);
      setBacktestData(btRes);
    } catch (err) {
      console.error("Failed to load data:", err);
    } finally {
      setLoading(false);
    }
  };

  // Use real backtest equity curve if available, fallback to mock
  const chartData = backtestData?.equity_curve?.length > 0
    ? backtestData.equity_curve.map((p: any) => ({
        date: p.date?.slice(5) || p.date, // Show "MM-DD" format
        strategy: Math.round(p.strategy),
        benchmark: Math.round(p.benchmark),
      }))
    : [
        { date: "Oct 01", strategy: 97800, benchmark: 98100 },
        { date: "Oct 04", strategy: 98400, benchmark: 98300 },
        { date: "Oct 08", strategy: 96900, benchmark: 97400 },
        { date: "Oct 12", strategy: 99100, benchmark: 98000 },
        { date: "Oct 16", strategy: 98900, benchmark: 98600 },
        { date: "Oct 20", strategy: 101200, benchmark: 99400 },
        { date: "Oct 24", strategy: 100800, benchmark: 99100 },
        { date: "Oct 28", strategy: 102400, benchmark: 99900 },
        { date: "Nov 01", strategy: 103400, benchmark: 100400 },
      ];

  // Extract real metrics or use demo values
  const m = backtestData?.metrics || {};
  const finalEquity = chartData.length > 0 ? chartData[chartData.length - 1].strategy : 103400;
  const totalReturnPct = m.total_return_pct ?? 3.4;
  const calmar = m.calmar_ratio ?? 2.65;
  const maxDD = m.max_drawdown_pct ?? 7.2;
  const winRate = m.win_rate_pct ?? 56.3;
  const nTrades = backtestData?.trades?.length ?? 47;

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
            <span>Allocated cash: $11,340.00 (11%)</span>
            <span className="text-[#334155]">|</span>
            <span>Invested equity: $92,060.00 (89%)</span>
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
                  BUY <span className="font-mono text-[#6366F1]">{liveData?.ticker || "QQQ"}</span>
                </span>
                <span className="bg-[#10B981]/15 border border-[#10B981]/30 text-[#10B981] text-[10px] font-mono px-2 py-0.5 rounded-full font-bold">
                  BULLISH
                </span>
              </div>
              <p className="text-xs text-[#94A3B8] leading-relaxed line-clamp-3">
                {liveData?.reason || "High momentum divergence. Multi-factor quant rankings show strong asset compliance. Maintain allocated long weights."}
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
              <span>Institutional Portfolio Valuation Curve</span>
            </h3>
            <p className="text-[10px] text-[#94A3B8] font-mono mt-0.5">Dual Momentum vs. SPY Absolute Benchmark</p>
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

        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
              <defs>
                <linearGradient id="colorStrategy" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366F1" stopOpacity={0.25} />
                  <stop offset="95%" stopColor="#6366F1" stopOpacity={0.0} />
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
                domain={['dataMin - 1000', 'dataMax + 1000']}
                tickFormatter={(v) => `$${Math.round(v / 1000)}k`}
                tick={{ fill: "#94A3B8", fontSize: 9, fontFamily: "monospace" }}
              />
              <Tooltip content={<CustomTooltip />} />
              <ReferenceLine y={100000} stroke="#464554" strokeDasharray="5 5" label={{ value: 'INITIAL AT $100K', fill: '#94A3B8', fontSize: 8, fontFamily: "monospace", position: "bottom" }} />
              <Area 
                type="monotone" 
                dataKey="strategy" 
                stroke="#6366F1" 
                strokeWidth={3} 
                fillOpacity={1} 
                fill="url(#colorStrategy)" 
                activeDot={{ r: 5, strokeWidth: 0, fill: "#22D3EE" }}
              />
              <Area 
                type="monotone" 
                dataKey="benchmark" 
                stroke="#464554" 
                strokeWidth={1.5} 
                strokeDasharray="4 4"
                fill="none" 
                dot={false}
              />
            </AreaChart>
          </ResponsiveContainer>
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

      {/* Active Portfolio Positions section */}
      <div className="bg-[#1e293b]/80 border border-[#334155] rounded-xl p-0 overflow-hidden backdrop-blur-md shadow-lg">
        <div className="p-4 border-b border-[#334155] flex justify-between items-center">
          <h3 className="text-xs font-bold text-white tracking-tight uppercase font-mono">Current Live Allocated Positions</h3>
          <span className="bg-[#0b1326] border border-[#334155] text-[#94A3B8] px-2.5 py-1 rounded text-[10px] font-mono">
            Last rebalanced: Oct 28
          </span>
        </div>
        <div className="w-full overflow-x-auto">
          <table className="w-full text-left border-collapse min-w-[500px]">
            <thead>
              <tr className="bg-[#0b1326] border-b border-[#334155]">
                <th className="p-4 text-[10px] font-mono uppercase text-[#94A3B8] tracking-wider select-none">Asset ETF</th>
                <th className="p-4 text-[10px] font-mono uppercase text-[#94A3B8] tracking-wider text-right select-none">Shares</th>
                <th className="p-4 text-[10px] font-mono uppercase text-[#94A3B8] tracking-wider text-right select-none">Current Price</th>
                <th className="p-4 text-[10px] font-mono uppercase text-[#94A3B8] tracking-wider text-right select-none">Calculated P&amp;L</th>
                <th className="p-4 text-[10px] font-mono uppercase text-[#94A3B8] tracking-wider text-right select-none">Tactical Trigger</th>
              </tr>
            </thead>
            <tbody className="font-mono text-xs text-white">
              <tr className="border-b border-[#334155]/50 hover:bg-[#6366F1]/5 transition-colors group">
                <td className="p-4 flex items-center gap-3">
                  <div className="w-7 h-7 rounded-full bg-[#6366F1]/10 text-[#6366F1] flex items-center justify-center font-bold text-[11px] border border-[#6366F1]/20">
                    S
                  </div>
                  <span className="font-bold text-white">SPY</span>
                </td>
                <td className="p-4 text-all text-right text-[#94A3B8]">50</td>
                <td className="p-4 text-right font-medium text-white">$547.80</td>
                <td className="p-4 text-right">
                  <span className="inline-block bg-[#10B981]/15 text-[#10B981] px-2.5 py-1 rounded-md border border-[#10B981]/30 text-[10px] font-bold">
                    +4.9% (+$1,342.50)
                  </span>
                </td>
                <td className="p-4 text-right text-xs">
                  <button onClick={onRunBacktest} className="text-[#94A3B8] group-hover:text-[#6366F1] transition-colors text-[10px] font-bold tracking-wider hover:underline">
                    Re-Backtest SPY
                  </button>
                </td>
              </tr>
              <tr className="border-b border-[#334155]/50 hover:bg-[#6366F1]/5 transition-colors group">
                <td className="p-4 flex items-center gap-3">
                  <div className="w-7 h-7 rounded-full bg-[#6366F1]/10 text-[#6366F1] flex items-center justify-center font-bold text-[11px] border border-[#6366F1]/20">
                    Q
                  </div>
                  <span className="font-bold text-white">QQQ</span>
                </td>
                <td className="p-4 text-all text-right text-[#94A3B8]">70</td>
                <td className="p-4 text-right font-medium text-white">$445.22</td>
                <td className="p-4 text-right">
                  <span className="inline-block bg-[#10B981]/15 text-[#10B981] px-2.5 py-1 rounded-md border border-[#10B981]/30 text-[10px] font-bold">
                    +6.2% (+$1,925.32)
                  </span>
                </td>
                <td className="p-4 text-right text-xs">
                  <button onClick={onRunBacktest} className="text-[#94A3B8] group-hover:text-[#6366F1] transition-colors text-[10px] font-bold tracking-wider hover:underline">
                    Re-Backtest QQQ
                  </button>
                </td>
              </tr>
              <tr className="hover:bg-[#6366F1]/5 transition-colors group">
                <td className="p-4 flex items-center gap-3">
                  <div className="w-7 h-7 rounded-full bg-[#6366F1]/10 text-[#6366F1] flex items-center justify-center font-bold text-[11px] border border-[#6366F1]/20">
                    G
                  </div>
                  <span className="font-bold text-white">GLD</span>
                </td>
                <td className="p-4 text-all text-right text-[#94A3B8]">180</td>
                <td className="p-4 text-right font-medium text-white">$184.20</td>
                <td className="p-4 text-right">
                  <span className="inline-block bg-[#F87171]/15 text-[#F87171] px-2.5 py-1 rounded-md border border-[#F87171]/30 text-[10px] font-bold">
                    -0.4% (-$132.80)
                  </span>
                </td>
                <td className="p-4 text-right text-xs">
                  <button onClick={onRunBacktest} className="text-[#94A3B8] group-hover:text-[#6366F1] transition-colors text-[10px] font-bold tracking-wider hover:underline">
                    Re-Backtest GLD
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
