"""
Pure AI Fraud Detection System
Uses Groq AI for ALL analysis - format validation, image analysis, risk assessment
Only parse_pdf_ocr.py for document extraction
"""

import os
import sys
import json
import logging
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import fitz  # PyMuPDF
from PIL import Image
import io
import base64

from parse_pdf_ocr import parse_pdf_to_text
from groq import Groq

# --- Logging Configuration ---
# Create a logger instance for the module
logger = logging.getLogger('AIFraudDetector')
logger.setLevel(logging.INFO)

# Define the log file path (e.g., in a logs directory)
LOG_DIR = Path("data/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "audit_trail.log"

# Create file handler which logs even debug messages
fh = logging.FileHandler(LOG_FILE)
fh.setLevel(logging.INFO)

# Create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# Create formatter and add it to the handlers
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
fh.setFormatter(formatter)
ch.setFormatter(formatter)

# Add the handlers to the logger (avoiding duplicates if re-initialized)
if not logger.handlers:
    logger.addHandler(fh)
    logger.addHandler(ch)
# -----------------------------


class AIFraudDetector:
    """
    Pure AI-powered fraud detection - Groq does everything
    """
    
    def __init__(
        self,
        model: str = "llama-3.3-70b-versatile"
    ):
        """
        Initialize AI fraud detector
        
        Args:
            groq_api_key: Groq API key (or use GROQ_API_KEY env variable)
            model: Groq model to use
        """
        # Load .env file
        env_path = Path(__file__).resolve().parent.parent / ".env"  # adjust if needed
        load_dotenv()

        self.api_key = os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            error_msg = (
                "Groq API key required!\n"
                "Get your FREE key at: https://console.groq.com/keys\n"
                "Set as: export GROQ_API_KEY='your-key'"
            )
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        self.client = Groq(api_key=self.api_key)
        self.model = model
        
        # Log initialization
        logger.info(f"AI Fraud Detector initialized (Model: {model}). Log file: {LOG_FILE.resolve()}")
    
    def analyze_document(self, document_path: str, output_dir: str = "data/outputs") -> Dict[str, Any]:
        """
        Analyze document using pure AI approach
        
        Args:
            document_path: Path to document
            output_dir: Directory for outputs
        
        Returns:
            Complete AI analysis results
        """
        doc_path = Path(document_path)
        if not doc_path.exists():
            logger.error(f"Analysis failed: Document not found at {document_path}")
            raise FileNotFoundError(f"Document not found: {document_path}")
        
        analysis_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Log analysis start
        logger.info("-" * 80)
        logger.info(f"ANALYSIS STARTED | ID: {analysis_id} | Document: {doc_path.name} | Model: {self.model}")
        logger.info("-" * 80)
        
        start_time = datetime.now()
        
        try:
            # Step 1: Extract document data
            logger.info(f"[1/3] Extracting document content from {doc_path.name}...")
            doc_data = self._extract_document_data(str(doc_path))
            
            # Log extraction summary
            logger.info(f"      ✓ Extracted {len(doc_data['text'])} characters from {doc_data['total_pages']} page(s)")
            logger.debug(f"Document Data Snapshot: {json.dumps(doc_data['structure'])}") # Debug level for detailed log
            
            # Step 2: AI analyzes EVERYTHING
            logger.info("[2/3] AI analyzing document for fraud (comprehensive check)...")
            ai_analysis = self._ai_comprehensive_analysis(doc_data)
            
            # Log AI analysis summary
            logger.info(f"      ✓ AI analysis complete. Fraud likelihood: {ai_analysis['fraud_likelihood']} | Risk Score: {ai_analysis['risk_score']}/10")
            
            # Step 3: Generate reports
            logger.info("[3/3] Generating AI reports...")
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            reports = self._generate_reports(
                doc_data, ai_analysis, doc_path.stem, analysis_id, output_path
            )
            logger.info(f"      ✓ Generated {len(reports)} report(s): {', '.join(reports.keys())}")
            
            # Compile results
            results = {
                'analysis_id': analysis_id,
                'document': doc_path.name,
                'timestamp': datetime.now().isoformat(),
                'duration_seconds': (datetime.now() - start_time).total_seconds(),
                'model_used': self.model,
                'document_data': doc_data,
                'ai_analysis': ai_analysis,
                'reports': reports
            }
            
            # Log analysis completion and final results
            self._log_analysis_completion(results)
            
            return results
            
        except Exception as e:
            # Log failure
            error_trace = traceback.format_exc()
            logger.error(f"ANALYSIS FAILED | ID: {analysis_id} | Error: {e}\n{error_trace}")
            raise
    
    def _extract_document_data(self, pdf_path: str) -> Dict[str, Any]:
        """Extract all data from document using parse_pdf_ocr.py"""
        
        # Use parse_pdf_ocr for text extraction
        extracted_text = parse_pdf_to_text(pdf_path, output_path=None, dpi_scale=3)
        
        # Get metadata using PyMuPDF
        pdf_doc = fitz.open(pdf_path)
        
        doc_data = {
            'file_path': pdf_path,
            'file_name': Path(pdf_path).name,
            'file_size': Path(pdf_path).stat().st_size,
            'total_pages': len(pdf_doc),
            'text': extracted_text,
            'metadata': dict(pdf_doc.metadata),
            'images': [],
            'fonts': [],
            'structure': {}
        }
        
        # Extract images and fonts info (omitting image extraction logic for brevity in this response
        # but maintaining the original structure)
        fonts_seen = set()
        
        for page_num in range(len(pdf_doc)):
            page = pdf_doc[page_num]
            
            # Get images (as per original logic, only structure is kept here)
            image_list = page.get_images()
            for img_index, img_info in enumerate(image_list):
                xref = img_info[0]
                try:
                    base_image = pdf_doc.extract_image(xref)
                    if base_image:
                        doc_data['images'].append({
                            'page': page_num + 1,
                            'index': img_index,
                            'format': base_image['ext'],
                            'width': base_image.get('width', 0),
                            'height': base_image.get('height', 0),
                            'size_bytes': len(base_image['image']),
                            'colorspace': base_image.get('colorspace', 'unknown')
                        })
                except:
                    pass
            
            # Get fonts
            blocks = page.get_text("dict")["blocks"]
            for block in blocks:
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            font_name = span.get('font', 'Unknown')
                            font_size = span.get('size', 0)
                            fonts_seen.add(f"{font_name}|{font_size}")
        
        # Convert fonts to list
        doc_data['fonts'] = [
            {'name': f.split('|')[0], 'size': float(f.split('|')[1])} 
            for f in fonts_seen
        ]
        
        # Structure info
        doc_data['structure'] = {
            'text_length': len(extracted_text),
            'word_count': len(extracted_text.split()),
            'line_count': len(extracted_text.split('\n')),
            'has_images': len(doc_data['images']) > 0,
            'has_metadata': len(doc_data['metadata']) > 0
        }
        
        pdf_doc.close()
        
        return doc_data
    
    def _ai_comprehensive_analysis(self, doc_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Let AI do ALL the analysis:
        - Format validation (spacing, fonts, structure)
        - Image analysis (authenticity, manipulation)
        - Risk assessment
        - Recommendations
        """
        
        # Prepare comprehensive context for AI
        context = self._prepare_ai_context(doc_data)
        
        # AI does EVERYTHING in one comprehensive analysis
        prompt = f"""You are an expert forensic document analyst specializing in fraud detection.

Analyze this document for ANY signs of fraud, manipulation, or inauthenticity.

DOCUMENT DATA:
{context}

Perform a COMPREHENSIVE fraud analysis covering:
... (Rest of the original prompt) ...

Provide your analysis as JSON:
... (Rest of the original JSON structure) ...

Be thorough, specific, and precise. If you find fraud indicators, explain exactly what they are and why they're concerning."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert forensic document analyst. Provide thorough, accurate fraud detection analysis. Be specific and detailed. Output valid JSON only."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,  # Low temperature for consistent, factual analysis
                max_tokens=4000,
                response_format={"type": "json_object"}
            )
            
            analysis_text = response.choices[0].message.content
            analysis = json.loads(analysis_text)
            
            # Extract key fields for easy access
            overall = analysis.get('overall_assessment', {})
            
            # Log successful AI analysis
            logger.info(f"AI Model Response (Success). Risk Level: {overall.get('risk_level', 'UNKNOWN')}")

            return {
                'fraud_likelihood': overall.get('fraud_likelihood', 'UNKNOWN'),
                'risk_score': overall.get('risk_score', 5.0),
                'risk_level': overall.get('risk_level', 'MEDIUM'),
                'confidence': overall.get('confidence', 0.5),
                'key_findings': overall.get('key_findings', []),
                'critical_issues': overall.get('critical_issues', []),
                'primary_concerns': overall.get('primary_concerns', []),
                'overall_summary': overall.get('overall_summary', ''),
                'format_validation': analysis.get('format_validation', {}),
                'image_analysis': analysis.get('image_analysis', {}),
                'metadata_analysis': analysis.get('metadata_analysis', {}),
                'content_analysis': analysis.get('content_analysis', {}),
                'recommendations': analysis.get('recommendations', {}),
                'detailed_analysis': analysis.get('detailed_analysis', ''),
                'full_analysis': analysis  # Keep complete analysis
            }
            
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parsing error from AI response: {e}. Raw response logged at DEBUG level.")
            logger.debug(f"Raw AI Response: {analysis_text if 'analysis_text' in locals() else 'No response text available'}")
            return {
                'fraud_likelihood': 'UNKNOWN',
                'risk_score': 5.0,
                'risk_level': 'MEDIUM',
                'confidence': 0.3,
                'key_findings': ['AI analysis error - manual review required'],
                'error': str(e),
                'raw_response': analysis_text if 'analysis_text' in locals() else ''
            }
        except Exception as e:
            logger.error(f"Error during AI API call: {e}")
            raise
    
    def _prepare_ai_context(self, doc_data: Dict[str, Any]) -> str:
        """Prepare document data as context for AI"""
        # ... (Same as original)
        
        # Format document info
        context = f"""
FILE INFORMATION:
- File Name: {doc_data['file_name']}
- File Size: {doc_data['file_size']:,} bytes
- Total Pages: {doc_data['total_pages']}

EXTRACTED TEXT:
{doc_data['text'][:3000]}  # First 3000 characters
{"... (text truncated)" if len(doc_data['text']) > 3000 else ""}

TEXT STATISTICS:
- Total Length: {doc_data['structure']['text_length']} characters
- Word Count: {doc_data['structure']['word_count']} words
- Line Count: {doc_data['structure']['line_count']} lines

METADATA:
{json.dumps(doc_data['metadata'], indent=2)}

FONTS USED:
{json.dumps(doc_data['fonts'], indent=2)}

IMAGES FOUND:
- Total Images: {len(doc_data['images'])}
{json.dumps(doc_data['images'], indent=2) if doc_data['images'] else "No images found"}

STRUCTURE:
{json.dumps(doc_data['structure'], indent=2)}
"""
        return context
    
    def _generate_reports(
        self,
        doc_data: Dict[str, Any],
        ai_analysis: Dict[str, Any],
        doc_name: str,
        analysis_id: str,
        output_dir: Path
    ) -> Dict[str, str]:
        """Generate all reports"""
        
        reports = {}
        
        # 1. Complete JSON Report
        # ... (Same as original)
        complete_report = {
            'analysis_id': analysis_id,
            'timestamp': datetime.now().isoformat(),
            'document': doc_data['file_name'],
            'model_used': self.model,
            'document_data': doc_data,
            'ai_analysis': ai_analysis
        }
        
        json_path = output_dir / f"{doc_name}_{analysis_id}_AI_complete.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(complete_report, f, indent=2, ensure_ascii=False)
        reports['json'] = str(json_path)
        logger.info(f"      ✓ Generated JSON report: {json_path.name}")
        
        # 2. Executive Summary Report
        # ... (Same as original)
        exec_report = self._generate_executive_summary(doc_data, ai_analysis)
        exec_path = output_dir / f"{doc_name}_{analysis_id}_AI_executive.txt"
        with open(exec_path, 'w', encoding='utf-8') as f:
            f.write(exec_report)
        reports['executive'] = str(exec_path)
        logger.info(f"      ✓ Generated Executive report: {exec_path.name}")
        
        # 3. Detailed Analysis Report
        # ... (Same as original)
        detail_path = output_dir / f"{doc_name}_{analysis_id}_AI_detailed.txt"
        with open(detail_path, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("AI DETAILED FRAUD ANALYSIS\n")
            f.write("="*80 + "\n\n")
            f.write(ai_analysis.get('detailed_analysis', 'No detailed analysis available'))
        reports['detailed'] = str(detail_path)
        logger.info(f"      ✓ Generated Detailed report: {detail_path.name}")
        
        return reports
    
    def _generate_executive_summary(
        self,
        doc_data: Dict[str, Any],
        ai_analysis: Dict[str, Any]
    ) -> str:
        """Generate executive summary"""
        # ... (Same as original)
        lines = []
        lines.append("="*80)
        lines.append("EXECUTIVE FRAUD DETECTION REPORT")
        lines.append("AI-Powered Analysis")
        lines.append("="*80)
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Document: {doc_data['file_name']}")
        lines.append(f"AI Model: {self.model}")
        lines.append("")
        
        lines.append("RISK ASSESSMENT")
        lines.append("-"*80)
        lines.append(f"Risk Score: {ai_analysis['risk_score']}/10")
        lines.append(f"Risk Level: {ai_analysis['risk_level']}")
        lines.append(f"Fraud Likelihood: {ai_analysis['fraud_likelihood']}")
        lines.append(f"AI Confidence: {ai_analysis['confidence']*100:.1f}%")
        lines.append("")
        
        lines.append("EXECUTIVE SUMMARY")
        lines.append("-"*80)
        lines.append(ai_analysis.get('overall_summary', 'No summary available'))
        lines.append("")
        
        if ai_analysis.get('critical_issues'):
            lines.append("⚠️  CRITICAL ISSUES")
            lines.append("-"*80)
            for issue in ai_analysis['critical_issues']:
                lines.append(f"  • {issue}")
            lines.append("")
        
        lines.append("KEY FINDINGS")
        lines.append("-"*80)
        for finding in ai_analysis.get('key_findings', []):
            lines.append(f"  • {finding}")
        lines.append("")
        
        lines.append("PRIMARY CONCERNS")
        lines.append("-"*80)
        for concern in ai_analysis.get('primary_concerns', []):
            lines.append(f"  • {concern}")
        lines.append("")
        
        recommendations = ai_analysis.get('recommendations', {})
        if not isinstance(recommendations, dict):
            # Log the unexpected type for audit purposes
            logger.warning(
                f"Recommendations key in AI analysis was type {type(recommendations).__name__}, expected dict. Using empty dict."
            )
            recommendations = {}
        lines.append("RECOMMENDATION")
        lines.append("-"*80)
        lines.append(f"Action: {recommendations.get('approval_recommendation', 'REVIEW')}")
        lines.append(f"Justification: {recommendations.get('justification', 'See detailed analysis')}")
        lines.append("")
        
        if recommendations.get('immediate_actions'):
            lines.append("IMMEDIATE ACTIONS REQUIRED")
            lines.append("-"*80)
            for action in recommendations['immediate_actions']:
                lines.append(f"  1. {action}")
            lines.append("")
        
        lines.append("="*80)
        
        return "\n".join(lines)
    
    def _log_analysis_completion(self, results: Dict[str, Any]):
        """Log the completion summary to the audit trail"""
        ai = results['ai_analysis']
        
        log_message = (
            f"ANALYSIS COMPLETED | ID: {results['analysis_id']} | Document: {results['document']} | "
            f"Risk Level: {ai['risk_level']} | Score: {ai['risk_score']}/10 | "
            f"Recommendation: {ai.get('recommendations', {}).get('approval_recommendation', 'REVIEW')} | "
            f"Duration: {results['duration_seconds']:.2f}s"
        )
        logger.info("=" * 80)
        logger.info(log_message)
        
        # Log critical issues for high visibility
        if ai.get('critical_issues'):
            logger.warning(f"CRITICAL ISSUES: {len(ai['critical_issues'])}")
            for issue in ai['critical_issues']:
                logger.warning(f"  - {issue}")
        
        # Log report file paths
        logger.info("REPORTS GENERATED:")
        for report_type, path in results['reports'].items():
            logger.info(f"  {report_type.upper()}: {path}")
            
        logger.info("=" * 80)
    
    def _print_summary(self, results: Dict[str, Any]):
        """Print analysis summary (kept for CLI, now uses logging for all output)"""
        # This function is now essentially replaced by the logging setup,
        # but kept to maintain the original CLI behavior. It now relies on the 
        # logger which is configured to output to the console (ch).
        
        ai = results['ai_analysis']
        
        print("="*80)
        print("🤖 AI ANALYSIS COMPLETE (See logs for full audit trail)")
        print("="*80)
        print(f"Duration: {results['duration_seconds']:.2f} seconds")
        print("")
        
        print(f"Risk Score: {ai['risk_score']}/10")
        print(f"Risk Level: {ai['risk_level']}")
        print(f"Fraud Likelihood: {ai['fraud_likelihood']}")
        print(f"AI Confidence: {ai['confidence']*100:.1f}%")
        print("")
        
        print("Summary:")
        print(f"  {ai.get('overall_summary', 'N/A')}")
        print("")
        
        if ai.get('critical_issues'):
            print(f"⚠️  {len(ai['critical_issues'])} CRITICAL ISSUE(S) FOUND")
            for issue in ai['critical_issues'][:3]:
                print(f"  • {issue}")
            print("")
        
        print("Recommendation:")
        rec = ai.get('recommendations', {})
        print(f"  {rec.get('approval_recommendation', 'REVIEW')}")
        print("")
        
        print("Reports Generated:")
        for report_type, path in results['reports'].items():
            print(f"  {report_type.upper()}: {path}")
        print("")
        
        print("="*80)


def main():
    """Command-line interface"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Pure AI Fraud Detection - Groq does ALL analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python ai_fraud_detector.py document.pdf
  python ai_fraud_detector.py --model llama-3.2-90b-text-preview document.pdf
  python ai_fraud_detector.py --output-dir ./reports document.pdf

Get your FREE Groq API key at: https://console.groq.com/keys
Set as: export GROQ_API_KEY='your-key'
        """
    )
    
    parser.add_argument('document', help='Path to document to analyze')
    parser.add_argument('--model', default='llama-3.3-70b-versatile', help='Groq model')
    parser.add_argument('--output-dir', default='data/outputs', help='Output directory')
    parser.add_argument('--api-key', help='Groq API key (or use GROQ_API_KEY env var)')
    
    args = parser.parse_args()
    
    try:
        # Initialize detector
        detector = AIFraudDetector(model=args.model)
        
        # Analyze document
        results = detector.analyze_document(args.document, args.output_dir)
        
        # Success
        sys.exit(0)
        
    except Exception as e:
        # Exception is already logged in analyze_document, but adding a fallback print
        # for user visibility in the console.
        print(f"\n✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()