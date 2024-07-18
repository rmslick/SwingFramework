import requests
import pandas as pd
import numpy as np

# Constants
API_KEY = 'Ksn2Xx77FfWgJiGQAxFBYirsdIHSCFjg'  # Replace with your Financial Modeling Prep API key
STOCKS = [
    "AAPL", "MSFT", "NVDA",       # Information Technology
    "BRK.A", "JPM", "V", "WFC",          # Financials
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

def calculate_macd(df):
    df['EMA_12'] = df['close'].ewm(span=12, adjust=False).mean()
    df['EMA_26'] = df['close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = df['EMA_12'] - df['EMA_26']
    df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['Signal_Line']
    return df

def calculate_rsi(df, period=14):
    delta = df['close'].diff(1)
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period, min_periods=1).mean()
    avg_loss = loss.rolling(window=period, min_periods=1).mean()
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

def scan_stocks(stocks, api_key):
    results = []
    for stock in stocks:
        df = fetch_historical_data(stock, api_key)
        if not df.empty:
            df = calculate_macd(df)
            df = calculate_rsi(df)
            latest_date = df.index.max()
            recent = df.loc[latest_date]
            macd_buy_signal = recent['MACD'] > recent['Signal_Line'] and df['MACD'].iloc[-2] <= df['Signal_Line'].iloc[-2]
            #rsi_confirmation = recent['RSI'] < 30
            if macd_buy_signal: #and rsi_confirmation:
                results.append({
                    'Stock': stock,
                    'Date': latest_date,
                    'Close': recent['close'],
                    'MACD': recent['MACD'],
                    'Signal Line': recent['Signal_Line'],
                    'RSI': recent['RSI']
                })
    return pd.DataFrame(results)

# Scan stocks
results = scan_stocks(STOCKS, API_KEY)

# Save results to CSV
filename = 'macd_rsi_scanner_results.csv'
results.to_csv(filename, index=False)
print(f'Results saved to {filename}')
