import React, { useEffect, useState } from 'react';
import { ScrollText, RefreshCw, ArrowUpRight, ArrowDownRight, Clock, CheckCircle2, XCircle, Loader2, AlertCircle } from 'lucide-react';

interface Trade {
  id: string;
  symbol: string;
  side: string;
  qty: number;
  filled_qty: number;
  type: string;
  status: string;
  limit_price: number | null;
  filled_price: number | null;
  submitted_at: string | null;
  filled_at: string | null;
  notional: number | null;
}

export default function TradeLogScreen() {
  const [trades, setTrades] = useState<Trade[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchTrades = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/agent/trades');
      const data = await res.json();
      if (Array.isArray(data)) setTrades(data);
    } catch (err) {
      console.error('Failed to fetch trades:', err);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchTrades();
    const interval = setInterval(fetchTrades, 15000);
    return () => clearInterval(interval);
  }, []);

  const formatTime = (iso: string | null) => {
    if (!iso) return '—';
    const d = new Date(iso);
    return d.toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  };

  const getStatusBadge = (status: string) => {
    const s = status.toLowerCase();
    if (s === 'filled') return (
      <span className="flex items-center gap-1 bg-[#10B981]/15 text-[#10B981] border border-[#10B981]/30 text-[10px] font-mono font-bold px-2 py-0.5 rounded-full">
        <CheckCircle2 className="w-3 h-3" /> FILLED
      </span>
    );
    if (s === 'accepted' || s === 'pending_new' || s === 'new') return (
      <span className="flex items-center gap-1 bg-[#F59E0B]/15 text-[#F59E0B] border border-[#F59E0B]/30 text-[10px] font-mono font-bold px-2 py-0.5 rounded-full">
        <Clock className="w-3 h-3 animate-pulse" /> PENDING
      </span>
    );
    if (s === 'canceled' || s === 'cancelled') return (
      <span className="flex items-center gap-1 bg-[#94A3B8]/15 text-[#94A3B8] border border-[#94A3B8]/30 text-[10px] font-mono font-bold px-2 py-0.5 rounded-full">
        <XCircle className="w-3 h-3" /> CANCELLED
      </span>
    );
    return (
      <span className="flex items-center gap-1 bg-[#EF4444]/15 text-[#EF4444] border border-[#EF4444]/30 text-[10px] font-mono font-bold px-2 py-0.5 rounded-full">
        <AlertCircle className="w-3 h-3" /> {status.toUpperCase()}
      </span>
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#F59E0B] to-[#EF4444] flex items-center justify-center shadow-[0_0_20px_rgba(245,158,11,0.3)]">
              <ScrollText className="w-5 h-5 text-white" />
            </div>
            Live Trade Log
          </h2>
          <p className="text-[#94A3B8] mt-1 text-sm">Real-time feed of all agent orders and executions</p>
        </div>
        <button onClick={fetchTrades} disabled={loading} className="flex items-center gap-2 bg-[#1e293b] border border-[#334155] hover:border-[#F59E0B]/50 text-white px-4 py-2.5 rounded-lg font-bold transition-all text-sm">
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Stats bar */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { label: 'Total Orders', value: trades.length, color: '#6366F1' },
          { label: 'Filled', value: trades.filter(t => t.status === 'filled').length, color: '#10B981' },
          { label: 'Pending', value: trades.filter(t => ['accepted', 'new', 'pending_new'].includes(t.status)).length, color: '#F59E0B' },
          { label: 'Cancelled', value: trades.filter(t => t.status.includes('cancel')).length, color: '#94A3B8' },
        ].map(s => (
          <div key={s.label} className="bg-[#1e293b]/80 border border-[#334155] rounded-xl p-4 backdrop-blur-md">
            <span className="text-[10px] font-mono uppercase text-[#94A3B8] tracking-wider">{s.label}</span>
            <div className="text-2xl font-bold font-mono mt-1" style={{ color: s.color }}>{s.value}</div>
          </div>
        ))}
      </div>

      {/* Trade table */}
      <div className="bg-[#1e293b]/80 border border-[#334155] rounded-xl overflow-hidden backdrop-blur-md shadow-lg">
        <div className="w-full overflow-x-auto">
          <table className="w-full text-left border-collapse min-w-[700px]">
            <thead>
              <tr className="bg-[#0b1326] border-b border-[#334155]">
                <th className="p-4 text-[10px] font-mono uppercase text-[#94A3B8] tracking-wider">Time</th>
                <th className="p-4 text-[10px] font-mono uppercase text-[#94A3B8] tracking-wider">Side</th>
                <th className="p-4 text-[10px] font-mono uppercase text-[#94A3B8] tracking-wider">Symbol</th>
                <th className="p-4 text-[10px] font-mono uppercase text-[#94A3B8] tracking-wider text-right">Qty</th>
                <th className="p-4 text-[10px] font-mono uppercase text-[#94A3B8] tracking-wider text-right">Price</th>
                <th className="p-4 text-[10px] font-mono uppercase text-[#94A3B8] tracking-wider text-right">Value</th>
                <th className="p-4 text-[10px] font-mono uppercase text-[#94A3B8] tracking-wider text-center">Status</th>
              </tr>
            </thead>
            <tbody className="font-mono text-xs text-white">
              {loading && trades.length === 0 ? (
                <tr><td colSpan={7} className="p-12 text-center text-[#94A3B8]">
                  <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2" />
                  Loading trade history...
                </td></tr>
              ) : trades.length === 0 ? (
                <tr><td colSpan={7} className="p-12 text-center text-[#94A3B8]">
                  No trades yet. Agent will log trades here when market opens.
                </td></tr>
              ) : trades.map((trade, i) => (
                <tr key={trade.id + i} className="border-b border-[#334155]/50 hover:bg-[#6366F1]/5 transition-colors animate-in fade-in duration-300" style={{ animationDelay: `${i * 30}ms` }}>
                  <td className="p-4 text-[#94A3B8]">{formatTime(trade.submitted_at)}</td>
                  <td className="p-4">
                    <span className={`flex items-center gap-1 font-bold ${trade.side === 'BUY' ? 'text-[#10B981]' : 'text-[#EF4444]'}`}>
                      {trade.side === 'BUY' ? <ArrowUpRight className="w-3.5 h-3.5" /> : <ArrowDownRight className="w-3.5 h-3.5" />}
                      {trade.side}
                    </span>
                  </td>
                  <td className="p-4">
                    <span className="font-bold text-white bg-[#6366F1]/10 border border-[#6366F1]/20 px-2 py-0.5 rounded">{trade.symbol}</span>
                  </td>
                  <td className="p-4 text-right text-[#e2e8f0]">{trade.filled_qty || trade.qty}</td>
                  <td className="p-4 text-right text-[#e2e8f0]">
                    {trade.filled_price ? `$${trade.filled_price.toFixed(2)}` : trade.limit_price ? `$${trade.limit_price.toFixed(2)}` : '—'}
                  </td>
                  <td className="p-4 text-right text-[#e2e8f0]">
                    {trade.notional ? `$${trade.notional.toLocaleString(undefined, { minimumFractionDigits: 2 })}` : '—'}
                  </td>
                  <td className="p-4 text-center">{getStatusBadge(trade.status)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
