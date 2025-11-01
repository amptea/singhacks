"""
Pure AI Fraud Detection System
Uses Groq AI for ALL analysis - format validation, image analysis, risk assessment
Only parse_pdf_ocr.py for document extraction
"""

import os
import sys
import json
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


class AIFraudDetector:
    """
    Pure AI-powered fraud detection - Groq does everything
    """
    
    def __init__(
        self,
        groq_api_key: Optional[str] = "None",
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
        load_dotenv(dotenv_path=env_path)

        self.api_key = groq_api_key or os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Groq API key required!\n"
                "Get your FREE key at: https://console.groq.com/keys\n"
                "Set as: export GROQ_API_KEY='your-key'"
            )
        
        self.client = Groq(api_key=self.api_key)
        self.model = model
        print(f"✓ AI Fraud Detector initialized (Model: {model})")
    
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
            raise FileNotFoundError(f"Document not found: {document_path}")
        
        analysis_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        print("\n" + "="*80)
        print("🤖 PURE AI FRAUD DETECTION")
        print("="*80)
        print(f"Document: {doc_path.name}")
        print(f"Analysis ID: {analysis_id}")
        print(f"Model: {self.model}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("")
        
        start_time = datetime.now()
        
        try:
            # Step 1: Extract document data
            print("[1/3] Extracting document content...")
            doc_data = self._extract_document_data(str(doc_path))
            print(f"      ✓ Extracted {len(doc_data['text'])} characters")
            print(f"      ✓ Found {doc_data['total_pages']} page(s)")
            print(f"      ✓ Found {len(doc_data['images'])} image(s)")
            print(f"      ✓ Found {len(doc_data['fonts'])} unique font(s)")
            print("")
            
            # Step 2: AI analyzes EVERYTHING
            print("[2/3] AI analyzing document for fraud (all checks)...")
            ai_analysis = self._ai_comprehensive_analysis(doc_data)
            print(f"      ✓ AI analysis complete")
            print(f"      ✓ Fraud likelihood: {ai_analysis['fraud_likelihood']}")
            print(f"      ✓ Risk score: {ai_analysis['risk_score']}/10")
            print(f"      ✓ Risk level: {ai_analysis['risk_level']}")
            print("")
            
            # Step 3: Generate reports
            print("[3/3] Generating AI reports...")
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            reports = self._generate_reports(
                doc_data, ai_analysis, doc_path.stem, analysis_id, output_path
            )
            print(f"      ✓ Generated {len(reports)} report(s)")
            print("")
            
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
            
            # Print summary
            self._print_summary(results)
            
            return results
            
        except Exception as e:
            print(f"\n✗ Analysis failed: {e}")
            import traceback
            traceback.print_exc()
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
        
        # Extract images and fonts info
        fonts_seen = set()
        
        for page_num in range(len(pdf_doc)):
            page = pdf_doc[page_num]
            
            # Get images
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

1. FORMAT VALIDATION:
   - Check for spacing anomalies (double spacing, irregular indentation)
   - Analyze font consistency (unusual variety, size changes between sections)
   - Detect copy-paste artifacts (duplicate content, style changes)
   - Check formatting patterns (date formats, number formats, alignment)
   - Verify document structure (headers, paragraphs, sections)
   - Look for spelling/grammar issues that suggest manipulation

2. IMAGE ANALYSIS:
   - Assess image authenticity (metadata presence, consistency)
   - Check for signs of image manipulation or editing
   - Evaluate image quality and appropriateness
   - Look for AI-generated or synthetic image indicators
   - Check if images match document context

3. METADATA ANALYSIS:
   - Evaluate metadata completeness
   - Check for suspicious missing metadata
   - Look for timestamp inconsistencies
   - Assess file size appropriateness

4. CONTENT ANALYSIS:
   - Check text quality and completeness
   - Look for unusual patterns in content
   - Assess overall document coherence
   - Identify any red flags in the text

5. OVERALL RISK ASSESSMENT:
   - Calculate comprehensive risk score (0-10)
   - Determine fraud likelihood (MINIMAL/LOW/MEDIUM/HIGH/CRITICAL)
   - Identify key fraud indicators
   - Provide specific concerns

Provide your analysis as JSON:
{{
    "format_validation": {{
        "spacing_issues": ["list of issues found"],
        "font_issues": ["list of issues found"],
        "structure_issues": ["list of issues found"],
        "formatting_score": <0-10, 10=perfect>,
        "red_flags": ["list of red flags"]
    }},
    "image_analysis": {{
        "authenticity_assessment": "assessment of image authenticity",
        "manipulation_indicators": ["list of indicators"],
        "image_quality_score": <0-10>,
        "concerns": ["list of concerns"]
    }},
    "metadata_analysis": {{
        "completeness_score": <0-10>,
        "suspicious_elements": ["list of suspicious elements"],
        "concerns": ["list of concerns"]
    }},
    "content_analysis": {{
        "quality_score": <0-10>,
        "coherence_score": <0-10>,
        "red_flags": ["list of red flags"],
        "patterns_detected": ["list of patterns"]
    }},
    "overall_assessment": {{
        "risk_score": <0-10>,
        "risk_level": "MINIMAL/LOW/MEDIUM/HIGH/CRITICAL",
        "fraud_likelihood": "MINIMAL/LOW/MEDIUM/HIGH/CRITICAL",
        "confidence": <0-1>,
        "key_findings": ["list of most important findings"],
        "critical_issues": ["list of critical issues if any"],
        "patterns_indicating_fraud": ["list of fraud patterns"],
        "authenticity_indicators": ["list of things that look legitimate"],
        "primary_concerns": ["top 3-5 concerns"],
        "overall_summary": "Brief summary of authenticity assessment"
    }},
    "recommendations": {{
        "immediate_actions": ["list of immediate actions to take"],
        "verification_needed": ["what needs further verification"],
        "approval_recommendation": "APPROVE/REVIEW/REJECT",
        "justification": "Explanation of recommendation"
    }},
    "detailed_analysis": "A comprehensive narrative explanation of all findings, how they relate to each other, and why they matter for fraud detection. Explain your reasoning in detail."
}}

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
            print(f"Warning: JSON parsing error, using fallback: {e}")
            return {
                'fraud_likelihood': 'UNKNOWN',
                'risk_score': 5.0,
                'risk_level': 'MEDIUM',
                'confidence': 0.3,
                'key_findings': ['AI analysis error - manual review required'],
                'error': str(e),
                'raw_response': analysis_text if 'analysis_text' in locals() else ''
            }
    
    def _prepare_ai_context(self, doc_data: Dict[str, Any]) -> str:
        """Prepare document data as context for AI"""
        
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
        print(f"      ✓ JSON report: {json_path.name}")
        
        # 2. Executive Summary Report
        exec_report = self._generate_executive_summary(doc_data, ai_analysis)
        exec_path = output_dir / f"{doc_name}_{analysis_id}_AI_executive.txt"
        with open(exec_path, 'w', encoding='utf-8') as f:
            f.write(exec_report)
        reports['executive'] = str(exec_path)
        print(f"      ✓ Executive report: {exec_path.name}")
        
        # 3. Detailed Analysis Report
        detail_path = output_dir / f"{doc_name}_{analysis_id}_AI_detailed.txt"
        with open(detail_path, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("AI DETAILED FRAUD ANALYSIS\n")
            f.write("="*80 + "\n\n")
            f.write(ai_analysis.get('detailed_analysis', 'No detailed analysis available'))
        reports['detailed'] = str(detail_path)
        print(f"      ✓ Detailed report: {detail_path.name}")
        
        return reports
    
    def _generate_executive_summary(
        self,
        doc_data: Dict[str, Any],
        ai_analysis: Dict[str, Any]
    ) -> str:
        """Generate executive summary"""
        
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
    
    def _print_summary(self, results: Dict[str, Any]):
        """Print analysis summary"""
        
        ai = results['ai_analysis']
        
        print("="*80)
        print("🤖 AI ANALYSIS COMPLETE")
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
        detector = AIFraudDetector(groq_api_key=args.api_key, model=args.model)
        
        # Analyze document
        results = detector.analyze_document(args.document, args.output_dir)
        
        # Success
        sys.exit(0)
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

