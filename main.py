import requests
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("COINGECKO_API_KEY")

response = requests.get(f"https://api.coingecko.com/api/v3/simple/price?vs_currencies=usd&ids=bitcoin&x_cg_demo_api_key={api_key}")

print(response.json())