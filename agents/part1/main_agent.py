import pandas as pd
from groq import Groq
import json
from dotenv import load_dotenv
import os
import time
from typing import Any, Dict, List

load_dotenv()

# directory
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")
RULES_PATH = os.path.join(DATA_DIR, "mas.json")
TRANSACTIONS_CSV = os.path.join(DATA_DIR, "transactions_mock_1000_for_participants.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
OUTPUT_CSV = os.path.join(OUTPUT_DIR, "transactions_analysis_results.csv")
MODEL_RESPONSES_DIR = os.path.join(OUTPUT_DIR, "model_responses")

# config
NUM_ROWS = 5  # limit number of rows to process for testing

# key
KEY = os.getenv("GROQ_API_KEY")

# Model configuration
MODEL = "openai/gpt-oss-20b"
TEMPERATURE = 0.1
SLEEP_SECONDS = 0.08  # Rate limiting delay between API calls

# Load dataframe directly from CSV
df = pd.read_csv(TRANSACTIONS_CSV)
df2 = df[df['regulator'] == 'MAS'].reset_index(drop=True)
print(f"Loaded {len(df2)} MAS transactions from CSV")


def load_rules(rules_path: str) -> Dict[str, Any]:
	"""Load rules JSON from the given path and return as a Python dict.

	Raises FileNotFoundError or json.JSONDecodeError on failure.
	"""
	with open(rules_path, "r", encoding="utf-8") as f:
		return json.load(f)


def extract_critical_columns(rules: Dict[str, Any]) -> Dict[str, List[str]]:
	"""Recurse through a nested rules dict and find all keys named
	'critical_columns' (case-insensitive) whose value is a list of strings.

	Returns a flattened mapping where the key is a dot-separated path to the
	clause/subclause and the value is the list of critical column names.
	"""
	results: Dict[str, List[str]] = {}

	def _is_list_of_strings(v: Any) -> bool:
		return isinstance(v, list) and all(isinstance(i, str) for i in v)

	def _recurse(obj: Any, path: List[str]) -> None:
		if isinstance(obj, dict):
			for k, v in obj.items():
				if isinstance(k, str) and k.lower() == "critical_columns" and _is_list_of_strings(v):
					key_path = ".".join(path) if path else "root"
					results[key_path] = v
				else:
					_recurse(v, path + [k])
		elif isinstance(obj, list):
			for idx, item in enumerate(obj):
				# include index to keep paths unique when encountering lists
				_recurse(item, path + [str(idx)])

	_recurse(rules, [])
	return results


def process_rules(rules_path: str) -> Dict[str, List[str]]:
	"""Load rules, extract critical columns, and optionally save flattened mapping.

	Returns the flattened dict mapping clause paths to critical column lists.
	If out_path is None the result is saved to '<BASE_DIR>/output/critical_columns_flattened.json'.
	"""
	rules = load_rules(rules_path)
	flattened = extract_critical_columns(rules)
	return flattened

# create a function to prompt groq for a single query
def prompt_groq(prompt: str) -> str:
    """Call Groq API with the given prompt and return the response."""
    if not KEY:
        raise RuntimeError(
            "Missing API key: set the GROQ_API_KEY environment variable or add it to a local .env file.\n"
        )

    client = Groq(api_key=KEY)

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are a helpful financial crime analyst assistant.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=TEMPERATURE
    )
    return response.choices[0].message.content

# iterate through each row in dataframe up to a limit
def main_agent():
    """Main agent function to analyze transactions and output results in the expected format."""
    
    # Ensure output directories exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(MODEL_RESPONSES_DIR, exist_ok=True)
    
    # load search dictionary
    rules_dict = process_rules(RULES_PATH)
    
    with open(RULES_PATH, "r", encoding="utf-8") as f:
        rules_json = json.load(f)
    truth = str(json.dumps(rules_json))
    
    print(f"Analyzing {NUM_ROWS} transaction(s) using main agent...")
    
    # List to store results for CSV output
    results = []

    for index, row in df2.head(NUM_ROWS).iterrows():
        print(f"Processing transaction {index}...")
        
        # iterate through each key, value pair in rules_dict and select those columns from the row
        feature = {}
        for key, columns in rules_dict.items():
            relevant_info = {col: row[col] for col in columns if col in row} # relevant info based on crit columns for that clause
            feature[key] = relevant_info
            
        final_decision_prompt = f"""Based on the critical features identified for each Clause in FEATURES, determine if the particular clause has been violated by referencing the MAS Money Laundering rules RULES.

FEATURES: {str(feature)}

RULES: {truth}

Provide a final risk assessment for the transaction based on the number of violations found with reference to the RULES.

If there is high risk, label the transaction as "High". If there is some risk of money laundering, label the transaction as "Medium". If little to no violations were found, label it as "Low".

Please respond with a valid JSON object containing these fields:
- risk_label: "Low", "Medium", or "High" 
- score: A number from 0-100 indicating risk level (0-40 = Low, 41-70 = Medium, 71-100 = High)
- matched_rules: A list of rule names that were triggered (e.g., ["High Transaction Amount", "Potential Sanctions Hit"])
- explanation: A brief explanation of your assessment

Response must be valid JSON format with no other text.
"""
        
        try:
            # Call Groq API
            raw_response = prompt_groq(final_decision_prompt)
            
            # Parse JSON response
            try:
                parsed = json.loads(raw_response)
                
                # Validate required fields
                if not all(key in parsed for key in ['risk_label', 'score', 'matched_rules', 'explanation']):
                    raise ValueError("Missing required fields in response")
                
                analysis = parsed
                
            except (json.JSONDecodeError, ValueError) as e:
                print(f"  ⚠️ Error parsing JSON for transaction {index}: {e}")
                # Create error response
                analysis = {
                    "risk_label": "Error",
                    "score": -1,
                    "matched_rules": [],
                    "explanation": f"Error processing response: {str(e)}"
                }
            
            # Add transaction metadata
            transaction_id = row.get("transaction_id", f"TX_{index}")
            analysis["transaction_id"] = transaction_id
            analysis["index"] = int(index)
            
            # Save individual JSON file to model_responses directory
            response_file = os.path.join(MODEL_RESPONSES_DIR, f"transaction_{index}.json")
            with open(response_file, "w", encoding="utf-8") as f:
                json.dump(analysis, f, indent=2)
            
            # Add to results list for CSV
            results.append(analysis)
            
            print(f"  ✓ Transaction {index} analyzed: {analysis['risk_label']} (score: {analysis['score']})")
            
        except Exception as e:
            print(f"  ❌ Error processing transaction {index}: {e}")
            # Create error entry
            error_analysis = {
                "risk_label": "Error",
                "score": -1,
                "matched_rules": [],
                "explanation": f"Error: {str(e)}",
                "transaction_id": row.get("transaction_id", f"TX_{index}"),
                "index": int(index)
            }
            
            # Save error response
            response_file = os.path.join(MODEL_RESPONSES_DIR, f"transaction_{index}.json")
            with open(response_file, "w", encoding="utf-8") as f:
                json.dump(error_analysis, f, indent=2)
            
            results.append(error_analysis)
        
        # Rate limiting
        time.sleep(SLEEP_SECONDS)
    
    # Save results to CSV
    results_df = pd.DataFrame(results)
    results_df.to_csv(OUTPUT_CSV, index=False)
    
    print(f"\n✅ Analysis complete!")
    print(f"   Results saved to: {OUTPUT_CSV}")
    print(f"   Individual responses saved to: {MODEL_RESPONSES_DIR}")
    print(f"\n📊 Summary:")
    print(f"   Total transactions: {len(results)}")
    if len(results) > 0:
        risk_counts = results_df['risk_label'].value_counts().to_dict()
        for risk_level, count in risk_counts.items():
            print(f"   {risk_level}: {count}")
    
    # Check if there are any high-risk transactions
    high_risk_count = risk_counts.get('High', 0)
    if high_risk_count > 0:
        print(f"\n🚨 Found {high_risk_count} high-risk transaction(s)")
        print("📋 Generating actionable next steps...")
        
        try:
            # Import and run actionables agent
            from actionablesAgent import process_high_risk_transactions
            process_high_risk_transactions()
        except Exception as e:
            print(f"⚠️ Error generating actionables: {e}")
            print("   You can manually run: python agents/part1/actionablesAgent.py")
    else:
        print("\n✅ No high-risk transactions detected - no actionables needed")
            
if __name__ == "__main__":
    main_agent()