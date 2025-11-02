# Enhanced Fraud Detection System - Implementation Guide

## 🎯 Overview

This comprehensive fraud detection and compliance verification system has been enhanced with:

1. **Universal Document Parser** - Support for PDFs, Images (JPG/PNG/TIFF), Text files (TXT), and Word documents (DOCX)
2. **Advanced Image Analysis** - AI-generated image detection, reverse image search, metadata tampering detection, and pixel-level anomaly detection
3. **Complete Validation** - Lists ALL validation issues (spelling, formatting, structure) without summarization
4. **Firestore Audit Trail** - Comprehensive logging of all actions, agents, inputs, outputs, and errors
5. **Multi-Format Support** - Handle diverse document types with automatic format detection

## 📋 New Features

### 1. Universal Document Parser (`src/universal_document_parser.py`)

**Capabilities:**
- **PDF Documents**: OCR with Tesseract, metadata extraction, image detection
- **Images**: JPG, PNG, TIFF with EXIF metadata extraction
- **Text Files**: Plain text with encoding detection
- **Word Documents**: DOCX with document properties extraction

**Usage:**
```python
from universal_document_parser import UniversalDocumentParser

parser = UniversalDocumentParser(dpi_scale=3)
result = parser.parse_document("document.pdf")

# Access extracted content
text = result['text']
metadata = result['metadata']
images = result['images']
```

**Key Features:**
- Automatic format detection
- Metadata extraction (EXIF, document properties, PDF metadata)
- Support for scanned documents
- Configurable OCR quality (DPI scale)

### 2. Advanced Image Analyzer (`src/advanced_image_analyzer.py`)

**Capabilities:**
- **Reverse Image Search**: Using SerpAPI to detect stolen/reused images
- **AI-Generated Detection**: Using Hugging Face models (orikami/ai-image-detector, Llama models)
- **Metadata Tampering**: EXIF analysis for editing software, date inconsistencies, GPS manipulation
- **Pixel Anomalies**: Cloning detection, splicing detection, noise inconsistency analysis

**Usage:**
```python
from advanced_image_analyzer import AdvancedImageAnalyzer

analyzer = AdvancedImageAnalyzer()

# Analyze single image
result = analyzer.analyze_image(
    "image.jpg",
    check_reverse_search=True,
    check_ai_generated=True,
    check_metadata_tampering=True,
    check_pixel_anomalies=True
)

# Analyze all images in PDF
pdf_result = analyzer.analyze_pdf_images("document.pdf")
```

**Detection Methods:**

#### a) Reverse Image Search
- Integrates with SerpAPI Google Lens
- Detects stolen or reused images
- Provides match confidence scores

#### b) AI-Generated Image Detection
- **Orikami Model**: Lightweight classifier for AI-generated images
- **Heuristic Analysis**: Fallback method analyzing smoothness, saturation, dimensions
- Combined confidence scoring

#### c) Metadata Tampering Detection
- Missing EXIF data (potential stripping)
- Editing software detection (Photoshop, GIMP, etc.)
- Date timestamp inconsistencies
- GPS data manipulation
- File modification time vs. EXIF date discrepancies

#### d) Pixel-Level Anomaly Detection
- **Cloning Detection**: Identifies repeating patterns using correlation
- **Splicing Detection**: Analyzes noise level inconsistencies across regions
- **JPEG Artifacts**: Checks compression artifact consistency
- **Edge Analysis**: Detects unnaturally sharp edges

**Manipulation Indicators:**
The system combines all analyses into a final manipulation assessment:
- Combined manipulation score (0-1)
- Overall verdict (AUTHENTIC / LOW / MODERATE / HIGH RISK)
- Specific indicators found
- Actionable recommendations

### 3. Enhanced Validation (`src/enhanced_validator.py`)

**Key Improvement:**
The validator now lists **ALL** issues found, not just representative examples.

**Validation Categories:**
1. **Formatting Issues**: Double spacing, irregular fonts, inconsistent indentation
2. **Content Issues**: Spelling errors, incorrect headers, missing sections, grammar
3. **Structure Issues**: Missing sections, incorrect order, incomplete documents
4. **Accuracy Issues**: Date inconsistencies, number formatting, contradictions

**Updated Prompt:**
```
CRITICAL INSTRUCTION: List ALL issues found, not just a few examples. 
Be exhaustive and complete.

If you find 10 spelling mistakes, list all 10. 
If you find 15 formatting issues, list all 15.
```

### 4. Firestore Audit Trail (`src/firestore_audit_logger.py`)

**Comprehensive Logging:**
Every action is logged with:
- **Timestamp**: ISO format and Unix timestamp
- **Agent**: Which component/model performed the action
- **Input Data**: Parameters and data used
- **Output Data**: Results and decisions made
- **Status**: Success, error, or warning
- **Error Details**: Full error messages and tracebacks
- **Metadata**: Additional context (duration, file info, etc.)

**Logged Actions:**
- Document parsing (format, success, text length)
- Image analysis (checks performed, results)
- Validation (issues found, scores)
- AI analysis (model used, risk assessment)
- External verification (API calls, results)
- Errors (with full traceback)
- Decisions (reasoning, confidence, factors)

**Storage Options:**
1. **Firestore**: Cloud-based with Firebase Admin SDK
2. **Local JSON**: Fallback to local JSONL files if Firebase unavailable

**Usage:**
```python
from firestore_audit_logger import FirestoreAuditLogger

logger = FirestoreAuditLogger(fallback_to_local=True)

# Log an action
logger.log_action(
    action_type='document_parsing',
    agent='pdf_parser',
    input_data={'file': 'doc.pdf'},
    output_data={'text_length': 5000},
    status='success'
)

# Retrieve session logs
logs = logger.get_session_logs()

# Generate audit report
report = logger.generate_audit_report()
```

**Audit Report Generation:**
- Summary of all actions by type
- Detailed chronological log
- Error tracking
- Exportable as text file

## 🚀 Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

**New Dependencies Added:**
- `exifread==3.0.0` - EXIF metadata extraction
- `python-docx==1.1.2` - Word document parsing
- `google-search-results==2.4.2` - SerpAPI for reverse image search
- `firebase-admin==6.5.0` - Firestore audit logging
- `huggingface-hub==0.27.0` - AI model integration

### 2. Configure Environment Variables

Copy `.env.template` to `.env` and configure:

```bash
cp .env.template .env
```

**Required:**
```
GROQ_API_KEY=your-groq-api-key
```

**Optional (for advanced features):**
```
SERPAPI_KEY=your-serpapi-key
HUGGINGFACE_TOKEN=your-hf-token
FIREBASE_CREDENTIALS_PATH=/path/to/firebase-credentials.json
```

### 3. Setup Firebase (Optional, for Audit Trail)

1. Create Firebase project: https://console.firebase.google.com/
2. Enable Firestore Database
3. Generate service account key:
   - Project Settings > Service Accounts > Generate New Private Key
4. Save JSON file and set path in `.env`:
   ```
   FIREBASE_CREDENTIALS_PATH=/path/to/credentials.json
   ```

**Note:** If Firebase is not configured, the system automatically falls back to local JSON logging in `data/logs/audit_trail/`.

### 4. Install Tesseract OCR

**Windows:**
1. Download from: https://github.com/UB-Mannheim/tesseract/wiki
2. Install to default location: `C:\Program Files\Tesseract-OCR`
3. The system will auto-detect the installation

**Mac:**
```bash
brew install tesseract
```

**Linux:**
```bash
sudo apt-get install tesseract-ocr
```

## 📖 Usage Guide

### Running the Application

```bash
streamlit run streamlit_app.py
```

### Supported Document Formats

1. **PDF Files** (`.pdf`)
   - Scanned documents with OCR
   - Native PDF text extraction
   - Image extraction and analysis

2. **Images** (`.jpg`, `.jpeg`, `.png`, `.tiff`)
   - OCR text extraction
   - EXIF metadata analysis
   - AI-generated detection
   - Manipulation detection

3. **Text Files** (`.txt`)
   - Direct text reading
   - File metadata extraction

4. **Word Documents** (`.docx`)
   - Text extraction from paragraphs
   - Document properties analysis

### Analysis Workflow

1. **Upload Document**: Select any supported format
2. **Configure Settings**:
   - Document type (general/statement/invoice/contract)
   - OCR quality (DPI scale)
   - Enable/disable image analysis
   - Select image analysis checks
3. **Run Analysis**: Click "Start Comprehensive Analysis"
4. **Review Results**:
   - Overview: Risk assessment and key findings
   - Image Analysis: Manipulation indicators and detailed checks
   - Extracted Data: Structured fields from document
   - Validation Issues: ALL formatting, content, and structure issues
   - External Verification: Company registers and sanctions
   - AI Analysis: Comprehensive fraud assessment
   - Reports: Generate executive and detailed reports
   - Audit Trail: View complete action log

### Image Analysis Options

**Reverse Image Search** (requires SerpAPI):
- Detects if image appears elsewhere online
- Identifies stolen or reused images

**AI-Generated Detection**:
- Uses Hugging Face models
- Heuristic fallback if models unavailable
- Confidence scoring

**Metadata Tampering**:
- EXIF analysis
- Software modification detection
- Date inconsistency checks

**Pixel Anomalies**:
- Cloning detection
- Splicing detection
- Noise analysis
- Edge detection

## 🔍 API Keys & Services

### Required Services

**Groq** (Required):
- Free tier available
- Sign up: https://console.groq.com/
- Used for: AI analysis, validation, field extraction

### Optional Services

**SerpAPI** (Optional):
- Free tier: 100 searches/month
- Sign up: https://serpapi.com/
- Used for: Reverse image search

**Hugging Face** (Optional):
- Free tier available
- Sign up: https://huggingface.co/
- Used for: AI-generated image detection

**Firebase** (Optional):
- Free tier available (Spark plan)
- Sign up: https://console.firebase.google.com/
- Used for: Cloud-based audit logging

## 📊 Output Files

### Analysis Reports
- **Executive Report**: Management summary (`.txt`)
- **Detailed Report**: Complete analysis (`.txt`)
- **Complete Analysis**: All data (`.json`)

### Audit Logs
- **Firestore**: Cloud database (if configured)
- **Local JSONL**: `data/logs/audit_trail/<session_id>.jsonl`
- **Audit Report**: Human-readable summary (`.txt`)

### Temporary Files
- **Uploaded Documents**: `temp/<filename>`
- **Extracted Images**: `temp/pdf_images/`

## 🔧 Configuration Options

### OCR Quality
- **DPI Scale 1**: 72 DPI - Fast, lower quality
- **DPI Scale 2**: 144 DPI - Balanced
- **DPI Scale 3**: 216 DPI - High quality (default)
- **DPI Scale 4-5**: 288-360 DPI - Highest quality, slowest

### Image Analysis Sensitivity
All checks are configurable via UI checkboxes:
- Reverse Image Search
- AI-Generated Detection
- Metadata Tampering
- Pixel Anomaly Detection

## 🐛 Troubleshooting

### Tesseract Not Found
**Error**: "Tesseract not found in common locations"
**Solution**: 
1. Install Tesseract (see Setup Instructions)
2. Restart the application

### Firebase Connection Failed
**Error**: "Failed to initialize Firebase"
**Solution**: 
- Check credentials path in `.env`
- Ensure JSON file is valid
- System will automatically use local logging as fallback

### SerpAPI Errors
**Error**: "Reverse image search requires image URL"
**Solution**: 
- SerpAPI requires images to be accessible via URL
- System will log warning but continue analysis
- Consider hosting images temporarily or using local analysis only

### Out of Memory (Large PDFs)
**Solution**: 
- Reduce OCR DPI scale
- Process fewer pages at once
- Increase system memory

## 📝 Development Notes

### Adding New Document Formats

1. Update `UniversalDocumentParser._get_document_type()`
2. Add format to `supported_formats` dict
3. Implement parser method (e.g., `_parse_xml()`)
4. Update Streamlit file uploader types

### Adding New Image Analysis Checks

1. Add method to `AdvancedImageAnalyzer`
2. Update `analyze_image()` to call new check
3. Add to `_combine_manipulation_indicators()`
4. Update UI checkboxes in `streamlit_app.py`

### Customizing Validation Rules

Edit `enhanced_validator.py`:
- Update templates in `_load_templates()`
- Modify prompt to add new validation categories
- Adjust severity thresholds

## 🎓 Best Practices

1. **Document Quality**: Higher DPI for better OCR, but slower processing
2. **Image Analysis**: Enable all checks for maximum fraud detection
3. **Audit Trail**: Keep Firebase enabled for compliance and auditability
4. **Regular Updates**: Update API keys and dependencies regularly
5. **Error Handling**: Review audit logs for any failed analyses

## 📚 Technical Architecture

```
streamlit_app.py (Main UI)
    ├── universal_document_parser.py (Multi-format parsing)
    │   ├── PDF: PyMuPDF + Tesseract OCR
    │   ├── Images: PIL + exifread + OCR
    │   ├── Text: Direct reading
    │   └── DOCX: python-docx
    │
    ├── advanced_image_analyzer.py (Image fraud detection)
    │   ├── Reverse Search: SerpAPI
    │   ├── AI Detection: Hugging Face + Heuristics
    │   ├── Metadata: EXIF analysis
    │   └── Pixels: scipy + numpy
    │
    ├── enhanced_validator.py (Document validation)
    │   └── Groq AI: Exhaustive issue listing
    │
    ├── structured_extractor.py (Field extraction)
    ├── external_verification.py (Company/sanctions checks)
    ├── ai_fraud_detector.py (Fraud analysis)
    └── firestore_audit_logger.py (Audit trail)
        ├── Firebase Firestore (cloud)
        └── Local JSONL (fallback)
```

## 🔒 Security Considerations

1. **API Keys**: Never commit `.env` file to version control
2. **Firebase Credentials**: Secure JSON files, use environment variables
3. **Audit Logs**: May contain sensitive document data - secure appropriately
4. **Temporary Files**: Automatically cleaned, but consider manual cleanup for sensitive docs
5. **Cloud Services**: Review Firebase security rules for production use

## 📞 Support

For issues or questions:
1. Check troubleshooting section above
2. Review audit logs for detailed error information
3. Ensure all dependencies are correctly installed
4. Verify API keys and service availability

## 🚦 Status Indicators

The system provides clear visual feedback:
- 🟢 **GREEN (Low Risk)**: Document appears authentic
- 🟡 **YELLOW (Medium Risk)**: Some concerns, review recommended
- 🟠 **ORANGE (High Risk)**: Multiple red flags, additional verification needed
- 🔴 **RED (Critical)**: Strong fraud indicators, reject document

## 📈 Performance Metrics

Typical processing times (3-page PDF):
- Document Parsing: 5-15 seconds (depends on DPI)
- Image Analysis: 10-30 seconds per image
- Validation: 3-5 seconds
- AI Analysis: 5-10 seconds
- Total: 30-60 seconds

For optimal performance:
- Use DPI scale 2-3 for balanced speed/quality
- Disable image analysis for text-only documents
- Process documents in batches during off-peak hours

