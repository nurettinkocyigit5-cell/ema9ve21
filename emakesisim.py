import ccxt
import pandas as pd
import streamlit as st

# -------------------------------------------------
# Streamlit Ayarları
# -------------------------------------------------
st.set_page_config(
    page_title="Bitget EMA Scanner",
    layout="wide"
)

st.title("EMA(9) / EMA(21) Yukarı Kesişim Tarayıcı")
st.caption("Bitget | Seçilebilir Timeframe")

# -------------------------------------------------
# Timeframe Seçimi
# -------------------------------------------------
TIMEFRAME_OPTIONS = {
    "15 Dakika": "15m",
    "1 Saat": "1h",
    "4 Saat": "4h",
    "1 Gün": "1d",
}

selected_label = st.selectbox(
    "Zaman Dilimi",
    list(TIMEFRAME_OPTIONS.keys()),
    index=1
)

TIMEFRAME = TIMEFRAME_OPTIONS[selected_label]
LIMIT = 100

# -------------------------------------------------
# Bitget
# -------------------------------------------------
exchange = ccxt.bitget({"enableRateLimit": True})

# -------------------------------------------------
# Fonksiyonlar
# -------------------------------------------------
def fetch_ohlcv(symbol):
    try:
        data = exchange.fetch_ohlcv(
            symbol,
            timeframe=TIMEFRAME,
            limit=LIMIT
        )
        return pd.DataFrame(
            data,
            columns=["ts", "open", "high", "low", "close", "volume"]
        )
    except Exception:
        return None


def ema_crossover(df):
    df["ema9"] = df["close"].ewm(span=9, adjust=False).mean()
    df["ema21"] = df["close"].ewm(span=21, adjust=False).mean()

    prev = df.iloc[-2]
    last = df.iloc[-1]

    return prev["ema9"] < prev["ema21"] and last["ema9"] > last["ema21"]


# -------------------------------------------------
# Tarama
# -------------------------------------------------
results = []

with st.spinner("Bitget taranıyor..."):
    markets = exchange.load_markets()
    symbols = [
        s for s in markets
        if s.endswith("/USDT") and markets[s]["active"]
    ]

    for symbol in symbols:
        df = fetch_ohlcv(symbol)
        if df is not None and len(df) >= 21:
            if ema_crossover(df):
                results.append({
                    "Coin": symbol,
                    "Timeframe": TIMEFRAME
                })

# -------------------------------------------------
# Sonuçlar
# -------------------------------------------------
st.subheader("Tespit Edilen Coinler")

if results:
    df_result = pd.DataFrame(results)
    st.dataframe(
        df_result.sort_values("Coin"),
        use_container_width=True
    )
else:
    st.warning("Seçilen timeframe için EMA(9) yukarı kesişimi bulunamadı.")
