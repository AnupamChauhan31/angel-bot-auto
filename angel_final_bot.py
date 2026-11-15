
import os
from SmartApi import SmartConnect
import pyotp
import datetime

API_KEY = os.getenv("API_KEY")
CLIENT_ID = os.getenv("CLIENT_ID")
PASSWORD = os.getenv("PASSWORD")
TOTP_SECRET = os.getenv("TOTP_SECRET")

MIN_BALANCE = 2000

def main():
    try:
        now = datetime.datetime.now()
        if now.weekday() >= 5:
            print(f"Market Closed - {now.strftime('%A')} hai. Bot exit. No trade today.")
            return
        
        totp = pyotp.TOTP(TOTP_SECRET).now()
        smartApi = SmartConnect(API_KEY)
        data = smartApi.generateSession(CLIENT_ID, PASSWORD, totp)
        print("Login Success!")

        rms = smartApi.getRMS()
        print(f"RMS Response: {rms}")

        if not rms or not rms.get('data') or rms['data'] is None:
            print("Market Closed or RMS data None - Sunday/Holiday. Bot exit safely.")
            return

        try:
            available = float(rms['data'].get('availablecash') or rms['data'].get('availableCash') or rms['data'].get('net') or 0)
        except:
            available = 0
        
        print(f"Balance: {available}")

        if available < MIN_BALANCE:
            print(f"Balance low {available} < {MIN_BALANCE}. No trade.")
            return

        print("Safety OK - Ready for Trading")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
