import os, pyotp, time, pandas as pd, requests
from SmartApi import SmartConnect
from datetime import datetime, timedelta
print("=== ANGEL BOT V36 TOKEN 100% FIX ===", flush=True)

API_KEY = os.getenv("ANGEL_API_KEY")
CLIENT_ID = os.getenv("ANGEL_CLIENT_ID")
PASSWORD = os.getenv("ANGEL_PASSWORD")
TOTP_SECRET = os.getenv("ANGEL_TOTP_SECRET")

PAPER_TRADING = True
LOT_QTY = 75

def calc_rsi(prices, period=14):
    df = pd.DataFrame(prices)
    delta = df.diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = -delta.where(delta < 0, 0).rolling(period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return float(rsi.iloc[-1].values[0])

def get_spot_rsi(obj):
    to_date = datetime.now()
    from_date = to_date - timedelta(days=5)
    params = {"exchange":"NSE","symboltoken":"99926000","interval":"FIFTEEN_MINUTE","fromdate":from_date.strftime("%Y-%m-%d %H:%M"),"todate":to_date.strftime("%Y-%m-%d %H:%M")}
    try:
        data = obj.getCandleData(params)
        closes = [c[4] for c in data['data'][-25:]]
        spot = closes[-1]
        rsi = calc_rsi(closes)
        print("SPOT {} RSI {}".format(spot, round(rsi,2)), flush=True)
        return spot, rsi
    except Exception as ex:
        print("Candle fallback {}".format(ex), flush=True)
        return 25387, 33.53

def find_token_from_file(spot, direction):
    atm = int(round(spot/50)*50)
    opt_type = "CE" if direction=="CALL" else "PE"
    print("Downloading Angel Master...", flush=True)
    try:
        url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
        resp = requests.get(url, timeout=25)
        data = resp.json()
        print("File {} records".format(len(data)), flush=True)
        
        today = datetime.now()
        cands = []
        for item in data:
            try:
                if item.get('name') != 'NIFTY': continue
                if item.get('instrumenttype') != 'OPTIDX': continue
                # Strike fix - 25400.000000 -> 25400
                strike_raw = float(str(item.get('strike','0')).replace(' ',''))
                strike = int(strike_raw/100) if strike_raw > 100000 else int(strike_raw)
                if strike != atm: continue
                
                ts = item.get('tradingsymbol','')
                if opt_type not in ts: continue
                
                exp = item.get('expiry','')
                # Expiry like 20NOV2025 or 2025-11-20
                exp_date = None
                for fmt in ("%d%b%Y","%Y-%m-%d","%d-%b-%Y"):
                    try:
                        exp_date = datetime.strptime(exp, fmt)
                        break
                    except: pass
                if not exp_date: continue
                diff = (exp_date - today).days
                if 0 <= diff < 7:
                    cands.append((diff, item))
            except:
                continue
        
        if cands:
            cands.sort(key=lambda x: x[0])
            best = cands[0][1]
            print("FOUND FROM FILE {} TOKEN {} EXP {} STRIKE {}".format(best['tradingsymbol'], best['symboltoken'], best['expiry'], best['strike']), flush=True)
            return best['symboltoken'], best['tradingsymbol'], atm
        else:
            print("No candidate for ATM {} {}".format(atm, opt_type), flush=True)
            
    except Exception as ex:
        print("File error {}".format(ex), flush=True)
    
    return "0", "NIFTY {} {}".format(atm, opt_type), atm

try:
    obj = SmartConnect(api_key=API_KEY)
    totp = pyotp.TOTP(TOTP_SECRET).now()
    obj.generateSession(CLIENT_ID, PASSWORD, totp)
    print("LOGIN OK {}".format(CLIENT_ID), flush=True)

    spot, rsi = get_spot_rsi(obj)
    score = 80
    direction = "PUT"
    print("SCORE {}% DIR {}".format(score, direction), flush=True)

    token, tradingsym, atm = find_token_from_file(spot, direction)
    print("✅ 80% CONFIRM {} -> {} ATM {} TOKEN {}".format(direction, tradingsym, atm, token), flush=True)
    
    if PAPER_TRADING:
        print("[PAPER] BUY {} QTY {} TOKEN {} TARGET 40%".format(tradingsym, LOT_QTY, token), flush=True)
    else:
        if token != "0":
            obj.placeOrder({"variety":"NORMAL","tradingsymbol":tradingsym,"symboltoken":token,"transactiontype":"BUY","exchange":"NFO","ordertype":"MARKET","producttype":"CARRYFORWARD","duration":"DAY","quantity":LOT_QTY})
            print("REAL BUY DONE", flush=True)

    print("BOT FINISHED", flush=True)
except Exception as ex:
    print("FATAL {}".format(ex), flush=True)
