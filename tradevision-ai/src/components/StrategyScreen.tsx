import React, { useState, useEffect } from "react";
import { Sparkles, HelpCircle, Save, Check, Lock, ShieldCheck, HelpCircle as HelpIcon, TrendingUp, RefreshCw, Layers } from "lucide-react";
import { StrategyType } from "../types";

export default function StrategyScreen() {
  const [selectedStrategy, setSelectedStrategy] = useState<StrategyType>("Dual Momentum");
  const [lookback, setLookback] = useState(63);
  const [topN, setTopN] = useState(3);
  const [maxPositionSize, setMaxPositionSize] = useState(30);
  const [smaFilter, setSmaFilter] = useState(true);
  const [universe, setUniverse] = useState<string[]>(["SPY", "QQQ", "IWM", "XLK", "XLF", "XLE", "XLV", "GLD"]);
  const [isSaved, setIsSaved] = useState(false);

  // Load custom strategy set from local storage on render
  useEffect(() => {
    const saved = localStorage.getItem("tradevision_strategy_config");
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        setSelectedStrategy(parsed.strategy || "Dual Momentum");
        setLookback(parsed.lookback || 63);
        setTopN(parsed.top_n || 3);
        setMaxPositionSize(parsed.max_pos_size || 30);
        setSmaFilter(parsed.sma_filter !== undefined ? parsed.sma_filter : true);
        setUniverse(parsed.tickers || ["SPY", "QQQ", "IWM", "XLK", "XLF", "XLE", "XLV", "GLD"]);
      } catch (err) {
        console.warn("Failed to load local strategy parameters:", err);
      }
    }
  }, []);

  const saveConfiguration = () => {
    const configObj = {
      strategy: selectedStrategy,
      lookback,
      top_n: topN,
      max_pos_size: maxPositionSize,
      sma_filter: smaFilter,
      leverage_cap: 1.5,
      tickers: universe
    };

    localStorage.setItem("tradevision_strategy_config", JSON.stringify(configObj));
    setIsSaved(true);
    setTimeout(() => {
      setIsSaved(false);
    }, 2500);
  };

  const handleStrategyChange = (strat: StrategyType) => {
    setSelectedStrategy(strat);
    // Autofill recommended core quantitative parameter shapes based on institutional presets
    if (strat === "SMA Crossover") {
      setLookback(50);
      setTopN(1);
      setMaxPositionSize(100);
      setSmaFilter(false);
    } else if (strat === "Volatility Target") {
      setLookback(20);
      setTopN(5);
      setMaxPositionSize(50);
      setSmaFilter(false);
    } else {
      setLookback(63);
      setTopN(3);
      setMaxPositionSize(30);
      setSmaFilter(true);
    }
  };

  const toggleUniverseAsset = (sym: string) => {
    if (universe.includes(sym)) {
      if (universe.length > 1) { // Prevent empty universe
        setUniverse(universe.filter((x) => x !== sym));
      }
    } else {
      setUniverse([...universe, sym]);
    }
  };

  const availableUniverseAssets = ["SPY", "QQQ", "IWM", "XLK", "XLF", "XLE", "XLV", "GLD", "TLT", "BTC-USD", "ETH-USD"];

  return (
    <div className="space-y-6">
      
      {/* Description header */}
      <div>
        <h3 className="text-xl font-bold text-white tracking-tight">Strategy Configuration</h3>
        <p className="text-xs text-[#94A3B8] font-sans mt-1">
          Configure algorithmic parameters, portfolio allocation limits, and active risk controls for live deployment.
        </p>
      </div>

      {/* Strategies Card Selectors */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        
        {/* Strategy Card 1 - Dual Momentum */}
        <div 
          onClick={() => handleStrategyChange("Dual Momentum")}
          className={`border rounded-xl p-5 cursor-pointer relative overflow-hidden transition-all duration-150 backdrop-blur-md ${
            selectedStrategy === "Dual Momentum"
              ? "bg-[#1e293b]/95 border-[#6366F1] shadow-[0_0_20px_rgba(99,102,241,0.15)] ring-1 ring-[#6366F1]"
              : "bg-[#1e293b]/40 border-[#334155] hover:bg-[#1e293b]/60 hover:border-[#464554]"
          }`}
        >
          {selectedStrategy === "Dual Momentum" && (
            <div className="absolute top-0 left-0 w-1.5 h-full bg-[#6366F1]"></div>
          )}
          <div className="flex items-center justify-between mb-4">
            <div className={`w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold ${selectedStrategy === "Dual Momentum" ? "bg-[#1e293b] text-[#6366F1] border border-[#6366F1]/30" : "bg-[#0b1326] text-[#94A3B8]"}`}>
              DM
            </div>
            <div className={`w-4 h-4 rounded-full border-2 flex items-center justify-center ${selectedStrategy === "Dual Momentum" ? "border-[#6366F1]" : "border-[#334155]"}`}>
              {selectedStrategy === "Dual Momentum" && <div className="w-1.5 h-1.5 bg-[#6366F1] rounded-full"></div>}
            </div>
          </div>
          <h4 className="text-sm font-bold text-white mb-1">Dual Momentum (Default)</h4>
          <p className="text-xs text-[#94A3B8] leading-relaxed line-clamp-2">
            Rotates capital between asset classes of positive momentum. Defensively transitions to Cash under SPY &lt; SMA-200.
          </p>
        </div>

        {/* Strategy Card 2 - SMA Crossover */}
        <div 
          onClick={() => handleStrategyChange("SMA Crossover")}
          className={`border rounded-xl p-5 cursor-pointer relative overflow-hidden transition-all duration-150 backdrop-blur-md ${
            selectedStrategy === "SMA Crossover"
              ? "bg-[#1e293b]/95 border-[#6366F1] shadow-[0_0_20px_rgba(99,102,241,0.15)] ring-1 ring-[#6366F1]"
              : "bg-[#1e293b]/40 border-[#334155] hover:bg-[#1e293b]/60 hover:border-[#464554]"
          }`}
        >
          {selectedStrategy === "SMA Crossover" && (
            <div className="absolute top-0 left-0 w-1.5 h-full bg-[#6366F1]"></div>
          )}
          <div className="flex items-center justify-between mb-4">
            <div className={`w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold ${selectedStrategy === "SMA Crossover" ? "bg-[#1e293b] text-[#6366F1] border border-[#6366F1]/30" : "bg-[#0b1326] text-[#94A3B8]"}`}>
              SC
            </div>
            <div className={`w-4 h-4 rounded-full border-2 flex items-center justify-center ${selectedStrategy === "SMA Crossover" ? "border-[#6366F1]" : "border-[#334155]"}`}>
              {selectedStrategy === "SMA Crossover" && <div className="w-1.5 h-1.5 bg-[#6366F1] rounded-full"></div>}
            </div>
          </div>
          <h4 className="text-sm font-bold text-white mb-1">SMA Crossover</h4>
          <p className="text-xs text-[#94A3B8] leading-relaxed line-clamp-2">
            Standard institutional trend-following strategy. Allocates during Golden Crosses, sells on Death Crosses.
          </p>
        </div>

        {/* Strategy Card 3 - Volatility Target */}
        <div 
          onClick={() => handleStrategyChange("Volatility Target")}
          className={`border rounded-xl p-5 cursor-pointer relative overflow-hidden transition-all duration-150 backdrop-blur-md ${
            selectedStrategy === "Volatility Target"
              ? "bg-[#1e293b]/95 border-[#6366F1] shadow-[0_0_20px_rgba(99,102,241,0.15)] ring-1 ring-[#6366F1]"
              : "bg-[#1e293b]/40 border-[#334155] hover:bg-[#1e293b]/60 hover:border-[#464554]"
          }`}
        >
          {selectedStrategy === "Volatility Target" && (
            <div className="absolute top-0 left-0 w-1.5 h-full bg-[#6366F1]"></div>
          )}
          <div className="flex items-center justify-between mb-4">
            <div className={`w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold ${selectedStrategy === "Volatility Target" ? "bg-[#1e293b] text-[#6366F1] border border-[#6366F1]/30" : "bg-[#0b1326] text-[#94A3B8]"}`}>
              VT
            </div>
            <div className={`w-4 h-4 rounded-full border-2 flex items-center justify-center ${selectedStrategy === "Volatility Target" ? "border-[#6366F1]" : "border-[#334155]"}`}>
              {selectedStrategy === "Volatility Target" && <div className="w-1.5 h-1.5 bg-[#6366F1] rounded-full"></div>}
            </div>
          </div>
          <h4 className="text-sm font-bold text-white mb-1">Volatility Target</h4>
          <p className="text-xs text-[#94A3B8] leading-relaxed line-clamp-2">
            Sizes active risk structures dynamically. Allocates capital inversely proportional to trailing twenty-day standard volatilities.
          </p>
        </div>

      </div>

      {/* Bento parameters tuning layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        
        {/* Core Sliders (Left spans 8 cols) */}
        <div className="lg:col-span-8 bg-[#1e293b]/85 border border-[#334155] rounded-xl p-5 flex flex-col justify-between backdrop-blur-md shadow-lg min-h-[300px]">
          <div className="pb-3 mb-6 border-b border-[#334155]">
            <h4 className="text-xs font-bold text-white uppercase tracking-wider font-mono">Strategy Core Parameters</h4>
          </div>

          <div className="space-y-6 flex-1 flex flex-col justify-around">
            
            {/* Slider 1 - Lookback */}
            <div>
              <div className="flex justify-between items-center mb-1.5">
                <label className="text-[10px] font-mono text-[#94A3B8] uppercase tracking-wider">Trailing Price Lookback</label>
                <span className="bg-[#6366F1]/10 border border-[#6366F1]/30 text-[#6366F1] px-2 py-0.5 rounded text-xs font-bold font-mono">
                  {lookback} Days
                </span>
              </div>
              <div className="relative pt-1">
                <input 
                  type="range"
                  min="21"
                  max="252"
                  value={lookback}
                  onChange={(e) => setLookback(Number(e.target.value))}
                  className="w-full accent-[#6366F1] h-1.5 bg-[#0b1326] rounded-lg cursor-pointer appearance-none outline-none"
                />
                <div className="flex justify-between text-[9px] text-[#94A3B8] font-mono mt-1">
                  <span>21 (1 Month)</span>
                  <span>126 (6 Months)</span>
                  <span>252 (1 Year)</span>
                </div>
              </div>
            </div>

            {/* Slider 2 - Top N Holdings */}
            <div>
              <div className="flex justify-between items-center mb-1.5">
                <label className="text-[10px] font-mono text-[#94A3B8] uppercase tracking-wider font-sans">Top N Selected Holdings</label>
                <span className="bg-[#6366F1]/10 border border-[#6366F1]/30 text-[#6366F1] px-2 py-0.5 rounded text-xs font-bold font-mono">
                  {topN} ETFs
                </span>
              </div>
              <div className="relative pt-1">
                <input 
                  type="range"
                  min="1"
                  max="10"
                  value={topN}
                  disabled={selectedStrategy === "SMA Crossover"}
                  onChange={(e) => setTopN(Number(e.target.value))}
                  className={`w-full accent-[#6366F1] h-1.5 bg-[#0b1326] rounded-lg cursor-pointer appearance-none outline-none ${selectedStrategy === "SMA Crossover" ? "opacity-30 cursor-not-allowed" : ""}`}
                />
                <div className="flex justify-between text-[9px] text-[#94A3B8] font-mono mt-1">
                  <span>1 Holding</span>
                  <span>5 holdings</span>
                  <span>10 Holdings (Full Universe)</span>
                </div>
              </div>
            </div>

            {/* Slider 3 - Max Position Size */}
            <div>
              <div className="flex justify-between items-center mb-1.5">
                <label className="text-[10px] font-mono text-[#94A3B8] uppercase tracking-wider">Maximum Asset Weight Cap</label>
                <span className="bg-[#6366F1]/10 border border-[#6366F1]/30 text-[#6366F1] px-2 py-0.5 rounded text-xs font-bold font-mono">
                  {maxPositionSize}%
                </span>
              </div>
              <div className="relative pt-1">
                <input 
                  type="range"
                  min="5"
                  max="100"
                  value={maxPositionSize}
                  disabled={selectedStrategy === "SMA Crossover"}
                  onChange={(e) => setMaxPositionSize(Number(e.target.value))}
                  className={`w-full accent-[#6366F1] h-1.5 bg-[#0b1326] rounded-lg cursor-pointer appearance-none outline-none ${selectedStrategy === "SMA Crossover" ? "opacity-30 cursor-not-allowed" : ""}`}
                />
                <div className="flex justify-between text-[9px] text-[#94A3B8] font-mono mt-1">
                  <span>5% (Highly Diversified)</span>
                  <span>30% Standard Limit</span>
                  <span>100% (Concentrated Longs)</span>
                </div>
              </div>
            </div>

          </div>
        </div>

        {/* Risk management & universe chips (Right spans 4 cols) */}
        <div className="lg:col-span-4 flex flex-col gap-4">
          
          {/* Risk controls panel */}
          <div className="bg-[#1e293b]/85 border border-[#334155] rounded-xl p-5 flex-1 backdrop-blur-md shadow-lg">
            <div className="pb-3 mb-4 border-b border-[#334155] flex justify-between items-center">
              <h4 className="text-xs font-bold text-white uppercase tracking-wider font-mono">Active Risk Safeguards</h4>
              <ShieldCheck className="w-4 h-4 text-[#94A3B8]" />
            </div>

            <div className="space-y-4">
              
              {/* Toggle 1 - SMA Filter */}
              <div className="flex justify-between items-center">
                <div>
                  <p className="text-xs font-bold text-[#e2e8f0]">SMA-200 Filter Toggle</p>
                  <p className="text-[9px] text-[#94A3B8] mt-0.5 leading-tight font-mono select-none uppercase">Risk-off cash liquidator</p>
                </div>
                <button 
                  onClick={() => setSmaFilter(!smaFilter)}
                  className={`w-10 h-5.5 rounded-full p-0.5 transition-colors focus:outline-none ${
                    smaFilter ? "bg-[#6366F1]" : "bg-[#0b1326] border border-[#334155]"
                  }`}
                >
                  <div className={`w-4.5 h-4.5 rounded-full bg-white transition-transform ${
                    smaFilter ? "translate-x-4.5 shadow-sm" : "translate-x-0"
                  }`}></div>
                </button>
              </div>

              {/* Toggle 2 - Leverage Cap (Locked) */}
              <div className="flex justify-between items-center opacity-75 select-none">
                <div>
                  <div className="flex items-center gap-1.5">
                    <p className="text-xs font-bold text-[#e2e8f0]">Leverage Cap Limit</p>
                    <Lock className="w-3 h-3 text-[#6366F1]" />
                  </div>
                  <p className="text-[9px] text-[#94A3B8] mt-0.5 leading-tight font-mono uppercase">1.5x portfolio mandate limit</p>
                </div>
                <div className="w-10 h-5.5 rounded-full p-0.5 bg-[#6366F1] cursor-not-allowed">
                  <div className="w-4.5 h-4.5 rounded-full bg-white translate-x-4.5 shadow-sm"></div>
                </div>
              </div>

            </div>
          </div>

          {/* Universe selection panel */}
          <div className="bg-[#1e293b]/85 border border-[#334155] rounded-xl p-5 backdrop-blur-md shadow-lg">
            <div className="pb-3 mb-3 border-b border-[#334155]">
              <h4 className="text-xs font-bold text-white uppercase tracking-wider font-mono">ETF Asset Universe Selection</h4>
            </div>

            <div className="flex flex-wrap gap-1.5 pt-2">
              {availableUniverseAssets.map((sym) => {
                const isSelected = universe.includes(sym);
                return (
                  <button
                    key={sym}
                    onClick={() => toggleUniverseAsset(sym)}
                    className={`px-3 py-1.5 rounded-full text-[10px] font-bold font-mono transition-all duration-150 ${
                      isSelected
                        ? "bg-[#6366F1]/10 text-[#6366F1] border border-[#6366F1]"
                        : "bg-[#0b1326]/60 text-[#94A3B8] border border-[#334155] hover:bg-[#1e293b] hover:text-[#e2e8f0]"
                    }`}
                  >
                    {sym}
                  </button>
                );
              })}
            </div>
          </div>

        </div>

      </div>

      {/* Bottom save actions triggers */}
      <div className="pt-4 border-t border-[#334155] flex justify-end">
        <button 
          onClick={saveConfiguration}
          className="w-full sm:w-auto px-8 py-3 bg-gradient-to-r from-[#6366F1] to-[#22D3EE] hover:opacity-95 text-white font-mono text-xs uppercase tracking-wider font-bold rounded-lg transition-transform active:scale-95 flex items-center justify-center gap-2 shadow-[0_0_20px_rgba(99,102,241,0.25)]"
        >
          {isSaved ? (
            <>
              <Check className="w-4 h-4 text-[#10B981]" />
              <span>SAVED SYSTEM PRESET!</span>
            </>
          ) : (
            <>
              <Save className="w-4 h-4" />
              <span>SAVE CONFIGURATION Presets</span>
            </>
          )}
        </button>
      </div>

    </div>
  );
}
