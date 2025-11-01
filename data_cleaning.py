import pandas as pd
import numpy as np

df = pd.read_csv("../data/transactions_mock_1000_for_participants.csv")

# I have a list of columns to keep. How do I drop all other columns from the dataframe?
columns_to_keep = ['regulator', 'booking_datetime', 'amount', 'currency', 'channel','product_type','travel_rule_complete','customer_risk_rating','kyc_last_completed','kyc_due_date','originator_country','beneficiary_country','customer_type','customer_is_pep','edd_required','edd_performed','sow_documented','purpose_code',"is_advised", "product_complex", "client_risk_profile", "suitability_assessed", "suitability_result", "product_has_va_exposure", "va_disclosure_provided", "cash_id_verified", "daily_cash_total_customer", "daily_cash_txn_count", "sanctions_screening",'suspicion_determined_datetime']
df_2 = df[columns_to_keep]

# convert datetime column to pandas datetime format and create a new dataframe with the converted column
df_2['booking_datetime'] = pd.to_datetime(df_2['booking_datetime'])

# results stored in df_2