# omni_bot/omni_backtest.py
import yfinance as yf
import numpy as np
from config import ALL_ASSETS, BB_PERIOD, SPREAD_COSTS, DEFAULT_SPREAD
from master_agent import decide, reset_state
import time

def run_backtest(start_date=None, end_date=None, period=None, interval="1d", leverage=1.0, initial_cash=10000.0, label="RESULTS"):
    reset_state()  # Clear state between runs
    if start_date and end_date:
        print(f"Downloading data for {len(ALL_ASSETS)} assets ({start_date} to {end_date}, {interval} intervals)...")
        data = yf.download(ALL_ASSETS, start=start_date, end=end_date, interval=interval)
    else:
        print(f"Downloading data for {len(ALL_ASSETS)} assets (last {period}, {interval} intervals)...")
        data = yf.download(ALL_ASSETS, period=period, interval=interval)
        
    # Reformat for the agent (now includes volume!)
    history = {}
    for ticker in ALL_ASSETS:
        close_series = data['Close'][ticker].dropna()
        if len(close_series) == 0:
            print(f"Warning: No data for {ticker}")
            continue
        
        # Try to get volume data too
        vol_series = None
        try:
            vol_series = data['Volume'][ticker]
        except (KeyError, TypeError):
            pass
        
        bars = []
        for i, val in enumerate(close_series.values):
            bar = {'close': float(val)}
            if vol_series is not None and i < len(vol_series):
                v = vol_series.values[i]
                if not np.isnan(v):
                    bar['volume'] = float(v)
            bars.append(bar)
        
        history[ticker] = bars
        
    cash = initial_cash
    tradeable_equity = cash * leverage 
    
    portfolio_state = {'positions': [], 'last_prices': {}}
    market_state = {}
    
    print(f"\n[OMNI-BOT v3.0] Starting Balance: ${cash:,.2f} (Buying Power: ${tradeable_equity:,.2f})")
    
    winning_trades = 0
    losing_trades = 0
    total_spread_paid = 0.0
    
    # Drawdown tracking
    equity_curve = []
    peak_equity = initial_cash
    max_drawdown = 0.0
    daily_returns = []
    prev_equity = initial_cash
    
    # We must find the common denominator of steps
    min_steps = min(len(history[t]) for t in history)
    total_steps = min_steps
    start_step = BB_PERIOD + 1 # Need enough data for indicator warm-up
    
    start_time = time.time()
    
    for step in range(start_step, total_steps):
        # Calculate total equity for sizing
        current_eq = tradeable_equity / leverage
        for p in portfolio_state['positions']:
            val = p['quantity'] * portfolio_state['last_prices'].get(p['ticker'], 0) / leverage
            if p.get('is_short', False):
                current_eq -= val  # Short positions are liabilities
            else:
                current_eq += val  # Long positions are assets
                
        portfolio_state['total_equity'] = current_eq * leverage
        portfolio_state['real_equity'] = current_eq  # Un-leveraged equity for circuit breaker
        
        # Track equity curve and drawdown
        equity_curve.append(current_eq)
        if current_eq > peak_equity:
            peak_equity = current_eq
        current_dd = 1 - (current_eq / peak_equity) if peak_equity > 0 else 0
        max_drawdown = max(max_drawdown, current_dd)
        
        # Track daily returns for Sharpe Ratio
        if prev_equity > 0:
            daily_ret = (current_eq / prev_equity) - 1
            daily_returns.append(daily_ret)
        prev_equity = current_eq
        
        # Build market state up to this step
        for ticker in history:
            market_state[ticker] = history[ticker][:step]
            portfolio_state['last_prices'][ticker] = history[ticker][step-1]['close']
            
        # The Omni-Bot v2.0 decides
        orders = decide(market_state, portfolio_state, tradeable_equity)
        
        # Process orders (with spread costs!)
        for o in orders:
            t = o['ticker']
            price = portfolio_state['last_prices'][t]
            qty = o['quantity']
            spread = SPREAD_COSTS.get(t, DEFAULT_SPREAD)
            
            if o['side'] == 'buy':
                # Apply spread: You buy at a slightly HIGHER price
                effective_price = price * (1 + spread)
                cost = qty * effective_price
                total_spread_paid += qty * price * spread
                
                if tradeable_equity >= cost:
                    tradeable_equity -= cost
                    existing = next((p for p in portfolio_state['positions'] if p['ticker'] == t), None)
                    if existing:
                        total_qty = existing['quantity'] + qty
                        existing['entry_price'] = ((existing['entry_price'] * existing['quantity']) + (effective_price * qty)) / total_qty
                        existing['quantity'] = total_qty
                    else:
                        portfolio_state['positions'].append({'ticker': t, 'quantity': qty, 'entry_price': effective_price, 'entry_step': step})
            
            elif o['side'] == 'short':
                # Short selling: You sell at a slightly LOWER price
                effective_price = price * (1 - spread)
                proceeds = qty * effective_price
                total_spread_paid += qty * price * spread
                
                # For simplicity, track shorts as negative-direction positions
                portfolio_state['positions'].append({
                    'ticker': t, 'quantity': qty, 
                    'entry_price': effective_price, 'is_short': True, 'entry_step': step
                })
                tradeable_equity += proceeds  # You receive cash from the short
                        
            elif o['side'] in ['sell', 'cover', 'sell_half', 'cover_half']:
                existing = next((p for p in portfolio_state['positions'] if p['ticker'] == t), None)
                if existing and existing['quantity'] >= qty:
                    # Apply spread
                    if existing.get('is_short', False):
                        # Closing a short position means BUYING it back
                        # Spread: You buy back at a slightly HIGHER price
                        effective_price = price * (1 + spread)
                        cost_to_cover = qty * effective_price
                        tradeable_equity -= cost_to_cover
                        total_spread_paid += qty * price * spread
                        
                        trade_profit = (existing['entry_price'] - effective_price) * qty
                    else:
                        # Selling a long position
                        # Spread: You sell at a slightly LOWER price
                        effective_price = price * (1 - spread)
                        proceeds = qty * effective_price
                        tradeable_equity += proceeds
                        total_spread_paid += qty * price * spread
                        
                        trade_profit = (effective_price - existing['entry_price']) * qty
                        
                    if trade_profit > 0:
                        winning_trades += 1
                    else:
                        losing_trades += 1
                        
                    # Handle partial exits
                    if o['side'] in ['sell_half', 'cover_half']:
                        existing['quantity'] -= qty
                    else:
                        # Full exit
                        portfolio_state['positions'].remove(existing)
                        if 'best_prices' in portfolio_state and t in portfolio_state['best_prices']:
                            del portfolio_state['best_prices'][t]
                        if 'high_water_marks' in portfolio_state and t in portfolio_state['high_water_marks']:
                            del portfolio_state['high_water_marks'][t]
    
    end_time = time.time()
    
    # Calculate Final Equity
    current_equity = tradeable_equity / leverage
    for p in portfolio_state['positions']:
        val = p['quantity'] * portfolio_state['last_prices'][p['ticker']] / leverage
        if p.get('is_short', False):
            current_equity -= val
        else:
            current_equity += val
    profit = current_equity - initial_cash
    total_trades = winning_trades + losing_trades
    win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
    
    # Calculate Sharpe Ratio (annualized)
    if len(daily_returns) > 1:
        avg_return = np.mean(daily_returns)
        std_return = np.std(daily_returns)
        sharpe = (avg_return / std_return) * np.sqrt(252) if std_return > 0 else 0
    else:
        sharpe = 0
    
    # Calculate Return %
    return_pct = (profit / initial_cash) * 100
    
    print("\n" + "="*50)
    print(f"  {label}")
    print("="*50)
    print(f"  Ending Balance:    ${current_equity:,.2f}")
    if start_date and end_date:
        print(f"  Total Profit:      ${profit:,.2f} ({start_date} to {end_date})")
    else:
        print(f"  Total Profit:      ${profit:,.2f} (in {period})")
    print(f"  Return:            {return_pct:+.2f}%")
    print(f"  Win Rate:          {win_rate:.1f}% ({winning_trades}W / {losing_trades}L)")
    print(f"  Sharpe Ratio:      {sharpe:.2f}")
    print(f"  Max Drawdown:      {max_drawdown*100:.2f}%")
    print(f"  Spread Costs Paid: ${total_spread_paid:,.2f}")
    print(f"  Sim Time:          {(end_time - start_time):.2f}s")
    print("  Positions Held at End:")
    if not portfolio_state['positions']:
        print("   - None (All flat in cash)")
    else:
        for p in portfolio_state['positions']:
            t = p['ticker']
            price = portfolio_state['last_prices'][t]
            profit_pct = (price / p['entry_price']) - 1
            direction = "SHORT" if p.get('is_short', False) else "LONG"
            print(f"   - {t} ({direction}): {p['quantity']:.5f} units | Unrealized: {profit_pct*100:.2f}%")
    print("="*50)

if __name__ == "__main__":
    run_backtest(period="180d", interval="1d", leverage=1.0, initial_cash=10000.0)
