import os
import requests
import json
from datetime import datetime

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

def send_discord_alert(side, ticker, qty, price, pnl=None):
    """
    Send a rich embed message to a Discord webhook.
    """
    if not DISCORD_WEBHOOK_URL:
        print("[Notifier] No DISCORD_WEBHOOK_URL configured, skipping alert.")
        return

    is_buy = side.upper() == "BUY"
    color = 0x22C55E if is_buy else 0xEF4444  # Green for BUY, Red for SELL
    
    title = f"🟢 BUY Executed: {ticker}" if is_buy else f"🔴 SELL Executed: {ticker}"
    
    # Calculate total value
    total_value = qty * price
    
    description = f"**{qty} shares** of **{ticker}** at **${price:.2f}**\nTotal Value: **${total_value:.2f}**"
    
    if pnl is not None and not is_buy:
        # If it's a sell, we can report realized PnL
        pnl_str = f"+${pnl:.2f}" if pnl >= 0 else f"-${abs(pnl):.2f}"
        description += f"\n\nRealized PnL: **{pnl_str}**"

    embed = {
        "title": title,
        "description": description,
        "color": color,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "footer": {
            "text": "TradeVision AI Terminal"
        }
    }

    payload = {
        "embeds": [embed]
    }

    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        if response.status_code == 204:
            print(f"[Notifier] Successfully sent Discord alert for {ticker}")
        else:
            print(f"[Notifier] Failed to send Discord alert: {response.status_code}")
    except Exception as e:
        print(f"[Notifier] Exception sending Discord alert: {e}")
