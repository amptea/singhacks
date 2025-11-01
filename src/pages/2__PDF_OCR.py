"""
AI-Powered Fraud Detection & PDF OCR
Streamlit-based interface with JigsawStack OCR and AI fraud detection
"""

import streamlit as st
import os
import sys
import tempfile
from pathlib import Path
import time
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Page configuration
st.set_page_config(
    page_title="AI Fraud Detection & PDF OCR",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffc107;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .risk-high {
        background-color: #ff4444;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
    }
    .risk-medium {
        background-color: #ff9800;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
    }
    .risk-low {
        background-color: #4caf50;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Import AI fraud detector
try:
    from document_parser_jigsawstack import JigsawDocumentParser
    from ai_fraud_detector import AIFraudDetector
    from structured_extractor import StructuredFieldExtractor
    from enhanced_validator import EnhancedDocumentValidator
    from external_verification import ExternalVerificationAgent
    
    IMPORTS_OK = True
except ImportError as e:
    st.error(f"❌ Missing dependencies: {e}")
    st.info("Please ensure all required modules are installed")
    IMPORTS_OK = False

def display_risk_badge(risk_level, risk_score):
    """Display colored risk badge"""
    if risk_score >= 7:
        risk_class = "risk-high"
        emoji = "🔴"
    elif risk_score >= 4:
        risk_class = "risk-medium"
        emoji = "🟡"
    else:
        risk_class = "risk-low"
        emoji = "🟢"
    
    return f'{emoji} <span class="{risk_class}">{risk_level} ({risk_score}/10)</span>'

def main():
    """Main Streamlit application"""
    
    # Header
    st.markdown('<div class="main-header">🔍 AI-Powered Fraud Detection System</div>', unsafe_allow_html=True)
    st.markdown("### Upload documents for comprehensive fraud detection analysis powered by AI")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Document type selection
        doc_type = st.selectbox(
            "Document Type",
            [
                "statement",
                "invoice",
                "contract",
                "certificate",
                "identity",
                "financial_report",
                "receipt",
                "other"
            ],
            help="Select the type of document for specialized analysis"
        )
        
        # Analysis options
        st.subheader("📊 Analysis Options")
        use_external_verification = st.checkbox(
            "External Verification",
            value=False,
            help="Query company registers and sanction lists (takes longer)"
        )
        
        show_debug = st.checkbox(
            "Show Debug Info",
            value=False,
            help="Display detailed API responses and processing logs"
        )
        
        st.markdown("---")
        
        # API Key status
        st.subheader("🔑 API Status")
        
        # Check for API keys
        from dotenv import load_dotenv
        load_dotenv()
        
        groq_key = os.getenv("GROQ_API_KEY")
        jigsaw_key = os.getenv("JIGSAWSTACK_API_KEY")
        
        if groq_key:
            st.success("✅ Groq API")
        else:
            st.error("❌ Groq API Key Missing")
        
        if jigsaw_key:
            st.success("✅ JigsawStack API")
        else:
            st.error("❌ JigsawStack API Key Missing")
        
        st.markdown("---")
        st.info("""
        **How it works:**
        1. Upload PDF/image document
        2. JigsawStack OCR extracts text
        3. AI extracts structured data
        4. AI validates format & content
        5. Optional external verification
        6. AI generates fraud risk report
        """)
    
    # Main content
    if not IMPORTS_OK:
        st.error("Cannot proceed without required dependencies")
        return
    
    # File uploader
    st.subheader("📤 Upload Document")
    
    uploaded_file = st.file_uploader(
        "Drag and drop your document here (PDF, JPG, PNG, TXT)",
        type=['pdf', 'jpg', 'jpeg', 'png', 'txt'],
        help="Upload a document for AI-powered fraud detection analysis"
    )
    
    if uploaded_file is not None:
        # File info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Filename", uploaded_file.name)
        with col2:
            st.metric("Size", f"{uploaded_file.size / 1024:.2f} KB")
        with col3:
            st.metric("Type", uploaded_file.type)
        
        # Analyze button
        if st.button("🚀 Analyze Document", type="primary", use_container_width=True):
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name
            
            try:
                # Progress tracking
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Initialize results container
                results = {
                    'stages': {},
                    'overall_risk': None,
                    'processing_time': 0
                }
                
                start_time = time.time()
                
                # Stage 1: Parse Document
                status_text.text("📄 Stage 1/5: Parsing document with JigsawStack OCR...")
                progress_bar.progress(20)
                
                with st.spinner("Extracting text from document..."):
                    parser = JigsawDocumentParser()
                    parsed = parser.parse_document(tmp_path)
                    results['stages']['parsing'] = parsed
                
                if not parsed.get('success', False):
                    st.error(f"❌ Document parsing failed: {parsed.get('error', 'Unknown error')}")
                    st.info("💡 Check your JigsawStack API key in .env file")
                    os.unlink(tmp_path)
                    return
                
                parser_method = parsed.get('parser_used', 'jigsawstack')
                if 'warning' in parsed:
                    st.warning(f"⚠️ {parsed['warning']}")
                
                pages_info = f"{parsed['page_count']} page(s)"
                if parsed.get('pages_processed') and parsed.get('pages_processed') != parsed.get('page_count'):
                    pages_info = f"{parsed['pages_processed']}/{parsed['page_count']} pages"
                
                st.success(f"✓ Extracted {len(parsed['text'])} characters from {pages_info} using {parser_method}")
                
                # Stage 2: Extract Structured Fields
                status_text.text("🔍 Stage 2/5: Extracting structured fields...")
                progress_bar.progress(40)
                
                with st.spinner("AI analyzing document structure..."):
                    extractor = StructuredFieldExtractor()
                    extracted = extractor.extract_fields(parsed['text'], document_type=doc_type)
                    results['stages']['extraction'] = extracted
                
                if extracted['success']:
                    st.success(f"✓ Extracted {extracted['fields_found']} data fields")
                
                # Stage 3: Enhanced Validation
                status_text.text("✅ Stage 3/5: Validating document quality...")
                progress_bar.progress(60)
                
                with st.spinner("AI checking format and content..."):
                    validator = EnhancedDocumentValidator()
                    validation = validator.validate_document(
                        parsed['text'],
                        doc_type,
                        extracted.get('extracted_fields')
                    )
                    results['stages']['validation'] = validation
                
                st.success(f"✓ Validation complete: {validation.get('overall_quality', 'N/A')}")
                
                # Stage 4: External Verification (if enabled)
                if use_external_verification:
                    status_text.text("🌐 Stage 4/5: Verifying with external sources...")
                    progress_bar.progress(75)
                    
                    with st.spinner("Checking company registers and sanction lists..."):
                        verifier = ExternalVerificationAgent()
                        verification = verifier.verify_entity(extracted)
                        results['stages']['verification'] = verification
                    
                    st.success("✓ External verification complete")
                else:
                    st.info("⏭️ Skipping external verification (disabled)")
                
                # Stage 5: AI Fraud Analysis
                status_text.text("🤖 Stage 5/5: AI fraud analysis...")
                progress_bar.progress(90)
                
                with st.spinner("Generating comprehensive fraud detection report..."):
                    detector = AIFraudDetector()
                    fraud_analysis = detector.analyze_document(tmp_path)
                    results['stages']['fraud_analysis'] = fraud_analysis
                
                # Complete
                progress_bar.progress(100)
                status_text.text("✅ Analysis complete!")
                
                results['processing_time'] = time.time() - start_time
                results['overall_risk'] = fraud_analysis.get('ai_analysis', {})
                
                # Store in session state
                st.session_state.results = results
                st.session_state.filename = uploaded_file.name
                
                # Clean up
                os.unlink(tmp_path)
                
                st.balloons()
                
            except Exception as e:
                st.error(f"❌ Error during analysis: {str(e)}")
                if show_debug:
                    st.exception(e)
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                return
    
    # Display Results
    if 'results' in st.session_state:
        st.markdown("---")
        st.header("📊 Analysis Results")
        
        results = st.session_state.results
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            risk_score = results['overall_risk'].get('risk_score', 0)
            st.metric("Risk Score", f"{risk_score}/10")
        
        with col2:
            risk_level = results['overall_risk'].get('risk_level', 'UNKNOWN')
            st.metric("Risk Level", risk_level)
        
        with col3:
            fields_found = results['stages'].get('extraction', {}).get('fields_found', 0)
            st.metric("Fields Extracted", fields_found)
        
        with col4:
            st.metric("Processing Time", f"{results['processing_time']:.1f}s")
        
        # Risk Badge
        st.markdown(
            f"### Overall Assessment: {display_risk_badge(risk_level, risk_score)}",
            unsafe_allow_html=True
        )
        
        # Tabs for detailed results
        tabs = st.tabs([
            "📋 Overview",
            "🔍 Extracted Data",
            "✅ Validation",
            "🌐 Verification",
            "🤖 AI Analysis",
            "📄 Full Report"
        ])
        
        # Tab 1: Overview
        with tabs[0]:
            st.subheader("Executive Summary")
            
            recommendations = results['overall_risk'].get('recommendations', [])
            if recommendations:
                st.markdown("**Recommendations:**")
                for rec in recommendations:
                    st.markdown(f"- {rec}")
            
            key_findings = results['overall_risk'].get('key_findings', [])
            if key_findings:
                st.markdown("**Key Findings:**")
                for finding in key_findings:
                    st.markdown(f"- {finding}")
        
        # Tab 2: Extracted Data
        with tabs[1]:
            st.subheader("Structured Fields")
            
            extraction = results['stages'].get('extraction', {})
            if extraction.get('success'):
                fields = extraction.get('extracted_fields', {})
                
                # Display in expanders by category
                for category, data in fields.items():
                    if data and data != {}:
                        with st.expander(f"📁 {category.replace('_', ' ').title()}"):
                            st.json(data)
            else:
                st.warning("No structured data extracted")
        
        # Tab 3: Validation
        with tabs[2]:
            st.subheader("Document Validation Results")
            
            validation = results['stages'].get('validation', {})
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Formatting Issues:**")
                formatting = validation.get('formatting_issues', [])
                if formatting:
                    for issue in formatting:
                        st.warning(f"⚠️ {issue.get('issue', 'Unknown')}: {issue.get('details', '')}")
                else:
                    st.success("✅ No formatting issues found")
            
            with col2:
                st.markdown("**Content Issues:**")
                content = validation.get('content_issues', [])
                if content:
                    for issue in content:
                        st.warning(f"⚠️ {issue.get('issue', 'Unknown')}: {issue.get('details', '')}")
                else:
                    st.success("✅ No content issues found")
        
        # Tab 4: Verification
        with tabs[3]:
            verification = results['stages'].get('verification', {})
            
            if verification:
                st.subheader("External Verification Results")
                
                # Company Register
                company_reg = verification.get('company_register', {})
                if company_reg:
                    with st.expander("🏢 Company Register"):
                        st.json(company_reg)
                
                # Sanctions
                sanctions = verification.get('sanctions', {})
                if sanctions:
                    with st.expander("🚫 Sanctions Check"):
                        st.json(sanctions)
            else:
                st.info("External verification was not performed")
        
        # Tab 5: AI Analysis
        with tabs[4]:
            st.subheader("Comprehensive AI Fraud Detection")
            
            ai_analysis = results['overall_risk']
            
            st.markdown("**Analysis Categories:**")
            
            # Format Analysis
            with st.expander("📋 Format Analysis"):
                format_analysis = ai_analysis.get('format_analysis', {})
                st.write(format_analysis.get('summary', 'No analysis available'))
                
                issues = format_analysis.get('issues', [])
                if issues:
                    for issue in issues:
                        st.warning(f"⚠️ {issue}")
            
            # Image Analysis
            with st.expander("🖼️ Image Analysis"):
                image_analysis = ai_analysis.get('image_analysis', {})
                st.write(image_analysis.get('summary', 'No analysis available'))
            
            # Content Analysis
            with st.expander("📝 Content Analysis"):
                content_analysis = ai_analysis.get('content_analysis', {})
                st.write(content_analysis.get('summary', 'No analysis available'))
        
        # Tab 6: Full Report
        with tabs[5]:
            st.subheader("Complete Analysis Report")
            
            # Generate downloadable report
            report = {
                'filename': st.session_state.filename,
                'analysis_date': time.strftime("%Y-%m-%d %H:%M:%S"),
                'risk_score': risk_score,
                'risk_level': risk_level,
                'results': results
            }
            
            report_json = json.dumps(report, indent=2, default=str)
            
            st.download_button(
                label="📥 Download JSON Report",
                data=report_json,
                file_name=f"fraud_analysis_{int(time.time())}.json",
                mime="application/json",
                use_container_width=True
            )
            
            st.json(report)

    # Footer
    st.markdown("---")
    st.markdown("Powered by JigsawStack OCR + Groq AI | Built for SingHacks")

if __name__ == "__main__":
    main()
