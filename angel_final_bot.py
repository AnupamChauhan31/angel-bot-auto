
import os, requests, datetime, time
from datetime import datetime as dt
from SmartApi import SmartConnect
import pyotp

MIN_BALANCE = 2000
LOTS = 2
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
        s.get("https://www.nseindia.com",headers=h,timeout=10)
        r=s.get("https://www.nseindia.com/api/fiidiiTradeReco",headers=h,timeout=10).json()
        net=float(r['data'][0]['buyValue'])-float(r['data'][0]['sellValue'])
        msg+=f"FII:{net:.0f} "
        if net>1000: ce+=20
        elif net<-1000: pe+=20
    except Exception as e:
        msg+="FIIFail "
    return ce,pe,msg

def get_oi_pcr():
    ce=0;pe=0;msg=""
    try:
        h={"User-Agent":"Mozilla/5.0"}
        s=requests.Session()
        s.get("https://www.nseindia.com",headers=h,timeout=10)
        r=s.get("https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY",headers=h,timeout=10).json()
        ce_oi=0;pe_oi=0
        for d in r['records']['data'][:30]:
            if 'CE' in d: ce_oi+=d['CE']['openInterest']
            if 'PE' in d: pe_oi+=d['PE']['openInterest']
        pcr=pe_oi/ce_oi if ce_oi>0 else 1
        msg+=f"PCR:{pcr:.2f} "
        if pcr>1.25: ce+=20
        elif pcr<0.85: pe+=20
    except Exception as e:
        msg+="OIFail "
    return ce,pe,msg,r if 'r' in locals() else None

def get_direction(obj):
    ce=0;pe=0;msg=""; diff=0
    try:
        ltp = obj.ltpData("NSE","NIFTY","99926000")['data']['ltp']
        today=datetime.date.today().strftime("%Y-%m-%d")
        p={"exchange":"NSE","symboltoken":"99926000","interval":"FIVE_MINUTE","fromdate":f"{today} 09:15","todate":f"{today} 09:45"}
        c=obj.getCandleData(p)
        o=c['data'][0][1]
        diff=ltp-o
        msg+=f"Diff:{diff:.1f} "
        if diff>30: ce+=40
        elif diff<-30: pe+=40
    except:
        msg+="DirFail "
    return ce,pe,msg,diff

def get_best_strike(chain, spot, side):
    # side = CE or PE, Volume + OI se best strike
    best=None; max_score=0
    for d in chain['records']['data']:
        if side in d and 'strikePrice' in d:
            # ATM ke aas paas 3 strike me se best
            strike=d['strikePrice']
            if abs(strike-spot)>300: continue
            vol=d[side].get('totalTradedVolume',0)
            oi=d[side].get('openInterest',0)
            score=vol*0.6 + oi*0.4
            if score>max_score:
                max_score=score
                best=d
    if best:
        return best[side]['symbol'], best[side]['lastPrice'], best['strikePrice']
    return None,None,None

def monitor_and_exit(obj, symbol, token, buy_price, diff_start):
    target = buy_price * 1.3  # 30% target
    sl = buy_price * 0.7
    half_booked=False
    qty_total = LOTS*QTY_PER_LOT
    print(f"MONITOR START {symbol} Buy:{buy_price} Target:{target:.1f}")
    while True:
        try:
            ltp = obj.ltpData("NSE", symbol, token)['data']['ltp']
            # 1. Target check
            if not half_booked and ltp >= buy_price*1.15 and LOTS>=2:
                print(f"PARTIAL BOOK 50% at {ltp}")
                obj.placeOrder({"variety":"NORMAL","tradingsymbol":symbol,"symboltoken":token,"transactiontype":"SELL","exchange":"NFO","ordertype":"MARKET","producttype":"INTRADAY","duration":"DAY","quantity":QTY_PER_LOT})
                half_booked=True
            if ltp >= target:
                print(f"TARGET HIT {ltp} -> FULL EXIT")
                obj.placeOrder({"variety":"NORMAL","tradingsymbol":symbol,"symboltoken":token,"transactiontype":"SELL","exchange":"NFO","ordertype":"MARKET","producttype":"INTRADAY","duration":"DAY","quantity":qty_total-QTY_PER_LOT if half_booked else qty_total})
                break
            if ltp <= sl:
                print(f"SL HIT {ltp} -> EXIT")
                obj.placeOrder({"variety":"NORMAL","tradingsymbol":symbol,"symboltoken":token,"transactiontype":"SELL","exchange":"NFO","ordertype":"MARKET","producttype":"INTRADAY","duration":"DAY","quantity":qty_total-QTY_PER_LOT if half_booked else qty_total})
                break
            # 2. Direction fail check
            _,_,_,curr_diff = get_direction(obj)
            if diff_start>0 and curr_diff < 10: # CALL direction khatam
                print(f"DIRECTION KHATAM {curr_diff} -> EXIT")
                obj.placeOrder({"variety":"NORMAL","tradingsymbol":symbol,"symboltoken":token,"transactiontype":"SELL","exchange":"NFO","ordertype":"MARKET","producttype":"INTRADAY","duration":"DAY","quantity":qty_total-QTY_PER_LOT if half_booked else qty_total})
                break
            if diff_start<0 and curr_diff > -10: # PUT direction khatam
                print(f"DIRECTION KHATAM {curr_diff} -> EXIT")
                obj.placeOrder({"variety":"NORMAL","tradingsymbol":symbol,"symboltoken":token,"transactiontype":"SELL","exchange":"NFO","ordertype":"MARKET","producttype":"INTRADAY","duration":"DAY","quantity":qty_total-QTY_PER_LOT if half_booked else qty_total})
                break
            time.sleep(30)
        except Exception as e:
            print(f"Monitor Error {e}")
            time.sleep(10)

# ===== MAIN =====
print("===FINAL BOT WITH BALANCE+TGT+CLOSE===")
now=dt.now()
if now.weekday()>=5: print("Weekend");exit()

obj=SmartConnect(api_key=os.getenv("ANGEL_API_KEY"))
data=obj.generateSession(os.getenv("ANGEL_CLIENT_ID"),os.getenv("ANGEL_PASSWORD"),pyotp.TOTP(os.getenv("ANGEL_TOTP_SECRET")).now())
if not data['status']: print(f"LoginFail {data}");exit()
print("LoginOK")

bal = get_balance(obj)
if bal < MIN_BALANCE:
    print(f"LOW BALANCE {bal} < {MIN_BALANCE} -> NO TRADE")
    exit()

ce1,pe1,m1=get_fii()
ce2,pe2,m2,chain=get_oi_pcr()
ce3,pe3,m3,diff=get_direction(obj)

tc=ce1+ce2+ce3
tp=pe1+pe2+pe3
print(f"{m1}|{m2}|{m3}| CE:{tc}% PE:{tp}%")

side=None
if tc>=80: side="CE"
elif tp>=80: side="PE"
else:
    print(f"FINAL NO TRADE")
    exit()

spot = obj.ltpData("NSE","NIFTY","99926000")['data']['ltp']
sym, price, strike = get_best_strike(chain, spot, side)
if not sym:
    print("Strike Not Found")
    exit()

print(f"FINAL BUY {side} {strike} {sym} @ {price} Vol+OI Best")
# BUY ORDER
token = chain['records']['data'][0][side]['symbol'] # placeholder, will search correct token
# Find token for selected symbol
for d in chain['records']['data']:
    if d['strikePrice']==strike and side in d:
        token=str(d[side].get('identifier','')) # fallback search from ltpData? Use searchScrip
        # better search token via search
        break

# search token properly
search = obj.searchScrip("NFO", sym)
token = search['data'][0]['symboltoken'] if search['data'] else None
if not token:
    print("Token Fail")
    exit()

order = obj.placeOrder({"variety":"NORMAL","tradingsymbol":sym,"symboltoken":token,"transactiontype":"BUY","exchange":"NFO","ordertype":"MARKET","producttype":"INTRADAY","duration":"DAY","quantity":LOTS*QTY_PER_LOT})
print(f"ORDER PLACED {order}")

monitor_and_exit(obj, sym, token, price, diff)
