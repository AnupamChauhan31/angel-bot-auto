
import os, pyotp, requests, time
from SmartApi import SmartConnect
from datetime import datetime
print("=== ANGEL BOT V43 REAL ===", flush=True)

API_KEY = os.getenv("ANGEL_API_KEY")
CLIENT_ID = os.getenv("ANGEL_CLIENT_ID")
PASSWORD = os.getenv("ANGEL_PASSWORD")
TOTP_SECRET = os.getenv("ANGEL_TOTP_SECRET")

# 🔴 REAL TRADING ON
PAPER_TRADING = False
LOT_QTY = 75

def find_token(spot, direction):
    atm = int(round(spot/50)*50)
    opt_type = "CE" if direction=="CALL" else "PE"
    print("ATM {} {}".format(atm, opt_type), flush=True)
    url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
    data = requests.get(url, timeout=30).json()
    cands=[]
    for item in data:
        sym = str(item.get('symbol','')).upper().strip()
        if not sym.startswith('NIFTY'): continue
        if sym.startswith('FINNIFTY') or sym.startswith('BANKNIFTY') or sym.startswith('MIDCPNIFTY'): continue
        if not sym.endswith(opt_type): continue
        if str(atm) not in sym: continue
        try:
            exp = datetime.strptime(item.get('expiry',''), "%d%b%Y")
            days = (exp - datetime.now()).days
            if 0 <= days < 10:
                cands.append((days, item))
        except: pass
    cands.sort(key=lambda x: x[0])
    if cands:
        b = cands[0][1]
        print("✅ WEEKLY NIFTY FOUND {} TOKEN {} EXP {}".format(b['symbol'], b['token'], b['expiry']), flush=True)
        return b['token'], b['symbol'], atm
    return "0","",atm

try:
    obj = SmartConnect(api_key=API_KEY)
    obj.generateSession(CLIENT_ID, PASSWORD, pyotp.TOTP(TOTP_SECRET).now())
    print("LOGIN OK {}".format(CLIENT_ID), flush=True)

    spot = 25387.4
    rsi = 33.53
    print("SPOT {} RSI {} SCORE 80% DIR PUT".format(spot, rsi), flush=True)

    token, tradingsym, atm = find_token(spot, "PUT")
    print("✅ FINAL {} TOKEN {} ATM {}".format(tradingsym, token, atm), flush=True)

    if token != "0":
        if PAPER_TRADING:
            print("[PAPER] BUY {} QTY {} TOKEN {}".format(tradingsym, LOT_QTY, token), flush=True)
        else:
            print("🔴 REAL ORDER PLACING {} QTY {}".format(tradingsym, LOT_QTY), flush=True)
            order = obj.placeOrder({"variety":"NORMAL","tradingsymbol":tradingsym,"symboltoken":token,"transactiontype":"BUY","exchange":"NFO","ordertype":"MARKET","producttype":"CARRYFORWARD","duration":"DAY","quantity":LOT_QTY})
            print("ORDER RESPONSE {}".format(order), flush=True)
            print("✅ REAL ORDER DONE", flush=True)
    else:
        print("TOKEN 0 FAIL", flush=True)

    print("BOT FINISHED", flush=True)
except Exception as ex:
    print("FATAL {}".format(ex), flush=True)
