"""
TradeVision AI - Trade History Logger
Saves every BUY/SELL to a CSV file for review.
"""
import csv
import os
import datetime

LOG_FILE = os.path.join(os.path.dirname(__file__), 'trade_history.csv')

def _ensure_file():
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'side', 'ticker', 'quantity', 'price', 'equity_after', 'reason'])

def log_trade(side, ticker, quantity, price=0.0, equity_after=0.0, reason=''):
    _ensure_file()
    with open(LOG_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.datetime.now().isoformat(),
            side,
            ticker,
            f"{quantity:.4f}",
            f"{price:.4f}",
            f"{equity_after:.2f}",
            reason
        ])

def log_equity_snapshot(equity, cash, positions_count):
    """Log periodic equity snapshots for the equity curve."""
    snap_file = os.path.join(os.path.dirname(__file__), 'equity_curve.csv')
    if not os.path.exists(snap_file):
        with open(snap_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'equity', 'cash', 'positions'])
    with open(snap_file, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.datetime.now().isoformat(),
            f"{equity:.2f}",
            f"{cash:.2f}",
            positions_count
        ])

def get_trade_history(limit=50):
    _ensure_file()
    trades = []
    with open(LOG_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            trades.append(row)
    return trades[-limit:]

def get_equity_curve():
    snap_file = os.path.join(os.path.dirname(__file__), 'equity_curve.csv')
    if not os.path.exists(snap_file):
        return []
    points = []
    with open(snap_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            points.append(row)
    return points
