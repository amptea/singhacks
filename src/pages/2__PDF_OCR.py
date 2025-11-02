"""
Comprehensive Fraud Detection & Compliance Verification System
Enhanced with Multi-Format Support, Advanced Image Analysis, and Audit Trail
"""

import streamlit as st
import sys
import json
from pathlib import Path
import pandas as pd
from datetime import datetime

# Add src to path
sys.path.insert(0, 'src')

# Import components
from universal_document_parser import UniversalDocumentParser
from structured_extractor import StructuredFieldExtractor
from enhanced_validator import EnhancedDocumentValidator
from advanced_image_analyzer import AdvancedImageAnalyzer
from ai_fraud_detector import AIFraudDetector
from firestore_audit_logger import FirestoreAuditLogger

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
if 'audit_logger' not in st.session_state:
    st.session_state.audit_logger = FirestoreAuditLogger(fallback_to_local=True)


def main():
    st.title("🔍 Enhanced Compliance Verification System")
    st.markdown("**Automated Document Fraud Detection with Advanced Image Analysis & Audit Trail**")
    
    # Sidebar
    with st.sidebar:
        st.header("Analysis Steps")
        st.markdown("""
        1. **Upload Document** (PDF/Image/Text/DOCX)
        2. **Parse & Extract** (Universal Parser)
        3. **Image Analysis** (AI Detection, Metadata, Reverse Search)
        4. **Validate Format** (List ALL issues)
        5. **Generate Report**
        6. **Audit Trail** (Firestore)
        """)

        st.divider()

        st.header("Settings")
        document_type = st.selectbox(
            "Document Type",
            ["general", "statement", "invoice", "contract"]
        )

        # External verification removed from UI; default to False
        use_external_verification = False

        # OCR DPI scale
        ocr_dpi_scale = st.slider(
            "OCR DPI Scale",
            min_value=1,
            max_value=5,
            value=2,
            help="Higher scale = better OCR but slower"
        )

        st.divider()
        st.subheader("🖼️ Image Analysis")

        enable_image_analysis = st.checkbox(
            "Enable Advanced Image Analysis",
            value=True,
            help="Analyze images for fraud indicators"
        )

        if enable_image_analysis:
            check_reverse_search = st.checkbox(
                "Reverse Image Search",
                value=True,
                help="Check if image is stolen/reused (requires SerpAPI)"
            )

            check_ai_generated = st.checkbox(
                "AI-Generated Detection",
                value=True,
                help="Detect AI-generated images"
            )

            check_metadata_tampering = st.checkbox(
                "Metadata Tampering",
                value=True,
                help="Check EXIF metadata for manipulation"
            )

            check_pixel_anomalies = st.checkbox(
                "Pixel Anomaly Detection",
                value=True,
                help="Detect cloning, splicing, and other manipulations"
            )
        else:
            check_reverse_search = False
            check_ai_generated = False
            check_metadata_tampering = False
            check_pixel_anomalies = False

        st.divider()

        if st.session_state.analysis_complete:
            if st.button("🔄 New Analysis"):
                st.session_state.analysis_complete = False
                st.session_state.results = None
                st.rerun()
    
    # Main content
    if not st.session_state.analysis_complete:
        show_upload_interface(
            document_type,
            use_external_verification,
            ocr_dpi_scale,
            enable_image_analysis,
            check_reverse_search,
            check_ai_generated,
            check_metadata_tampering,
            check_pixel_anomalies
        )
    else:
        show_results_interface()


def show_upload_interface(
    document_type,
    use_external_verification,
    ocr_dpi_scale,
    enable_image_analysis,
    check_reverse_search,
    check_ai_generated,
    check_metadata_tampering,
    check_pixel_anomalies
):
    """Document upload and analysis interface"""
    
    st.header("📄 Step 1: Upload Document")
    
    uploaded_file = st.file_uploader(
        "Upload document for analysis",
        type=['pdf', 'jpg', 'jpeg', 'png', 'txt', 'docx'],
        help="Supported: PDF, Images (JPG/PNG), Text files (TXT), Word documents (DOCX)"
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
            analyze_document(
                str(temp_path),
                document_type,
                use_external_verification,
                ocr_dpi_scale,
                enable_image_analysis,
                check_reverse_search,
                check_ai_generated,
                check_metadata_tampering,
                check_pixel_anomalies
            )


def analyze_document(
    file_path,
    document_type,
    use_external_verification,
    ocr_dpi_scale,
    enable_image_analysis,
    check_reverse_search,
    check_ai_generated,
    check_metadata_tampering,
    check_pixel_anomalies
):
    """Run comprehensive document analysis with audit trail"""
    
    audit_logger = st.session_state.audit_logger
    
    results = {
        'file_path': file_path,
        'file_name': Path(file_path).name,
        'document_type': document_type,
        'timestamp': datetime.now().isoformat(),
        'stages': {}
    }
    
    # Log analysis start
    audit_logger.log_document_analysis_start(
        file_path,
        document_type,
        {
            'external_verification': use_external_verification,
            'ocr_dpi_scale': ocr_dpi_scale,
            'image_analysis_enabled': enable_image_analysis
        }
    )
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    start_time = datetime.now()
    
    try:
        # Stage 1: Parse Document with Universal Parser
        status_text.text("📄 Stage 1/6: Parsing document (Universal Parser)...")
        progress_bar.progress(15)
        
        with st.spinner(f"Parsing document (DPI Scale: {ocr_dpi_scale})..."):
            parser = UniversalDocumentParser(dpi_scale=ocr_dpi_scale)
            parsed = parser.parse_document(file_path)
            results['stages']['parsing'] = parsed
            
            # Log parsing
            audit_logger.log_parsing(
                parser_name='UniversalDocumentParser',
                file_path=file_path,
                text_extracted=parsed.get('text', ''),
                metadata_extracted=parsed.get('metadata', {}),
                success=parsed.get('success', False)
            )
        
        if not parsed.get('success') or not parsed.get('text'):
            st.error("❌ Document parsing failed: No text extracted")
            st.stop()
        
        st.success(f"✓ Extracted {len(parsed['text'])} characters using {parsed.get('parser_used', 'unknown')}")
        
        # Stage 2: Advanced Image Analysis (if image document or PDF with images)
        if enable_image_analysis and (parsed.get('is_image_document') or parsed.get('images')):
            status_text.text("🖼️ Stage 2/6: Advanced image analysis...")
            progress_bar.progress(30)
            
            with st.spinner("Analyzing images for manipulation..."):
                image_analyzer = AdvancedImageAnalyzer()
                
                # Analyze based on document type
                if parsed.get('format') == 'pdf' and parsed.get('images'):
                    # PDF with images - analyze all images
                    image_analysis = image_analyzer.analyze_pdf_images(
                        file_path,
                        check_reverse_search=check_reverse_search,
                        check_ai_generated=check_ai_generated,
                        check_metadata_tampering=check_metadata_tampering,
                        check_pixel_anomalies=check_pixel_anomalies
                    )
                elif parsed.get('is_image_document'):
                    # Direct image file
                    image_analysis = image_analyzer.analyze_image(
                        file_path,
                        check_reverse_search=check_reverse_search,
                        check_ai_generated=check_ai_generated,
                        check_metadata_tampering=check_metadata_tampering,
                        check_pixel_anomalies=check_pixel_anomalies
                    )
                else:
                    image_analysis = {'skipped': True, 'reason': 'No images found'}
                
                results['stages']['image_analysis'] = image_analysis
                
                # Log image analysis
                audit_logger.log_image_analysis(
                    analyzer_name='AdvancedImageAnalyzer',
                    image_path=file_path,
                    analysis_results=image_analysis,
                    checks_performed=image_analysis.get('analysis_performed', [])
                )
            
            st.success("✓ Image analysis complete")
        else:
            results['stages']['image_analysis'] = {'skipped': True, 'reason': 'Image analysis disabled or no images'}
            progress_bar.progress(30)
        
        # Stage 3: Extract Structured Fields
        status_text.text("🔍 Stage 3/6: Extracting structured fields...")
        progress_bar.progress(45)
        
        with st.spinner("Extracting structured data with AI..."):
            extractor = StructuredFieldExtractor()
            extracted = extractor.extract_fields(parsed['text'], document_type)
            results['stages']['extraction'] = extracted
        
        if extracted['success']:
            st.success(f"✓ Extracted {extracted['fields_found']} data fields")
        
        # Stage 4: Enhanced Validation (LIST ALL ISSUES)
        status_text.text("✅ Stage 4/6: Validating document (listing ALL issues)...")
        progress_bar.progress(60)
        
        with st.spinner("Running comprehensive validation..."):
            validator = EnhancedDocumentValidator()
            validation = validator.validate_document(
                parsed['text'],
                document_type,
                extracted.get('extracted_fields')
            )
            results['stages']['validation'] = validation
            
            # Log validation
            audit_logger.log_validation(
                validator_name='EnhancedDocumentValidator',
                document_text=parsed['text'],
                validation_results=validation
            )
        
        total_issues = validation.get('total_issues_found', sum([
            len(validation.get('formatting_issues', [])),
            len(validation.get('content_issues', [])),
            len(validation.get('structure_issues', []))
        ]))
        
        st.success(f"✓ Validation: {validation.get('overall_quality', 'N/A')} ({total_issues} total issues)")
        
        # Stage 5: External Verification intentionally skipped/disabled
        results['stages']['verification'] = {'skipped': True}
        progress_bar.progress(75)
        
        # Stage 6: AI Fraud Analysis (Groq) - analyze using aggregated pipeline results
        status_text.text("🤖 Stage 6/6: AI fraud analysis with Groq...")
        progress_bar.progress(90)

        with st.spinner("AI analyzing all findings (Groq)..."):
            try:
                detector = AIFraudDetector()
                # Provide the aggregated results (all stages) so the model can reason across them
                fraud_analysis = detector.analyze_from_aggregated(results)
                # keep compatibility with expected structure
                results['stages']['fraud_analysis'] = {'ai_analysis': fraud_analysis}

                # Log AI analysis
                try:
                    audit_logger.log_ai_analysis(
                        model_name=detector.model,
                        input_prompt=f"Aggregated analysis for {Path(file_path).name}",
                        output_analysis=fraud_analysis
                    )
                except Exception:
                    logger = None

                st.success("✓ AI analysis complete")
            except Exception as e:
                st.error(f"❌ AI analysis failed: {e}")
                # Fallback: set a conservative default
                results['stages']['fraud_analysis'] = {'ai_analysis': {
                    'overall_summary': 'AI analysis failed - manual review required',
                    'risk_score': 5,
                    'risk_level': 'MEDIUM',
                    'confidence': 0.3,
                    'key_findings': ['AI analysis error - see logs']
                }}
        
        # Complete
        progress_bar.progress(100)
        status_text.text("✅ Analysis Complete!")
        
        # Log completion
        duration = (datetime.now() - start_time).total_seconds()
        audit_logger.log_document_analysis_complete(
            file_path,
            results,
            duration
        )
        
        # Save results to session state
        st.session_state.results = results
        st.session_state.analysis_complete = True
        
        # Auto-refresh to show results
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Analysis failed: {str(e)}")
        
        # Log error
        import traceback
        audit_logger.log_error(
            component='analyze_document',
            error_message=str(e),
            error_traceback=traceback.format_exc(),
            context={'file_path': file_path}
        )
        
        st.exception(e)
        st.stop()


def show_results_interface():
    """Display comprehensive results interface"""
    
    results = st.session_state.results
    
    st.header("📊 Analysis Results")
    st.markdown(f"**Document:** {results['file_name']} | **Type:** {results['document_type']}")
    
    # Create tabs (External Verification & AI Analysis removed)
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📋 Overview",
        "🖼️ Image Analysis",
        "🔍 Extracted Data",
        "✅ Validation Issues",
        "📄 Reports",
        "📜 Audit Trail"
    ])

    with tab1:
        show_overview_tab(results)

    with tab2:
        show_image_analysis_tab(results)

    with tab3:
        show_extracted_data_tab(results)

    with tab4:
        show_validation_tab(results)

    with tab5:
        show_reports_tab(results)

    with tab6:
        show_audit_trail_tab()


def show_overview_tab(results):
    """Overview dashboard"""
    
    st.subheader("Risk Assessment Summary")
    
    # Get fraud analysis
    fraud = results['stages'].get('fraud_analysis', {}).get('ai_analysis', {})
    verification = results['stages'].get('verification', {})
    validation = results['stages'].get('validation', {})
    image_analysis = results['stages'].get('image_analysis', {})
    
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
    
    # Image manipulation indicators
    if not image_analysis.get('skipped'):
        st.subheader("🖼️ Image Manipulation Assessment")
        
        if 'manipulation_indicators' in image_analysis:
            manip = image_analysis['manipulation_indicators']
            st.markdown(f"**Verdict:** {manip.get('verdict', 'UNKNOWN')}")
            st.markdown(f"**Manipulation Score:** {manip.get('combined_manipulation_score', 0):.2%}")
            st.markdown(f"**Recommendation:** {manip.get('recommendation', 'N/A')}")
            
            if manip.get('indicators'):
                st.markdown("**Indicators:**")
                for indicator in manip['indicators']:
                    st.markdown(f"• {indicator}")
        elif 'images_analyzed' in image_analysis:
            st.markdown(f"**Images Analyzed:** {len(image_analysis['images_analyzed'])}")
            for img_result in image_analysis['images_analyzed']:
                if 'manipulation_indicators' in img_result:
                    manip = img_result['manipulation_indicators']
                    st.markdown(f"• Page {img_result.get('pdf_page', 'N/A')}: {manip.get('verdict', 'UNKNOWN')}")
    
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


def show_image_analysis_tab(results):
    """Show detailed image analysis"""
    
    st.subheader("🖼️ Advanced Image Analysis Results")
    
    image_analysis = results['stages'].get('image_analysis', {})
    
    if image_analysis.get('skipped'):
        st.info(f"Image analysis skipped: {image_analysis.get('reason', 'Unknown')}")
        return
    
    # Check if single image or PDF with multiple images
    if 'images_analyzed' in image_analysis:
        # PDF with multiple images
        st.markdown(f"**Total Images Analyzed:** {image_analysis['images_found']}")
        
        for i, img_result in enumerate(image_analysis['images_analyzed'], 1):
            with st.expander(f"Image {i} - Page {img_result.get('pdf_page', 'N/A')}", expanded=i==1):
                display_single_image_analysis(img_result)
    else:
        # Single image
        display_single_image_analysis(image_analysis)


def display_single_image_analysis(analysis):
    """Display analysis for a single image"""
    
    # Manipulation indicators summary
    if 'manipulation_indicators' in analysis:
        manip = analysis['manipulation_indicators']
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Verdict", manip.get('verdict', 'UNKNOWN'))
        with col2:
            st.metric("Manipulation Score", f"{manip.get('combined_manipulation_score', 0):.0%}")
        with col3:
            st.metric("Confidence", f"{manip.get('confidence', 0):.0%}")
        
        st.markdown(f"**Recommendation:** {manip.get('recommendation', 'N/A')}")
        
        if manip.get('indicators'):
            st.markdown("**Manipulation Indicators:**")
            for indicator in manip['indicators']:
                st.warning(f"⚠️ {indicator}")
    
    st.divider()
    
    # Detailed analysis sections
    
    # 1. Reverse Image Search
    if 'reverse_search' in analysis:
        with st.expander("🔍 Reverse Image Search"):
            rs = analysis['reverse_search']
            if rs.get('success'):
                st.markdown(f"**Matches Found:** {rs.get('matches_found', 0)}")
                st.markdown(f"**Stolen Image Likelihood:** {rs.get('stolen_image_likelihood', 'UNKNOWN')}")
                if rs.get('warning'):
                    st.info(rs['warning'])
            else:
                st.error(f"Error: {rs.get('error', 'Unknown')}")
    
    # 2. AI-Generated Detection
    if 'ai_detection' in analysis:
        with st.expander("🤖 AI-Generated Detection"):
            ai = analysis['ai_detection']
            st.markdown(f"**Verdict:** {ai.get('verdict', 'UNKNOWN')}")
            st.markdown(f"**AI Confidence:** {ai.get('ai_generated_confidence', 0):.0%}")
            st.markdown(f"**Models Tested:** {', '.join(ai.get('models_tested', []))}")
            
            if ai.get('details'):
                st.json(ai['details'])
    
    # 3. Metadata Tampering
    if 'metadata_analysis' in analysis:
        with st.expander("📋 Metadata Tampering Analysis"):
            meta = analysis['metadata_analysis']
            if meta.get('success'):
                st.markdown(f"**Verdict:** {meta.get('verdict', 'UNKNOWN')}")
                st.markdown(f"**Tampering Risk Score:** {meta.get('tampering_risk_score', 0):.0%}")
                st.markdown(f"**EXIF Data Present:** {'Yes' if meta.get('exif_data_present') else 'No'}")
                st.markdown(f"**Total EXIF Tags:** {meta.get('total_exif_tags', 0)}")
                
                if meta.get('tampering_indicators'):
                    st.markdown(f"**Tampering Indicators Found:** {len(meta['tampering_indicators'])}")
                    for indicator in meta['tampering_indicators']:
                        severity = indicator.get('severity', 'LOW')
                        if severity == 'HIGH':
                            st.error(f"🔴 {indicator.get('indicator')}: {indicator.get('description')}")
                        elif severity == 'MEDIUM':
                            st.warning(f"🟡 {indicator.get('indicator')}: {indicator.get('description')}")
                        else:
                            st.info(f"🟢 {indicator.get('indicator')}: {indicator.get('description')}")
            else:
                st.error(f"Error: {meta.get('error', 'Unknown')}")
    
    # 4. Pixel Anomalies
    if 'pixel_analysis' in analysis:
        with st.expander("🔬 Pixel-Level Anomaly Detection"):
            pixel = analysis['pixel_analysis']
            if pixel.get('success'):
                st.markdown(f"**Verdict:** {pixel.get('verdict', 'UNKNOWN')}")
                st.markdown(f"**Anomaly Score:** {pixel.get('anomaly_score', 0):.0%}")
                st.markdown(f"**Anomalies Detected:** {pixel.get('total_anomalies', 0)}")
                
                if pixel.get('anomalies_detected'):
                    for anomaly in pixel['anomalies_detected']:
                        severity = anomaly.get('severity', 'LOW')
                        if severity == 'HIGH':
                            st.error(f"🔴 {anomaly.get('type')}: {anomaly.get('description')}")
                        elif severity == 'MEDIUM':
                            st.warning(f"🟡 {anomaly.get('type')}: {anomaly.get('description')}")
                        else:
                            st.info(f"🟢 {anomaly.get('type')}: {anomaly.get('description')}")
            else:
                st.error(f"Error: {pixel.get('error', 'Unknown')}")


def show_extracted_data_tab(results):
    """Show extracted structured data"""
    
    st.subheader("Extracted Structured Fields")
    
    extracted = results['stages'].get('extraction', {}).get('extracted_fields', {})
    
    if extracted:
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
    """Show validation issues - ALL OF THEM"""
    
    st.subheader("Document Validation Results (ALL Issues Listed)")
    
    validation = results['stages'].get('validation', {})
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Completeness", f"{validation.get('completeness_score', 0)}%")
    with col2:
        st.metric("Accuracy", f"{validation.get('accuracy_score', 0)}%")
    with col3:
        quality = validation.get('overall_quality', 'Unknown')
        st.metric("Quality", quality.title())
    with col4:
        total = validation.get('total_issues_found', sum([
            len(validation.get('formatting_issues', [])),
            len(validation.get('content_issues', [])),
            len(validation.get('structure_issues', []))
        ]))
        st.metric("Total Issues", total)
    
    st.divider()
    
    # Issues by category - LIST ALL
    issue_categories = [
        ('Formatting Issues', 'formatting_issues', '📝'),
        ('Content Issues', 'content_issues', '📄'),
        ('Structure Issues', 'structure_issues', '🏗️')
    ]
    
    for title, key, icon in issue_categories:
        issues = validation.get(key, [])
        
        if issues:
            st.subheader(f"{icon} {title} ({len(issues)} issues)")
            
            # Create table - SHOW ALL ISSUES
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
                hide_index=True,
                height=min(400, len(issues) * 35 + 38)  # Adjust height based on number of issues
            )


def show_verification_tab(results):
    """Show external verification results"""
    
    st.subheader("External Verification Results")
    
    verification = results['stages'].get('verification', {})
    
    if verification.get('skipped'):
        st.info("External verification was skipped")
        return
    
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
    
    with st.expander("Sanctions Check Details"):
        st.json(sanctions)


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
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Executive Summary Report")
        st.markdown("Management-ready summary")
        if st.button("Generate Executive Report"):
            generate_executive_report(results)
    
    with col2:
        st.markdown("### Detailed Compliance Report")
        st.markdown("Complete analysis")
        if st.button("Generate Detailed Report"):
            generate_detailed_report(results)
    
    st.divider()
    
    st.markdown("### Export Complete Analysis")
    
    if st.button("Export All Data (JSON)"):
        st.download_button(
            "Download Complete Analysis",
            data=json.dumps(results, indent=2, default=str),
            file_name=f"complete_analysis_{results['file_name']}.json",
            mime="application/json"
        )


def show_audit_trail_tab():
    """Show audit trail"""
    
    st.subheader("📜 Audit Trail")
    
    audit_logger = st.session_state.audit_logger
    
    st.markdown(f"**Session ID:** {audit_logger.session_id}")
    
    # Get session logs
    logs = audit_logger.get_session_logs()
    
    if not logs:
        st.info("No audit logs available for this session")
        return
    
    st.markdown(f"**Total Actions Logged:** {len(logs)}")
    
    # Summary
    action_types = {}
    for log in logs:
        action_type = log.get('action_type', 'unknown')
        action_types[action_type] = action_types.get(action_type, 0) + 1
    
    st.markdown("### Action Summary")
    summary_df = pd.DataFrame([
        {'Action Type': k, 'Count': v}
        for k, v in action_types.items()
    ])
    st.dataframe(summary_df, use_container_width=True, hide_index=True)
    
    st.divider()
    
    # Detailed logs
    st.markdown("### Detailed Log Entries")
    
    for i, log in enumerate(logs, 1):
        with st.expander(f"[{i}] {log.get('timestamp', 'N/A')} - {log.get('action_type', 'unknown')}"):
            st.json(log)
    
    # Generate audit report
    if st.button("Generate Audit Report"):
        report = audit_logger.generate_audit_report()
        
        st.download_button(
            "Download Audit Report",
            data=report,
            file_name=f"audit_report_{audit_logger.session_id}.txt",
            mime="text/plain"
        )


def generate_executive_report(results):
    """Generate executive summary report"""
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
