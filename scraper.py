import os
import csv
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz
import sys

BAR_INTERVAL = pd.Timedelta(minutes=5)
CSV_HEADER = ['Timestamp', 'Current Price', 'Ticker', 'Open', 'High', 'Low', 'Close', 'Volume', 'RSI', 'SMA10', 'SMA50', 'SMA200']


def get_saveable_row(data, now=None):
    """Return the latest completed 5-minute bar.

    yfinance's last row is the in-progress interval bar whose OHLCV and indicators
    are still changing. During an active interval we persist the previous bar instead.
    """
    if data is None or data.empty:
        return None

    last_row = data.iloc[-1]
    last_ts = last_row.name
    if now is None:
        tz = last_ts.tzinfo if getattr(last_ts, "tzinfo", None) else pytz.UTC
        now = pd.Timestamp.now(tz=tz)

    if now >= last_ts + BAR_INTERVAL:
        return last_row

    if len(data) >= 2:
        return data.iloc[-2]

    return None


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

    return latest_row.get('Timestamp'), latest_row.get('Ticker')


# Function to get the current timestamp in EST
def get_est_timestamp(utc_timestamp):
    utc_dt = utc_timestamp.to_pydatetime().replace(tzinfo=pytz.utc)
    est_dt = utc_dt.astimezone(pytz.timezone("US/Eastern"))
    return est_dt.strftime("%Y-%m-%d %H:%M:%S %Z")

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

    latest_data = get_saveable_row(data)
    if latest_data is None:
        print(f"No completed 5-minute bar available for {ticker}.")
        return None

    # Ensure all extracted values are scalars using `.item()`
    data_to_save = {
        'Timestamp': get_est_timestamp(latest_data.name),  # Convert to EST
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
    if data_to_save is None:
        print(f"No data saved for {ticker}.")
        return

    record_key = (data_to_save['Timestamp'], data_to_save['Ticker'])
    if get_latest_record_key(csv_filename) == record_key:
        print(f"Skipping already-saved bar for {ticker}: {data_to_save['Timestamp']}")
        return

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
