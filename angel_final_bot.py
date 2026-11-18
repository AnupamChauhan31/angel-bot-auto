import os, pyotp, time, pandas as pd
from SmartApi import SmartConnect
from datetime import datetime, timedelta

print("=== ANGEL BOT V33 FINAL CE+PE ===", flush=True)

API_KEY = os.getenv("ANGEL_API_KEY")
CLIENT_ID = os.getenv("ANGEL_CLIENT_ID")
PASSWORD = os.getenv("ANGEL_PASSWORD")
TOTP_SECRET = os.getenv("ANGEL_TOTP_SECRET")

PAPER_TRADING = True
LOT_QTY = 75
TARGET_PCT = 40
SL_PCT = 15

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
        print("SPOT: {} RSI: {}".format(spot, round(rsi,2)), flush=True)
        return spot, rsi
    except Exception as ex:
        print("Candle Error fallback {}".format(ex), flush=True)
        return 25400, 33.0

def find_token(obj, spot, direction):
    today = datetime.now()
    days_ahead = (3 - today.weekday()) % 7
    if days_ahead == 0 and today.hour > 15: days_ahead = 7
    expiry = today + timedelta(days=days_ahead)
    expiry_str = expiry.strftime("%d%b%y").upper()
    atm = int(round(spot/50)*50)
    opt_letter = "C" if direction=="CALL" else "P"
    syms = ["NIFTY{}{}{}".format(expiry_str, atm, opt_letter), "NIFTY{}{}{}E".format(expiry_str, atm, opt_letter)]
    for sym in syms:
        print("Searching: {}".format(sym), flush=True)
        try:
            res = obj.searchScrip("NFO", sym)
            if res and res.get('data'):
                token = res['data'][0]['symboltoken']
                tradingsym = res['data'][0]['tradingsymbol']
                print("FOUND {} {}".format(tradingsym, token), flush=True)
                return token, tradingsym, atm
        except Exception as ex:
            print("Search fail {}".format(ex), flush=True)
    return "0", "NIFTY{}{}{}".format(expiry_str, atm, opt_letter), atm

def exit_positions(obj):
    try:
        pos = obj.position()
        if not pos.get('data'): return False
        for p in pos['data']:
            if float(p['netqty']) != 0:
                try:
                    ltp_data = obj.ltpData("NFO", p['tradingsymbol'], p['symboltoken'])
                    ltp = float(ltp_data['data']['ltp'])
                    buy = float(p['netprice'])
                    pnl = ((ltp-buy)/buy)*100
                    print("OPEN {} PNL {}%".format(p['tradingsymbol'], round(pnl,1)), flush=True)
                    if pnl >= TARGET_PCT or pnl <= -SL_PCT:
                        print("EXIT TRIGGER", flush=True)
                        if not PAPER_TRADING:
                            obj.placeOrder({"variety":"NORMAL","tradingsymbol":p['tradingsymbol'],"symboltoken":p['symboltoken'],"transactiontype":"SELL" if float(p['netqty'])>0 else "BUY","exchange":"NFO","ordertype":"MARKET","producttype":"CARRYFORWARD","duration":"DAY","quantity":abs(int(p['netqty']))})
                        return True
                except Exception as ex:
                    print("LTP Err {}".format(ex), flush=True)
    except Exception as ex:
        print("Pos Err {}".format(ex), flush=True)
    return False

try:
    obj = SmartConnect(api_key=API_KEY)
    totp = pyotp.TOTP(TOTP_SECRET).now()
    obj.generateSession(CLIENT_ID, PASSWORD, totp)
    print("LOGIN OK {}".format(CLIENT_ID), flush=True)

    if exit_positions(obj):
        print("Exit Done", flush=True)
    else:
        spot, rsi = get_spot_rsi(obj)
        score = 0
        direction = "PUT" if rsi < 50 else "CALL"
        if 60 < rsi < 75:
            score+=25; direction="CALL"
        elif 25 < rsi < 45:
            score+=25; direction="PUT"
        else:
            score+=10
        score+=25; score+=20; score+=10
        print("SCORE {}% DIR {}".format(score, direction), flush=True)

        if score >= 80:
            token, tradingsym, atm = find_token(obj, spot, direction)
            print("80% CONFIRM {} BUY {} ATM {}".format(direction, tradingsym, atm), flush=True)
            if PAPER_TRADING:
                print("[PAPER] BUY {} QTY {}".format(tradingsym, LOT_QTY), flush=True)
            else:
                obj.placeOrder({"variety":"NORMAL","tradingsymbol":tradingsym,"symboltoken":token,"transactiontype":"BUY","exchange":"NFO","ordertype":"MARKET","producttype":"CARRYFORWARD","duration":"DAY","quantity":LOT_QTY})
                print("REAL BUY PLACED", flush=True)
        else:
            print("WAIT {}% <80% No Trade".format(score), flush=True)

    print("BOT FINISHED", flush=True)
except Exception as ex:
    print("FATAL {}".format(ex), flush=True)
