# MAS Regulation Compliance Agent

## 📋 Overview

This agent automatically validates regulatory compliance by comparing the latest MAS Notice 626 regulations from the official Monetary Authority of Singapore website against your organization's documented compliance requirements.

## 🎯 Source of Truth

### Primary Source (Authoritative)
**MAS Notice 626 PDF** - Official regulatory document
- **Authority**: Monetary Authority of Singapore (MAS)
- **URL**: https://www.mas.gov.sg/regulation/notices/notice-626
- **Current Version**: Last revised 30 June 2025
- **Status**: Legal requirement for all banks in Singapore
- **Format**: PDF document with ~44 pages

This is the **single source of truth** for compliance requirements.

### Validation Target
**data/mas.json** - Your organization's compliance documentation
- **Purpose**: Structured representation of your understanding/implementation of Notice 626
- **Status**: Should match the official Notice 626 requirements
- **Use**: Internal compliance tracking and validation

## 🔄 How It Works

```
┌─────────────────────────────────────────────────────────────┐
│  1. SCRAPE MAS WEBSITE                                      │
│     → Navigate to Notice 626 page                           │
│     → Find latest PDF (30 June 2025 revision)               │
│     → Download complete PDF document                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  2. EXTRACT CONTENT                                         │
│     → Extract text from ALL pages (no limits)               │
│     → Load mas.json from data/ directory                    │
│     → Prepare both for comparison                           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  3. AI ANALYSIS (Groq - llama-3.3-70b-versatile)            │
│     → Compare document metadata                             │
│     → Analyze EVERY clause (4, 5, 6, 7, 8, 9, 10...)        │
│     → Check all sub-clauses (4.1, 4.2, 6.1-6.26, etc.)      │
│     → Identify substantive vs cosmetic differences          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  4. GENERATE REPORT                                         │
│     → Consistency score (%)                                 │
│     → Critical differences (action required)                │
│     → Minor differences (informational)                     │
│     → Clause-by-clause breakdown                            │
│     → Save to data/scraping_results.json                    │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Usage

### Running the Agent

```bash
# Basic execution
python agents/regIngestAgent.py

# Or use the batch file
run_agent.bat
```

### Viewing Results

1. **Streamlit UI** (Recommended):
   ```bash
   streamlit run src/mas_scraping_ui.py
   ```
   Open http://localhost:8501 in your browser

2. **Raw JSON**:
   View `data/scraping_results.json` directly

## 📊 Understanding Results

### Status Indicators

| Status | Meaning | Action Required |
|--------|---------|----------------|
| ✅ **CONSISTENT** | Content matches official notice | None - keep as is |
| ⚠️ **DIFFERENT** | Substantive changes detected | Review and update mas.json |
| 🚨 **MISSING** | Clause missing from mas.json | Add missing requirements |

### Consistency Scores

- **95-100%**: Excellent alignment, minimal action needed
- **85-94%**: Good alignment, review minor differences
- **70-84%**: Moderate gaps, update recommended
- **<70%**: Significant gaps, immediate review required

### Example Output

```json
{
  "overall_assessment": {
    "total_clauses_checked": 12,
    "consistency_score": "95%",
    "consistent_clauses": 11,
    "different_clauses": 1,
    "missing_clauses": 0,
    "critical_differences": [],
    "minor_differences": [
      "Minor wording variations in clause 6.3 that don't alter meaning"
    ]
  }
}
```

## ⚙️ Configuration

### Environment Setup

Create `.env` file in project root:
```env
GROQ_API_KEY=your_api_key_here
# or
api_key=your_api_key_here
```

### Agent Parameters

Located in `regIngestAgent.py`:
- **Model**: `llama-3.3-70b-versatile` (Groq)
- **Temperature**: `0.1` (low for consistency)
- **Max Tokens**: `16,000` (comprehensive analysis)
- **Cost Priority**: Thoroughness > Speed

## 📁 File Structure

```
agents/
├── regIngestAgent.py          # Main agent code
├── README.md                  # This file
└── part1/                     # Legacy/backup files

data/
├── mas.json                   # Your compliance docs (validation target)
└── scraping_results.json      # Agent output (generated)

src/
├── mas_scraping_ui.py         # Streamlit viewer for results
└── pdf_ocr_ui.py              # OCR tool (separate utility)
```

## 🔍 What Gets Compared

### All Major Clauses

The agent comprehensively checks:

1. **Clause 4**: Risk Assessment and Risk-Based Approach
2. **Clause 5**: New Products and Technologies
3. **Clause 6**: Customer Due Diligence (CDD)
   - Sub-clauses: 6.1, 6.2, 6.3, 6.4, 6.19-6.26, etc.
4. **Clause 7**: Internal Policies, Procedures and Controls
5. **Clause 8**: (Simplified CDD)
6. **Clause 9**: Suspicious Transaction Reporting
7. **Clause 10**: Correspondent Banking
8. **Clause 11**: Record Keeping
9. **Clause 12**: (Record keeping details)
10. **Clause 13**: (Additional requirements)
11. **Clause 14**: (Training requirements)
12. **Clause 15**: (Additional provisions)

### Document Metadata

- Notice number (MAS Notice 626)
- Effective date (1 April 2024)
- Last revised date (30 June 2025)
- Document title

## 🛠️ Maintenance

### When to Run

- **Weekly**: During regulatory monitoring periods
- **Monthly**: Regular compliance checks
- **Ad-hoc**: When MAS announces updates
- **Pre-audit**: Before compliance audits

### Updating mas.json

When differences are found:

1. Review the specific clause differences in the results
2. Consult with compliance team
3. Update mas.json to match official Notice 626
4. Re-run agent to verify updates
5. Document changes in version control

## ⚠️ Important Notes

### What This Agent Does

✅ Compares text content of regulations  
✅ Identifies structural differences  
✅ Flags missing or changed requirements  
✅ Provides detailed clause-by-clause analysis  

### What This Agent Doesn't Do

❌ Provide legal advice  
❌ Interpret ambiguous requirements  
❌ Make compliance decisions  
❌ Replace human compliance review  

**Always consult with compliance officers and legal counsel when implementing regulatory changes.**

## 📞 Support

For issues or questions:
1. Check `data/scraping_results.json` for detailed error messages
2. Review agent logs in terminal output
3. Verify GROQ_API_KEY is set correctly in `.env`
4. Ensure internet connectivity for MAS website access

## 🔐 Dependencies

Required packages (see `requirements.txt`):
- `requests` - HTTP client for web scraping
- `beautifulsoup4` - HTML parsing
- `PyPDF2` - PDF text extraction
- `groq` - AI analysis API
- `python-dotenv` - Environment variable management

## 📝 License

Part of the SingHacks project. See main repository for license details.
