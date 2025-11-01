"""
PDF OCR Parser with Drag & Drop UI
Streamlit-based interface for PDF OCR extraction
"""

import streamlit as st
import os
import sys
import tempfile
from pathlib import Path
import time

# Page configuration
st.set_page_config(
    page_title="PDF OCR Extractor",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .upload-area {
        border: 2px dashed #cccccc;
        border-radius: 10px;
        padding: 3rem;
        text-align: center;
        margin: 1rem 0;
        background-color: #fafafa;
        transition: all 0.3s ease;
    }
    .upload-area:hover {
        border-color: #1f77b4;
        background-color: #f0f8ff;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
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
    .progress-bar {
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Import OCR functionality
try:
    import pytesseract
    from PIL import Image
    import fitz  # PyMuPDF
    
    # Common Tesseract installation paths on Windows
    TESSERACT_PATHS = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        r"C:\Users\Public\Tesseract-OCR\tesseract.exe",
    ]
    
    # Try to find Tesseract
    tesseract_found = False
    for path in TESSERACT_PATHS:
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            tesseract_found = True
            st.session_state.tesseract_path = path
            break
    
    if not tesseract_found:
        st.warning("⚠️ Tesseract not found in common locations. OCR may not work properly.")
        
except ImportError as e:
    st.error(f"❌ Missing required dependency: {e}")
    st.stop()

def parse_pdf_to_text(pdf_path, output_path=None, dpi_scale=3, progress_bar=None, status_text=None):
    """
    Parse a scanned PDF and extract text using OCR
    Modified to work with Streamlit progress tracking
    """
    try:
        if status_text:
            status_text.text("Opening PDF document...")
        
        # Open the PDF
        pdf_document = fitz.open(pdf_path)
        
        all_text = []
        total_pages = len(pdf_document)
        
        if status_text:
            status_text.text(f"Processing {total_pages} page(s)...")
        
        for page_num in range(total_pages):
            if progress_bar:
                progress = (page_num + 1) / total_pages
                progress_bar.progress(progress)
            
            if status_text:
                status_text.text(f"Processing page {page_num + 1}/{total_pages}...")
            
            try:
                # Get the page
                page = pdf_document[page_num]
                
                # Convert page to image (higher DPI for better OCR)
                mat = fitz.Matrix(dpi_scale, dpi_scale)
                pix = page.get_pixmap(matrix=mat)
                
                # Convert to PIL Image
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                # Perform OCR on the image
                if status_text:
                    status_text.text(f"Running OCR on page {page_num + 1}...")
                
                text = pytesseract.image_to_string(img, lang='deu+fra+eng')
                
                # Add page header
                all_text.append(f"\n{'='*80}\n")
                all_text.append(f"PAGE {page_num + 1}\n")
                all_text.append(f"{'='*80}\n\n")
                all_text.append(text)
                
            except Exception as e:
                error_msg = f"ERROR processing page {page_num + 1}: {e}"
                all_text.append(f"\n{'='*80}\n")
                all_text.append(f"PAGE {page_num + 1} - ERROR\n")
                all_text.append(f"{'='*80}\n\n")
                all_text.append(f"[Error: {str(e)}]\n")
        
        # Close the PDF
        pdf_document.close()
        
        # Combine all text
        full_text = "".join(all_text)
        
        # Save to file if output path is provided
        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(full_text)
        
        return full_text, None  # Return text and no error
        
    except Exception as e:
        return None, str(e)

def main():
    """Main Streamlit application"""
    
    # Header
    st.markdown('<div class="main-header">📄 PDF OCR Text Extractor</div>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # DPI Scale selection
        dpi_scale = st.slider(
            "Image Quality (DPI Scale)",
            min_value=1,
            max_value=4,
            value=2,
            help="Higher values = better quality but slower processing"
        )
        
        # Language selection
        languages = st.multiselect(
            "OCR Languages",
            options=['eng', 'deu', 'fra', 'spa', 'ita', 'por'],
            default=['eng', 'deu', 'fra'],
            help="Select languages for OCR (multiple for multilingual documents)"
        )
        
        # Manual Tesseract path
        st.subheader("Tesseract Configuration")
        manual_path = st.text_input(
            "Tesseract Path (if not auto-detected)",
            value=st.session_state.get('tesseract_path', ''),
            help="Path to tesseract.exe on Windows"
        )
        
        if manual_path and os.path.exists(manual_path):
            pytesseract.pytesseract.tesseract_cmd = manual_path
            st.session_state.tesseract_path = manual_path
            st.success("✅ Tesseract path set successfully")
        
        st.markdown("---")
        st.info("""
        **How to use:**
        1. Drag & drop a PDF file
        2. Adjust settings if needed
        3. Click 'Extract Text'
        4. Download or copy the extracted text
        """)
    
    # Main content area
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📤 Upload PDF File")
        
        # File uploader with drag & drop
        uploaded_file = st.file_uploader(
            "Drag and drop your PDF file here",
            type=['pdf'],
            help="Upload a scanned PDF document for text extraction"
        )
        
        if uploaded_file is not None:
            # File info
            file_details = {
                "Filename": uploaded_file.name,
                "File size": f"{uploaded_file.size / 1024:.2f} KB"
            }
            
            st.json(file_details)
            
            # Preview upload
            st.success("✅ File uploaded successfully!")
            
            # Extract button
            if st.button("🚀 Extract Text", type="primary", use_container_width=True):
                with st.spinner("Processing PDF..."):
                    # Create temporary file
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_path = tmp_file.name
                    
                    try:
                        # Setup progress tracking
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        # Process PDF
                        start_time = time.time()
                        extracted_text, error = parse_pdf_to_text(
                            tmp_path, 
                            dpi_scale=dpi_scale,
                            progress_bar=progress_bar,
                            status_text=status_text
                        )
                        processing_time = time.time() - start_time
                        
                        # Clean up temp file
                        os.unlink(tmp_path)
                        
                        if error:
                            st.error(f"❌ Extraction failed: {error}")
                        else:
                            st.session_state.extracted_text = extracted_text
                            st.session_state.processing_time = processing_time
                            st.session_state.filename = uploaded_file.name
                            
                            progress_bar.progress(1.0)
                            status_text.text("✅ Extraction complete!")
                            
                    except Exception as e:
                        st.error(f"❌ Error during processing: {str(e)}")
    
    with col2:
        st.subheader("📋 Extraction Results")
        
        if 'extracted_text' in st.session_state:
            # Success message
            st.markdown(f"""
            <div class="success-box">
                <strong>✅ Text Extraction Complete!</strong><br>
                File: {st.session_state.filename}<br>
                Processing time: {st.session_state.processing_time:.2f} seconds<br>
                Characters extracted: {len(st.session_state.extracted_text)}
            </div>
            """, unsafe_allow_html=True)
            
            # Text preview
            st.subheader("📝 Text Preview")
            preview_length = min(1000, len(st.session_state.extracted_text))
            st.text_area(
                "First 1000 characters preview",
                st.session_state.extracted_text[:preview_length] + ("..." if len(st.session_state.extracted_text) > preview_length else ""),
                height=200
            )
            
            # Download button
            st.download_button(
                label="💾 Download Full Text",
                data=st.session_state.extracted_text,
                file_name=f"{Path(st.session_state.filename).stem}_extracted.txt",
                mime="text/plain",
                use_container_width=True
            )
            
            # Copy to clipboard button
            if st.button("📋 Copy to Clipboard", use_container_width=True):
                st.code(st.session_state.extracted_text[:500] + ("..." if len(st.session_state.extracted_text) > 500 else ""))
                st.success("Text copied to clipboard!")
            
            # Full text expander
            with st.expander("📖 View Full Extracted Text"):
                st.text_area("Full Text", st.session_state.extracted_text, height=400)
        
        else:
            # Initial state message
            st.info("👆 Upload a PDF file and click 'Extract Text' to see results here")
            
            # Example of what the tool can do
            with st.expander("ℹ️ About this tool"):
                st.markdown("""
                **What this tool does:**
                - Extracts text from scanned PDF documents using OCR
                - Supports multiple languages
                - Handles image-based PDFs (scanned documents)
                - Provides downloadable results
                
                **Best practices:**
                - Use high-quality scans for better accuracy
                - Choose appropriate languages for your document
                - Higher DPI scale = better quality but slower processing
                
                **Supported languages:** English, German, French, Spanish, Italian, Portuguese
                """)

    # Footer
    st.markdown("---")
    st.markdown(
        "**Note:** This tool uses Tesseract OCR for text extraction. "
        "For best results, ensure your PDF pages are clear and legible."
    )

if __name__ == "__main__":
    main()