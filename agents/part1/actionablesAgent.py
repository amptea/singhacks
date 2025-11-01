"""
Transaction Actionables Agent
==============================

PURPOSE:
--------
This agent analyzes high-risk transactions identified by the risk analysis agent
and generates sequential, actionable next steps for different teams (Front Office,
Legal, and Compliance) to handle suspicious transactions appropriately.

HOW IT WORKS:
-------------
1. IDENTIFICATION PHASE:
   - Reads transactions_analysis_results.csv from output folder
   - Filters for High risk transactions (risk_label == "High")
   - Loads detailed analysis from corresponding JSON files in model_responses/

2. ACTION PLANNING PHASE:
   - Uses Groq AI (llama-3.3-70b-versatile model) to analyze each high-risk transaction
   - Generates sequential action steps based on:
     * Transaction characteristics (amount, sanctions hits, KYC status, etc.)
     * Matched AML rules
     * Risk factors identified
     * Regulatory requirements (MAS Notice 626)
   
3. TEAM ALLOCATION PHASE:
   - Assigns each action step to appropriate team:
     * FRONT: Front office staff (customer-facing, immediate actions)
     * LEGAL: Legal team (regulatory filings, legal review)
     * COMPLIANCE: Compliance team (investigations, monitoring, documentation)
   
4. ENRICHMENT PHASE:
   - Appends actionable recommendations to existing transaction JSON files
   - Maintains original risk analysis data
   - Adds new "actionables" field with sequential steps

5. REPORTING PHASE:
   - Creates actionables_summary.json with overview of all high-risk transactions
   - Generates team-specific action lists
   - Provides priority ordering based on risk scores

OUTPUT STRUCTURE:
-----------------
Each transaction JSON gets enriched with:
{
  "risk_label": "High",
  "score": 90,
  "matched_rules": [...],
  "explanation": "...",
  "actionables": {
    "next_steps": [
      {
        "step_number": 1,
        "action": "Freeze transaction pending review",
        "team": "FRONT",
        "priority": "IMMEDIATE",
        "details": "...",
        "deadline": "Within 1 hour"
      },
      {
        "step_number": 2,
        "action": "Conduct enhanced due diligence",
        "team": "COMPLIANCE",
        "priority": "HIGH",
        "details": "...",
        "deadline": "Within 24 hours"
      },
      ...
    ],
    "recommended_outcome": "File STR and escalate to senior management",
    "estimated_resolution_time": "3-5 business days"
  }
}

TEAM RESPONSIBILITIES:
----------------------
FRONT:
  - Immediate transaction holds/freezes
  - Customer contact and information gathering
  - Document collection requests
  - Initial triage and screening
  - Account restrictions if needed

COMPLIANCE:
  - Enhanced Due Diligence (EDD) investigations
  - Transaction monitoring and pattern analysis
  - Internal reporting and documentation
  - Risk assessment reviews
  - Policy compliance verification
  - Ongoing monitoring setup

LEGAL:
  - Suspicious Transaction Report (STR) filing with STRO
  - Regulatory notification requirements
  - Legal opinion on actions
  - Sanctions compliance review
  - Documentation for potential enforcement
  - Liaison with MAS and law enforcement

PRIORITY LEVELS:
----------------
IMMEDIATE: Within 1 hour - critical actions to prevent harm
HIGH: Within 24 hours - urgent compliance requirements
MEDIUM: Within 3 days - important follow-up actions
ROUTINE: Within 1 week - documentation and closure tasks

USE CASES:
----------
1. Incident Response: Immediate action plans for flagged transactions
2. Team Coordination: Clear task allocation across departments
3. Compliance Workflow: Structured approach to handling suspicious activity
4. Audit Trail: Sequential documentation of response actions
5. Training: Examples of proper handling procedures

CONFIGURATION:
--------------
- API Key: Set GROQ_API_KEY or API_KEY in .env file
- Temperature: 0.2 (slightly higher for creative action planning)
- Max Tokens: 2000 (sufficient for detailed action plans)
- Processes only High risk transactions (score >= 70)
"""

import os
import json
import time
from typing import Dict, Any, List
import pandas as pd
from dotenv import load_dotenv
from groq import Groq

# Set BASE_DIR to the singhacks repository root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
RESULTS_CSV = os.path.join(OUTPUT_DIR, "transactions_analysis_results.csv")
MODEL_RESPONSES_DIR = os.path.join(OUTPUT_DIR, "model_responses")
ACTIONABLES_SUMMARY = os.path.join(OUTPUT_DIR, "actionables_summary.json")

# Model configuration
MODEL = "llama-3.3-70b-versatile"
TEMPERATURE = 0.2
MAX_TOKENS = 2000
SLEEP_SECONDS = 0.1  # Rate limiting delay between API calls

# Load environment variables and initialize client
load_dotenv()

key = os.getenv("GROQ_API_KEY") or os.getenv("API_KEY")
if not key:
    raise RuntimeError(
        "Missing API key: set GROQ_API_KEY or API_KEY in your .env file.\n"
    )

client = Groq(api_key=key)


def load_transaction_details(transaction_id: str, index: int) -> Dict[str, Any]:
    """Load detailed analysis from the transaction's JSON file."""
    json_path = os.path.join(MODEL_RESPONSES_DIR, f"transaction_{index}.json")
    
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        # Try .txt file if JSON doesn't exist (error cases)
        txt_path = os.path.join(MODEL_RESPONSES_DIR, f"transaction_{index}.txt")
        if os.path.exists(txt_path):
            with open(txt_path, 'r', encoding='utf-8') as f:
                return {
                    "error": "Invalid JSON response",
                    "raw_response": f.read()
                }
    
    return {}


def build_actionables_prompt(transaction_data: Dict[str, Any]) -> str:
    """Build a prompt to generate actionable next steps for a high-risk transaction."""
    
    prompt = f"""You are an expert financial crime compliance advisor. A high-risk transaction has been flagged for potential money laundering activity.

TRANSACTION ANALYSIS:
{json.dumps(transaction_data, indent=2)}

Based on MAS Notice 626 requirements and AML/CFT best practices, generate a detailed action plan with sequential next steps.

For each step, specify:
1. Action to be taken
2. Responsible team (FRONT, COMPLIANCE, or LEGAL)
3. Priority level (IMMEDIATE, HIGH, MEDIUM, or ROUTINE)
4. Detailed explanation of why this action is needed
5. Deadline for completion

TEAM DEFINITIONS:
- FRONT: Front office staff handling customer interactions and immediate actions
- COMPLIANCE: Compliance team conducting investigations and risk assessments
- LEGAL: Legal team handling regulatory filings and legal matters

PRIORITY DEFINITIONS:
- IMMEDIATE: Within 1 hour - critical actions
- HIGH: Within 24 hours - urgent compliance requirements
- MEDIUM: Within 3 days - important follow-up
- ROUTINE: Within 1 week - documentation and closure

Consider factors like:
- Transaction amount and characteristics
- Sanctions screening results
- Customer risk rating
- KYC status and recency
- Pattern indicators (structuring, unusual activity)
- Regulatory reporting obligations

Provide your response as valid JSON with this exact structure:
{{
  "next_steps": [
    {{
      "step_number": 1,
      "action": "Brief action description",
      "team": "FRONT/COMPLIANCE/LEGAL",
      "priority": "IMMEDIATE/HIGH/MEDIUM/ROUTINE",
      "details": "Detailed explanation of what to do and why",
      "deadline": "Specific timeframe"
    }}
  ],
  "recommended_outcome": "Final disposition recommendation",
  "estimated_resolution_time": "Expected time to complete all actions"
}}

Response must be valid JSON only, no other text."""
    
    return prompt


def generate_actionables(transaction_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate actionable next steps for a high-risk transaction using Groq AI."""
    
    prompt = build_actionables_prompt(transaction_data)
    
    try:
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert financial crime compliance advisor specializing in AML/CFT procedures and MAS regulations. You provide clear, actionable guidance for handling suspicious transactions."
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
        
        # Parse JSON response
        actionables = json.loads(raw_response)
        return actionables
        
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        return {
            "next_steps": [],
            "recommended_outcome": "Error generating actionables",
            "estimated_resolution_time": "Unknown",
            "error": str(e)
        }
    except Exception as e:
        print(f"Error calling Groq API: {e}")
        return {
            "next_steps": [],
            "recommended_outcome": "Error generating actionables",
            "estimated_resolution_time": "Unknown",
            "error": str(e)
        }


def process_high_risk_transactions() -> None:
    """Process all high-risk transactions and generate actionables."""
    
    print("=" * 70)
    print("TRANSACTION ACTIONABLES AGENT")
    print("=" * 70)
    print()
    
    # Check if results file exists
    if not os.path.exists(RESULTS_CSV):
        print(f"❌ Error: Results file not found at {RESULTS_CSV}")
        print("   Please run the risk analysis agent first.")
        return
    
    # Load transaction results
    print("📊 Loading transaction analysis results...")
    df = pd.read_csv(RESULTS_CSV)
    
    # Filter for high-risk transactions
    high_risk_df = df[df['risk_label'] == 'High'].copy()
    print(f"   Found {len(high_risk_df)} high-risk transaction(s)")
    print()
    
    if len(high_risk_df) == 0:
        print("✅ No high-risk transactions found. No actions needed.")
        return
    
    # Process each high-risk transaction
    all_actionables = []
    team_summary = {
        "FRONT": [],
        "COMPLIANCE": [],
        "LEGAL": []
    }
    
    print("🔍 Generating actionables for high-risk transactions...")
    print()
    
    for idx, row in high_risk_df.iterrows():
        transaction_id = row['transaction_id']
        risk_score = row['score']
        index = row['index']
        
        print(f"   Processing: {transaction_id} (Risk Score: {risk_score})")
        
        # Load detailed transaction data
        transaction_details = load_transaction_details(transaction_id, index)
        
        # Generate actionables
        actionables = generate_actionables(transaction_details)
        
        # Add metadata
        actionables['transaction_id'] = transaction_id
        actionables['risk_score'] = int(risk_score)
        actionables['index'] = int(index)
        
        # Update the JSON file with actionables
        json_path = os.path.join(MODEL_RESPONSES_DIR, f"transaction_{index}.json")
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                full_data = json.load(f)
            
            full_data['actionables'] = actionables
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(full_data, f, indent=2, ensure_ascii=False)
            
            print(f"      ✓ Updated {json_path}")
        
        # Collect for summary
        all_actionables.append(actionables)
        
        # Organize by team
        for step in actionables.get('next_steps', []):
            team = step.get('team', 'UNKNOWN')
            if team in team_summary:
                team_summary[team].append({
                    'transaction_id': transaction_id,
                    'risk_score': risk_score,
                    'step': step
                })
        
        # Rate limiting
        time.sleep(SLEEP_SECONDS)
        print()
    
    # Generate summary report
    summary = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_high_risk_transactions": len(high_risk_df),
        "transactions": all_actionables,
        "team_breakdown": {
            "FRONT": {
                "total_actions": len(team_summary['FRONT']),
                "actions": team_summary['FRONT']
            },
            "COMPLIANCE": {
                "total_actions": len(team_summary['COMPLIANCE']),
                "actions": team_summary['COMPLIANCE']
            },
            "LEGAL": {
                "total_actions": len(team_summary['LEGAL']),
                "actions": team_summary['LEGAL']
            }
        }
    }
    
    # Save summary
    with open(ACTIONABLES_SUMMARY, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print("=" * 70)
    print("✅ ACTIONABLES GENERATION COMPLETE")
    print("=" * 70)
    print()
    print(f"📄 Summary saved to: {ACTIONABLES_SUMMARY}")
    print()
    print("📊 Team Action Summary:")
    print(f"   FRONT:      {len(team_summary['FRONT'])} actions")
    print(f"   COMPLIANCE: {len(team_summary['COMPLIANCE'])} actions")
    print(f"   LEGAL:      {len(team_summary['LEGAL'])} actions")
    print()
    print(f"✓ {len(high_risk_df)} transaction JSON files updated with actionables")
    print()


if __name__ == "__main__":
    process_high_risk_transactions()
