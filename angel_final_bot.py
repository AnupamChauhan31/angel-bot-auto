import os
from SmartApi import SmartConnect
import pyotp

print("BOT START - ANGEL ONE")

API_KEY = os.getenv("ANGEL_API_KEY")
CLIENT_ID = os.getenv("ANGEL_CLIENT_ID")
PASSWORD = os.getenv("ANGEL_PASSWORD")
TOTP_SECRET = os.getenv("ANGEL_TOTP_SECRET")

TARGET = 40
STOPLOSS = 25

try:
    totp = pyotp.TOTP(TOTP_SECRET).now()
    obj = SmartConnect(api_key=API_KEY)
    data = obj.generateSession(CLIENT_ID, PASSWORD, totp)
    print(f"LOGIN SUCCESS: {CLIENT_ID}")

    holdings = obj.holding()
    print(f"HOLDINGS: {holdings}")
    
    if holdings and holdings.get('data'):
        for stock in holdings['data']:
            symbol = stock['tradingsymbol']
            ltp = float(stock['ltp'])
            avg = float(stock['averageprice'])
            pnl_per = ((ltp - avg) / avg * 100) if avg != 0 else 0
            print(f"HOLDING: {symbol} PnL: {pnl_per:.2f}%")
            if pnl_per >= TARGET:
                print(f"PROFIT BOOK SIGNAL: {symbol}")
            if pnl_per <= -STOPLOSS:
                print(f"STOPLOSS SIGNAL: {symbol}")
    else:
        print("No holdings found")

    print("Bot completed")

except Exception as e:
    print(f"ERROR: {e}")
