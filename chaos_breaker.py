import sys
import random
import importlib.util
from copy import deepcopy

# Load omni_stress_test utilities
spec = importlib.util.spec_from_file_location("omni", "builderr-template/omni_stress_test.py")
omni = importlib.util.module_from_spec(spec)
spec.loader.exec_module(omni)

def load_agent():
    spec = importlib.util.spec_from_file_location("agent", "agent.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def run_chaos():
    agent = load_agent()
    print("Beginning Extreme Chaos Loop (100 Scenarios)...\n")
    
    for i in range(1, 101):
        # 1. Generate base price curve
        scenario_type = random.choice([
            "flash_crash", "bear_grind", "whipsaw", "melt_up", "v_recovery"
        ])
        
        days = random.randint(100, 300)
        start = random.uniform(50, 500)
        
        if scenario_type == "flash_crash":
            prices = omni.generate_flash_crash(days, start, crash_day=random.randint(50, days-20), crash_pct=random.uniform(0.1, 0.6))
        elif scenario_type == "bear_grind":
            prices = omni.generate_slow_grind_down(days, start)
        elif scenario_type == "whipsaw":
            prices = omni.generate_whipsaw(days, start)
            # Add violent spikes
            for _ in range(5):
                idx = random.randint(1, days-1)
                prices[idx] = round(prices[idx-1] * random.uniform(0.7, 1.3), 2)
        elif scenario_type == "melt_up":
            prices = omni.generate_meltup(days, start)
        else:
            prices = omni.generate_v_recovery(days, start, bottom_day=random.randint(50, days-20))
            
        # 2. Build market state with noise
        ms = omni.build_market_state(prices)
        
        # 3. Inject Extreme Chaos
        for ticker in list(ms.keys()):
            # 10% chance a ticker just stops reporting
            if random.random() < 0.1:
                ms[ticker] = ms[ticker][:random.randint(5, len(ms[ticker])-1)]
                
            # 5% chance of corrupt data (zero/negative prices)
            if random.random() < 0.05 and ms[ticker]:
                idx = random.randint(0, len(ms[ticker])-1)
                ms[ticker][idx]["close"] = random.choice([-100, 0, "N/A", None])
                
            # Simulate 3x Leveraged ETFs imploding completely
            if ticker in ["TQQQ", "SOXL", "UPRO"] and random.random() < 0.2:
                for j in range(len(ms[ticker]) // 2, len(ms[ticker])):
                    if isinstance(ms[ticker][j]["close"], (int, float)) and ms[ticker][j]["close"] > 0:
                        ms[ticker][j]["close"] = round(ms[ticker][j]["close"] * 0.1, 2) # 90% drop
        
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
            
        # 5. Check Safety Rules strictly
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
            
        if i % 10 == 0:
            print(f"Passed {i}/100 chaos scenarios... (Latest: {scenario_type}, Lev={peak_g:.2f}x)")
            
    print("\n[VICTORY] Agent survived all 100 Extreme Chaos scenarios!")
    return True

if __name__ == "__main__":
    success = run_chaos()
    sys.exit(0 if success else 1)
