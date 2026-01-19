import ccxt
import pandas as pd
import streamlit as st

# -------------------------------------------------
# Streamlit Ayarları
# -------------------------------------------------
st.set_page_config(
    page_title="Multi-Exchange EMA Scanner",
    layout="wide"
)

st.title("EMA(9) / EMA(21) Yukarı Kesişim Tarayıcı")
st.caption("Gate.io • OKX • Bitget | Seçilebilir Timeframe")

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
    index=1  # Varsayılan: 1 Saat
)

TIMEFRAME = TIMEFRAME_OPTIONS[selected_label]
LIMIT = 100

# -------------------------------------------------
# Borsalar
# -------------------------------------------------
EXCHANGES = {
    "Gate.io": ccxt.gateio({"enableRateLimit": True}),
    "OKX": ccxt.okx({"enableRateLimit": True}),
    "Bitget": ccxt.bitget({"enableRateLimit": True}),
}

# -------------------------------------------------
# Fonksiyonlar
# -------------------------------------------------
def fetch_ohlcv(exchange, symbol):
    try:
        data = exchange.fetch_ohlcv(
            symbol,
            timeframe=TIMEFRAME,
            limit=LIMIT
        )
        df = pd.DataFrame(
            data,
            columns=["ts", "open", "high", "low", "close", "volume"]
        )
        return df
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

with st.spinner("Borsalar taranıyor..."):
    for exchange_name, exchange in EXCHANGES.items():
        try:
            markets = exchange.load_markets()
            symbols = [
                s for s in markets
                if s.endswith("/USDT") and markets[s]["active"]
            ]

            for symbol in symbols:
                df = fetch_ohlcv(exchange, symbol)
                if df is not None and len(df) >= 21:
                    if ema_crossover(df):
                        results.append({
                            "Borsa": exchange_name,
                            "Coin": symbol,
                            "Timeframe": TIMEFRAME
                        })
        except Exception:
            st.error(f"{exchange_name} taranırken hata oluştu")

# -------------------------------------------------
# Sonuçlar
# -------------------------------------------------
st.subheader("Tespit Edilen Coinler")

if results:
    df_result = pd.DataFrame(results)
    st.dataframe(
        df_result.sort_values(["Borsa", "Coin"]),
        use_container_width=True
    )
else:
    st.warning("Seçilen timeframe için EMA(9) yukarı kesişimi bulunamadı.")
