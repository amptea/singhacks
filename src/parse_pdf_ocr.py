"""
PDF OCR Parser with Auto-Detection of Tesseract
Extracts text from scanned PDF documents using OCR
"""

import os
import sys
from pathlib import Path

# Try to configure Tesseract path for Windows
import pytesseract

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
        print(f"Found Tesseract at: {path}\n")
        break

if not tesseract_found:
    print("WARNING: Tesseract not found in common locations.")
    print("If you have Tesseract installed, please set the path manually.\n")

import fitz  # PyMuPDF
from PIL import Image
import io

def parse_pdf_to_text(pdf_path, output_path=None, dpi_scale=3):
    """
    Parse a scanned PDF and extract text using OCR
    
    Args:
        pdf_path: Path to the PDF file
        output_path: Optional path to save the extracted text
        dpi_scale: Scale factor for image resolution (default 2 = 144 DPI)
    
    Returns:
        Extracted text as a string
    """
    print(f"Opening PDF: {pdf_path}")
    
    # Open the PDF
    pdf_document = fitz.open(pdf_path)
    
    all_text = []
    total_pages = len(pdf_document)
    
    print(f"Processing {total_pages} page(s)...")
    print(f"Using DPI scale: {dpi_scale} (effective DPI: {72 * dpi_scale})\n")
    
    for page_num in range(total_pages):
        print(f"Processing page {page_num + 1}/{total_pages}...")
        
        try:
            # Get the page
            page = pdf_document[page_num]
            
            # Convert page to image (higher DPI for better OCR)
            mat = fitz.Matrix(dpi_scale, dpi_scale)
            pix = page.get_pixmap(matrix=mat)
            
            # Convert to PIL Image
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            # Perform OCR on the image
            print(f"  Running OCR on page {page_num + 1}...")
            text = pytesseract.image_to_string(img, lang='deu+fra+eng')
            
            # Add page header
            all_text.append(f"\n{'='*80}\n")
            all_text.append(f"PAGE {page_num + 1}\n")
            all_text.append(f"{'='*80}\n\n")
            all_text.append(text)
            
            print(f"  Extracted {len(text)} characters from page {page_num + 1}")
            
        except Exception as e:
            print(f"  ERROR processing page {page_num + 1}: {e}")
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
        print(f"\nText saved to: {output_path}")
    
    return full_text

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python pdf_ocr.py <pdf_path> [output_path]")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        print("="*80)
        print("PDF OCR EXTRACTION")
        print("="*80)
        print()
        
        extracted_text = parse_pdf_to_text(pdf_path, output_path, dpi_scale=2)
        
        print("\n" + "="*80)
        print("EXTRACTION COMPLETE")
        print("="*80)
        print(f"\nTotal characters extracted: {len(extracted_text)}")
        
        if len(extracted_text.strip()) > 100:
            print(f"\nFirst 500 characters of extracted text:\n")
            print("-" * 80)
            print(extracted_text[:500])
            print("-" * 80)
            
    except pytesseract.TesseractNotFoundError:
        print("\n" + "="*80)
        print("TESSERACT NOT FOUND")
        print("="*80)
        print("\nTesseract OCR is not installed or not found in your PATH.")
        print("\nTo install Tesseract on Windows:")
        print("  1. Download from: https://github.com/UB-Mannheim/tesseract/wiki")
        print("  2. Run the installer (tesseract-ocr-w64-setup-*.exe)")
        print("  3. Install to default location or note the custom path")
        print("  4. Rerun this script")
        print("\nAlternatively, you can manually set the path in this script:")
        print("  pytesseract.pytesseract.tesseract_cmd = r'C:\\Path\\To\\tesseract.exe'")
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
