import pandas as pd
import requests
import json
import os
import argparse
from datetime import datetime, timedelta

# Define the path to the configuration file
config_file_path = os.path.join(os.path.dirname(__file__), 'config.json')

# Load the configuration from the JSON file
with open(config_file_path, 'r') as config_file:
    config = json.load(config_file)

# Define parameters from the configuration file
API_KEY = config['API_KEY']
YEARS_TO_LOOK_BACK = config['YEARS_TO_LOOK_BACK']
INITIAL_CASH = config['INITIAL_CASH']
PERCENT_TO_INVEST = config['PERCENT_TO_INVEST']
PERCENT_STOP_LOSS = config['PERCENT_STOP_LOSS']
STRATEGY_TITLE = 'MACD and SMA Crossover Strategy with Positioning'

# Parse command-line arguments
parser = argparse.ArgumentParser(description='MACD and SMA Crossover Backtesting Script')
parser.add_argument('symbol', type=str, help='Stock symbol to backtest')
args = parser.parse_args()

SYMBOL = args.symbol

# Calculate date range
END_DATE = datetime.now()
START_DATE = END_DATE - timedelta(days=YEARS_TO_LOOK_BACK * 365)

# Fetch historical stock data
URL = f'https://financialmodelingprep.com/api/v3/historical-price-full/{SYMBOL}?from={START_DATE.strftime("%Y-%m-%d")}&to={END_DATE.strftime("%Y-%m-%d")}&apikey={API_KEY}'
response = requests.get(URL)
data = response.json()

# Convert data to DataFrame
df = pd.DataFrame(data['historical'])
df['date'] = pd.to_datetime(df['date'])
df.set_index('date', inplace=True)
df = df.sort_index()

# Calculate SMAs
df['SMA50'] = df['close'].rolling(window=50).mean()
df['SMA200'] = df['close'].rolling(window=200).mean()
df['SMA5'] = df['close'].rolling(window=5).mean()
df['SMA10'] = df['close'].rolling(window=10).mean()

# Calculate MACD
df['EMA12'] = df['close'].ewm(span=12, adjust=False).mean()
df['EMA26'] = df['close'].ewm(span=26, adjust=False).mean()
df['MACD'] = df['EMA12'] - df['EMA26']
df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()

# Generate buy/sell signals
df['Signal'] = 0
df['MACD_Crossover'] = (df['MACD'] > df['Signal_Line']) & (df['MACD'].shift(1) <= df['Signal_Line'].shift(1))
df['SMA5_Slope_Positive'] = df['SMA5'] > df['SMA5'].shift(1)
df['SMA_Crossover_Recent'] = df['SMA5'].shift(1).rolling(window=3).apply(lambda x: any(x > df['SMA10'].shift(1).rolling(window=3).apply(lambda y: y.any())), raw=False)

# Check buy conditions
df.loc[(df['close'] > df['SMA50']) & (df['close'] > df['SMA200']) & df['MACD_Crossover'] & df['SMA_Crossover_Recent'] & df['SMA5_Slope_Positive'], 'Signal'] = 1
df.loc[df['MACD'] < df['Signal_Line'], 'Signal'] = -1  # Sell signal

# Correctly set the Position column
df['Position'] = df['Signal'].shift().fillna(0)

# Initialize backtesting variables
cash = INITIAL_CASH
account_value = INITIAL_CASH
shares = 0
trades = []

# Backtest the strategy
for i in range(1, len(df)):
    if df['Position'].iloc[i] == 1 and df['Position'].iloc[i-1] != 1:  # Buy signal
        amount_to_invest = account_value * PERCENT_TO_INVEST
        shares = amount_to_invest // df['close'].iloc[i]
        stop_loss_price = df['close'].iloc[i] * (1 - PERCENT_STOP_LOSS)
        cash -= shares * df['close'].iloc[i]
        trades.append({
            'type': 'buy',
            'date': df.index[i],
            'price': df['close'].iloc[i],
            'shares': shares,
            'stop_loss': stop_loss_price
        })
    elif df['Position'].iloc[i] == -1 and df['Position'].iloc[i-1] != -1 and shares > 0:  # Sell signal
        cash += shares * df['close'].iloc[i]
        trades.append({
            'type': 'sell',
            'date': df.index[i],
            'price': df['close'].iloc[i],
            'shares': shares,
            'stopped_out': False
        })
        shares = 0
    '''
    elif shares > 0 and df['close'].iloc[i] <= trades[-1]['stop_loss']:  # Stop loss condition
        cash += shares * df['close'].iloc[i]
        trades.append({
            'type': 'sell',
            'date': df.index[i],
            'price': df['close'].iloc[i],
            'shares': shares,
            'stopped_out': True
        })
        shares = 0
    '''
    account_value = cash + shares * df['close'].iloc[i]

# Create trading log DataFrame
trade_log = []
for i in range(1, len(trades), 2):
    buy_trade = trades[i-1]
    sell_trade = trades[i]
    profit = (sell_trade['price'] - buy_trade['price']) * buy_trade['shares']
    trade_log.append({
        'Date Bought': buy_trade['date'],
        'Date Sold': sell_trade['date'],
        'Quantity': buy_trade['shares'],
        'Entry Price': buy_trade['price'],
        'Exit Price': sell_trade['price'],
        'Profit/Loss': profit,
        'Stopped Out': sell_trade.get('stopped_out', False)
    })

trade_log_df = pd.DataFrame(trade_log)

# Compute performance metrics
total_trades = len(trade_log_df)
profitable_trades = len(trade_log_df[trade_log_df['Profit/Loss'] > 0])
percent_profitable = (profitable_trades / total_trades) * 100 if total_trades > 0 else 0

gross_profit = trade_log_df[trade_log_df['Profit/Loss'] > 0]['Profit/Loss'].sum()
gross_loss = trade_log_df[trade_log_df['Profit/Loss'] <= 0]['Profit/Loss'].sum()
profit_factor = (gross_profit / abs(gross_loss)) if gross_loss != 0 else float('inf')

total_profit_loss = trade_log_df['Profit/Loss'].sum()

# Performance metrics dictionary
performance_metrics = {
    'Strategy Title': STRATEGY_TITLE,
    'Symbol': SYMBOL,
    'Total Trades': total_trades,
    'Percent Profitable': percent_profitable,
    'Profit Factor': profit_factor,
    'Total Profit/Loss': total_profit_loss
}

# Define directories
results_dir = 'MACD_SMA_Crossover_Results'
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
result_dir_with_timestamp = os.path.join(results_dir, SYMBOL, timestamp)

# Create directories if they do not exist
os.makedirs(result_dir_with_timestamp, exist_ok=True)

# Save trading log to CSV
trade_log_csv_path = os.path.join(result_dir_with_timestamp, 'trading_log.csv')
trade_log_df.to_csv(trade_log_csv_path, index=False)

# Save performance metrics to JSON
performance_metrics_json_path = os.path.join(result_dir_with_timestamp, 'performance_metrics.json')
with open(performance_metrics_json_path, 'w') as f:
    json.dump(performance_metrics, f, indent=4)

# Save the config file
config_json_path = os.path.join(result_dir_with_timestamp, 'config.json')
with open(config_json_path, 'w') as f:
    json.dump(config, f, indent=4)

# Print performance metrics
print(performance_metrics)

# Print the first few rows of the trading log
print(trade_log_df.head())
