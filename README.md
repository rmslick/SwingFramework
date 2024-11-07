
# Configurable Stock Strategy Scanner

This repository provides a configurable pipeline for executing, analyzing, and backtesting various stock trading strategies. It leverages **pandas** for efficient data handling and **NumPy** for performance metric normalization and scoring.

## Overview of Components

1. **ScanDriver**: Orchestrates the execution of strategy scanners and backtests based on configurations.
2. **Scanner Execution**: Finds and executes all `*Scanner.py` scripts to generate strategy-specific CSV files.
3. **Duplicate Symbol Detection**: Identifies stock symbols that appear in multiple strategy outputs.
4. **CSV Processing with DataFrames**: Loads CSV files, appends strategy metadata, and consolidates them into a single DataFrame.
5. **Backtesting**: Runs backtest scripts for each identified strategy.
6. **Performance Evaluation with NumPy**: Normalizes performance metrics across strategies and generates a ranked JSON report.

---

## How It Works

### ScanDriver Overview

`ScanDriver` acts as the primary control module, managing the execution flow for the entire strategy scanning and backtesting process. It is designed to:
- **Automatically Discover Scanner Scripts**: Searches for Python scripts ending in `*Scanner.py` in the configured directory.
- **Invoke Scanners Dynamically**: Executes each scanner script independently, capturing output in CSV format for post-processing.
- **Run Backtests by Strategy**: Based on the strategy detected in each CSV file, `ScanDriver` invokes the relevant backtest script with appropriate arguments (e.g., stock symbol, signal lengths).

### Configuration-Based Invocation

- **Dynamic Strategy Detection**: Each CSV filename indicates the trading strategy it contains (e.g., `sma_20_50_crosses`). `ScanDriver` extracts strategy parameters directly from filenames.
- **Strategy-to-Script Mapping**: A dictionary links each strategy type to a specific backtest script, allowing `ScanDriver` to determine which backtest to run based on the configuration.
- **Flexible Configuration**: New strategies can be easily added by creating a new scanner and backtest script and updating the strategy-to-script mapping.

---

## Detailed Workflow

### 1. Scanner Script Execution

```python
import glob
import subprocess
import os

# Define the directory to search for scripts
directory = '.'  # Modify if scripts are in a different directory

# Find and execute each scanner script
scanner_scripts = glob.glob(os.path.join(directory, '*Scanner.py'))
for script in scanner_scripts:
    print(f'Executing {script}...')
    result = subprocess.run(['python', script], capture_output=True, text=True)
    if result.returncode != 0:
        print(f'Error executing {script}:
{result.stderr}')
print('All scripts executed.')
```

### 2. Finding Duplicate Stock Symbols Using DataFrames

```python
import pandas as pd
from collections import defaultdict

# Mapping symbols to CSV files they appear in
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

# Print duplicates
print("\nStock symbols in multiple CSV files:")
for symbol, files in symbol_files_map.items():
    if len(files) > 1:
        print(f'{symbol}: {", ".join(files)}')
```

### 3. Extract Strategy Information from Filenames

```python
import re

# Function to extract strategy and signal details from filenames
def extract_strategy_and_signals(filename):
    if 'sma' in filename and 'crosses' in filename:
        match = re.search(r'sma_(\d+)_(\d+)_crosses', filename)
        strategy = 'SMA Cross'
        short_signal = match.group(1) if match else 'N/A'
        long_signal = match.group(2) if match else 'N/A'
        signal_length = 'N/A'
    # Additional patterns omitted for brevity
    else:
        strategy, short_signal, long_signal, signal_length = 'N/A', 'N/A', 'N/A', 'N/A'
    return strategy, short_signal, long_signal, signal_length
```

### 4. Consolidate CSV Files into a Single DataFrame

```python
dataframes = []
for filename in os.listdir(directory):
    if filename.endswith('.csv'):
        df = pd.read_csv(filename)
        if df.empty:
            print(f'Skipping empty file: {filename}')
            continue

        # Extract and append strategy details
        strategy, short_signal, long_signal, signal_length = extract_strategy_and_signals(filename)
        if strategy != 'N/A':
            df['strategy'] = strategy
            df['short_signal'] = short_signal
            df['long_signal'] = long_signal
            df['signal_length'] = signal_length
            dataframes.append(df)

# Combine all DataFrames into a consolidated one
if dataframes:
    consolidated_df = pd.concat(dataframes, ignore_index=True)
    consolidated_df = consolidated_df[['Stock', 'Date', 'Close', 'strategy', 'short_signal', 'long_signal', 'signal_length']]
    consolidated_df.to_csv('consolidated_trades.csv', index=False)
    print(consolidated_df.head())
else:
    print('No valid data found.')
```

### 5. Running Backtests Based on Strategy

```python
# Dictionary linking strategies to their backtest scripts
scripts = {
    'EMA Slope Change': 'BackTest/EMASlopeBacktest.py',
    'SMA Cross': 'BackTest/SMACrossBacktest.py',
    # Additional scripts omitted for brevity
}

# Function to execute backtest scripts
def run_backtest(script, args):
    cmd = ['python3', script] + args
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")

# Run relevant backtest for each row in the consolidated DataFrame
df = pd.read_csv('consolidated_trades.csv')
for _, row in df.iterrows():
    strategy, symbol = row['strategy'], row['Stock']
    if strategy in scripts:
        script = scripts[strategy]
        args = [symbol] + [row['short_signal'], row['long_signal']] if strategy == 'SMA Cross' else [symbol]
        run_backtest(script, args)
```

### 6. Evaluating Performance Metrics with NumPy

```python
import numpy as np
import json

# Collect and normalize performance metrics using NumPy arrays
performance_metrics_list = []
start_directory = '.'

# Load JSON metrics from files
for root, _, files in os.walk(start_directory):
    for file in files:
        if file == 'performance_metrics.json':
            with open(os.path.join(root, file)) as f:
                performance_metrics_list.append(json.load(f))

# Normalize Percent Profitable, Profit Factor, Total Profit/Loss
percent_profitable = np.array([m["Percent Profitable"] for m in performance_metrics_list])
profit_factor = np.array([m["Profit Factor"] for m in performance_metrics_list])
total_profit_loss = np.array([m["Total Profit/Loss"] for m in performance_metrics_list])

percent_profitable_norm = (percent_profitable - percent_profitable.min()) / (percent_profitable.max() - percent_profitable.min())
profit_factor_norm = (profit_factor - profit_factor.min()) / (profit_factor.max() - profit_factor.min())
total_profit_loss_norm = (total_profit_loss - total_profit_loss.min()) / (total_profit_loss.max() - total_profit_loss.min())

# Calculate combined scores
scores = percent_profitable_norm + profit_factor_norm + total_profit_loss_norm

# Add scores to metrics and sort by score
for i, metrics in enumerate(performance_metrics_list):
    metrics["Score"] = scores[i]
performance_metrics_list.sort(key=lambda x: x["Score"], reverse=True)

# Save sorted metrics to a JSON file
with open('performance_metrics_sorted.json', 'w') as f:
    json.dump(performance_metrics_list, f, indent=4)
print('Performance metrics saved.')
```

---

## Key Highlights

1. **Efficient Data Processing with DataFrames**:
   - **Loading and Merging**: All strategy output CSV files are read into DataFrames, and strategy-specific metadata is appended.
   - **Consolidation**: Multiple DataFrames are concatenated to create a single, comprehensive dataset, enabling easy querying and further analysis.

2. **NumPy Array Normalization**:
   - **Min-Max Scaling**: The performance metrics (`Percent Profitable`, `Profit Factor`, `Total Profit/Loss`) are normalized using **NumPy arrays** for efficient mathematical operations.
   - **Combined Scoring**: Using NumPy’s vectorized operations, normalized values are summed to produce a combined score for ranking strategies.

This configurable scanner demonstrates an integrated use of **pandas** for data management and **NumPy** for performance normalization, making it a highly adaptable tool for stock trading analysis.
