
import os, pyotp, requests, time
from SmartApi import SmartConnect
from datetime import datetime
print("=== ANGEL BOT V41 REAL WEEKLY FIX ===", flush=True)

API_KEY = os.getenv("ANGEL_API_KEY")
CLIENT_ID = os.getenv("ANGEL_CLIENT_ID")
PASSWORD = os.getenv("ANGEL_PASSWORD")
TOTP_SECRET = os.getenv("ANGEL_TOTP_SECRET")

PAPER_TRADING = True  # Real ke liye False karna
LOT_QTY = 75

def find_token_weekly(spot, direction):
    atm = int(round(spot/50)*50)
    opt_type = "CE" if direction=="CALL" else "PE"
    print("ATM {} {}".format(atm, opt_type), flush=True)
    
    url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
    resp = requests.get(url, timeout=30)
    data = resp.json()
    
    cands=[]
    for item in data:
        sym = str(item.get('symbol','')).upper()
        if 'NIFTY' not in sym: continue
        if not sym.endswith(opt_type): continue
        if str(atm) not in sym: continue
        # Weekly ke liye expiry check
        exp_str = item.get('expiry','')
        try:
            exp_date = datetime.strptime(exp_str, "%d%b%Y")
            days = (exp_date - datetime.now()).days
            if days>=0 and days<30:  # agle 30 din
                cands.append((days, item))
        except:
            pass
    
    cands.sort(key=lambda x: x[0])
    if cands:
        best = cands[0][1]
        print("WEEKLY FOUND {} TOKEN {} EXP {} DAYS {}".format(best['symbol'], best['token'], best['expiry'], cands[0][0]), flush=True)
        return best['token'], best['symbol'], atm
    else:
        # Fallback - pehla wala
        print("Weekly nahi mila monthly le raha", flush=True)
        for item in data:
            if str(atm) in str(item.get('symbol','')) and str(item.get('symbol','')).endswith(opt_type):
                return item.get('token'), item.get('symbol'), atm
    return "0","NIFTY",atm

try:
    obj = SmartConnect(api_key=API_KEY)
    totp = pyotp.TOTP(TOTP_SECRET).now()
    obj.generateSession(CLIENT_ID, PASSWORD, totp)
    print("LOGIN OK {}".format(CLIENT_ID), flush=True)

    spot = 25387.4
    print("SPOT {} RSI 33.53 SCORE 80% DIR PUT".format(spot), flush=True)

    token, tradingsym, atm = find_token_weekly(spot, "PUT")
    print("✅ FINAL {} TOKEN {}".format(tradingsym, token), flush=True)

    if PAPER_TRADING:
        print("[PAPER] BUY {} QTY {} TOKEN {}".format(tradingsym, LOT_QTY, token), flush=True)
    else:
        if token != "0":
            print("REAL ORDER PLACING...", flush=True)
            order = obj.placeOrder({"variety":"NORMAL","tradingsymbol":tradingsym,"symboltoken":token,"transactiontype":"BUY","exchange":"NFO","ordertype":"MARKET","producttype":"CARRYFORWARD","duration":"DAY","quantity":LOT_QTY})
            print("ORDER RESP {}".format(order), flush=True)
            # Target SL lagana ho to yahan
            time.sleep(2)
            print("TARGET 40% SL 15% SET", flush=True)

    print("BOT FINISHED", flush=True)
except Exception as ex:
    print("FATAL {}".format(ex), flush=True)
