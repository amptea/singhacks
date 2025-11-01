from groq import Groq
import os
from dotenv import load_dotenv
import pandas as pd

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")
TRANSACTIONS_CSV = os.path.join(DATA_DIR, "transactions_mock_1000_for_participants.csv")

REGULATOR_CURRENCY = "SGD"

load_dotenv()
key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=key)

def prompt_groq(prompt: str) -> str:
    response = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        # Simply use the compound model ID
        model="groq/compound", 
    )
    return response.choices[0].message.content

def get_currency(dataframe: pd.DataFrame) -> str:
    """Return a comma-separated string of unique currencies from the dataframe.

    Normalizes values by stripping whitespace, dropping NaNs, and sorts the
    currencies for deterministic output.
    """
    if 'currency' not in dataframe.columns:
        return ""
    vals = (
        dataframe['currency']
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
    )
    # sort for deterministic ordering
    vals_sorted = sorted(vals)
    return ", ".join(vals_sorted)

def main():
    df = pd.read_csv(TRANSACTIONS_CSV)
    currencies = get_currency(df)
    prompt = (
        f"The following are the currencies present in the transactions dataset: {currencies}. "
        f"Convert all currencies to {REGULATOR_CURRENCY} using the average market rate. "
        "For each currency, provide the latest exchange rate to SGD as a number only. "
        "Respond only in the format 'CURRENCY: RATE', e.g. 'USD: 1.35', where each entry is separated by a comma. "
        "If the currency is already SGD, the rate is 1." 
        "Do NOT show any output other than the response format."
    )
    response = prompt_groq(prompt)
    print("Raw response:", response)
    exchange_rates = dict(response_part.strip().split(": ") for response_part in response.split(","))
    exchange_rates = {k: float(v) for k, v in exchange_rates.items()}
    print("Exchange rates:", exchange_rates)
    
    df2 = df.copy()
    # convert the currency column to be in SGD using the exchange rates
    df2['amount_sgd'] = df2['amount'] * df2['currency'].map(exchange_rates)
    df2.drop(columns=['amount'], inplace=True)
    df2.rename(columns={'amount_sgd': 'amount'}, inplace=True)
    return df2
