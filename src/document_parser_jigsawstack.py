"""
Document Parser using JigsawStack OCR
Supports PDF, images (JPG, PNG, JPEG), and text files
"""

import os
import base64
from pathlib import Path
from typing import Dict, Any, Optional
from jigsawstack import JigsawStack
from dotenv import load_dotenv
import fitz  # PyMuPDF for metadata


class JigsawDocumentParser:
    """
    Parse documents using JigsawStack OCR - supports PDFs, images, and text files
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize JigsawStack parser
        
        Args:
            api_key: JigsawStack API key (or use JIGSAWSTACK_API_KEY env variable)
        """
        load_dotenv()
        self.api_key = api_key or os.environ.get("JIGSAWSTACK_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "JigsawStack API key required!\n"
                "Get your key at: https://jigsawstack.com\n"
                "Set as: export JIGSAWSTACK_API_KEY='your-key'"
            )
        
        self.client = JigsawStack(api_key=self.api_key)
        print("✓ JigsawStack Document Parser initialized")
    
    def parse_document(self, file_path: str) -> Dict[str, Any]:
        """
        Parse document (PDF, image, or text) using JigsawStack OCR
        
        Args:
            file_path: Path to document
        
        Returns:
            Parsed document data with text and metadata
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Determine file type
        file_ext = file_path.suffix.lower()
        supported_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.txt']
        
        if file_ext not in supported_extensions:
            raise ValueError(
                f"Unsupported file type: {file_ext}\n"
                f"Supported: {', '.join(supported_extensions)}"
            )
        
        print(f"\n[Parser] Processing {file_ext} file...")
        
        # Parse based on file type
        if file_ext == '.txt':
            return self._parse_text_file(str(file_path))
        else:
            # Use JigsawStack for PDF and images
            return self._parse_with_jigsawstack(str(file_path))
    
    def _parse_text_file(self, file_path: str) -> Dict[str, Any]:
        """Parse plain text file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        return {
            'file_path': file_path,
            'file_name': Path(file_path).name,
            'file_type': 'text',
            'file_size': Path(file_path).stat().st_size,
            'text': text,
            'page_count': 1,
            'metadata': {},
            'images': [],
            'fonts': [],
            'success': True
        }
    
    def _parse_with_jigsawstack(self, file_path: str) -> Dict[str, Any]:
        """Parse PDF or image using JigsawStack OCR"""
        
        try:
            print(f"[JigsawStack] Reading file: {Path(file_path).name}")
            
            # Read and encode file to base64 data URI
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # Get file extension and MIME type
            file_ext = Path(file_path).suffix.lower()
            mime_types = {
                '.pdf': 'application/pdf',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png'
            }
            mime_type = mime_types.get(file_ext, 'application/octet-stream')
            
            # Create base64 data URI
            base64_data = base64.b64encode(file_data).decode('utf-8')
            data_uri = f"data:{mime_type};base64,{base64_data}"
            
            print(f"[JigsawStack] Encoded file as data URI ({len(base64_data)} chars)")
            
            # Get page count for PDFs to handle page_range
            total_pages = 1
            if file_ext == '.pdf':
                try:
                    pdf_doc = fitz.open(file_path)
                    total_pages = len(pdf_doc)
                    pdf_doc.close()
                    print(f"[JigsawStack] PDF has {total_pages} page(s)")
                except:
                    pass
            
            print(f"[JigsawStack] Running OCR with AI extraction...")
            
            # Build vOCR request using URL (data URI approach from official docs)
            vocr_params = {
                "url": data_uri,  # Use data URI as URL (official method)
                "prompt": ["Extracted Text"]  # Guide the OCR to extract all text
            }
            
            # Add page_range for multi-page PDFs (max 10 pages per API limit)
            pages_processed = total_pages
            if total_pages > 1:
                # Process up to 10 pages at a time (API limit)
                end_page = min(total_pages, 10)
                pages_processed = end_page
                vocr_params["page_range"] = [1, end_page]
                print(f"[JigsawStack] Processing pages 1-{end_page}")
                
                if total_pages > 10:
                    print(f"[JigsawStack] ⚠️  WARNING: Document has {total_pages} pages, but JigsawStack vOCR limit is 10 pages per call")
                    print(f"[JigsawStack] Only processing first 10 pages")
            
            # Call JigsawStack vOCR API (matches official docs pattern)
            result = self.client.vision.vocr(vocr_params)
            
            print(f"[JigsawStack] OCR complete!")
            
            # Debug: Print the result structure
            print(f"[JigsawStack] Result type: {type(result)}")
            print(f"[JigsawStack] Result keys: {result.keys() if isinstance(result, dict) else 'N/A'}")
            
            # Extract text from OCR result
            # JigsawStack vocr returns: {"context": {"Extracted Text": [text_content]}, ...}
            extracted_text = ""
            
            if isinstance(result, dict):
                # Primary method: Check context["Extracted Text"]
                context = result.get('context', {})
                if isinstance(context, dict) and 'Extracted Text' in context:
                    extracted_content = context['Extracted Text']
                    if isinstance(extracted_content, list):
                        extracted_text = '\n'.join(str(item) for item in extracted_content)
                    else:
                        extracted_text = str(extracted_content)
                    print(f"[JigsawStack] Extracted from context['Extracted Text']")
                
                # Fallback methods
                if not extracted_text:
                    extracted_text = (
                        result.get('text', '') or 
                        result.get('content', '') or
                        result.get('data', {}).get('text', '') or
                        result.get('result', {}).get('text', '')
                    )
                
                # Check for pages structure
                if not extracted_text and 'pages' in result:
                    pages_text = []
                    for page in result['pages']:
                        if isinstance(page, dict):
                            pages_text.append(page.get('text', ''))
                        elif isinstance(page, str):
                            pages_text.append(page)
                    extracted_text = '\n'.join(pages_text)
                
                # If still nothing, log the full result for debugging
                if not extracted_text:
                    print(f"[JigsawStack] WARNING: Could not find text in standard fields")
                    print(f"[JigsawStack] Full result structure:")
                    import json
                    print(json.dumps(result, indent=2, default=str))
            else:
                extracted_text = str(result)
            
            print(f"[JigsawStack] Extracted text length: {len(extracted_text)}")
            
            # Get additional metadata if PDF (we already opened it earlier for page count)
            metadata = {}
            if file_ext == '.pdf':
                try:
                    pdf_doc = fitz.open(file_path)
                    metadata = dict(pdf_doc.metadata)
                    pdf_doc.close()
                except:
                    pass
            
            result_data = {
                'file_path': file_path,
                'file_name': Path(file_path).name,
                'file_type': Path(file_path).suffix[1:],
                'file_size': Path(file_path).stat().st_size,
                'text': extracted_text,
                'page_count': total_pages,
                'pages_processed': pages_processed,  # May be less than page_count due to 10-page limit
                'metadata': metadata,
                'images': result.get('images', []) if isinstance(result, dict) else [],
                'fonts': result.get('fonts', []) if isinstance(result, dict) else [],
                'ocr_result': result if isinstance(result, dict) else {'text': result},
                'success': True,
                'parser_used': 'jigsawstack'
            }
            
            # Add warning if not all pages were processed
            if pages_processed < total_pages:
                result_data['warning'] = f"Only {pages_processed} of {total_pages} pages were processed (JigsawStack vOCR limit is 10 pages)"
            
            return result_data
            
        except Exception as e:
            print(f"[JigsawStack] OCR error: {e}")
            print(f"[JigsawStack] Falling back to PyMuPDF...")
            # Fallback to basic extraction
            return self._fallback_parse(file_path)
    
    def _fallback_parse(self, file_path: str) -> Dict[str, Any]:
        """Fallback parser if JigsawStack fails"""
        
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext == '.pdf':
            # Use PyMuPDF as fallback
            try:
                print(f"[PyMuPDF] Extracting text from PDF...")
                pdf_doc = fitz.open(file_path)
                text = ""
                for page in pdf_doc:
                    text += page.get_text()
                
                print(f"[PyMuPDF] Extracted {len(text)} characters")
                
                return {
                    'file_path': file_path,
                    'file_name': Path(file_path).name,
                    'file_type': 'pdf',
                    'file_size': Path(file_path).stat().st_size,
                    'text': text,
                    'page_count': len(pdf_doc),
                    'metadata': dict(pdf_doc.metadata),
                    'images': [],
                    'fonts': [],
                    'success': True,
                    'parser_used': 'pymupdf_fallback',
                    'fallback': True
                }
            except Exception as e:
                print(f"[PyMuPDF] Error: {e}")
                return {'success': False, 'error': str(e)}
        elif file_ext in ['.jpg', '.jpeg', '.png']:
            # For images, we need OCR - inform user
            return {
                'success': False, 
                'error': 'Image OCR failed. JigsawStack API error. Please check your API key and connection.'
            }
        
        return {'success': False, 'error': 'Unable to parse document'}


if __name__ == "__main__":
    parser = JigsawDocumentParser()
    
    # Test with different file types
    test_files = [
        "data/docs/Swiss_Home_Purchase_Agreement_Scanned_Noise_forparticipants.pdf",
        # Add your test files here
    ]
    
    for file_path in test_files:
        if Path(file_path).exists():
            result = parser.parse_document(file_path)
            print(f"\n✓ Parsed: {result['file_name']}")
            print(f"  Text length: {len(result['text'])} characters")
            print(f"  Pages: {result['page_count']}")

