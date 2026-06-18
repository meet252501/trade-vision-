import React from "react";
import { LayoutDashboard, BarChart3, Brain, Radio, Settings, HelpCircle, Sparkles } from "lucide-react";

interface SideNavBarProps {
  currentTab: string;
  setTab: (tab: string) => void;
  onSettingsClick?: () => void;
  onSupportClick?: () => void;
}

export default function SideNavBar({ currentTab, setTab, onSettingsClick, onSupportClick }: SideNavBarProps) {
  const tabs = [
    { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
    { id: "backtest", label: "Backtest", icon: BarChart3 },
    { id: "strategy", label: "Strategy", icon: Brain },
    { id: "signals", label: "Signals", icon: Radio },
  ];

  return (
    <>
      {/* Structural Desktop/Tablet Side Bar Navigation */}
      <nav className="fixed left-0 top-0 h-full w-16 lg:w-[240px] border-r border-[#334155] bg-[#0b1326] flex flex-col justify-between py-6 z-30 hidden md:flex transition-all duration-300">
        <div>
          {/* Executive Header Branding Context */}
          <div className="px-3 lg:px-6 mb-8 flex items-center justify-center lg:justify-start gap-3 overflow-hidden">
            <div className="w-8 h-8 shrink-0 rounded-lg bg-gradient-to-tr from-[#6366F1] to-[#22D3EE] flex items-center justify-center font-bold text-white text-md shadow-[0_0_12px_rgba(99,102,241,0.4)] hover:rotate-12 transition-transform select-none">
              TV
            </div>
            <div className="lg:block hidden animate-fade-in whitespace-nowrap">
              <h1 className="text-lg font-bold text-transparent bg-clip-text bg-gradient-to-r from-[#e2e8f0] to-[#22D3EE] tracking-tight">
                TradeVision AI
              </h1>
              <p className="font-mono text-[9px] uppercase tracking-wider text-[#94A3B8]">
                Institutional Terminal
              </p>
            </div>
          </div>

          {/* Primary Nav Navigation Items */}
          <div className="flex flex-col space-y-1.5 px-2 lg:px-3">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = currentTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setTab(tab.id)}
                  className={`w-full flex items-center justify-center lg:justify-start gap-3 px-3 lg:px-4 py-3 rounded-lg text-sm font-medium transition-all duration-150 relative ${
                    isActive
                      ? "text-white bg-[#1e293b] border-l-4 border-[#6366F1] shadow-[0_4px_12px_rgba(99,102,241,0.05)]"
                      : "text-[#94A3B8] hover:text-[#e2e8f0] hover:bg-[#1e293b]/50"
                  }`}
                  title={tab.label}
                >
                  <Icon className={`w-4 h-4 shrink-0 transition-transform duration-200 ${isActive ? "text-[#6366F1] scale-110" : ""}`} />
                  <span className="lg:block hidden transition-opacity duration-200">{tab.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Footer actions and configuration links */}
        <div className="px-2 lg:px-4">
          {/* Institutional Status Card folded on Tablet */}
          <div className="hidden lg:block bg-[#1e293b]/80 border border-[#334155] rounded-xl p-4 mb-4 text-center shadow-lg relative overflow-hidden group">
            <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-bl from-[#22D3EE]/10 to-transparent rounded-full blur-xl group-hover:scale-125 transition-transform"></div>
            <div className="flex justify-center mb-1">
              <Sparkles className="w-5 h-5 text-[#22D3EE] animate-pulse" />
            </div>
            <h4 className="text-xs font-bold text-[#e2e8f0] mb-1">Pro Terminal Active</h4>
            <p className="text-[10px] text-[#94A3B8] line-clamp-2 leading-relaxed">
              Algorithmic execution, risk mandates, and low-latency pricing enabled.
            </p>
          </div>

          {/* Tablet Mini Pro Badge */}
          <div className="block lg:hidden flex justify-center mb-4 group relative cursor-help">
            <div className="w-8 h-8 rounded-lg bg-[#1e293b] border border-[#334155] flex items-center justify-center text-[#22D3EE] shadow-md hover:border-[#22D3EE] transition-all">
              <Sparkles className="w-4 h-4 text-[#22D3EE] animate-pulse" />
            </div>
          </div>

          <div className="flex flex-col space-y-1">
            <button 
              onClick={onSettingsClick}
              className="flex items-center justify-center lg:justify-start gap-3 px-3 lg:px-4 py-2.5 rounded-lg text-xs font-medium text-[#94A3B8] hover:text-[#e2e8f0] hover:bg-[#1e293b]/50 text-left w-full transition-colors"
              title="Settings"
            >
              <Settings className="w-4 h-4 shrink-0" />
              <span className="lg:block hidden">Settings</span>
            </button>
            <button 
              onClick={onSupportClick}
              className="flex items-center justify-center lg:justify-start gap-3 px-3 lg:px-4 py-2.5 rounded-lg text-xs font-medium text-[#94A3B8] hover:text-[#e2e8f0] hover:bg-[#1e293b]/50 text-left w-full transition-colors"
              title="Support Terminal"
            >
              <HelpCircle className="w-4 h-4 shrink-0" />
              <span className="lg:block hidden">Support</span>
            </button>
          </div>
        </div>
      </nav>

      {/* Structural Mobile Navigation Bottom Bar Utility */}
      <nav className="fixed bottom-0 left-0 right-0 h-16 border-t border-[#334155] bg-[#0b1326]/95 backdrop-blur-md flex justify-around items-center z-30 md:hidden pb-safe">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = currentTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setTab(tab.id)}
              className={`flex flex-col items-center justify-center w-16 h-full transition-all duration-150 ${
                isActive ? "text-[#6366F1]" : "text-[#94A3B8]"
              }`}
            >
              <Icon className="w-5 h-5" />
              <span className="text-[10px] mt-1 font-sans font-medium">{tab.label}</span>
              {isActive && (
                <div className="absolute bottom-1 w-1 h-1 rounded-full bg-[#6366F1] shadow-[0_0_8px_#6366F1]"></div>
              )}
            </button>
          );
        })}
      </nav>
    </>
  );
}
