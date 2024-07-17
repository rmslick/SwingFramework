import requests
import pandas as pd
import numpy as np

# Replace with your Financial Modeling Prep API key
#api_key = 'Ksn2Xx77FfWgJiGQAxFBYirsdIHSCFjg'

# List of stock symbols you want to monitor
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
    "AMT", "PLD", "EQIX",          # Real Estate
    "SO",
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
    "RWL"                        # Invesco S&P 500 Revenue ETF
]
SMA_COMBINATIONS = [(5, 10), (10, 20), (20, 50), (50, 100), (50, 200), (9, 21), (13, 34), (20, 100)]

# Constants
API_KEY = 'Ksn2Xx77FfWgJiGQAxFBYirsdIHSCFjg'  # Replace with your Financial Modeling Prep API key
#STOCKS = ['AAPL', 'MSFT', 'GOOGL']  # Sample list of stocks
SHORT_SMA = 5
LONG_SMA = 10

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

def calculate_smas(df, short_sma, long_sma):
    df[f'SMA_{short_sma}'] = df['close'].rolling(window=short_sma).mean()
    df[f'SMA_{long_sma}'] = df['close'].rolling(window=long_sma).mean()
    return df

def detect_crossovers(df, short_sma, long_sma):
    df['Signal'] = 0
    df['Signal'][short_sma:] = np.where(df[f'SMA_{short_sma}'][short_sma:] > df[f'SMA_{long_sma}'][short_sma:], 1, 0)
    df['Crossover'] = df['Signal'].diff()
    return df

def scan_stocks(stocks, short_sma, long_sma, api_key):
    results = []
    for stock in stocks:
        df = fetch_historical_data(stock, api_key)
        if not df.empty:
            df = calculate_smas(df, short_sma, long_sma)
            df = detect_crossovers(df, short_sma, long_sma)
            latest_date = df.index.max()
            crossovers = df[(df['Crossover'] == 1) & (df.index == latest_date)]  # Filter for Golden Crosses today
            for date, row in crossovers.iterrows():
                results.append({
                    'Stock': stock,
                    'Date': date,
                    'Close': row['close'],
                    'Short_SMA': row[f'SMA_{short_sma}'],
                    'Long_SMA': row[f'SMA_{long_sma}'],
                    'Crossover_Type': 'Golden Cross'
                })
    return pd.DataFrame(results)

# Iterate over SMA combinations and save results to files
for short_sma, long_sma in SMA_COMBINATIONS:
    results = scan_stocks(STOCKS, short_sma, long_sma, API_KEY)
    filename = f'sma_{short_sma}_{long_sma}_crosses_today.csv'
    results.to_csv(filename, index=False)
    print(f'Results for SMA {short_sma} and {long_sma} saved to {filename}')

# Print the results of Golden Crosses today
print("Stocks with Golden Crosses today:")
print(results)
# results.to_csv('golden_crosses_today.csv', index=False)  # Optionally save to CSV

# Print or save the results
print(results)
# results.to_csv('sma_crossovers.csv', index=False)
