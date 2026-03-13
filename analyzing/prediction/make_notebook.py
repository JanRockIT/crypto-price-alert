import json
import textwrap

def md_cell(text):
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": textwrap.dedent(text).strip("\n").splitlines(keepends=True)
    }

def code_cell(code):
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": textwrap.dedent(code).strip("\n").splitlines(keepends=True)
    }

cells = []

cells.append(md_cell("""
# Multi-Coin Crypto Forecasting Notebook

This notebook builds a shared deep learning model that learns from many cryptocurrencies at once and then evaluates how well it can predict the next-day return and the next-day close for a selected coin such as BTCUSDT.

## What this notebook does

1. Downloads daily OHLCV data from the public Binance REST API
2. Selects the most liquid USDT pairs
3. Engineers rolling features for every coin
4. Builds a panel dataset across many coins
5. Trains a Keras model on all coins together
6. Evaluates the model on one selected target coin
7. Visualizes:
   - market coverage
   - training curves
   - actual vs predicted returns
   - reconstructed price paths
   - rolling directional accuracy
   - prediction scatter plots

## Practical note

This notebook is intentionally written as a single run, end-to-end workflow with detailed documentation and plots.
Training on many symbols can take time. The defaults are chosen to be ambitious but still realistic for a home machine.

You only need to execute the cells from top to bottom.
"""))

cells.append(code_cell("""
%pip -q install pandas numpy matplotlib scikit-learn requests tqdm tensorflow joblib
"""))

cells.append(md_cell("""
## Configuration

You can change the values below if you want to trade off:
- more coins vs faster runtime
- longer history vs smaller memory use
- more epochs vs faster experiments
"""))

cells.append(code_cell("""
import math
import time
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import requests

from tqdm.auto import tqdm
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

warnings.filterwarnings("ignore")
plt.rcParams["figure.figsize"] = (12, 6)

SEED = 42
np.random.seed(SEED)
tf.random.set_seed(SEED)

MAX_SYMBOLS = 150
LOOKBACK_DAYS = 30
HISTORY_LIMIT = 500
MIN_HISTORY = 220
TARGET_SYMBOL = "BTCUSDT"
EPOCHS = 30
BATCH_SIZE = 512

TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
TEST_RATIO = 0.15

assert abs(TRAIN_RATIO + VAL_RATIO + TEST_RATIO - 1.0) < 1e-9

BINANCE_BASE = "https://api.binance.com"

print("TensorFlow version:", tf.__version__)
print("Target symbol:", TARGET_SYMBOL)
print("Maximum symbols:", MAX_SYMBOLS)
"""))

cells.append(md_cell("""
## Data download helpers

We use the public Binance REST API:
- exchangeInfo to discover tradable spot symbols
- ticker/24hr to rank symbols by liquidity
- klines to download daily candles

The selection strategy is simple and practical:
- keep USDT spot pairs
- exclude leveraged tokens and stablecoin bases
- sort by 24-hour quote volume
- keep the top MAX_SYMBOLS
"""))

cells.append(code_cell("""
def get_exchange_info():
    url = f"{BINANCE_BASE}/api/v3/exchangeInfo"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.json()

def get_24h_tickers():
    url = f"{BINANCE_BASE}/api/v3/ticker/24hr"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.json()

def is_clean_usdt_spot_symbol(symbol_row):
    symbol = symbol_row["symbol"]
    status = symbol_row.get("status")
    quote = symbol_row.get("quoteAsset")
    base = symbol_row.get("baseAsset")
    spot_allowed = symbol_row.get("isSpotTradingAllowed", False)

    banned_suffixes = ("UPUSDT", "DOWNUSDT", "BULLUSDT", "BEARUSDT")
    stable_bases = {"USDC", "FDUSD", "TUSD", "USDP", "BUSD", "DAI", "USDS", "EURI", "EUR"}

    if quote != "USDT":
        return False
    if status != "TRADING":
        return False
    if not spot_allowed:
        return False
    if symbol.endswith(banned_suffixes):
        return False
    if base in stable_bases:
        return False
    return True

def get_top_symbols(max_symbols=MAX_SYMBOLS):
    exchange = get_exchange_info()
    tickers = pd.DataFrame(get_24h_tickers())

    tradable = pd.DataFrame(exchange["symbols"])
    tradable = tradable[tradable.apply(is_clean_usdt_spot_symbol, axis=1)].copy()

    tickers["quoteVolume"] = pd.to_numeric(tickers["quoteVolume"], errors="coerce")
    tickers["volume"] = pd.to_numeric(tickers["volume"], errors="coerce")
    tickers = tickers[["symbol", "quoteVolume", "volume"]]

    merged = tradable.merge(tickers, on="symbol", how="left")
    merged["quoteVolume"] = merged["quoteVolume"].fillna(0.0)
    merged = merged.sort_values("quoteVolume", ascending=False)

    selected = merged["symbol"].head(max_symbols).tolist()

    if TARGET_SYMBOL not in selected and TARGET_SYMBOL in merged["symbol"].values:
        selected = [TARGET_SYMBOL] + [s for s in selected if s != TARGET_SYMBOL]
        selected = selected[:max_symbols]

    return selected, merged

def fetch_daily_klines(symbol, limit=HISTORY_LIMIT):
    url = f"{BINANCE_BASE}/api/v3/klines"
    params = {"symbol": symbol, "interval": "1d", "limit": limit}
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    raw = r.json()

    cols = [
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "num_trades",
        "taker_buy_base_volume", "taker_buy_quote_volume", "ignore"
    ]
    df = pd.DataFrame(raw, columns=cols)

    numeric_cols = [
        "open", "high", "low", "close", "volume",
        "quote_asset_volume", "taker_buy_base_volume", "taker_buy_quote_volume"
    ]
    for c in numeric_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    df["close_time"] = pd.to_datetime(df["close_time"], unit="ms", utc=True)
    df["symbol"] = symbol
    return df

symbols, symbol_table = get_top_symbols(MAX_SYMBOLS)
print(f"Selected {len(symbols)} symbols.")
print(symbols[:20], "...")
"""))

cells.append(code_cell("""
all_frames = []
failed_symbols = []

for symbol in tqdm(symbols, desc="Downloading daily candles"):
    try:
        df_sym = fetch_daily_klines(symbol, limit=HISTORY_LIMIT)
        if len(df_sym) >= MIN_HISTORY:
            all_frames.append(df_sym)
        else:
            failed_symbols.append((symbol, f"Too short: {len(df_sym)} rows"))
        time.sleep(0.02)
    except Exception as e:
        failed_symbols.append((symbol, str(e)[:120]))

raw_df = pd.concat(all_frames, ignore_index=True).sort_values(["symbol", "open_time"]).reset_index(drop=True)

print("Downloaded symbols:", raw_df["symbol"].nunique())
print("Rows:", len(raw_df))
print("Failures / skipped:", len(failed_symbols))
raw_df.head()
"""))

cells.append(md_cell("""
## Basic market coverage plots
"""))

cells.append(code_cell("""
coverage = raw_df.groupby("symbol").agg(
    rows=("close", "size"),
    first_date=("open_time", "min"),
    last_date=("open_time", "max"),
    last_close=("close", "last"),
    total_quote_volume=("quote_asset_volume", "sum")
).sort_values("total_quote_volume", ascending=False)

print(coverage.head(10))

fig, ax = plt.subplots()
coverage["rows"].hist(ax=ax, bins=30)
ax.set_title("Distribution of history length per symbol")
ax.set_xlabel("Number of daily candles")
ax.set_ylabel("Frequency")
plt.show()

top_liquidity = coverage.head(20).sort_values("total_quote_volume")
fig, ax = plt.subplots()
ax.barh(top_liquidity.index, top_liquidity["total_quote_volume"])
ax.set_title("Top 20 downloaded symbols by cumulative quote volume")
ax.set_xlabel("Cumulative quote volume")
ax.set_ylabel("Symbol")
plt.show()

sample_symbols = [s for s in ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT"] if s in raw_df["symbol"].unique()]
fig, ax = plt.subplots()
for s in sample_symbols:
    tmp = raw_df[raw_df["symbol"] == s].copy().sort_values("open_time")
    normalized = tmp["close"] / tmp["close"].iloc[0]
    ax.plot(tmp["open_time"], normalized, label=s)
ax.set_title("Normalized price comparison of selected large-cap coins")
ax.set_xlabel("Date")
ax.set_ylabel("Normalized close")
ax.legend()
plt.show()
"""))

cells.append(md_cell("""
## Feature engineering

The target is:

**next-day return = (close[t+1] / close[t]) - 1**

This is more stable than predicting the absolute next-day price directly.
"""))

cells.append(code_cell("""
def engineer_features(df):
    df = df.sort_values(["symbol", "open_time"]).copy()
    g = df.groupby("symbol", group_keys=False)

    df["log_close"] = np.log(df["close"])
    df["ret_1"] = g["close"].pct_change(1)
    df["ret_3"] = g["close"].pct_change(3)
    df["ret_7"] = g["close"].pct_change(7)
    df["ret_14"] = g["close"].pct_change(14)

    df["log_ret_1"] = g["log_close"].diff(1)
    df["vol_chg_1"] = g["volume"].pct_change(1)

    df["hl_range"] = (df["high"] - df["low"]) / df["close"]
    df["oc_range"] = (df["close"] - df["open"]) / df["open"]

    for w in [5, 10, 20, 30]:
        df[f"sma_{w}"] = g["close"].transform(lambda x: x.rolling(w).mean())
        df[f"std_{w}"] = g["ret_1"].transform(lambda x: x.rolling(w).std())
        df[f"vol_sma_{w}"] = g["volume"].transform(lambda x: x.rolling(w).mean())

    df["dist_sma_5"] = (df["close"] / df["sma_5"]) - 1
    df["dist_sma_10"] = (df["close"] / df["sma_10"]) - 1
    df["dist_sma_20"] = (df["close"] / df["sma_20"]) - 1
    df["dist_sma_30"] = (df["close"] / df["sma_30"]) - 1

    df["vol_rel_5"] = (df["volume"] / df["vol_sma_5"]) - 1
    df["vol_rel_20"] = (df["volume"] / df["vol_sma_20"]) - 1

    df["target_next_ret"] = g["close"].shift(-1) / df["close"] - 1
    df["next_close"] = g["close"].shift(-1)

    return df

feat_df = engineer_features(raw_df)

feature_cols = [
    "ret_1", "ret_3", "ret_7", "ret_14",
    "log_ret_1", "vol_chg_1",
    "hl_range", "oc_range",
    "std_5", "std_10", "std_20", "std_30",
    "dist_sma_5", "dist_sma_10", "dist_sma_20", "dist_sma_30",
    "vol_rel_5", "vol_rel_20"
]

needed = ["symbol", "open_time", "close"] + feature_cols + ["target_next_ret", "next_close"]
feat_df = feat_df[needed].replace([np.inf, -np.inf], np.nan)
feat_df = feat_df.dropna().reset_index(drop=True)

print("Feature rows after cleaning:", len(feat_df))
print("Symbols remaining:", feat_df["symbol"].nunique())
feat_df.head()
"""))

cells.append(md_cell("""
## Chronological split
"""))

cells.append(code_cell("""
split_frames = []

for symbol, grp in feat_df.groupby("symbol"):
    grp = grp.sort_values("open_time").reset_index(drop=True)
    n = len(grp)
    train_end = int(n * TRAIN_RATIO)
    val_end = int(n * (TRAIN_RATIO + VAL_RATIO))

    grp.loc[:train_end - 1, "split"] = "train"
    grp.loc[train_end:val_end - 1, "split"] = "val"
    grp.loc[val_end:, "split"] = "test"

    split_frames.append(grp)

split_df = pd.concat(split_frames, ignore_index=True)

train_mask = split_df["split"] == "train"
val_mask = split_df["split"] == "val"
test_mask = split_df["split"] == "test"

scaler = StandardScaler()
split_df.loc[train_mask, feature_cols] = scaler.fit_transform(split_df.loc[train_mask, feature_cols])
split_df.loc[val_mask, feature_cols] = scaler.transform(split_df.loc[val_mask, feature_cols])
split_df.loc[test_mask, feature_cols] = scaler.transform(split_df.loc[test_mask, feature_cols])

split_df.head()
"""))

cells.append(md_cell("""
## Sequence builder
"""))

cells.append(code_cell("""
def build_sequences(df, feature_cols, lookback=30):
    X, y, meta = [], [], []

    for symbol, grp in df.groupby("symbol"):
        grp = grp.sort_values("open_time").reset_index(drop=True)

        values = grp[feature_cols].values.astype(np.float32)
        targets = grp["target_next_ret"].values.astype(np.float32)

        dates = grp["open_time"].values
        closes = grp["close"].values.astype(np.float32)
        next_closes = grp["next_close"].values.astype(np.float32)
        splits = grp["split"].values

        for i in range(lookback, len(grp)):
            X.append(values[i - lookback:i])
            y.append(targets[i])
            meta.append({
                "symbol": symbol,
                "date": pd.Timestamp(dates[i]),
                "split": splits[i],
                "current_close": closes[i],
                "next_close": next_closes[i],
            })

    X = np.asarray(X, dtype=np.float32)
    y = np.asarray(y, dtype=np.float32)
    meta = pd.DataFrame(meta)
    return X, y, meta

X_all, y_all, meta_all = build_sequences(split_df, feature_cols, lookback=LOOKBACK_DAYS)

train_idx = meta_all["split"] == "train"
val_idx = meta_all["split"] == "val"
test_idx = meta_all["split"] == "test"

X_train, y_train = X_all[train_idx], y_all[train_idx]
X_val, y_val = X_all[val_idx], y_all[val_idx]
X_test, y_test = X_all[test_idx], y_all[test_idx]

print("X_train:", X_train.shape)
print("X_val:", X_val.shape)
print("X_test:", X_test.shape)
"""))

cells.append(md_cell("""
## Model
"""))

cells.append(code_cell("""
def build_model(lookback, n_features):
    model = keras.Sequential([
        layers.Input(shape=(lookback, n_features)),
        layers.Conv1D(filters=32, kernel_size=3, activation="relu", padding="causal"),
        layers.GRU(64, return_sequences=True),
        layers.Dropout(0.15),
        layers.GRU(32),
        layers.Dense(32, activation="relu"),
        layers.Dropout(0.10),
        layers.Dense(1, activation="linear")
    ])

    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=1e-3),
        loss=keras.losses.Huber(),
        metrics=[keras.metrics.MeanAbsoluteError(name="mae")]
    )
    return model

model = build_model(LOOKBACK_DAYS, len(feature_cols))
model.summary()
"""))

cells.append(code_cell("""
callbacks = [
    keras.callbacks.EarlyStopping(monitor="val_loss", patience=6, restore_best_weights=True),
    keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=3, min_lr=1e-5)
]

history = model.fit(
    X_train, y_train,
    validation_data=(X_val, y_val),
    epochs=EPOCHS,
    batch_size=BATCH_SIZE,
    callbacks=callbacks,
    verbose=1
)
"""))

cells.append(md_cell("""
## Training curves
"""))

cells.append(code_cell("""
hist_df = pd.DataFrame(history.history)

fig, ax = plt.subplots()
ax.plot(hist_df.index + 1, hist_df["loss"], label="Train loss")
ax.plot(hist_df.index + 1, hist_df["val_loss"], label="Validation loss")
ax.set_title("Training and validation loss")
ax.set_xlabel("Epoch")
ax.set_ylabel("Huber loss")
ax.legend()
plt.show()

fig, ax = plt.subplots()
ax.plot(hist_df.index + 1, hist_df["mae"], label="Train MAE")
ax.plot(hist_df.index + 1, hist_df["val_mae"], label="Validation MAE")
ax.set_title("Training and validation MAE")
ax.set_xlabel("Epoch")
ax.set_ylabel("Mean absolute error")
ax.legend()
plt.show()
"""))

cells.append(md_cell("""
## Predictions
"""))

cells.append(code_cell("""
pred_train = model.predict(X_train, verbose=0).reshape(-1)
pred_val = model.predict(X_val, verbose=0).reshape(-1)
pred_test = model.predict(X_test, verbose=0).reshape(-1)

pred_all = np.empty(len(meta_all), dtype=np.float32)
pred_all[train_idx.values] = pred_train
pred_all[val_idx.values] = pred_val
pred_all[test_idx.values] = pred_test

results = meta_all.copy()
results["actual_next_ret"] = y_all
results["pred_next_ret"] = pred_all
results["pred_next_close"] = results["current_close"] * (1.0 + results["pred_next_ret"])
results["actual_direction"] = np.sign(results["actual_next_ret"])
results["pred_direction"] = np.sign(results["pred_next_ret"])
results["direction_correct"] = (results["actual_direction"] == results["pred_direction"]).astype(int)

results.head()
"""))

cells.append(md_cell("""
## Global test metrics
"""))

cells.append(code_cell("""
test_results = results[results["split"] == "test"].copy()

test_mae = mean_absolute_error(test_results["actual_next_ret"], test_results["pred_next_ret"])
test_rmse = math.sqrt(mean_squared_error(test_results["actual_next_ret"], test_results["pred_next_ret"]))
test_dir_acc = test_results["direction_correct"].mean()

print("Global test return MAE:", round(test_mae, 6))
print("Global test return RMSE:", round(test_rmse, 6))
print("Global test direction accuracy:", round(float(test_dir_acc), 4))
"""))

cells.append(code_cell("""
fig, ax = plt.subplots()
ax.hist(test_results["actual_next_ret"], bins=100, alpha=0.6, label="Actual")
ax.hist(test_results["pred_next_ret"], bins=100, alpha=0.6, label="Predicted")
ax.set_title("Distribution of actual vs predicted next-day returns")
ax.set_xlabel("Next-day return")
ax.set_ylabel("Frequency")
ax.legend()
plt.show()

sample_for_scatter = test_results.sample(min(len(test_results), 5000), random_state=SEED)
fig, ax = plt.subplots()
ax.scatter(sample_for_scatter["actual_next_ret"], sample_for_scatter["pred_next_ret"], alpha=0.25)
lims = [
    min(sample_for_scatter["actual_next_ret"].min(), sample_for_scatter["pred_next_ret"].min()),
    max(sample_for_scatter["actual_next_ret"].max(), sample_for_scatter["pred_next_ret"].max())
]
ax.plot(lims, lims)
ax.set_title("Actual vs predicted returns")
ax.set_xlabel("Actual")
ax.set_ylabel("Predicted")
plt.show()
"""))

cells.append(md_cell("""
## Target coin evaluation
"""))

cells.append(code_cell("""
target_results = results[results["symbol"] == TARGET_SYMBOL].sort_values("date").reset_index(drop=True)
target_test = target_results[target_results["split"] == "test"].copy().reset_index(drop=True)

print("Target test rows:", len(target_test))
target_test.head()
"""))

cells.append(code_cell("""
target_ret_mae = mean_absolute_error(target_test["actual_next_ret"], target_test["pred_next_ret"])
target_ret_rmse = math.sqrt(mean_squared_error(target_test["actual_next_ret"], target_test["pred_next_ret"]))
target_dir_acc = target_test["direction_correct"].mean()
target_price_mae = mean_absolute_error(target_test["next_close"], target_test["pred_next_close"])
target_price_rmse = math.sqrt(mean_squared_error(target_test["next_close"], target_test["pred_next_close"]))
target_r2 = r2_score(target_test["next_close"], target_test["pred_next_close"])

print(f"{TARGET_SYMBOL} test return MAE: {target_ret_mae:.6f}")
print(f"{TARGET_SYMBOL} test return RMSE: {target_ret_rmse:.6f}")
print(f"{TARGET_SYMBOL} direction accuracy: {target_dir_acc:.4f}")
print(f"{TARGET_SYMBOL} next-close MAE: {target_price_mae:.2f}")
print(f"{TARGET_SYMBOL} next-close RMSE: {target_price_rmse:.2f}")
print(f"{TARGET_SYMBOL} next-close R²: {target_r2:.4f}")
"""))

cells.append(code_cell("""
fig, ax = plt.subplots()
ax.plot(target_test["date"], target_test["actual_next_ret"], label="Actual next-day return")
ax.plot(target_test["date"], target_test["pred_next_ret"], label="Predicted next-day return")
ax.set_title(f"{TARGET_SYMBOL}: actual vs predicted next-day returns")
ax.set_xlabel("Date")
ax.set_ylabel("Return")
ax.legend()
plt.show()

fig, ax = plt.subplots()
ax.plot(target_test["date"], target_test["next_close"], label="Actual next-day close")
ax.plot(target_test["date"], target_test["pred_next_close"], label="Predicted next-day close")
ax.set_title(f"{TARGET_SYMBOL}: actual vs predicted next-day close")
ax.set_xlabel("Date")
ax.set_ylabel("Price")
ax.legend()
plt.show()
"""))

cells.append(code_cell("""
rolling_window = 20
target_test["rolling_dir_acc"] = target_test["direction_correct"].rolling(rolling_window).mean()

fig, ax = plt.subplots()
ax.plot(target_test["date"], target_test["rolling_dir_acc"])
ax.axhline(0.5)
ax.set_title(f"{TARGET_SYMBOL}: rolling directional accuracy")
ax.set_xlabel("Date")
ax.set_ylabel("Accuracy")
plt.show()

fig, ax = plt.subplots()
ax.scatter(target_test["actual_next_ret"], target_test["pred_next_ret"], alpha=0.35)
lims = [
    min(target_test["actual_next_ret"].min(), target_test["pred_next_ret"].min()),
    max(target_test["actual_next_ret"].max(), target_test["pred_next_ret"].max())
]
ax.plot(lims, lims)
ax.set_title(f"{TARGET_SYMBOL}: actual vs predicted returns")
ax.set_xlabel("Actual")
ax.set_ylabel("Predicted")
plt.show()
"""))

cells.append(md_cell("""
## Illustrative sign strategy

This is not a production trading strategy. It is only a simple visual comparison.
"""))

cells.append(code_cell("""
target_test["buy_hold_curve"] = (1.0 + target_test["actual_next_ret"]).cumprod()
target_test["signal"] = np.where(target_test["pred_next_ret"] > 0, 1.0, -1.0)
target_test["strategy_ret"] = target_test["signal"] * target_test["actual_next_ret"]
target_test["strategy_curve"] = (1.0 + target_test["strategy_ret"]).cumprod()

fig, ax = plt.subplots()
ax.plot(target_test["date"], target_test["buy_hold_curve"], label="Buy and hold")
ax.plot(target_test["date"], target_test["strategy_curve"], label="Prediction sign strategy")
ax.set_title(f"{TARGET_SYMBOL}: illustrative cumulative curves")
ax.set_xlabel("Date")
ax.set_ylabel("Growth of 1.0")
ax.legend()
plt.show()
"""))

cells.append(md_cell("""
## Save artifacts
"""))

cells.append(code_cell("""
from pathlib import Path
import joblib

out_dir = Path("artifacts_crypto_panel_model")
out_dir.mkdir(exist_ok=True)

model.save(out_dir / "keras_multi_coin_model.keras")
joblib.dump(scaler, out_dir / "feature_scaler.joblib")
target_test.to_csv(out_dir / f"{TARGET_SYMBOL.lower()}_test_predictions.csv", index=False)
results.to_csv(out_dir / "all_predictions.csv", index=False)

print("Saved files:")
for p in sorted(out_dir.glob("*")):
    print("-", p)
"""))

nb = {
    "cells": cells,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "name": "python",
            "version": "3.11"
        }
    },
    "nbformat": 4,
    "nbformat_minor": 5
}

with open("multi_coin_crypto_forecasting_notebook.ipynb", "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print("Notebook created: multi_coin_crypto_forecasting_notebook.ipynb")