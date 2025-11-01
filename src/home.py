"""
SingHacks - Regulatory Compliance Suite
Main navigation hub for all tools
"""

import streamlit as st
from streamlit import switch_page

# Page configuration
st.set_page_config(
    page_title="SingHacks - Compliance Suite",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
        font-weight: bold;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 3rem;
    }
    .tool-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        padding: 2rem;
        margin: 1rem 0;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: transform 0.3s ease;
    }
    .tool-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 12px rgba(0,0,0,0.2);
    }
    .tool-card-alt {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        border-radius: 15px;
        padding: 2rem;
        margin: 1rem 0;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: transform 0.3s ease;
    }
    .tool-card-alt:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 12px rgba(0,0,0,0.2);
    }
    .tool-title {
        font-size: 1.8rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .tool-description {
        font-size: 1rem;
        margin-bottom: 1.5rem;
        line-height: 1.6;
    }
    .feature-list {
        list-style: none;
        padding-left: 0;
    }
    .feature-list li {
        padding: 0.5rem 0;
        padding-left: 1.5rem;
        position: relative;
    }
    .feature-list li:before {
        content: "✓";
        position: absolute;
        left: 0;
        font-weight: bold;
        font-size: 1.2rem;
    }
    .launch-button {
        background-color: white;
        color: #667eea;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 25px;
        font-size: 1.1rem;
        font-weight: bold;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .launch-button:hover {
        background-color: #f0f0f0;
        transform: scale(1.05);
    }
    .info-box {
        background-color: #f8f9fa;
        border-left: 4px solid #1f77b4;
        border-radius: 5px;
        padding: 1.5rem;
        margin: 2rem 0;
    }
    .stats-container {
        display: flex;
        justify-content: space-around;
        margin: 2rem 0;
    }
    .stat-box {
        text-align: center;
        padding: 1rem;
    }
    .stat-number {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
    }
    .stat-label {
        font-size: 1rem;
        color: #666;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Header
    st.markdown('<div class="main-header">🏠 SingHacks Compliance Suite</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Intelligent Tools for Regulatory Compliance & Document Processing</div>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("📋 Quick Navigation")
        st.markdown("---")
        
        selected_tool = st.radio(
            "Select a tool:",
            ["Home", "MAS Regulation Compliance", "AI Fraud Detection"],
            index=0
        )
        
        st.markdown("---")
        st.subheader("ℹ️ About")
        st.info("""
        **SingHacks** provides automated tools for:
        - Regulatory compliance monitoring
        - Document text extraction
        - AI-powered analysis
        """)
        
        st.markdown("---")
        st.subheader("🔗 Resources")
        st.markdown("""
        - [MAS Website](https://www.mas.gov.sg)
        - [Notice 626](https://www.mas.gov.sg/regulation/notices/notice-626)
        - [GitHub Repository](https://github.com/amptea/singhacks)
        """)
    
    # Main content based on selection
    if selected_tool == "Home":
        show_home_page()
    elif selected_tool == "MAS Regulation Compliance":
        show_mas_tool_info()
    elif selected_tool == "AI Fraud Detection":
        show_fraud_detection_info()

def show_home_page():
    """Display the home page with tool cards"""
    
    # Stats section
    st.markdown('<div class="stats-container">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="stat-box">
            <div class="stat-number">2</div>
            <div class="stat-label">Tools Available</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="stat-box">
            <div class="stat-number">15+</div>
            <div class="stat-label">Clauses Analyzed</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="stat-box">
            <div class="stat-number">AI</div>
            <div class="stat-label">Powered Analysis</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Tool 1: MAS Regulation Compliance
    st.markdown("""
    <div class="tool-card">
        <div class="tool-title">📊 MAS Regulation Compliance Viewer</div>
        <div class="tool-description">
            Automated monitoring and validation of MAS Notice 626 regulations. 
            Compares official MAS documents with your organization's compliance documentation 
            using AI-powered clause-by-clause analysis.
        </div>
        <ul class="feature-list">
            <li>Real-time scraping of MAS Notice 626</li>
            <li>Comprehensive clause-by-clause comparison</li>
            <li>AI-powered consistency scoring</li>
            <li>Detailed compliance gap analysis</li>
            <li>Interactive results dashboard</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Launch MAS Compliance Viewer", type="primary", use_container_width=True, key="mas_btn"):
            st.switch_page("pages/1__MAS_Compliance.py")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Tool 2: AI Fraud Detection
    st.markdown("""
    <div class="tool-card-alt">
        <div class="tool-title">🔍 AI-Powered Fraud Detection System</div>
        <div class="tool-description">
            Comprehensive document fraud detection using JigsawStack OCR and Groq AI. 
            Analyzes documents for authenticity, validates content, extracts structured data, 
            and provides risk scoring with actionable recommendations.
        </div>
        <ul class="feature-list">
            <li>JigsawStack OCR for PDFs, images (JPG, PNG), and text files</li>
            <li>AI-powered structured field extraction (names, IDs, amounts, etc.)</li>
            <li>Format & content validation with LLM reasoning</li>
            <li>External verification (company registers, sanction lists, PEP data)</li>
            <li>Comprehensive fraud risk scoring and reporting</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Launch AI Fraud Detection", type="primary", use_container_width=True, key="fraud_btn"):
            st.switch_page("pages/2__PDF_OCR.py")
    

def show_mas_tool_info():
    """Show detailed info about MAS Regulation Compliance tool"""
    st.header("📊 MAS Regulation Compliance Viewer")
    
    st.markdown("""
    ### Overview
    The MAS Regulation Compliance Viewer helps organizations monitor and validate their compliance 
    with MAS Notice 626 (Prevention of Money Laundering and Countering the Financing of Terrorism – Banks).
    
    ### Key Features
    
    #### 🔍 Automated Monitoring
    - Automatically scrapes the latest MAS Notice 626 from the official MAS website
    - Extracts complete PDF content for analysis
    - No manual download or updates required
    
    #### 🤖 AI-Powered Analysis
    - Uses Groq AI (llama-3.3-70b-versatile) for intelligent comparison
    - Analyzes ALL clauses comprehensively (4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, etc.)
    - Distinguishes between substantive and cosmetic differences
    
    #### 📈 Detailed Reporting
    - Consistency score (percentage match)
    - Clause-by-clause breakdown
    - Critical vs minor differences
    - Interactive dashboard with tables and metrics
    
    ### Source of Truth
    - **Primary Source**: MAS Notice 626 PDF (official regulation)
    - **Validation Target**: `data/mas.json` (your organization's documentation)
    - **Purpose**: Ensures your docs stay aligned with official requirements
    
    ### How to Use
    1. Ensure `GROQ_API_KEY` is set in `.env` file
    2. Run the agent: `python agents/part1/regIngestAgent.py`
    3. View results in UI: `streamlit run src/mas_scraping_ui.py`
    4. Review compliance gaps and update `mas.json` as needed
    
    ### Launch Command
    ```bash
    streamlit run src/mas_scraping_ui.py
    ```
    """)
    
    if st.button("📚 View Documentation", type="secondary"):
        st.info("Documentation available at: `agents/README.md`")

def show_fraud_detection_info():
    """Show detailed info about AI Fraud Detection tool"""
    st.header("🔍 AI-Powered Fraud Detection System")
    
    st.markdown("""
    ### Overview
    The AI Fraud Detection System provides comprehensive document fraud detection using 
    cutting-edge AI technology. It combines JigsawStack's advanced OCR with Groq AI's 
    reasoning capabilities to detect fraud indicators across multiple dimensions.
    
    ### Key Features
    
    #### 📄 Multi-Format Document Processing
    - **JigsawStack OCR**: Industry-leading text extraction
    - **Supported formats**: PDF, JPG, PNG, JPEG, TXT
    - **Multi-page support**: Up to 10 pages per document
    - **Fallback system**: PyMuPDF for PDFs if OCR fails
    
    #### 🔍 Structured Field Extraction
    - **AI-powered parsing**: Automatically extracts key fields
    - **Document info**: Type, number, date, issuer
    - **Parties**: Names, IDs, addresses, contact info
    - **Financial**: Bank names, SWIFT codes, transaction IDs, amounts
    - **Additional**: Account numbers, purpose, notes
    - **Output**: Clean JSON structure for easy analysis
    
    #### ✅ Advanced Validation
    - **Formatting checks**: Double spacing, irregular fonts, inconsistent indentation
    - **Content validation**: Spelling errors, incorrect headers, missing sections
    - **Structure analysis**: Document organization and completeness
    - **Template matching**: Comparison against standard document types
    - **AI reasoning**: LLM explains each validation issue
    
    #### 🌐 External Verification
    - **Company registers**: OpenCorporates, GLEIF, EU Business Register
    - **Sanction lists**: OFAC, EU, UN (via public APIs)
    - **PEP databases**: Politically Exposed Persons screening
    - **Match confidence**: AI-calculated similarity scores
    - **Discrepancy detection**: Flags mismatches between document and external data
    
    #### 🎯 Risk Scoring & Reporting
    - **Risk scores**: 0-10 scale with AI reasoning
    - **Risk levels**: Critical (8-10), High (6-8), Medium (4-6), Low (2-4), Minimal (0-2)
    - **Key findings**: Prioritized list of fraud indicators
    - **Recommendations**: Actionable next steps for compliance officers
    - **Audit trail**: Complete processing log for compliance records
    
    ### How It Works
    
    1. **Upload**: Drag & drop document (PDF, image, or text)
    2. **Parse**: JigsawStack OCR extracts text from document
    3. **Extract**: AI identifies and structures key data fields
    4. **Validate**: LLM checks formatting, content, and organization
    5. **Verify**: Optional external checks against company/sanction databases
    6. **Analyze**: Comprehensive AI fraud risk assessment
    7. **Report**: Downloadable JSON report with full analysis
    
    ### Requirements
    
    #### API Keys (Required)
    - **Groq API**: Get free key at [console.groq.com/keys](https://console.groq.com/keys)
    - **JigsawStack API**: Sign up at [jigsawstack.com](https://jigsawstack.com)
    
    #### Configuration
    Create `.env` file in project root:
    ```
    GROQ_API_KEY=your-groq-key
    JIGSAWSTACK_API_KEY=your-jigsawstack-key
    ```
    
    #### Python Packages
    All dependencies listed in `requirements.txt`:
    ```bash
    pip install groq jigsawstack python-dotenv streamlit requests PyMuPDF Pillow
    ```
    
    ### Use Cases
    
    - **Financial Compliance**: Validate bank statements, invoices, receipts
    - **Identity Verification**: Check ID documents, certificates
    - **Contract Analysis**: Verify contracts, agreements
    - **KYC/AML**: Know Your Customer and Anti-Money Laundering checks
    - **Document Authentication**: Detect forged or manipulated documents
    
    ### Launch Command
    ```bash
    cd src
    streamlit run home.py
    ```
    
    Then navigate to "AI Fraud Detection" from the sidebar or home page.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔑 Get Groq API Key", type="secondary", use_container_width=True):
            st.info("Visit: https://console.groq.com/keys")
    
    with col2:
        if st.button("🔑 Get JigsawStack API Key", type="secondary", use_container_width=True):
            st.info("Visit: https://jigsawstack.com")

if __name__ == "__main__":
    main()
