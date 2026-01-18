import ccxt
import pandas as pd
import streamlit as st

# -----------------------------
# Streamlit Ayarları
# -----------------------------
st.set_page_config(page_title="Bitget EMA Kesişim Tarayıcı", layout="wide")
st.title("Bitget | 1 Saatlik EMA(9) / EMA(21) Yukarı Kesişim Tarayıcı")

# -----------------------------
# Bitget Bağlantısı
# -----------------------------
exchange = ccxt.bitget({
    "enableRateLimit": True
})

# -----------------------------
# Yardımcı Fonksiyonlar
# -----------------------------
def fetch_ohlcv(symbol, timeframe="1h", limit=100):
    try:
        data = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(
            data,
            columns=["timestamp", "open", "high", "low", "close", "volume"]
        )
        return df
    except Exception:
        return None


def check_ema_crossover(df):
    df["ema9"] = df["close"].ewm(span=9, adjust=False).mean()
    df["ema21"] = df["close"].ewm(span=21, adjust=False).mean()

    # Son iki mumda yukarı kesişim kontrolü
    prev = df.iloc[-2]
    last = df.iloc[-1]

    return prev["ema9"] < prev["ema21"] and last["ema9"] > last["ema21"]


# -----------------------------
# Marketleri Al
# -----------------------------
st.info("Pariteler taranıyor...")

markets = exchange.load_markets()
symbols = [
    s for s in markets.keys()
    if s.endswith("/USDT") and markets[s]["active"]
]

# -----------------------------
# Tarama
# -----------------------------
matched_coins = []

progress = st.progress(0)
total = len(symbols)

for i, symbol in enumerate(symbols):
    df = fetch_ohlcv(symbol)
    if df is not None and len(df) >= 21:
        if check_ema_crossover(df):
            matched_coins.append(symbol)

    progress.progress((i + 1) / total)

# -----------------------------
# Sonuçlar
# -----------------------------
st.success(f"Bulunan Coin Sayısı: {len(matched_coins)}")

if matched_coins:
    result_df = pd.DataFrame(matched_coins, columns=["Coin"])
    st.dataframe(result_df, use_container_width=True)
else:
    st.warning("Şu anda EMA(9) yukarı kesişimi yapan coin bulunamadı.")
