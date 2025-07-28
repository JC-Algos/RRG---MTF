# rrg_mini.py
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from io import BytesIO

st.set_page_config(layout="wide", page_title="RRG – World / US / HK")

# ---------- 1.  BIG TICKER LISTS ----------
WORLD_TICKERS = ["^GSPC","^NDX","^RUT","^HSI","3032.HK","^STOXX50E","^BSESN","^KS11",
                 "^TWII","000300.SS","^N225","HYG","AGG","EEM","GDX","XLE","XME","AAXJ","IBB",
                 "DBA","TLT","EFA","EWZ","EWG","EWJ","EWY","EWT","EWQ","EWA","EWC","EWH",
                 "EWS","EIDO","EPHE","THD","INDA","KWEB","QQQ","SPY","IWM","VNQ","GLD","SLV",
                 "USO","UNG","VEA","VWO","VTI","VXUS"][:150]

US_TICKERS = ["AAPL","MSFT","GOOGL","AMZN","META","NVDA","TSLA","BRK-B","JPM","JNJ","V","PG",
              "UNH","HD","MA","BAC","ABBV","PFE","KO","AVGO","PEP","WMT","MRK","CSCO","ADBE",
              "NFLX","CRM","ACN","TMO","COST","DIS","ABT","VZ","DHR","NKE","TXN","BMY","QCOM",
              "NEE","PM","RTX","HON","UPS","UNP","BA","CAT","GE","MMM","LMT","SPGI","LOW",
              "INTU","IBM","GS","AMD","BLK","ISRG","AMAT","MU","F","GM","ORLY","TJX","SBUX",
              "MAR","BKNG","CVS","GILD","BDX","ADP","KMB","GIS","ITW","EOG","SLB","PSX","VLO",
              "KMI","WMB","OXY","HAL","DVN","FANG","MRO","APA","EOG","COP","XOM","CVX"][:150]

HK_TICKERS = ["0001.HK","0002.HK","0003.HK","0005.HK","0006.HK","0011.HK","0012.HK","0016.HK",
              "0017.HK","0027.HK","0066.HK","0175.HK","0267.HK","0288.HK","0291.HK","0386.HK",
              "0388.HK","0669.HK","0762.HK","0823.HK","0836.HK","0857.HK","0883.HK","0939.HK",
              "0941.HK","0960.HK","0968.HK","0981.HK","1038.HK","1044.HK","1088.HK","1093.HK",
              "1109.HK","1113.HK","1177.HK","1211.HK","1299.HK","1378.HK","1398.HK","1810.HK",
              "1876.HK","1928.HK","1929.HK","1997.HK","2007.HK","2018.HK","2269.HK","2318.HK",
              "2319.HK","2382.HK","2388.HK","2628.HK","2688.HK","2689.HK","3690.HK","3888.HK",
              "3900.HK","3968.HK","3988.HK","6030.HK","6098.HK","6139.HK","6690.HK","6808.HK",
              "6862.HK","6969.HK","9618.HK","9626.HK","9698.HK","9801.HK","9922.HK","9988.HK",
              "9999.HK","0700.HK","0388.HK","0005.HK","1299.HK","0941.HK","1398.HK","2318.HK",
              "2388.HK","2628.HK","3988.HK","0883.HK","0001.HK","0016.HK","0017.HK","0027.HK",
              "0267.HK","0288.HK","0291.HK","0386.HK","0669.HK","0762.HK","0823.HK","0857.HK"][:150]

UNIVERSE_MAP = {
    "World": {"tickers": WORLD_TICKERS, "bench": "ACWI"},
    "US":    {"tickers": US_TICKERS,    "bench": "^GSPC"},
    "HK":    {"tickers": HK_TICKERS,    "bench": "^HSI"}
}

# ---------- 2.  DATA ----------
@st.cache_data(ttl=3600)
def fetch(universe):
    cfg = UNIVERSE_MAP[universe]
    tickers = [cfg["bench"]] + cfg["tickers"]
    end = datetime.today()
    w_end = end - timedelta(hours=4)
    w_start = w_end - timedelta(weeks=100)
    
    # Fetch data
    weekly = yf.download(tickers, start=w_start, end=w_end, progress=False)["Close"].resample("W-FRI").last()
    daily  = yf.download(tickers, start=w_end-timedelta(days=500), end=w_end, progress=False)["Close"]
    
    # Clean data properly - forward fill then backward fill to handle missing values
    weekly = weekly.fillna(method='ffill').fillna(method='bfill')
    daily = daily.fillna(method='ffill').fillna(method='bfill')
    
    # Only drop columns that are completely empty after filling
    weekly = weekly.dropna(axis=1, how="all")
    daily = daily.dropna(axis=1, how="all")
    
    return weekly, daily, cfg["bench"]

# ---------- 3.  RRG ----------
def ma(s, n): 
    """Simple moving average with proper NaN handling"""
    if n == 1:
        return s  # No need to calculate rolling mean for period 1
    return s.rolling(n, min_periods=1).mean()

def rs_rm(sym, bench, data):
    """Calculate RS-Ratio and RS-Momentum with proper data alignment"""
    # Ensure both series are aligned and handle missing data
    sym_data = data[sym].dropna()
    bench_data = data[bench].dropna()
    
    # Align the data by common index
    common_index = sym_data.index.intersection(bench_data.index)
    if len(common_index) < 30:  # Need minimum data points
        return np.nan, np.nan
    
    sym_aligned = sym_data.reindex(common_index)
    bench_aligned = bench_data.reindex(common_index)
    
    # Calculate base ratio with zero division protection
    base = sym_aligned / bench_aligned
    base = base.replace([np.inf, -np.inf], np.nan).dropna()
    
    if len(base) < 30:  # Need minimum data points for moving averages
        return np.nan, np.nan
    
    # Calculate RS-Ratio (matches Pine Script logic exactly)
    rs1 = ma(base, 10)
    rs2 = ma(base, 26)
    
    # Avoid division by zero
    rs2_safe = rs2.replace(0, np.nan)
    rs_ratio = 100 * ((rs1 - rs2_safe) / rs2_safe + 1)
    
    # Calculate RS-Momentum (matches Pine Script logic exactly) 
    rm1 = ma(rs_ratio, 1)  # This is just rs_ratio itself
    rm2 = ma(rs_ratio, 4)
    
    # Avoid division by zero
    rm2_safe = rm2.replace(0, np.nan)
    rs_momentum = 100 * ((rm1 - rm2_safe) / rm2_safe + 1)
    
    # Return the last valid values rounded to 2 decimal places
    rs_final = round(rs_ratio.dropna().iloc[-1], 2) if not rs_ratio.dropna().empty else np.nan
    rm_final = round(rs_momentum.dropna().iloc[-1], 2) if not rs_momentum.dropna().empty else np.nan
    
    return rs_final, rm_final

def quadrant(x, y):
    if pd.isna(x) or pd.isna(y):
        return "No Data"
    if x >= 100 and y >= 100: return "Leading"
    if x >= 100 and y < 100:  return "Weakening"
    if x < 100  and y >= 100: return "Improving"
    return "Lagging"

# ---------- 4.  UI ----------
st.sidebar.title("Universe")
uni = st.sidebar.radio("Choose universe", list(UNIVERSE_MAP.keys()), index=0)

# Add refresh button
if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()

weekly, daily, bench = fetch(uni)
tickers = [c for c in weekly.columns if c != bench and c in daily.columns]

rows = []
for tk in tickers:
    try:
        # Only process tickers that exist in both datasets
        if tk in weekly.columns and tk in daily.columns and bench in weekly.columns and bench in daily.columns:
            w_rs, w_rm = rs_rm(tk, bench, weekly)
            d_rs, d_rm = rs_rm(tk, bench, daily)
            
            # Only add to results if we have valid data
            if not (pd.isna(w_rs) or pd.isna(w_rm) or pd.isna(d_rs) or pd.isna(d_rm)):
                rows.append({
                    "Ticker": tk,
                    "Weekly Q": quadrant(w_rs, w_rm),
                    "Weekly RS": w_rs,
                    "Weekly RM": w_rm,
                    "Daily Q": quadrant(d_rs, d_rm),
                    "Daily RS": d_rs,
                    "Daily RM": d_rm
                })
    except Exception as e:
        st.sidebar.write(f"Error processing {tk}: {str(e)}")
        continue

df = pd.DataFrame(rows)

if df.empty:
    st.error("No valid data available. Please check your data source and try again.")
    st.stop()

# ---------- 5.  SORT BY WEEKLY QUADRANT ----------
quad_order = {'Leading': 0, 'Improving': 1, 'Weakening': 2, 'Lagging': 3, 'No Data': 4}
df = df.sort_values(by='Weekly Q', key=lambda x: x.map(quad_order))

# ---------- 6.  DISPLAY ----------
st.subheader(f"{uni} rotation table  (bench: {bench})")
styled = df.style.applymap(
    lambda v: {"Leading":"background-color:#90EE90",
               "Improving":"background-color:#ADD8E6",
               "Weakening":"background-color:#FFFFE0",
               "Lagging":"background-color:#FFB6C1",
               "No Data":"background-color:#D3D3D3"}.get(v, ""),
    subset=["Weekly Q", "Daily Q"]
)
st.dataframe(styled, use_container_width=True, height=600)

# ---------- 7.  EXCEL DOWNLOAD ----------
buffer = BytesIO()
with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
    # Write the dataframe to Excel
    df.to_excel(writer, sheet_name="RRG", index=False)
    
    # Get the xlsxwriter workbook and worksheet objects
    workbook = writer.book
    worksheet = writer.sheets['RRG']
    
    # Define formats for different quadrants
    leading_format = workbook.add_format({'bg_color': '#90EE90'})
    improving_format = workbook.add_format({'bg_color': '#ADD8E6'})
    weakening_format = workbook.add_format({'bg_color': '#FFFFE0'})
    lagging_format = workbook.add_format({'bg_color': '#FFB6C1'})
    no_data_format = workbook.add_format({'bg_color': '#D3D3D3'})
    
    # Number format for RS values (2 decimal places)
    number_format = workbook.add_format({'num_format': '0.00'})
    leading_number = workbook.add_format({'bg_color': '#90EE90', 'num_format': '0.00'})
    improving_number = workbook.add_format({'bg_color': '#ADD8E6', 'num_format': '0.00'})
    weakening_number = workbook.add_format({'bg_color': '#FFFFE0', 'num_format': '0.00'})
    lagging_number = workbook.add_format({'bg_color': '#FFB6C1', 'num_format': '0.00'})
    no_data_number = workbook.add_format({'bg_color': '#D3D3D3', 'num_format': '0.00'})
    
    # Apply formatting to each row
    for row_num in range(1, len(df) + 1):  # Start from 1 to skip header
        weekly_q = df.iloc[row_num-1]['Weekly Q']
        daily_q = df.iloc[row_num-1]['Daily Q']
        
        # Format Weekly Quadrant column (column 1)
        if weekly_q == 'Leading':
            worksheet.write(row_num, 1, weekly_q, leading_format)
            worksheet.write(row_num, 2, df.iloc[row_num-1]['Weekly RS'], leading_number)
            worksheet.write(row_num, 3, df.iloc[row_num-1]['Weekly RM'], leading_number)
        elif weekly_q == 'Improving':
            worksheet.write(row_num, 1, weekly_q, improving_format)
            worksheet.write(row_num, 2, df.iloc[row_num-1]['Weekly RS'], improving_number)
            worksheet.write(row_num, 3, df.iloc[row_num-1]['Weekly RM'], improving_number)
        elif weekly_q == 'Weakening':
            worksheet.write(row_num, 1, weekly_q, weakening_format)
            worksheet.write(row_num, 2, df.iloc[row_num-1]['Weekly RS'], weakening_number)
            worksheet.write(row_num, 3, df.iloc[row_num-1]['Weekly RM'], weakening_number)
        elif weekly_q == 'Lagging':
            worksheet.write(row_num, 1, weekly_q, lagging_format)
            worksheet.write(row_num, 2, df.iloc[row_num-1]['Weekly RS'], lagging_number)
            worksheet.write(row_num, 3, df.iloc[row_num-1]['Weekly RM'], lagging_number)
        else:
            worksheet.write(row_num, 1, weekly_q, no_data_format)
            worksheet.write(row_num, 2, df.iloc[row_num-1]['Weekly RS'], no_data_number)
            worksheet.write(row_num, 3, df.iloc[row_num-1]['Weekly RM'], no_data_number)
        
        # Format Daily Quadrant column (column 4)
        if daily_q == 'Leading':
            worksheet.write(row_num, 4, daily_q, leading_format)
            worksheet.write(row_num, 5, df.iloc[row_num-1]['Daily RS'], leading_number)
            worksheet.write(row_num, 6, df.iloc[row_num-1]['Daily RM'], leading_number)
        elif daily_q == 'Improving':
            worksheet.write(row_num, 4, daily_q, improving_format)
            worksheet.write(row_num, 5, df.iloc[row_num-1]['Daily RS'], improving_number)
            worksheet.write(row_num, 6, df.iloc[row_num-1]['Daily RM'], improving_number)
        elif daily_q == 'Weakening':
            worksheet.write(row_num, 4, daily_q, weakening_format)
            worksheet.write(row_num, 5, df.iloc[row_num-1]['Daily RS'], weakening_number)
            worksheet.write(row_num, 6, df.iloc[row_num-1]['Daily RM'], weakening_number)
        elif daily_q == 'Lagging':
            worksheet.write(row_num, 4, daily_q, lagging_format)
            worksheet.write(row_num, 5, df.iloc[row_num-1]['Daily RS'], lagging_number)
            worksheet.write(row_num, 6, df.iloc[row_num-1]['Daily RM'], lagging_number)
        else:
            worksheet.write(row_num, 4, daily_q, no_data_format)
            worksheet.write(row_num, 5, df.iloc[row_num-1]['Daily RS'], no_data_number)
            worksheet.write(row_num, 6, df.iloc[row_num-1]['Daily RM'], no_data_number)
    
    # Auto-adjust column widths
    worksheet.set_column('A:A', 15)  # Ticker
    worksheet.set_column('B:B', 12)  # Weekly Q
    worksheet.set_column('C:C', 12)  # Weekly RS
    worksheet.set_column('D:D', 15)  # Weekly RM
    worksheet.set_column('E:E', 12)  # Daily Q
    worksheet.set_column('F:F', 12)  # Daily RS
    worksheet.set_column('G:G', 15)  # Daily RM

buffer.seek(0)
st.download_button(
    "Download Excel",
    data=buffer,
    file_name=f"RRG_{uni}_{datetime.now():%Y%m%d_%H%M%S}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
