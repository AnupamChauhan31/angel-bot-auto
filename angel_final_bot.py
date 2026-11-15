import os
from SmartApi import SmartConnect
import pyotp

API_KEY = os.getenv("API_KEY")
CLIENT_ID = os.getenv("CLIENT_ID")
PASSWORD = os.getenv("PASSWORD")
TOTP_SECRET = os.getenv("TOTP_SECRET")

MIN_BALANCE = 2000

def main():
    try:
        totp = pyotp.TOTP(TOTP_SECRET).now()
        smartApi = SmartConnect(API_KEY)
        data = smartApi.generateSession(CLIENT_ID, PASSWORD, totp)
        print("Login Success!")
        
        rms = smartApi.getRMS()
        available = float(rms['data']['availablecash'])
        print(f"Balance: {available}")
        
        if available < MIN_BALANCE:
            print(f"Balance low {available} - No trade today")
            return
            
        print("Safety OK - Ready for Trading")
        # Aapka trading logic yahan add karenge
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
