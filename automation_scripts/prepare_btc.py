import pandas as pd

# reading big file
df = pd.read_csv('data/btcusd_1-min_data.csv')
# Extracts only the Close column by removing null values
close_prices = df['Close'].dropna()
# Save a C++ and GitHub compatible plain text file (under 100MB)
close_prices.to_csv('data/bitcoin_close_1m.txt', index=False, header=False)
print("File bitcoin_close_1m.txt has been successfully generated!")