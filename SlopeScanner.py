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
]

SMA_LENGTH = 20
SLOPE_LENGTH = 20

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

def calculate_sma(df, length):
    return df['close'].rolling(window=length).mean()

def calculate_slope(series, length):
    """Calculate the slope of the series using linear regression"""
    x = np.arange(length)
    slopes = [np.nan] * (length - 1)
    for i in range(length, len(series) + 1):
        y = series[i-length:i]
        if len(y.dropna()) == length:
            slope = np.polyfit(x, y, 1)[0]
            slopes.append(slope)
        else:
            slopes.append(np.nan)
    return np.array(slopes)

def scan_stocks(stocks, api_key):
    results = []
    for stock in stocks:
        df = fetch_historical_data(stock, api_key)
        if not df.empty:
            df['SMA'] = calculate_sma(df, SMA_LENGTH)
            df['Slope'] = calculate_slope(df['SMA'], SLOPE_LENGTH)
            df['Positive_Slope_Change'] = (df['Slope'] > 0) & (df['Slope'].shift(1) <= 0)
            df['Negative_Slope_Change'] = (df['Slope'] < 0) & (df['Slope'].shift(1) >= 0)
            latest_date = df.index.max()
            positive_slope_changes = df[(df['Positive_Slope_Change']) & (df.index == latest_date)]
            negative_slope_changes = df[(df['Negative_Slope_Change']) & (df.index == latest_date)]
            for date, row in positive_slope_changes.iterrows():
                results.append({
                    'Stock': stock,
                    'Date': date,
                    'Close': row['close'],
                    'SMA': row['SMA'],
                    'Slope': row['Slope'],
                    'Signal': 'Buy'
                })
            for date, row in negative_slope_changes.iterrows():
                results.append({
                    'Stock': stock,
                    'Date': date,
                    'Close': row['close'],
                    'SMA': row['SMA'],
                    'Slope': row['Slope'],
                    'Signal': 'Sell'
                })
    return pd.DataFrame(results)

# Scan the stocks and save results to a file
results = scan_stocks(STOCKS, API_KEY)
filename = 'sma_slope_scanner_results.csv'
results.to_csv(filename, index=False)
print(f'Results saved to {filename}')
