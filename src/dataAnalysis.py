import pandas as pd

# === 1. Load the dataset ===
file_path = "./data/transactions_mock_1000_for_participants.csv"
df = pd.read_csv(file_path)

print("\n=== Basic Info ===")
print(df.info())

print("\n=== Preview ===")
print(df.head())

# === 2. Basic statistics ===
print("\n=== Summary Statistics ===")
print(df.describe(include='all'))

# === 3. Missing values ===
print("\n=== Missing Value Count ===")
print(df.isnull().sum())

# === 4. Domain checks ===
# (Assuming common columns: transaction_id, amount, currency, jurisdiction, screening_flag, sender_country, receiver_country)
expected_columns = ['transaction_id', 'amount', 'currency', 'jurisdiction', 'screening_flag']
missing_cols = [c for c in expected_columns if c not in df.columns]

if missing_cols:
    print(f"\n⚠️ Missing expected columns: {missing_cols}")
else:
    print("\n✅ All expected columns found.")

# === 5. Quick AML-style checks ===

# Rule 1: High-value transactions (example threshold: 50,000)
high_value_threshold = 50000
df['is_high_value'] = df['amount'] > high_value_threshold

# Rule 2: Offshore transfers (if sender != receiver country)
if 'sender_country' in df.columns and 'receiver_country' in df.columns:
    df['is_offshore'] = df['sender_country'] != df['receiver_country']
else:
    df['is_offshore'] = False

# Rule 3: Flagged by screening system
if 'screening_flag' in df.columns:
    df['is_screened'] = df['screening_flag'].astype(str).str.lower().isin(['y', 'yes', 'true', 'flagged'])
else:
    df['is_screened'] = False

# === 6. Compute a simple risk score ===
# Weighted combination of flags
df['risk_score'] = (
    (df['is_high_value'] * 40)
    + (df['is_offshore'] * 30)
    + (df['is_screened'] * 50)
)

# Normalize score to 0–100
df['risk_score'] = df['risk_score'].clip(upper=100)

# === 7. Summary of high-risk transactions ===
high_risk = df[df['risk_score'] >= 70]
print(f"\n🚨 High-risk transactions found: {len(high_risk)}")
print(high_risk[['transaction_id', 'amount', 'jurisdiction', 'risk_score']].head(10))

# === 8. Save enriched dataset ===
output_path = "transactions_enriched.csv"
df.to_csv(output_path, index=False)
print(f"\n✅ Enriched transaction file saved to {output_path}")
