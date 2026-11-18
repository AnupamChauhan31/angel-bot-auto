def find_option_token(obj, spot, direction):
    today = datetime.now()
    days_ahead = (3 - today.weekday()) % 7
    if days_ahead == 0 and today.hour > 15: days_ahead = 7
    expiry = today + timedelta(days=days_ahead)
    expiry_str = expiry.strftime("%d%b%y").upper() # 19NOV26
    
    atm = int(round(spot/50)*50)
    opt_letter = "C" if direction=="CALL" else "P"
    symbol = f"NIFTY{expiry_str}{atm}{opt_letter}"
    print(f"Searching: {symbol}")

    try:
        # Try 2 formats - C/P and CE/PE
        for sym in [symbol, f"NIFTY{expiry_str}{atm}{'CE' if direction=='CALL' else 'PE'}"]:
            res = obj.searchScrip("NFO", sym)
            if res and res.get('data') and len(res['data'])>0:
                token = res['data'][0]['symboltoken']
                tradingsym = res['data'][0]['tradingsymbol']
                print(f"FOUND {tradingsym} {token}")
                return token, tradingsym, atm
    except Exception as e:
        print(f"Search Error {e}")

    # Fallback: If search fails, try with option chain method
    try:
        # Use LTP to guess token is valid, Angel allows direct tradingsymbol
        return None, symbol, atm
    except:
        pass
    return None, symbol, atm
