
import os, requests
from SmartApi import SmartConnect
import pyotp

MIN_BALANCE = 2000
LOTS = 1
QTY_PER_LOT = 65
STRONG_PERCENT = 80

def get_balance(obj):
    try: return float(obj.rmsLimit()['data']['availablecash'])
    except: return 0

def get_fii():
    try:
        h={"User-Agent":"Mozilla/5.0"}
        s=requests.Session()
        s.get("https://www.nseindia.com",headers=h,timeout=10)
        r=s.get("https://www.nseindia.com/api/fiidiiTradeReco",headers=h,timeout=10)
        net=float(r.json()['data'][0]['buyValue'])-float(r.json()['data'][0]['sellValue'])
        if net>1000: return 20,0,f"FII:{net:.0f} BULL"
        if net<-1000: return 0,20,f"FII:{net:.0f} BEAR"
        return 10,10,f"FII:{net:.0f} NEU"
    except: return 10,10,"FII:NEU"

def get_oi_with_max_volume():
    max_ce_vol=0; max_pe_vol=0
    max_ce_strike=0; max_pe_strike=0
    ce_oi=0; pe_oi=0
    try:
        h={"User-Agent":"Mozilla/5.0"}
        s=requests.Session()
        s.get("https://www.nseindia.com",headers=h,timeout=10)
        r=s.get("https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY",headers=h,timeout=10)
        for d in r.json()['records']['data']:
            if 'CE' in d:
                ce_oi+=d['CE'].get('openInterest',0)
                v=d['CE'].get('totalTradedVolume',0)
                if v>max_ce_vol: max_ce_vol=v; max_ce_strike=d['strikePrice']
            if 'PE' in d:
                pe_oi+=d['PE'].get('openInterest',0)
                v=d['PE'].get('totalTradedVolume',0)
                if v>max_pe_vol: max_pe_vol=v; max_pe_strike=d['strikePrice']
        pcr=pe_oi/ce_oi if ce_oi>0 else 1
        if pcr>1.2: oi_ce,oi_pe=0,20
        elif pcr<0.8: oi_ce,oi_pe=20,0
        else: oi_ce,oi_pe=10,10
        msg=f"PCR:{pcr:.2f} MAX_CE:{max_ce_strike}({max_ce_vol}) MAX_PE:{max_pe_strike}({max_pe_vol})"
        return oi_ce,oi_pe,msg,max_ce_strike,max_ce_vol,max_pe_strike,max_pe_vol
    except Exception as e:
        return 10,10,f"OI Error {e}",0,0,0,0

def main():
    print("=== 80% + MAX VOLUME BOT ===")
    try:
        obj=SmartConnect(api_key=os.getenv("ANGEL_API_KEY"))
        obj.generateSession(os.getenv("ANGEL_CLIENT_ID"),os.getenv("ANGEL_PASSWORD"),pyotp.TOTP(os.getenv("ANGEL_TOTP_SECRET")).now())
        print("LoginOK")
    except Exception as e: print(f"Login Fail {e}"); return
    bal=get_balance(obj)
    print(f"BALANCE:{bal}")
    if bal<MIN_BALANCE: print("Low Balance"); return
    fii_ce,fii_pe,fii_msg=get_fii()
    oi_ce,oi_pe,oi_msg,c_strike,c_vol,p_strike,p_vol=get_oi_with_max_volume()
    total_ce=fii_ce+oi_ce
    total_pe=fii_pe+oi_pe
    total=total_ce+total_pe
    ce_per=(total_ce/total*100) if total>0 else 50
    pe_per=(total_pe/total*100) if total>0 else 50
    print(f"{fii_msg} | {oi_msg}")
    print(f"DIR: CE {ce_per:.0f}% | PE {pe_per:.0f}%")
    if ce_per>=STRONG_PERCENT and c_vol>0:
        print(f"FINAL TRADE: {c_strike}CE QTY:{LOTS*QTY_PER_LOT} REASON: STRONG BULL {ce_per:.0f}% + MAX_VOL {c_vol}")
    elif pe_per>=STRONG_PERCENT and p_vol>0:
        print(f"FINAL TRADE: {p_strike}PE QTY:{LOTS*QTY_PER_LOT} REASON: STRONG BEAR {pe_per:.0f}% + MAX_VOL {p_vol}")
    else:
        print(f"NO TRADE: WEAK {ce_per:.0f}%/{pe_per:.0f}% <80% - Capital Safe")

if __name__=="__main__": main()
