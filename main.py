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
              # Missing NASDAQ 100 tickers:
              "GOOG", "TMUS", "AZN", "LIN", "SHOP", "PDD", "CMCSA", "APP", "MELI", "VRTX", 
              "SNPS", "KLAC", "MSTR", "ADI", "CEG", "DASH", "CTAS", "TRI", "MRVL", "PYPL", 
              "WDAY", "AEP", "MNST", "ROP", "AXON", "NXPI", "FAST", "PAYX", "PCAR", "KDP", 
              "CCEP", "ROST", "CPRT", "BKR", "EXC", "XEL", "CSGP", "EA", "MCHP", "VRSK", 
              "CTSH", "GEHC", "WBD", "ODFL", "LULU", "ON", "CDW", "GFS", "BIIB",
              # Missing S&P 500 top 200 tickers:
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
              "9901.HK","9922.HK","9923.HK","9961.HK","9968.HK","9988.HK","9992.HK","9995.HK","9999.HK"]


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
                    "Weekly Quadrant": quadrant(w_rs, w_rm),
                    "Weekly RS": w_rs,
                    "Weekly RM": w_rm,
                    "Daily Quadrant": quadrant(d_rs, d_rm),
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
df = df.sort_values(by='Weekly Quadrant', key=lambda x: x.map(quad_order))

# ---------- 6.  DISPLAY ----------
st.subheader(f"{uni} rotation table  (bench: {bench})")
styled = df.style.applymap(
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
    
    # Define border format
    border_format = workbook.add_format({'border': 1})
    
    # Define formats for different quadrants with borders
    leading_format = workbook.add_format({'bg_color': '#90EE90', 'border': 1})
    improving_format = workbook.add_format({'bg_color': '#ADD8E6', 'border': 1})
    weakening_format = workbook.add_format({'bg_color': '#FFFFE0', 'border': 1})
    lagging_format = workbook.add_format({'bg_color': '#FFB6C1', 'border': 1})
    no_data_format = workbook.add_format({'bg_color': '#D3D3D3', 'border': 1})
    
    # Number format for RS values (2 decimal places) with borders
    leading_number = workbook.add_format({'bg_color': '#90EE90', 'num_format': '0.00', 'border': 1})
    improving_number = workbook.add_format({'bg_color': '#ADD8E6', 'num_format': '0.00', 'border': 1})
    weakening_number = workbook.add_format({'bg_color': '#FFFFE0', 'num_format': '0.00', 'border': 1})
    lagging_number = workbook.add_format({'bg_color': '#FFB6C1', 'num_format': '0.00', 'border': 1})
    no_data_number = workbook.add_format({'bg_color': '#D3D3D3', 'num_format': '0.00', 'border': 1})
    
    # Header format with borders
    header_format = workbook.add_format({'bold': True, 'bg_color': '#D3D3D3', 'border': 1})
    
    # Apply border formatting to headers (row 2, which is index 2)
    for col in range(len(df.columns)):
        worksheet.write(2, col, df.columns[col], header_format)
    
    # Apply border formatting to ticker column (no background color)
    ticker_format = workbook.add_format({'border': 1})
    for row_num in range(len(df)):
        worksheet.write(row_num + 3, 0, df.iloc[row_num]['Ticker'], ticker_format)
    
    # Apply formatting to each data row (starting from row 3, which is index 3)
    for row_num in range(len(df)):
        excel_row = row_num + 3  # Offset by 3 because we start at row 3 (index 2 is header)
        weekly_q = df.iloc[row_num]['Weekly Quadrant']
        daily_q = df.iloc[row_num]['Daily Quadrant']
        
        # Format Weekly Quadrant column (column 1)
        if weekly_q == 'Leading':
            worksheet.write(excel_row, 1, weekly_q, leading_format)
            worksheet.write(excel_row, 2, df.iloc[row_num]['Weekly RS'], leading_number)
            worksheet.write(excel_row, 3, df.iloc[row_num]['Weekly RM'], leading_number)
        elif weekly_q == 'Improving':
            worksheet.write(excel_row, 1, weekly_q, improving_format)
            worksheet.write(excel_row, 2, df.iloc[row_num]['Weekly RS'], improving_number)
            worksheet.write(excel_row, 3, df.iloc[row_num]['Weekly RM'], improving_number)
        elif weekly_q == 'Weakening':
            worksheet.write(excel_row, 1, weekly_q, weakening_format)
            worksheet.write(excel_row, 2, df.iloc[row_num]['Weekly RS'], weakening_number)
            worksheet.write(excel_row, 3, df.iloc[row_num]['Weekly RM'], weakening_number)
        elif weekly_q == 'Lagging':
            worksheet.write(excel_row, 1, weekly_q, lagging_format)
            worksheet.write(excel_row, 2, df.iloc[row_num]['Weekly RS'], lagging_number)
            worksheet.write(excel_row, 3, df.iloc[row_num]['Weekly RM'], lagging_number)
        else:
            worksheet.write(excel_row, 1, weekly_q, no_data_format)
            worksheet.write(excel_row, 2, df.iloc[row_num]['Weekly RS'], no_data_number)
            worksheet.write(excel_row, 3, df.iloc[row_num]['Weekly RM'], no_data_number)
        
        # Format Daily Quadrant column (column 4)
        if daily_q == 'Leading':
            worksheet.write(excel_row, 4, daily_q, leading_format)
            worksheet.write(excel_row, 5, df.iloc[row_num]['Daily RS'], leading_number)
            worksheet.write(excel_row, 6, df.iloc[row_num]['Daily RM'], leading_number)
        elif daily_q == 'Improving':
            worksheet.write(excel_row, 4, daily_q, improving_format)
            worksheet.write(excel_row, 5, df.iloc[row_num]['Daily RS'], improving_number)
            worksheet.write(excel_row, 6, df.iloc[row_num]['Daily RM'], improving_number)
        elif daily_q == 'Weakening':
            worksheet.write(excel_row, 4, daily_q, weakening_format)
            worksheet.write(excel_row, 5, df.iloc[row_num]['Daily RS'], weakening_number)
            worksheet.write(excel_row, 6, df.iloc[row_num]['Daily RM'], weakening_number)
        elif daily_q == 'Lagging':
            worksheet.write(excel_row, 4, daily_q, lagging_format)
            worksheet.write(excel_row, 5, df.iloc[row_num]['Daily RS'], lagging_number)
            worksheet.write(excel_row, 6, df.iloc[row_num]['Daily RM'], lagging_number)
        else:
            worksheet.write(excel_row, 4, daily_q, no_data_format)
            worksheet.write(excel_row, 5, df.iloc[row_num]['Daily RS'], no_data_number)
            worksheet.write(excel_row, 6, df.iloc[row_num]['Daily RM'], no_data_number)
    
    # Auto-adjust column widths
    worksheet.set_column('A:A', 15)  # Ticker
    worksheet.set_column('B:B', 18)  # Weekly Quadrant
    worksheet.set_column('C:C', 12)  # Weekly RS
    worksheet.set_column('D:D', 15)  # Weekly RM
    worksheet.set_column('E:E', 16)  # Daily Quadrant
    worksheet.set_column('F:F', 12)  # Daily RS
    worksheet.set_column('G:G', 15)  # Daily RM

buffer.seek(0)
st.download_button(
    "Download Excel",
    data=buffer,
    file_name=f"RRG_{uni}_{datetime.now():%Y%m%d_%H%M%S}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
