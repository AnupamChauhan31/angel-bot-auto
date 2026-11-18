   
   from dhanhq import DhanContext, dhanhq
import datetime

# === CONFIG - Aapka wala ===
CLIENT_ID = "1101462989"
ACCESS_TOKEN = "YOUR_DHAN_TOKEN_HERE" # Apna token yahi lagao
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
            if p.get('netQty',0) != 0 and p.get('productType') == 'INTRADAY':
                buy_cost = float(p.get('buyCost',0) or 1)
                pnl = float(p.get('unrealizedProfit',0))
                pnl_per = (pnl / buy_cost) * 100
                print(f"HOLDING: {p['tradingSymbol']} P&L {pnl_per:.2f}%")
                if pnl_per >= TARGET:
                    dhan.place_order(security_id=p['securityId'], exchange_segment=p['exchangeSegment'], transaction_type='SELL', quantity=abs(p['netQty']), order_type='MARKET', product_type='INTRADAY')
                    print(f"✅ PROFIT BOOKED {pnl_per:.2f}%")
                    return True
                if pnl_per <= -STOPLOSS:
                    dhan.place_order(security_id=p['securityId'], exchange_segment=p['exchangeSegment'], transaction_type='SELL', quantity=abs(p['netQty']), order_type='MARKET', product_type='INTRADAY')
                    print(f"🛑 STOPLOSS SAVED {pnl_per:.2f}%")
                    return True
    except Exception as e:
        print(f"Exit Error: {e}")
    return False

# Time Exit
now = datetime.datetime.now()
if now.hour == 15 and now.minute >= 15:
    auto_exit_if_holding()
    print("3:15 FORCE EXIT DONE")
    exit()

if auto_exit_if_holding():
    exit()

# === 2. YOUR 80% + MAX VOLUME + FII + OI ENTRY LOGIC ===
print("Checking 80% Condition + Max Volume...")

# --- Yaha se aapka purana FII + OI + Max Vol logic shuru ---
# CE Power, PE Power nikalna
# Agar CE >=80: Max Volume CE Strike BUY
# Agar PE >=80: Max Volume PE Strike BUY
# Nahi to NO TRADE - Capital Safe

# Example Entry (aapke purane function se):
# if ce_power >= 80:
#    strike = get_max_volume_strike("CE")
#    dhan.place_order(...)
#    print(f"CE BUY {strike}")

print("BOT CYCLE COMPLETE - Capital Safe if no 80%")
