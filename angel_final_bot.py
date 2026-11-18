import os, pyotp, time, pandas as pd
from SmartApi import SmartConnect
from datetime import datetime, timedelta

print("=== ANGEL FINAL BOT V32 - CE+PE REAL AUTO ===", flush=True)

# --- SECRETS ---
API_KEY = os.getenv("ANGEL_API_KEY")
CLIENT_ID = os.getenv("ANGEL_CLIENT_ID")
PASSWORD = os.getenv("ANGEL_PASSWORD")
TOTP_SECRET = os.getenv("ANGEL_TOTP_SECRET")

# --- SETTING - Yahaan se control karo ---
PAPER_TRADING = True   # Pehle True rakho test ke liye, Profit dekho fir False kar dena Real ke liye
LOT_QTY = 75           # NIFTY 1 Lot
TARGET_PCT = 40        # 40% Profit pe auto sell
SL_PCT = 15            # 15% Loss pe auto sell

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
        print(f"NIFTY SPOT: {spot} RSI: {rsi:.2f}", flush=True)
        return spot, rsi
    except Exception as e:
        print(f"Candle Error {e} -> Fallback", flush=True)
        return 25400, 33.0

def find_token(obj, spot, direction):
    today = datetime.now()
    days_ahead = (3 - today.weekday()) % 7
    if days_ahead == 0 and today.hour > 15: days_ahead = 7
    expiry = today + timedelta(days=days_ahead)
    expiry_str = expiry.strftime("%d%b%y").upper() # 20NOV25
    atm = int(round(spot/50)*50)
    opt_letter = "C" if direction=="CALL" else "P"
    
    symbols_to_try = [
        f"NIFTY{expiry_str}{atm}{opt_letter}",
        f"NIFTY{expiry_str}{atm}{'CE' if direction=='CALL' else 'PE'}",
        f"NIFTY {expiry_str} {atm} {opt_letter}E"
    ]
    for sym in symbols_to_try:
        print(f"Searching Token: {sym}", flush=True)
        try:
            res = obj.searchScrip("NFO", sym)
            if res and res.get('data') and len(res['data'])>0:
                token = res['data'][0]['symboltoken']
                tradingsym = res['data'][0]['tradingsymbol']
                print(f"FOUND: {tradingsym} TOKEN:{token}", flush=True)
                return token, tradingsym, atm
        except Exception as e:
            print(f"Search fail {e}", flush=True)
    print("Token Not Found Fallback use symbol", flush=True)
    return "0", f"NIFTY{expiry_str}{atm}{opt_letter}", atm

def exit_positions(obj):
    try:
        pos = obj.position()
        if not pos.get('data'): return False
        for p in pos['data']:
            if p['producttype']=='CARRYFORWARD' and float(p['netqty'])!=0:
                try:
                    ltp_data = obj.ltpData("NFO", p['tradingsymbol'], p['symboltoken'])
                    ltp = float(ltp_data['data']['ltp'])
                    buy = float(p['netprice'])
                    pnl = ((ltp-buy)/buy)*100
                    print(f"OPEN: {p['tradingsymbol']} QTY:{p['netqty']} PNL:{pnl:.1f}%", flush=True)
                    if pnl >= TARGET_PCT or pnl <= -SL_PCT:
                        print(f"EXIT TRIGGER PNL {pnl:.1f}% -> SELLING", flush=True)
                        if not PAPER_TRADING:
                            obj.placeOrder({"variety":"NORMAL","tradingsymbol":p['tradingsymbol'],"symboltoken":p['symboltoken'],"transactiontype":"SELL" if float(p['netqty'])>0 else "BUY","exchange":"NFO","ordertype":"MARKET","producttype":"CARRYFORWARD","duration":"DAY","quantity":abs(int(p['netqty']))})
                            print("EXIT ORDER PLACED", flush=True)
                        else:
                            print(f"[PAPER] EXIT {p['tradingsymbol']}", flush=True)
                        return True
                except Exception as e:
                    print(f"LTP Error {e}",
