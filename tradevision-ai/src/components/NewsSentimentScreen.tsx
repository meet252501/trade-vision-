import React, { useEffect, useState } from 'react';
import { Newspaper, RefreshCw, TrendingUp, TrendingDown, Minus, Loader2, ExternalLink } from 'lucide-react';

interface NewsItem {
  headline: string;
  source: string;
  sentiment: number;
  time: string;
  url?: string;
  symbols?: string[];
}

export default function NewsSentimentScreen() {
  const [news, setNews] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [ticker, setTicker] = useState('SPY');
  const tickers = ['SPY', 'QQQ', 'XLK', 'SMH', 'XLF', 'XLE', 'XLV', 'GLD', 'TLT', 'IWM'];

  const fetchNews = async (sym: string) => {
    setLoading(true);
    try {
      const res = await fetch(`/api/news/${sym}`);
      const data = await res.json();
      if (Array.isArray(data)) setNews(data);
    } catch (err) {
      console.error('Failed to fetch news:', err);
    }
    setLoading(false);
  };

  useEffect(() => { fetchNews(ticker); }, [ticker]);

  const getSentimentBadge = (sentiment: number) => {
    if (sentiment > 0.15) return { label: 'BULLISH', color: '#10B981', icon: TrendingUp, bg: 'rgba(16,185,129,0.12)' };
    if (sentiment < -0.15) return { label: 'BEARISH', color: '#EF4444', icon: TrendingDown, bg: 'rgba(239,68,68,0.12)' };
    return { label: 'NEUTRAL', color: '#94A3B8', icon: Minus, bg: 'rgba(148,163,184,0.12)' };
  };

  const avgSentiment = news.length > 0 ? news.reduce((s, n) => s + n.sentiment, 0) / news.length : 0;
  const overallBadge = getSentimentBadge(avgSentiment);

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#8B5CF6] to-[#EC4899] flex items-center justify-center shadow-[0_0_20px_rgba(139,92,246,0.3)]">
              <Newspaper className="w-5 h-5 text-white" />
            </div>
            News Sentiment
          </h2>
          <p className="text-[#94A3B8] mt-1 text-sm">AI-scored financial news headlines for your universe</p>
        </div>
      </div>

      {/* Ticker selector */}
      <div className="flex flex-wrap gap-2">
        {tickers.map(t => (
          <button
            key={t}
            onClick={() => { setTicker(t); }}
            className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold border transition-all ${
              t === ticker
                ? 'bg-[#8B5CF6]/20 border-[#8B5CF6] text-[#8B5CF6] shadow-[0_0_12px_rgba(139,92,246,0.2)]'
                : 'bg-[#1e293b] border-[#334155] text-[#94A3B8] hover:border-[#8B5CF6]/50 hover:text-white'
            }`}
          >{t}</button>
        ))}
      </div>

      {/* Overall Sentiment */}
      <div className="bg-[#1e293b]/80 border border-[#334155] rounded-xl p-6 backdrop-blur-md flex items-center gap-6">
        <div className="w-20 h-20 rounded-2xl flex items-center justify-center" style={{ background: overallBadge.bg, border: `2px solid ${overallBadge.color}30` }}>
          <overallBadge.icon className="w-10 h-10" style={{ color: overallBadge.color }} />
        </div>
        <div>
          <span className="text-[10px] font-mono uppercase text-[#94A3B8] tracking-wider">Overall Sentiment for {ticker}</span>
          <div className="text-3xl font-black mt-1" style={{ color: overallBadge.color }}>{overallBadge.label}</div>
          <div className="text-sm font-mono text-[#94A3B8] mt-0.5">
            Score: {avgSentiment >= 0 ? '+' : ''}{avgSentiment.toFixed(2)} | {news.length} articles
          </div>
        </div>
        {/* Sentiment meter */}
        <div className="flex-1 hidden md:block">
          <div className="flex items-center gap-2">
            <span className="text-xs text-[#EF4444] font-mono">-1.0</span>
            <div className="flex-1 h-3 rounded-full bg-gradient-to-r from-[#EF4444] via-[#94A3B8] to-[#10B981] relative">
              <div
                className="absolute top-1/2 -translate-y-1/2 w-4 h-4 rounded-full bg-white border-2 shadow-lg transition-all duration-500"
                style={{ left: `${Math.min(100, Math.max(0, (avgSentiment + 1) * 50))}%`, borderColor: overallBadge.color }}
              />
            </div>
            <span className="text-xs text-[#10B981] font-mono">+1.0</span>
          </div>
        </div>
      </div>

      {/* News list */}
      <div className="space-y-3">
        {loading ? (
          <div className="flex items-center justify-center py-16">
            <Loader2 className="w-8 h-8 text-[#8B5CF6] animate-spin" />
          </div>
        ) : news.length === 0 ? (
          <div className="text-center py-16 text-[#94A3B8]">
            <Newspaper className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p className="font-mono text-sm">No recent news found for {ticker}</p>
          </div>
        ) : news.map((item, i) => {
          const badge = getSentimentBadge(item.sentiment);
          return (
            <div
              key={i}
              className="bg-[#1e293b]/80 border border-[#334155] rounded-xl p-5 backdrop-blur-md hover:border-[#8B5CF6]/30 transition-all group"
              style={{ animationDelay: `${i * 50}ms` }}
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <h3 className="text-sm font-semibold text-white leading-relaxed group-hover:text-[#e2e8f0] transition-colors">
                    {item.headline}
                  </h3>
                  <div className="flex items-center gap-3 mt-2">
                    <span className="text-[10px] font-mono text-[#94A3B8]">{item.source}</span>
                    <span className="text-[10px] font-mono text-[#64748B]">{item.time}</span>
                    {item.symbols && item.symbols.length > 0 && (
                      <div className="flex gap-1">
                        {item.symbols.slice(0, 3).map(s => (
                          <span key={s} className="text-[9px] font-mono bg-[#6366F1]/10 text-[#6366F1] px-1.5 py-0.5 rounded">{s}</span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
                <div className="flex flex-col items-end gap-2 shrink-0">
                  <span
                    className="flex items-center gap-1 text-[10px] font-mono font-bold px-2.5 py-1 rounded-lg"
                    style={{ background: badge.bg, color: badge.color, border: `1px solid ${badge.color}30` }}
                  >
                    <badge.icon className="w-3 h-3" />
                    {badge.label}
                  </span>
                  <div className="w-16 h-1.5 rounded-full bg-[#0b1326] overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-500"
                      style={{
                        width: `${Math.abs(item.sentiment) * 100}%`,
                        background: badge.color,
                        marginLeft: item.sentiment < 0 ? 'auto' : 0
                      }}
                    />
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
