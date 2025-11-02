"""
Universal Document Parser
Supports PDFs, Images (JPG, PNG, TIFF), Text files (TXT, DOCX)
Extracts text and metadata from multiple document formats
"""

import os
import io
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
import logging

# PDF and Image processing
import fitz  # PyMuPDF
from PIL import Image
import pytesseract

# Document processing
try:
    import docx
except ImportError:
    docx = None

# Metadata extraction
try:
    import exifread
except ImportError:
    exifread = None

from parse_pdf_ocr import parse_pdf_to_text

logger = logging.getLogger(__name__)


class UniversalDocumentParser:
    """
    Parse multiple document formats with text and metadata extraction
    """
    
    def __init__(self, dpi_scale: int = 3):
        """
        Initialize parser
        
        Args:
            dpi_scale: DPI scale for OCR (default 3 = 216 DPI)
        """
        self.dpi_scale = dpi_scale
        self.supported_formats = {
            'pdf': ['.pdf'],
            'image': ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp'],
            'text': ['.txt'],
            'document': ['.docx', '.doc']
        }
        
        logger.info(f"UniversalDocumentParser initialized (DPI: {72 * dpi_scale})")
    
    def parse_document(self, file_path: str) -> Dict[str, Any]:
        """
        Parse any supported document format
        
        Args:
            file_path: Path to document
        
        Returns:
            Dict containing:
                - text: extracted text
                - metadata: document metadata
                - format: document format
                - file_info: file information
                - images: list of images found (for PDFs)
                - success: boolean
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")
        
        # Determine file type
        file_ext = file_path.suffix.lower()
        doc_type = self._get_document_type(file_ext)
        
        logger.info(f"Parsing document: {file_path.name} (type: {doc_type})")
        
        # Route to appropriate parser
        if doc_type == 'pdf':
            return self._parse_pdf(str(file_path))
        elif doc_type == 'image':
            return self._parse_image(str(file_path))
        elif doc_type == 'text':
            return self._parse_text(str(file_path))
        elif doc_type == 'document':
            return self._parse_docx(str(file_path))
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
    
    def _get_document_type(self, file_ext: str) -> str:
        """Determine document type from extension"""
        for doc_type, extensions in self.supported_formats.items():
            if file_ext in extensions:
                return doc_type
        return 'unknown'
    
    def _parse_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """Parse PDF with OCR and extract metadata"""
        # Use existing parse_pdf_to_text for text extraction
        extracted_text = parse_pdf_to_text(pdf_path, output_path=None, dpi_scale=self.dpi_scale)
        
        # Get PDF metadata and structure
        pdf_doc = fitz.open(pdf_path)
        
        # Check if PDF contains images (scanned document)
        is_scanned = self._is_scanned_pdf(pdf_doc)
        
        result = {
            'success': True,
            'format': 'pdf',
            'text': extracted_text,
            'metadata': {
                'pdf_metadata': dict(pdf_doc.metadata),
                'page_count': len(pdf_doc),
                'is_scanned': is_scanned,
                'file_size': Path(pdf_path).stat().st_size,
                'created': datetime.fromtimestamp(Path(pdf_path).stat().st_ctime).isoformat(),
                'modified': datetime.fromtimestamp(Path(pdf_path).stat().st_mtime).isoformat()
            },
            'file_info': {
                'name': Path(pdf_path).name,
                'size': Path(pdf_path).stat().st_size,
                'path': pdf_path
            },
            'images': [],
            'parser_used': f'pytesseract_ocr (DPI:{72 * self.dpi_scale})',
            'is_image_document': is_scanned
        }
        
        # Extract images information
        for page_num in range(len(pdf_doc)):
            page = pdf_doc[page_num]
            image_list = page.get_images()
            
            for img_index, img_info in enumerate(image_list):
                xref = img_info[0]
                try:
                    base_image = pdf_doc.extract_image(xref)
                    if base_image:
                        result['images'].append({
                            'page': page_num + 1,
                            'index': img_index,
                            'format': base_image['ext'],
                            'width': base_image.get('width', 0),
                            'height': base_image.get('height', 0),
                            'size_bytes': len(base_image['image']),
                            'colorspace': base_image.get('colorspace', 'unknown'),
                            'xref': xref
                        })
                except Exception as e:
                    logger.warning(f"Failed to extract image {img_index} from page {page_num + 1}: {e}")
        
        pdf_doc.close()
        
        logger.info(f"PDF parsed: {len(extracted_text)} chars, {result['metadata']['page_count']} pages, {len(result['images'])} images")
        
        return result
    
    def _is_scanned_pdf(self, pdf_doc) -> bool:
        """Check if PDF is primarily scanned images"""
        if len(pdf_doc) == 0:
            return False
        
        # Sample first few pages
        pages_to_check = min(3, len(pdf_doc))
        image_heavy_count = 0
        
        for page_num in range(pages_to_check):
            page = pdf_doc[page_num]
            # Check if page has images
            image_list = page.get_images()
            # Check text content
            text = page.get_text()
            
            # If has images and very little text, likely scanned
            if len(image_list) > 0 and len(text.strip()) < 100:
                image_heavy_count += 1
        
        return image_heavy_count >= (pages_to_check * 0.5)
    
    def _parse_image(self, image_path: str) -> Dict[str, Any]:
        """Parse image with OCR and extract EXIF metadata"""
        # Open image
        image = Image.open(image_path)
        
        # Extract EXIF metadata if available
        exif_data = {}
        if exifread:
            with open(image_path, 'rb') as f:
                tags = exifread.process_file(f, details=True)
                exif_data = {str(tag): str(value) for tag, value in tags.items()}
        
        # Get PIL metadata
        pil_info = {
            'format': image.format,
            'mode': image.mode,
            'size': image.size,
            'width': image.width,
            'height': image.height
        }
        
        # Extract any PIL EXIF
        try:
            exif = image.getexif()
            if exif:
                pil_info['exif_tags'] = {k: str(v) for k, v in exif.items()}
        except:
            pass
        
        # Perform OCR
        logger.info(f"Running OCR on image: {Path(image_path).name}")
        try:
            text = pytesseract.image_to_string(image, lang='deu+fra+eng')
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            text = ""
        
        result = {
            'success': True,
            'format': 'image',
            'text': text,
            'metadata': {
                'exif': exif_data,
                'image_info': pil_info,
                'file_size': Path(image_path).stat().st_size,
                'created': datetime.fromtimestamp(Path(image_path).stat().st_ctime).isoformat(),
                'modified': datetime.fromtimestamp(Path(image_path).stat().st_mtime).isoformat()
            },
            'file_info': {
                'name': Path(image_path).name,
                'size': Path(image_path).stat().st_size,
                'path': image_path
            },
            'parser_used': 'pytesseract_ocr',
            'is_image_document': True
        }
        
        logger.info(f"Image parsed: {len(text)} chars extracted, {len(exif_data)} EXIF tags")
        
        return result
    
    def _parse_text(self, text_path: str) -> Dict[str, Any]:
        """Parse plain text file"""
        with open(text_path, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
        
        result = {
            'success': True,
            'format': 'text',
            'text': text,
            'metadata': {
                'file_size': Path(text_path).stat().st_size,
                'line_count': len(text.split('\n')),
                'word_count': len(text.split()),
                'char_count': len(text),
                'created': datetime.fromtimestamp(Path(text_path).stat().st_ctime).isoformat(),
                'modified': datetime.fromtimestamp(Path(text_path).stat().st_mtime).isoformat()
            },
            'file_info': {
                'name': Path(text_path).name,
                'size': Path(text_path).stat().st_size,
                'path': text_path
            },
            'parser_used': 'text_reader',
            'is_image_document': False
        }
        
        logger.info(f"Text file parsed: {len(text)} chars, {result['metadata']['line_count']} lines")
        
        return result
    
    def _parse_docx(self, docx_path: str) -> Dict[str, Any]:
        """Parse DOCX file"""
        if not docx:
            raise ImportError("python-docx not installed. Install with: pip install python-docx")
        
        doc = docx.Document(docx_path)
        
        # Extract text from paragraphs
        paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
        text = '\n\n'.join(paragraphs)
        
        # Extract document properties
        core_props = doc.core_properties
        properties = {
            'author': core_props.author,
            'created': core_props.created.isoformat() if core_props.created else None,
            'modified': core_props.modified.isoformat() if core_props.modified else None,
            'title': core_props.title,
            'subject': core_props.subject,
            'keywords': core_props.keywords,
            'category': core_props.category,
            'comments': core_props.comments
        }
        
        result = {
            'success': True,
            'format': 'docx',
            'text': text,
            'metadata': {
                'document_properties': properties,
                'paragraph_count': len(paragraphs),
                'file_size': Path(docx_path).stat().st_size,
                'created': datetime.fromtimestamp(Path(docx_path).stat().st_ctime).isoformat(),
                'modified': datetime.fromtimestamp(Path(docx_path).stat().st_mtime).isoformat()
            },
            'file_info': {
                'name': Path(docx_path).name,
                'size': Path(docx_path).stat().st_size,
                'path': docx_path
            },
            'parser_used': 'python-docx',
            'is_image_document': False
        }
        
        logger.info(f"DOCX parsed: {len(text)} chars, {len(paragraphs)} paragraphs")
        
        return result


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python universal_document_parser.py <file_path>")
        sys.exit(1)
    
    logging.basicConfig(level=logging.INFO)
    
    parser = UniversalDocumentParser()
    result = parser.parse_document(sys.argv[1])
    
    print("\n" + "="*80)
    print("PARSING RESULTS")
    print("="*80)
    print(f"\nFormat: {result['format']}")
    print(f"Text extracted: {len(result['text'])} characters")
    print(f"\nMetadata:")
    print(json.dumps(result['metadata'], indent=2))
    print(f"\nFirst 500 chars of text:")
    print("-"*80)
    print(result['text'][:500])

