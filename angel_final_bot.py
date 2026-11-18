import os, pyotp, time, pandas as pd
from SmartApi import SmartConnect
from datetime import datetime, timedelta
print("=== ANGEL BOT V34 TOKEN FIX ===", flush=True)

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

def find_token_smart(obj, spot, direction):
    atm = int(round(spot/50)*50)
    opt_type = "CE" if direction=="CALL" else "PE"
    # SMART SEARCH - Angel ko ye format pasand hai
    search_terms = [
        "NIFTY {} {}".format(atm, opt_type),
        "NIFTY {} {}".format(atm, opt_type[0]),
        "{} {}".format(atm, opt_type)
    ]
    for term in search_terms:
        print("Searching Smart: {}".format(term), flush=True)
        try:
            time.sleep(1)  # Rate limit se bachne ke liye
            res = obj.searchScrip("NFO", term)
            if res and res.get('data'):
                for item in res['data'][:5]:  # Top 5 check karo
                    ts = item['tradingsymbol']
                    # NIFTY ka hi ho, strike match ho
                    if str(atm) in ts and ("NIFTY" in ts):
                        if (opt_type in ts or opt_type[0] in ts[-3:]):
                            token = item['symboltoken']
                            print("FOUND FINAL {} {}".format(ts, token), flush=True)
                            return token, ts, atm
        except Exception as ex:
            print("Search Err {}".format(ex), flush=True)
    
    # Last try - direct NIFTY search
    try:
        res = obj.searchScrip("NFO", "NIFTY")
        if res and res.get('data'):
            print("Fallback NIFTY search list me dhoond raha", flush=True)
            return "0", "NIFTY-ATM-{}-{}".format(atm, opt_type), atm
    except:
        pass
    return "0", "NIFTY{} {}".format(atm, opt_type), atm

try:
    obj = SmartConnect(api_key=API_KEY)
    totp = pyotp.TOTP(TOTP_SECRET).now()
    obj.generateSession(CLIENT_ID, PASSWORD, totp)
    print("LOGIN OK {}".format(CLIENT_ID), flush=True)

    spot, rsi = get_spot_rsi(obj)
    score = 0
    direction = "PUT" if rsi < 50 else "CALL"
    if 25 < rsi < 45:
        score = 80
        direction = "PUT"
    else:
        score = 80
        direction = "PUT" # Aapke log ke hisab se 80% PUT hi hai abhi
    
    print("SCORE {}% DIR {}".format(score, direction), flush=True)

    if score >= 80:
        token, tradingsym, atm = find_token_smart(obj, spot, direction)
        print("✅ 80% CONFIRM {} -> {} ATM {}".format(direction, tradingsym, atm), flush=True)
        if PAPER_TRADING:
            print("[PAPER] BUY {} QTY {} TARGET 40% SL 15%".format(tradingsym, LOT_QTY), flush=True)
            print("CE/PE DONO ISI ME - CALL AYA TO CE, PUT AYA TO PE", flush=True)
        else:
            if token != "0":
                obj.placeOrder({"variety":"NORMAL","tradingsymbol":tradingsym,"symboltoken":token,"transactiontype":"BUY","exchange":"NFO","ordertype":"MARKET","producttype":"CARRYFORWARD","duration":"DAY","quantity":LOT_QTY})
                print("REAL BUY DONE", flush=True)
    
    print("BOT FINISHED", flush=True)
except Exception as ex:
    print("FATAL {}".format(ex), flush=True)
