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
            ["Home", "MAS Regulation Compliance", "PDF OCR Extractor"],
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
    elif selected_tool == "PDF OCR Extractor":
        show_ocr_tool_info()

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
    
    # Tool 2: PDF OCR
    st.markdown("""
    <div class="tool-card-alt">
        <div class="tool-title">📄 PDF OCR Text Extractor</div>
        <div class="tool-description">
            Extract text from scanned PDF documents using advanced OCR technology. 
            Supports multiple languages and provides high-quality text extraction 
            for document digitization and analysis.
        </div>
        <ul class="feature-list">
            <li>Multi-language OCR support (English, German, French, etc.)</li>
            <li>Drag & drop PDF upload</li>
            <li>Adjustable quality settings</li>
            <li>Downloadable extracted text</li>
            <li>Real-time processing progress</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Launch PDF OCR Extractor", type="primary", use_container_width=True, key="ocr_btn"):
            st.switch_page("pages/2__PDF_OCR.py")
    
    # Additional info
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
    <div class="info-box">
        <h3>🎯 Getting Started</h3>
        <p><strong>Prerequisites:</strong></p>
        <ul>
            <li>Python 3.12+ installed</li>
            <li>Required packages: <code>pip install -r requirements.txt</code></li>
            <li>For OCR: Tesseract-OCR executable installed</li>
            <li>For MAS tool: Groq API key in <code>.env</code> file</li>
        </ul>
        <p><strong>Quick Start Commands:</strong></p>
        <ul>
            <li>MAS Compliance: <code>streamlit run src/mas_scraping_ui.py</code></li>
            <li>PDF OCR: <code>streamlit run src/pdf_ocr_ui.py</code></li>
            <li>Run Agent: <code>python agents/part1/regIngestAgent.py</code></li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

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

def show_ocr_tool_info():
    """Show detailed info about PDF OCR tool"""
    st.header("📄 PDF OCR Text Extractor")
    
    st.markdown("""
    ### Overview
    The PDF OCR Text Extractor converts scanned PDF documents into searchable, editable text 
    using advanced Optical Character Recognition (OCR) technology.
    
    ### Key Features
    
    #### 📤 Easy Upload
    - Drag & drop PDF interface
    - Supports all PDF file types
    - Real-time file size and format validation
    
    #### 🌍 Multi-Language Support
    - English, German, French, Spanish, Italian, Portuguese
    - Configurable language selection
    - Handles multilingual documents
    
    #### ⚙️ Customizable Processing
    - Adjustable DPI scale (1-4) for quality vs speed trade-off
    - Page-by-page progress tracking
    - Configurable Tesseract path
    
    #### 💾 Output Options
    - Text preview in browser
    - Download full extracted text
    - Copy to clipboard functionality
    
    ### Requirements
    
    #### Software
    - **Tesseract-OCR**: Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
    - Install to: `C:\\Program Files\\Tesseract-OCR\\tesseract.exe`
    
    #### Python Packages
    - pytesseract
    - Pillow
    - PyMuPDF (fitz)
    
    ### Best Practices
    - Use high-quality scans for better accuracy
    - Select appropriate languages for your document
    - Higher DPI scale = better quality but slower processing
    - Clear, legible source documents yield best results
    
    ### Launch Command
    ```bash
    streamlit run src/pdf_ocr_ui.py
    ```
    """)
    
    if st.button("🔧 Install Tesseract", type="secondary"):
        st.info("Download Tesseract: https://github.com/UB-Mannheim/tesseract/wiki")

if __name__ == "__main__":
    main()
