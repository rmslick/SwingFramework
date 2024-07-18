import glob
import subprocess
import os
import pandas as pd
import re
from collections import defaultdict
# Define the directory to search for scripts
directory = '.'  # Change to the directory where your scripts are located if needed

# Find all files ending with *Scanner.py
scanner_scripts = glob.glob(os.path.join(directory, '*Scanner.py'))
dataframes = []

# Execute each script
for script in scanner_scripts:
    print(f'Executing {script}...')
    result = subprocess.run(['python', script], capture_output=True, text=True)
    if result.returncode == 0:
        print(f'{script} executed successfully.')
    else:
        print(f'Error executing {script}:')
        print(result.stderr)

print('All scripts executed.')

# Post-processing: Find stock symbols that appear in more than one CSV file
csv_files = glob.glob(os.path.join(directory, '*.csv'))
symbol_files_map = defaultdict(list)

for csv_file in csv_files:
    try:
        df = pd.read_csv(csv_file)
        if not df.empty:
            for symbol in df['Stock'].unique():
                symbol_files_map[symbol].append(csv_file)
    except pd.errors.EmptyDataError:
        print(f'Skipping empty file: {csv_file}')
        continue

# Print stock symbols that appear in more than one CSV
print("\nStock symbols that appear in more than one CSV file:")
for symbol, files in symbol_files_map.items():
    if len(files) > 1:
        print(f'{symbol}: {", ".join(files)}')




def extract_strategy_and_signals(filename):
    if 'sma' in filename and 'crosses' in filename:
        match = re.search(r'sma_(\d+)_(\d+)_crosses', filename)
        if match:
            short_signal = match.group(1)
            long_signal = match.group(2)
            signal_length = 'N/A'
        strategy = 'SMA Cross'
    elif 'sma' in filename and 'slope_changes' in filename:
        match = re.search(r'sma_(\d+)_slope_changes', filename)
        if match:
            short_signal = 'N/A'
            long_signal = 'N/A'
            signal_length = match.group(1)
        strategy = 'SMA Slope Change'
    elif 'ema' in filename and 'crosses' in filename:
        match = re.search(r'ema_(\d+)_(\d+)_crosses', filename)
        if match:
            short_signal = match.group(1)
            long_signal = match.group(2)
            signal_length = 'N/A'
        strategy = 'EMA Cross'
    elif 'ema' in filename and 'slope_changes' in filename:
        match = re.search(r'ema_(\d+)_slope_changes', filename)
        if match:
            short_signal = 'N/A'
            long_signal = 'N/A'
            signal_length = match.group(1)
        strategy = 'EMA Slope Change'
    elif 'williams_alligator' in filename:
        short_signal = 'N/A'
        long_signal = 'N/A'
        signal_length = 'N/A'
        strategy = 'Williams Alligator'
    elif 'macd' in filename:
        short_signal = 'N/A'
        long_signal = 'N/A'
        signal_length = 'N/A'
        strategy = 'MACD'
    else:
        short_signal = 'N/A'
        long_signal = 'N/A'
        signal_length = 'N/A'
        strategy = 'Unknown'
    return strategy, short_signal, long_signal, signal_length

# Loop through all the files in the directory
for filename in os.listdir(directory):
    if filename.endswith('.csv'):
        filepath = os.path.join(directory, filename)
        try:
            # Read the CSV file into a DataFrame
            df = pd.read_csv(filepath)
            if df.empty:
                print(f'Skipping empty file: {filename}')
                continue
            # Extract the strategy and signals from the filename
            strategy, short_signal, long_signal, signal_length = extract_strategy_and_signals(filename)
            # Add the new columns to the DataFrame
            df['strategy'] = strategy
            df['short_signal'] = short_signal
            df['long_signal'] = long_signal
            df['signal_length'] = signal_length
            # Append the DataFrame to the list
            dataframes.append(df)
        except pd.errors.EmptyDataError:
            print(f'Skipping completely empty file: {filename}')

# Concatenate all the DataFrames into a single DataFrame
if dataframes:
    consolidated_df = pd.concat(dataframes, ignore_index=True)

    # Select only the relevant columns
    consolidated_df = consolidated_df[['Stock', 'Date', 'Close', 'strategy', 'short_signal', 'long_signal', 'signal_length']]

    # Save the consolidated DataFrame to a new CSV file
    consolidated_df.to_csv('consolidated_trades.csv', index=False)

    # Print the first few rows of the consolidated DataFrame
    print(consolidated_df.head())
else:
    print('No valid data found in the CSV files.')


# Define the path to the consolidated CSV file
consolidated_csv = 'consolidated_trades.csv'

# Define the paths to the backtest scripts
scripts = {
    'EMA Slope Change': 'BackTest/EMASlopeBacktest.py',
    'SMA Cross': 'BackTest/SMACrossBacktest.py',
    'Williams Alligator': 'BackTest/WIlliamsAlligatorBacktest.py',
    'MACD': 'BackTest/MACDBacktest.py',
    'SMA Slope Change': 'BackTest/SMASlopeBacktest.py'
}

# Load the consolidated CSV into a DataFrame
df = pd.read_csv(consolidated_csv)

# Define a function to run the backtest script with the given arguments
def run_backtest(script, args):
    cmd = ['python3', script] + args
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running {script}: {result.stderr}")
    else:
        print(f"Output: {result.stdout}")

# Walk through the DataFrame and invoke the relevant scripts
for _, row in df.iterrows():
    strategy = row['strategy']
    symbol = row['Stock']
    if strategy in scripts:
        script = scripts[strategy]
        if strategy == 'EMA Slope Change':
            length = row['signal_length']  # or 'long_signal' depending on your data
            args = [symbol, str(int(length))]
        elif strategy == 'SMA Cross':
            short_length = row['short_signal']
            long_length = row['long_signal']
            args = [symbol, str(int(short_length)), str(int(long_length))]
        elif strategy == 'Williams Alligator':
            args = [symbol]
        elif strategy == 'MACD':
            args = [symbol]
        elif strategy == 'SMA Slope Change':
            length = row['signal_length']  # or 'long_signal' depending on your data
            args = [symbol, str(int(length))]
        else:
            continue

        run_backtest(script, args)


import json
import numpy as np

# Define the directory to start the search
start_directory = '.'

# Initialize a list to store the performance metrics
performance_metrics_list = []

# Walk through the directory and subdirectories to find performance_metrics.json files
for root, _, files in os.walk(start_directory):
    for file in files:
        if file == 'performance_metrics.json':
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r') as f:
                    metrics = json.load(f)
                    performance_metrics_list.append(metrics)
            except Exception as e:
                print(f"Error reading {file_path}: {e}")

# Extract the values for normalization
percent_profitable = [metrics["Percent Profitable"] for metrics in performance_metrics_list]
profit_factor = [metrics["Profit Factor"] for metrics in performance_metrics_list]
total_profit_loss = [metrics["Total Profit/Loss"] for metrics in performance_metrics_list]

# Normalize the values using min-max normalization
percent_profitable_norm = (np.array(percent_profitable) - np.min(percent_profitable)) / (np.max(percent_profitable) - np.min(percent_profitable))
profit_factor_norm = (np.array(profit_factor) - np.min(profit_factor)) / (np.max(profit_factor) - np.min(profit_factor))
total_profit_loss_norm = (np.array(total_profit_loss) - np.min(total_profit_loss)) / (np.max(total_profit_loss) - np.min(total_profit_loss))

# Combine the normalized values into a single score
scores = percent_profitable_norm + profit_factor_norm + total_profit_loss_norm

# Add the scores to the performance metrics
for i, metrics in enumerate(performance_metrics_list):
    metrics["Score"] = scores[i]

# Sort the list of dictionaries by the combined score
performance_metrics_list.sort(key=lambda x: x["Percent Profitable"], reverse=True)

# Define the output file path
output_file_path = os.path.join(os.getcwd(), 'performance_metrics.json')

# Save the sorted list to the JSON file
with open(output_file_path, 'w') as f:
    for metrics in performance_metrics_list:
        f.write(json.dumps(metrics, indent=4) + '\n')

print(f'Performance metrics saved to {output_file_path}')
