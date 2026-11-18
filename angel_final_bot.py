from dhanhq import DhanContext, dhanhq
import datetime
import os

# === CONFIG - Aapka wala ===
CLIENT_ID = "1101462989"
ACCESS_TOKEN = os.getenv("DHAN_ACCESS_TOKEN", "YOUR_DHAN_TOKEN_HERE")
dhan_context = DhanContext(CLIENT_ID, ACCESS_TOKEN)
dhan = dhanhq(dhan_context)

TARGET = 40
STOPLOSS = 25

print(f"BOT START {datetime.datetime.now()}")

# === 1. AUTO EXIT - PROFIT BOOK & LOSS EXIT ===
def auto_exit_if_holding():
    try:
        holdings = dhan.get_positions()
        for p in holdings.get('data', []):
            if p.get('netQty',0) != 0 and p.get('productType') == 'CNC':
                buy_cost = float(p.get('buyCost',0) or 1)
                pnl = float(p.get('unrealizedProfit',0) or 0)
                pnl_per = (pnl / buy_cost) * 100
                print(f"HOLDING: {p['tradingSymbol']} PnL%: {pnl_per}")
                if pnl_per >= TARGET:
                    dhan.place_order(security_id=p['securityId'], exchange_segment=p['exchangeSegment'], transaction_type='SELL', quantity=p['netQty'], order_type='MARKET', product_type=p['productType'], price=0)
                    print(f"PROFIT BOOKED {pnl_per}")
                    return True
                if pnl_per <= -STOPLOSS:
                    dhan.place_order(security_id=p['securityId'], exchange_segment=p['exchangeSegment'], transaction_type='SELL', quantity=p['netQty'], order_type='MARKET', product_type=p['productType'], price=0)
                    print(f"STOPLOSS SAVED {pnl_per}")
                    return True
    except Exception as e:
        print(f"Exit Error: {e}")
    return False

auto_exit_if_holding()
print("Bot run completed successfully!")
