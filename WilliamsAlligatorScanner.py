import requests
import pandas as pd

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

def calculate_smas(df, jaw_length=13, jaw_shift=8, teeth_length=8, teeth_shift=5, lips_length=5, lips_shift=3):
    df['SMA_Jaw'] = df['close'].rolling(window=jaw_length).mean().shift(jaw_shift)
    df['SMA_Teeth'] = df['close'].rolling(window=teeth_length).mean().shift(teeth_shift)
    df['SMA_Lips'] = df['close'].rolling(window=lips_length).mean().shift(lips_shift)
    df['SMA_200'] = df['close'].rolling(window=200).mean()
    return df

def detect_alligator_signals(df):
    df['Teeth_above_Jaw'] = df['SMA_Teeth'] > df['SMA_Jaw']
    df['Teeth_above_Jaw'] = df['Teeth_above_Jaw'].astype(bool)
    df['Teeth_crossed_Jaw'] = df['Teeth_above_Jaw'] & (~df['Teeth_above_Jaw'].shift(1).fillna(False).astype(bool))
    df['Buy_Signal'] = df['Teeth_crossed_Jaw'] & (df['SMA_Lips'] > df['SMA_Teeth']) & (df['SMA_Lips'] > df['SMA_Jaw']) & (df['close'] > df['SMA_200'])
    return df

def scan_stocks(stocks, api_key):
    results = []
    for stock in stocks:
        df = fetch_historical_data(stock, api_key)
        if not df.empty:
            df = calculate_smas(df)
            df = detect_alligator_signals(df)
            latest_date = df.index.max()
            buy_signals = df[(df['Buy_Signal']) & (df.index == latest_date)]
            for date, row in buy_signals.iterrows():
                results.append({
                    'Stock': stock,
                    'Date': date,
                    'Close': row['close'],
                    'SMA_Jaw': row['SMA_Jaw'],
                    'SMA_Teeth': row['SMA_Teeth'],
                    'SMA_Lips': row['SMA_Lips'],
                    'SMA_200': row['SMA_200']
                })
    return pd.DataFrame(results)

# Run the scanner
results = scan_stocks(STOCKS, API_KEY)

# Save the results to a CSV file
filename = 'williams_alligator_buy_signals_today.csv'
results.to_csv(filename, index=False)
print(f'Results saved to {filename}')
