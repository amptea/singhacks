# 🚀 Quick Start Guide - AI Fraud Detection System

## Overview

Your Streamlit multi-page app is now configured with:
- **Home Page**: `src/home.py` - Main navigation hub
- **Page 1**: MAS Compliance Viewer (`src/pages/1__MAS_Compliance.py`)
- **Page 2**: AI Fraud Detection (`src/pages/2__PDF_OCR.py`) ✨ NEW!

## Setup

### 1. Install Dependencies

```bash
pip install groq jigsawstack python-dotenv streamlit requests PyMuPDF Pillow
```

### 2. Configure API Keys

Create a `.env` file in your project root:

```bash
# .env file
GROQ_API_KEY=your-groq-api-key-here
JIGSAWSTACK_API_KEY=your-jigsawstack-api-key-here
```

**Get your API keys:**
- Groq: https://console.groq.com/keys (FREE)
- JigsawStack: https://jigsawstack.com (Sign up)

## Running the App

### Method 1: Run from src directory (Recommended)

```bash
cd src
streamlit run home.py
```

### Method 2: Run with full path

```bash
streamlit run src/home.py
```

## What's New

### 🔍 AI-Powered Fraud Detection System

The updated `pages/2__PDF_OCR.py` now includes:

#### ✅ Features Integrated

1. **JigsawStack OCR Integration**
   - Supports PDF, JPG, PNG, JPEG, TXT files
   - Base64 data URI method ([official JigsawStack docs](https://jigsawstack.com/docs/api-reference/handling-files))
   - Multi-page support (up to 10 pages)
   - Automatic fallback to PyMuPDF for PDFs

2. **AI-Powered Structured Field Extraction**
   - Uses `structured_extractor.py`
   - Extracts names, IDs, transaction details, bank info
   - Outputs clean JSON structure

3. **Enhanced LLM Validation**
   - Uses `enhanced_validator.py`
   - Checks formatting, content, document structure
   - Compares against standard document templates
   - AI explains each issue found

4. **External Verification** (Optional)
   - Uses `external_verification.py`
   - Queries company registers (OpenCorporates, GLEIF, EU)
   - Checks sanction lists (OFAC, EU, UN)
   - PEP database screening
   - Match confidence scoring

5. **Comprehensive AI Fraud Analysis**
   - Uses `ai_fraud_detector.py`
   - Risk scoring (0-10 scale)
   - Key findings and recommendations
   - Downloadable JSON reports

#### 📊 User Interface

- **Stage-by-stage progress tracking** with visual progress bar
- **5 analysis stages**: Parse → Extract → Validate → Verify → Analyze
- **6 result tabs**: 
  - Overview (Executive summary)
  - Extracted Data (Structured fields)
  - Validation (Format/content issues)
  - Verification (External checks)
  - AI Analysis (Fraud detection)
  - Full Report (Downloadable JSON)

- **Risk-based color coding**: 
  - 🔴 High Risk (8-10)
  - 🟡 Medium Risk (4-7)
  - 🟢 Low Risk (0-3)

## Navigation Flow

```
Home Page (src/home.py)
├── Sidebar Navigation
│   ├── Home
│   ├── MAS Regulation Compliance → pages/1__MAS_Compliance.py
│   └── AI Fraud Detection → pages/2__PDF_OCR.py
│
└── Tool Cards
    ├── 📊 MAS Compliance Viewer [Launch Button]
    └── 🔍 AI Fraud Detection [Launch Button]
```

## Usage Example

1. **Start the app**:
   ```bash
   cd src
   streamlit run home.py
   ```

2. **From Home Page**: Click "🚀 Launch AI Fraud Detection" button

3. **Or use Sidebar**: Select "AI Fraud Detection" from radio buttons

4. **Upload a document**:
   - Supported: PDF, JPG, PNG, JPEG, TXT
   - Drag & drop or click to upload

5. **Configure options** (in sidebar):
   - Select document type (statement, invoice, contract, etc.)
   - Enable/disable external verification
   - Toggle debug info

6. **Click "Analyze Document"** and wait for results

7. **Review results** in organized tabs

8. **Download report** as JSON for records

## File Structure

```
src/
├── home.py                          # Main entry point ✨
├── pages/
│   ├── 1__MAS_Compliance.py        # MAS tool
│   └── 2__PDF_OCR.py               # AI Fraud Detection ✨
├── document_parser_jigsawstack.py  # JigsawStack OCR integration
├── ai_fraud_detector.py            # AI fraud analysis engine
├── structured_extractor.py         # Field extraction
├── enhanced_validator.py           # Document validation
└── external_verification.py        # External data checks
```

## API Integration

### JigsawStack vOCR

Based on [official documentation](https://jigsawstack.com/docs/api-reference/handling-files):

```python
# Method used: Base64 data URI
with open(file_path, 'rb') as f:
    file_data = f.read()

base64_data = base64.b64encode(file_data).decode('utf-8')
data_uri = f"data:{mime_type};base64,{base64_data}"

# Call OCR
result = client.vision.vocr({
    "url": data_uri,
    "prompt": ["Extracted Text"]
})
```

### Groq AI

Used for:
- Structured field extraction
- Document validation
- External verification reasoning
- Comprehensive fraud analysis

## Troubleshooting

### "API key required" error
- Check `.env` file exists in project root
- Verify keys are correct (no quotes needed)
- Restart Streamlit after adding keys

### "Module not found" error
```bash
cd "path/to/singhacks"
pip install -r requirements.txt
```

### Page navigation not working
- Ensure you're running from `src/` directory
- Check that `pages/` folder exists with proper naming: `1__Name.py`, `2__Name.py`

### OCR returning 0 characters
- Check JigsawStack API key is valid
- Look at console for detailed error messages
- Try with a simple image first (clear text, good quality)

## Performance

Expected processing times per document:
- **Parsing (JigsawStack OCR)**: 3-10 seconds
- **Field Extraction**: 2-5 seconds
- **Validation**: 3-5 seconds
- **External Verification**: 5-15 seconds (if enabled)
- **AI Fraud Analysis**: 5-10 seconds
- **Total**: 20-45 seconds

## Cost Estimates (per document)

- Groq AI: ~$0.01-0.03 (FREE tier available)
- JigsawStack: ~$0.02-0.05
- **Total**: ~$0.03-0.08 per document

## Support

- **Documentation**: See inline code docstrings
- **JigsawStack Docs**: https://jigsawstack.com/docs
- **Groq Docs**: https://console.groq.com/docs

---

**You're ready to detect fraud! 🔍✨**

Run the app: `cd src && streamlit run home.py`

