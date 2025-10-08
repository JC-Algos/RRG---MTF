# rrg_mini_fixed.py
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from io import BytesIO
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(layout="wide", page_title="RRG – World / US / HK")

# ---------- 1.  BIG TICKER LISTS ----------
WORLD_TICKERS = ["^GSPC","^NDX","^RUT","^HSI","3032.HK","^STOXX50E","^BSESN","^KS11",
                 "^TWII","000300.SS","^N225","HYG","AGG","EEM","GDX","XLE","XME","AAXJ","IBB",
                 "DBA","TLT","EFA","EWZ","EWG","EWJ","EWY","EWT","EWQ","EWA","EWC","EWH",
                 "EWS","EIDO","EPHE","THD","INDA","KWEB","QQQ","SPY","IWM","VNQ","GLD","SLV",
                 "USO","UNG","VEA","VWO","VTI","VXUS"][:150]

US_TICKERS = ["AAPL", "ABBV", "ABNB", "ABSV", "ABT", "ACN", "ADBE", "ADP", "ADSK", "ALGN", 
              "AMAT", "AMD", "AMGN", "AMZN", "AMT", "ANET", "APA", "ARGO", "ARM", "AS", 
              "ASML", "AVGO", "BA", "BAC", "BDX", "BLK", "BKNG", "BMRG", "BMY", "BRK-B", 
              "CAT", "CB", "CCL", "CDNS", "CF", "CHTR", "CME", "COP", "COST", "CRM", 
              "CRWD", "CSCO", "CSX", "CVS", "CVX", "DDOG", "DE", "DHR", "DIS", "DLTR", 
              "DVN", "DXCM", "EOG", "EXM", "F", "FANG", "FCX", "FDD", "FTNT", "FUTU", 
              "G", "GE", "GILD", "GIS", "GM", "GOOGL", "GS", "HAL", "HD", "HON", "HSY", 
              "IBM", "ICE", "IDXX", "INTC", "INTU", "ISRG", "ITW", "IWM", "JNJ", "JPM", 
              "JPU", "KD", "KHC", "KMB", "KMI", "KO", "LEN", "LIAT", "LLY", "LMT", "LOW", 
              "LRCX", "MA", "MAR", "MCD", "MDLZ", "META", "MMM", "MRK", "MRO", "MSFT", 
              "MU", "NEE", "NFLX", "NKE", "NOW", "NRG", "NVO", "NVDA", "NXTR", "ORCL", 
              "ORLY", "OXY", "PANW", "PEP", "PFE", "PG", "PGR", "PLTR", "PM", "PSX", 
              "QCOM", "REGN", "RTX", "SBUX", "SLB", "SMH", "SNOW", "SPGI", "TGT", "TJX", 
              "TMO", "TRV", "TSLA", "TSM", "TTD", "TTWO", "TXN", "TEAM", "ULTA", "UNH", 
              "UNP", "UPS", "V", "VLO", "VMO", "VST", "VZ", "WDH", "WMB", "WMT", "WRTC", 
              "XLC", "XLE", "XLF", "XLI", "XLK", "XLP", "XLRE", "XLU", "XLV", "XLY", 
              "XOM", "YUM", "ZS", "BX", "COIN",
              "GOOG", "TMUS", "AZN", "LIN", "SHOP", "PDD", "CMCSA", "APP", "MELI", "VRTX", 
              "SNPS", "KLAC", "MSTR", "ADI", "CEG", "DASH", "CTAS", "TRI", "MRVL", "PYPL", 
              "WDAY", "AEP", "MNST", "ROP", "AXON", "NXPI", "FAST", "PAYX", "PCAR", "KDP", 
              "CCEP", "ROST", "CPRT", "BKR", "EXC", "XEL", "CSGP", "EA", "MCHP", "VRSK", 
              "CTSH", "GEHC", "WBD", "ODFL", "LULU", "ON", "CDW", "GFS", "BIIB",
              "WFC", "AXP", "MS", "T", "UBER", "SCHW", "BSX", "SYK", "C", "GEV", 
              "ETN", "MMC", "APH", "MDT", "KKR", "PLD", "WELL", "MO", "SO", "TT", 
              "WM", "HCA", "FI", "DUK", "EQIX", "SHW", "MCK", "ELV", "MCO", "PH", 
              "AJG", "CI", "TDG", "AON", "RSG", "DELL", "APO", "COF", "ZTS", "ECL", 
              "RCL", "GD", "CL", "HWM", "CMG", "PNC", "NOC", "MSI", "USB", "EMR", 
              "JCI", "BK", "APD", "AZO", "SPG", "DLR", "CARR", "HLT", "NEM", "NSC", 
              "AFL", "COR", "ALL", "MET", "PWR", "PSA", "TFC", "FDX", "GWW", "OKE", 
              "O", "AIG", "SRE", "AMP", "MPC", "NDAQ"]

HK_TICKERS = ["0001.HK","0002.HK","0003.HK","0005.HK","0006.HK","0011.HK","0012.HK","0016.HK","0017.HK","0019.HK",
              "0020.HK","0027.HK","0066.HK","0101.HK","0144.HK","0168.HK","0175.HK","0177.HK","0220.HK","0241.HK",
              "0267.HK","0268.HK","0285.HK","0288.HK","0291.HK","0300.HK","0316.HK","0317.HK","0322.HK","0338.HK",
              "0358.HK","0386.HK","0388.HK","0390.HK","0489.HK","0552.HK","0598.HK","0636.HK","0669.HK","0688.HK",
              "0696.HK","0700.HK","0728.HK","0753.HK","0762.HK","0763.HK","0772.HK","0788.HK","0799.HK","0806.HK",
              "0811.HK","0823.HK","0836.HK","0857.HK","0868.HK","0883.HK","0902.HK","0914.HK","0916.HK","0921.HK",
              "0939.HK","0941.HK","0956.HK","0960.HK","0968.HK","0981.HK","0991.HK","0992.HK","0998.HK","1024.HK",
              "1033.HK","1038.HK","1044.HK","1055.HK","1066.HK","1071.HK","1072.HK","1088.HK","1093.HK","1099.HK",
              "1109.HK","1113.HK","1133.HK","1138.HK","1157.HK","1171.HK","1177.HK","1186.HK","1209.HK","1211.HK",
              "1288.HK","1299.HK","1316.HK","1336.HK","1339.HK","1347.HK","1359.HK","1378.HK","1398.HK","1515.HK",
              "1618.HK","1658.HK","1766.HK","1772.HK","1776.HK","1787.HK","1800.HK","1801.HK","1810.HK","1816.HK",
              "1818.HK","1833.HK","1860.HK","1876.HK","1880.HK","1886.HK","1898.HK","1918.HK","1919.HK","1928.HK",
              "1929.HK","1958.HK","1988.HK","1997.HK","2007.HK","2013.HK","2015.HK","2018.HK","2020.HK","2196.HK",
              "2202.HK","2208.HK","2238.HK","2252.HK","2269.HK","2313.HK","2318.HK","2319.HK","2328.HK","2331.HK",
              "2333.HK","2382.HK","2386.HK","2388.HK","2400.HK","2480.HK","2498.HK","2533.HK","2600.HK","2601.HK",
              "2607.HK","2611.HK","2628.HK","2688.HK","2689.HK","2696.HK","2727.HK","2799.HK","2845.HK","2866.HK",
              "2880.HK","2883.HK","2899.HK","3191.HK","3311.HK","3319.HK","3323.HK","3328.HK","3330.HK","3606.HK",
              "3618.HK","3690.HK","3698.HK","3800.HK","3866.HK","3880.HK","3888.HK","3898.HK","3900.HK","3908.HK",
              "3931.HK","3968.HK","3969.HK","3988.HK","3993.HK","3996.HK","6030.HK","6060.HK","6078.HK","6098.HK",
              "6099.HK","6139.HK","6160.HK","6178.HK","6181.HK","6618.HK","6655.HK","6680.HK","6682.HK","6690.HK",
              "6699.HK","6806.HK","6808.HK","6818.HK","6862.HK","6865.HK","6869.HK","6881.HK","6886.HK","6955.HK",
              "6963.HK","6969.HK","6990.HK","9600.HK","9601.HK","9618.HK","9626.HK","9633.HK","9666.HK","9668.HK",
              "9676.HK","9696.HK","9698.HK","9699.HK","9801.HK","9863.HK","9868.HK","9880.HK","9888.HK","9889.HK",
              "9901.HK","9922.HK","9923.HK","9961.HK","9988.HK","9992.HK","9995.HK","9999.HK"]


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
    
    # Fetch data with error handling
    try:
        weekly = yf.download(tickers, start=w_start, end=w_end, progress=False)["Close"].resample("W-FRI").last()
        daily  = yf.download(tickers, start=w_end-timedelta(days=500), end=w_end, progress=False)["Close"]
    except Exception as e:
        st.error(f"Error fetching data: {str(e)}")
        return pd.DataFrame(), pd.DataFrame(), cfg["bench"]
    
    # FIXED: Replace deprecated fillna methods with ffill() and bfill()
    weekly = weekly.ffill().bfill()
    daily = daily.ffill().bfill()
    
    # Only drop columns that are completely empty after filling
    weekly = weekly.dropna(axis=1, how="all")
    daily = daily.dropna(axis=1, how="all")
    
    # Ensure we have minimum required data
    if len(weekly) < 30 or len(daily) < 30:
        st.warning(f"Insufficient data: Weekly={len(weekly)}, Daily={len(daily)}")
    
    return weekly, daily, cfg["bench"]

# ---------- 3.  RRG ----------
def ma(s, n): 
    """Simple moving average with proper NaN handling and minimum periods"""
    if n == 1:
        return s
    # FIXED: Use min_periods equal to n to ensure reliable calculations
    result = s.rolling(n, min_periods=n).mean()
    return result

def rs_rm(sym, bench, data):
    """Calculate RS-Ratio and RS-Momentum with robust error handling"""
    try:
        # Ensure both series exist
        if sym not in data.columns or bench not in data.columns:
            return np.nan, np.nan
        
        # Drop NaN values before alignment
        sym_data = data[sym].dropna()
        bench_data = data[bench].dropna()
        
        # Align the data by common index
        common_index = sym_data.index.intersection(bench_data.index)
        
        # FIXED: Require more data points for reliable calculations
        if len(common_index) < 50:
            return np.nan, np.nan
        
        sym_aligned = sym_data.reindex(common_index)
        bench_aligned = bench_data.reindex(common_index)
        
        # Calculate base ratio with zero division protection
        # FIXED: Add small epsilon to avoid division by zero
        bench_safe = bench_aligned.replace(0, np.nan)
        base = sym_aligned / bench_safe
        
        # Remove infinite values and NaN
        base = base.replace([np.inf, -np.inf], np.nan).dropna()
        
        # FIXED: Check again for sufficient data after cleaning
        if len(base) < 50:
            return np.nan, np.nan
        
        # Calculate RS-Ratio
        rs1 = ma(base, 10)
        rs2 = ma(base, 26)
        
        # FIXED: More robust NaN handling
        if rs1.isna().all() or rs2.isna().all():
            return np.nan, np.nan
        
        # Avoid division by zero
        rs2_safe = rs2.replace(0, np.nan)
        rs_ratio = 100 * ((rs1 - rs2_safe) / rs2_safe + 1)
        
        # FIXED: Check for valid RS-Ratio before calculating momentum
        rs_ratio_clean = rs_ratio.dropna()
        if len(rs_ratio_clean) < 10:
            return np.nan, np.nan
        
        # Calculate RS-Momentum
        rm1 = rs_ratio  # Current value
        rm2 = ma(rs_ratio, 4)
        
        # FIXED: More robust NaN handling for momentum
        if rm2.isna().all():
            return np.nan, np.nan
        
        # Avoid division by zero
        rm2_safe = rm2.replace(0, np.nan)
        rs_momentum = 100 * ((rm1 - rm2_safe) / rm2_safe + 1)
        
        # Return the last valid values rounded to 2 decimal places
        rs_ratio_valid = rs_ratio.dropna()
        rs_momentum_valid = rs_momentum.dropna()
        
        if len(rs_ratio_valid) == 0 or len(rs_momentum_valid) == 0:
            return np.nan, np.nan
        
        rs_final = round(rs_ratio_valid.iloc[-1], 2)
        rm_final = round(rs_momentum_valid.iloc[-1], 2)
        
        # FIXED: Validate results are not extreme values
        if abs(rs_final) > 1000 or abs(rm_final) > 1000:
            return np.nan, np.nan
        
        return rs_final, rm_final
        
    except Exception as e:
        # FIXED: Better error logging
        return np.nan, np.nan

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

# Add status indicators
with st.spinner(f"Fetching {uni} market data..."):
    weekly, daily, bench = fetch(uni)

# FIXED: Better validation of fetched data
if weekly.empty or daily.empty:
    st.error("❌ Failed to fetch data. Please try again or check your internet connection.")
    st.stop()

tickers = [c for c in weekly.columns if c != bench and c in daily.columns]

if not tickers:
    st.error("❌ No valid tickers found in the data.")
    st.stop()

# Progress tracking
progress_bar = st.progress(0)
status_text = st.empty()

rows = []
failed_tickers = []
processed = 0

for i, tk in enumerate(tickers):
    processed += 1
    progress_bar.progress(processed / len(tickers))
    status_text.text(f"Processing {tk}... ({processed}/{len(tickers)})")
    
    try:
        # Only process tickers that exist in both datasets
        if tk in weekly.columns and tk in daily.columns and bench in weekly.columns and bench in daily.columns:
            w_rs, w_rm = rs_rm(tk, bench, weekly)
            d_rs, d_rm = rs_rm(tk, bench, daily)
            
            # Only add to results if we have valid data
            if not (pd.isna(w_rs) or pd.isna(w_rm) or pd.isna(d_rs) or pd.isna(d_rm)):
                rows.append({
                    "Ticker": tk,
                    "Weekly Quadrant": quadrant(w_rs, w_rm),
                    "Weekly RS": w_rs,
                    "Weekly RM": w_rm,
                    "Daily Quadrant": quadrant(d_rs, d_rm),
                    "Daily RS": d_rs,
                    "Daily RM": d_rm
                })
            else:
                failed_tickers.append(tk)
    except Exception as e:
        failed_tickers.append(tk)
        continue

# Clear progress indicators
progress_bar.empty()
status_text.empty()

# FIXED: Show processing summary
if failed_tickers:
    with st.expander(f"⚠️ {len(failed_tickers)} tickers had insufficient data", expanded=False):
        st.write(", ".join(failed_tickers[:50]))
        if len(failed_tickers) > 50:
            st.write(f"... and {len(failed_tickers) - 50} more")

df = pd.DataFrame(rows)

if df.empty:
    st.error("❌ No valid data available after processing. This could be due to:")
    st.write("- Network connectivity issues")
    st.write("- Insufficient historical data for tickers")
    st.write("- Market data provider restrictions")
    st.stop()

# Success indicator
st.success(f"✅ Successfully processed {len(df)} out of {len(tickers)} tickers")

# ---------- 5.  SORT BY WEEKLY QUADRANT ----------
quad_order = {'Leading': 0, 'Improving': 1, 'Weakening': 2, 'Lagging': 3, 'No Data': 4}
df = df.sort_values(by='Weekly Quadrant', key=lambda x: x.map(quad_order))

# ---------- 6.  DISPLAY ----------
st.subheader(f"{uni} Rotation Table (Benchmark: {bench})")

# Add summary statistics
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Leading", len(df[df['Weekly Quadrant'] == 'Leading']))
with col2:
    st.metric("Improving", len(df[df['Weekly Quadrant'] == 'Improving']))
with col3:
    st.metric("Weakening", len(df[df['Weekly Quadrant'] == 'Weakening']))
with col4:
    st.metric("Lagging", len(df[df['Weekly Quadrant'] == 'Lagging']))

# FIXED: Use modern pandas styling method
styled = df.style.map(
    lambda v: {"Leading":"background-color:#90EE90",
               "Improving":"background-color:#ADD8E6",
               "Weakening":"background-color:#FFFFE0",
               "Lagging":"background-color:#FFB6C1",
               "No Data":"background-color:#D3D3D3"}.get(v, ""),
    subset=["Weekly Quadrant", "Daily Quadrant"]
)

st.dataframe(styled, use_container_width=True, height=600)

# ---------- 7.  EXCEL DOWNLOAD ----------
buffer = BytesIO()
with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
    # Write the dataframe to Excel starting at row 2 (3rd row)
    df.to_excel(writer, sheet_name="RRG", index=False, startrow=2)
    
    # Get the xlsxwriter workbook and worksheet objects
    workbook = writer.book
    worksheet = writer.sheets['RRG']
    
    # Add timestamp at the first row (GMT+8)
    timestamp_format = workbook.add_format({'bold': True, 'font_size': 12})
    current_time = (datetime.now() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")
    worksheet.write(0, 0, f"RRG Analysis - Generated on: {current_time} (GMT+8)", timestamp_format)
    
    # Define formats for different quadrants with borders
    leading_format = workbook.add_format({'bg_color': '#90EE90', 'border': 1})
    improving_format = workbook.add_format({'bg_color': '#ADD8E6', 'border': 1})
    weakening_format = workbook.add_format({'bg_color': '#FFFFE0', 'border': 1})
    lagging_format = workbook.add_format({'bg_color': '#FFB6C1', 'border': 1})
    no_data_format = workbook.add_format({'bg_color': '#D3D3D3', 'border': 1})
    
    # Number formats with borders
    leading_number = workbook.add_format({'bg_color': '#90EE90', 'num_format': '0.00', 'border': 1})
    improving_number = workbook.add_format({'bg_color': '#ADD8E6', 'num_format': '0.00', 'border': 1})
    weakening_number = workbook.add_format({'bg_color': '#FFFFE0', 'num_format': '0.00', 'border': 1})
    lagging_number = workbook.add_format({'bg_color': '#FFB6C1', 'num_format': '0.00', 'border': 1})
    no_data_number = workbook.add_format({'bg_color': '#D3D3D3', 'num_format': '0.00', 'border': 1})
    
    # Header and ticker formats
    header_format = workbook.add_format({'bold': True, 'bg_color': '#D3D3D3', 'border': 1})
    ticker_format = workbook.add_format({'border': 1})
    
    # Apply header formatting
    for col in range(len(df.columns)):
        worksheet.write(2, col, df.columns[col], header_format)
    
    # Apply data formatting
    for row_num in range(len(df)):
        excel_row = row_num + 3
        weekly_q = df.iloc[row_num]['Weekly Quadrant']
        daily_q = df.iloc[row_num]['Daily Quadrant']
        
        # Ticker column
        worksheet.write(excel_row, 0, df.iloc[row_num]['Ticker'], ticker_format)
        
        # Weekly quadrant formatting
        fmt_map = {
            'Leading': (leading_format, leading_number),
            'Improving': (improving_format, improving_number),
            'Weakening': (weakening_format, weakening_number),
            'Lagging': (lagging_format, lagging_number),
            'No Data': (no_data_format, no_data_number)
        }
        
        w_fmt, w_num = fmt_map.get(weekly_q, (no_data_format, no_data_number))
        worksheet.write(excel_row, 1, weekly_q, w_fmt)
        worksheet.write(excel_row, 2, df.iloc[row_num]['Weekly RS'], w_num)
        worksheet.write(excel_row, 3, df.iloc[row_num]['Weekly RM'], w_num)
        
        # Daily quadrant formatting
        d_fmt, d_num = fmt_map.get(daily_q, (no_data_format, no_data_number))
        worksheet.write(excel_row, 4, daily_q, d_fmt)
        worksheet.write(excel_row, 5, df.iloc[row_num]['Daily RS'], d_num)
        worksheet.write(excel_row, 6, df.iloc[row_num]['Daily RM'], d_num)
    
    # Auto-adjust column widths
    worksheet.set_column('A:A', 15)
    worksheet.set_column('B:B', 18)
    worksheet.set_column('C:C', 12)
    worksheet.set_column('D:D', 15)
    worksheet.set_column('E:E', 16)
    worksheet.set_column('F:F', 12)
    worksheet.set_column('G:G', 15)

buffer.seek(0)
st.download_button(
    "📥 Download Excel Report",
    data=buffer,
    file_name=f"RRG_{uni}_{datetime.now():%Y%m%d_%H%M%S}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
