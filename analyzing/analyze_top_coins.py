from coingecko_fetch.fetch_functions import get_top_coins, get_history_data, get_coin_data
import time
from analyze_functions import *
from telegram_post.send_functions import send_message

N = 10000
COINS = [coin["id"] for coin in get_top_coins(N, "usd")["data"]]
CURRENCY = "usd"

for i, coin in enumerate(COINS):
    history_data = get_history_data(
        start_date=time.time() - 360*24*60*60,
        end_date=time.time(),
        coin=coin,
        currency=CURRENCY
    )

    if history_data["error"]:
        print(history_data)
        exit()

    history_prices = [i[1] for i in history_data["data"]["prices"]]

    # get the current coin price

    coin_data_now = get_coin_data(coin, CURRENCY)
    coin_price_now = coin_data_now["data"][coin][CURRENCY]

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

    print("\n", i, "\n")

    signals = analyze_market_signals(
        history_average_year,
        history_average_6_months,
        history_average_month,
        history_average_week,
        coin_price_now
    )

    for key, value in signals.items():
        if value:
            print("!!!", coin, key, "!!!")
            send_message(f"! {coin} {key} {i=} !")
            break
    
    time.sleep(4)