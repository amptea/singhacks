"""
AI Fraud Detection UI - Working File Upload
Interactive interface that highlights suspicious parts with reasoning
"""

import streamlit as st
import os
import tempfile
from pathlib import Path
import time
import platform
import json
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="AI Fraud Detector",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for highlighting and styling
st.markdown("""
<style>
    .main-container {
        max-width: 1200px;
        margin: 0 auto;
        padding: 2rem 1rem;
    }
    
    /* Custom upload area */
    .upload-area {
        border: 3px dashed #d1d5db;
        border-radius: 15px;
        padding: 4rem 2rem;
        text-align: center;
        transition: all 0.3s ease;
        background: #fafafa;
        margin: 2rem 0;
        cursor: pointer;
    }
    
    .upload-area:hover {
        border-color: #3b82f6;
        background: #f8faff;
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(59, 130, 246, 0.1);
    }
    
    .upload-icon {
        font-size: 4rem;
        margin-bottom: 1rem;
        color: #6b7280;
    }
    
    .upload-text {
        font-size: 1.3rem;
        color: #374151;
        font-weight: 500;
        margin-bottom: 0.5rem;
    }
    
    .upload-subtext {
        font-size: 1rem;
        color: #6b7280;
    }
    
    /* Hide the actual file uploader but keep it functional */
    .hidden-uploader {
        position: absolute;
        opacity: 0;
        width: 100%;
        height: 100%;
        top: 0;
        left: 0;
        cursor: pointer;
    }
    
    .upload-wrapper {
        position: relative;
        display: inline-block;
        width: 100%;
    }
    
    /* File info card */
    .file-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 2rem;
        margin: 2rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    
    /* Risk level badges */
    .risk-minimal { background: #dcfce7; color: #166534; border: 1px solid #bbf7d0; }
    .risk-low { background: #dbeafe; color: #1e40af; border: 1px solid #bfdbfe; }
    .risk-medium { background: #fef3c7; color: #92400e; border: 1px solid #fde68a; }
    .risk-high { background: #fecaca; color: #991b1b; border: 1px solid #fca5a5; }
    .risk-critical { background: #fecaca; color: #7f1d1d; border: 1px solid #fca5a5; font-weight: bold; }
    
    .risk-badge {
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.9rem;
        display: inline-block;
        margin: 0.25rem;
    }
    
    /* Highlighting for suspicious content */
    .suspicious-high {
        background: #fef2f2;
        border-left: 4px solid #dc2626;
        padding: 0.5rem 1rem;
        margin: 0.5rem 0;
        border-radius: 4px;
    }
    
    .suspicious-medium {
        background: #fffbeb;
        border-left: 4px solid #d97706;
        padding: 0.5rem 1rem;
        margin: 0.5rem 0;
        border-radius: 4px;
    }
    
    .suspicious-low {
        background: #f0f9ff;
        border-left: 4px solid #0369a1;
        padding: 0.5rem 1rem;
        margin: 0.5rem 0;
        border-radius: 4px;
    }
    
    .finding-item {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    .critical-item {
        background: #fef2f2;
        border: 1px solid #fecaca;
        border-left: 4px solid #dc2626;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { background-color: #fef2f2; }
        50% { background-color: #fee2e2; }
        100% { background-color: #fef2f2; }
    }
    
    .metric-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    .risk-score-high {
        color: #dc2626;
        font-weight: bold;
        font-size: 1.2em;
    }
    
    .risk-score-medium {
        color: #d97706;
        font-weight: bold;
        font-size: 1.2em;
    }
    
    .risk-score-low {
        color: #059669;
        font-weight: bold;
        font-size: 1.2em;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

def get_risk_color(risk_level):
    """Get CSS class for risk level"""
    risk_map = {
        'MINIMAL': 'risk-minimal',
        'LOW': 'risk-low', 
        'MEDIUM': 'risk-medium',
        'HIGH': 'risk-high',
        'CRITICAL': 'risk-critical'
    }
    return risk_map.get(risk_level.upper(), 'risk-medium')

def get_risk_score_class(score):
    """Get CSS class for risk score"""
    if score >= 8:
        return 'risk-score-high'
    elif score >= 5:
        return 'risk-score-medium'
    else:
        return 'risk-score-low'

def format_suspicious_reasoning(analysis):
    """Format suspicious findings with reasoning"""
    formatted = []
    
    # Critical Issues
    if analysis.get('critical_issues'):
        formatted.append("### 🔴 Critical Issues")
        for issue in analysis['critical_issues']:
            formatted.append(f'<div class="critical-item">🚨 **Critical**: {issue}</div>')
        formatted.append("")
    
    # Primary Concerns
    if analysis.get('primary_concerns'):
        formatted.append("### ⚠️ Primary Concerns")
        for concern in analysis['primary_concerns']:
            formatted.append(f'<div class="suspicious-high">⚠️ {concern}</div>')
        formatted.append("")
    
    # Format Validation Issues
    format_issues = analysis.get('format_validation', {})
    if format_issues.get('red_flags'):
        formatted.append("### 📝 Format Red Flags")
        for flag in format_issues['red_flags']:
            formatted.append(f'<div class="suspicious-medium">📝 {flag}</div>')
        formatted.append("")
    
    # Image Analysis Concerns
    image_issues = analysis.get('image_analysis', {})
    if image_issues.get('concerns'):
        formatted.append("### 🖼️ Image Concerns")
        for concern in image_issues['concerns']:
            formatted.append(f'<div class="suspicious-medium">🖼️ {concern}</div>')
        formatted.append("")
    
    # Metadata Issues
    metadata_issues = analysis.get('metadata_analysis', {})
    if metadata_issues.get('suspicious_elements'):
        formatted.append("### 📊 Metadata Issues")
        for element in metadata_issues['suspicious_elements']:
            formatted.append(f'<div class="suspicious-low">📊 {element}</div>')
        formatted.append("")
    
    # Content Analysis Red Flags
    content_issues = analysis.get('content_analysis', {})
    if content_issues.get('red_flags'):
        formatted.append("### 📄 Content Red Flags")
        for flag in content_issues['red_flags']:
            formatted.append(f'<div class="suspicious-medium">📄 {flag}</div>')
        formatted.append("")
    
    # Key Findings
    if analysis.get('key_findings'):
        formatted.append("### 🔍 Key Findings")
        for finding in analysis['key_findings']:
            formatted.append(f'<div class="finding-item">🔍 {finding}</div>')
        formatted.append("")
    
    return "\n".join(formatted)

def main():
    """AI Fraud Detection UI"""
    
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div style='text-align: center; margin-bottom: 3rem;'>
        <h1 style='margin-bottom: 0.5rem;'>🔍 AI Fraud Detection</h1>
        <p style='color: #6b7280; font-size: 1.1rem;'>
            Upload documents to detect fraud with AI-powered analysis
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None
    if 'uploaded_file' not in st.session_state:
        st.session_state.uploaded_file = None
    
    # File upload section - Using a different approach
    st.markdown("### 📁 Upload Document")
    
    # Create a custom file uploader using st.file_uploader but with better styling
    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=["pdf"],
        label_visibility="collapsed",
        help="Drag and drop a PDF file here or click to browse"
    )
    
    # Display custom upload area when no file is selected
    if uploaded_file is None:
        st.markdown("""
        <div class="upload-area" onclick="document.querySelector('input[type=file]').click()">
            <div class="upload-icon">📁</div>
            <div class="upload-text">Drag & Drop PDF Here</div>
            <div class="upload-subtext">or click to browse files • PDF only</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Add some JavaScript to make the entire area clickable
        st.markdown("""
        <script>
            // Make the entire upload area clickable
            const uploadArea = document.querySelector('.upload-area');
            const fileInput = document.querySelector('input[type="file"]');
            
            if (uploadArea && fileInput) {
                uploadArea.addEventListener('click', function() {
                    fileInput.click();
                });
                
                // Add drag and drop visual feedback
                uploadArea.addEventListener('dragover', function(e) {
                    e.preventDefault();
                    this.style.borderColor = '#3b82f6';
                    this.style.background = '#f0f4ff';
                });
                
                uploadArea.addEventListener('dragleave', function(e) {
                    e.preventDefault();
                    this.style.borderColor = '#d1d5db';
                    this.style.background = '#fafafa';
                });
                
                uploadArea.addEventListener('drop', function(e) {
                    e.preventDefault();
                    this.style.borderColor = '#d1d5db';
                    this.style.background = '#fafafa';
                    // The file input will automatically handle the drop
                });
            }
        </script>
        """, unsafe_allow_html=True)
    
    # Store uploaded file in session state
    if uploaded_file is not None:
        st.session_state.uploaded_file = uploaded_file
    
    # Show file info and analysis options when file is uploaded
    if st.session_state.uploaded_file is not None:
        uploaded_file = st.session_state.uploaded_file
        
        st.markdown(f"""
        <div class="file-card">
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <div>
                    <div style="font-size: 1.3rem; font-weight: 600; color: #374151; margin-bottom: 0.5rem;">
                        📄 {uploaded_file.name}
                    </div>
                    <div style="color: #6b7280; font-size: 1rem;">
                        Size: {uploaded_file.size / 1024:.1f} KB • Ready for fraud analysis
                    </div>
                </div>
                <div style="color: #10b981; font-size: 2rem;">✅</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Analysis settings
        with st.expander("🔧 Analysis Settings", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                api_key = st.text_input(
                    "Groq API Key",
                    type="password",
                    placeholder="Enter your Groq API key",
                    help="Get free key from: https://console.groq.com/keys"
                )
                # You can also set it via environment variable
                if not api_key:
                    api_key = os.environ.get("GROQ_API_KEY")
                    
            with col2:
                model = st.selectbox(
                    "AI Model",
                    ["llama-3.3-70b-versatile", "llama-3.2-90b-text-preview", "mixtral-8x7b-32768"],
                    index=0
                )
        
        # Analyze button
        if st.button("🔍 Analyze for Fraud", type="primary", use_container_width=True):
            if not api_key:
                st.error("❌ Please enter your Groq API key")
                st.info("Get a free key from: https://console.groq.com/keys")
            else:
                with st.spinner("🤖 AI is analyzing document for fraud patterns..."):
                    try:
                        # Save uploaded file temporarily
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                            tmp_file.write(uploaded_file.getvalue())
                            tmp_path = tmp_file.name
                        
                        # Import and run fraud detection
                        # Make sure ai_fraud_detector.py is in the same directory
                        from ai_fraud_detector import AIFraudDetector
                        
                        start_time = time.time()
                        detector = AIFraudDetector(groq_api_key=api_key, model=model)
                        results = detector.analyze_document(tmp_path)
                        processing_time = time.time() - start_time
                        
                        # Store results
                        st.session_state.analysis_results = results
                        st.session_state.processing_time = processing_time
                        
                        # Clean up
                        os.unlink(tmp_path)
                        
                        st.success("✅ Fraud analysis complete!")
                        
                    except Exception as e:
                        st.error(f"❌ Analysis failed: {str(e)}")
                        st.info("Make sure all required files are in the same directory and dependencies are installed.")
    
    # Display analysis results
    if st.session_state.analysis_results is not None:
        results = st.session_state.analysis_results
        analysis = results['ai_analysis']
        
        st.markdown("---")
        
        # Risk Overview
        st.subheader("📊 Risk Overview")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            risk_score = analysis['risk_score']
            risk_class = get_risk_score_class(risk_score)
            st.markdown(f"""
            <div class="metric-card">
                <div style="font-size: 0.9rem; color: #6b7280; margin-bottom: 0.5rem;">Risk Score</div>
                <div class="{risk_class}" style="font-size: 2rem;">{risk_score}/10</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            risk_level = analysis['risk_level']
            risk_class = get_risk_color(risk_level)
            st.markdown(f"""
            <div class="metric-card">
                <div style="font-size: 0.9rem; color: #6b7280; margin-bottom: 0.5rem;">Risk Level</div>
                <div class="risk-badge {risk_class}">{risk_level}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            fraud_likelihood = analysis['fraud_likelihood']
            risk_class = get_risk_color(fraud_likelihood)
            st.markdown(f"""
            <div class="metric-card">
                <div style="font-size: 0.9rem; color: #6b7280; margin-bottom: 0.5rem;">Fraud Likelihood</div>
                <div class="risk-badge {risk_class}">{fraud_likelihood}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            confidence = analysis['confidence'] * 100
            st.markdown(f"""
            <div class="metric-card">
                <div style="font-size: 0.9rem; color: #6b7280; margin-bottom: 0.5rem;">AI Confidence</div>
                <div style="font-size: 1.5rem; font-weight: bold; color: #059669;">{confidence:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Recommendation
        rec = analysis.get('recommendations', {})
        recommendation = rec.get('approval_recommendation', 'REVIEW')
        justification = rec.get('justification', '')
        
        if recommendation == 'REJECT':
            st.error(f"🚫 Recommendation: {recommendation} - {justification}")
        elif recommendation == 'REVIEW':
            st.warning(f"⚠️ Recommendation: {recommendation} - {justification}")
        else:
            st.success(f"✅ Recommendation: {recommendation} - {justification}")
        
        # Suspicious Findings with Reasoning
        st.subheader("🔍 Suspicious Findings & Reasoning")
        
        # Create tabs for different views
        tab1, tab2, tab3 = st.tabs(["🎯 Key Findings", "📋 Detailed Analysis", "📄 Extracted Text"])
        
        with tab1:
            # Format and display suspicious findings
            suspicious_content = format_suspicious_reasoning(analysis)
            if suspicious_content.strip():
                st.markdown(suspicious_content, unsafe_allow_html=True)
            else:
                st.info("No suspicious findings detected. Document appears legitimate.")
            
            # Immediate actions if any
            if analysis.get('recommendations', {}).get('immediate_actions'):
                st.markdown("### 🚨 Immediate Actions Required")
                for i, action in enumerate(analysis['recommendations']['immediate_actions'], 1):
                    st.markdown(f"**{i}.** {action}")
        
        with tab2:
            # Detailed analysis
            if analysis.get('detailed_analysis'):
                st.markdown("### 📖 Comprehensive Analysis")
                st.markdown(analysis['detailed_analysis'])
            else:
                st.info("No detailed analysis available")
            
            # Show full analysis JSON in expander
            with st.expander("View Raw Analysis Data"):
                st.json(analysis.get('full_analysis', {}))
        
        with tab3:
            # Extracted text from document
            doc_data = results.get('document_data', {})
            extracted_text = doc_data.get('text', 'No text extracted')
            
            st.markdown("### 📄 Extracted Document Text")
            st.text_area(
                "Full extracted text",
                extracted_text,
                height=400,
                label_visibility="collapsed"
            )
        
        # Additional document info
        with st.expander("📊 Document Statistics"):
            doc_data = results.get('document_data', {})
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Pages", doc_data.get('total_pages', 0))
                st.metric("File Size", f"{doc_data.get('file_size', 0) / 1024:.1f} KB")
            
            with col2:
                st.metric("Images Found", len(doc_data.get('images', [])))
                st.metric("Unique Fonts", len(doc_data.get('fonts', [])))
            
            with col3:
                structure = doc_data.get('structure', {})
                st.metric("Text Length", f"{structure.get('text_length', 0):,} chars")
                st.metric("Word Count", f"{structure.get('word_count', 0):,} words")
        
        # Action buttons
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📥 Download Reports", use_container_width=True):
                st.info("Report download would be implemented here")
        
        with col2:
            if st.button("🔄 Analyze New Document", use_container_width=True):
                # Reset session state
                for key in ['analysis_results', 'uploaded_file', 'processing_time']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()