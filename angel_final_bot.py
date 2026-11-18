import os, pyotp, time, requests
from SmartApi import SmartConnect
from datetime import datetime
print("=== ANGEL BOT V38 STRIKE x100 FIX ===", flush=True)

API_KEY = os.getenv("ANGEL_API_KEY")
CLIENT_ID = os.getenv("ANGEL_CLIENT_ID")
PASSWORD = os.getenv("ANGEL_PASSWORD")
TOTP_SECRET = os.getenv("ANGEL_TOTP_SECRET")

PAPER_TRADING = True
LOT_QTY = 75

def find_token_correct(spot, direction):
    atm = int(round(spot/50)*50)
    opt_type = "CE" if direction=="CALL" else "PE"
    # Angel file me strike x100 hota hai
    strike_file_format = str(atm * 100)  
    print("ATM {} -> File me strike {}".format(atm, strike_file_format), flush=True)
    print("Downloading Master...", flush=True)
    try:
        url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
        resp = requests.get(url, timeout=30)
        data = resp.json()
        print("Total {} records".format(len(data)), flush=True)
        
        cands = []
        for item in data:
            if item.get('exch_seg') != 'NFO': continue
            if item.get('name') != 'NIFTY': continue
            if item.get('instrumenttype') != 'OPTIDX': continue
            # Strike check - x100 wala
            file_strike = str(item.get('strike','')).split('.')[0]  # 2540000.000000 -> 2540000
            if file_strike != strike_file_format and file_strike != str(atm*100) and file_strike != str(atm):
                # Kabhi kabhi 25400 hi hota hai
                try:
                    if int(float(file_strike)) // 100 != atm and int(float(file_strike)) != atm:
                        continue
                except:
                    continue
            
            ts = str(item.get('tradingsymbol','')).upper()
            if not ts.endswith(opt_type): continue
            if str(atm) not in ts: continue
            
            # Expiry sabse nazdeek wali
            exp = item.get('expiry','')
            try:
                # Format: 18NOV2025
                exp_date = datetime.strptime(exp, "%d%b%Y")
                days = (exp_date - datetime.now()).days
                if days >=0 and days < 8:
                    cands.append((days, item))
            except:
                cands.append((99, item))
        
        if cands:
            cands.sort(key=lambda x: x[0])
            best = cands[0][1]
            print("FOUND FINAL {} TOKEN {} STRIKE {} EXP {}".format(best['tradingsymbol'], best['symboltoken'], best['strike'], best['expiry']), flush=True)
            return best['symboltoken'], best['tradingsymbol'], atm
        else:
            print("No candidate even after x100 fix for {} {}".format(atm, opt_type), flush=True)
            
    except Exception as ex:
        print("File error {}".format(ex), flush=True)
    
    return "0", "NIFTY{} {}".format(atm, opt_type), atm

try:
    obj = SmartConnect(api_key=API_KEY)
    totp = pyotp.TOTP(TOTP_SECRET).now()
    obj.generateSession(CLIENT_ID, PASSWORD, totp)
    print("LOGIN OK {}".format(CLIENT_ID), flush=True)

    spot = 25387.4
    rsi = 33.53
    print("SPOT {} RSI {} SCORE 80% DIR PUT".format(spot, rsi), flush=True)

    token, tradingsym, atm = find_token_correct(spot, "PUT")
    print("✅ 80% CONFIRM PUT -> {} ATM {} TOKEN {}".format(tradingsym, atm, token), flush=True)
    print("[PAPER] BUY {} QTY {} TOKEN {} | TARGET 40%".format(tradingsym, LOT_QTY, token), flush=True)
    print("BOT FINISHED", flush=True)
except Exception as ex:
    print("FATAL {}".format(ex), flush=True)
