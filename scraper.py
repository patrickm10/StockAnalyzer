import os
import csv
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz
import sys

CSV_HEADER = ['Timestamp', 'Current Price', 'Ticker', 'Open', 'High', 'Low', 'Close', 'Volume', 'RSI', 'SMA10', 'SMA50', 'SMA200']
EASTERN = pytz.timezone("US/Eastern")


def normalize_to_eastern(timestamp):
    dt = timestamp.to_pydatetime() if hasattr(timestamp, "to_pydatetime") else timestamp
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        dt = pytz.utc.localize(dt)
    return dt.astimezone(EASTERN)


def floor_to_five_minute_bar(timestamp):
    est_dt = normalize_to_eastern(timestamp)
    floored_minute = (est_dt.minute // 5) * 5
    return est_dt.replace(minute=floored_minute, second=0, microsecond=0)


def format_bar_timestamp(timestamp):
    return floor_to_five_minute_bar(timestamp).strftime("%Y-%m-%d %H:%M:%S %Z")


def get_bar_record_key(timestamp_str, ticker):
    timestamp_part = timestamp_str.rsplit(" ", 1)[0]
    parsed = datetime.strptime(timestamp_part, "%Y-%m-%d %H:%M:%S")
    localized = EASTERN.localize(parsed)
    floored = floor_to_five_minute_bar(localized)
    return floored.strftime("%Y-%m-%d %H:%M:%S"), ticker


def get_latest_record_key(csv_filename):
    if not os.path.exists(csv_filename):
        return None

    with open(csv_filename, mode='r', newline='') as file:
        reader = csv.DictReader(file)
        latest_row = None
        for row in reader:
            latest_row = row

    if not latest_row:
        return None

    timestamp = latest_row.get('Timestamp')
    ticker = latest_row.get('Ticker')
    if not timestamp or not ticker:
        return None

    return get_bar_record_key(timestamp, ticker)


# Function to calculate RSI
def calculate_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    avg_gain = gain.rolling(window=window, min_periods=1).mean()
    avg_loss = loss.rolling(window=window, min_periods=1).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# Function to calculate Simple Moving Average (SMA)
def calculate_sma(data, window):
    return data['Close'].rolling(window=window).mean()

# Function to fetch and process stock data
def get_stock_data(ticker):
    # Get historical data, including pre-market and after-hours
    data = yf.download(ticker, period="2d", interval="5m", prepost=True)

    # Drop any rows with missing data
    data.dropna(inplace=True)

    # Calculate RSI and Moving Averages
    data['RSI'] = calculate_rsi(data, window=14)
    data['SMA10'] = calculate_sma(data, window=10)
    data['SMA50'] = calculate_sma(data, window=50)
    data['SMA200'] = calculate_sma(data, window=200)

    # Get the most recent data (latest available 5-minute interval)
    latest_data = data.iloc[-1]

    # Ensure all extracted values are scalars using `.item()`
    data_to_save = {
        'Timestamp': format_bar_timestamp(latest_data.name),
        'Current Price': latest_data['Close'].item(),
        'Ticker': ticker,
        'Open': latest_data['Open'].item(),
        'High': latest_data['High'].item(),
        'Low': latest_data['Low'].item(),
        'Close': latest_data['Close'].item(),
        'Volume': latest_data['Volume'].item(),
        'RSI': latest_data['RSI'].item(),
        'SMA10': latest_data['SMA10'].item(),
        'SMA50': latest_data['SMA50'].item(),
        'SMA200': latest_data['SMA200'].item(),
    }

    return data_to_save

# Main function to fetch data and append to the CSV file
def main(ticker):
    csv_filename = f'{ticker}_stock_data.csv'

    print(f"Fetching stock data for {ticker}...")
    data_to_save = get_stock_data(ticker)

    # Convert the data to a row suitable for CSV
    row_to_write = [
        data_to_save['Timestamp'],
        data_to_save['Current Price'],
        data_to_save['Ticker'],
        data_to_save['Open'],
        data_to_save['High'],
        data_to_save['Low'],
        data_to_save['Close'],
        data_to_save['Volume'],
        data_to_save['RSI'],
        data_to_save['SMA10'],
        data_to_save['SMA50'],
        data_to_save['SMA200'],
    ]

    record_key = get_bar_record_key(data_to_save['Timestamp'], data_to_save['Ticker'])
    if get_latest_record_key(csv_filename) == record_key:
        print(f"Skipping duplicate 5-minute bar for {ticker}: {data_to_save['Timestamp']}")
        return

    # Append data to the CSV file
    file_needs_header = not os.path.exists(csv_filename) or os.path.getsize(csv_filename) == 0

    with open(csv_filename, mode='a', newline='') as file:
        writer = csv.writer(file)

        if file_needs_header:
            writer.writerow(CSV_HEADER)

        writer.writerow(row_to_write)

    print(f"Data saved successfully for {ticker}: {row_to_write}")

# Run the script with a ticker passed as a command-line argument
if __name__ == "__main__":
    if len(sys.argv) > 1:
        ticker = sys.argv[1]
        main(ticker)
    else:
        print("Please provide a ticker symbol as a command-line argument.")
