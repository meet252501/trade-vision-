class BaseExchangeAdapter:
    """
    Abstract interface for all broker/exchange integrations.
    Any new exchange (Binance, Alpaca, etc.) must implement these methods.
    """
    
    def initialize(self):
        """Connects to the exchange and authenticates."""
        raise NotImplementedError

    def shutdown(self):
        """Disconnects cleanly from the exchange."""
        raise NotImplementedError

    def fetch_live_data(self, tickers, num_bars=100):
        """
        Fetches the latest OHLCV bars and current tick prices.
        Returns: (market_state, last_prices)
        """
        raise NotImplementedError

    def get_portfolio_state(self):
        """
        Fetches the account equity, balance, and open positions.
        Returns: portfolio_state dict
        """
        raise NotImplementedError

    def execute_orders(self, orders):
        """
        Translates bot signals into broker-specific API calls and executes them.
        """
        raise NotImplementedError
