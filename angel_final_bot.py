
import os, pyotp, requests, time
from SmartApi import SmartConnect
from datetime import datetime
print("=== ANGEL BOT V42 ONLY NIFTY WEEKLY ===", flush=True)

API_KEY = os.getenv("ANGEL_API_KEY")
CLIENT_ID = os.getenv("ANGEL_CLIENT_ID")
PASSWORD = os.getenv("ANGEL_PASSWORD")
TOTP_SECRET = os.getenv("ANGEL_TOTP_SECRET")

PAPER_TRADING = True
LOT_QTY = 75

def find_token_only_nifty(spot, direction):
    atm = int(round(spot/50)*50)
    opt_type = "CE" if direction=="CALL" else "PE"
    print("ATM {} {}".format(atm, opt_type), flush=True)
    
    url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
    resp = requests.get(url, timeout=30)
    data = resp.json()
    
    cands=[]
    for item in data:
        sym = str(item.get('symbol','')).upper().strip()
        # ✅ SIRF NIFTY - FINNIFTY, BANKNIFTY SKIP
        if not sym.startswith('NIFTY'):  # FINNIFTY startswith FINNIFTY, not NIFTY
            continue
        # NIFTY ke baad number aana chahiye, FINNIFTY nahi
        if sym.startswith('FINNIFTY') or sym.startswith('BANKNIFTY') or sym.startswith('MIDCPNIFTY'):
            continue
            
        if not sym.endswith(opt_type): continue
        if str(atm) not in sym: continue
        
        exp_str = item.get('expiry','')
        try:
            exp_date = datetime.strptime(exp_str, "%d%b%Y")
            days = (exp_date - datetime.now()).days
            if days>=0 and days<30:
                cands.append((days, item))
        except:
            pass
    
    cands.sort(key=lambda x: x[0])
    if cands:
        best = cands[0][1]
        print("✅ WEEKLY NIFTY FOUND {} TOKEN {} EXP {} DAYS {}".format(best['symbol'], best['token'], best['expiry'], cands[0][0]), flush=True)
        return best['token'], best['symbol'], atm
    else:
        print("No weekly Nifty found", flush=True)
    return "0","NIFTY",atm

try:
    obj = SmartConnect(api_key=API_KEY)
    totp = pyotp.TOTP(TOTP_SECRET).now()
    obj.generateSession(CLIENT_ID, PASSWORD, totp)
    print("LOGIN OK {}".format(CLIENT_ID), flush=True)

    spot = 25387.4
    print("SPOT {} RSI 33.53 SCORE 80% DIR PUT".format(spot), flush=True)

    token, tradingsym, atm = find_token_only_nifty(spot, "PUT")
    print("✅ FINAL {} TOKEN {} ATM {}".format(tradingsym, token, atm), flush=True)
    print("[PAPER] BUY {} QTY {} TOKEN {}".format(tradingsym, LOT_QTY, token), flush=True)
    print("BOT FINISHED", flush=True)
except Exception as ex:
    print("FATAL {}".format(ex), flush=True)
