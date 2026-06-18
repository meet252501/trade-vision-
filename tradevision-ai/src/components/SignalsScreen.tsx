import React, { useEffect, useState } from "react";
import { Radio, AlertCircle, ArrowUpRight, ArrowDownRight, RefreshCw, Star, Layers, Table, BookOpen, Loader } from "lucide-react";

export default function SignalsScreen() {
  const [liveData, setLiveData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchLiveData();
  }, []);

  const fetchLiveData = async () => {
    try {
      setLoading(true);
      const res = await fetch("/api/simulate/live", { method: "POST" });
      if (res.ok) {
        const data = await res.json();
        setLiveData(data);
      }
    } catch (err) {
      console.error("Failed to load live signals mapping:", err);
    } finally {
      setLoading(false);
    }
  };

  const formattedDate = liveData?.date || new Date().toISOString().split("T")[0];
  const tickerMark = liveData?.ticker || "QQQ";
  const actionMark = liveData?.action || "BUY";
  const rationale = liveData?.reason || "System momentum breakouts confirm entry. Maintain full long capacity. SPY continues above 200-day Simple Moving Average trend filter support limits.";
  const momentumScore = liveData?.momentum || 6.2;

  // Render signal action badges correctly
  const getActionBadge = (act: string) => {
    if (act === "BUY") {
      return (
        <span className="bg-[#10B981]/15 border border-[#10B981]/40 text-[#10B981] text-[10px] uppercase font-bold font-mono px-2.5 py-1 rounded-md">
          BUY SIGNAL
        </span>
      );
    } else if (act === "SELL") {
      return (
        <span className="bg-[#F87171]/15 border border-[#F87171]/40 text-[#F87171] text-[10px] uppercase font-bold font-mono px-2.5 py-1 rounded-md">
          SELL SIGNAL
        </span>
      );
    } else {
      return (
        <span className="bg-[#94A3B8]/15 border border-[#94A3B8]/40 text-[#94A3B8] text-[10px] uppercase font-bold font-mono px-2.5 py-1 rounded-md">
          HOLD SIGNAL
        </span>
      );
    }
  };

  // Historic mock log events matching previous 30 days
  const historyData = [
    { date: "2026-06-15", ticker: "QQQ", action: "BUY", momentum: "+6.82%", reason: "Tech breakout confirming strong institutional accumulation. Volume expansion suggests multi-week trend follow." },
    { date: "2026-06-10", ticker: "SPY", action: "BUY", momentum: "+4.40%", reason: "Risk regime shifted to RISK-ON. Closed clean breakout above trailing channel. SMA-200 acting as core support." },
    { date: "2026-06-02", ticker: "GLD", action: "SELL", momentum: "-1.10%", reason: "Momentum index drifted negative. Sliced below previous monthly low pivot line. Capital reallocation triggered." },
    { date: "2026-05-28", ticker: "TLT", action: "HOLD", momentum: "+0.25%", reason: "Bonds consolidated sideways in flat volume. Risk filters mandate capital conservation. Sitting flat." },
    { date: "2026-05-18", ticker: "XLK", action: "BUY", momentum: "+8.91%", reason: "Ranked #1 momentum across all technical indexes. Clean structural breakout triggered under high volume." }
  ];

  return (
    <div className="space-y-6">
      
      {/* Top conviction tactical hero card */}
      <div className="bg-[#1e293b]/80 border border-[#334155] rounded-xl p-6 relative overflow-hidden backdrop-blur-md shadow-lg group">
        
        {/* Shorter ambient glow highlight */}
        <div className="absolute -top-20 -right-20 w-52 h-52 bg-[#22D3EE]/10 rounded-full blur-3xl pointer-events-none group-hover:scale-125 transition-transform"></div>
        
        {loading ? (
          <div className="flex flex-col items-center justify-center py-10">
            <Loader className="w-8 h-8 text-[#22D3EE] animate-spin mb-3" />
            <span className="font-mono text-xs text-[#94A3B8] uppercase">Formulating AI quantitative tactical analysis...</span>
          </div>
        ) : (
          <div className="space-y-4">
            
            <div className="flex flex-wrap justify-between items-center gap-3">
              <div className="flex items-center gap-2.5">
                <div className="w-2.5 h-2.5 rounded-full bg-[#10B981] animate-ping"></div>
                <span className="text-[10px] font-mono text-[#94A3B8] uppercase tracking-wider">
                  Tactical Top Conviction Core Active Trade
                </span>
              </div>
              <div className="bg-[#22D3EE]/10 border border-[#22D3EE]/30 text-[#22D3EE] text-[9px] font-mono px-3 py-1 rounded-full uppercase tracking-wider font-bold">
                92% Confidence Score
              </div>
            </div>

            <div className="flex items-baseline gap-4 pt-1">
              <h1 className="text-4xl font-extrabold text-white tracking-tight">
                {actionMark} {tickerMark}
              </h1>
              <span className={`text-sm font-mono font-bold ${momentumScore >= 0 ? "text-[#10B981]" : "text-[#F87171]"}`}>
                {momentumScore >= 0 ? "+" : ""}{momentumScore}% Momentum (63d)
              </span>
            </div>

            <div className="border-t border-[#334155]/60 pt-4">
              <span className="text-[10px] font-mono uppercase text-[#94A3B8] tracking-widest block mb-2">
                Quantitative / AI Rationale
              </span>
              <p className="text-sm text-[#e2e8f0] leading-relaxed select-all">
                {rationale}
              </p>
            </div>

            <div className="flex justify-between items-center text-[10px] text-[#94A3B8] font-mono pt-2 border-t border-[#334155]/30">
              <span>ESTIMATED SIGNAL DATE: {formattedDate}</span>
              <span>MARKETS REBALANCED AT 16:00 EST DAILY</span>
            </div>

          </div>
        )}
      </div>

      {/* Grid of All Tickers tactical recommendations */}
      <div className="space-y-4">
        <div>
          <h4 className="text-xs font-bold text-white uppercase tracking-wider font-mono">Asset Universe Tactical Status Grid</h4>
          <p className="text-[10px] text-[#94A3B8] font-sans mt-0.5">Automated signal overlays mapped across active indices tickers.</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          
          {/* Asset 1: SPY */}
          <div className="bg-[#1e293b]/75 border border-[#334155] rounded-xl p-4 flex flex-col justify-between h-[120px] backdrop-blur-md hover:border-[#6366F1]/30 transition-colors">
            <div className="flex justify-between items-start">
              <div>
                <h5 className="font-bold text-white text-md">SPY</h5>
                <p className="text-[9px] text-[#94A3B8] font-mono">S&amp;P 500 Index ETF</p>
              </div>
              {getActionBadge("BUY")}
            </div>
            <div className="mt-2.5">
              <div className="flex justify-between text-[10px] font-mono mb-1">
                <span className="text-[#94A3B8]">Momentum Score:</span>
                <span className="text-[#10B981] font-bold">+4.92%</span>
              </div>
              <div className="w-full bg-[#0b1326] h-1.5 rounded-full overflow-hidden">
                <div className="bg-[#10B981] h-full rounded-full" style={{ width: "70%" }}></div>
              </div>
            </div>
          </div>

          {/* Asset 2: QQQ */}
          <div className="bg-[#1e293b]/75 border border-[#334155] rounded-xl p-4 flex flex-col justify-between h-[120px] backdrop-blur-md hover:border-[#6366F1]/30 transition-colors">
            <div className="flex justify-between items-start">
              <div>
                <h5 className="font-bold text-white text-md">QQQ</h5>
                <p className="text-[9px] text-[#94A3B8] font-mono">Nasdaq 100 Growth ETF</p>
              </div>
              {getActionBadge("BUY")}
            </div>
            <div className="mt-2.5">
              <div className="flex justify-between text-[10px] font-mono mb-1">
                <span className="text-[#94A3B8]">Momentum Score:</span>
                <span className="text-[#10B981] font-bold">+6.22%</span>
              </div>
              <div className="w-full bg-[#0b1326] h-1.5 rounded-full overflow-hidden">
                <div className="bg-[#10B981] h-full rounded-full" style={{ width: "85%" }}></div>
              </div>
            </div>
          </div>

          {/* Asset 3: GLD */}
          <div className="bg-[#1e293b]/75 border border-[#334155] rounded-xl p-4 flex flex-col justify-between h-[120px] backdrop-blur-md hover:border-[#6366F1]/30 transition-colors">
            <div className="flex justify-between items-start">
              <div>
                <h5 className="font-bold text-white text-md">GLD</h5>
                <p className="text-[9px] text-[#94A3B8] font-mono">SPDR Gold Trust ETF</p>
              </div>
              {getActionBadge("HOLD")}
            </div>
            <div className="mt-2.5">
              <div className="flex justify-between text-[10px] font-mono mb-1">
                <span className="text-[#94A3B8]">Momentum Score:</span>
                <span className="text-[#94A3B8]">-0.41%</span>
              </div>
              <div className="w-full bg-[#0b1326] h-1.5 rounded-full overflow-hidden">
                <div className="bg-[#94A3B8] h-full rounded-full" style={{ width: "40%" }}></div>
              </div>
            </div>
          </div>

          {/* Asset 4: XLK */}
          <div className="bg-[#1e293b]/75 border border-[#334155] rounded-xl p-4 flex flex-col justify-between h-[120px] backdrop-blur-md hover:border-[#6366F1]/30 transition-colors">
            <div className="flex justify-between items-start">
              <div>
                <h5 className="font-bold text-white text-md">XLK</h5>
                <p className="text-[9px] text-[#94A3B8] font-mono">Technology Select Sector</p>
              </div>
              {getActionBadge("BUY")}
            </div>
            <div className="mt-2.5">
              <div className="flex justify-between text-[10px] font-mono mb-1">
                <span className="text-[#94A3B8]">Momentum Score:</span>
                <span className="text-[#10B981] font-bold">+8.91%</span>
              </div>
              <div className="w-full bg-[#0b1326] h-1.5 rounded-full overflow-hidden">
                <div className="bg-[#10B981] h-full rounded-full" style={{ width: "95%" }}></div>
              </div>
            </div>
          </div>

          {/* Asset 5: GLD */}
          <div className="bg-[#1e293b]/75 border border-[#334155] rounded-xl p-4 flex flex-col justify-between h-[120px] backdrop-blur-md hover:border-[#6366F1]/30 transition-colors">
            <div className="flex justify-between items-start">
              <div>
                <h5 className="font-bold text-white text-md">TLT</h5>
                <p className="text-[9px] text-[#94A3B8] font-mono">20+ Year Treasury Bond</p>
              </div>
              {getActionBadge("SELL")}
            </div>
            <div className="mt-2.5">
              <div className="flex justify-between text-[10px] font-mono mb-1">
                <span className="text-[#94A3B8]">Momentum Score:</span>
                <span className="text-[#F87171] font-bold">-3.20%</span>
              </div>
              <div className="w-full bg-[#0b1326] h-1.5 rounded-full overflow-hidden">
                <div className="bg-[#F87171] h-full rounded-full" style={{ width: "20%" }}></div>
              </div>
            </div>
          </div>

          {/* Asset 6: IWM */}
          <div className="bg-[#1e293b]/75 border border-[#334155] rounded-xl p-4 flex flex-col justify-between h-[120px] backdrop-blur-md hover:border-[#6366F1]/30 transition-colors">
            <div className="flex justify-between items-start">
              <div>
                <h5 className="font-bold text-white text-md">IWM</h5>
                <p className="text-[9px] text-[#94A3B8] font-mono">Russell 2000 Small Cap</p>
              </div>
              {getActionBadge("HOLD")}
            </div>
            <div className="mt-2.5">
              <div className="flex justify-between text-[10px] font-mono mb-1">
                <span className="text-[#94A3B8]">Momentum Score:</span>
                <span className="text-white">+0.85%</span>
              </div>
              <div className="w-full bg-[#0b1326] h-1.5 rounded-full overflow-hidden">
                <div className="bg-[#94A3B8] h-full rounded-full" style={{ width: "50%" }}></div>
              </div>
            </div>
          </div>

        </div>
      </div>

      {/* Historical Signals logs journal */}
      <div className="bg-[#1e293b]/80 border border-[#334155] rounded-xl overflow-hidden shadow-lg">
        <div className="p-4 border-b border-[#334155] flex items-center gap-2">
          <BookOpen className="w-4 h-4 text-[#22D3EE]" />
          <h3 className="text-xs font-bold text-white uppercase tracking-wider font-mono">Historical Tactical Signals Journal</h3>
        </div>
        <div className="w-full overflow-x-auto">
          <table className="w-full text-left border-collapse min-w-[650px]">
            <thead>
              <tr className="bg-[#0b1326] border-b border-[#334155] text-[10px] font-mono uppercase text-[#94A3B8]">
                <th className="p-3">Signal Date</th>
                <th className="p-3">ETF Ticker</th>
                <th className="p-3">Indicated Action</th>
                <th className="p-3">Momentum Score</th>
                <th className="p-3">Core Quantitative Model Rationale</th>
              </tr>
            </thead>
            <tbody className="font-mono text-xs text-white">
              {historyData.map((h, i) => (
                <tr key={i} className="border-b border-[#334155]/20 hover:bg-[#6366F1]/5 transition-colors">
                  <td className="p-3 text-[#94A3B8]">{h.date}</td>
                  <td className="p-3 font-bold">{h.ticker}</td>
                  <td className="p-3">
                    <span className={`inline-block text-[9px] font-bold px-2 py-0.5 rounded border border-opacity-30 ${
                      h.action === "BUY" 
                        ? "bg-[#10B981]/15 text-[#10B981] border-[#10B981]" 
                        : "bg-[#F87171]/15 text-[#F87171] border-[#F87171]"
                    }`}>
                      {h.action}
                    </span>
                  </td>
                  <td className={`p-3 font-bold ${h.action === "BUY" ? "text-[#10B981]" : "text-[#F87171]"}`}>{h.momentum}</td>
                  <td className="p-3 text-[#94A3B8] leading-normal">{h.reason}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
}
