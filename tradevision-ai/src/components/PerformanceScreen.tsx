import React, { useEffect, useState } from 'react';
import { Trophy, TrendingUp, TrendingDown, Target, Clock, Zap, BarChart3, Loader2 } from 'lucide-react';

export default function PerformanceScreen() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchPerformance = async () => {
      try {
        const res = await fetch('/api/agent/performance');
        const json = await res.json();
        if (!json.error) setData(json);
      } catch (err) {
        console.error('Failed to fetch performance:', err);
      }
      setLoading(false);
    };
    fetchPerformance();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-10 h-10 text-[#8B5CF6] animate-spin" />
      </div>
    );
  }

  const winRate = data?.win_rate || 0;
  const totalTrades = data?.total_trades || 0;
  const totalPnl = data?.total_pnl || 0;
  const avgHold = data?.avg_hold_hours || 0;
  const avgWin = data?.avg_win || 0;
  const avgLoss = data?.avg_loss || 0;
  const equity = data?.equity || 0;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white tracking-tight flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#10B981] to-[#22D3EE] flex items-center justify-center shadow-[0_0_20px_rgba(16,185,129,0.3)]">
            <Trophy className="w-5 h-5 text-white" />
          </div>
          Agent Performance
        </h2>
        <p className="text-[#94A3B8] mt-1 text-sm">Comprehensive analytics on your autonomous trading agent</p>
      </div>

      {/* Key metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-[#1e293b]/80 border border-[#334155] rounded-xl p-5 backdrop-blur-md relative overflow-hidden group">
          <div className="absolute -top-8 -right-8 w-20 h-20 bg-[#10B981]/10 rounded-full blur-2xl group-hover:scale-150 transition-transform" />
          <Target className="w-5 h-5 text-[#10B981] mb-2" />
          <span className="text-[10px] font-mono uppercase text-[#94A3B8] tracking-wider block">Win Rate</span>
          <span className="text-3xl font-black font-mono text-[#10B981] mt-1 block">{winRate}%</span>
          <span className="text-[10px] text-[#94A3B8] font-mono">{data?.wins || 0}W / {data?.losses || 0}L</span>
        </div>

        <div className="bg-[#1e293b]/80 border border-[#334155] rounded-xl p-5 backdrop-blur-md relative overflow-hidden group">
          <div className="absolute -top-8 -right-8 w-20 h-20 bg-[#6366F1]/10 rounded-full blur-2xl group-hover:scale-150 transition-transform" />
          <BarChart3 className="w-5 h-5 text-[#6366F1] mb-2" />
          <span className="text-[10px] font-mono uppercase text-[#94A3B8] tracking-wider block">Total P&L</span>
          <span className={`text-3xl font-black font-mono mt-1 block ${totalPnl >= 0 ? 'text-[#10B981]' : 'text-[#EF4444]'}`}>
            {totalPnl >= 0 ? '+' : ''}${totalPnl.toFixed(2)}
          </span>
          <span className="text-[10px] text-[#94A3B8] font-mono">{totalTrades} round-trip trades</span>
        </div>

        <div className="bg-[#1e293b]/80 border border-[#334155] rounded-xl p-5 backdrop-blur-md relative overflow-hidden group">
          <div className="absolute -top-8 -right-8 w-20 h-20 bg-[#22D3EE]/10 rounded-full blur-2xl group-hover:scale-150 transition-transform" />
          <Clock className="w-5 h-5 text-[#22D3EE] mb-2" />
          <span className="text-[10px] font-mono uppercase text-[#94A3B8] tracking-wider block">Avg Hold Time</span>
          <span className="text-3xl font-black font-mono text-[#22D3EE] mt-1 block">{avgHold}h</span>
          <span className="text-[10px] text-[#94A3B8] font-mono">Per completed trade</span>
        </div>

        <div className="bg-[#1e293b]/80 border border-[#334155] rounded-xl p-5 backdrop-blur-md relative overflow-hidden group">
          <div className="absolute -top-8 -right-8 w-20 h-20 bg-[#F59E0B]/10 rounded-full blur-2xl group-hover:scale-150 transition-transform" />
          <Zap className="w-5 h-5 text-[#F59E0B] mb-2" />
          <span className="text-[10px] font-mono uppercase text-[#94A3B8] tracking-wider block">Account Equity</span>
          <span className="text-3xl font-black font-mono text-white mt-1 block">${equity.toLocaleString(undefined, {minimumFractionDigits: 0})}</span>
          <span className="text-[10px] text-[#94A3B8] font-mono">
            {data?.daily_return_pct >= 0 ? '+' : ''}{data?.daily_return_pct || 0}% today
          </span>
        </div>
      </div>

      {/* Win/Loss distribution */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-[#1e293b]/80 border border-[#334155] rounded-xl p-6 backdrop-blur-md">
          <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-[#10B981]" /> Average Win
          </h3>
          <div className="text-4xl font-black font-mono text-[#10B981]">+${avgWin.toFixed(2)}</div>
          {data?.best_trade && (
            <div className="mt-3 bg-[#10B981]/10 border border-[#10B981]/20 rounded-lg p-3">
              <span className="text-[10px] font-mono text-[#10B981] uppercase">Best Trade</span>
              <div className="text-sm font-bold text-white mt-1">
                {data.best_trade.symbol} — +${data.best_trade.pnl.toFixed(2)}
              </div>
              <div className="text-[10px] text-[#94A3B8] font-mono">
                Buy ${data.best_trade.buy_price?.toFixed(2)} → Sell ${data.best_trade.sell_price?.toFixed(2)} ({data.best_trade.qty} shares)
              </div>
            </div>
          )}
        </div>

        <div className="bg-[#1e293b]/80 border border-[#334155] rounded-xl p-6 backdrop-blur-md">
          <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
            <TrendingDown className="w-4 h-4 text-[#EF4444]" /> Average Loss
          </h3>
          <div className="text-4xl font-black font-mono text-[#EF4444]">${avgLoss.toFixed(2)}</div>
          {data?.worst_trade && (
            <div className="mt-3 bg-[#EF4444]/10 border border-[#EF4444]/20 rounded-lg p-3">
              <span className="text-[10px] font-mono text-[#EF4444] uppercase">Worst Trade</span>
              <div className="text-sm font-bold text-white mt-1">
                {data.worst_trade.symbol} — ${data.worst_trade.pnl.toFixed(2)}
              </div>
              <div className="text-[10px] text-[#94A3B8] font-mono">
                Buy ${data.worst_trade.buy_price?.toFixed(2)} → Sell ${data.worst_trade.sell_price?.toFixed(2)} ({data.worst_trade.qty} shares)
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Win rate visual bar */}
      <div className="bg-[#1e293b]/80 border border-[#334155] rounded-xl p-6 backdrop-blur-md">
        <h3 className="text-sm font-bold text-white mb-4">Win/Loss Distribution</h3>
        <div className="flex h-8 rounded-lg overflow-hidden border border-[#334155]">
          <div className="bg-gradient-to-r from-[#10B981] to-[#22c55e] transition-all duration-1000" style={{ width: `${winRate}%` }} />
          <div className="bg-gradient-to-r from-[#EF4444] to-[#dc2626] flex-1" />
        </div>
        <div className="flex justify-between mt-2 text-xs font-mono">
          <span className="text-[#10B981]">{winRate}% Wins</span>
          <span className="text-[#EF4444]">{(100 - winRate).toFixed(1)}% Losses</span>
        </div>
      </div>

      {/* Trade history table */}
      {data?.trades && data.trades.length > 0 && (
        <div className="bg-[#1e293b]/80 border border-[#334155] rounded-xl overflow-hidden backdrop-blur-md">
          <div className="p-4 border-b border-[#334155]">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider font-mono">Recent Round-Trip Trades</h3>
          </div>
          <div className="w-full overflow-x-auto">
            <table className="w-full text-left border-collapse min-w-[500px]">
              <thead>
                <tr className="bg-[#0b1326]">
                  <th className="p-3 text-[10px] font-mono uppercase text-[#94A3B8]">Symbol</th>
                  <th className="p-3 text-[10px] font-mono uppercase text-[#94A3B8] text-right">Buy</th>
                  <th className="p-3 text-[10px] font-mono uppercase text-[#94A3B8] text-right">Sell</th>
                  <th className="p-3 text-[10px] font-mono uppercase text-[#94A3B8] text-right">Qty</th>
                  <th className="p-3 text-[10px] font-mono uppercase text-[#94A3B8] text-right">P&L</th>
                </tr>
              </thead>
              <tbody className="font-mono text-xs">
                {data.trades.map((t: any, i: number) => (
                  <tr key={i} className="border-b border-[#334155]/30 hover:bg-[#6366F1]/5 transition-colors">
                    <td className="p-3 text-white font-bold">{t.symbol}</td>
                    <td className="p-3 text-right text-[#94A3B8]">${t.buy_price?.toFixed(2)}</td>
                    <td className="p-3 text-right text-[#94A3B8]">${t.sell_price?.toFixed(2)}</td>
                    <td className="p-3 text-right text-[#94A3B8]">{t.qty}</td>
                    <td className={`p-3 text-right font-bold ${t.pnl >= 0 ? 'text-[#10B981]' : 'text-[#EF4444]'}`}>
                      {t.pnl >= 0 ? '+' : ''}${t.pnl.toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
