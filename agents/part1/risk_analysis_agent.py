import os
import json
import time
from typing import Dict, Any, List
import pandas as pd
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

key = os.getenv("API_KEY")
if not key:
    raise RuntimeError(
        "Missing API key: set the GROQ_API_KEY environment variable or add it to a local .env file.\n"
    )

client = Groq(api_key=key)
MODEL = "openai/gpt-oss-20b"

def load_rules(rules_path: str) -> Dict[str, Any]:
    with open(rules_path, "r", encoding="utf-8") as f:
        return json.load(f)

def evaluate_condition(value, operator, expected) -> bool:
    # Coerce booleans and numeric-like strings
    # Attempt numeric comparison first
    try:
        # handle booleans represented as strings
        if isinstance(expected, bool):
            if isinstance(value, str):
                val = value.strip().lower() in ("true", "1", "yes")
            else:
                val = bool(value)
        else:
            val = float(value)
    except Exception:
        val = value

    if operator == "eq":
        return val == expected
    if operator == "gt":
        try:
            return float(val) > float(expected)
        except Exception:
            return False
    if operator == "lt":
        try:
            return float(val) < float(expected)
        except Exception:
            return False

    # Unknown operator -> no match
    return False


def format_rules_as_text(rules: Dict[str, Any]) -> str:
    """Convert JSON rules into a natural language format."""
    rule_texts = []
    for idx, rule in enumerate(rules.get("money_laundering_rules", []), 1):
        name = rule.get("rule_name", "Unnamed Rule")
        desc = rule.get("description", "No description provided")
        
        # Convert condition to text
        cond = rule.get("condition", {})
        if isinstance(cond, list):
            # Handle compound conditions (e.g., EDD rules)
            conditions = []
            for c in cond:
                field = c.get("field", "unknown")
                op = c.get("operator", "unknown")
                val = c.get("value", "unknown")
                conditions.append(f"{field} {op} {val}")
            condition_text = " AND ".join(conditions)
        else:
            # Single condition
            field = cond.get("field", "unknown")
            op = cond.get("operator", "unknown")
            val = cond.get("value", "unknown")
            condition_text = f"{field} {op} {val}"
        
        evidence = rule.get("evidence", "No evidence provided")
        
        rule_text = (
            f"Rule {idx}: {name}\n"
            f"Description: {desc}\n"
            f"Trigger Condition: {condition_text}\n"
            f"Historical Evidence: {evidence}\n"
        )
        rule_texts.append(rule_text)
    
    return "\n".join(rule_texts)


def format_transaction_as_text(row: pd.Series) -> str:
    """Convert a transaction record into natural language text."""
    # Drop NaN/None values and convert to dict
    trans_dict = row.dropna().to_dict()
    
    # Order key fields first if present
    key_fields = [
        "transaction_id",
        "amount",
        "customer_risk_rating",
        "sanctions_screening",
        "edd_required",
        "edd_performed",
        "daily_cash_total_customer",
        "travel_rule_complete",
    ]
    
    lines = []
    # Add key fields first (if present)
    for field in key_fields:
        if field in trans_dict:
            value = trans_dict.pop(field)  # Remove from dict after adding
            lines.append(f"{field}: {value}")
    
    # Add any remaining fields
    for field, value in sorted(trans_dict.items()):
        lines.append(f"{field}: {value}")
    
    return "\n".join(lines)


def build_prompt_for_row(row: pd.Series, rules: Dict[str, Any]) -> str:
    """Build a natural language prompt for analyzing a transaction."""
    rules_text = format_rules_as_text(rules)
    transaction_text = format_transaction_as_text(row)
    
    prompt = f"""You are a financial crime analyst. Please analyze this transaction against our anti-money laundering rules and determine if it poses a risk.

ANTI-MONEY LAUNDERING RULES:
{rules_text}

TRANSACTION DETAILS:
{transaction_text}

Based on these rules and transaction details, determine if this transaction is likely part of a money laundering scheme.
Please respond with a valid JSON object containing these fields:
- risk_label: "Low", "Medium", or "High"
- score: A number from 0-100 indicating risk level
- matched_rules: A list of rule names that were triggered
- explanation: A brief explanation of your assessment

Response must be valid JSON with no other text.
"""
    return prompt

def analyze_transactions(
    transactions_csv: str = os.path.join(os.path.dirname(__file__), "..", "data", "transactions_mock_1000_for_participants.csv"),
    rules_path: str = os.path.join(os.path.dirname(__file__), "rulestemp.json"),
    output_csv: str = os.path.join(os.path.dirname(__file__), "..", "data", "transactions_analysis_results.csv"),
    sleep_seconds: float = 0.08,
    limit: int | None = None,
) -> None:
    """Analyze transactions in the given CSV file using the GROQ chat API."""
    rules = load_rules(rules_path)
    df = pd.read_csv(transactions_csv)
    
    if limit is not None:
        df = df.head(limit)
        
    print(f"Analyzing {len(df)} transaction(s) using GROQ API...")
        
    results = []
    for idx, row in df.iterrows():
        prompt = build_prompt_for_row(row, rules)
        
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
            model = MODEL,
            temperature=0.1,
            max_tokens=500,
            top_p=1,
            stop=None
        )
        
        try:
            analysis = json.loads(response.choices[0].message.content)
            analysis["transaction_id"] = row.get("transaction_id", f"TX_{idx}")
            analysis["index"] = int(idx)
            results.append(analysis)
        except json.JSONDecodeError as e:
            print(f"Error decoding response for transaction {idx}: {e}")
            print("Response:", response.choices[0].message.content)
            results.append({
                "index": int(idx),
                "transaction_id": row.get("transaction_id", f"TX_{idx}"),
                "risk_label": "Error",
                "score": -1,
                "matched_rules": [],
                "explanation": f"Error processing response: {e}"
            })
        
        time.sleep(sleep_seconds)  # Rate limiting
    
    # Save results
    results_df = pd.DataFrame(results)
    results_df.to_csv(output_csv, index=False)
    print(f"Analysis complete. Results saved to {output_csv}")


if __name__ == "__main__":
    # Interactive entrypoint: ask user how many transactions to analyze
    try:
        df_path = os.path.join(os.path.dirname(__file__), "..", "data", "transactions_mock_1000_for_participants.csv")
        df = pd.read_csv(df_path)
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