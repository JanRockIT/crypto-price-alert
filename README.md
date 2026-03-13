# crypto-price-alert

A small Python project that fetches crypto market data from CoinGecko, analyzes price signals across multiple timeframes, and sends Telegram alerts when interesting conditions are detected.

## Features

- Fetch current and historical crypto prices from CoinGecko
- Analyze coins using simple multi-timeframe signal logic
- Monitor a single coin or many top coins
- Send Telegram notifications when a signal is triggered
- Keep API keys and secrets in environment variables

## Project Structure

```text
crypto-price-alert/
├── analyzing/
│   ├── analyze_btc.py
│   ├── analyze_functions.py
│   └── analyze_top_coins.py
├── coingecko_fetch/
│   ├── __init__.py
│   ├── fetch_functions.py
│   ├── main.py
│   └── top_coin_plots.ipynb
├── telegram_post/
│   └── send_functions.py
├── config.py
├── __init__.py
└── README.md
