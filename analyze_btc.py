from coingecko_fetch.fetch_functions import get_history_data, get_coin_data
import time
# doing the process just for bitcoin

COIN = "bitcoin"
CURRENCY = "usd"
# get the coin history

history_data = get_history_data(
    start_date=time.time() - 360*24*60*60,
    end_date=time.time(),
    coin=COIN,
    currency=CURRENCY
)

if history_data["error"]:
    print(history_data)
    exit()

history_prices = [i[1] for i in history_data["data"]["prices"]]

# get the current coin price

coin_data_now = get_coin_data(COIN, CURRENCY)
coin_price_now = coin_data_now["data"][COIN][CURRENCY]

#  compare
history_average_year = sum(history_prices[:360]) / len(history_prices)
history_average_6_months = sum(history_prices[:180]) / 180
history_average_month = sum(history_prices[:30]) / 30
history_average_week = sum(history_prices[:7]) / 7

print(f"""
    {history_average_year=},
    {history_average_6_months=},
    {history_average_month=},
    {history_average_week=}
""")