"""
Comprehensive Fraud Detection & Compliance Verification System
Streamlit Interface for Compliance Officers
"""

import streamlit as st
import sys
# Adjust path insertion if 'src' contains other dependencies like extractor and validator
# Assuming all necessary files (parse_pdf_ocr, ai_fraud_detector, etc.) are in the same directory or accessible via system path
# If document_parser_jigsawstack.py was in 'src', removing this line might break other imports if not adjusted.
# Keeping the sys.path.insert for other assumed modules, but commenting out the specific JigsawStack import.
sys.path.insert(0, 'src') 

# from document_parser_jigsawstack import JigsawDocumentParser # REMOVED JigsawStack dependency
from structured_extractor import StructuredFieldExtractor
from enhanced_validator import EnhancedDocumentValidator
from external_verification import ExternalVerificationAgent
from ai_fraud_detector import AIFraudDetector
# from groq_agent import FraudDetectionAgent # Not used in analyze_document, keeping for completeness if needed elsewhere
from parse_pdf_ocr import parse_pdf_to_text # ADDED dependency on local OCR parser
import json
from pathlib import Path
import pandas as pd
from datetime import datetime
import fitz # PyMuPDF is needed to get page count and other metadata (like size)

# Page config
st.set_page_config(
    page_title="Compliance Verification System",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .stAlert {margin-top: 1rem;}
    .risk-critical {background-color: #ff4444; color: white; padding: 10px; border-radius: 5px;}
    .risk-high {background-color: #ff8800; color: white; padding: 10px; border-radius: 5px;}
    .risk-medium {background-color: #ffbb33; color: black; padding: 10px; border-radius: 5px;}
    .risk-low {background-color: #00C851; color: white; padding: 10px; border-radius: 5px;}
    .issue-table {font-size: 14px;}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'analysis_complete' not in st.session_state:
    st.session_state.analysis_complete = False
if 'results' not in st.session_state:
    st.session_state.results = None


def main():
    st.title("🔍 Compliance Verification System")
    st.markdown("**Automated Document Fraud Detection & Entity Verification**")
    
    # Sidebar
    with st.sidebar:
        st.header("Analysis Steps")
        st.markdown("""
        1. **Upload Document**
        2. **Parse & Extract (Local OCR)**
        3. **Validate Format**
        4. **Verify Externally**
        5. **Generate Report**
        """)
        
        st.divider()
        
        st.header("Settings")
        document_type = st.selectbox(
            "Document Type",
            ["general", "statement", "invoice", "contract"]
        )
        
        use_external_verification = st.checkbox(
            "External Verification",
            value=True,
            help="Query company registers and sanction lists"
        )
        
        # New setting for OCR DPI scale
        ocr_dpi_scale = st.slider(
            "OCR DPI Scale",
            min_value=1,
            max_value=5,
            value=3,
            help="Higher scale (e.g., 3 = 216 DPI) results in better OCR but slower processing. Default is 3."
        )

        st.divider()
        
        if st.session_state.analysis_complete:
            if st.button("🔄 New Analysis"):
                st.session_state.analysis_complete = False
                st.session_state.results = None
                st.rerun()
    
    # Main content
    if not st.session_state.analysis_complete:
        show_upload_interface(document_type, use_external_verification, ocr_dpi_scale)
    else:
        show_results_interface()


def show_upload_interface(document_type, use_external_verification, ocr_dpi_scale):
    """Document upload and analysis interface"""
    
    st.header("📄 Step 1: Upload Document")
    
    uploaded_file = st.file_uploader(
        "Upload document for analysis",
        type=['pdf', 'jpg', 'jpeg', 'png', 'txt'],
        help="Supported: PDF, JPG, PNG, TXT (PDF is required for current parsing logic)"
    )
    
    if uploaded_file:
        # Display file info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("File Name", uploaded_file.name)
        with col2:
            st.metric("File Size", f"{uploaded_file.size / 1024:.1f} KB")
        with col3:
            st.metric("File Type", uploaded_file.type)
        
        # Save uploaded file
        temp_path = Path("temp") / uploaded_file.name
        temp_path.parent.mkdir(exist_ok=True)
        
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getvalue())
        
        st.success(f"✓ File uploaded: {uploaded_file.name}")
        
        # Analyze button
        if st.button("🚀 Start Comprehensive Analysis", type="primary"):
            # Check for PDF compatibility
            if uploaded_file.type != "application/pdf":
                st.error("❌ The current local OCR parsing only fully supports PDF files. Please upload a PDF.")
                st.stop()
            
            analyze_document(
                str(temp_path),
                document_type,
                use_external_verification,
                ocr_dpi_scale
            )


def analyze_document(file_path, document_type, use_external_verification, ocr_dpi_scale):
    """Run comprehensive document analysis, modified to use parse_pdf_to_text"""
    
    results = {
        'file_path': file_path,
        'file_name': Path(file_path).name,
        'document_type': document_type,
        'timestamp': datetime.now().isoformat(),
        'stages': {}
    }
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Stage 1: Parse Document using local OCR
        status_text.text("📄 Stage 1/5: Parsing document with local OCR...")
        progress_bar.progress(20)
        
        # Determine page count for status display
        page_count = 0
        try:
            doc = fitz.open(file_path)
            page_count = len(doc)
            doc.close()
        except Exception:
            # Continue even if page count fails, as text extraction might still work
            page_count = 1 
            st.warning("⚠️ Could not reliably determine page count.")
            
        with st.spinner(f"Parsing document with Tesseract OCR (DPI Scale: {ocr_dpi_scale})..."):
            extracted_text = parse_pdf_to_text(file_path, output_path=None, dpi_scale=ocr_dpi_scale)
            
            # Manually construct a 'parsed' structure for downstream compatibility
            parsed = {
                'success': True,
                'text': extracted_text,
                'page_count': page_count,
                'pages_processed': page_count, # Assume all pages are processed by the internal loop in parse_pdf_to_text
                'parser_used': f'local_ocr (DPI:{72 * ocr_dpi_scale})',
                'file_name': results['file_name'],
                'warning': 'Local OCR might be less accurate than commercial OCR for complex documents.'
            }
            results['stages']['parsing'] = parsed
        
        # Check if text was extracted
        if not extracted_text or extracted_text.strip() == "":
            st.error("❌ Document parsing failed: No text extracted. Check Tesseract installation or document quality.")
            st.info("💡 Tip: Ensure Tesseract OCR is correctly installed and accessible on your system.")
            st.stop()
        
        pages_info = f"{parsed['page_count']} page(s)"
        st.success(f"✓ Extracted {len(parsed['text'])} characters from {pages_info} using {parsed['parser_used']}")
        
        # Stage 2: Extract Structured Fields
        status_text.text("🔍 Stage 2/5: Extracting structured fields...")
        progress_bar.progress(40)
        
        with st.spinner("Extracting structured data with AI..."):
            extractor = StructuredFieldExtractor()
            extracted = extractor.extract_fields(parsed['text'], document_type)
            results['stages']['extraction'] = extracted
        
        if extracted['success']:
            st.success(f"✓ Extracted {extracted['fields_found']} data fields")
        
        # Stage 3: Enhanced Validation
        status_text.text("✅ Stage 3/5: Validating document quality...")
        progress_bar.progress(60)
        
        with st.spinner("Running comprehensive validation..."):
            validator = EnhancedDocumentValidator()
            validation = validator.validate_document(
                parsed['text'],
                document_type,
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
            
            st.success(f"✓ Verification complete: {verification.get('overall_status', 'N/A')}")
        else:
            results['stages']['verification'] = {'skipped': True}
            progress_bar.progress(75)
        
        # Stage 5: AI Fraud Analysis
        status_text.text("🤖 Stage 5/5: AI fraud analysis...")
        progress_bar.progress(90)
        
        with st.spinner("AI analyzing all findings..."):
            # AIFraudDetector internally calls _extract_document_data which uses parse_pdf_to_text again
            detector = AIFraudDetector()
            fraud_analysis = detector.analyze_document(file_path)
            results['stages']['fraud_analysis'] = fraud_analysis
        
        st.success("✓ AI analysis complete")
        
        # Complete
        progress_bar.progress(100)
        status_text.text("✅ Analysis Complete!")
        
        # Save results to session state
        st.session_state.results = results
        st.session_state.analysis_complete = True
        
        # Auto-refresh to show results
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Analysis failed: {str(e)}")
        st.exception(e)
        st.stop() # Stop execution if a major error occurs


def show_results_interface():
    """Display comprehensive results interface for compliance officers"""
    
    results = st.session_state.results
    
    st.header("📊 Analysis Results")
    st.markdown(f"**Document:** {results['file_name']} | **Type:** {results['document_type']}")
    
    # Create tabs for different views
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📋 Overview",
        "🔍 Extracted Data",
        "✅ Validation Issues",
        "🌐 External Verification",
        "🤖 AI Analysis",
        "📄 Reports"
    ])
    
    with tab1:
        show_overview_tab(results)
    
    with tab2:
        show_extracted_data_tab(results)
    
    with tab3:
        show_validation_tab(results)
    
    with tab4:
        show_verification_tab(results)
    
    with tab5:
        show_ai_analysis_tab(results)
    
    with tab6:
        show_reports_tab(results)


def show_overview_tab(results):
    """Overview dashboard"""
    
    st.subheader("Risk Assessment Summary")
    
    # Get fraud analysis
    fraud = results['stages'].get('fraud_analysis', {}).get('ai_analysis', {})
    verification = results['stages'].get('verification', {})
    validation = results['stages'].get('validation', {})
    
    # Risk score display
    risk_score = fraud.get('risk_score', 0)
    risk_level = fraud.get('risk_level', 'UNKNOWN')
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Risk Score", f"{risk_score}/10")
    with col2:
        st.metric("Risk Level", risk_level)
    with col3:
        completeness = validation.get('completeness_score', 0)
        st.metric("Completeness", f"{completeness}%")
    with col4:
        confidence = fraud.get('confidence', 0)
        st.metric("AI Confidence", f"{confidence*100:.0f}%")
    
    # Risk indicator
    if risk_level == "CRITICAL":
        st.markdown('<div class="risk-critical">⛔ CRITICAL RISK - REJECT DOCUMENT</div>', unsafe_allow_html=True)
    elif risk_level == "HIGH":
        st.markdown('<div class="risk-high">⚠️ HIGH RISK - DO NOT APPROVE</div>', unsafe_allow_html=True)
    elif risk_level == "MEDIUM":
        st.markdown('<div class="risk-medium">⚡ MEDIUM RISK - ADDITIONAL VERIFICATION REQUIRED</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="risk-low">✓ LOW RISK - STANDARD PROCESS</div>', unsafe_allow_html=True)
    
    st.divider()
    
    # Key findings
    st.subheader("Key Findings")
    key_findings = fraud.get('key_findings', [])
    if key_findings:
        for finding in key_findings:
            st.markdown(f"• {finding}")
    else:
        st.info("No significant findings")
    
    # Critical issues
    critical = fraud.get('critical_issues', [])
    if critical:
        st.subheader("⚠️ Critical Issues")
        for issue in critical:
            st.error(f"❌ {issue}")
    
    # Recommendations
    st.subheader("Recommended Actions")
    recommendations = fraud.get('recommendations', {})
    approval = recommendations.get('approval_recommendation', 'REVIEW')
    
    st.markdown(f"**Decision:** {approval}")
    
    for action in recommendations.get('immediate_actions', []):
        st.markdown(f"1. {action}")


def show_extracted_data_tab(results):
    """Show extracted structured data"""
    
    st.subheader("Extracted Structured Fields")
    
    extracted = results['stages'].get('extraction', {}).get('extracted_fields', {})
    
    if extracted:
        # Display as expandable sections
        for category, fields in extracted.items():
            with st.expander(f"📁 {category.replace('_', ' ').title()}", expanded=True):
                if isinstance(fields, dict):
                    df = pd.DataFrame([
                        {'Field': k.replace('_', ' ').title(), 'Value': v or 'N/A'}
                        for k, v in fields.items()
                    ])
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.json(fields)
        
        # Export option
        if st.button("📥 Export as JSON"):
            st.download_button(
                "Download JSON",
                data=json.dumps(extracted, indent=2),
                file_name=f"extracted_data_{results['file_name']}.json",
                mime="application/json"
            )
    else:
        st.info("No structured data extracted")


def show_validation_tab(results):
    """Show validation issues"""
    
    st.subheader("Document Validation Results")
    
    validation = results['stages'].get('validation', {})
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Completeness", f"{validation.get('completeness_score', 0)}%")
    with col2:
        st.metric("Accuracy", f"{validation.get('accuracy_score', 0)}%")
    with col3:
        quality = validation.get('overall_quality', 'Unknown')
        st.metric("Quality", quality.title())
    
    st.divider()
    
    # Issues by category
    issue_categories = [
        ('Formatting Issues', 'formatting_issues', '📝'),
        ('Content Issues', 'content_issues', '📄'),
        ('Structure Issues', 'structure_issues', '🏗️')
    ]
    
    for title, key, icon in issue_categories:
        issues = validation.get(key, [])
        
        if issues:
            st.subheader(f"{icon} {title} ({len(issues)})")
            
            # Create table
            issue_data = []
            for issue in issues:
                issue_data.append({
                    'Severity': issue.get('severity', 'low').upper(),
                    'Type': issue.get('type', 'unknown'),
                    'Location': issue.get('location', 'N/A'),
                    'Description': issue.get('description', '')
                })
            
            df = pd.DataFrame(issue_data)
            
            # Color code by severity
            def highlight_severity(row):
                if row['Severity'] == 'HIGH':
                    return ['background-color: #ff4444; color: white'] * len(row)
                elif row['Severity'] == 'MEDIUM':
                    return ['background-color: #ffbb33; color: black'] * len(row)
                return [''] * len(row)
            
            st.dataframe(
                df.style.apply(highlight_severity, axis=1),
                use_container_width=True,
                hide_index=True
            )


def show_verification_tab(results):
    """Show external verification results"""
    
    st.subheader("External Verification Results")
    
    verification = results['stages'].get('verification', {})
    
    if verification.get('skipped'):
        st.info("External verification was skipped")
        return
    
    # Overall status
    status = verification.get('overall_status', 'UNKNOWN')
    confidence = verification.get('match_confidence', 0)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Verification Status", status)
    with col2:
        st.metric("Match Confidence", f"{confidence*100:.0f}%")
    
    st.divider()
    
    # Company registers
    st.subheader("🏢 Company Registers")
    company = verification.get('company_register', {})
    
    col1, col2, col3 = st.columns(3)
    with col1:
        oc = company.get('opencorporates', {})
        st.metric("OpenCorporates", "✓ Found" if oc.get('found') else "Not Found")
        if oc.get('found'):
            st.json(oc)
    
    with col2:
        gleif = company.get('gleif', {})
        st.metric("GLEIF", "✓ Found" if gleif.get('found') else "Not Found")
        if gleif.get('found'):
            st.json(gleif)
    
    with col3:
        eu = company.get('eu_business_register', {})
        st.metric("EU Register", "✓ Found" if eu.get('found') else "Not Found")
    
    st.divider()
    
    # Sanctions check
    st.subheader("⚠️ Sanctions & Watchlists")
    sanctions = verification.get('sanctions', {})
    
    if sanctions.get('hit'):
        st.error("🚨 SANCTIONS HIT DETECTED!")
        st.warning("This entity appears on one or more sanctions lists. IMMEDIATE REVIEW REQUIRED.")
    else:
        st.success("✓ No sanctions hits")
    
    # Show details
    with st.expander("Sanctions Check Details"):
        st.json(sanctions)
    
    # AI reasoning
    st.divider()
    st.subheader("🤖 AI Verification Analysis")
    st.markdown(verification.get('ai_analysis', 'No analysis available'))
    
    # Discrepancies
    discrepancies = verification.get('discrepancies', [])
    if discrepancies:
        st.subheader("⚠️ Discrepancies Found")
        for disc in discrepancies:
            st.warning(disc)


def show_ai_analysis_tab(results):
    """Show comprehensive AI analysis"""
    
    st.subheader("🤖 AI Fraud Detection Analysis")
    
    fraud = results['stages'].get('fraud_analysis', {})
    ai_analysis = fraud.get('ai_analysis', {})
    
    # Overall summary
    st.markdown("### Executive Summary")
    st.info(ai_analysis.get('overall_summary', 'No summary available'))
    
    st.divider()
    
    # Detailed analysis by category
    categories = [
        ('Format Validation', 'format_validation'),
        ('Image Analysis', 'image_analysis'),
        ('Metadata Analysis', 'metadata_analysis'),
        ('Content Analysis', 'content_analysis')
    ]
    
    for title, key in categories:
        category_data = ai_analysis.get(key, {})
        if category_data:
            with st.expander(f"📊 {title}"):
                st.json(category_data)
    
    st.divider()
    
    # Detailed narrative
    st.markdown("### Detailed Analysis")
    detailed = ai_analysis.get('detailed_analysis', '')
    if detailed:
        st.markdown(detailed)
    else:
        st.info("No detailed analysis available")


def show_reports_tab(results):
    """Generate and download reports"""
    
    st.subheader("📄 Generate Compliance Reports")
    
    # Report generation
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Executive Summary Report")
        st.markdown("Management-ready summary with key findings and recommendations")
        if st.button("Generate Executive Report"):
            generate_executive_report(results)
    
    with col2:
        st.markdown("### Detailed Compliance Report")
        st.markdown("Complete analysis for compliance files")
        if st.button("Generate Detailed Report"):
            generate_detailed_report(results)
    
    st.divider()
    
    # Export all data
    st.markdown("### Export Complete Analysis")
    
    if st.button("Export All Data (JSON)"):
        st.download_button(
            "Download Complete Analysis",
            data=json.dumps(results, indent=2, default=str),
            file_name=f"complete_analysis_{results['file_name']}.json",
            mime="application/json"
        )


def generate_executive_report(results):
    """Generate executive summary report"""
    # Implementation in fraud detector already generates this
    fraud = results['stages'].get('fraud_analysis', {})
    reports = fraud.get('reports', {})
    
    if 'executive' in reports:
        with open(reports['executive'], 'r') as f:
            report_text = f.read()
        
        st.download_button(
            "Download Executive Report",
            data=report_text,
            file_name=f"executive_report_{results['file_name']}.txt",
            mime="text/plain"
        )
        st.success("✓ Report generated!")


def generate_detailed_report(results):
    """Generate detailed compliance report"""
    fraud = results['stages'].get('fraud_analysis', {})
    reports = fraud.get('reports', {})
    
    if 'detailed' in reports:
        with open(reports['detailed'], 'r') as f:
            report_text = f.read()
        
        st.download_button(
            "Download Detailed Report",
            data=report_text,
            file_name=f"detailed_report_{results['file_name']}.txt",
            mime="text/plain"
        )
        st.success("✓ Report generated!")


if __name__ == "__main__":
    main()