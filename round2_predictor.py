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

def run_prediction():
    agent = load_agent()
    print("=====================================================")
    print("  ROUND 2 MONTE CARLO PREDICTOR (38 DAYS LEFT)")
    print("=====================================================")
    
    simulations = 1000
    days_left = 38
    history_needed = 150 # Need at least 100 for SMA_LONG
    total_days = history_needed + days_left
    
    returns = []
    
    for i in range(simulations):
        scenario_type = random.choices(
            ["bull", "bear", "flat_whipsaw", "flash_crash", "melt_up"],
            weights=[0.4, 0.1, 0.3, 0.05, 0.15],
            k=1
        )[0]
        
        start = random.uniform(50, 500)
        
        if scenario_type == "bull":
            prices = omni.generate_trending_up(total_days, start)
        elif scenario_type == "bear":
            prices = omni.generate_slow_grind_down(total_days, start)
        elif scenario_type == "flat_whipsaw":
            prices = omni.generate_whipsaw(total_days, start)
        elif scenario_type == "flash_crash":
            # Crash in the last 38 days
            crash_day = total_days - random.randint(5, 30)
            prices = omni.generate_flash_crash(total_days, start, crash_day=crash_day, crash_pct=random.uniform(0.1, 0.3))
        else:
            prices = omni.generate_meltup(total_days, start)
            
        ms = omni.build_market_state(prices)
        
        res = omni.run_simulation(agent, ms, days_to_run=days_left, start_cash=100000)
        ret = res["total_return"]
        returns.append(ret)
        
    avg_ret = sum(returns) / len(returns)
    max_ret = max(returns)
    min_ret = min(returns)
    
    # Probability of beating Arnav's current +4.23%
    prob_beat_5 = sum(1 for r in returns if r > 5.0) / len(returns) * 100
    prob_positive = sum(1 for r in returns if r > 0.0) / len(returns) * 100
    
    print(f"\nResults of {simulations} Monte Carlo Simulations over {days_left} Days:")
    print(f"-----------------------------------------------------")
    print(f"Average Expected Return:  +{avg_ret:.2f}%")
    print(f"Best-Case Scenario:       +{max_ret:.2f}% (Melt-up)")
    print(f"Worst-Case Scenario:      {min_ret:.2f}% (Sudden Crash)")
    print(f"-----------------------------------------------------")
    print(f"Win Probability (> 0%):   {prob_positive:.1f}%")
    print(f"Prob. of > +5.0% Return:  {prob_beat_5:.1f}%")
    print("=====================================================")

if __name__ == "__main__":
    run_prediction()
