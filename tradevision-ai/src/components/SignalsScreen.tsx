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
  const tickerMark = liveData?.ticker || "—";
  const actionMark = liveData?.action || "HOLD";
  const rationale = liveData?.reason || "Awaiting real-time signal compilation...";
  const momentumScore = liveData?.momentum || 0;

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

  const universeAssets = liveData?.universe?.latestReturns 
    ? Object.entries(liveData.universe.latestReturns).map(([sym, ret]) => ({
        sym,
        ret: Number(ret),
        action: Number(ret) > 0 ? "BUY" : "SELL"
      }))
    : [];

  return (
    <div className="space-y-6">
      
      {/* Top conviction tactical hero card */}
      <div className="bg-[#1e293b]/80 border border-[#334155] rounded-xl p-6 relative overflow-hidden backdrop-blur-md shadow-lg group">
        <div className="absolute -top-20 -right-20 w-52 h-52 bg-[#22D3EE]/10 rounded-full blur-3xl pointer-events-none group-hover:scale-125 transition-transform"></div>
        
        {loading ? (
          <div className="flex flex-col items-center justify-center py-10">
            <Loader className="w-8 h-8 text-[#22D3EE] animate-spin mb-3" />
            <span className="font-mono text-xs text-[#94A3B8] uppercase">Formulating quantitative tactical analysis...</span>
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
              <button onClick={fetchLiveData} className="hover:bg-[#334155] p-1.5 rounded transition">
                <RefreshCw className="w-4 h-4 text-[#94A3B8]" />
              </button>
            </div>

            <div className="flex items-baseline gap-4 pt-1">
              <h1 className="text-4xl font-extrabold text-white tracking-tight">
                {actionMark} {tickerMark}
              </h1>
              <span className={`text-sm font-mono font-bold ${momentumScore >= 0 ? "text-[#10B981]" : "text-[#F87171]"}`}>
                {momentumScore > 0 ? "+" : ""}{momentumScore}% Momentum (63d)
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
      {!loading && universeAssets.length > 0 && (
        <div className="space-y-4">
          <div>
            <h4 className="text-xs font-bold text-white uppercase tracking-wider font-mono">Real-Time Asset Universe Status</h4>
            <p className="text-[10px] text-[#94A3B8] font-sans mt-0.5">Automated signal overlays mapped across active indices tickers.</p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {universeAssets.map((asset) => {
              const perc = Math.min(Math.max((asset.ret + 10) * 5, 5), 100); // normalized bar width
              return (
                <div key={asset.sym} className="bg-[#1e293b]/75 border border-[#334155] rounded-xl p-4 flex flex-col justify-between h-[120px] backdrop-blur-md hover:border-[#6366F1]/30 transition-colors">
                  <div className="flex justify-between items-start">
                    <div>
                      <h5 className="font-bold text-white text-md">{asset.sym}</h5>
                    </div>
                    {getActionBadge(asset.action)}
                  </div>
                  <div className="mt-2.5">
                    <div className="flex justify-between text-[10px] font-mono mb-1">
                      <span className="text-[#94A3B8]">Momentum Score:</span>
                      <span className={`font-bold ${asset.ret > 0 ? "text-[#10B981]" : "text-[#F87171]"}`}>
                        {asset.ret > 0 ? "+" : ""}{asset.ret}%
                      </span>
                    </div>
                    <div className="w-full bg-[#0b1326] h-1.5 rounded-full overflow-hidden">
                      <div className={`h-full rounded-full ${asset.ret > 0 ? "bg-[#10B981]" : "bg-[#F87171]"}`} style={{ width: `${perc}%` }}></div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
