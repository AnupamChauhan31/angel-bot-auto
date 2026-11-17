
import os, requests, datetime, time
from datetime import datetime as dt
from SmartApi import SmartConnect
import pyotp

MIN_BALANCE = 2000
LOTS = 1
QTY_PER_LOT = 65

def get_balance(obj):
    try:
        r = obj.rmsLimit()
        avail = float(r['data']['availablecash'])
        print(f"BALANCE: {avail}")
        return avail
    except Exception as e:
        print(f"Balance Fail {e}")
        return 0

def get_fii():
    ce=0;pe=0;msg=""
    try:
        h={"User-Agent":"Mozilla/5.0"}
        s=requests.Session()
        s.get("https://www.nseindia.com",headers=h, timeout=10)
        r=s.get("https://www.nseindia.com/api/fiidiiTradeReco",headers=h, timeout=10)
        net=float(r['data'][0]['buyValue'])-float(r['data'][0]['sellValue'])
        msg+=f"FII:{net:.0f} "
        if net>1000: ce+=20; msg+="FII-BULLISH "
        elif net<-1000: pe+=20; msg+="FII-BEARISH "
        else: ce+=10; pe+=10; msg+="FII-NEUTRAL "
    except Exception as e:
        msg+=f"FIIFail-NEUTRAL "; ce=10; pe=10
        print(f"FII Error {e}")
    return ce,pe,msg

def get_oi_pcr():
    ce=0;pe=0;msg=""; max_vol=0; max_strike=25500; max_type="CE"
    try:
        h={"User-Agent":"Mozilla/5.0"}
        s=requests.Session()
        s.get("https://www.nseindia.com",headers=h, timeout=10)
        r=s.get("https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY",headers=h, timeout=10)
        data=r.json()
        ce_oi=0;pe_oi=0
        for d in data['records']['data']:
            strike = d['strikePrice']
            if 'CE' in d:
                ce_oi+=d['CE'].get('openInterest',0)
                vol = d['CE'].get('totalTradedVolume',0)
                if vol > max_vol:
                    max_vol=vol; max_strike=strike; max_type="CE"
            if 'PE' in d:
                pe_oi+=d['PE'].get('openInterest',0)
                vol = d['PE'].get('totalTradedVolume',0)
                if vol > max_vol:
                    max_vol=vol; max_strike=strike; max_type="PE"
        pcr=pe_oi/ce_oi if ce_oi>0 else 1
        msg+=f"PCR:{pcr:.2f} MAX_VOL:{max_strike}{max_type} VOL:{max_vol} "
        if pcr>1.05: pe+=20
        elif pcr<0.95: ce+=20
        else: ce+=10; pe+=10
    except Exception as e:
        print(f"OI Fail {e}"); ce=10; pe=10; msg+=f"OIFail "
    return ce,pe,msg,max_strike,max_vol,max_type

def get_direction():
    try:
        h={"User-Agent":"Mozilla/5.0"}
        s=requests.Session()
        s.get("https://www.nseindia.com",headers=h, timeout=10)
        r=s.get("https://www.nseindia.com/api/allIndices",headers=h, timeout=10)
        for idx in r.json():
            if idx['index'] == 'NIFTY 50':
                change = idx['percentChange']
                if change > 0: return "BULLISH", f"NIFTY {change}%"
                else: return "BEARISH", f"NIFTY {change}%"
        return "BULLISH", "Default BULLISH"
    except:
        return "BULLISH", "DIR Default"

def main():
    print("=== ANGEL BOT AUTO START ===")
    try:
        api_key = os.getenv("ANGEL_API_KEY"); client_id = os.getenv("ANGEL_CLIENT_ID")
        pwd = os.getenv("ANGEL_PASSWORD"); totp_secret = os.getenv("ANGEL_TOTP_SECRET")
        totp = pyotp.TOTP(totp_secret).now()
        obj = SmartConnect(api_key=api_key)
        data = obj.generateSession(client_id, pwd, totp)
        print("Login Success")
        bal = get_balance(obj)
        if bal < MIN_BALANCE:
            print(f"Balance Low {bal}"); return
    except Exception as e:
        print(f"Login Fail {e}"); return

    fii_ce, fii_pe, fii_msg = get_fii()
    oi_ce, oi_pe, oi_msg, max_strike, max_vol, max_type = get_oi_pcr()
    direction, dir_msg = get_direction()

    print(f"{fii_msg} | {oi_msg} | {dir_msg} | DIR:{direction}")
    print(f"FINAL MAX VOLUME STRIKE: {max_strike} {max_type} VOL:{max_vol}")

    qty = LOTS * QTY_PER_LOT
    if direction == "BULLISH":
        if (oi_ce >= 10 or fii_ce >= 10) and max_vol > 0:
            print(f"TRIGGER CE: {max_strike}CE QTY {qty} - MAX VOL LOGIC")
    if direction == "BEARISH":
        if (oi_pe >= 10 or fii_pe >= 10) and max_vol > 0:
            print(f"TRIGGER PE: {max_strike}PE QTY {qty} - MAX VOL LOGIC")
    print("=== BOT END ===")

if __name__ == "__main__":
    main()
