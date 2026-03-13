import requests
import os
from dotenv import load_dotenv
import time
from fetch_coin_historys.fetch_functions import get_top_coins, get_history_range, date_to_unix
load_dotenv()
api_key = os.getenv("COINGECKO_API_KEY")

while True:
    top_coins = get_top_coins(5)
    print(top_coins)

    end_date = time.time()
    start_date = end_date - 364 * 24 * 60 * 60
    
    prices_now = {}
    for coin in top_coins:
        response = requests.get(f"https://api.coingecko.com/api/v3/simple/price?vs_currencies=usd&ids={coin}&x_cg_demo_api_key={api_key}")
        prices_now[coin] = response
    
    print(prices_now)

    time.sleep(10)