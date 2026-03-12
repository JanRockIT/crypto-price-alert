import requests
from datetime import datetime
import time
from config import get_headers

def date_to_unix(date_string):
    dt = datetime.strptime(date_string, "%Y-%m-%d")
    return int(dt.timestamp())

def get_history_range(start_date=date_to_unix("2025-6-15"), end_date=time.time(), coin="bitcoin", currency="usd"):
    params = {
        "vs_currency": currency,
        "from": start_date,
        "to": end_date
    }
    
    response = requests.get("https://api.coingecko.com/api/v3/coins/bitcoin/market_chart/range", headers=get_headers(), params=params)
    data = response.json()

    return data

print(
    get_history_range()
)