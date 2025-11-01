import os
import json
import time
from typing import Dict, Any, List, Tuple
import pandas as pd
from dotenv import load_dotenv
from groq import Groq

# Set BASE_DIR to the singhacks repository root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
TRANSACTIONS_CSV = os.path.join(DATA_DIR, "transactions_mock_1000_for_participants.csv")
RULES_PATH = os.path.join(os.path.dirname(__file__), "rulestemp.json")
# Output directory (new) - place analysis outputs here
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
OUTPUT_CSV = os.path.join(OUTPUT_DIR, "transactions_analysis_results.csv")
# A human-readable rules document saved alongside analysis outputs
OUTPUT_RULES_DOC = os.path.join(OUTPUT_DIR, "rules_document.txt")
# Directory for saving raw model responses
MODEL_RESPONSES_DIR = os.path.join(OUTPUT_DIR, "model_responses")

# Model configuration
MODEL = "openai/gpt-oss-20b"
TEMPERATURE = 0.1
MAX_TOKENS = 500
SLEEP_SECONDS = 0.08  # Rate limiting delay between API calls

# Load environment variables and initialize client
load_dotenv()

key = os.getenv("API_KEY")
if not key:
    raise RuntimeError(
        "Missing API key: set the GROQ_API_KEY environment variable or add it to a local .env file.\n"
    )

client = Groq(api_key=key)

def load_rules(rules_path: str) -> str:
    #Load rules from JSON file as dictionary and type cast to string.

    with open(rules_path, "r", encoding="utf-8") as f:
        rules_json = json.load(f)
    
    rules_dict = json.dumps(rules_json)
    return str(rules_dict)

def format_transaction_as_text(row: pd.Series) -> str:
    """Convert a transaction record into natural language text."""
    # Drop NaN/None values and convert to dict
    trans_dict = row.dropna().to_dict()
    return str(trans_dict)

def build_prompt_for_row(row: pd.Series, rules: str) -> str:
    """Build a natural language prompt for analyzing a transaction."""
    transaction_text = format_transaction_as_text(row)
    
    prompt = f"""You are a financial crime analyst. Please analyze this transaction against our anti-money laundering rules and determine if it poses a risk.

ANTI-MONEY LAUNDERING RULES:
{rules}

TRANSACTION DETAILS:
{transaction_text}

Based on these rules and transaction details, determine if this transaction is likely part of a money laundering scheme.
Please respond with a valid JSON object containing these fields:
- risk_label: "Low", "Medium", or "High"
- score: A number from 0-100 indicating risk level
- matched_rules: A list of rule names that were triggered
- explanation: A brief explanation of your assessment

Response must be valid JSON format with no other text.
"""
    return prompt

def analyze_transactions(
    transactions_csv: str = TRANSACTIONS_CSV,
    rules_path: str = RULES_PATH,
    output_csv: str = OUTPUT_CSV,
    sleep_seconds: float = SLEEP_SECONDS,
    limit: int | None = None,
) -> None:
    """Analyze transactions in the given CSV file using the GROQ chat API."""
    # Ensure output directories exist
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    os.makedirs(MODEL_RESPONSES_DIR, exist_ok=True)
    
    rules = load_rules(rules_path)
    df = pd.read_csv(transactions_csv)
    
    if limit is not None:
        df = df.head(limit)
        
    print(f"Analyzing {len(df)} transaction(s) using GROQ API...")
        
    results = []
    for idx, row in df.iterrows():
        prompt = build_prompt_for_row(row, rules)
        
        # Call Groq API
        try:
            response = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a financial crime analyst expert trained to analyze transactions for money laundering risk."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=MODEL,
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
                top_p=1,
                stop=None
            )
            raw_response = response.choices[0].message.content
        except Exception as e:
            print(f"Error calling Groq API for transaction {idx}: {e}")
            raw_response = str(e)

        # Save raw response, either as JSON if valid or .txt if not
        response_base = os.path.join(MODEL_RESPONSES_DIR, f"transaction_{idx}")
        try:
            # Try to parse as JSON first
            parsed = json.loads(raw_response)
            with open(f"{response_base}.json", "w", encoding="utf-8") as f:
                json.dump(parsed, f, indent=2)
            analysis = parsed  # Use for results
        except json.JSONDecodeError:
            # If not valid JSON, save as text and create error analysis
            with open(f"{response_base}.txt", "w", encoding="utf-8") as f:
                f.write(raw_response)
            analysis = {
                "risk_label": "Error",
                "score": -1,
                "matched_rules": [],
                "explanation": f"Error processing response: Invalid JSON"
            }
        
        # Add metadata and append to results
        analysis["transaction_id"] = row.get("transaction_id", f"TX_{idx}")
        analysis["index"] = int(idx)
        results.append(analysis)
        
        time.sleep(sleep_seconds)  # Rate limiting
    
    # Save results
    results_df = pd.DataFrame(results)
    results_df.to_csv(output_csv, index=False)
    print(f"Analysis complete. Results saved to {output_csv}")
    print(f"Raw model responses saved to {MODEL_RESPONSES_DIR}")


if __name__ == "__main__":
    # Interactive entrypoint: ask user how many transactions to analyze
    try:
        df = pd.read_csv(TRANSACTIONS_CSV)
        max_rows = len(df)
    except Exception:
        max_rows = None

    prompt_text = f"How many transactions to analyze (press Enter for all{'' if max_rows is None else f', max {max_rows}'})? "
    user_in = input(prompt_text)
    if user_in.strip() == "":
        limit = None
    else:
        try:
            limit = int(user_in)
            if max_rows is not None:
                limit = min(limit, max_rows)
        except Exception:
            print("Invalid number entered; analyzing all transactions.")
            limit = None

    analyze_transactions(limit=limit)