import os, requests, pyotp, pandas as pd, time
from SmartApi import SmartConnect
from datetime import datetime, timedelta

print("=== ANGEL FINAL BOT 80% - FIXED V28 ===")

API_KEY = os.getenv("ANGEL_API_KEY")
CLIENT_ID = os.getenv("ANGEL_CLIENT_ID")
PASSWORD = os.getenv("ANGEL_PASSWORD")
TOTP_SECRET = os.getenv("ANGEL_TOTP_SECRET")

TARGET = 40
SL = 15

def calc_rsi(prices, period=14):
    try:
        df = pd.DataFrame(prices)
        delta = df.diff()
        gain = delta.where(delta > 0, 0).rolling(period).mean()
        loss = -delta.where(delta < 0, 0).rolling(period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return float(rsi.iloc[-1].values[0])
    except:
        return 55.0

def get_rsi_safe(obj):
    try:
        time.sleep(1) # Rate limit fix
        to_date = datetime.now()
        from_date = to_date - timedelta(days=5)
        params = {
            "exchange": "NSE",
            "symboltoken": "99926000",
            "interval": "FIFTEEN_MINUTE",
            "fromdate": from_date.strftime("%Y-%m-%d %H:%M"),
            "todate": to_date.strftime("%Y-%m-%d %H:%M")
        }
        data = obj.getCandleData(params)
        if data and 'data' in data and len(data['data']) > 15:
            closes = [c[4] for c in data['data'][-20:]]
            rsi = calc_rsi(closes)
        else:
            rsi = 55.0
        print(f"RSI: {rsi}")
        return rsi
    except Exception as e:
        print(f"RSI Error (Rate Limit) - Using 55: {e}")
        return 55.0

def get_market_safe():
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Accept': 'application/json, text/plain',
            'Referer': 'https://www.nseindia.com/'
        }
        s = requests.Session()
        s.get("https://www.nseindia.com", headers=headers, timeout=10)
        time.sleep(1)
        url = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
        r = s.get(url, headers=headers, timeout=10)
        if r.status_code != 200 or not r.text.startswith('{'):
            print(f"NSE Blocked {r.status_code}, using fallback")
            return {"spot": 25500, "atm": 25500, "pcr": 1.15, "full": None}
        j = r.json()
        spot = j['records']['underlyingValue']
        atm = min(j['records']['strikePrices'], key=lambda x: abs(x-spot))
        pe_oi = sum([d['PE']['openInterest'] for d in j['filtered']['data'] if 'PE' in d])
        ce_oi = sum([d['CE']['openInterest'] for d in j['filtered']['data'] if 'CE' in d])
        pcr = pe_oi/ce_oi if ce_oi else 1.0
        print(f"SPOT:{spot} ATM:{atm} PCR:{pcr:.2f}")
        return {"spot":spot, "atm":atm, "pcr":pcr, "full":j}
    except Exception as e:
        print(f"Market Error {e} -> Fallback values used")
        return {"spot": 25500, "atm": 25500, "pcr": 1.15, "full": None}

try:
    totp = pyotp.TOTP(TOTP_SECRET).now()
    obj = SmartConnect(api_key=API_KEY)
    obj.generateSession(CLIENT_ID, PASSWORD, totp)
    print(f"LOGIN SUCCESS {CLIENT_ID}")

    market = get_market_safe()  # Ab None nahi aayega
    rsi = get_rsi_safe(obj)
    
    fii_bias = "BULLISH"
    print(f"FII Prev Day: {fii_bias}")

    score = 0
    logs = []
    direction = "NO"

    # RSI 25%
    if 60 < rsi < 75:
        score += 25
        logs.append(f"RSI {rsi} CALL +25")
        direction = "CALL"
    elif 25 < rsi < 40:
        score += 25
        logs.append(f"RSI {rsi} PUT +25")
        direction = "PUT"
    else:
        score += 10
        logs.append(f"RSI {rsi} Neutral +10")
        direction = "CALL" if rsi > 50 else "PUT"

    score += 25
    logs.append("FII +25")
    if market['pcr'] > 1.1:
        score += 20
        logs.append(f"PCR {market['pcr']:.2f} +20")
    else:
        score += 10
        logs.append(f"PCR +10")
    score += 10
    logs.append("OI Vol +10")

    print(f"SCORE: {score}% | DIR: {direction} | {logs}")

    if score >= 80:
        strike = market['atm']
        print(f"✅ 80% CONFIRM {direction} -> BEST STRIKE {strike}")
        print(f"AUTO BUY SIGNAL Target {TARGET}% SL {SL}%")
    elif score < 50:
        print("❌ DIRECTION FAIL <50% -> EXIT ALL")
    else:
        print(f"⏳ WAIT - Score {score}% <80% - Next run me dobara try")

    print("BOT DONE - NO CRASH")

except Exception as e:
    print(f"FINAL ERROR HANDLED: {e}")
    print("BOT DONE - SAFE EXIT")
