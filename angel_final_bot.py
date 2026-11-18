import os, pyotp, requests
from SmartApi import SmartConnect
from datetime import datetime
print("=== ANGEL BOT V40 SYMBOL FIELD FIX ===", flush=True)

API_KEY = os.getenv("ANGEL_API_KEY")
CLIENT_ID = os.getenv("ANGEL_CLIENT_ID")
PASSWORD = os.getenv("ANGEL_PASSWORD")
TOTP_SECRET = os.getenv("ANGEL_TOTP_SECRET")

LOT_QTY = 75

def find_token_v40(spot, direction):
    atm = int(round(spot/50)*50)
    opt_type = "CE" if direction=="CALL" else "PE"
    print("Looking ATM {} {}".format(atm, opt_type), flush=True)
    
    url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
    resp = requests.get(url, timeout=30)
    data = resp.json()
    print("Total {} records".format(len(data)), flush=True)

    print("--- SAMPLE FROM FILE (symbol field) ---", flush=True)
    c=0
    for item in data:
        sym = str(item.get('symbol',''))
        if 'NIFTY' in sym and ('CE' in sym or 'PE' in sym) and '25400' in sym:
            print("SAMPLE {} strike={} exp={} token={}".format(sym, item.get('strike'), item.get('expiry'), item.get('token')), flush=True)
            c+=1
            if c>=3:
                break

    # FINAL LOOSE SEARCH - symbol field use karo
    for item in data:
        sym = str(item.get('symbol','')).upper()
        if 'NIFTY' not in sym: continue
        if not sym.endswith(opt_type): continue
        if str(atm) not in sym: continue
        # Mil gaya
        print("FOUND {} TOKEN {} EXP {} STRIKE {}".format(item.get('symbol'), item.get('token'), item.get('expiry'), item.get('strike')), flush=True)
        return item.get('token'), item.get('symbol'), atm

    print("NOT FOUND STILL", flush=True)
    return "0", "NIFTY{} {}".format(atm, opt_type), atm

try:
    obj = SmartConnect(api_key=API_KEY)
    totp = pyotp.TOTP(TOTP_SECRET).now()
    obj.generateSession(CLIENT_ID, PASSWORD, totp)
    print("LOGIN OK {}".format(CLIENT_ID), flush=True)

    spot = 25387.4
    print("SPOT {} RSI 33.53 SCORE 80% DIR PUT".format(spot), flush=True)

    token, tradingsym, atm = find_token_v40(spot, "PUT")
    print("✅ FINAL {} TOKEN {} ATM {}".format(tradingsym, token, atm), flush=True)
    print("[PAPER] BUY {} QTY {} TOKEN {}".format(tradingsym, LOT_QTY, token), flush=True)
    print("BOT FINISHED", flush=True)
except Exception as ex:
    print("FATAL {}".format(ex), flush=True)
