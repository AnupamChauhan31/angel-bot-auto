
# === ADD THIS PROFIT BOOKING BLOCK ===
TARGET = 40
STOPLOSS = 25

def auto_exit_if_holding():
    try:
        holdings = dhan.get_positions()
        for p in holdings.get('data', []):
            if p.get('netQty',0) != 0:
                pnl_per = float(p.get('unrealizedProfit',0)) / float(p.get('buyCost',1)) * 100
                print(f"Checking P&L: {p['tradingSymbol']} {pnl_per:.2f}%")
                if pnl_per >= TARGET or pnl_per <= -STOPLOSS:
                    dhan.place_order(
                        security_id=p['securityId'],
                        exchange_segment=p['exchangeSegment'],
                        transaction_type='SELL',
                        quantity=abs(p['netQty']),
                        order_type='MARKET',
                        product_type='INTRADAY'
                    )
                    print(f"EXIT DONE at {pnl_per:.2f}%")
                    return True
    except Exception as e:
        print(e)
    return False

# 3:15 PM Force Exit
import datetime
now = datetime.datetime.now()
if now.hour >= 15 and now.minute >= 15:
    auto_exit_if_holding()
    exit()

# Normal Exit Check
if auto_exit_if_holding():
    print("Position exited - Profit/Loss booked!")
    exit()
# === BLOCK END ===
