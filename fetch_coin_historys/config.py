import os
from dotenv import load_dotenv

load_dotenv()
COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY")

def get_headers():
    return {
        "accept": "application/json",
        "x-cg-demo-api-key": COINGECKO_API_KEY
    }
