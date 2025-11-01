"""
Structured Field Extractor
Uses Groq LLM to extract specific fields from documents into JSON
"""

import os
import json
from typing import Dict, Any, List, Optional
from groq import Groq
from dotenv import load_dotenv


class StructuredFieldExtractor:
    """
    Extract structured fields from documents using LLM
    """
    
    def __init__(self, groq_api_key: Optional[str] = None):
        """Initialize with Groq API key"""
        load_dotenv()
        self.api_key = groq_api_key or os.environ.get("GROQ_API_KEY")
        
        if not self.api_key:
            raise ValueError("Groq API key required!")
        
        self.client = Groq(api_key=self.api_key)
        self.model = "llama-3.3-70b-versatile"
    
    def extract_fields(self, text: str, document_type: str = "general") -> Dict[str, Any]:
        """
        Extract structured fields from document text
        
        Args:
            text: Document text
            document_type: Type of document (general, statement, invoice, etc.)
        
        Returns:
            Extracted fields as JSON
        """
        
        print(f"\n[Extractor] Extracting structured fields...")
        
        # Define fields to extract based on document type
        fields_schema = self._get_fields_schema(document_type)
        
        prompt = f"""You are a document data extraction expert. Extract the following structured information from the document text.

DOCUMENT TEXT:
{text[:4000]}  # First 4000 characters

EXTRACT THESE FIELDS:
{json.dumps(fields_schema, indent=2)}

INSTRUCTIONS:
1. Extract ONLY information that is explicitly present in the document
2. Use null for fields that are not found
3. Be precise and accurate - do not infer or guess
4. For dates, use format: YYYY-MM-DD
5. For amounts, include currency if mentioned
6. Extract ALL relevant information for each field

Return a JSON object with the extracted data. Follow the schema structure exactly.

IMPORTANT: Output ONLY valid JSON, no explanations or additional text."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a precise data extraction system. Extract structured information from documents and return valid JSON only."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,  # Very low for precise extraction
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            extracted = json.loads(response.choices[0].message.content)
            
            print(f"  ✓ Extracted {len(extracted)} field groups")
            
            return {
                'success': True,
                'extracted_fields': extracted,
                'document_type': document_type,
                'fields_found': sum(1 for v in self._flatten_dict(extracted).values() if v is not None)
            }
            
        except Exception as e:
            print(f"  ✗ Extraction error: {e}")
            return {
                'success': False,
                'error': str(e),
                'extracted_fields': {}
            }
    
    def _get_fields_schema(self, document_type: str) -> Dict[str, Any]:
        """Get extraction schema based on document type"""
        
        # Universal fields for all documents
        base_schema = {
            "document_info": {
                "document_type": "Type of document",
                "document_number": "Reference or document number",
                "document_date": "Date of document (YYYY-MM-DD)",
                "issuer": "Who issued this document"
            },
            "parties": {
                "party_name": "Name of main party/client",
                "party_id": "ID number, registration number, or reference",
                "party_address": "Full address",
                "party_contact": "Phone, email, or other contact"
            },
            "institution": {
                "bank_name": "Name of bank or financial institution",
                "bank_address": "Institution address",
                "branch": "Branch name or code",
                "swift_code": "SWIFT/BIC code if present"
            },
            "transaction_info": {
                "transaction_id": "Transaction reference or ID",
                "transaction_date": "Transaction date (YYYY-MM-DD)",
                "amount": "Transaction amount with currency",
                "description": "Transaction description"
            },
            "additional_info": {
                "account_number": "Account number if present",
                "purpose": "Purpose of transaction or document",
                "notes": "Any special notes or remarks"
            }
        }
        
        # Add document-specific fields
        if document_type == "statement":
            base_schema["statement_specific"] = {
                "period_start": "Statement period start date",
                "period_end": "Statement period end date",
                "opening_balance": "Opening balance",
                "closing_balance": "Closing balance"
            }
        
        elif document_type == "invoice":
            base_schema["invoice_specific"] = {
                "invoice_number": "Invoice number",
                "due_date": "Payment due date",
                "items": "List of items or services",
                "total_amount": "Total amount due"
            }
        
        return base_schema
    
    def _flatten_dict(self, d: Dict, parent_key: str = '', sep: str = '.') -> Dict:
        """Flatten nested dictionary"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)


if __name__ == "__main__":
    # Test extraction
    extractor = StructuredFieldExtractor()
    
    sample_text = """
    BANK STATEMENT
    Account Holder: John Doe
    Account Number: 1234567890
    Bank: Global Bank Ltd
    Statement Period: 01/01/2024 - 31/01/2024
    Transaction ID: TXN-2024-001
    Amount: $5,000.00
    """
    
    result = extractor.extract_fields(sample_text, "statement")
    print("\nExtracted Fields:")
    print(json.dumps(result['extracted_fields'], indent=2))

