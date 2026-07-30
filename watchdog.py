"""
TradeVision AI - Auto-Restart Watchdog
Monitors the live agent and auto-restarts if it crashes.
Run this instead of run_live.py directly.
"""
import subprocess
import sys
import time
import datetime

AGENT_CMD = [sys.executable, '-u', 'backend/run_live.py', '--target', '5000']
MAX_RESTARTS = 50
RESTART_DELAY = 10  # seconds

def run_watchdog():
    restart_count = 0
    
    print("=" * 60)
    print("  TradeVision AI - WATCHDOG ACTIVE")
    print("=" * 60)
    print(f"  Max restarts: {MAX_RESTARTS}")
    print(f"  Restart delay: {RESTART_DELAY}s")
    print("=" * 60)
    
    while restart_count < MAX_RESTARTS:
        ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"\n[{ts}] Starting agent (attempt #{restart_count + 1})...")
        
        try:
            process = subprocess.run(
                AGENT_CMD,
                cwd='.',
                timeout=None  # Run forever until crash or target hit
            )
            
            if process.returncode == 0:
                print(f"\n[WATCHDOG] Agent exited cleanly (target likely reached!). Stopping.")
                break
            else:
                restart_count += 1
                ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f"\n[{ts}] [WATCHDOG] Agent crashed with code {process.returncode}. Restart #{restart_count} in {RESTART_DELAY}s...")
                time.sleep(RESTART_DELAY)
                
        except KeyboardInterrupt:
            print("\n[WATCHDOG] Manual shutdown. Goodbye!")
            break
        except Exception as e:
            restart_count += 1
            ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"\n[{ts}] [WATCHDOG] Exception: {e}. Restart #{restart_count} in {RESTART_DELAY}s...")
            time.sleep(RESTART_DELAY)
    
    if restart_count >= MAX_RESTARTS:
        print(f"\n[WATCHDOG] Max restarts ({MAX_RESTARTS}) reached. Stopping for safety.")

if __name__ == '__main__':
    run_watchdog()
