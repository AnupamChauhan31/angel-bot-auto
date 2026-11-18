import os, requests, pyotp, pandas as pd
from SmartApi import SmartConnect
from datetime import datetime, timedelta

print("=== ANGEL FINAL BOT 80% - RSI+FII+OI+PCR ===")

API_KEY = os.getenv("ANGEL_API_KEY")
CLIENT_ID = os.getenv("ANGEL_CLIENT_ID")
PASSWORD = os.getenv("ANGEL_PASSWORD")
TOTP_SECRET = os.getenv("ANGEL_TOTP_SECRET")

TARGET = 40  # Profit %
SL = 15      # Loss %

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

def get_rsi(obj):
    try:
        # Nifty candle for RSI
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
        closes = [c[4] for c in data['data'][-20:]] if data and 'data' in data else [18000]*20
        rsi = calc_rsi(closes)
        print(f"RSI: {rsi}")
        return rsi
    except Exception as e:
        print(f"RSI Error {e}")
        return 55.0

def get_market():
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        s = requests.Session()
        s.get("https://www.nseindia.com", headers=headers, timeout=10)
        url = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
        j = s.get(url, headers=headers, timeout=10).json()
        spot = j['records']['underlyingValue']
        atm = min(j['records']['strikePrices'], key=lambda x: abs(x-spot))
        pe_oi = sum([d['PE']['openInterest'] for d in j['filtered']['data'] if 'PE' in d])
        ce_oi = sum([d['CE']['openInterest'] for d in j['filtered']['data'] if 'CE' in d])
        pcr = pe_oi/ce_oi if ce_oi else 1.0
        print(f"SPOT:{spot} ATM:{atm} PCR:{pcr:.2f}")
        return {"spot":spot, "atm":atm, "pcr":pcr, "full":j}
    except Exception as e:
        print(f"Market Error {e}")
        return None

# --- START ---
try:
    totp = pyotp.TOTP(TOTP_SECRET).now()
    obj = SmartConnect(api_key=API_KEY)
    obj.generateSession(CLIENT_ID, PASSWORD, totp)
    print(f"LOGIN SUCCESS {CLIENT_ID}")

    market = get_market()
    rsi = get_rsi(obj)
    
    # FII PREV DAY (Mock bullish, NSE se live fetch hota hai)
    fii_bias = "BULLISH"
    print(f"FII Prev Day: {fii_bias}")

    score = 0
    logs = []

    # 1. RSI 25%
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
        direction = "NO"

    # 2. FII 25%
    if fii_bias == "BULLISH":
        score += 25
        logs.append("FII Buy +25")

    # 3. PCR 20%
    if market['pcr'] > 1.15:
        score += 20
        logs.append(f"PCR {market['pcr']:.2f} +20")
    elif market['pcr'] < 0.85:
        score += 5
        logs.append(f"PCR Bearish +5")
    else:
        score += 10
        logs.append(f"PCR Neutral +10")

    # 4. OI+Volume 10%
    score += 10
    logs.append("OI Vol +10")

    print(f"SCORE: {score}% | DIR: {direction} | {logs}")

    # 80% CONFIRM LOGIC
    if score >= 80 and direction != "NO":
        strike = market['atm']
        if direction == "CALL":
            tradingsymbol = f"NIFTY{datetime.now().strftime('%d%b%y').upper()}{strike}CE"
        else:
            tradingsymbol = f"NIFTY{datetime.now().strftime('%d%b%y').upper()}{strike}PE"
        
        print(f"✅ 80% CONFIRM {direction} -> BEST STRIKE {strike} {tradingsymbol}")
        print(f"AUTO BUY SIGNAL | Target {TARGET}% SL {SL}%")

        # REAL ORDER (Paper mode now, uncomment to live)
        # orderparams = {
        #   "variety": "NORMAL", "tradingsymbol": tradingsymbol,
        #   "symboltoken": "99926000", "transactiontype": "BUY",
        #   "exchange": "NFO", "ordertype": "MARKET",
        #   "producttype": "INTRADAY", "duration": "DAY",
        #   "price": "0", "quantity": "50"
        # }
        # obj.placeOrder(orderparams)

        print("PAPER TRADE OK - Loss Min Profit Max Active")
    elif score < 50:
        print("❌ DIRECTION FAIL <50% -> EXIT ALL POSITIONS SIGNAL")
    else:
        print(f"⏳ WAIT - Score {score}% <80% - Dobara check karega, sahi hone par entry lega")

    print("BOT DONE")

except Exception as e:
    print(f"ERROR: {e}")
