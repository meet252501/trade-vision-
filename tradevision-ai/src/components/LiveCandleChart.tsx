import React, { useEffect, useRef, useState } from "react";
import { createChart, ColorType, CrosshairMode, CandlestickSeries } from "lightweight-charts";
import { Loader2 } from "lucide-react";

interface LiveCandleChartProps {
  ticker: string;
}

export default function LiveCandleChart({ ticker }: LiveCandleChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<any>(null);
  const seriesRef = useRef<any>(null);
  const disposed = useRef(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    disposed.current = false;
    if (!chartContainerRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "#94A3B8",
        fontFamily: "'Inter', sans-serif",
      },
      grid: {
        vertLines: { color: "#1E293B" },
        horzLines: { color: "#1E293B" },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
        vertLine: { width: 1, color: "#6366F1", style: 0, labelBackgroundColor: "#6366F1" },
        horzLine: { width: 1, color: "#6366F1", style: 0, labelBackgroundColor: "#6366F1" },
      },
      timeScale: {
        borderColor: "#334155",
        timeVisible: true,
      },
      rightPriceScale: {
        borderColor: "#334155",
      },
      autoSize: true,
    });

    chartRef.current = chart;

    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: "#10B981",
      downColor: "#EF4444",
      borderVisible: false,
      wickUpColor: "#10B981",
      wickDownColor: "#EF4444",
    });
    seriesRef.current = candleSeries;

    const fetchRealData = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(`/api/market/candles/${ticker}`);
        if (!res.ok) throw new Error("Failed to fetch candle data");
        const rawCandles = await res.json();
        
        if (disposed.current) return; // Abort if unmounted

        if (Array.isArray(rawCandles) && rawCandles.length > 0) {
          const unique: Record<string, any> = {};
          rawCandles.forEach((c: any) => { unique[c.time] = c; });
          const sorted = Object.values(unique)
            .sort((a: any, b: any) => a.time - b.time);
          
          if (!disposed.current && seriesRef.current) {
            seriesRef.current.setData(sorted as any);
            chart.timeScale().fitContent();
          }
        } else {
          setError("No candle data available");
        }
      } catch (err: any) {
        if (!disposed.current) {
          console.error("LiveCandleChart fetch error:", err);
          setError(err.message || "Failed to load data");
        }
      }
      if (!disposed.current) setLoading(false);
    };

    fetchRealData();

    return () => {
      disposed.current = true;
      chart.remove();
      chartRef.current = null;
      seriesRef.current = null;
    };
  }, [ticker]);

  return (
    <div className="w-full h-[300px] relative">
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-[#0f172a]/60 backdrop-blur-sm z-10 rounded-lg">
          <div className="flex items-center gap-2">
            <Loader2 className="w-5 h-5 text-[#6366F1] animate-spin" />
            <span className="text-[#94A3B8] text-sm font-mono">Loading {ticker} candles...</span>
          </div>
        </div>
      )}
      {error && !loading && (
        <div className="absolute inset-0 flex items-center justify-center z-10">
          <span className="text-[#EF4444] text-sm font-mono">{error}</span>
        </div>
      )}
      <div className="w-full h-full" ref={chartContainerRef} />
    </div>
  );
}
