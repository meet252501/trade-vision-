import React, { useEffect, useRef, useState } from 'react';
import { createChart, ISeriesApi, CandlestickData, CandlestickSeries, createSeriesMarkers } from 'lightweight-charts';
import { Cpu, TrendingUp, Play, Loader2, Zap, BarChart3 } from 'lucide-react';

// Real Alpaca universe — matches agent.py UNIVERSE exactly
const UNIVERSE = ['SPY', 'QQQ', 'IWM', 'XLK', 'XLF', 'XLE', 'XLV', 'GLD', 'TLT', 'SMH'];

export const AITradingLabScreen: React.FC = () => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<any>(null);
  const seriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const markersRef = useRef<any>(null);
  const disposed = useRef(false);
  
  const [ticker, setTicker] = useState("SPY");
  const [loading, setLoading] = useState(false);
  const [mlData, setMlData] = useState<any>(null);
  const [chartReady, setChartReady] = useState(false);
  const [candleCount, setCandleCount] = useState(0);

  // Create chart once on mount, destroy on unmount
  useEffect(() => {
    disposed.current = false;
    if (!chartContainerRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { color: 'transparent' },
        textColor: '#94A3B8',
        fontFamily: "'Inter', sans-serif",
      },
      grid: {
        vertLines: { color: '#1E293B', style: 1 },
        horzLines: { color: '#1E293B', style: 1 },
      },
      crosshair: {
        mode: 1,
        vertLine: { color: '#6366F1', labelBackgroundColor: '#6366F1' },
        horzLine: { color: '#6366F1', labelBackgroundColor: '#6366F1' },
      },
      timeScale: {
        borderColor: '#334155',
        timeVisible: true,
      },
      rightPriceScale: {
        borderColor: '#334155',
      },
      autoSize: true,
    });

    chartRef.current = chart;
    
    const candlestickSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#22c55e',
      downColor: '#ef4444',
      borderVisible: false,
      wickUpColor: '#22c55e',
      wickDownColor: '#ef4444',
    });
    seriesRef.current = candlestickSeries;

    return () => {
      disposed.current = true;
      chart.remove();
      chartRef.current = null;
      seriesRef.current = null;
      markersRef.current = null;
    };
  }, []);

  const runAnalysis = async () => {
    if (disposed.current) return;
    setLoading(true);
    setChartReady(false);
    setCandleCount(0);
    try {
      // Fetch Candles from Alpaca via backend
      const candleRes = await fetch(`/api/market/candles/${ticker}`);
      const rawCandles = await candleRes.json();
      
      if (disposed.current) return;

      // Fetch ML prediction
      let mlResult = null;
      try {
        const mlRes = await fetch(`/api/ml/predict/${ticker}`);
        if (mlRes.ok) {
          mlResult = await mlRes.json();
          if (!mlResult.error) {
            setMlData(mlResult);
          } else {
            setMlData(null);
          }
        }
      } catch (err) {
        console.warn("ML Engine not available.");
        setMlData(null);
      }
      
      if (disposed.current) return;

      if (seriesRef.current && Array.isArray(rawCandles) && rawCandles.length > 0) {
        // Deduplicate and sort
        const uniqueCandles: Record<string, any> = {};
        rawCandles.forEach((c: any) => { uniqueCandles[c.time] = c; });
        const candleData: CandlestickData[] = Object.values(uniqueCandles)
          .sort((a: any, b: any) => a.time - b.time) as CandlestickData[];

        if (disposed.current) return;

        // Set all data at once (no animation loop = no dispose crash)
        seriesRef.current.setData(candleData);
        setCandleCount(candleData.length);
        
        // Apply ML markers
        if (mlResult && mlResult.markers && Array.isArray(mlResult.markers)) {
          const sortedMarkers = mlResult.markers.map((m: any) => ({
            ...m,
            time: typeof m.time === 'string' ? Math.floor(new Date(m.time).getTime() / 1000) : m.time
          })).sort((a: any, b: any) => a.time - b.time);
          
          if (!disposed.current && seriesRef.current) {
            if (markersRef.current) {
              markersRef.current.setMarkers(sortedMarkers);
            } else {
              markersRef.current = createSeriesMarkers(seriesRef.current, sortedMarkers);
            }
          }
        }
        
        if (!disposed.current && chartRef.current) {
          chartRef.current.timeScale().fitContent();
        }
        
        setChartReady(true);
      }
    } catch (e) {
      console.error("Failed AI Lab Analysis", e);
    }
    if (!disposed.current) setLoading(false);
  };

  useEffect(() => {
    // Small delay to ensure chart is created first
    const timer = setTimeout(() => {
      if (!disposed.current) runAnalysis();
    }, 100);
    return () => clearTimeout(timer);
    // eslint-disable-next-line
  }, [ticker]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#8B5CF6] to-[#6366F1] flex items-center justify-center shadow-[0_0_20px_rgba(139,92,246,0.3)]">
              <Cpu className="w-5 h-5 text-white" />
            </div>
            AI Trading Lab
          </h2>
          <p className="text-[#94A3B8] mt-1 text-sm">Random Forest quantitative model · Real-time Alpaca data · ML buy/sell markers</p>
        </div>
        
        <div className="flex gap-3 items-center">
          <select 
            value={ticker}
            onChange={(e) => setTicker(e.target.value)}
            className="bg-[#0b1326] border border-[#334155] text-white px-4 py-2.5 rounded-lg font-mono text-sm focus:border-[#8B5CF6] focus:ring-1 focus:ring-[#8B5CF6]/30 outline-none transition-all"
          >
            {UNIVERSE.map(t => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
          <button 
            onClick={runAnalysis}
            disabled={loading}
            className="flex items-center gap-2 bg-gradient-to-r from-[#8B5CF6] to-[#6366F1] hover:from-[#7C3AED] hover:to-[#4F46E5] disabled:opacity-60 text-white px-5 py-2.5 rounded-lg font-bold transition-all shadow-[0_0_20px_rgba(139,92,246,0.25)] text-sm"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
            ANALYZE
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Chart Area */}
        <div className="lg:col-span-3">
          <div className="bg-[#0f172a]/80 p-5 rounded-2xl border border-[#334155] backdrop-blur-sm relative overflow-hidden">
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-[#8B5CF6] to-transparent opacity-40"></div>
            
            <div className="flex justify-between items-center mb-4">
              <div className="flex items-center gap-3">
                <BarChart3 className="w-4 h-4 text-[#8B5CF6]" />
                <h3 className="text-sm font-bold text-white tracking-tight">
                  {ticker} — OHLC Candlestick
                </h3>
                {chartReady && (
                  <span className="text-[10px] font-mono text-[#22c55e] bg-[#22c55e]/10 border border-[#22c55e]/20 px-2 py-0.5 rounded-full animate-in fade-in duration-300">
                    {candleCount} candles loaded
                  </span>
                )}
              </div>
              <span className="text-[#94A3B8] font-mono text-xs border border-[#334155] px-2 py-0.5 rounded bg-black/30">15Min · IEX Feed</span>
            </div>
            
            {/* Chart loading skeleton */}
            {loading && !chartReady && (
              <div className="absolute inset-0 z-10 flex items-center justify-center bg-[#0f172a]/90 backdrop-blur-sm rounded-2xl">
                <div className="flex flex-col items-center gap-3">
                  <div className="relative">
                    <Loader2 className="w-10 h-10 text-[#8B5CF6] animate-spin" />
                    <div className="absolute inset-0 w-10 h-10 rounded-full bg-[#8B5CF6]/20 animate-ping" />
                  </div>
                  <p className="text-[#8B5CF6] font-mono text-sm animate-pulse">Loading {ticker} market data...</p>
                </div>
              </div>
            )}
            
            <div 
              className={`w-full h-[420px] transition-opacity duration-500 ${chartReady ? 'opacity-100' : 'opacity-30'}`} 
              ref={chartContainerRef} 
            />
            
            <div className="mt-4 flex items-center gap-6 text-sm text-[#94A3B8]">
              <div className="flex items-center gap-2"><div className="w-3 h-3 bg-[#22c55e] rounded-sm"></div> ML Buy Signal</div>
              <div className="flex items-center gap-2"><div className="w-3 h-3 bg-[#ef4444] rounded-sm"></div> ML Sell Signal</div>
              <div className="flex items-center gap-2"><div className="w-3 h-3 bg-[#22c55e]/30 border border-[#22c55e] rounded-sm"></div> Bullish Candle</div>
              <div className="flex items-center gap-2"><div className="w-3 h-3 bg-[#ef4444]/30 border border-[#ef4444] rounded-sm"></div> Bearish Candle</div>
            </div>
          </div>
        </div>

        {/* Right sidebar: Prediction + Info */}
        <div className="space-y-6">
          {/* Prediction Panel */}
          <div className="bg-[#0f172a]/80 p-5 rounded-2xl border border-[#334155] backdrop-blur-sm relative overflow-hidden">
            <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-bl from-[#8B5CF6]/10 to-transparent rounded-full blur-2xl"></div>
            <h3 className="text-sm font-bold text-[#94A3B8] uppercase tracking-wider mb-4">Tomorrow's Prediction</h3>
            {loading ? (
              <div className="flex flex-col items-center justify-center py-8">
                <div className="relative">
                  <Loader2 className="w-10 h-10 text-[#8B5CF6] animate-spin" />
                </div>
                <p className="text-[#8B5CF6] font-mono text-sm animate-pulse mt-3">Running Random Forest...</p>
              </div>
            ) : mlData && mlData.prediction ? (
              <div className="space-y-5">
                <div className="text-center">
                  <div className={`text-5xl font-black mb-1 ${mlData.prediction === 'UP' ? 'text-[#22c55e]' : 'text-[#ef4444]'}`}>
                    {mlData.prediction}
                  </div>
                  <div className="font-mono text-sm">
                    {mlData.prediction === 'UP' ? 
                      <span className="text-[#22c55e]">Bullish Bias</span> : 
                      <span className="text-[#ef4444]">Bearish Bias</span>
                    }
                  </div>
                </div>

                <div className="space-y-3">
                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-white">Upside Probability</span>
                      <span className="text-[#22c55e] font-mono font-bold">{(mlData.probability_up * 100).toFixed(1)}%</span>
                    </div>
                    <div className="w-full bg-[#1E293B] rounded-full h-2.5 overflow-hidden">
                      <div 
                        className="bg-gradient-to-r from-[#22c55e] to-[#10B981] h-2.5 rounded-full transition-all duration-1000 ease-out" 
                        style={{ width: `${mlData.probability_up * 100}%` }}
                      />
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-white">Downside Probability</span>
                      <span className="text-[#ef4444] font-mono font-bold">{(mlData.probability_down * 100).toFixed(1)}%</span>
                    </div>
                    <div className="w-full bg-[#1E293B] rounded-full h-2.5 overflow-hidden">
                      <div 
                        className="bg-gradient-to-r from-[#ef4444] to-[#dc2626] h-2.5 rounded-full transition-all duration-1000 ease-out" 
                        style={{ width: `${mlData.probability_down * 100}%` }}
                      />
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-6">
                <Cpu className="w-8 h-8 text-[#334155] mx-auto mb-2" />
                <p className="text-[#94A3B8] text-sm">ML engine initializing...</p>
                <p className="text-[#475569] text-xs mt-1">Click ANALYZE to run prediction</p>
              </div>
            )}
          </div>

          {/* Info Panel */}
          <div className="bg-[#3b82f6]/10 border border-[#3b82f6]/20 p-4 rounded-xl">
            <div className="flex items-start gap-3">
              <TrendingUp className="w-5 h-5 text-[#3b82f6] shrink-0 mt-0.5" />
              <div className="text-sm">
                <div className="text-[#3b82f6] font-bold mb-1">How It Works</div>
                <div className="text-[#94A3B8] leading-relaxed text-xs">
                  The Random Forest model evaluates RSI, SMA-20, and SMA-50 from real Alpaca IEX data to predict tomorrow's price direction. Green/red arrows on the chart show where the AI would have bought/sold historically.
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
