import os, pyotp, requests
from SmartApi import SmartConnect
from datetime import datetime
print("=== ANGEL BOT V39 DEBUG TOKEN ===", flush=True)

API_KEY = os.getenv("ANGEL_API_KEY")
CLIENT_ID = os.getenv("ANGEL_CLIENT_ID")
PASSWORD = os.getenv("ANGEL_PASSWORD")
TOTP_SECRET = os.getenv("ANGEL_TOTP_SECRET")

LOT_QTY = 75

def find_token_debug(spot, direction):
    atm = int(round(spot/50)*50)
    opt_type = "CE" if direction=="CALL" else "PE"
    print("Looking ATM {} {}".format(atm, opt_type), flush=True)
    
    url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
    resp = requests.get(url, timeout=30)
    data = resp.json()
    print("Total {} records".format(len(data)), flush=True)

    # DEBUG - Pehle 5 NIFTY OPT dikhao
    print("--- SAMPLE NIFTY OPTIONS FROM FILE ---", flush=True)
    cnt=0
    for item in data:
        ts = str(item.get('tradingsymbol',''))
        if 'NIFTY' in ts and ts.endswith(opt_type):
            print("SAMPLE: {} | strike={} | expiry={} | token={}".format(ts, item.get('strike'), item.get('expiry'), item.get('symboltoken')), flush=True)
            cnt+=1
            if cnt>=5:
                break

    # AB FINAL SEARCH - Sabse loose filter
    found = None
    for item in data:
        ts = str(item.get('tradingsymbol','')).upper()
        # Loose: NIFTY ho, PE/CE se khatam ho, 25400 ho
        if 'NIFTY' not in ts: continue
        if not ts.endswith(opt_type): continue
        if str(atm) not in ts: continue
        # Mil gaya
        found = item
        break
    
    if found:
        print("FOUND LOOSE {} TOKEN {} STRIKE {} EXP {}".format(found['tradingsymbol'], found['symboltoken'], found.get('strike'), found.get('expiry')), flush=True)
        return found['symboltoken'], found['tradingsymbol'], atm
    else:
        print("LOOSE BHI FAIL - File me {} ka option hi nahi hai".format(atm), flush=True)
        # Koi bhi NIFTY PE le lo nearest
        for item in data:
            ts = str(item.get('tradingsymbol',''))
            if 'NIFTY' in ts and ts.endswith('PE'):
                print("FALLBACK PE {} TOKEN {}".format(ts, item.get('symboltoken')), flush=True)
                return item['symboltoken'], ts, atm

    return "0", "NIFTY{} {}".format(atm, opt_type), atm

try:
    obj = SmartConnect(api_key=API_KEY)
    totp = pyotp.TOTP(TOTP_SECRET).now()
    obj.generateSession(CLIENT_ID, PASSWORD, totp)
    print("LOGIN OK {}".format(CLIENT_ID), flush=True)

    spot = 25387.4
    print("SPOT {} RSI 33.53 SCORE 80% DIR PUT ATM 25400".format(spot), flush=True)

    token, tradingsym, atm = find_token_debug(spot, "PUT")
    print("✅ FINAL {} TOKEN {} ATM {}".format(tradingsym, token, atm), flush=True)
    print("[PAPER] BUY {} QTY {} TOKEN {}".format(tradingsym, LOT_QTY, token), flush=True)
    print("BOT FINISHED", flush=True)
except Exception as ex:
    print("FATAL {}".format(ex), flush=True)
