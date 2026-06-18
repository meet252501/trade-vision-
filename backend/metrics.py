"""
metrics.py — Trading Performance Metrics
==========================================
Calculates key quantitative metrics for strategy evaluation:
Calmar Ratio, Sharpe Ratio, Max Drawdown, Win Rate, Sortino, etc.
"""

import numpy as np


def calc_metrics(equity_curve: list[float], risk_free_rate: float = 0.0) -> dict:
    """
    Calculate comprehensive trading metrics from an equity curve.
    
    Args:
        equity_curve: List of daily portfolio values
        risk_free_rate: Annual risk-free rate (default 0%)
    
    Returns:
        dict with all computed metrics
    """
    eq = np.array(equity_curve, dtype=float)
    
    if len(eq) < 2:
        return _empty_metrics()
    
    returns = np.diff(eq) / eq[:-1]
    
    # ─── Total & Annualized Return ───
    total_return = (eq[-1] - eq[0]) / eq[0]
    n_years = len(eq) / 252
    ann_return = (1 + total_return) ** (1 / max(n_years, 0.01)) - 1
    
    # ─── Max Drawdown ───
    peak = np.maximum.accumulate(eq)
    drawdown = (eq - peak) / peak
    max_dd = abs(drawdown.min())
    
    # ─── Drawdown Series (for chart) ───
    drawdown_series = (drawdown * 100).tolist()
    
    # ─── Calmar Ratio ───
    calmar = ann_return / max_dd if max_dd > 0 else 0
    
    # ─── Sharpe Ratio (annualized) ───
    daily_rf = risk_free_rate / 252
    excess_returns = returns - daily_rf
    ann_vol = returns.std() * np.sqrt(252)
    sharpe = (ann_return - risk_free_rate) / ann_vol if ann_vol > 0 else 0
    
    # ─── Sortino Ratio ───
    downside_returns = returns[returns < 0]
    downside_std = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else 0
    sortino = (ann_return - risk_free_rate) / downside_std if downside_std > 0 else 0
    
    # ─── Win Rate ───
    wins = (returns > 0).sum()
    total_trades = len(returns)
    win_rate = wins / total_trades if total_trades > 0 else 0
    
    # ─── Profit Factor ───
    gross_profit = returns[returns > 0].sum()
    gross_loss = abs(returns[returns < 0].sum())
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
    
    # ─── Average Win / Average Loss ───
    avg_win = returns[returns > 0].mean() if len(returns[returns > 0]) > 0 else 0
    avg_loss = abs(returns[returns < 0].mean()) if len(returns[returns < 0]) > 0 else 0
    avg_win_loss = avg_win / avg_loss if avg_loss > 0 else 0
    
    # ─── Volatility ───
    daily_vol = returns.std()
    ann_volatility = daily_vol * np.sqrt(252)
    
    return {
        'total_return_pct':   round(total_return * 100, 2),
        'ann_return_pct':     round(ann_return * 100, 2),
        'max_drawdown_pct':   round(max_dd * 100, 2),
        'calmar_ratio':       round(calmar, 3),
        'sharpe_ratio':       round(sharpe, 3),
        'sortino_ratio':      round(sortino, 3),
        'win_rate_pct':       round(win_rate * 100, 2),
        'profit_factor':      round(profit_factor, 3),
        'avg_win_loss_ratio': round(avg_win_loss, 3),
        'volatility_pct':     round(ann_volatility * 100, 2),
        'total_trading_days': total_trades,
        'drawdown_series':    drawdown_series,
    }


def _empty_metrics() -> dict:
    """Return zeroed-out metrics when data is insufficient."""
    return {
        'total_return_pct':   0,
        'ann_return_pct':     0,
        'max_drawdown_pct':   0,
        'calmar_ratio':       0,
        'sharpe_ratio':       0,
        'sortino_ratio':      0,
        'win_rate_pct':       0,
        'profit_factor':      0,
        'avg_win_loss_ratio': 0,
        'volatility_pct':     0,
        'total_trading_days': 0,
        'drawdown_series':    [],
    }
