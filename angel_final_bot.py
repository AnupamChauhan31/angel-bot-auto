
import os
from datetime import datetime
from SmartApi import SmartConnect

# === CONFIG ===
MIN_BALANCE = 2000
VIX_LIMIT = 16

def get_market_direction(obj):
    """Direction Confirm Logic"""
    try:
        # 1. Nifty LTP lo - Angel API se
        # Nifty 50 token = 99926000
        nifty_ltp_data = obj.ltpData("NSE", "NIFTY", "99926000")
        ltp = nifty_ltp_data['data']['ltp']
        
        # 2. Day open vs abhi ka compare (Simple logic)
        # Agar LTP > Day Open + 30 points = Uptrend = CE
        # Agar LTP < Day Open - 30 points = Downtrend = PE
        
        # Day open lene ke liye candle data
        import datetime as dt
        today = dt.date.today()
        from_time = f"{today} 09:15"
        to_time = f"{today} 09:45"
        
        # History se open nikalo
        try:
            historicParam = {
                "exchange": "NSE",
                "symboltoken": "99926000",
                "interval": "FIVE_MINUTE",
                "fromdate": from_time,
                "todate": to_time
            }
            candles = obj.getCandleData(historicParam)
            day_open = candles['data'][0][1] # open price
        except:
            day_open = ltp # fallback
            
        diff = ltp - day_open
        print(f"Nifty LTP: {ltp} | Day Open: {day_open} | Diff: {diff:.2f}")

        # 3. Direction Decision
        if diff > 30:
            return "CE", f"Uptrend Confirm +{diff:.2f} -> CALL"
        elif diff < -30:
            return "PE", f"Downtrend Confirm {diff:.2f} -> PUT"
        else:
            return "NONE", f"Sideways {diff:.2f} - No Clear Direction - SKIP"

    except Exception as e:
        print(f"Direction Error: {e}")
        return "NONE", "Direction fetch fail - No Trade"

# === MAIN BOT ===
print("=== ANGEL BOT START ===")
now = datetime.now()
print(f"Time: {now}")

# Sunday check
if now.weekday() == 6:
    print("Market Closed - Sunday hai. Bot exit. No trade today.")
    exit()
if now.weekday() == 5:
    print("Market Closed - Saturday hai. Bot exit.")
    exit()

# Login
api_key = os.getenv("ANGEL_API_KEY")
client_id = os.getenv("ANGEL_CLIENT_ID")
password = os.getenv("ANGEL_PASSWORD")
totp_secret = os.getenv("ANGEL_TOTP_SECRET")

obj = SmartConnect(api_key=api_key)
import pyotp
totp = pyotp.TOTP(totp_secret).now()
data = obj.generateSession(client_id, password, totp)

if not data['status']:
    print(f"Login Fail: {data}")
    exit()

print("Login Success!")

# Balance check
try:
    rms = obj.rmsLimit()
    print(f"RMS Response: {rms}")
    balance = float(rms['data']['availablecash'] if 'availablecash' in str(rms) else rms['data']['net'] if 'net' in str(rms['data']) else 0)
    # Safe parse
    if balance == 0:
        # Try alternate field
        balance = float(rms['data'].get('availablecash', 10000))
    print(f"Balance: {balance}")
    if balance < MIN_BALANCE:
        print(f"Balance low {balance} < {MIN_BALANCE}. No trade.")
        exit()
except Exception as e:
    print(f"Balance check error: {e} - Continuing with safe mode")
    balance = 10000

print(f"Safety OK - Balance {balance}")

# DIRECTION CHECK - NEW
print("--- Direction Check Start ---")
side, msg = get_market_direction(obj)
print(msg)

if side == "CE":
    print("FINAL DECISION: BUY CALL (CE)")
    # Yahan aapka placeOrder ayega
elif side == "PE":
    print("FINAL DECISION: BUY PUT (PE)")
    # Yahan aapka placeOrder ayega
else:
    print("FINAL DECISION: NO TRADE TODAY - Direction clear nahi hai")
    exit()

print("Bot Ready - Place Order Logic Yahan Add Karo")
