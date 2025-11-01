import pandas as pd

# Read the CSV file
df = pd.read_csv('transactions_mock_1000_for_participants.csv')

# Print the head of the dataframe
print("Original DataFrame:")
print(df.head())
print("\n" + "="*80 + "\n")

# Drop transaction_id and swift_f70_purpose columns
df = df.drop(columns=['transaction_id', 'swift_f70_purpose, 'value_date'])
df = df.drop(columns=['booking_jurisdiction'])
# filter regulator for "MAS"
df = df[df['regulator'] == 'MAS']

# Print the head again after dropping columns
print("DataFrame after dropping 'transaction_id' and 'swift_f70_purpose':")
print(df.head())
