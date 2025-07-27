import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
from io import BytesIO

# Set page config to wide layout
st.set_page_config(layout="wide", page_title="JC Algos 資產輪動分析")

# Display disclaimer at the top
st.warning("""
## Disclaimer:
免責聲明：
* 此應用程式僅供教育用途，不應視為財務建議。
* 我們不保證數據的準確性。數據來源為Yahoo Finance，可能存在限制或不準確之處。
* 在做出任何投資決策之前，請自行進行研究並諮詢合格的財務顧問。
""")

# Function to get path to a file in the data directory
def get_data_path(filename):
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, "data")
    
    # Create data directory if it doesn't exist
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    return os.path.join(data_dir, filename)

# Use the function to get file paths
us_portfolio_path = get_data_path("Customised Portfolio_US.txt")
hk_portfolio_path = get_data_path("Customised Portfolio_HK.txt")

# Read the files and parse tickers
try:
    with open(us_portfolio_path, 'r') as f:
        us_portfolio_data = f.read()
    
    with open(hk_portfolio_path, 'r') as f:
        hk_portfolio_data = f.read()
    
    # Parse the portfolio data into lists of tickers
    us_portfolio_tickers = [line.strip() for line in us_portfolio_data.split('\n') if line.strip()]
    hk_portfolio_tickers = [line.strip() for line in hk_portfolio_data.split('\n') if line.strip()]
    
    # Store the parsed tickers in session state for use in the customized portfolio sections
    st.session_state['customised_portfolio_us_tickers'] = us_portfolio_tickers
    st.session_state['customised_portfolio_hk_tickers'] = hk_portfolio_tickers
        
except Exception as e:
    # If files don't exist, create default portfolios
    st.session_state['customised_portfolio_us_tickers'] = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "BRK.B", "JPM", "JNJ"]
    st.session_state['customised_portfolio_hk_tickers'] = ["0005.HK", "0700.HK", "3988.HK", "0388.HK", "1398.HK", "0941.HK", "0939.HK", "2318.HK", "0883.HK", "0001.HK"]

def get_preset_portfolio(portfolio_type="HK"):
    # Use the loaded tickers from session state
    if portfolio_type == "HK" and 'customised_portfolio_hk_tickers' in st.session_state and st.session_state['customised_portfolio_hk_tickers']:
        return st.session_state['customised_portfolio_hk_tickers']
    elif portfolio_type == "US" and 'customised_portfolio_us_tickers' in st.session_state and st.session_state['customised_portfolio_us_tickers']:
        return st.session_state['customised_portfolio_us_tickers']
    
    # Provide fallback portfolios as a last resort
    if portfolio_type == "HK":
        return ["0005.HK", "0700.HK", "3988.HK", "0388.HK", "1398.HK"]
    else:
        return ["AAPL", "MSFT", "GOOGL", "AMZN", "META"]


def refresh_data():
    try:
        # Clear all cached data
        st.cache_data.clear()
        
        # Re-fetch data for the current universe
        universe = st.session_state.get('selected_universe', 'WORLD')
        sector = st.session_state.get('sector', None)
        custom_tickers = st.session_state.get('custom_tickers', None)
        custom_benchmark = st.session_state.get('custom_benchmark', None)
        
        # Call get_data with current parameters to refresh the data
        get_data(universe, sector, custom_tickers, custom_benchmark, force_refresh=True)
        
        st.session_state.data_refreshed = True
        st.success("Data refreshed successfully!")
    except Exception as e:
        st.error(f"An error occurred while refreshing data: {str(e)}")
        st.session_state.data_refreshed = False


@st.cache_data
def ma(data, period):
    return data.rolling(window=period).mean()

@st.cache_data
def calculate_rrg_values(data, benchmark):
    sbr = data / benchmark
    rs1 = ma(sbr, 10)
    rs2 = ma(sbr, 26)
    rs = 100 * ((rs1 - rs2) / rs2 + 1)
    rm1 = ma(rs, 1)
    rm2 = ma(rs, 4)
    rm = 100 * ((rm1 - rm2) / rm2 + 1)
    return rs, rm

def get_quadrant(x, y):
    if x < 100 and y < 100: return "Lagging"
    elif x >= 100 and y < 100: return "Weakening"
    elif x < 100 and y >= 100: return "Improving"
    else: return "Leading"

@st.cache_data
def get_data(universe, sector, custom_tickers=None, custom_benchmark=None, force_refresh=False):
    """
    Fetch financial data for the specified universe and sector for both Weekly and Daily timeframes.
    
    Parameters:
        universe (str): The market universe to analyze (e.g., "WORLD", "US", "HK")
        sector (str, optional): Specific sector within the universe
        custom_tickers (list, optional): List of custom tickers for custom portfolios
        custom_benchmark (str, optional): Custom benchmark ticker for custom portfolios
        force_refresh (bool): If True, bypass cache and force new data fetch
        
    Returns:
        tuple: (weekly_data DataFrame, daily_data DataFrame, benchmark ticker, sectors list, sector_names dict)
    """
    # Import timezone handling
    import pytz
    
    # Set appropriate timezone based on universe
    if universe == "HK" or universe == "Customised Portfolio_HK":
        tz = pytz.timezone('Asia/Hong_Kong')
    else:
        tz = pytz.timezone('America/New_York')
    
    # Get current date in the appropriate timezone
    end_date = datetime.now(tz).replace(tzinfo=None)
    debug_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Set start dates for both timeframes
    weekly_start_date = end_date - timedelta(weeks=100)
    daily_start_date = end_date - timedelta(days=500)

    # Define sector universes
    sector_universes = {
        "US": {
            "XLK": ["AAPL", "MSFT", "NVDA", "AVGO", "ADBE", "MU", "CRM", "ASML", "SNPS", "IBM", "INTC", "TXN", "NOW", "QCOM", "AMD", "AMAT", "NOW", "PANW", "CDNS", "TSMC"],
            "XLY": ["AMZN", "TSLA", "HD", "MCD", "NKE", "LOW", "SBUX", "TJX", "BKNG", "MAR", "F", "GM", "ORLY", "DHI", "CMG", "TJX", "YUM", "LEN", "ULTA", "CCL", "EXPE"],
            "XLV": ["UNH", "JNJ", "LLY", "PFE", "ABT", "TMO", "MRK", "ABBV", "DHR", "BMY", "AMGN", "CVS", "ISRG", "MDT", "GILD", "VRTX", "CI", "ZTS", "RGEN", "BSX", "HCA"],
            "XLF": ["BRK.B", "JPM", "BAC", "WFC", "GS", "MS", "SPGI", "BLK", "C", "AXP", "CB", "MMC", "PGR", "PNC", "TFC", "V", "MA", "PYPL", "AON", "CME", "ICE", "COF"],
            "XLC": ["META", "GOOGL", "GOOG", "NFLX", "CMCSA", "DIS", "VZ", "T", "TMUS", "ATVI", "EA", "TTWO", "MTCH", "CHTR", "DISH", "FOXA", "TTWO", "FOX", "NWS", "WBD"],
            "XLI": ["UNP", "HON", "UPS", "BA", "CAT", "GE", "MMM", "RTX", "LMT", "FDX", "DE", "ETN", "EMR", "NSC", "CSX", "ADP", "GD", "NOC", "FDX", "JCI", "CARR", "ITW"],
            "XLE": ["XOM", "CVX", "COP", "SLB", "EOG", "MPC", "PSX", "VLO", "OXY", "KMI", "WMB", "HES", "HAL", "DVN", "BKR", "CTRA", "EQT", "APA", "MRO", "TRGP", "FANG"],
            "XLB": ["LIN", "APD", "SHW", "FCX", "ECL", "NEM", "DOW", "DD", "CTVA", "PPG", "NUE", "VMC", "ALB", "FMC", "CE", "MLM", "IFF", "STLD", "CF", "FMC"],
            "XLP": ["PG", "KO", "PEP", "COST", "WMT", "PM", "MO", "EL", "CL", "GIS", "KMB", "SYY", "KHC", "STZ", "HSY", "TGT", "ADM", "MNST", "DG", "DLTR", "WBA", "SJM"],
            "XLU": ["NEE", "DUK", "SO", "D", "AEP", "SRE", "EXC", "XEL", "PCG", "WEC", "ES", "ED", "DTE", "AEE", "ETR", "CEG", "PCG", "EIX", "FFE", "CMS", "CNP", "PPL"],
            "XLRE": ["PLD", "AMT", "CCI", "EQIX", "PSA", "O", "WELL", "SPG", "SBAC", "AVB", "EQR", "DLR", "VTR", "ARE", "CBRE", "WY", "EXR", "MAA", "IRM", "ESS", "HST"]
        },
        "HK": {
            "^HSNU": ["0002.HK", "0003.HK", "0006.HK", "0836.HK", "1038.HK", "2688.HK",],
            "^HSNF": ["0005.HK", "0011.HK", "0388.HK", "0939.HK", "1398.HK", "2318.HK", "2388.HK", "2628.HK","3968.HK","3988.HK","1299.HK"],
            "^HSNP": ["0012.HK", "0016.HK", "0017.HK", "0101.HK", "0823.HK", "0688.HK", "1109.HK", "1997.HK", "1209.HK", "0960.HK","1113.HK"],
            "^HSNC": ["0700.HK", "0857.HK", "0883.HK", "0941.HK", "0001.HK","0175.HK","0241.HK","0267.HK","0285.HK","0027.HK",
                     "0288.HK","0291.HK","0316.HK","0332.HK", "0386.HK", "0669.HK", "0762.HK", "0968.HK", "0981.HK", "0386.HK"]
        }
    }

    # Determine universe, benchmark, sectors, and sector names
    if universe == "WORLD":
        benchmark = "ACWI"
        sectors = ["^GSPC", "^NDX", "^RUT", "^HSI", "3032.HK", "^STOXX50E", "^BSESN", "^KS11", 
                  "^TWII", "000300.SS", "^N225", "HYG", "AGG", "EEM", "GDX", "XLE", "XME", "AAXJ","IBB","DBA"]
        sector_names = {
            "^GSPC": "標普500", "^NDX": "納指100", "^RUT": "羅素2000", "^HSI": "恆指",
            "3032.HK": "恒生科技", "^STOXX50E": "歐洲", "^BSESN": "印度", "^KS11": "韓國",
            "^TWII": "台灣", "000300.SS": "滬深300", "^N225": "日本", "HYG": "高收益債券",
            "AGG": "投資級別債券", "EEM": "新興市場", "GDX": "金礦", "XLE": "能源",
            "XME": "礦業", "AAXJ": "亞太日本除外", "IBB": "生物科技","DBA":"農業"
        }
    elif universe == "US":
        benchmark = "^GSPC"
        sectors = list(sector_universes["US"].keys())
        sector_names = {
            "XLK": "科技", "XLY": "非必須消費", "XLV": "健康護理",
            "XLF": "金融", "XLC": "通訊", "XLI": "工業", "XLE": "能源",
            "XLB": "物料", "XLP": "必須消費", "XLU": "公用", "XLRE": "房地產"
        }
    elif universe == "US Sectors":
        if sector:
            benchmark = sector
            sectors = sector_universes["US"][sector]
            sector_names = {s: "" for s in sectors}
        else:
            st.error("Please select a US sector.")
            return None, None, None, None, None
    elif universe == "HK":
        benchmark = "^HSI"
        sectors = list(sector_universes["HK"].keys())
        sector_names = {"^HSNU": "公用", "^HSNF": "金融", "^HSNP": "地產", "^HSNC": "工商"}
    elif universe == "HK Sub-indexes":
        if sector:
            benchmark = sector
            sectors = sector_universes["HK"][sector]
            sector_names = {s: "" for s in sectors}
        else:
            st.error("Please select a HK sub-index.")
            return None, None, None, None, None
    elif universe == "Customised Portfolio_HK" or universe == "Customised Portfolio_US":
        if custom_benchmark and custom_tickers and len(custom_tickers) > 0:
            benchmark = custom_benchmark
            sectors = [ticker for ticker in custom_tickers if ticker]
            sector_names = {s: "" for s in sectors}
        else:
            portfolio_type = "HK" if universe == "Customised Portfolio_HK" else "US"
            st.error(f"Please provide at least one stock ticker and select a benchmark for your custom {portfolio_type} portfolio.")
            return None, None, None, None, None
    elif universe == "FX":
        benchmark = "HKDUSD=X"
        sectors = ["GBPUSD=X", "EURUSD=X", "AUDUSD=X", "NZDUSD=X", "CADUSD=X", "CHFUSD=X", "JPYUSD=X", "CNYUSD=X",  "EURGBP=X", "AUDNZD=X", "AUDCAD=X", "NZDCAD=X", "DX-Y.NYB"]
        sector_names = {
            "GBPUSD=X": "GBP", "EURUSD=X": "EUR", "AUDUSD=X": "AUD", "NZDUSD=X": "NZD",
            "CADUSD=X": "CAD",  "JPYUSD=X": "JPY", "EURGBP=X": "EURGBP", "AUDNZD=X": "AUDNZD",
            "AUDCAD=X": "AUDCAD", "NZDCAD=X": "NZDCAD", "DX-Y.NYB":"DXY", "CHFUSD=X":"CHF","CNYUSD=X":"CNY" 
        }
    else:
        st.error("Invalid universe selection.")
        return None, None, None, None, None

    try:
        tickers_to_download = [benchmark] + sectors
        
        # Create status indicator
        fetch_status = st.empty()
        fetch_status.info(f"Fetching data for {len(tickers_to_download)} tickers as of {debug_timestamp}...")
        
        # Download data for both timeframes
        weekly_data = yf.download(
            tickers_to_download, 
            start=weekly_start_date, 
            end=end_date, 
            progress=False, 
            ignore_tz=True, 
            auto_adjust=True
        )['Close']
        
        daily_data = yf.download(
            tickers_to_download, 
            start=daily_start_date, 
            end=end_date, 
            progress=False, 
            ignore_tz=True, 
            auto_adjust=True
        )['Close']
        
        # Handle missing tickers
        missing_tickers = set(tickers_to_download) - set(weekly_data.columns)
        if missing_tickers:
            if universe == "WORLD":
                if "^TWII" in missing_tickers:
                    twii_data_weekly = yf.download("TAIEX", start=weekly_start_date, end=end_date, ignore_tz=True)['Close']
                    twii_data_daily = yf.download("TAIEX", start=daily_start_date, end=end_date, ignore_tz=True)['Close']
                    if not twii_data_weekly.empty:
                        weekly_data["^TWII"] = twii_data_weekly
                        daily_data["^TWII"] = twii_data_daily
                        missing_tickers.remove("^TWII")
                
                if "3032.HK" in missing_tickers:
                    hstech_data_weekly = yf.download("^HSTECH", start=weekly_start_date, end=end_date, ignore_tz=True)['Close']
                    hstech_data_daily = yf.download("^HSTECH", start=daily_start_date, end=end_date, ignore_tz=True)['Close']
                    if not hstech_data_weekly.empty:
                        weekly_data["3032.HK"] = hstech_data_weekly
                        daily_data["3032.HK"] = hstech_data_daily
                        missing_tickers.remove("3032.HK")
            
            for missing_ticker in missing_tickers:
                weekly_data[missing_ticker] = pd.Series(index=weekly_data.index, dtype='float64')
                daily_data[missing_ticker] = pd.Series(index=daily_data.index, dtype='float64')
        
        # Fill missing data
        weekly_data = weekly_data.fillna(method='ffill', limit=5)
        daily_data = daily_data.fillna(method='ffill', limit=5)
        
        # For World dashboard, be more aggressive with filling
        if universe == "WORLD":
            weekly_data = weekly_data.fillna(method='ffill')
            daily_data = daily_data.fillna(method='ffill')
        
        # Validate data
        if weekly_data.empty or daily_data.empty:
            fetch_status.error(f"No data available for the selected universe and sector.")
            return None, None, benchmark, sectors, sector_names
        
        # Clean up data
        weekly_data = weekly_data.dropna(axis=1, how='all')
        daily_data = daily_data.dropna(axis=1, how='all')
        
        # Validate benchmark data
        if benchmark not in weekly_data.columns or benchmark not in daily_data.columns:
            fetch_status.error(f"No data available for the benchmark {benchmark}. Please choose a different benchmark.")
            return None, None, benchmark, sectors, sector_names
        
        # Filter out sectors with no data
        valid_sectors = [s for s in sectors if s in weekly_data.columns and s in daily_data.columns]
        if len(valid_sectors) == 0:
            fetch_status.error("No valid sector data available. Please check your input and try again.")
            return None, None, benchmark, sectors, sector_names
        
        # Update sectors and sector_names
        sectors = valid_sectors
        sector_names = {s: sector_names[s] for s in valid_sectors if s in sector_names}
        
        # Clear the status message
        fetch_status.empty()
        
    except Exception as e:
        st.error(f"Error fetching data: {str(e)}")
        return None, None, benchmark, sectors, sector_names

    # Success message with date information
    latest_date = weekly_data.index.max().strftime("%Y-%m-%d")
    st.success(f"Successfully downloaded data for {len(weekly_data.columns)} tickers (up to {latest_date}).")
    
    return weekly_data, daily_data, benchmark, sectors, sector_names

def create_rrg_table(weekly_data, daily_data, benchmark, sectors, sector_names, universe):
    """Create a table showing RS and RS-momentum for both weekly and daily timeframes"""
    
    # Resample weekly data
    weekly_resampled = weekly_data.resample('W-FRI').last()
    
    table_data = []
    
    for sector in sectors:
        # Calculate weekly RS and RS-momentum
        weekly_rs, weekly_rm = calculate_rrg_values(weekly_resampled[sector], weekly_resampled[benchmark])
        weekly_rs_latest = weekly_rs.iloc[-1] if len(weekly_rs) > 0 else np.nan
        weekly_rm_latest = weekly_rm.iloc[-1] if len(weekly_rm) > 0 else np.nan
        weekly_quadrant = get_quadrant(weekly_rs_latest, weekly_rm_latest)
        
        # Calculate daily RS and RS-momentum
        daily_rs, daily_rm = calculate_rrg_values(daily_data[sector], daily_data[benchmark])
        daily_rs_latest = daily_rs.iloc[-1] if len(daily_rs) > 0 else np.nan
        daily_rm_latest = daily_rm.iloc[-1] if len(daily_rm) > 0 else np.nan
        daily_quadrant = get_quadrant(daily_rs_latest, daily_rm_latest)
        
        # Get display name
        if universe == "FX":
            display_name = f"{sector} ({sector_names.get(sector, '')})"
        elif universe == "US Sectors" or universe == "HK Sub-indexes" or universe == "Customised Portfolio_HK" or universe == "Customised Portfolio_US":
            display_name = sector
        else:
            display_name = f"{sector} ({sector_names.get(sector, '')})"
        
        table_data.append({
            'Ticker': display_name,
            'Weekly_Quadrant': weekly_quadrant,
            'Weekly_RS': round(weekly_rs_latest, 2) if not np.isnan(weekly_rs_latest) else None,
            'Weekly_RS-Momentum': round(weekly_rm_latest, 2) if not np.isnan(weekly_rm_latest) else None,
            'Daily_Quadrant': daily_quadrant,
            'Daily_RS': round(daily_rs_latest, 2) if not np.isnan(daily_rs_latest) else None,
            'Daily_RS-Momentum': round(daily_rm_latest, 2) if not np.isnan(daily_rm_latest) else None
        })
    
    # Convert to DataFrame
    df = pd.DataFrame(table_data)
    
    # Define quadrant order for sorting
    quadrant_order = {'Leading': 0, 'Improving': 1, 'Weakening': 2, 'Lagging': 3}
    
    # Sort by weekly quadrant in descending order (Leading first)
    df['Quadrant_Order'] = df['Weekly_Quadrant'].map(quadrant_order)
    df = df.sort_values('Quadrant_Order')
    df = df.drop('Quadrant_Order', axis=1)
    
    # Rename columns for display
    df.columns = ['Ticker', 'Weekly Quadrant', 'Weekly RS', 'Weekly RS-Momentum', 
                  'Daily Quadrant', 'Daily RS', 'Daily RS-Momentum']
    
    return df

def style_dataframe(df):
    """Apply styling to the dataframe"""
    def color_quadrant(val):
        colors = {
            'Leading': 'background-color: lightgreen',
            'Improving': 'background-color: lightblue',
            'Weakening': 'background-color: lightyellow',
            'Lagging': 'background-color: lightpink'
        }
        return colors.get(val, '')
    
    # Apply styling
    styled_df = df.style.applymap(color_quadrant, subset=['Weekly Quadrant', 'Daily Quadrant'])
    
    # Format numbers
    styled_df = styled_df.format({
        'Weekly RS': '{:.2f}',
        'Weekly RS-Momentum': '{:.2f}',
        'Daily RS': '{:.2f}',
        'Daily RS-Momentum': '{:.2f}'
    }, na_rep='')
    
    return styled_df

def convert_df_to_excel(df):
    """Convert DataFrame to Excel file in memory"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='RRG_Analysis', index=False)
        
        # Get the workbook and worksheet
        workbook = writer.book
        worksheet = writer.sheets['RRG_Analysis']
        
        # Define formats
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#D7E4BD',
            'border': 1
        })
        
        # Define quadrant colors
        leading_format = workbook.add_format({'bg_color': '#90EE90', 'border': 1})
        improving_format = workbook.add_format({'bg_color': '#ADD8E6', 'border': 1})
        weakening_format = workbook.add_format({'bg_color': '#FFFFE0', 'border': 1})
        lagging_format = workbook.add_format({'bg_color': '#FFB6C1', 'border': 1})
        
        # Apply header format
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
        
        # Apply conditional formatting to quadrant columns
        quadrant_formats = {
            'Leading': leading_format,
            'Improving': improving_format,
            'Weakening': weakening_format,
            'Lagging': lagging_format
        }
        
        # Apply formatting to cells
        for row_num in range(1, len(df) + 1):
            weekly_quadrant = df.iloc[row_num - 1]['Weekly Quadrant']
            daily_quadrant = df.iloc[row_num - 1]['Daily Quadrant']
            
            # Format Weekly Quadrant cell
            worksheet.write(row_num, 1, weekly_quadrant, quadrant_formats.get(weekly_quadrant))
            
            # Format Daily Quadrant cell
            worksheet.write(row_num, 4, daily_quadrant, quadrant_formats.get(daily_quadrant))
        
        # Adjust column widths
        worksheet.set_column('A:A', 25)  # Ticker
        worksheet.set_column('B:B', 15)  # Weekly Quadrant
        worksheet.set_column('C:D', 12)  # Weekly RS and RS-Momentum
        worksheet.set_column('E:E', 15)  # Daily Quadrant
        worksheet.set_column('F:G', 12)  # Daily RS and RS-Momentum
        
    output.seek(0)
    return output

def save_excel_to_drive(df, filename):
    """Save Excel file to C:\B_Drive"""
    try:
        # Create directory if it doesn't exist
        save_path = r"C:\B_Drive"
        if not os.path.exists(save_path):
            os.makedirs(save_path)
        
        # Generate timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        full_filename = f"{filename}_{timestamp}.xlsx"
        full_path = os.path.join(save_path, full_filename)
        
        # Save to Excel
        with pd.ExcelWriter(full_path, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='RRG_Analysis', index=False)
            
            # Get the workbook and worksheet
            workbook = writer.book
            worksheet = writer.sheets['RRG_Analysis']
            
            # Define formats
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'fg_color': '#D7E4BD',
                'border': 1
            })
            
            # Define quadrant colors
            leading_format = workbook.add_format({'bg_color': '#90EE90', 'border': 1})
            improving_format = workbook.add_format({'bg_color': '#ADD8E6', 'border': 1})
            weakening_format = workbook.add_format({'bg_color': '#FFFFE0', 'border': 1})
            lagging_format = workbook.add_format({'bg_color': '#FFB6C1', 'border': 1})
            
            # Apply header format
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
            
            # Apply conditional formatting to quadrant columns
            quadrant_formats = {
                'Leading': leading_format,
                'Improving': improving_format,
                'Weakening': weakening_format,
                'Lagging': lagging_format
            }
            
            # Apply formatting to cells
            for row_num in range(1, len(df) + 1):
                weekly_quadrant = df.iloc[row_num - 1]['Weekly Quadrant']
                daily_quadrant = df.iloc[row_num - 1]['Daily Quadrant']
                
                # Format Weekly Quadrant cell
                worksheet.write(row_num, 1, weekly_quadrant, quadrant_formats.get(weekly_quadrant))
                
                # Format Daily Quadrant cell
                worksheet.write(row_num, 4, daily_quadrant, quadrant_formats.get(daily_quadrant))
            
            # Adjust column widths
            worksheet.set_column('A:A', 25)  # Ticker
            worksheet.set_column('B:B', 15)  # Weekly Quadrant
            worksheet.set_column('C:D', 12)  # Weekly RS and RS-Momentum
            worksheet.set_column('E:E', 15)  # Daily Quadrant
            worksheet.set_column('F:G', 12)  # Daily RS and RS-Momentum
        
        return True, full_path
    except Exception as e:
        return False, str(e)

# Main Streamlit app
st.title("Asset Rotation Analysis by JC Algos - Table View")

# Initialize session state
if 'selected_universe' not in st.session_state:
    st.session_state.selected_universe = "WORLD"
if 'data_refreshed' not in st.session_state:
    st.session_state.data_refreshed = False

# Sidebar
st.sidebar.header("Settings")

# Add Refresh button at the top of the sidebar
if st.sidebar.button("Refresh Data"):
    refresh_data()
    st.rerun()

st.sidebar.header("Universe Selection")

universe_options = ["WORLD", "US", "US Sectors", "HK", "HK Sub-indexes", "Customised Portfolio_HK", "Customised Portfolio_US", "FX"]
universe_names = {
    "WORLD": "World", 
    "US": "US", 
    "US Sectors": "US Sectors", 
    "HK": "Hong Kong", 
    "HK Sub-indexes": "HK Sub-indexes", 
    "Customised Portfolio_HK": "Customised Portfolio - Hong Kong",
    "Customised Portfolio_US": "Customised Portfolio - US",
    "FX": "Foreign Exchange"
}

selected_universe = st.sidebar.selectbox(
    "Select Universe",
    options=universe_options,
    format_func=lambda x: universe_names[x],
    key="universe_selector",
    index=universe_options.index(st.session_state.selected_universe)
)

# Update the selected universe in session state
st.session_state.selected_universe = selected_universe

# Initialize variables for different universes
sector = None
custom_tickers = None
custom_benchmark = None

if selected_universe == "US Sectors":
    us_sectors = ["XLK", "XLY", "XLV", "XLF", "XLC", "XLI", "XLE", "XLB", "XLP", "XLU", "XLRE"]
    us_sector_names = {
        "XLK": "Technology", "XLY": "Consumer Discretionary", "XLV": "Health Care",
        "XLF": "Financials", "XLC": "Communications", "XLI": "Industrials", "XLE": "Energy",
        "XLB": "Materials", "XLP": "Consumer Staples", "XLU": "Utilities", "XLRE": "Real Estate"
    }
    st.sidebar.subheader("US Sectors")
    selected_us_sector = st.sidebar.selectbox(
        "Select US Sector",
        options=us_sectors,
        format_func=lambda x: us_sector_names[x],
        key="us_sector_selector"
    )
    if selected_us_sector:
        sector = selected_us_sector
elif selected_universe == "HK Sub-indexes":
    hk_sectors = ["^HSNU", "^HSNF", "^HSNP", "^HSNC"]
    hk_sector_names = {"^HSNU": "Utilities", "^HSNF": "Financials", "^HSNP": "Properties", "^HSNC": "Commerce & Industry"}
    st.sidebar.subheader("Hang Seng Sub-indexes")
    selected_hk_sector = st.sidebar.selectbox(
        "Select HK Sub-index",
        options=hk_sectors,
        format_func=lambda x: hk_sector_names[x],
        key="hk_sector_selector"
    )
    if selected_hk_sector:
        sector = selected_hk_sector
elif selected_universe == "Customised Portfolio_HK" or selected_universe == "Customised Portfolio_US":
    st.sidebar.subheader(f"{selected_universe}")
    
    if 'reset_tickers' not in st.session_state:
        st.session_state.reset_tickers = False
    
    portfolio_key = selected_universe.lower().replace(" ", "_")
    if f'{portfolio_key}_tickers' not in st.session_state or st.session_state.reset_tickers:
        portfolio_type = "HK" if selected_universe == "Customised Portfolio_HK" else "US"
        # Use the parsed tickers from session state if available
        if portfolio_type == "HK" and 'customised_portfolio_hk_tickers' in st.session_state and st.session_state['customised_portfolio_hk_tickers']:
            st.session_state[f'{portfolio_key}_tickers'] = st.session_state['customised_portfolio_hk_tickers']
        elif portfolio_type == "US" and 'customised_portfolio_us_tickers' in st.session_state and st.session_state['customised_portfolio_us_tickers']:
            st.session_state[f'{portfolio_key}_tickers'] = st.session_state['customised_portfolio_us_tickers']
        else:
            # Fall back to the preset portfolio as before
            st.session_state[f'{portfolio_key}_tickers'] = get_preset_portfolio(portfolio_type)
    
    # Determine the number of tickers to display
    num_tickers = len(st.session_state[f'{portfolio_key}_tickers'])
    num_tickers = max(num_tickers, 30)  # Ensure at least 30 input fields
    
    # Calculate the number of columns needed
    num_columns = (num_tickers + 2) // 3  # Round up to the nearest multiple of 3
    # Create columns
    columns = st.sidebar.columns(3)
    
    custom_tickers = []
    for i in range(num_columns * 3):  # This ensures we always have a multiple of 3 input fields
        col_index = i % 3
        if i < num_tickers:
            ticker = columns[col_index].text_input(
                f"Stock {i+1}", 
                key=f"{portfolio_key}_stock_{i+1}", 
                value=st.session_state[f'{portfolio_key}_tickers'][i] if i < len(st.session_state[f'{portfolio_key}_tickers']) else ""
            )
        else:
            ticker = columns[col_index].text_input(
                f"Stock {i+1}", 
                key=f"{portfolio_key}_stock_{i+1}", 
                value=""
            )
        
        if ticker:
            if selected_universe == "Customised Portfolio_HK" and ticker.isdigit():
                processed_ticker = f"{ticker.zfill(4)}.HK"
            elif ticker.isalpha():
                processed_ticker = ticker.upper()
            else:
                processed_ticker = ticker
            custom_tickers.append(processed_ticker)
    
    st.session_state[f'{portfolio_key}_tickers'] = custom_tickers
    
    benchmark_options = ["^GSPC", "^HSI", "ACWI"]
    default_benchmark = "^HSI" if selected_universe == "Customised Portfolio_HK" else "^GSPC"
    
    custom_benchmark = st.sidebar.selectbox(
        "Select Benchmark",
        options=benchmark_options,
        index=benchmark_options.index(default_benchmark) if default_benchmark in benchmark_options else 0,
        key=f"{portfolio_key}_benchmark_selector"
    )
    
    # Update the Reset button
    if st.sidebar.button(f"Reset to Preset {selected_universe}"):
        portfolio_type = "HK" if selected_universe == "Customised Portfolio_HK" else "US"
        st.session_state[f'{portfolio_key}_tickers'] = get_preset_portfolio(portfolio_type)
        st.rerun()
    
    # Reset the flag after use
    if st.session_state.reset_tickers:
        st.session_state.reset_tickers = False

# Main content area
if selected_universe:
    # Manually add some default tickers if none are found
    if (selected_universe == "Customised Portfolio_HK" or selected_universe == "Customised Portfolio_US") and (not custom_tickers or len(custom_tickers) == 0):
        portfolio_type = "HK" if selected_universe == "Customised Portfolio_HK" else "US"
        if portfolio_type == "HK":
            custom_tickers = ["0005.HK", "0700.HK", "3988.HK", "0388.HK", "1398.HK"]
            custom_benchmark = "^HSI"
        else:
            custom_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "META"]
            custom_benchmark = "^GSPC"
    
    # Get data for both timeframes
    weekly_data, daily_data, benchmark, sectors, sector_names = get_data(selected_universe, sector, custom_tickers, custom_benchmark)
    
    if weekly_data is not None and daily_data is not None and not weekly_data.empty and not daily_data.empty:
        # Create the RRG table
        rrg_table = create_rrg_table(weekly_data, daily_data, benchmark, sectors, sector_names, selected_universe)
        
        # Display the table with styling
        st.subheader(f"Asset Rotation Analysis for {universe_names[selected_universe]}")
        st.info(f"Benchmark: {benchmark}")
        
        # Apply styling and display
        styled_table = style_dataframe(rrg_table)
        st.dataframe(styled_table, use_container_width=True, height=600)
        
        # Add download buttons
        col1, col2 = st.columns(2)
        
        with col1:
            # Download to memory button
            excel_data = convert_df_to_excel(rrg_table)
            st.download_button(
                label="Download Excel (to Downloads folder)",
                data=excel_data,
                file_name=f"RRG_Analysis_{selected_universe}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        with col2:
            # Save to C:\B_Drive button
            if st.button("Save to C:\\B_Drive"):
                success, result = save_excel_to_drive(rrg_table, f"RRG_Analysis_{selected_universe}")
                if success:
                    st.success(f"File saved successfully to: {result}")
                else:
                    st.error(f"Error saving file: {result}")
        
        # Show data info
        st.subheader("Data Information")
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"Data range: {weekly_data.index.min().strftime('%Y-%m-%d')} to {weekly_data.index.max().strftime('%Y-%m-%d')}")
        with col2:
            # Calculate how old the data is
            latest_date = weekly_data.index.max()
            current_date = datetime.now()
            days_old = (current_date.date() - latest_date.date()).days
            
            if days_old == 0:
                st.success("✅ Data is current (updated today)")
            elif days_old == 1:
                st.info("ℹ️ Data is from yesterday")
            else:
                st.warning(f"⚠️ Data is {days_old} days old")
        
        if st.session_state.data_refreshed:
            st.success("Data refreshed successfully!")
            st.session_state.data_refreshed = False
    else:
        st.error("No data available for the selected universe and sector. Please try a different selection.")
else:
    st.write("Please select a universe from the sidebar.")

# Show raw data option
if st.checkbox("Show raw data"):
    if 'weekly_data' in locals() and weekly_data is not None and 'daily_data' in locals() and daily_data is not None:
        st.write("Weekly data (last 5 rows):")
        st.write(weekly_data.tail())
        st.write("Daily data (last 5 rows):")
        st.write(daily_data.tail())
        st.write("Sectors:")
        st.write(sectors)
        st.write("Benchmark:")
        st.write(benchmark)
