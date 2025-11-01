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

# Load environment variables from .env file
load_dotenv()

class MASRegulationScraper:
    """Agent to scrape MAS regulations and compare with existing mas.json"""
    
    def __init__(self, groq_api_key=None):
        self.base_url = "https://www.mas.gov.sg"
        self.search_url = "https://www.mas.gov.sg/regulation/regulations-and-guidance?content_type=Notices&sectors=Banking&page=1&topics=Anti-Money%20Laundering"
        # Updated path: go up two directories from agents/part1 to reach data folder
        self.mas_json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'mas.json')
        
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
        """Scrape the MAS regulation search page"""
        print(f"🔍 Scraping MAS website: {self.search_url}")
        
        try:
            response = requests.get(self.search_url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract document listings
            documents = []
            
            # Find all result items (adjust selectors based on actual page structure)
            result_items = soup.find_all(['div', 'article', 'li'], class_=re.compile(r'result|item|document|notice', re.I))
            
            if not result_items:
                # Try alternative selectors
                result_items = soup.find_all(['a'], href=re.compile(r'(notice|regulation|guidance)', re.I))
            
            print(f"📄 Found {len(result_items)} potential document items")
            
            for item in result_items[:5]:  # Get top 5 results
                doc_info = self._extract_document_info(item, soup)
                if doc_info:
                    documents.append(doc_info)
            
            return {
                'scraped_at': datetime.now().isoformat(),
                'source_url': self.search_url,
                'documents_found': len(documents),
                'documents': documents
            }
            
        except Exception as e:
            print(f"❌ Error scraping MAS page: {str(e)}")
            return {
                'error': str(e),
                'scraped_at': datetime.now().isoformat(),
                'documents': []
            }
    
    def _extract_document_info(self, item, soup) -> Dict:
        """Extract document information from a search result item"""
        try:
            doc_info = {}
            
            # Try to find title
            title_elem = item.find(['h1', 'h2', 'h3', 'h4', 'a'])
            if title_elem:
                doc_info['title'] = title_elem.get_text(strip=True)
            
            # Try to find link
            link_elem = item.find('a', href=True)
            if link_elem:
                doc_info['url'] = urljoin(self.base_url, link_elem['href'])
            elif item.name == 'a' and item.get('href'):
                doc_info['url'] = urljoin(self.base_url, item['href'])
            
            # Try to find date
            date_elem = item.find(['time', 'span'], class_=re.compile(r'date|time', re.I))
            if date_elem:
                doc_info['date'] = date_elem.get_text(strip=True)
            
            # Try to find description/summary
            desc_elem = item.find(['p', 'div'], class_=re.compile(r'description|summary|excerpt', re.I))
            if desc_elem:
                doc_info['description'] = desc_elem.get_text(strip=True)
            
            # Get document type
            type_elem = item.find(['span', 'div'], class_=re.compile(r'type|category', re.I))
            if type_elem:
                doc_info['type'] = type_elem.get_text(strip=True)
            
            return doc_info if doc_info else None
            
        except Exception as e:
            print(f"⚠️  Error extracting document info: {str(e)}")
            return None
    
    def fetch_document_content(self, url: str) -> str:
        """Fetch the full content of a document"""
        try:
            print(f"📥 Fetching document: {url}")
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Get text content
            text = soup.get_text(separator='\n', strip=True)
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            return text
            
        except Exception as e:
            print(f"❌ Error fetching document: {str(e)}")
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
        """Use Groq AI to compare scraped content with mas.json"""
        print("\n🤖 Using Groq AI to analyze differences...")
        
        # Prepare the prompt
        mas_summary = json.dumps(mas_json_content.get('document_info', {}), indent=2)
        
        prompt = f"""You are an expert regulatory compliance analyst. Compare the following scraped content from the MAS website with the existing regulatory document stored in mas.json.

EXISTING DOCUMENT (mas.json):
{mas_summary}

Key requirements from mas.json:
- Risk Assessment Requirements
- Customer Due Diligence (CDD)
- Enhanced Customer Due Diligence
- Suspicious Transaction Reporting

SCRAPED CONTENT FROM MAS WEBSITE:
{scraped_content[:4000]}  # Limit to avoid token limits

Please analyze and provide:
1. **Changes Detected**: List any new requirements, updated clauses, or modifications
2. **Missing Elements**: What's in the scraped content but not in mas.json
3. **Consistency Check**: Are the requirements in mas.json still current?
4. **Risk Rating**: Rate the impact of any changes (LOW/MEDIUM/HIGH)
5. **Recommendations**: What updates should be made to mas.json

Format your response as a structured JSON."""
        
        try:
            completion = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a regulatory compliance expert specializing in Anti-Money Laundering (AML) and Counter-Terrorism Financing (CTF) regulations."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_completion_tokens=4096,
                top_p=0.9
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
    
    def cross_reference_sections(self, scraped_docs: List[Dict], mas_json: Dict) -> Dict:
        """Cross-reference each section of the document"""
        print("\n🔄 Cross-referencing sections...")
        
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
        
        # Compare with scraped documents
        for doc in scraped_docs:
            if doc.get('url'):
                doc_content = self.fetch_document_content(doc['url'])
                
                for section_name, section_data in mas_sections:
                    comparison = self._compare_section(section_name, section_data, doc_content)
                    cross_reference_results['comparisons'].append({
                        'document': doc.get('title', 'Unknown'),
                        'section': section_name,
                        'comparison': comparison
                    })
        
        return cross_reference_results
    
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
        
        # Step 1: Scrape MAS website
        scraped_data = self.scrape_mas_page()
        
        # Step 2: Load existing mas.json
        mas_json = self.load_mas_json()
        
        # Step 3: Get latest document content
        latest_doc_content = ""
        if scraped_data.get('documents'):
            latest_doc = scraped_data['documents'][0]
            print(f"\n📌 Latest Document: {latest_doc.get('title', 'Unknown')}")
            if latest_doc.get('url'):
                latest_doc_content = self.fetch_document_content(latest_doc['url'])
        
        # Step 4: Compare with Groq AI
        comparison_result = {}
        if latest_doc_content and mas_json:
            comparison_result = self.compare_with_groq(latest_doc_content, mas_json)
        
        # Step 5: Cross-reference sections
        cross_ref_result = {}
        if scraped_data.get('documents'):
            cross_ref_result = self.cross_reference_sections(
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