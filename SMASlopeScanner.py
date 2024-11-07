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

SMA_LENGTHS = [10, 20, 50, 100, 200]

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

def calculate_sma(df, sma_length):
    df[f'SMA_{sma_length}'] = df['close'].rolling(window=sma_length).mean()
    return df

def detect_slope_changes(df, sma_length):
    slope_length = 5  # You can adjust the slope length if needed
    sma_col = f'SMA_{sma_length}'
    df['SMA_Slope'] = (df[sma_col] - df[sma_col].shift(slope_length)) / slope_length
    df['Positive_Slope_Change'] = (df['SMA_Slope'] > 0) & (df['SMA_Slope'].shift(1) <= 0)
    return df

def scan_stocks(stocks, sma_length, api_key):
    results = []
    for stock in stocks:
        df = fetch_historical_data(stock, api_key)
        if not df.empty:
            df = calculate_sma(df, sma_length)
            df = detect_slope_changes(df, sma_length)
            latest_date = df.index.max()
            positive_slope_changes = df[(df['Positive_Slope_Change']) & (df.index == latest_date)]
            for date, row in positive_slope_changes.iterrows():
                results.append({
                    'Stock': stock,
                    'Date': date,
                    'Close': row['close'],
                    'SMA_Length': sma_length,
                    'SMA_Value': row[f'SMA_{sma_length}'],
                    'SMA_Slope': row['SMA_Slope']
                })
    return pd.DataFrame(results)

# Iterate over SMA lengths and save results to files
for sma_length in SMA_LENGTHS:
    results = scan_stocks(STOCKS, sma_length, API_KEY)
    filename = f'sma_{sma_length}_slope_changes_today.csv'
    results.to_csv(filename, index=False)
    print(f'Results for SMA {sma_length} saved to {filename}')
