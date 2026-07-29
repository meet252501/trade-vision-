import sys
import random
import importlib.util

# Load omni_stress_test utilities
spec = importlib.util.spec_from_file_location("omni", "builderr-template/omni_stress_test.py")
omni = importlib.util.module_from_spec(spec)
spec.loader.exec_module(omni)

def load_agent():
    spec = importlib.util.spec_from_file_location("agent", "agent.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def run_ultimate_chaos():
    agent = load_agent()
    print("Beginning THE ULTIMATE CHAOS LOOP (10,000 Scenarios)...\n")
    
    for i in range(1, 10001):
        scenario_type = random.choice([
            "flash_crash", "bear_grind", "whipsaw", "melt_up", "v_recovery",
            "liquidity_blackhole", "sector_contagion", "liquidation_event", "dead_cat_bounce"
        ])
        
        days = random.randint(100, 300)
        start = random.uniform(0.1, 500) # Testing near-zero penny stock prices
        
        # Base Curve
        if scenario_type in ["flash_crash", "sector_contagion"]:
            prices = omni.generate_flash_crash(days, start, crash_day=random.randint(50, days-20), crash_pct=random.uniform(0.1, 0.7))
        elif scenario_type in ["bear_grind", "liquidation_event"]:
            prices = omni.generate_slow_grind_down(days, start)
        elif scenario_type in ["whipsaw", "liquidity_blackhole"]:
            prices = omni.generate_whipsaw(days, start)
        elif scenario_type == "dead_cat_bounce":
            prices = omni.generate_slow_grind_down(days, start)
            # Add violent dead cat bounces
            for _ in range(3):
                idx = random.randint(10, days-10)
                for j in range(idx, min(idx+5, days)):
                    prices[j] = round(prices[j-1] * random.uniform(1.05, 1.15), 2)
        elif scenario_type == "melt_up":
            prices = omni.generate_meltup(days, start)
        else:
            prices = omni.generate_v_recovery(days, start, bottom_day=random.randint(50, days-20))
            
        ms = omni.build_market_state(prices)
        
        # Inject Ultimate Pathologies
        for ticker in list(ms.keys()):
            # Liquidity Blackhole (Trading Halted, then gap down)
            if scenario_type == "liquidity_blackhole" and random.random() < 0.3:
                halt_day = random.randint(30, days - 10)
                halt_price = ms[ticker][halt_day]["close"]
                for j in range(halt_day, halt_day + random.randint(3, 10)):
                    if j < len(ms[ticker]): ms[ticker][j]["close"] = halt_price
                if halt_day + 10 < len(ms[ticker]):
                    if isinstance(ms[ticker][halt_day + 10]["close"], (int, float)):
                        ms[ticker][halt_day + 10]["close"] = round(halt_price * 0.7, 2) # 30% gap down
                    
            # Sector Contagion (Only specific tickers crash)
            if scenario_type == "sector_contagion":
                if ticker in ["QQQ", "XLK", "SMH", "NVDA", "AAPL", "MSFT", "TQQQ", "SOXL"]:
                    # Tech crashes, everything else is fine
                    pass 
                else:
                    # Overwrite non-tech with a smooth uptrend
                    ms[ticker] = omni.build_market_state(omni.generate_trending_up(days, start))[ticker]
            
            # Liquidation Event (Everything crashes, even Gold)
            if scenario_type == "liquidation_event":
                if random.random() < 0.5:
                    for j in range(len(ms[ticker])):
                        if isinstance(ms[ticker][j]["close"], (int, float)):
                            ms[ticker][j]["close"] = ms[ticker][j]["close"] * 0.99 # Everyone bleeds every day
                            
            # Random Corruptions
            if random.random() < 0.1: # Missing data
                ms[ticker] = ms[ticker][:random.randint(5, len(ms[ticker])-1)]
            if random.random() < 0.05 and ms[ticker]: # Zero or invalid prices
                idx = random.randint(0, len(ms[ticker])-1)
                ms[ticker][idx]["close"] = random.choice([-100, 0, "N/A", None])
            if ticker in ["TQQQ", "SOXL", "UPRO"] and random.random() < 0.2: # 3x implosions
                for j in range(len(ms[ticker]) // 2, len(ms[ticker])):
                    if isinstance(ms[ticker][j]["close"], (int, float)) and ms[ticker][j]["close"] > 0:
                        ms[ticker][j]["close"] = round(ms[ticker][j]["close"] * 0.1, 2)
        
        # Run
        try:
            res = omni.run_simulation(agent, ms, days_to_run=days-10)
            ret = res["total_return"] / 100.0
            max_dd = res["max_drawdown"] / 100.0
            trades = res["total_trades"]
            peak_g = res["peak_gross"]
            peak_c = res["peak_concentration"]
            errs = len(res["errors"])
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"[CRITICAL FAIL] Scenario {i} ({scenario_type}) caused a raw exception: {e}")
            return False
            
        failed = False
        reason = ""
        
        if errs > 0:
            failed = True; reason = f"{errs} Errors during run"
        elif peak_g > 1.50:
            failed = True; reason = f"Leverage limit breached: {peak_g}x"
        elif peak_c >= 0.30:
            failed = True; reason = f"Concentration limit breached: {peak_c*100}%"
        elif max_dd >= 0.50:
            failed = True; reason = f"Drawdown exceeded 50%: {max_dd*100}%"
            
        if failed:
            print(f"\n[FAIL] Scenario {i} ({scenario_type}) broke the bot!")
            print(f"  Reason: {reason}")
            print(f"  Stats: Ret={ret*100:.2f}%, MaxDD={max_dd*100:.2f}%, PeakLev={peak_g}x, PeakConc={peak_c*100:.2f}%")
            return False
            
        if i % 1000 == 0:
            print(f"Passed {i}/10000 scenarios... (Latest: {scenario_type}, Lev={peak_g:.2f}x)")
            
    print("\n[VICTORY] Agent survived all 10,000 Ultimate Chaos scenarios!")
    return True

if __name__ == "__main__":
    success = run_ultimate_chaos()
    sys.exit(0 if success else 1)
