"""
Enhanced Document Validator
Uses LLM to check formatting, content, and compare against standard templates
"""

import json
from typing import Dict, Any, List, Optional
from groq import Groq
import os
from dotenv import load_dotenv


class EnhancedDocumentValidator:
    """
    Enhanced validation using LLM with template comparison
    """
    
    def __init__(self, groq_api_key: Optional[str] = None):
        """Initialize validator"""
        load_dotenv()
        self.api_key = groq_api_key or os.environ.get("GROQ_API_KEY")
        
        if not self.api_key:
            raise ValueError("Groq API key required!")
        
        self.client = Groq(api_key=self.api_key)
        self.model = "llama-3.3-70b-versatile"
        
        # Document templates for comparison
        self.templates = self._load_templates()
    
    def validate_document(
        self, 
        text: str, 
        document_type: str = "statement",
        extracted_fields: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive document validation
        
        Args:
            text: Document text
            document_type: Type of document
            extracted_fields: Previously extracted structured fields
        
        Returns:
            Validation results with issues categorized
        """
        
        print(f"\n[Validator] Running comprehensive validation...")
        
        # Get template for this document type
        template = self.templates.get(document_type, self.templates['general'])
        
        prompt = f"""You are a document quality assurance expert. Perform comprehensive validation of this document.

DOCUMENT TEXT:
{text[:4000]}

DOCUMENT TYPE: {document_type}

EXPECTED DOCUMENT STRUCTURE:
{json.dumps(template, indent=2)}

PERFORM THESE CHECKS:

1. FORMATTING VALIDATION:
   - Detect double spacing, irregular fonts, inconsistent indentation
   - Check for unusual whitespace patterns
   - Identify formatting inconsistencies
   - Verify consistent use of formatting elements

2. CONTENT VALIDATION:
   - Check for spelling mistakes
   - Verify headers are correct and present
   - Identify missing sections compared to template
   - Check grammar and language quality

3. STRUCTURE VALIDATION:
   - Compare document structure against expected template
   - Verify all required sections are present
   - Check section ordering and organization
   - Assess document completeness

4. ACCURACY VALIDATION:
   - Check for inconsistent dates
   - Verify number/amount formatting
   - Identify contradictory information
   - Check logical flow

Provide analysis as JSON:
{{
    "formatting_issues": [
        {{
            "type": "double_spacing/irregular_font/inconsistent_indent/other",
            "severity": "low/medium/high",
            "location": "where found (e.g., paragraph 2, line 5)",
            "description": "detailed description",
            "highlight_text": "the actual text with issue (if applicable)"
        }}
    ],
    "content_issues": [
        {{
            "type": "spelling/grammar/missing_header/incorrect_header",
            "severity": "low/medium/high",
            "location": "where found",
            "description": "detailed description",
            "expected": "what should be there",
            "actual": "what is actually there"
        }}
    ],
    "structure_issues": [
        {{
            "type": "missing_section/incorrect_order/incomplete",
            "severity": "low/medium/high",
            "section": "section name",
            "description": "detailed description"
        }}
    ],
    "completeness_score": <0-100>,
    "accuracy_score": <0-100>,
    "overall_quality": "excellent/good/fair/poor",
    "critical_issues": ["list of critical issues that must be addressed"],
    "recommendations": ["specific recommendations for improvement"]
}}

Be thorough and specific. For each issue, provide enough detail for precise identification and correction."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert document quality analyst. Provide detailed, accurate validation results. Output valid JSON only."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,
                max_tokens=3000,
                response_format={"type": "json_object"}
            )
            
            validation_results = json.loads(response.choices[0].message.content)
            
            # Categorize issues for display
            validation_results['issue_summary'] = self._create_issue_summary(validation_results)
            validation_results['display_format'] = self._determine_display_format(validation_results)
            
            print(f"  ✓ Found {len(validation_results.get('formatting_issues', []))} formatting issues")
            print(f"  ✓ Found {len(validation_results.get('content_issues', []))} content issues")
            print(f"  ✓ Found {len(validation_results.get('structure_issues', []))} structure issues")
            print(f"  ✓ Completeness: {validation_results.get('completeness_score', 0)}%")
            
            return validation_results
            
        except Exception as e:
            print(f"  ✗ Validation error: {e}")
            return {
                'error': str(e),
                'formatting_issues': [],
                'content_issues': [],
                'structure_issues': [],
                'completeness_score': 0,
                'accuracy_score': 0
            }
    
    def _load_templates(self) -> Dict[str, Any]:
        """Load document templates for comparison"""
        return {
            'statement': {
                'required_sections': [
                    'Header with bank name and logo',
                    'Account holder information',
                    'Account number',
                    'Statement period',
                    'Transaction list',
                    'Balance information',
                    'Footer with disclaimers'
                ],
                'required_fields': [
                    'Account holder name',
                    'Account number',
                    'Statement date',
                    'Period start and end',
                    'Opening balance',
                    'Closing balance'
                ]
            },
            'invoice': {
                'required_sections': [
                    'Company header',
                    'Invoice number and date',
                    'Billing information',
                    'Items/Services list',
                    'Amounts and totals',
                    'Payment terms',
                    'Footer'
                ],
                'required_fields': [
                    'Invoice number',
                    'Invoice date',
                    'Due date',
                    'Bill to information',
                    'Items with prices',
                    'Total amount'
                ]
            },
            'general': {
                'required_sections': [
                    'Header or title',
                    'Date',
                    'Main content',
                    'Signature or closing'
                ],
                'required_fields': [
                    'Document type or title',
                    'Date',
                    'Issuer or author'
                ]
            }
        }
    
    def _create_issue_summary(self, results: Dict[str, Any]) -> Dict[str, int]:
        """Create summary of issues by severity"""
        summary = {'high': 0, 'medium': 0, 'low': 0}
        
        for issue_type in ['formatting_issues', 'content_issues', 'structure_issues']:
            for issue in results.get(issue_type, []):
                severity = issue.get('severity', 'low')
                summary[severity] = summary.get(severity, 0) + 1
        
        return summary
    
    def _determine_display_format(self, results: Dict[str, Any]) -> str:
        """Determine best display format for issues"""
        total_issues = (
            len(results.get('formatting_issues', [])) +
            len(results.get('content_issues', [])) +
            len(results.get('structure_issues', []))
        )
        
        # If many issues with specific locations, use table
        # If few issues, use text highlighting
        if total_issues > 10:
            return 'table'
        else:
            return 'highlight'


if __name__ == "__main__":
    validator = EnhancedDocumentValidator()
    
    test_text = """
    BANK  STATEMENT
    
    Account Holder: John  Doe
    Account Number: 123456789
    
    Period: January 2024
    Opening Balance: $1,000
    Closing Balance: $1,500
    
    Transactions:
    01/05/2024 - Deposit - $500
    """
    
    results = validator.validate_document(test_text, "statement")
    print("\nValidation Results:")
    print(json.dumps(results, indent=2))

