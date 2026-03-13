import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY")
COINGECKO_HISTORY_HEADERS = {
    "accept": "application/json",
    "x-cg-demo-api-key": COINGECKO_API_KEY
}

def get_history_url(coin: str):
    return f"https://api.coingecko.com/api/v3/coins/{coin}/market_chart/range"

def get_top_coins_url(n: int):
    return f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page={n}&page=1"

def get_coin_url(coin: str):
    return (f"https://api.coingecko.com/api/v3/simple/price?vs_currencies=usd&ids={coin}&x_cg_demo_api_key={COINGECKO_API_KEY}")