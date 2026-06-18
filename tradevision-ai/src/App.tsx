import React, { useState } from "react";
import SideNavBar from "./components/SideNavBar";
import TopAppBar from "./components/TopAppBar";
import DashboardScreen from "./components/DashboardScreen";
import BacktestScreen from "./components/BacktestScreen";
import StrategyScreen from "./components/StrategyScreen";
import SignalsScreen from "./components/SignalsScreen";
import { X, Shield, Activity, Save, Mail, HelpCircle, AlertOctagon, Bell, Cpu, ArrowUpRight, Check, Sparkles } from "lucide-react";

export default function App() {
  const [activeTab, setActiveTab ] = useState<string>("dashboard");
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isSupportOpen, setIsSupportOpen] = useState(false);
  const [isNotificationsOpen, setIsNotificationsOpen] = useState(false);

  // System parameters state inside settings
  const [systemAlertThreshold, setSystemAlertThreshold] = useState("2.5");
  const [executionRoute, setExecutionRoute] = useState("Low-Latency Router");
  
  // Custom support form state
  const [supportCategory, setSupportCategory] = useState("Strategy Execution");
  const [supportText, setSupportText] = useState("");
  const [supportSuccess, setSupportSuccess] = useState(false);

  const handleSupportSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSupportSuccess(true);
    setTimeout(() => {
      setSupportSuccess(false);
      setSupportText("");
      setIsSupportOpen(false);
    }, 2000);
  };

  // Route selector map
  const renderTabContent = () => {
    switch (activeTab) {
      case "dashboard":
        return <DashboardScreen setTab={setActiveTab} onRunBacktest={() => setActiveTab("backtest")} />;
      case "backtest":
        return <BacktestScreen />;
      case "strategy":
        return <StrategyScreen />;
      case "signals":
        return <SignalsScreen />;
      default:
        return <DashboardScreen setTab={setActiveTab} onRunBacktest={() => setActiveTab("backtest")} />;
    }
  };

  return (
    <div className="min-h-screen bg-[#090d16] text-[#e2e8f0] font-sans antialiased pb-20 md:pb-6 selection:bg-[#6366F1] selection:text-white transition-all duration-300">
      
      {/* Decorative ambient subtle cyber grid vector background */}
      <div className="fixed inset-0 bg-[linear-gradient(to_right,#1f29370a_1px,transparent_1px),linear-gradient(to_bottom,#1f29370a_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none z-0"></div>
      
      {/* Structural Adaptive Navigation HUD (Desktop: 240px, Tablet: 64px, Mobile: Bottom bar) */}
      <SideNavBar 
        currentTab={activeTab} 
        setTab={setActiveTab} 
        onSettingsClick={() => setIsSettingsOpen(true)}
        onSupportClick={() => setIsSupportOpen(true)}
      />

      {/* Main Terminal Shell container layout adjusts padding responsively for tablet (md:pl-16) & desktop (lg:pl-[240px]) */}
      <div className="md:pl-16 lg:pl-[240px] flex flex-col min-h-screen relative z-10 transition-all duration-300">
        
        {/* Global Institutional Top Action Bar */}
        <TopAppBar 
          currentTab={activeTab} 
          setTab={setActiveTab} 
          onRunBacktestClick={() => setActiveTab("backtest")} 
          onSettingsClick={() => setIsSettingsOpen(true)}
          onSupportClick={() => setIsSupportOpen(true)}
          onNotificationClick={() => setIsNotificationsOpen(true)}
        />

        {/* Tactical Screen Canvas Area */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8 mt-16 max-w-7xl w-full mx-auto animate-fade-in">
          {renderTabContent()}
        </main>
      </div>

      {/* ================= MODAL OVERLAYS AND DRAWERS FOR PERFECT VIEWPORT ADAPTABILITY ================= */}

      {/* INTERACTIVE SETTINGS MODAL */}
      {isSettingsOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 backdrop-blur-md bg-[#000000a0] animate-fade-in px-4 sm:px-6">
          <div className="relative bg-[#0f172a] border border-[#334155] rounded-xl w-full max-w-lg overflow-hidden shadow-2xl flex flex-col max-h-[90vh]">
            <header className="p-4 sm:p-5 border-b border-[#334155] flex justify-between items-center bg-[#0b1326]">
              <div className="flex items-center gap-2">
                <Shield className="w-5 h-5 text-[#22D3EE]" />
                <h3 className="font-bold text-white text-md tracking-tight font-display">Institutional Security &amp; Settings</h3>
              </div>
              <button onClick={() => setIsSettingsOpen(false)} className="p-1 rounded-md text-[#94A3B8] hover:text-white hover:bg-[#1e293b] transition-all">
                <X className="w-5 h-5" />
              </button>
            </header>

            <div className="p-5 sm:p-6 overflow-y-auto space-y-6">
              {/* User Profile Info section parsed from local context */}
              <div className="flex items-center gap-4 bg-[#1e293b]/50 border border-[#334155] p-4 rounded-xl">
                <div className="w-12 h-12 rounded-full border-2 border-[#22D3EE] overflow-hidden bg-[#1e293b] shrink-0">
                  <img
                    alt="Institutional User Avatar"
                    className="w-full h-full object-cover"
                    src="https://lh3.googleusercontent.com/aida-public/AB6AXuADODbzfV-so7r4CPZYXDSv1hCRefLDf7ZBRGZQWpVemdkcVVurI3KYMHIDKjKi6eB5wo2KwrMp7YNch8PvrsktmM8CX93WXWFLZDONavoRsYY_glqATm7gsm8iyBq7aSqILC4GAtS6XAGBSkGkOchPSfyLBfZCO_3O-dklUtUa6yLMnTX9Ia7Z4ranCkWgerv3iHcP36v29XDPoSGE0BAgmKofoVuLLgwdxfTeDIw_knMFjKnOfKboc-TD-jAhF_j5mR2hJSfUQEWf"
                  />
                </div>
                <div className="overflow-hidden">
                  <h4 className="font-bold text-white text-sm">Mets Sutariya</h4>
                  <p className="font-mono text-[10px] text-[#22D3EE] tracking-widest uppercase mt-0.5">Role: Alpha Fund Trader</p>
                  <p className="font-mono text-[10px] text-[#94A3B8] truncate mt-0.5">meetsutariya.2008@gmail.com</p>
                </div>
              </div>

              {/* Tactical System Controls */}
              <div className="space-y-4">
                <h5 className="font-mono text-xs text-[#94A3B8] uppercase tracking-wider select-none border-b border-[#334155]/40 pb-2">Risk Safeguards &amp; Routing</h5>
                
                <div>
                  <label className="block text-[10px] font-mono text-[#94A3B8] uppercase tracking-wider mb-2">Max Single-Asset Drift Cap</label>
                  <div className="flex items-center gap-3">
                    <input 
                      type="range" 
                      min="1.0" 
                      max="10.0" 
                      step="0.5" 
                      value={systemAlertThreshold} 
                      onChange={(e) => setSystemAlertThreshold(e.target.value)}
                      className="flex-1 accent-[#6366F1] h-1 bg-[#0b1326] rounded-lg cursor-pointer appearance-none outline-none"	
                    />
                    <span className="bg-[#6366F1]/10 border border-[#6366F1]/30 text-[#6366F1] px-2.5 py-0.5 rounded font-mono text-xs font-bold w-14 text-center">
                      {systemAlertThreshold}%
                    </span>
                  </div>
                </div>

                <div>
                  <label className="block text-[10px] font-mono text-[#94A3B8] uppercase tracking-wider mb-1.5">Execution Broker routing</label>
                  <select 
                    value={executionRoute} 
                    onChange={(e) => setExecutionRoute(e.target.value)}
                    className="w-full bg-[#0b1326] border border-[#334155] rounded-lg text-xs leading-none h-9 px-3 text-white focus:ring-1 focus:ring-[#22D3EE] outline-none"
                  >
                    <option value="Low-Latency Router">Interactive Brokers (Ultra-Low Latency Direct Routing)</option>
                    <option value="Paper Simulation">System Paper Backtester (In-Memory Internal Engine)</option>
                    <option value="Dark Pool Engine">Institutional Dark Pool Block Allocator</option>
                  </select>
                </div>
              </div>

              {/* Tech Stats Diagnostic Grid */}
              <div className="space-y-3">
                <h5 className="font-mono text-xs text-[#94A3B8] uppercase tracking-wider select-none border-b border-[#334155]/40 pb-2">Terminal Server Health</h5>
                <div className="grid grid-cols-3 gap-3">
                  <div className="bg-[#0b1326] border border-[#334155] rounded-lg p-2.5 text-center">
                    <span className="text-[9px] font-mono uppercase text-[#94A3B8] block">API Latency</span>
                    <span className="text-xs font-bold font-mono text-[#10B981] mt-1 inline-block">12ms</span>
                  </div>
                  <div className="bg-[#0b1326] border border-[#334155] rounded-lg p-2.5 text-center">
                    <span className="text-[9px] font-mono uppercase text-[#94A3B8] block">Engine Node</span>
                    <span className="text-xs font-bold font-mono text-[#10B981] mt-1 inline-block">ONLINE</span>
                  </div>
                  <div className="bg-[#0b1326] border border-[#334155] rounded-lg p-2.5 text-center">
                    <span className="text-[9px] font-mono uppercase text-[#94A3B8] block">SSL Security</span>
                    <span className="text-xs font-bold font-mono text-[#22D3EE] mt-1 inline-block">AES-256</span>
                  </div>
                </div>
              </div>
            </div>

            <footer className="p-4 border-t border-[#334155] flex justify-end bg-[#0b1326] gap-3">
              <button onClick={() => setIsSettingsOpen(false)} className="px-4 py-2 text-xs font-mono font-bold text-[#94A3B8] hover:text-white hover:bg-[#1e293b] rounded-lg transition-all uppercase">
                Close
              </button>
              <button onClick={() => setIsSettingsOpen(false)} className="px-5 py-2 text-xs font-mono font-bold text-white bg-[#6366F1] hover:bg-opacity-90 rounded-lg transition-all uppercase flex items-center gap-1">
                <Check className="w-4 h-4" />
                <span>Save Client Rules</span>
              </button>
            </footer>
          </div>
        </div>
      )}

      {/* SUPPORT & HELP CONSOLE MODAL */}
      {isSupportOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 backdrop-blur-md bg-[#000000a0] animate-fade-in px-4 sm:px-6">
          <div className="relative bg-[#0f172a] border border-[#334155] rounded-xl w-full max-w-md overflow-hidden shadow-2xl flex flex-col">
            <header className="p-4 sm:p-5 border-b border-[#334155] flex justify-between items-center bg-[#0b1326]">
              <div className="flex items-center gap-2">
                <HelpCircle className="w-5 h-5 text-[#22D3EE]" />
                <h3 className="font-bold text-white text-md tracking-tight font-display">Quant Help Desk Support</h3>
              </div>
              <button onClick={() => setIsSupportOpen(false)} className="p-1 rounded-md text-[#94A3B8] hover:text-white hover:bg-[#1e293b] transition-all">
                <X className="w-5 h-5" />
              </button>
            </header>

            <form onSubmit={handleSupportSubmit} className="flex-1 flex flex-col">
              <div className="p-5 sm:p-6 space-y-4">
                <p className="text-xs text-[#94A3B8] leading-relaxed">
                  Submit tickets directly to our institutional system operations group. Low latency response within 15 minutes.
                </p>

                {supportSuccess ? (
                  <div className="bg-[#10B981]/15 border border-[#10B981]/30 rounded-lg p-5 text-center space-y-2 animate-fade-in">
                    <Check className="w-8 h-8 text-[#10B981] mx-auto animate-bounce" />
                    <h4 className="text-white text-sm font-bold font-mono">TICKET TRANSMITTED!</h4>
                    <p className="text-[10px] text-[#94A3B8] font-mono uppercase">Ticket ID: TV-8809-AISTUDIO</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div>
                      <label className="block text-[10px] font-mono text-[#94A3B8] uppercase tracking-wider mb-1.5">Problem Classification</label>
                      <select 
                        value={supportCategory} 
                        onChange={(e) => setSupportCategory(e.target.value)}
                        className="w-full bg-[#0b1326] border border-[#334155] rounded-lg text-xs leading-none h-9 px-3 text-white focus:ring-1 focus:ring-[#22D3EE] outline-none"
                      >
                        <option value="Strategy Execution">Divergence in Backtest vs. Simulated Curve</option>
                        <option value="API Pricing">Live Pricing Feeds Latency/Lag</option>
                        <option value="Risk Filter">SMA-200 Protective Filter False Trigger</option>
                        <option value="Billing Plan">Institutional Account Limits Upgrade</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-[10px] font-mono text-[#94A3B8] uppercase tracking-wider mb-1.5">Detailed diagnostics</label>
                      <textarea
                        required
                        value={supportText}
                        onChange={(e) => setSupportText(e.target.value)}
                        placeholder="Provide details of transaction, ticker, parameters or requested assets..."
                        className="w-full bg-[#0b1326] border border-[#334155] rounded-lg text-xs p-3 text-white h-24 focus:ring-1 focus:ring-[#22D3EE] outline-none font-mono resize-none"
                      />
                    </div>
                  </div>
                )}
              </div>

              {!supportSuccess && (
                <footer className="p-4 border-t border-[#334155] flex justify-end bg-[#0b1326] gap-3">
                  <button type="button" onClick={() => setIsSupportOpen(false)} className="px-4 py-2 text-xs font-mono font-bold text-[#94A3B8] hover:text-white hover:bg-[#1e293b] rounded-lg transition-all uppercase">
                    Cancel
                  </button>
                  <button type="submit" className="px-5 py-2 text-xs font-mono font-bold text-white bg-[#6366F1] hover:bg-opacity-90 rounded-lg transition-all uppercase">
                    Transmit Ticket
                  </button>
                </footer>
              )}
            </form>
          </div>
        </div>
      )}

      {/* SYSTEM ALERTS & NOTIFICATIONS LOG DRAWER */}
      {isNotificationsOpen && (
        <div className="fixed inset-y-0 right-0 z-50 w-full sm:w-80 bg-[#0f172a] border-l border-[#334155] shadow-2xl flex flex-col animate-fade-in">
          <header className="p-5 border-b border-[#334155] flex justify-between items-center bg-[#0b1326]">
            <div className="flex items-center gap-2">
              <Bell className="w-4 h-4 text-[#22D3EE]" />
              <h3 className="font-bold text-white text-sm uppercase tracking-wider font-mono">System Signal Log</h3>
            </div>
            <button onClick={() => setIsNotificationsOpen(false)} className="p-1 rounded-md text-[#94A3B8] hover:text-white hover:bg-[#1e293b] transition-all">
              <X className="w-5 h-5" />
            </button>
          </header>

          <div className="flex-1 overflow-y-auto p-4 space-y-3.5">
            <p className="text-[10px] font-mono text-[#94A3B8] uppercase tracking-widest pb-2 border-b border-[#334155]/20">Most Recent Events</p>
            
            {/* Event 1 */}
            <div className="p-3 bg-[#1e293b]/50 border border-[#334155] rounded-xl space-y-1">
              <div className="flex justify-between items-start">
                <span className="text-[9px] font-mono text-[#10B981] font-bold uppercase bg-[#10B981]/10 px-1.5 py-0.5 rounded">Rebalanced</span>
                <span className="text-[9px] font-mono text-[#94A3B8]">16:00 EST Today</span>
              </div>
              <h5 className="text-xs font-bold text-white font-mono">QQQ Momentum Active</h5>
              <p className="text-[10px] text-[#94A3B8] leading-tight">Reallocated long weights to QQQ. Momentum index exceeds GLD and TLT.</p>
            </div>

            {/* Event 2 */}
            <div className="p-3 bg-[#1e293b]/50 border border-[#334155] rounded-xl space-y-1">
              <div className="flex justify-between items-start">
                <span className="text-[9px] font-mono text-[#22D3EE] font-bold uppercase bg-[#22D3EE]/10 px-1.5 py-0.5 rounded flex items-center gap-1">
                  <Activity className="w-2.5 h-2.5 animate-pulse" />
                  <span>System Ping</span>
                </span>
                <span className="text-[9px] font-mono text-[#94A3B8]">15:45 EST</span>
              </div>
              <h5 className="text-xs font-bold text-white font-mono">Datafeed latency check</h5>
              <p className="text-[10px] text-[#94A3B8] leading-tight">Quant connection to IEX Cloud and AlphaVantage normalized with 12ms latency.</p>
            </div>

            {/* Event 3 */}
            <div className="p-3 bg-[#1e293b]/50 border border-[#334155] rounded-xl space-y-1">
              <div className="flex justify-between items-start">
                <span className="text-[9px] font-mono text-[#6366F1] font-bold uppercase bg-[#6366F1]/10 px-1.5 py-0.5 rounded">Risk Shield</span>
                <span className="text-[9px] font-mono text-[#94A3B8]">Yesterday</span>
              </div>
              <h5 className="text-xs font-bold text-white font-mono">SMA protective filter status</h5>
              <p className="text-[10px] text-[#94A3B8] leading-tight">SPY pricing continues above 200-day Simple Moving Average trend support. Risk limits clear.</p>
            </div>

            {/* Event 4 */}
            <div className="p-3 bg-[#1e293b]/30 border border-[#334155]/50 rounded-xl space-y-1 opacity-60">
              <div className="flex justify-between items-start">
                <span className="text-[9px] font-mono text-[#94A3B8] font-bold uppercase bg-[#94A3B8]/10 px-1.5 py-0.5 rounded">Client Action</span>
                <span className="text-[9px] font-mono text-[#94A3B8]">Oct 15</span>
              </div>
              <h5 className="text-xs font-bold text-white font-mono">Configuration Preset Saved</h5>
              <p className="text-[10px] text-[#94A3B8] leading-tight">Mets Sutariya updated the Lookback period limit parameter to 63 trading days.</p>
            </div>
          </div>

          <div className="p-4 border-t border-[#334155] bg-[#0b1326] text-center">
            <button onClick={() => setIsNotificationsOpen(false)} className="w-full py-2.5 bg-[#1e293b] hover:bg-[#334155] text-white font-mono text-[10px] font-bold uppercase tracking-wider rounded-lg transition-colors">
              Dismiss All Logs
            </button>
          </div>
        </div>
      )}

      {/* Floating notifications background backdrop */}
      {isNotificationsOpen && (
        <div 
          onClick={() => setIsNotificationsOpen(false)} 
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm"
        />
      )}

    </div>
  );
}
