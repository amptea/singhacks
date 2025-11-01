# Transaction Actionables Agent

## Overview
The Transaction Actionables Agent automatically generates sequential, actionable next steps for high-risk transactions identified by the risk analysis agent. It assigns actions to specific teams (Front Office, Compliance, Legal) with priorities and deadlines.

## Purpose
When high-risk transactions are flagged for potential money laundering activity, organizations need clear, structured action plans. This agent:
- Analyzes risk factors and regulatory requirements
- Generates step-by-step action plans
- Assigns responsibility to appropriate teams
- Sets priorities and deadlines
- Enriches transaction data with actionable recommendations

## How It Works

### 1. Identification Phase
- Reads `transactions_analysis_results.csv` from the output folder
- Filters for High risk transactions (`risk_label == "High"`)
- Loads detailed analysis from JSON files in `model_responses/`

### 2. Action Planning Phase
- Uses Groq AI (llama-3.3-70b-versatile) to analyze each high-risk transaction
- Considers:
  - Transaction characteristics (amount, sanctions hits, KYC status)
  - Matched AML rules
  - Risk factors identified
  - MAS Notice 626 regulatory requirements

### 3. Team Allocation Phase
Assigns each action to the appropriate team:
- **FRONT**: Customer-facing staff handling immediate actions
- **COMPLIANCE**: Investigation, monitoring, and documentation
- **LEGAL**: Regulatory filings and legal review

### 4. Enrichment Phase
- Appends actionable recommendations to existing transaction JSON files
- Maintains original risk analysis data
- Adds new "actionables" field with sequential steps

### 5. Reporting Phase
- Creates `actionables_summary.json` with overview
- Generates team-specific action lists
- Provides priority ordering based on risk scores

## Team Responsibilities

### FRONT (Front Office)
- Immediate transaction holds/freezes
- Customer contact and information gathering
- Document collection requests
- Initial triage and screening
- Account restrictions if needed

### COMPLIANCE
- Enhanced Due Diligence (EDD) investigations
- Transaction monitoring and pattern analysis
- Internal reporting and documentation
- Risk assessment reviews
- Policy compliance verification
- Ongoing monitoring setup

### LEGAL
- Suspicious Transaction Report (STR) filing with STRO
- Regulatory notification requirements
- Legal opinion on actions
- Sanctions compliance review
- Documentation for potential enforcement
- Liaison with MAS and law enforcement

## Priority Levels

| Priority | Timeframe | Description |
|----------|-----------|-------------|
| **IMMEDIATE** | Within 1 hour | Critical actions to prevent harm |
| **HIGH** | Within 24 hours | Urgent compliance requirements |
| **MEDIUM** | Within 3 days | Important follow-up actions |
| **ROUTINE** | Within 1 week | Documentation and closure tasks |

## Output Structure

### Enhanced Transaction JSON
Each high-risk transaction JSON file gets enriched with:

```json
{
  "risk_label": "High",
  "score": 90,
  "matched_rules": ["High Transaction Amount", "Potential Sanctions Hit"],
  "explanation": "...",
  "actionables": {
    "next_steps": [
      {
        "step_number": 1,
        "action": "Freeze transaction pending review",
        "team": "FRONT",
        "priority": "IMMEDIATE",
        "details": "Detailed explanation of what to do and why",
        "deadline": "Within 1 hour"
      },
      {
        "step_number": 2,
        "action": "Conduct enhanced due diligence",
        "team": "COMPLIANCE",
        "priority": "HIGH",
        "details": "...",
        "deadline": "Within 24 hours"
      }
    ],
    "recommended_outcome": "File STR and escalate to senior management",
    "estimated_resolution_time": "3-5 business days"
  }
}
```

### Summary Report (`actionables_summary.json`)

```json
{
  "generated_at": "2025-11-01 17:54:31",
  "total_high_risk_transactions": 4,
  "transactions": [...],
  "team_breakdown": {
    "FRONT": {
      "total_actions": 5,
      "actions": [...]
    },
    "COMPLIANCE": {
      "total_actions": 22,
      "actions": [...]
    },
    "LEGAL": {
      "total_actions": 0,
      "actions": [...]
    }
  }
}
```

## Usage

### Prerequisites
1. Run the risk analysis agent first to generate transaction risk assessments
2. Ensure `output/transactions_analysis_results.csv` exists
3. Set `GROQ_API_KEY` or `API_KEY` in your `.env` file

### Running the Agent

```bash
# From the repository root
python agents/part1/actionablesAgent.py
```

### Output
- Updates transaction JSON files in `output/model_responses/` with actionables
- Creates `output/actionables_summary.json` with overview and team breakdown
- Prints summary to console

### Example Output

```
======================================================================
TRANSACTION ACTIONABLES AGENT
======================================================================

📊 Loading transaction analysis results...
   Found 4 high-risk transaction(s)

🔍 Generating actionables for high-risk transactions...

   Processing: ad66338d-b17f-47fc-a966-1b4395351b41 (Risk Score: 90)
      ✓ Updated transaction_0.json

======================================================================
✅ ACTIONABLES GENERATION COMPLETE
======================================================================

📄 Summary saved to: output/actionables_summary.json

📊 Team Action Summary:
   FRONT:      5 actions
   COMPLIANCE: 22 actions
   LEGAL:      0 actions

✓ 4 transaction JSON files updated with actionables
```

## Use Cases

1. **Incident Response**: Immediate action plans for flagged transactions
2. **Team Coordination**: Clear task allocation across departments
3. **Compliance Workflow**: Structured approach to handling suspicious activity
4. **Audit Trail**: Sequential documentation of response actions
5. **Training**: Examples of proper handling procedures

## Configuration

### Model Settings
- **Model**: llama-3.3-70b-versatile
- **Temperature**: 0.2 (slightly higher for creative action planning)
- **Max Tokens**: 2000 (sufficient for detailed action plans)
- **Rate Limiting**: 0.1 seconds between API calls

### Thresholds
- Processes only transactions with `risk_label == "High"`
- Typically corresponds to risk scores >= 70

## Integration with Streamlit UI

The actionables can be displayed in the Transaction Viewer tab of the MAS Compliance UI:
1. Select a high-risk transaction
2. View the detailed analysis
3. See the recommended next steps with team assignments
4. Track deadlines and priorities

## Regulatory Compliance

This agent helps organizations comply with:
- **MAS Notice 626**: Prevention of Money Laundering and Countering the Financing of Terrorism
- **STR Requirements**: Suspicious Transaction Reporting to STRO
- **EDD Requirements**: Enhanced Due Diligence for high-risk customers
- **Sanctions Compliance**: OFAC and other sanctions screening requirements

## Best Practices

1. **Run Regularly**: Execute after each batch of transaction risk analysis
2. **Review Actionables**: Have compliance officer review generated actions
3. **Track Completion**: Use summary to monitor team progress
4. **Update KYC**: Ensure customer information stays current
5. **Document Everything**: Maintain audit trail of all actions taken

## Troubleshooting

### No High-Risk Transactions Found
```
✅ No high-risk transactions found. No actions needed.
```
This is normal if all transactions are low/medium risk.

### API Key Error
```
Missing API key: set GROQ_API_KEY or API_KEY in your .env file.
```
Solution: Add your Groq API key to the `.env` file.

### Results File Not Found
```
❌ Error: Results file not found at output/transactions_analysis_results.csv
   Please run the risk analysis agent first.
```
Solution: Run `python agents/part1/risk_analysis_agent.py` first.

## Example Action Plans

### High-Value Transaction with Sanctions Hit
1. **IMMEDIATE** (FRONT): Freeze transaction
2. **HIGH** (COMPLIANCE): Conduct EDD review
3. **HIGH** (COMPLIANCE): Investigate sanctions screening
4. **MEDIUM** (COMPLIANCE): Review transaction patterns
5. **HIGH** (COMPLIANCE): Prepare STR if necessary
6. **MEDIUM** (FRONT): Update KYC
7. **ROUTINE** (COMPLIANCE): Document actions

### Overdue KYC with Large Transaction
1. **IMMEDIATE** (FRONT): Contact customer for KYC update
2. **HIGH** (COMPLIANCE): Enhanced due diligence review
3. **MEDIUM** (COMPLIANCE): Verify source of funds
4. **MEDIUM** (FRONT): Collect updated documentation
5. **ROUTINE** (COMPLIANCE): Update risk assessment

## Files Modified

- `output/model_responses/transaction_*.json` - Enhanced with actionables
- `output/actionables_summary.json` - New summary report

## Future Enhancements

- [ ] Email notifications to team leads
- [ ] Integration with ticketing systems
- [ ] Automatic deadline tracking
- [ ] Escalation workflows for overdue actions
- [ ] Dashboard for team action monitoring
- [ ] Historical action effectiveness analysis

## Author Notes

This agent prioritizes thoroughness and regulatory compliance over speed. It ensures that all high-risk transactions receive appropriate attention and that actions are properly documented for audit purposes.
