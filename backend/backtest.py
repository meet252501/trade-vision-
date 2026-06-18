"""
backtest.py — Backtesting Engine
==================================
Simulates trading over historical data by:
1. Building daily market_state snapshots
2. Calling the strategy's decide() function each day
3. Executing orders and tracking equity curve + trades
"""

import numpy as np
from data import fetch_prices_as_df
from strategies.momentum import decide as momentum_decide
from strategies.sma_crossover import decide as sma_decide
from strategies.vol_target import decide as vol_decide


STRATEGY_MAP = {
    'momentum':     momentum_decide,
    'sma_crossover': sma_decide,
    'vol_target':   vol_decide,
}


def run_backtest(prices_raw: dict, initial_cash: float = 100000,
                 strategy: str = 'momentum', tickers: list = None,
                 start_date: str = None, end_date: str = None) -> dict:
    """
    Run a full backtest simulation.
    
    Args:
        prices_raw: dict of {ticker: list of bar dicts} from data.py
        initial_cash: Starting portfolio value
        strategy: Strategy name key
        tickers: List of tickers (for fetching if prices_raw empty)
        start_date: Backtest start date
        end_date: Backtest end date
    
    Returns:
        dict with equity_curve, trades, daily_dates, drawdown_series
    """
    decide_fn = STRATEGY_MAP.get(strategy, momentum_decide)
    
    # ─── Build aligned date-indexed data ───
    # Collect all dates across tickers
    all_dates = set()
    ticker_bars = {}
    
    for ticker, bars in prices_raw.items():
        if isinstance(bars, dict) and 'error' in bars:
            continue
        ticker_bars[ticker] = {b['ts']: b for b in bars}
        all_dates.update(b['ts'] for b in bars)
    
    if not all_dates:
        return _empty_result()
    
    sorted_dates = sorted(all_dates)
    
    # ─── Simulation State ───
    cash = initial_cash
    positions = {}     # {ticker: {'quantity': int, 'avg_price': float}}
    equity_curve = []
    trades = []
    daily_dates = []
    
    # ─── Iterate through each trading day ───
    for day_idx, date in enumerate(sorted_dates):
        # Build market_state: all bars up to this date for each ticker
        market_state = {}
        last_prices = {}
        
        for ticker, bars_by_date in ticker_bars.items():
            # Collect all bars up to current date
            historical_bars = []
            for d in sorted_dates[:day_idx + 1]:
                if d in bars_by_date:
                    historical_bars.append(bars_by_date[d])
            
            if historical_bars:
                market_state[ticker] = historical_bars
                last_prices[ticker] = historical_bars[-1]['close']
        
        # Build portfolio_state
        position_list = [
            {'ticker': t, 'quantity': p['quantity'], 'avg_price': p['avg_price']}
            for t, p in positions.items()
        ]
        portfolio_state = {
            'positions': position_list,
            'last_prices': last_prices,
        }
        
        # ─── Call strategy's decide() function ───
        try:
            orders = decide_fn(market_state, portfolio_state, cash)
        except Exception:
            orders = []
        
        # ─── Execute orders ───
        for order in orders:
            ticker = order.get('ticker', '')
            side = order.get('side', '')
            qty = order.get('quantity', 0)
            price = last_prices.get(ticker, 0)
            
            if price <= 0 or qty <= 0:
                continue
            
            if side == 'buy':
                cost = qty * price
                if cost <= cash:
                    cash -= cost
                    if ticker in positions:
                        # Average up
                        old = positions[ticker]
                        total_qty = old['quantity'] + qty
                        avg = (old['quantity'] * old['avg_price'] + cost) / total_qty
                        positions[ticker] = {'quantity': total_qty, 'avg_price': avg}
                    else:
                        positions[ticker] = {'quantity': qty, 'avg_price': price}
                    
                    trades.append({
                        'date': date,
                        'ticker': ticker,
                        'side': 'buy',
                        'qty': qty,
                        'price': round(price, 2),
                        'value': round(cost, 2),
                    })
            
            elif side == 'sell':
                if ticker in positions:
                    actual_qty = min(qty, positions[ticker]['quantity'])
                    revenue = actual_qty * price
                    cash += revenue
                    
                    pnl = (price - positions[ticker]['avg_price']) * actual_qty
                    
                    positions[ticker]['quantity'] -= actual_qty
                    if positions[ticker]['quantity'] <= 0:
                        del positions[ticker]
                    
                    trades.append({
                        'date': date,
                        'ticker': ticker,
                        'side': 'sell',
                        'qty': actual_qty,
                        'price': round(price, 2),
                        'value': round(revenue, 2),
                        'pnl': round(pnl, 2),
                    })
        
        # ─── Calculate portfolio value ───
        portfolio_value = cash
        for ticker, pos in positions.items():
            portfolio_value += pos['quantity'] * last_prices.get(ticker, 0)
        
        equity_curve.append(round(portfolio_value, 2))
        daily_dates.append(date)
    
    # ─── Compute drawdown series ───
    eq = np.array(equity_curve, dtype=float)
    if len(eq) > 0:
        peak = np.maximum.accumulate(eq)
        drawdown = ((eq - peak) / peak * 100).tolist()
    else:
        drawdown = []
    
    return {
        'equity_curve': equity_curve,
        'trades': trades,
        'dates': daily_dates,
        'drawdown_series': [round(d, 2) for d in drawdown],
        'final_value': equity_curve[-1] if equity_curve else initial_cash,
        'total_trades': len(trades),
    }


def _empty_result() -> dict:
    """Return empty backtest result when no data available."""
    return {
        'equity_curve': [],
        'trades': [],
        'dates': [],
        'drawdown_series': [],
        'final_value': 0,
        'total_trades': 0,
    }
