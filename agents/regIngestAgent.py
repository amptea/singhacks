"""
MAS Regulation Compliance Agent
================================

PURPOSE:
--------
This agent automatically monitors and validates regulatory compliance by comparing 
the latest MAS (Monetary Authority of Singapore) Notice 626 regulations with your 
organization's documented compliance requirements in mas.json.

SOURCE OF TRUTH:
----------------
MAS Notice 626 PDF (from MAS website) is the AUTHORITATIVE source of truth.
- Official URL: https://www.mas.gov.sg/regulation/notices/notice-626
- Latest revision: 30 June 2025
- Document: "Prevention of Money Laundering and Countering the Financing of Terrorism – Banks"

mas.json is YOUR ORGANIZATION'S documented interpretation/implementation of Notice 626.
- Location: data/mas.json
- Should match the official Notice 626 requirements
- This agent validates whether mas.json is up-to-date with the latest official notice

HOW IT WORKS:
-------------
1. SCRAPING PHASE:
   - Connects to MAS website and navigates to Notice 626 page
   - Locates the latest PDF version (currently 30 June 2025 revision)
   - Downloads the complete PDF document
   - Extracts ALL text content from ALL pages (no truncation)

2. EXTRACTION PHASE:
   - Reads your organization's mas.json file
   - Identifies all documented clauses (4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, etc.)
   - Prepares both documents for comprehensive comparison

3. AI ANALYSIS PHASE:
   - Uses Groq AI (llama-3.3-70b-versatile model) for intelligent comparison
   - Performs CLAUSE-BY-CLAUSE analysis of ALL clauses (not just samples)
   - Compares:
     * Document metadata (notice number, dates, title)
     * Every single clause and sub-clause
     * Requirements, obligations, and thresholds
     * Risk factors and compliance components
   
4. VALIDATION PHASE:
   - Identifies three types of status for each clause:
     * CONSISTENT: Content matches (ignore formatting differences)
     * DIFFERENT: Substantive changes in requirements
     * MISSING: Clause exists in one but not the other
   
5. REPORTING PHASE:
   - Generates detailed JSON report with:
     * Document match verification
     * Clause-by-clause comparison results
     * Overall consistency score
     * Critical differences (require immediate action)
     * Minor differences (cosmetic/formatting only)
   - Saves results to data/scraping_results.json
   - Results viewable in Streamlit UI (src/mas_scraping_ui.py)

WHAT TO DO WITH RESULTS:
-------------------------
✅ Consistency Score 95%+ & No Critical Differences:
   → Your mas.json is up-to-date, no action needed

⚠️ Critical Differences Found:
   → Review the differences immediately
   → Update mas.json to match the official Notice 626
   → Update your compliance procedures accordingly
   → Re-run this agent to verify updates

📊 Minor Differences:
   → Review for completeness
   → Update mas.json if needed for clarity
   → Generally cosmetic (formatting, word order)

USE CASES:
----------
1. Regular Compliance Monitoring: Run weekly/monthly to catch regulatory updates
2. Audit Preparation: Verify mas.json matches current regulations before audits
3. Change Detection: Automatically identify when MAS updates Notice 626
4. Documentation Sync: Ensure internal docs stay aligned with official requirements

CONFIGURATION:
--------------
- API Key: Set GROQ_API_KEY or api_key in .env file
- Temperature: 0.1 (low for consistent, factual analysis)
- Max Tokens: 16,000 (ensures comprehensive analysis of all clauses)
- No cost/time limits: Thoroughness prioritized over speed

AUTHOR NOTES:
-------------
Cost and inference time are not constraints - this agent prioritizes thoroughness
and accuracy over speed. It will analyze every clause comprehensively to ensure
no regulatory requirements are missed.
"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from groq import Groq
import os
from typing import Dict, List, Tuple
import re
from urllib.parse import urljoin, urlparse
from dotenv import load_dotenv
import PyPDF2
import io

# Load environment variables from .env file
load_dotenv()

class MASRegulationScraper:
    """
    Agent to scrape MAS Notice 626 regulations and compare with mas.json.
    
    Source of Truth: MAS Notice 626 PDF from official MAS website
    Validation Target: data/mas.json (your organization's compliance documentation)
    """
    
    def __init__(self, groq_api_key=None):
        self.base_url = "https://www.mas.gov.sg"
        self.search_url = "https://www.mas.gov.sg/regulation/regulations-and-guidance?content_type=Notices&sectors=Banking&page=1&topics=Anti-Money%20Laundering"
        
        # Direct links to known notices (fallback if search doesn't work)
        # Notice 626 is first since mas.json is now based on Notice 626 (Banks)
        self.known_notices = [
            {
                'title': 'MAS Notice 626 - Prevention of Money Laundering and Countering the Financing of Terrorism – Banks',
                'url': 'https://www.mas.gov.sg/regulation/notices/notice-626'
            }
        ]
        
        self.mas_json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'mas.json')
        
        # Initialize Groq client for AI analysis
        if groq_api_key:
            self.groq_client = Groq(api_key=groq_api_key)
        else:
            # Try to get API key from environment variables
            api_key = os.getenv('GROQ_API_KEY') or os.getenv('api_key')
            if api_key:
                self.groq_client = Groq(api_key=api_key)
            else:
                self.groq_client = Groq()  # Will raise error if not set
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def scrape_mas_page(self) -> Dict:
        """Scrape the MAS regulation search page and drill into notices"""
        print(f"🔍 Scraping MAS website: {self.search_url}")
        
        # Use known notices as fallback since the page uses JavaScript for dynamic content
        print(f"� Using known notice links (page uses dynamic JavaScript loading)")
        documents = self.known_notices.copy()
        
        print(f"\n📄 Processing {len(documents)} known MAS notices...")
        
        # Now drill into each notice page to find PDFs
        for doc in documents:
            print(f"\n🔎 Drilling into: {doc['title']}")
            pdf_info = self._drill_into_notice_page(doc['url'])
            doc.update(pdf_info)
        
        return {
            'scraped_at': datetime.now().isoformat(),
            'source_url': self.search_url,
            'documents_found': len(documents),
            'documents': documents
        }
    
    def _drill_into_notice_page(self, notice_url: str) -> Dict:
        """Drill into a notice page and find the PDF link"""
        try:
            print(f"   📥 Fetching notice page: {notice_url}")
            response = requests.get(notice_url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for PDF links or "View Notice" buttons
            pdf_links = []
            
            # Strategy 1: Find direct PDF links
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                if href.lower().endswith('.pdf') or 'view notice' in text.lower() or 'download' in text.lower():
                    pdf_url = urljoin(self.base_url, href)
                    pdf_links.append({
                        'pdf_url': pdf_url,
                        'link_text': text
                    })
                    print(f"   ✓ Found PDF link: {text} -> {pdf_url}")
            
            if not pdf_links:
                print(f"   ⚠️  No PDF links found on this page")
                return {'pdf_links': [], 'pdf_content': None}
            
            # Download and extract text from the first PDF
            first_pdf = pdf_links[0]
            pdf_text = self._extract_pdf_text(first_pdf['pdf_url'])
            
            return {
                'pdf_links': pdf_links,
                'pdf_content': pdf_text,  # Full text - no truncation since cost/time not crucial
                'pdf_full_length': len(pdf_text) if pdf_text else 0
            }
            
        except Exception as e:
            print(f"   ❌ Error drilling into notice page: {str(e)}")
            return {'error': str(e), 'pdf_links': [], 'pdf_content': None}
    
    def _extract_pdf_text(self, pdf_url: str) -> str:
        """Download and extract text from a PDF - ALL pages"""
        try:
            print(f"   📄 Downloading PDF: {pdf_url}")
            response = requests.get(pdf_url, headers=self.headers, timeout=60)
            response.raise_for_status()
            
            # Read PDF content
            pdf_file = io.BytesIO(response.content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text = ""
            num_pages = len(pdf_reader.pages)
            print(f"   📑 Extracting text from ALL {num_pages} pages (no limit)...")
            
            # Extract ALL pages - no limit since cost/time not crucial
            for page_num in range(num_pages):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n"
                if (page_num + 1) % 10 == 0:
                    print(f"      ... processed {page_num + 1}/{num_pages} pages")
            
            print(f"   ✓ Extracted {len(text)} characters from {num_pages} pages")
            return text
            
        except Exception as e:
            print(f"   ❌ Error extracting PDF text: {str(e)}")
            return ""
    
    def load_mas_json(self) -> Dict:
        """Load the existing mas.json file"""
        try:
            with open(self.mas_json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"⚠️  mas.json not found at {self.mas_json_path}")
            return {}
        except Exception as e:
            print(f"❌ Error loading mas.json: {str(e)}")
            return {}
    
    def compare_with_groq(self, scraped_content: str, mas_json_content: Dict) -> Dict:
        """Use Groq AI to compare scraped PDF content with mas.json clause by clause - ALL clauses comprehensively"""
        print("\n🤖 Using Groq AI to perform COMPREHENSIVE clause-by-clause comparison of ALL clauses...")
        
        # Get FULL mas.json content - no truncation
        mas_json_full = json.dumps(mas_json_content, indent=2)
        
        # Get FULL PDF content - no truncation
        full_pdf_content = scraped_content
        
        print(f"   📊 Analyzing FULL mas.json: {len(mas_json_full)} characters")
        print(f"   📄 Analyzing FULL PDF content: {len(full_pdf_content)} characters")
        
        # Create a comprehensive prompt that examines ALL clauses
        prompt = f"""You are a meticulous regulatory compliance analyst specializing in MAS Anti-Money Laundering regulations. Your task is to perform an EXHAUSTIVE CLAUSE-BY-CLAUSE comparison between the complete PDF content from MAS Notice 626 and ALL clauses in the structured mas.json file.

=== CRITICAL INSTRUCTIONS ===
1. Compare EVERY SINGLE clause mentioned in mas.json with the PDF - not just clause 4 and 6
2. Go through ALL sections in mas.json:
   - risk_assessment (clause_4 and all sub-clauses)
   - customer_due_diligence (clause_6 and all sub-clauses like 6.1, 6.2, 6.3, 6.4, 6.19-6.26)
   - internal_policies (clause_7)
   - record_keeping (clause_11)
   - suspicious_transaction_reporting (clause_9)
   - screening_procedures
   - training_requirements
   - reliance_on_third_parties
   - And ANY other clauses present in mas.json

3. For EACH clause, verify:
   - Clause number exists in PDF
   - Clause title matches exactly
   - ALL requirements and sub-requirements are identical
   - Risk factors and components are the same
   - No wording changes that alter legal meaning

4. Report ALL clauses checked, even if they match perfectly

5. Distinguish between:
   - CONSISTENT: Content is substantively identical (ignore formatting/minor wording)
   - DIFFERENT: Substantive changes in requirements, obligations, or thresholds
   - MISSING_IN_PDF: Clause exists in mas.json but not found in PDF
   - MISSING_IN_JSON: Important clause in PDF but not in mas.json

=== COMPLETE MAS.JSON CONTENT (Reference Document) ===
{mas_json_full}

=== COMPLETE SCRAPED PDF CONTENT FROM MAS NOTICE 626 ===
{full_pdf_content}

=== OUTPUT FORMAT ===
Provide your COMPREHENSIVE analysis in this exact JSON structure with ALL clauses:
{{
  "document_match": {{
    "notice_number": "Match status",
    "effective_date": "Match status",
    "last_revised": "Match status",
    "title": "Match status"
  }},
  "clause_by_clause_comparison": [
    {{
      "clause_id": "clause_4",
      "clause_title": "Risk Assessment",
      "status": "CONSISTENT|DIFFERENT|MISSING",
      "details": "Detailed explanation",
      "sub_clauses_checked": ["4.1", "4.2", "4.3", ...]
    }},
    {{
      "clause_id": "clause_6",
      "clause_title": "Customer Due Diligence",
      "status": "CONSISTENT|DIFFERENT|MISSING",
      "details": "Detailed explanation",
      "sub_clauses_checked": ["6.1", "6.2", "6.3", "6.4", "6.19", "6.20", ...]
    }},
    {{
      "clause_id": "clause_7",
      "clause_title": "Internal Policies, Procedures and Controls",
      "status": "CONSISTENT|DIFFERENT|MISSING",
      "details": "Detailed explanation",
      "sub_clauses_checked": [...]
    }},
    {{
      "clause_id": "clause_9",
      "clause_title": "Suspicious Transaction Reporting",
      "status": "CONSISTENT|DIFFERENT|MISSING",
      "details": "Detailed explanation",
      "sub_clauses_checked": [...]
    }},
    {{
      "clause_id": "clause_11",
      "clause_title": "Record Keeping",
      "status": "CONSISTENT|DIFFERENT|MISSING",
      "details": "Detailed explanation",
      "sub_clauses_checked": [...]
    }}
    // ... CONTINUE FOR ALL OTHER CLAUSES IN MAS.JSON
  ],
  "overall_assessment": {{
    "total_clauses_checked": "number",
    "consistency_score": "X%",
    "consistent_clauses": "number",
    "different_clauses": "number",
    "missing_clauses": "number",
    "critical_differences": ["List REAL substantive differences"],
    "minor_differences": ["List minor wording variations"],
    "conclusion": "Overall assessment - are documents substantially identical?"
  }}
}}

=== WHAT CONSTITUTES A REAL DIFFERENCE ===
REPORT as DIFFERENT only if:
- New requirements added or removed
- Obligations strengthened or weakened
- Thresholds or limits changed
- Scope of applicability changed
- Legal terminology changed meaning

IGNORE (mark as CONSISTENT):
- Formatting differences (bullets vs paragraphs)
- Word order if meaning unchanged
- Synonyms with same legal meaning ("shall" vs "must", "bank" vs "financial institution" in context)
- Structural reorganization if content identical

=== YOUR MISSION ===
Leave NO clause unchecked. Analyze EVERY clause in mas.json against the PDF comprehensively. Cost and time are not constraints - thoroughness is paramount."""
        
        try:
            completion = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert regulatory analyst with unlimited time and resources. You perform EXHAUSTIVE, detailed comparisons of regulatory documents, examining every single clause thoroughly. You never skip clauses or summarize - you analyze everything completely."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_completion_tokens=16000,  # Increased significantly for comprehensive output
                top_p=0.95
            )
            
            analysis = completion.choices[0].message.content
            
            return {
                'analysis': analysis,
                'timestamp': datetime.now().isoformat(),
                'model': 'llama-3.3-70b-versatile'
            }
            
        except Exception as e:
            print(f"❌ Error in Groq analysis: {str(e)}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _compare_section(self, section_name: str, section_data: Dict, doc_content: str) -> str:
        """Compare a specific section using AI"""
        prompt = f"""Compare this regulatory section with the document content.

SECTION: {section_name}
EXISTING DATA: {json.dumps(section_data, indent=2)[:1000]}

DOCUMENT CONTENT: {doc_content[:2000]}

Are there any changes or updates? Provide a brief summary."""
        
        try:
            completion = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_completion_tokens=500
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"Error: {str(e)}"
    
    def run(self) -> Dict:
        """Main execution method"""
        print("="*80)
        print("🚀 MAS REGULATION SCRAPER & CROSS-REFERENCE AGENT")
        print("="*80)
        
        # Step 1: Scrape MAS website and drill into notices
        scraped_data = self.scrape_mas_page()
        
        # Step 2: Load existing mas.json
        mas_json = self.load_mas_json()
        
        # Step 3: Get latest document PDF content
        latest_doc_content = ""
        if scraped_data.get('documents'):
            latest_doc = scraped_data['documents'][0]
            print(f"\n📌 Latest Document: {latest_doc.get('title', 'Unknown')}")
            
            # Use PDF content if available, otherwise fetch the page
            if latest_doc.get('pdf_content'):
                latest_doc_content = latest_doc['pdf_content']
                print(f"   ✓ Using extracted PDF content ({len(latest_doc_content)} chars)")
            elif latest_doc.get('url'):
                print(f"   ⚠️  No PDF content, falling back to page scraping")
                # This method is kept for fallback but won't be as useful
                pass
        
        # Step 4: Compare with Groq AI
        comparison_result = {}
        if latest_doc_content and mas_json:
            comparison_result = self.compare_with_groq(latest_doc_content, mas_json)
        
        # Step 5: Cross-reference sections with PDF content
        cross_ref_result = {}
        if scraped_data.get('documents'):
            cross_ref_result = self.cross_reference_sections_with_pdf(
                scraped_data['documents'][:2],  # Top 2 documents
                mas_json
            )
        
        # Compile final results
        results = {
            'execution_time': datetime.now().isoformat(),
            'scraped_data': scraped_data,
            'mas_json_info': mas_json.get('document_info', {}),
            'comparison': comparison_result,
            'cross_reference': cross_ref_result
        }
        
        # Save results
        output_path = os.path.join(os.path.dirname(self.mas_json_path), 'scraping_results.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Results saved to: {output_path}")
        
        # Print summary
        self._print_summary(results)
        
        return results
    
    def cross_reference_sections_with_pdf(self, scraped_docs: List[Dict], mas_json: Dict) -> Dict:
        """Cross-reference each section using PDF content"""
        print("\n🔄 Cross-referencing sections with PDF content...")
        
        cross_reference_results = {
            'timestamp': datetime.now().isoformat(),
            'comparisons': []
        }
        
        # Extract key sections from mas.json
        mas_sections = []
        if 'risk_assessment_requirements' in mas_json:
            mas_sections.append(('Risk Assessment', mas_json['risk_assessment_requirements']))
        if 'customer_due_diligence' in mas_json:
            mas_sections.append(('Customer Due Diligence', mas_json.get('customer_due_diligence', {})))
        
        # Compare with scraped documents using their PDF content
        for doc in scraped_docs:
            if doc.get('pdf_content'):
                for section_name, section_data in mas_sections:
                    comparison = self._compare_section(section_name, section_data, doc['pdf_content'])
                    cross_reference_results['comparisons'].append({
                        'document': doc.get('title', 'Unknown'),
                        'section': section_name,
                        'comparison': comparison
                    })
        
        return cross_reference_results
    
    def _print_summary(self, results: Dict):
        """Print a summary of the analysis"""
        print("\n" + "="*80)
        print("📊 SUMMARY")
        print("="*80)
        
        print(f"\n🔍 Documents Found: {results['scraped_data'].get('documents_found', 0)}")
        
        if results.get('comparison', {}).get('analysis'):
            print("\n🤖 AI Analysis:")
            print(results['comparison']['analysis'][:500] + "...")
        
        print("\n" + "="*80)


# Main execution
if __name__ == "__main__":
    agent = MASRegulationScraper()
    results = agent.run()