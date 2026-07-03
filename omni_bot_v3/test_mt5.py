import MetaTrader5 as mt5

print("Testing MT5 Connection...")

# Connect to the MetaTrader 5 terminal
if not mt5.initialize():
    print("initialize() failed. Please make sure the MetaTrader 5 program is open on your desktop!")
    mt5.shutdown()
else:
    print("Successfully connected to MetaTrader 5!")
    account_info = mt5.account_info()
    if account_info is None:
        print("Connected to terminal, but could not get account info. Make sure you are logged into a demo account.")
    else:
        print(f"Logged into Account: {account_info.login}")
        print(f"Server: {account_info.server}")
        print(f"Balance: ${account_info.balance:,.2f}")
        print(f"Equity: ${account_info.equity:,.2f}")
        print(f"Leverage: 1:{account_info.leverage}")
    
    mt5.shutdown()
