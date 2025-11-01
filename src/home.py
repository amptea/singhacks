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
    .simple-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px;
        padding: 2.5rem 2rem;
        margin: 1.5rem 0;
        color: white;
        text-align: center;
        cursor: pointer;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
        border: none;
    }
    .simple-button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 15px rgba(0,0,0,0.2);
    }
    .button-title {
        font-size: 2rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .button-desc {
        font-size: 1rem;
        opacity: 0.95;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Header
    st.markdown('<div class="main-header">🏠 SingHacks Compliance Suite</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Intelligent Tools for Regulatory Compliance & Document Processing</div>', unsafe_allow_html=True)
    
    # Minimal Sidebar
    with st.sidebar:
        st.markdown("### Navigation")
        st.markdown("Use the buttons below to access different tools")
    
    # Main content - Three simple buttons
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Button 1: MAS Compliance Viewer
    col1, col2, col3 = st.columns([1, 10, 1])
    with col2:
        if st.button("MAS Regulation Compliance Viewer", type="primary", use_container_width=True, key="mas_btn", help="Monitor and validate MAS Notice 626 compliance"):
            st.switch_page("pages/1__MAS_Compliance.py")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Button 2: PDF OCR Extractor
    col1, col2, col3 = st.columns([1, 10, 1])
    with col2:
        if st.button("PDF OCR Text Extractor", type="primary", use_container_width=True, key="ocr_btn", help="Extract text from scanned PDFs using OCR"):
            st.switch_page("pages/2__PDF_OCR.py")
    
    st.markdown("<br>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
