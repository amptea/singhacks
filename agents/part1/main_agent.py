import pandas as pd
from groq import Groq
import json
from dotenv import load_dotenv
import os
from typing import Any, Dict, List

load_dotenv()

# directory
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")
RULES_PATH = os.path.join(DATA_DIR, "mas.json")
TRANSACTIONS_CSV = os.path.join(DATA_DIR, "transactions_mock_1000_for_participants.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
OUTPUT_CSV = os.path.join(OUTPUT_DIR, "transactions_analysis_results.csv")

# config+NUM_ROWS = 5  # limit number of rows to process for testing
NUM_ROWS = 5  # limit number of rows to process for testing

# key
KEY = os.getenv("GROQ_API_KEY")

# import the dataframe and filter regulator column if it is MAS
df = pd.read_csv(TRANSACTIONS_CSV)
df2 = df[df['regulator'] == 'MAS'].reset_index(drop=True)


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
    if not KEY:
        raise RuntimeError(
            "Missing API key: set the GROQ_API_KEY environment variable or add it to a local .env file.\n"
        )

    client = Groq(api_key=KEY)

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful financial crime analyst assistant.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.1
    )
    return response.choices[0].message.content

# iterate through each row in dataframe up to a limit
def main_agent():

    # load search dictionary
    rules_dict = process_rules(RULES_PATH)
	
    with open(RULES_PATH, "r", encoding="utf-8") as f:
        rules_json = json.load(f)
    truth = str(json.dumps(rules_json))

    for index, row in df2.head(NUM_ROWS).iterrows():
    # iterate through each key, value pair in rules_dict and select those columns from the row
        feature = {}
        for key, columns in rules_dict.items():
            relevant_info = {col: row[col] for col in columns if col in row} # relevant info based on crit columns for that clause
            feature[key] = relevant_info
			
        final_decision_prompt = f"""Based on the critical features identified for each Clause in FEATURES, determine if the particular clause has been violated by referencing the MAS Money Laundering rules RULES".
		
		FEATURES: {str(feature)}
		
		RULES: {truth}
		
		Provide a final risk assessment for the transaction based on the number of violations found with reference to the RULES.
		
        If there is high risk, label the transaction as "High Risk". If there is some risk of money laundering, label the transaction as "Medium Risk". If little to no violations were found, label it as "Low Risk".
        Provide a brief explanation for the decision. Respond in the format: "Final Risk Assessment: <risk_label>,  Summary: <summary>."
        """
        final_assessment = prompt_groq(final_decision_prompt)
		# store each final assessment in the output directory as a json file with formatting "Final Risk Assessment: <risk_label>,  Summary: <summary>."
        with open(os.path.join(OUTPUT_DIR, f"assessment_row_{index}.txt"), "w", encoding="utf-8") as out_file:
            out_file.write(final_assessment)
			
if __name__ == "__main__":
    main_agent()