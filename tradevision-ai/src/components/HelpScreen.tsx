import React from "react";
import { BookOpen, Layers, Activity, TrendingUp, BarChart2, ShieldAlert, Cpu, Eye } from "lucide-react";

export default function HelpScreen() {
  const sections = [
    {
      title: "Dashboard & Control Center",
      icon: <Activity className="w-5 h-5 text-[#22D3EE]" />,
      desc: "The nerve center of the terminal. Here you can start/stop the autonomous Python agent, set its target profit, and monitor your high-level equity curve.",
      bullets: [
        "Autonomous Agent: Toggles the background Python process.",
        "Target Profit: The absolute dollar amount at which the agent will automatically halt trading.",
        "Live Portfolio: Mirrors your actual Alpaca paper trading balances."
      ]
    },
    {
      title: "Trade Log",
      icon: <Layers className="w-5 h-5 text-[#6366F1]" />,
      desc: "A raw, unfiltered feed of every single execution the agent makes through the Alpaca API.",
      bullets: [
        "Tracks Fill Price, Quantity, and timestamps.",
        "Shows both live orders and backtest-simulated orders depending on your mode."
      ]
    },
    {
      title: "Signals Engine",
      icon: <Cpu className="w-5 h-5 text-[#10B981]" />,
      desc: "Provides a transparent look into the agent's math. Shows exactly which asset it has the highest conviction on right now.",
      bullets: [
        "Driven by multi-timeframe momentum arrays (Fast, Med, Slow).",
        "Updates instantly based on live API ticks."
      ]
    },
    {
      title: "Strategy Builder",
      icon: <TrendingUp className="w-5 h-5 text-[#F59E0B]" />,
      desc: "The rules engine. Configure the logic that the Python agent follows.",
      bullets: [
        "Universe Selection: Choose which ETFs the agent is allowed to scan.",
        "SMA-200 Filter: A risk-off toggle. If SPY drops below its 200-day moving average, the agent liquidates everything to cash."
      ]
    },
    {
      title: "AI Trading Lab (Machine Learning)",
      icon: <Eye className="w-5 h-5 text-[#D946EF]" />,
      desc: "Runs a Random Forest Classifier locally to predict tomorrow's candlestick (Up or Down).",
      bullets: [
        "Consumes historical prices and technical indicators (RSI, MACD) to generate features.",
        "Purely informational—the live agent uses momentum, not this ML model, to execute."
      ]
    },
    {
      title: "Risk Heatmap",
      icon: <ShieldAlert className="w-5 h-5 text-[#EF4444]" />,
      desc: "Analyzes asset correlations. You want to avoid holding highly correlated assets (score close to 1.0) to maintain diversification.",
      bullets: [
        "Computes a live correlation matrix across the entire ETF universe.",
        "Calculates annualized volatility to spot danger zones."
      ]
    }
  ];

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-10">
      <div className="bg-[#1e293b]/80 border border-[#334155] rounded-xl p-8 backdrop-blur-md shadow-lg relative overflow-hidden">
        <div className="absolute -top-24 -right-24 w-64 h-64 bg-[#6366F1]/10 rounded-full blur-3xl pointer-events-none"></div>
        <div className="flex items-center gap-3 mb-3">
          <BookOpen className="w-8 h-8 text-[#6366F1]" />
          <h1 className="text-3xl font-extrabold text-white tracking-tight">Terminal Documentation</h1>
        </div>
        <p className="text-[#94A3B8] font-mono text-sm max-w-2xl leading-relaxed">
          Welcome to TradeVision V5. This institutional-grade quantitative platform is designed to operate autonomously. 
          Review the modules below to understand how the system derives alpha and executes trades.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {sections.map((sec, idx) => (
          <div key={idx} className="bg-[#1e293b]/50 border border-[#334155]/60 hover:border-[#6366F1]/40 transition-colors rounded-xl p-6 shadow-md group">
            <div className="flex items-center gap-3 mb-4 border-b border-[#334155]/60 pb-4">
              <div className="p-2 bg-[#0b1326] rounded-lg group-hover:scale-110 transition-transform">
                {sec.icon}
              </div>
              <h3 className="text-lg font-bold text-white tracking-tight">{sec.title}</h3>
            </div>
            
            <p className="text-xs text-[#e2e8f0] font-sans leading-relaxed mb-4">
              {sec.desc}
            </p>
            
            <ul className="space-y-2">
              {sec.bullets.map((bullet, i) => (
                <li key={i} className="flex items-start gap-2">
                  <div className="w-1 h-1 rounded-full bg-[#6366F1] mt-1.5 flex-shrink-0"></div>
                  <span className="text-[11px] text-[#94A3B8] font-mono leading-relaxed">{bullet}</span>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  );
}
