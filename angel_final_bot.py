
import os, requests, datetime
from datetime import datetime as dt
from SmartApi import SmartConnect
import pyotp
MIN_BALANCE=2000
def get_fii():
 ce=0;pe=0;msg=""
 try:
  h={"User-Agent":"Mozilla/5.0"}
  s=requests.Session()
  s.get("https://www.nseindia.com",headers=h,timeout=10)
  r=s.get("https://www.nseindia.com/api/fiidiiTradeReco",headers=h,timeout=10).json()
  net=float(r['data'][0]['buyValue'])-float(r['data'][0]['sellValue'])
  msg+=f"FII{net:.0f} "
  if net>1000: ce+=20
  elif net<-1000: pe+=20
 except: msg+=f"FIIFail "
 return ce,pe,msg
def get_oi():
 ce=0;pe=0;msg=""
 try:
  h={"User-Agent":"Mozilla/5.0"}
  s=requests.Session()
  s.get("https://www.nseindia.com",headers=h,timeout=10)
  r=s.get("https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY",headers=h,timeout=10).json()
  ce_oi=0;pe_oi=0
  for d in r['records']['data'][:20]:
   if 'CE' in d: ce_oi+=d['CE']['openInterest']
   if 'PE' in d: pe_oi+=d['PE']['openInterest']
  pcr=pe_oi/ce_oi if ce_oi>0 else 1
  msg+=f"PCR{pcr:.2f} "
  if pcr>1.25: ce+=20
  elif pcr<0.85: pe+=20
 except: msg+=f"OIFail "
 return ce,pe,msg
def get_dir(obj):
 ce=0;pe=0;msg=""
 try:
  n=obj.ltpData("NSE","NIFTY","99926000")
  ltp=n['data']['ltp']
  today=datetime.date.today().strftime("%Y-%m-%d")
  p={"exchange":"NSE","symboltoken":"99926000","interval":"FIVE_MINUTE","fromdate":f"{today} 09:15","todate":f"{today} 09:45"}
  c=obj.getCandleData(p)
  o=c['data'][0][1]
  diff=ltp-o
  msg+=f"Diff{diff:.1f} "
  if diff>30: ce+=40
  elif diff<-30: pe+=40
 except: msg+=f"DirFail "
 return ce,pe,msg
print("===80PCT BOT START===")
now=dt.now()
if now.weekday()>=5: print("Weekend");exit()
obj=SmartConnect(api_key=os.getenv("ANGEL_API_KEY"))
data=obj.generateSession(os.getenv("ANGEL_CLIENT_ID"),os.getenv("ANGEL_PASSWORD"),pyotp.TOTP(os.getenv("ANGEL_TOTP_SECRET")).now())
if not data['status']: print(f"LoginFail{data}");exit()
print("LoginOK")
ce1,pe1,m1=get_fii()
ce2,pe2,m2=get_oi()
ce3,pe3,m3=get_dir(obj)
tc=ce1+ce2+ce3
tp=pe1+pe2+pe3
print(f"{m1}|{m2}|{m3}")
print(f"CE{tc}% PE{tp}%")
if tc>=80: print(f"FINAL BUY CALL {tc}%")
elif tp>=80: print(f"FINAL BUY PUT {tp}%")
else: print(f"FINAL NO TRADE CE{tc} PE{tp}")
