import React, { useState, useEffect } from 'react';
import { Eye, Bell, Plus, Trash2, ArrowUpRight, ArrowDownRight, Settings } from 'lucide-react';

interface WatchItem {
  ticker: string;
  price: number | null;
  change: number | null;
  alertAbove: number | null;
  alertBelow: number | null;
}

export default function WatchlistScreen() {
  const [watchlist, setWatchlist] = useState<WatchItem[]>([]);
  const [newTicker, setNewTicker] = useState('');

  // Load from local storage on mount
  useEffect(() => {
    const saved = localStorage.getItem('tradevision_watchlist');
    if (saved) {
      setWatchlist(JSON.parse(saved));
    } else {
      setWatchlist([
        { ticker: 'SPY', price: null, change: null, alertAbove: 550, alertBelow: 500 },
        { ticker: 'QQQ', price: null, change: null, alertAbove: null, alertBelow: null },
      ]);
    }
  }, []);

  // Save to local storage
  useEffect(() => {
    if (watchlist.length > 0) {
      localStorage.setItem('tradevision_watchlist', JSON.stringify(watchlist));
    }
  }, [watchlist]);

  // Fetch prices
  useEffect(() => {
    const fetchPrices = async () => {
      if (watchlist.length === 0) return;
      
      const updated = [...watchlist];
      for (let i = 0; i < updated.length; i++) {
        try {
          const res = await fetch(`/api/prices/${updated[i].ticker}?period=1m`);
          const data = await res.json();
          if (data && data.length > 1) {
            const current = data[data.length - 1].close;
            const prev = data[data.length - 2].close;
            updated[i].price = current;
            updated[i].change = ((current - prev) / prev) * 100;

            // Check alerts
            if (updated[i].alertAbove && current > updated[i].alertAbove!) {
              if (Notification.permission === 'granted') {
                new Notification(`TradeVision Alert: ${updated[i].ticker} Breakout`, {
                  body: `${updated[i].ticker} crossed above ${updated[i].alertAbove}`,
                  icon: '/favicon.ico'
                });
              }
            }
            if (updated[i].alertBelow && current < updated[i].alertBelow!) {
              if (Notification.permission === 'granted') {
                new Notification(`TradeVision Alert: ${updated[i].ticker} Breakdown`, {
                  body: `${updated[i].ticker} crossed below ${updated[i].alertBelow}`,
                  icon: '/favicon.ico'
                });
              }
            }
          }
        } catch { /* ignore */ }
      }
      setWatchlist(updated);
    };

    fetchPrices();
    const interval = setInterval(fetchPrices, 60000); // update every minute
    return () => clearInterval(interval);
  }, [watchlist.length]); // only re-bind if watchlist size changes

  const addTicker = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTicker) return;
    const t = newTicker.toUpperCase().trim();
    if (!watchlist.find(w => w.ticker === t)) {
      setWatchlist([...watchlist, { ticker: t, price: null, change: null, alertAbove: null, alertBelow: null }]);
      
      // Request notification permission if adding first ticker
      if (Notification.permission !== 'granted' && Notification.permission !== 'denied') {
        Notification.requestPermission();
      }
    }
    setNewTicker('');
  };

  const removeTicker = (ticker: string) => {
    setWatchlist(watchlist.filter(w => w.ticker !== ticker));
  };

  const updateAlert = (ticker: string, field: 'alertAbove' | 'alertBelow', val: string) => {
    const num = val === '' ? null : parseFloat(val);
    setWatchlist(watchlist.map(w => w.ticker === ticker ? { ...w, [field]: num } : w));
  };

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h2 className="text-2xl font-bold text-white tracking-tight flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#3B82F6] to-[#8B5CF6] flex items-center justify-center shadow-[0_0_20px_rgba(59,130,246,0.3)]">
            <Eye className="w-5 h-5 text-white" />
          </div>
          Watchlist & Alerts
        </h2>
        <p className="text-[#94A3B8] mt-1 text-sm">Monitor custom assets and set browser push notifications for price levels.</p>
      </div>

      <div className="bg-[#1e293b]/80 border border-[#334155] rounded-xl p-6 backdrop-blur-md">
        <form onSubmit={addTicker} className="flex gap-3 mb-6">
          <input
            type="text"
            value={newTicker}
            onChange={(e) => setNewTicker(e.target.value)}
            placeholder="Add ticker (e.g., TSLA, NVDA)"
            className="bg-[#0b1326] border border-[#334155] rounded-lg px-4 py-2 text-white font-mono uppercase focus:outline-none focus:border-[#3B82F6] transition-colors flex-1"
          />
          <button type="submit" className="bg-[#3B82F6] hover:bg-[#2563EB] text-white px-4 py-2 rounded-lg font-bold flex items-center gap-2 transition-colors">
            <Plus className="w-4 h-4" /> Add
          </button>
        </form>

        <div className="space-y-3">
          {watchlist.map(item => (
            <div key={item.ticker} className="flex flex-col sm:flex-row sm:items-center justify-between p-4 bg-[#0b1326] border border-[#334155] rounded-lg gap-4 group">
              <div className="flex items-center justify-between sm:justify-start gap-6 min-w-[200px]">
                <span className="text-lg font-bold font-mono text-white">{item.ticker}</span>
                <div className="text-right sm:text-left">
                  <div className="text-sm font-mono text-[#e2e8f0]">
                    {item.price ? `$${item.price.toFixed(2)}` : 'Loading...'}
                  </div>
                  {item.change !== null && (
                    <div className={`flex items-center justify-end sm:justify-start gap-1 text-[10px] font-mono ${item.change >= 0 ? 'text-[#10B981]' : 'text-[#EF4444]'}`}>
                      {item.change >= 0 ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
                      {Math.abs(item.change).toFixed(2)}%
                    </div>
                  )}
                </div>
              </div>

              <div className="flex items-center gap-3 flex-1 sm:justify-end">
                <div className="flex items-center gap-2 bg-[#1e293b] px-3 py-1.5 rounded border border-[#334155]">
                  <Bell className="w-3.5 h-3.5 text-[#94A3B8]" />
                  <span className="text-[10px] text-[#94A3B8] font-mono uppercase">Above</span>
                  <input
                    type="number"
                    value={item.alertAbove || ''}
                    onChange={(e) => updateAlert(item.ticker, 'alertAbove', e.target.value)}
                    placeholder="None"
                    className="w-20 bg-transparent border-b border-[#334155] text-white font-mono text-sm focus:outline-none focus:border-[#10B981] text-right"
                  />
                </div>
                <div className="flex items-center gap-2 bg-[#1e293b] px-3 py-1.5 rounded border border-[#334155]">
                  <Bell className="w-3.5 h-3.5 text-[#94A3B8]" />
                  <span className="text-[10px] text-[#94A3B8] font-mono uppercase">Below</span>
                  <input
                    type="number"
                    value={item.alertBelow || ''}
                    onChange={(e) => updateAlert(item.ticker, 'alertBelow', e.target.value)}
                    placeholder="None"
                    className="w-20 bg-transparent border-b border-[#334155] text-white font-mono text-sm focus:outline-none focus:border-[#EF4444] text-right"
                  />
                </div>
                <button
                  onClick={() => removeTicker(item.ticker)}
                  className="p-2 text-[#64748B] hover:text-[#EF4444] hover:bg-[#EF4444]/10 rounded transition-colors ml-2"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
          {watchlist.length === 0 && (
            <div className="text-center py-12 text-[#64748B]">
              <Eye className="w-12 h-12 mx-auto mb-3 opacity-20" />
              <p>Your watchlist is empty.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
