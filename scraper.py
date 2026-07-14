import os
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz
import sys

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

    # Get the most recent data (latest available 5-minute interval)
    latest_data = data.iloc[-1]

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

def get_csv_filename(ticker):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, f'{ticker}_stock_data.csv')

# Main function to fetch data and append to the CSV file
def main(ticker):
    csv_filename = get_csv_filename(ticker)

    print(f"Fetching stock data for {ticker}...")
    data_to_save = get_stock_data(ticker)

    # Convert the data to a row suitable for CSV
    header = ['Timestamp', 'Current Price', 'Ticker', 'Open', 'High', 'Low', 'Close', 'Volume', 'RSI', 'SMA10', 'SMA50', 'SMA200']
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
    file_exists = os.path.exists(csv_filename)

    with open(csv_filename, mode='a') as file:
        # Write header only if the file is being created for the first time
        if not file_exists:
            file.write(','.join(header) + '\n')
        
        # Append the new row of data
        file.write(','.join(map(str, row_to_write)) + '\n')

    print(f"Data saved successfully for {ticker}: {row_to_write}")

# Run the script with a ticker passed as a command-line argument
if __name__ == "__main__":
    if len(sys.argv) > 1:
        ticker = sys.argv[1]
        main(ticker)
    else:
        print("Please provide a ticker symbol as a command-line argument.")
