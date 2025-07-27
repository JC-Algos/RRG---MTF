# rrg_mini.py
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from io import BytesIO

st.set_page_config(layout="wide", page_title="RRG – World / US / HK")

# ---------- 1.  HUGE TICKER LISTS  ----------
WORLD_TICKERS = [
    "ACWI","^GSPC","^NDX","^RUT","^HSI","3032.HK","^STOXX50E","^BSESN","^KS11",
    "^TWII","000300.SS","^N225","HYG","AGG","EEM","GDX","XLE","XME","AAXJ","IBB",
    "DBA","TLT","EFA","EWZ","EWG","EWJ","EWY","EWT","EWQ","EWA","EWC","EWH",
    "EWS","EIDO","EPHE","THD","INDA","ASHR","KWEB","QQQ","SPY","IWM","EFA","EMB",
    "VNQ","LQD","HYG","GLD","SLV","USO","UNG","VNQI","VEA","VWO","VTI","VXUS"
][:150]   # 150 tickers (trim or extend freely)

US_TICKERS = [
    "AAPL","MSFT","GOOGL","AMZN","META","NVDA","TSLA","BRK-B","JPM","JNJ","V","PG",
    "UNH","HD","MA","BAC","ABBV","PFE","KO","AVGO","PEP","WMT","MRK","CSCO","ADBE",
    "NFLX","CRM","ACN","TMO","COST","DIS","ABT","VZ","DHR","NKE","TXN","BMY","QCOM",
    "NEE","PM","RTX","HON","AMGN","LIN","LOW","UPS","UNP","MDT","T","CVX","SBUX",
    "INTU","IBM","GS","LMT","SPGI","INTC","BLK","AMD","BDX","ISRG","AMAT","CHTR",
    "MO","BKNG","GE","AMT","GILD","USB","CVS","ADP","MDLZ","C","CI","AXP","F",
    "MU","TJX","EOG","CSX","SLB","PLD","MMM","KMI","CCI","BSX","ICE","SYK",
    "FISV","ITW","COP","CAT","SO","EA","GM","DUK","AON","PGR","FCX","EMR",
    "VLO","NSC","ELV","SCHW","MET","PSX","D","HUM","APD","BK","MAR","ETN"
][:150]

HK_TICKERS = [
    "0001.HK","0002.HK","0003.HK","0005.HK","0006.HK","0011.HK","0012.HK",
    "0016.HK","0017.HK","0027.HK","0066.HK","0175.HK","0267.HK","0288.HK",
    "0291.HK","0386.HK","0388.HK","0669.HK","0762.HK","0823.HK","0836.HK",
    "0857.HK","0883.HK","0939.HK","0941.HK","0960.HK","0968.HK","0981.HK",
    "1038.HK","1044.HK","1088.HK","1093.HK","1109.HK","1113.HK","1177.HK",
    "1211.HK","1299.HK","1378.HK","1398.HK","1810.HK","1876.HK","1928.HK",
    "1929.HK","1997.HK","2007.HK","2018.HK","2269.HK","2318.HK","2319.HK",
    "2382.HK","2388.HK","2628.HK","2688.HK","2689.HK","3690.HK","3888.HK",
    "3900.HK","3968.HK","3988.HK","6030.HK","6098.HK","6139.HK","6690.HK",
    "6808.HK","6862.HK","6969.HK","9618.HK","9626.HK","9698.HK","9801.HK"
][:150]

UNIVERSE_MAP = {
    "World": {"tickers": WORLD_TICKERS, "bench": "ACWI"},
    "US":    {"tickers": US_TICKERS,    "bench": "^GSPC"},
    "HK":    {"tickers": HK_TICKERS,    "bench": "^HSI"}
}

# ---------- 2.  SIMPLE FETCH  ----------
@st.cache_data(ttl=3600)
def fetch(universe):
    cfg = UNIVERSE_MAP[universe]
    tickers = [cfg["bench"]] + cfg["tickers"]
    end   = datetime.today()
    w_end = end - timedelta(hours=4)
    w_start = w_end - timedelta(weeks=100)
    weekly = yf.download(tickers, start=w_start, end=w_end, progress=False)["Close"].resample("W-FRI").last()
    daily  = yf.download(tickers, start=w_end - timedelta(days=500), end=w_end, progress=False)["Close"]
    weekly = weekly.dropna(axis=1, how="all")
    daily  = daily.dropna(axis=1, how="all")
    return weekly, daily, cfg["bench"]

# ---------- 3.  RRG LOGIC  ----------
def ma(s, n): return s.rolling(n).mean()

def rs_rm(sym, bench, data):
    base = data[sym] / data[bench]
    rs = 100 * (ma(base, 10) / ma(base, 26) - 1) + 100
    rm = 100 * (ma(rs, 1)  / ma(rs, 4)  - 1) + 100
    return rs.iloc[-1], rm.iloc[-1]

def quadrant(x, y):
    if x >= 100 and y >= 100: return "Leading"
    if x >= 100 and y < 100:  return "Weakening"
    if x < 100  and y >= 100: return "Improving"
    return "Lagging"

# ---------- 4.  UI  ----------
st.sidebar.title("Universe")
uni = st.sidebar.radio("Choose", list(UNIVERSE_MAP.keys()), index=0)

weekly, daily, bench = fetch(uni)
tickers = [c for c in weekly.columns if c != bench]

rows = []
for tk in tickers:
    try:
        w_rs, w_rm = rs_rm(tk, bench, weekly)
        d_rs, d_rm = rs_rm(tk, bench, daily)
        rows.append({
            "Ticker": tk,
            "Weekly Q": quadrant(w_rs, w_rm),
            "Weekly RS": round(w_rs, 2),
            "Weekly RM": round(w_rm, 2),
            "Daily Q": quadrant(d_rs, d_rm),
            "Daily RS": round(d_rs, 2),
            "Daily RM": round(d_rm, 2)
        })
    except Exception:
        pass     # skip dead tickers

df = pd.DataFrame(rows)

# ---------- 5.  DISPLAY + DOWNLOAD  ----------
st.subheader(f"RRG Table – {uni} (bench: {bench})")
st.dataframe(
    df.style.applymap(lambda v: {
        "Leading":"background-color:#90EE90",
        "Improving":"background-color:#ADD8E6",
        "Weakening":"background-color:#FFFFE0",
        "Lagging":"background-color:#FFB6C1"
    }.get(v, ""), subset=["Weekly Q", "Daily Q"]),
    use_container_width=True,
    height=600
)

# Excel download
buffer = BytesIO()
with pd.ExcelWriter(buffer, engine="xlsxwriter") as w:
    df.to_excel(w, sheet_name="RRG", index=False)
buffer.seek(0)
st.download_button(
    "Download Excel",
    data=buffer,
    file_name=f"RRG_{uni}_{datetime.now():%Y%m%d_%H%M%S}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
