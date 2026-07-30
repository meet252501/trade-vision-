import MetaTrader5 as mt5
from datetime import datetime
from exchanges.base_adapter import BaseExchangeAdapter
from config import TIMEFRAME, CATASTROPHIC_SL_PCT, CATASTROPHIC_TP_PCT

# Map config timeframes to MT5 constants
TIMEFRAME_MAP = {
    '1H': mt5.TIMEFRAME_H1,
    '4H': mt5.TIMEFRAME_H4,
    '1D': mt5.TIMEFRAME_D1,
}

# Map Yahoo Finance tickers to MT5 MetaQuotes-Demo symbols
SYMBOL_MAP = {
    'EURUSD=X': 'EURUSD',
    'GBPUSD=X': 'GBPUSD',
    'USDJPY=X': 'USDJPY',
    'USDCHF=X': 'USDCHF',
    'BTC-USD': 'BTC',
    'ETH-USD': 'ETH',
    'SOL-USD': 'SOL'
}
# Stocks/ETFs share the exact same names on this server

def to_mt5_symbol(ticker):
    return SYMBOL_MAP.get(ticker, ticker)

def to_bot_ticker(mt5_symbol):
    for k, v in SYMBOL_MAP.items():
        if v == mt5_symbol:
            return k
    return mt5_symbol

class MT5Adapter(BaseExchangeAdapter):
    
    def initialize(self):
        if not mt5.initialize():
            print("initialize() failed, error code =", mt5.last_error())
            return False
        return True

    def shutdown(self):
        mt5.shutdown()

    def fetch_live_data(self, tickers, num_bars=100):
        market_state = {}
        last_prices = {}
        mt5_tf = TIMEFRAME_MAP.get(TIMEFRAME, mt5.TIMEFRAME_D1)
        
        for ticker in tickers:
            mt5_symbol = to_mt5_symbol(ticker)
            rates = mt5.copy_rates_from_pos(mt5_symbol, mt5_tf, 0, num_bars)
            if rates is None or len(rates) == 0:
                print(f"Warning: Could not fetch data for {mt5_symbol}")
                continue
                
            bars = []
            for r in rates:
                bars.append({
                    'date': datetime.fromtimestamp(r['time']).strftime('%Y-%m-%d %H:%M:%S'),
                    'open': float(r['open']),
                    'high': float(r['high']),
                    'low': float(r['low']),
                    'close': float(r['close']),
                    'volume': float(r['real_volume'] if r['real_volume'] > 0 else r['tick_volume'])
                })
            
            market_state[ticker] = bars
            
            tick = mt5.symbol_info_tick(mt5_symbol)
            if tick:
                last_prices[ticker] = (tick.bid + tick.ask) / 2
            else:
                last_prices[ticker] = bars[-1]['close']
                
        return market_state, last_prices

    def get_portfolio_state(self):
        account = mt5.account_info()
        if account is None:
            raise RuntimeError(f"Could not get MT5 account info. Error: {mt5.last_error()}")
            
        positions = mt5.positions_get()
        parsed_positions = []
        if positions:
            for pos in positions:
                parsed_positions.append({
                    'ticker': to_bot_ticker(pos.symbol),
                    'quantity': pos.volume,
                    'entry_price': pos.price_open,
                    'is_short': pos.type == mt5.ORDER_TYPE_SELL,
                    'entry_step': 0 
                })
                
        return {
            'total_equity': account.equity,
            'real_equity': account.equity,
            'positions': parsed_positions,
            'last_prices': {} 
        }

    def execute_orders(self, orders):
        for order in orders:
            bot_ticker = order['ticker']
            symbol = to_mt5_symbol(bot_ticker)
            qty = order['quantity']
            side = order['side']
            
            mt5.symbol_select(symbol, True)
            
            tick = mt5.symbol_info_tick(symbol)
            info = mt5.symbol_info(symbol)
            if tick is None or info is None:
                print(f"Could not get tick/info for {symbol}, skipping order.")
                continue
                
            step = info.volume_step
            qty = round(qty / step) * step
            if qty < info.volume_min:
                print(f"Quantity {qty} too small for {symbol} (min {info.volume_min}). Skipping.")
                continue
                
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": float(qty),
                "type": mt5.ORDER_TYPE_BUY if side in ['buy', 'cover', 'cover_half'] else mt5.ORDER_TYPE_SELL,
                "price": tick.ask if side in ['buy', 'cover', 'cover_half'] else tick.bid,
                "sl": tick.ask * (1 - CATASTROPHIC_SL_PCT) if side == 'buy' else tick.bid * (1 + CATASTROPHIC_SL_PCT) if side == 'short' else 0.0,
                "tp": tick.ask * (1 + CATASTROPHIC_TP_PCT) if side == 'buy' else tick.bid * (1 - CATASTROPHIC_TP_PCT) if side == 'short' else 0.0,
                "deviation": 20,
                "magic": 234000,
                "comment": "Omni-Bot v3.0",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            print(f"Sending order: {side} {qty} {symbol}")
            result = mt5.order_send(request)
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                print(f"Order failed! Code: {result.retcode}, Description: {result.comment}")
            else:
                print(f"Order filled! Ticket: {result.order}")
