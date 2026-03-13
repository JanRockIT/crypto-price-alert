import requests
from datetime import datetime
import time
from config import get_history_url, COINGECKO_HISTORY_HEADERS, get_top_coins_url, get_coin_url

def date_to_unix(date_string: str):
    dt = datetime.strptime(date_string, "%Y-%m-%d")
    return int(dt.timestamp())

def get_history_data(start_date: int=date_to_unix("2025-6-15"), coin: str="ethereum", currency: str="usd", end_date: int=time.time()):
    params = {
        "vs_currency": currency,
        "from": start_date,
        "to": end_date
    }
    
    response = requests.get(
        get_history_url(coin),
        headers=COINGECKO_HISTORY_HEADERS,
        params=params
    )

    if not response.ok:
        return {"error": True, "data": None}
    
    data = response.json()

    return {"error": False, "data": data}

def get_top_coins(n: int=5, currency: str="usd"):
    response = requests.get(get_top_coins_url(n, currency))

    if not response.ok:
        return { "error": True, "data": None }
    
    data = response.json()

    return { "error": False, "data": data }
    # [coin["id"] for coin in data]

def get_coin_data(coin: str, currency: str="usd"):
    response = requests.get(get_coin_url(coin, currency))

    if not response.ok:
        return { "error": True, "data": None }
    
    data = response.json()

    return { "error": False, "data": data }

if __name__ == "__main__":
    print(
        get_top_coins()
    )