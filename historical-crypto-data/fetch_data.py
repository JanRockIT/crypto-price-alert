import requests
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("COINGECKO_API_KEY")
BASE_URL = "https://api.coingecko.com/api/v3"
endpoint = f"{BASE_URL}/coins/bitcoin/market_chart/range"

def date_to_unix(date_string):
    dt = datetime.strptime(date_string, "%Y-%m-%d")
    return int(dt.timestamp())
def get_headers():
    return {
        "accept": "application/json",
        "x-cg-demo-api-key": api_key
    }
params = {
        "vs_currency": "usd",
        "from": date_to_unix("2025-04-3"),
        "to": date_to_unix("2026-03-03")
}

response = requests.get(endpoint, headers=get_headers(), params=params)
data = response.json()

print(data)