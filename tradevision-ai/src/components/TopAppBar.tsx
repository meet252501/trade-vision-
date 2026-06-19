import React from "react";
import { Bell, User, Cpu, ShieldAlert, Wifi, Sun, Moon } from "lucide-react";
import { useTheme } from "../ThemeContext";

interface TopAppBarProps {
  currentTab: string;
  setTab: (tab: string) => void;
  isRunningBacktest?: boolean;
  onRunBacktestClick?: () => void;
  onSettingsClick?: () => void;
  onSupportClick?: () => void;
  onNotificationClick?: () => void;
}

export default function TopAppBar({
  currentTab,
  setTab,
  isRunningBacktest = false,
  onRunBacktestClick,
  onSettingsClick,
  onSupportClick,
  onNotificationClick
}: TopAppBarProps) {
  const { theme, toggleTheme } = useTheme();
  // Format tab label for breadcrumb
  const formattedTabLabel = currentTab.charAt(0).toUpperCase() + currentTab.slice(1);

  return (
    <header className="fixed top-0 right-0 left-0 md:left-16 lg:left-[240px] h-16 border-b border-[#334155] bg-[#0f172a]/90 backdrop-blur-xl flex justify-between items-center px-4 sm:px-6 z-20 transition-all duration-300">
      {/* Title Context and Breadcrumbs */}
      <div className="flex items-center gap-2">
        <span className="text-xs font-mono text-[#94A3B8] hidden sm:inline uppercase tracking-wider select-none">
          Terminal /
        </span>
        <h2 className="text-sm sm:text-md font-bold text-white tracking-tight">
          {formattedTabLabel}
        </h2>
        {/* Real-time system pulse state */}
        <span className="flex h-2 w-2 relative ml-1 sm:ml-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#10B981] opacity-75"></span>
          <span className="relative inline-flex rounded-full h-2 w-2 bg-[#10B981]"></span>
        </span>
      </div>

      {/* Trailing Administrative Actions Widgets */}
      <div className="flex items-center gap-1.5 sm:gap-3">
        {/* Tactical Quick Run Triggers */}
        {currentTab !== "backtest" && onRunBacktestClick && (
          <button
            onClick={onRunBacktestClick}
            className="text-[11px] sm:text-xs font-semibold px-2.5 sm:px-4 py-1.5 border border-[#6366F1]/30 hover:border-[#6366F1] bg-[#6366F1]/10 text-white rounded-lg hover:bg-[#6366F1]/20 active:scale-95 transition-all text-center"
          >
            Run Backtest
          </button>
        )}

        <button
          onClick={() => setTab("signals")}
          className={`text-[10px] sm:text-xs font-mono uppercase tracking-wider px-2 sm:px-3 py-1.5 rounded-lg border hidden xs:flex items-center gap-1.5 transition-all duration-150 ${
            currentTab === "signals"
              ? "bg-[#22D3EE]/10 border-[#22D3EE] text-[#22D3EE]"
              : "bg-[#1e293b]/40 border-[#334155] text-[#94A3B8] hover:text-[#e2e8f0]"
          }`}
        >
          <Cpu className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Live Signal Feed</span>
          <span className="sm:hidden">Signals</span>
        </button>

        <div className="w-px h-6 bg-[#334155] mx-1 sm:mx-2 hidden sm:block"></div>

        {/* Global Connection state badge representation */}
        <div className="hidden lg:flex items-center gap-1 bg-[#10B981]/10 text-[#10B981] border border-[#10B981]/20 px-2 py-1 rounded-md text-[10px] font-mono tracking-wider select-none">
          <Wifi className="w-3 h-3 text-[#10B981]" />
          <span>CONNECTED</span>
        </div>

        {/* Theme Toggle */}
        <button
          onClick={toggleTheme}
          className="p-2 rounded-lg text-[#94A3B8] hover:text-[#e2e8f0] hover:bg-[#1e293b]/50 transition-colors"
          title="Toggle Theme"
        >
          {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
        </button>

        {/* Notifications and Alert center */}
        <button 
          onClick={onNotificationClick}
          className="p-2 rounded-lg text-[#94A3B8] hover:text-[#e2e8f0] hover:bg-[#1e293b]/50 relative transition-transform active:scale-95"
          title="System Notifications"
        >
          <Bell className="w-4 h-4" />
          <div className="absolute top-1 right-1 w-2 h-2 rounded-full bg-[#F87171] border-2 border-[#0F172A]"></div>
        </button>

        {/* Financial Officer User Account Avatar layout frame */}
        <div 
          onClick={onSettingsClick}
          className="w-8 h-8 rounded-full bg-[#1e293b] border border-[#334155] overflow-hidden flex items-center justify-center cursor-pointer shadow-md hover:border-[#22D3EE] transition-all relative group"
          title="Account Settings"
        >
          <img
            alt="User Profile"
            className="w-full h-full object-cover group-hover:scale-110 transition-transform"
            referrerPolicy="no-referrer"
            src="https://lh3.googleusercontent.com/aida-public/AB6AXuADODbzfV-so7r4CPZYXDSv1hCRefLDf7ZBRGZQWpVemdkcVVurI3KYMHIDKjKi6eB5wo2KwrMp7YNch8PvrsktmM8CX93WXWFLZDONavoRsYY_glqATm7gsm8iyBq7aSqILC4GAtS6XAGBSkGkOchPSfyLBfZCO_3O-dklUtUa6yLMnTX9Ia7Z4ranCkWgerv3iHcP36v29XDPoSGE0BAgmKofoVuLLgwdxfTeDIw_knMFjKnOfKboc-TD-jAhF_j5mR2hJSfUQEWf"
          />
        </div>
      </div>
    </header>
  );
}
