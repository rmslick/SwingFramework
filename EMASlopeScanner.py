import requests
import pandas as pd
import numpy as np

# Constants
API_KEY = 'api_here'  # Replace with your Financial Modeling Prep API key
STOCKS = [
    "AAPL", "MSFT", "NVDA",       # Information Technology
    "BRK.A", "JPM", "V",          # Financials
    "UNH", "JNJ", "LLY",          # Health Care
    "AMZN", "TSLA", "HD",         # Consumer Discretionary
    "GOOGL", "META", "NFLX",      # Communications Services
    "UNP", "HON", "BA",           # Industrials
    "PG", "PEP", "KO",            # Consumer Staples
    "XOM", "CVX", "COP",          # Energy
    "NEE", "DUK", "D",            # Utilities
    "AMT", "PLD", "EQIX",         # Real Estate
    "SO",                         # Utilities
    "SPY",                        # SPDR S&P 500 ETF Trust
    "IVV",                        # iShares Core S&P 500 ETF
    "VOO",                        # Vanguard S&P 500 ETF
    "SPLG",                       # SPDR Portfolio S&P 500 ETF
    "UPRO",                       # ProShares UltraPro S&P 500 (3x leverage)
    "SSO",                        # ProShares Ultra S&P 500 (2x leverage)
    "SPXL",                       # Direxion Daily S&P 500 Bull 3X Shares
    "SPXS",                       # Direxion Daily S&P 500 Bear 3X Shares (inverse)
    "SH",                         # ProShares Short S&P 500 (inverse)
    "VFINX",                      # Vanguard 500 Index Fund (mutual fund)
    "RSP",                        # Invesco S&P 500 Equal Weight ETF
    "XLG",                        # Invesco S&P 500 Top 50 ETF
    "IVW",                        # iShares S&P 500 Growth ETF
    "IVE",                        # iShares S&P 500 Value ETF
    "RWL",                        # Invesco S&P 500 Revenue ETF
    "XLC",                        # Communication Services Select Sector SPDR Fund
    "XLY",                        # Consumer Discretionary Select Sector SPDR Fund
    "XLP",                        # Consumer Staples Select Sector SPDR Fund
    "XLE",                        # Energy Select Sector SPDR Fund
    "XLF",                        # Financial Select Sector SPDR Fund
    "XLV",                        # Health Care Select Sector SPDR Fund
    "XLI",                        # Industrial Select Sector SPDR Fund
    "XLB",                        # Materials Select Sector SPDR Fund
    "XLRE",                       # Real Estate Select Sector SPDR Fund
    "XLK",                        # Technology Select Sector SPDR Fund
    "XLU"                         # Utilities Select Sector SPDR Fund
]

EMA_LENGTHS = [10, 20, 50, 100, 200]

def fetch_historical_data(symbol, api_key):
    url = f'https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}?apikey={api_key}'
    response = requests.get(url)
    data = response.json()
    if 'historical' in data:
        df = pd.DataFrame(data['historical'])
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        df.sort_index(inplace=True)
        return df
    else:
        return pd.DataFrame()

def calculate_ema(df, ema_length):
    df[f'EMA_{ema_length}'] = df['close'].ewm(span=ema_length, adjust=False).mean()
    return df

def detect_slope_changes(df, ema_length):
    slope_length = 5  # You can adjust the slope length if needed
    ema_col = f'EMA_{ema_length}'
    df['EMA_Slope'] = (df[ema_col] - df[ema_col].shift(slope_length)) / slope_length
    df['Positive_Slope_Change'] = (df['EMA_Slope'] > 0) & (df['EMA_Slope'].shift(1) <= 0)
    return df

def scan_stocks(stocks, ema_length, api_key):
    results = []
    for stock in stocks:
        df = fetch_historical_data(stock, api_key)
        if not df.empty:
            df = calculate_ema(df, ema_length)
            df = detect_slope_changes(df, ema_length)
            latest_date = df.index.max()
            positive_slope_changes = df[(df['Positive_Slope_Change']) & (df.index == latest_date)]
            for date, row in positive_slope_changes.iterrows():
                results.append({
                    'Stock': stock,
                    'Date': date,
                    'Close': row['close'],
                    'EMA_Length': ema_length,
                    'EMA_Value': row[f'EMA_{ema_length}'],
                    'EMA_Slope': row['EMA_Slope']
                })
    return pd.DataFrame(results)

# Iterate over EMA lengths and save results to files
for ema_length in EMA_LENGTHS:
    results = scan_stocks(STOCKS, ema_length, API_KEY)
    filename = f'ema_{ema_length}_slope_changes_today.csv'
    results.to_csv(filename, index=False)
    print(f'Results for EMA {ema_length} saved to {filename}')
