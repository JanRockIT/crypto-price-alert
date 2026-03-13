# import requests
# import os
# from dotenv import load_dotenv
# import time
# from coingecko_fetch.fetch_functions import get_top_coins, get_history_range, date_to_unix

# load_dotenv()
# api_key = os.getenv("COINGECKO_API_KEY")

# # while True:
# if True:
#     top_coins = get_top_coins(10)

#     end_date = time.time()
#     start_date = end_date - 364 * 24 * 60 * 60
    
#     prices_now = {}
#     for coin in top_coins:
#         response = requests.get(f"https://api.coingecko.com/api/v3/simple/price?vs_currencies=usd&ids={coin}&x_cg_demo_api_key={api_key}")
#         if response.status_code == "429":
#             print("canceled at", coin)
#             break
#         price = response.json()[coin]["usd"]
#         prices_now[coin] = price

#     print(prices_now)
#     for coin in top_coins:
#         try:
#             coin_history = get_history_range(start_date, coin, "usd", end_date)
#             coin_history = coin_history["prices"]
#         except Exception as e:
#             print(f"error at coin: {coin}, error: {e}")
#             continue
        
#         prices = [price[1] for price in coin_history]
#         average_price = sum(prices) / len(prices)

#         print(coin, prices_now[coin], average_price)

#         if prices_now[coin] < average_price / 2:
#             print(coin, "ist gerade günstiger als der halbe durchschnitt der letzten 364 tage")

