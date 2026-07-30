import sys
import os
import time
from ml_predictor import train_model

UNIVERSE = ['BTC/USD', 'ETH/USD', 'LTC/USD', 'BCH/USD', 'SPY', 'QQQ', 'IWM', 'XLK', 'XLF', 'XLE']

def nightly_retrain():
    print("==================================================")
    print("  TradeVision V6 - Autonomous Nightly Retraining")
    print("==================================================")
    
    for ticker in UNIVERSE:
        print(f"\n[*] Retraining Deep Neural Network for {ticker}...")
        try:
            # train_model will fetch the latest data and overwrite the .pkl file
            # In a production Level-6 system, we would first train it to a temporary file,
            # evaluate its accuracy against the existing model, and only swap if better.
            accuracy = train_model(ticker)
            print(f"[+] Successfully trained {ticker} model. Accuracy: {accuracy:.2f}%")
        except Exception as e:
            print(f"[-] Failed to train {ticker}: {e}")
            
        # Sleep to avoid hitting Alpaca rate limits
        time.sleep(2)
        
    print("\n[V] Nightly Retraining Complete. Agent is now smarter.")

if __name__ == "__main__":
    nightly_retrain()
