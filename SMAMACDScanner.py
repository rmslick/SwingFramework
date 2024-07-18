import requests
import pandas as pd
import numpy as np

# Constants
API_KEY = 'Ksn2Xx77FfWgJiGQAxFBYirsdIHSCFjg'  # Replace with your Financial Modeling Prep API key
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

def calculate_indicators(df):
    df['SMA50'] = df['close'].rolling(window=50).mean()
    df['SMA200'] = df['close'].rolling(window=200).mean()
    df['SMA5'] = df['close'].rolling(window=5).mean()
    df['SMA10'] = df['close'].rolling(window=10).mean()

    # Calculate MACD
    df['EMA12'] = df['close'].ewm(span=12, adjust=False).mean()
    df['EMA26'] = df['close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = df['EMA12'] - df['EMA26']
    df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()

    return df

def scan_stocks(stocks, api_key):
    results = []
    for stock in stocks:
        df = fetch_historical_data(stock, api_key)
        if not df.empty:
            df = calculate_indicators(df)

            latest_date = df.index.max()
            recent_data = df.loc[latest_date]

            macd_crossover = (recent_data['MACD'] > recent_data['Signal_Line']) & (df['MACD'].shift(1).loc[latest_date] <= df['Signal_Line'].shift(1).loc[latest_date])
            sma_crossover_recent = any((df['SMA5'].shift(i) > df['SMA10'].shift(i)).iloc[-1] & (df['SMA5'].shift(i+1) <= df['SMA10'].shift(i+1)).iloc[-1] for i in range(3))
            sma5_slope_positive = recent_data['SMA5'] > df['SMA5'].shift(1).loc[latest_date]

            if recent_data['close'] > recent_data['SMA50'] and recent_data['close'] > recent_data['SMA200'] and macd_crossover and sma_crossover_recent and sma5_slope_positive:
                results.append({
                    'Stock': stock,
                    'Date': latest_date,
                    'Close': recent_data['close'],
                    'SMA50': recent_data['SMA50'],
                    'SMA200': recent_data['SMA200'],
                    'MACD': recent_data['MACD'],
                    'Signal Line': recent_data['Signal_Line'],
                    'SMA5': recent_data['SMA5'],
                    'SMA10': recent_data['SMA10']
                })

    return pd.DataFrame(results)

# Scan stocks
results = scan_stocks(STOCKS, API_KEY)

# Save results to CSV
filename = 'sma_macd_slope_scanner_results.csv'
results.to_csv(filename, index=False)
print(f'Results saved to {filename}')
