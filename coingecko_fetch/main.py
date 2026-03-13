from fetch_functions import get_history_range, date_to_unix, get_top_coins
import time

CURRENCY = "usd"
N_TOP_COINS = 5

end_date = time.time()
start_date = end_date - 360 * 24 * 60 * 60

top_coins = get_top_coins(N_TOP_COINS)

# top_coin_historys = []

for coin in top_coins:
    try:
        coin_history = get_history_range(start_date, coin, CURRENCY, end_date)
        coin_history = coin_history["prices"]
    except Exception as e:
        print(f"error at coin: {coin}, error: {e}")
        continue

    prices = [price[1] for price in coin_history]
    average_price = sum(prices)

    # TODO: find a good location for this file and finish this snipped
    