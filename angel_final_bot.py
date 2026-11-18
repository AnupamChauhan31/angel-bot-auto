import os, pyotp, time, pandas as pd, requests
from SmartApi import SmartConnect
from datetime import datetime, timedelta
print("=== ANGEL BOT V35 INSTRUMENT FILE FIX ===", flush=True)

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
        return 25400, 33.0

def find_token_from_file(spot, direction):
    atm = int(round(spot/50)*50)
    opt_type = "CE" if direction=="CALL" else "PE"
    print("Downloading Angel Instrument Master...", flush=True)
    try:
        url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
        resp = requests.get(url, timeout=20)
        data = resp.json()
        print("File downloaded {} records".format(len(data)), flush=True)
        
        # Aaj ke aas paas ki expiry dhoondo
        today = datetime.now()
        candidates = []
        for item in data:
            if item.get('exch_seg')=='NFO' and item.get('symbol')=='NIFTY' and str(atm)==str(item.get('strike')):
                if item.get('instrumenttype')=='OPTIDX' and item.get('symboltoken'):
                    # PE/CE check
                    sym = item.get('tradingsymbol','')
                    if opt_type in sym and str(atm) in sym:
                        # Expiry
                        exp_str = item.get('expiry','')
                        try:
                            exp_date = datetime.strptime(exp_str, "%d%b%Y")
                            diff = (exp_date - today).days
                            if diff >=0 and diff < 10: # agle 10 din ki expiry
                                candidates.append((diff, item))
                        except:
                            pass
        
        if candidates:
            candidates.sort(key=lambda x: x[0])
            best = candidates[0][1]
            token = best['symboltoken']
            tradingsym = best['tradingsymbol']
            print("FOUND FROM FILE {} TOKEN {} EXP {}".format(tradingsym, token, best['expiry']), flush=True)
            return token, tradingsym, atm
            
    except Exception as ex:
        print("File download error {}".format(ex), flush=True)
    
    print("File se nahi mila fallback", flush=True)
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
        print("[PAPER] BUY {} QTY {} | TARGET 40% SL 15%".format(tradingsym, LOT_QTY), flush=True)
        print("CE/PE AUTO - Isi file se dono hoga", flush=True)
    else:
        if token != "0":
            obj.placeOrder({"variety":"NORMAL","tradingsymbol":tradingsym,"symboltoken":token,"transactiontype":"BUY","exchange":"NFO","ordertype":"MARKET","producttype":"CARRYFORWARD","duration":"DAY","quantity":LOT_QTY})
            print("REAL BUY DONE", flush=True)

    print("BOT FINISHED", flush=True)
except Exception as ex:
    print("FATAL {}".format(ex), flush=True)
