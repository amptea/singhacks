"""
Clean PDF OCR Parser - Minimal Modern UI
Streamlined interface without the blue background
"""

import streamlit as st
import os
import tempfile
from pathlib import Path
import time
import platform

# Page configuration - clean and minimal
st.set_page_config(
    page_title="PDF Text Extractor",
    page_icon="📄",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Clean CSS - no background colors
st.markdown("""
<style>
    .main-container {
        max-width: 800px;
        margin: 0 auto;
        padding: 2rem 1rem;
    }
    
    .upload-card {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 2.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    
    .upload-area {
        border: 2px dashed #d1d5db;
        border-radius: 10px;
        padding: 3rem 2rem;
        text-align: center;
        transition: all 0.2s ease;
        background: #fafafa;
        cursor: pointer;
    }
    
    .upload-area:hover {
        border-color: #3b82f6;
        background: #f8faff;
    }
    
    .metric-card {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
        border: 1px solid #e9ecef;
    }
    
    .stButton button {
        background: #3b82f6;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 2rem;
        font-weight: 500;
        width: 100%;
        transition: all 0.2s ease;
    }
    
    .stButton button:hover {
        background: #2563eb;
        transform: translateY(-1px);
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

def setup_tesseract():
    """Setup Tesseract OCR with auto-detection"""
    try:
        import pytesseract
        
        # Common Tesseract installation paths
        TESSERACT_PATHS = {
            'Windows': [
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            ],
            'Linux': ['/usr/bin/tesseract'],
            'Darwin': ['/usr/local/bin/tesseract', '/opt/homebrew/bin/tesseract']
        }
        
        # Auto-detect Tesseract
        system = platform.system()
        for path in TESSERACT_PATHS.get(system, []):
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                return True, path
        
        # Check if tesseract is in PATH
        try:
            pytesseract.get_tesseract_version()
            return True, "PATH"
        except:
            return False, None
            
    except ImportError:
        return False, None

def parse_pdf_to_text(pdf_path, dpi_scale=2, languages=['eng']):
    """Parse PDF and extract text using OCR"""
    try:
        import pytesseract
        from PIL import Image
        import fitz
        
        pdf_document = fitz.open(pdf_path)
        all_text = []
        total_pages = len(pdf_document)
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for page_num in range(total_pages):
            progress_bar.progress((page_num + 1) / total_pages)
            status_text.text(f"Processing page {page_num + 1} of {total_pages}")
            
            page = pdf_document[page_num]
            mat = fitz.Matrix(dpi_scale, dpi_scale)
            pix = page.get_pixmap(matrix=mat)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            lang_config = '+'.join(languages)
            text = pytesseract.image_to_string(img, lang=lang_config)
            
            all_text.append(f"\n--- Page {page_num + 1} ---\n\n{text}")
        
        pdf_document.close()
        progress_bar.empty()
        status_text.empty()
        
        return "".join(all_text), None
        
    except Exception as e:
        return None, str(e)

def main():
    """Clean PDF OCR Application"""
    
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    
    # Header - Simple and clean
    st.markdown("""
    <div style='text-align: center; margin-bottom: 3rem;'>
        <h1 style='margin-bottom: 0.5rem;'>📄 PDF Text Extractor</h1>
        <p style='color: #6b7280; font-size: 1.1rem;'>
            Extract text from scanned PDF documents using OCR
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Setup Tesseract
    tesseract_configured, tesseract_path = setup_tesseract()
    
    if not tesseract_configured:
        st.error("Tesseract OCR not found")
        with st.expander("Installation Instructions", expanded=True):
            st.markdown("""
            **Windows:**
            - Download from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki)
            - Install to default location
            
            **Linux:**
            ```bash
            sudo apt update && sudo apt install tesseract-ocr
            ```
            
            **macOS:**
            ```bash
            brew install tesseract
            ```
            """)
        return
    
    # Main upload card
    with st.container():
        st.markdown('<div class="upload-card">', unsafe_allow_html=True)
        
        st.subheader("Upload PDF")
        uploaded_file = st.file_uploader(
            "Choose a PDF file",
            type="pdf",
            label_visibility="collapsed"
        )
        
        if uploaded_file:
            st.success(f"**{uploaded_file.name}** ready for processing")
            
            # Settings
            with st.expander("Processing Settings"):
                col1, col2 = st.columns(2)
                with col1:
                    quality = st.selectbox("Quality", ["Standard", "High", "Maximum"], index=0)
                    dpi_scale = {"Standard": 2, "High": 3, "Maximum": 4}[quality]
                with col2:
                    languages = st.multiselect(
                        "Languages",
                        ["eng", "deu", "fra", "spa"],
                        default=["eng"]
                    )
            
            # Process button
            if st.button("Extract Text", type="primary"):
                with st.spinner("Processing PDF..."):
                    # Save uploaded file
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_path = tmp_file.name
                    
                    try:
                        start_time = time.time()
                        extracted_text, error = parse_pdf_to_text(tmp_path, dpi_scale, languages)
                        processing_time = time.time() - start_time
                        
                        os.unlink(tmp_path)
                        
                        if error:
                            st.error(f"Extraction failed: {error}")
                        else:
                            st.session_state.extracted_text = extracted_text
                            st.session_state.processing_time = processing_time
                            st.session_state.filename = uploaded_file.name
                            
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
        
        else:
            # Empty state
            st.markdown("""
            <div class="upload-area">
                <div style='font-size: 3rem; margin-bottom: 1rem;'>📁</div>
                <h3 style='color: #374151; margin-bottom: 0.5rem;'>Drag & Drop PDF Here</h3>
                <p style='color: #6b7280;'>or click to browse files</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Results section
    if 'extracted_text' in st.session_state:
        st.markdown("---")
        
        # Metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Processing Time", f"{st.session_state.processing_time:.1f}s")
        with col2:
            page_count = len([p for p in st.session_state.extracted_text.split('--- Page')]) - 1
            st.metric("Pages", page_count)
        with col3:
            st.metric("Characters", len(st.session_state.extracted_text))
        
        # Text output
        st.subheader("Extracted Text")
        
        tab1, tab2 = st.tabs(["Preview", "Full Text"])
        
        with tab1:
            preview = st.session_state.extracted_text[:1000]
            if len(st.session_state.extracted_text) > 1000:
                preview += "..."
            st.text_area("Preview", preview, height=200, label_visibility="collapsed")
        
        with tab2:
            st.text_area("Full Text", st.session_state.extracted_text, height=400, label_visibility="collapsed")
        
        # Actions
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "Download Text",
                st.session_state.extracted_text,
                file_name=f"{Path(st.session_state.filename).stem}.txt",
                use_container_width=True
            )
        with col2:
            if st.button("New File", use_container_width=True):
                for key in ['extracted_text', 'processing_time', 'filename']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()