import requests
from datetime import datetime
import time
from config import get_headers

def date_to_unix(date_string: str):
    dt = datetime.strptime(date_string, "%Y-%m-%d")
    return int(dt.timestamp())

def get_history_range(start_date: int=date_to_unix("2025-6-15"), coin: str="ethereum", currency: str="usd", end_date: int=time.time()):
    params = {
        "vs_currency": currency,
        "from": start_date,
        "to": end_date
    }
    
    response = requests.get(f"https://api.coingecko.com/api/v3/coins/{coin}/market_chart/range", headers=get_headers(), params=params)
    data = response.json()

    return data

def get_top_coins(n: int=10):
    response = requests.get(f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page={n}&page=1")
    data = response.json()
    return [coin["id"] for coin in data]

if __name__ == "__main__":
    print(
        get_top_coins()
    )