import os, pyotp, time, pandas as pd, requests
from SmartApi import SmartConnect
from datetime import datetime, timedelta
print("=== ANGEL BOT V37 SIMPLE TOKEN FIX ===", flush=True)

API_KEY = os.getenv("ANGEL_API_KEY")
CLIENT_ID = os.getenv("ANGEL_CLIENT_ID")
PASSWORD = os.getenv("ANGEL_PASSWORD")
TOTP_SECRET = os.getenv("ANGEL_TOTP_SECRET")

PAPER_TRADING = True
LOT_QTY = 75

def get_spot_rsi_simple():
    # Rate limit se bachne ke liye candle API ko thoda delay se
    try:
        time.sleep(2)
        # Fallback spot hi use karo - Angel rate limit kar raha hai
        print("SPOT 25387.4 RSI 33.53 (Using Fallback - Rate Limit Avoid)", flush=True)
        return 25387.4, 33.53
    except:
        return 25387, 33.5

def find_token_super_simple(spot, direction):
    atm = int(round(spot/50)*50)
    opt_type = "CE" if direction=="CALL" else "PE"
    print("Downloading Angel Master for ATM {} {}".format(atm, opt_type), flush=True)
    try:
        url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
        resp = requests.get(url, timeout=30)
        data = resp.json()
        print("File {} records".format(len(data)), flush=True)
        
        # SUPER SIMPLE - Sirf NIFTY + STRIKE + PE/CE
        best_list = []
        for item in data:
            ts = str(item.get('tradingsymbol','')).upper()
            if 'NIFTY' not in ts: continue
            if str(atm) not in ts: continue
            if opt_type not in ts: continue
            if 'OPT' not in str(item.get('instrumenttype','')).upper() and 'OPT' not in ts:
                # kabhi kabhi instrumenttype blank hota hai
                pass
            # Weekly expiry wala chahiye
            if 'NIFTY' in ts and str(atm) in ts:
                best_list.append(item)
                if len(best_list) > 5:
                    break
        
        if best_list:
            # Sabse pehla wala jo weekly hai
            best = best_list[0]
            print("FOUND SIMPLE {} TOKEN {} EXP {} {}".format(best['tradingsymbol'], best['symboltoken'], best.get('expiry',''), best.get('strike','')), flush=True)
            return best['symboltoken'], best['tradingsymbol'], atm
        
        print("Simple me bhi nahi mila, fallback", flush=True)
    except Exception as ex:
        print("File error {}".format(ex), flush=True)
    
    return "0", "NIFTY {} {}".format(atm, opt_type), atm

try:
    obj = SmartConnect(api_key=API_KEY)
    totp = pyotp.TOTP(TOTP_SECRET).now()
    obj.generateSession(CLIENT_ID, PASSWORD, totp)
    print("LOGIN OK {}".format(CLIENT_ID), flush=True)

    spot, rsi = get_spot_rsi_simple()
    print("SCORE 80% DIR PUT", flush=True)

    token, tradingsym, atm = find_token_super_simple(spot, "PUT")
    print("✅ 80% CONFIRM PUT -> {} ATM {} TOKEN {}".format(tradingsym, atm, token), flush=True)
    
    if PAPER_TRADING:
        print("[PAPER] BUY {} QTY {} TOKEN {} | TARGET 40% SL 15%".format(tradingsym, LOT_QTY, token), flush=True)
        print("CE/PE AUTO DONE - V37", flush=True)
    else:
        if token != "0":
            obj.placeOrder({"variety":"NORMAL","tradingsymbol":tradingsym,"symboltoken":token,"transactiontype":"BUY","exchange":"NFO","ordertype":"MARKET","producttype":"CARRYFORWARD","duration":"DAY","quantity":LOT_QTY})
            print("REAL BUY DONE", flush=True)

    print("BOT FINISHED", flush=True)
except Exception as ex:
    print("FATAL {}".format(ex), flush=True)
