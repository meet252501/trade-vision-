import React, { useEffect, useState } from 'react';
import { Grid, ShieldAlert, Activity, PieChart as PieChartIcon, Loader2 } from 'lucide-react';

export default function RiskHeatmapScreen() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchRisk = async () => {
      try {
        const res = await fetch('/api/risk/heatmap');
        const json = await res.json();
        if (!json.error) setData(json);
      } catch (err) {
        console.error('Failed to fetch risk heatmap:', err);
      }
      setLoading(false);
    };
    fetchRisk();
  }, []);

  if (loading || !data) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-10 h-10 text-[#F59E0B] animate-spin" />
      </div>
    );
  }

  const { correlation, sectors, volatility, tickers } = data;

  const getHeatmapColor = (val: number) => {
    if (val > 0.8) return 'bg-[#EF4444]/80 text-white'; // High correlation
    if (val > 0.5) return 'bg-[#F59E0B]/80 text-white'; // Moderate
    if (val > 0.2) return 'bg-[#10B981]/80 text-white'; // Low
    if (val > 0) return 'bg-[#22D3EE]/80 text-[#0b1326]'; // Very low
    return 'bg-[#6366F1]/80 text-white'; // Negative
  };

  // Sector breakdown
  const sectorCounts: Record<string, number> = {};
  tickers.forEach((t: string) => {
    const s = sectors[t] || 'Other';
    sectorCounts[s] = (sectorCounts[s] || 0) + 1;
  });

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white tracking-tight flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#EF4444] to-[#F59E0B] flex items-center justify-center shadow-[0_0_20px_rgba(239,68,68,0.3)]">
            <Grid className="w-5 h-5 text-white" />
          </div>
          Risk Heatmap
        </h2>
        <p className="text-[#94A3B8] mt-1 text-sm">Cross-asset correlation matrix and portfolio exposure analysis</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Correlation Matrix */}
        <div className="lg:col-span-2 bg-[#1e293b]/80 border border-[#334155] rounded-xl p-6 backdrop-blur-md overflow-x-auto">
          <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
            <Activity className="w-4 h-4 text-[#F59E0B]" /> 90-Day Correlation Matrix
          </h3>
          <div className="min-w-[600px]">
            <div className="grid" style={{ gridTemplateColumns: `50px repeat(${tickers.length}, minmax(40px, 1fr))` }}>
              <div className="p-2"></div>
              {tickers.map((t: string) => (
                <div key={t} className="p-2 text-center text-[10px] font-mono font-bold text-[#94A3B8]">{t}</div>
              ))}
              
              {tickers.map((t1: string) => (
                <React.Fragment key={t1}>
                  <div className="p-2 flex items-center justify-end text-[10px] font-mono font-bold text-[#94A3B8] pr-4">{t1}</div>
                  {tickers.map((t2: string) => {
                    const val = correlation[t1]?.[t2] || 0;
                    return (
                      <div key={`${t1}-${t2}`} className="p-1">
                        <div className={`w-full h-10 rounded flex items-center justify-center text-[10px] font-mono font-bold transition-all hover:scale-110 cursor-default ${t1 === t2 ? 'bg-[#334155] text-white opacity-50' : getHeatmapColor(val)}`} title={`${t1} vs ${t2}: ${val}`}>
                          {t1 === t2 ? '-' : val.toFixed(2)}
                        </div>
                      </div>
                    );
                  })}
                </React.Fragment>
              ))}
            </div>
          </div>
        </div>

        <div className="space-y-6">
          {/* Sector Exposure */}
          <div className="bg-[#1e293b]/80 border border-[#334155] rounded-xl p-6 backdrop-blur-md">
            <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
              <PieChartIcon className="w-4 h-4 text-[#22D3EE]" /> Sector Exposure
            </h3>
            <div className="space-y-3">
              {Object.entries(sectorCounts).map(([sector, count]) => {
                const pct = (count / tickers.length) * 100;
                return (
                  <div key={sector}>
                    <div className="flex justify-between text-xs font-mono mb-1">
                      <span className="text-[#e2e8f0]">{sector}</span>
                      <span className="text-[#94A3B8]">{count} assets ({pct.toFixed(0)}%)</span>
                    </div>
                    <div className="w-full h-2 bg-[#0b1326] rounded-full overflow-hidden">
                      <div className="h-full bg-gradient-to-r from-[#6366F1] to-[#22D3EE]" style={{ width: `${pct}%` }}></div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Asset Volatility */}
          <div className="bg-[#1e293b]/80 border border-[#334155] rounded-xl p-6 backdrop-blur-md">
            <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-[#EF4444]" /> Annualized Volatility
            </h3>
            <div className="space-y-2 max-h-[300px] overflow-y-auto pr-2 custom-scrollbar">
              {Object.entries(volatility)
                .sort((a: any, b: any) => b[1] - a[1])
                .map(([ticker, vol]: any) => (
                <div key={ticker} className="flex justify-between items-center p-2 rounded bg-[#0b1326]/50 border border-[#334155]/50">
                  <span className="text-xs font-mono font-bold text-white">{ticker}</span>
                  <span className={`text-xs font-mono font-bold px-2 py-0.5 rounded ${
                    vol > 30 ? 'bg-[#EF4444]/20 text-[#EF4444]' :
                    vol > 20 ? 'bg-[#F59E0B]/20 text-[#F59E0B]' :
                    'bg-[#10B981]/20 text-[#10B981]'
                  }`}>
                    {vol.toFixed(1)}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
