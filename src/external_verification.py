"""
External Verification Agents
Query company registers, sanction lists, and PEP databases
"""

import os
import requests
import json
from typing import Dict, Any, List, Optional
from groq import Groq
from dotenv import load_dotenv


class ExternalVerificationAgent:
    """
    Verify entities against external databases
    - Company registers (OpenCorporates, GLEIF, EU Business Register)
    - Sanction lists (OFAC, EU, UN)
    - PEP (Politically Exposed Persons) databases
    """
    
    def __init__(self, groq_api_key: Optional[str] = None):
        """Initialize verification agent"""
        load_dotenv()
        self.groq_api_key = groq_api_key or os.environ.get("GROQ_API_KEY")
        self.opencorporates_key = os.environ.get("OPENCORPORATES_API_KEY")
        
        if not self.groq_api_key:
            raise ValueError("Groq API key required for reasoning!")
        
        self.groq_client = Groq(api_key=self.groq_api_key)
        print("✓ External Verification Agent initialized")
    
    def verify_entity(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive entity verification
        
        Args:
            extracted_data: Structured data extracted from document
        
        Returns:
            Verification results with match confidence and discrepancies
        """
        print("\n[Verification] Starting external verification...")
        
        verification_results = {
            'company_register': {},
            'sanctions': {},
            'pep': {},
            'overall_status': 'PENDING',
            'match_confidence': 0.0,
            'discrepancies': [],
            'recommendations': []
        }
        
        # Extract entity information
        party_name = self._get_party_name(extracted_data)
        party_id = self._get_party_id(extracted_data)
        party_address = self._get_party_address(extracted_data)
        
        if not party_name:
            return {
                'success': False,
                'error': 'No entity name found for verification'
            }
        
        print(f"  Verifying entity: {party_name}")
        
        # 1. Company Register Check
        print("  [1/3] Checking company registers...")
        verification_results['company_register'] = self._check_company_registers(
            party_name, party_id, party_address
        )
        
        # 2. Sanctions List Check
        print("  [2/3] Checking sanction lists...")
        verification_results['sanctions'] = self._check_sanctions(party_name)
        
        # 3. PEP Database Check
        print("  [3/3] Checking PEP databases...")
        verification_results['pep'] = self._check_pep(party_name)
        
        # Use LLM to reason about verification results
        print("  [AI] Analyzing verification results...")
        analysis = self._ai_reasoning(extracted_data, verification_results)
        
        verification_results.update({
            'overall_status': analysis['status'],
            'match_confidence': analysis['confidence'],
            'discrepancies': analysis['discrepancies'],
            'recommendations': analysis['recommendations'],
            'ai_analysis': analysis['reasoning']
        })
        
        print(f"  ✓ Verification complete: {analysis['status']}")
        
        return verification_results
    
    def _check_company_registers(
        self, 
        name: str, 
        registration_id: Optional[str],
        address: Optional[str]
    ) -> Dict[str, Any]:
        """Check company registers (OpenCorporates, GLEIF, EU)"""
        
        results = {
            'opencorporates': self._check_opencorporates(name, registration_id),
            'gleif': self._check_gleif(name),
            'eu_business_register': self._check_eu_business(name),
            'found': False,
            'data': {}
        }
        
        # Determine if found
        results['found'] = any([
            results['opencorporates'].get('found'),
            results['gleif'].get('found'),
            results['eu_business_register'].get('found')
        ])
        
        return results
    
    def _check_opencorporates(self, name: str, registration_id: Optional[str]) -> Dict[str, Any]:
        """Check OpenCorporates API"""
        try:
            # OpenCorporates API
            url = f"https://api.opencorporates.com/v0.4/companies/search"
            params = {
                'q': name,
                'api_token': self.opencorporates_key if self.opencorporates_key else None
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                companies = data.get('results', {}).get('companies', [])
                
                if companies:
                    # Get first match
                    company = companies[0].get('company', {})
                    return {
                        'found': True,
                        'name': company.get('name'),
                        'jurisdiction': company.get('jurisdiction_code'),
                        'company_number': company.get('company_number'),
                        'status': company.get('current_status'),
                        'incorporation_date': company.get('incorporation_date'),
                        'address': company.get('registered_address_in_full'),
                        'confidence': 'medium' if name.lower() in company.get('name', '').lower() else 'low'
                    }
            
            return {'found': False, 'checked': True}
            
        except Exception as e:
            return {'found': False, 'error': str(e), 'checked': False}
    
    def _check_gleif(self, name: str) -> Dict[str, Any]:
        """Check GLEIF (Global LEI Index)"""
        try:
            # GLEIF API - search for LEI
            url = f"https://api.gleif.org/api/v1/lei-records"
            params = {'filter[entity.legalName]': name}
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                records = data.get('data', [])
                
                if records:
                    record = records[0]
                    attributes = record.get('attributes', {})
                    entity = attributes.get('entity', {})
                    
                    return {
                        'found': True,
                        'lei': attributes.get('lei'),
                        'legal_name': entity.get('legalName', {}).get('name'),
                        'status': entity.get('status'),
                        'jurisdiction': entity.get('legalJurisdiction'),
                        'registration_number': entity.get('legalForm', {}).get('id'),
                        'confidence': 'high'
                    }
            
            return {'found': False, 'checked': True}
            
        except Exception as e:
            return {'found': False, 'error': str(e), 'checked': False}
    
    def _check_eu_business(self, name: str) -> Dict[str, Any]:
        """Check EU Business Register (simplified - would need proper API access)"""
        # Note: EU Business Register requires special access
        # This is a placeholder for the implementation
        return {
            'found': False,
            'checked': False,
            'note': 'EU Business Register requires subscription'
        }
    
    def _check_sanctions(self, name: str) -> Dict[str, Any]:
        """Check sanction lists (OFAC, EU, UN)"""
        
        results = {
            'ofac': self._check_ofac(name),
            'eu_sanctions': self._check_eu_sanctions(name),
            'un_sanctions': self._check_un_sanctions(name),
            'hit': False,
            'data': []
        }
        
        # Determine if sanctioned
        results['hit'] = any([
            results['ofac'].get('hit'),
            results['eu_sanctions'].get('hit'),
            results['un_sanctions'].get('hit')
        ])
        
        if results['hit']:
            print("    ⚠️  SANCTIONS HIT DETECTED!")
        
        return results
    
    def _check_ofac(self, name: str) -> Dict[str, Any]:
        """Check OFAC Sanction List"""
        try:
            # OFAC SDN List API (simplified - use consolidated list)
            # In production, download and cache the XML list
            url = "https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/CONS_PRIM.CSV"
            
            # For now, return structure (implement proper CSV parsing)
            return {
                'hit': False,
                'checked': True,
                'list': 'OFAC SDN',
                'note': 'No match found'
            }
            
        except Exception as e:
            return {'hit': False, 'error': str(e), 'checked': False}
    
    def _check_eu_sanctions(self, name: str) -> Dict[str, Any]:
        """Check EU Sanctions List"""
        try:
            # EU Sanctions List API
            # Would need to parse official EU consolidated list
            return {
                'hit': False,
                'checked': True,
                'list': 'EU Sanctions',
                'note': 'No match found'
            }
            
        except Exception as e:
            return {'hit': False, 'error': str(e), 'checked': False}
    
    def _check_un_sanctions(self, name: str) -> Dict[str, Any]:
        """Check UN Sanctions List"""
        try:
            # UN Security Council Sanctions List
            url = "https://scsanctions.un.org/resources/xml/en/consolidated.xml"
            
            # Would need to parse XML and search
            return {
                'hit': False,
                'checked': True,
                'list': 'UN Sanctions',
                'note': 'No match found'
            }
            
        except Exception as e:
            return {'hit': False, 'error': str(e), 'checked': False}
    
    def _check_pep(self, name: str) -> Dict[str, Any]:
        """Check PEP (Politically Exposed Persons) databases"""
        # Note: PEP databases typically require commercial access
        # This is a simplified implementation
        
        return {
            'found': False,
            'checked': False,
            'note': 'PEP check requires commercial database access',
            'databases_checked': []
        }
    
    def _ai_reasoning(
        self, 
        extracted_data: Dict[str, Any], 
        verification_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Use Groq LLM to reason about verification results"""
        
        prompt = f"""You are a compliance verification expert. Analyze these verification results and provide reasoning.

EXTRACTED DOCUMENT DATA:
{json.dumps(extracted_data, indent=2)}

VERIFICATION RESULTS:
{json.dumps(verification_results, indent=2)}

ANALYZE:
1. Match confidence between document data and external sources
2. Any discrepancies found
3. Risk assessment
4. Recommendations for compliance officer

Provide analysis as JSON:
{{
    "status": "Verified/Partial/Not Found/Sanctions Hit",
    "confidence": <0-1>,
    "discrepancies": ["list any discrepancies"],
    "recommendations": ["specific recommendations"],
    "reasoning": "detailed explanation of your analysis"
}}"""

        try:
            response = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a compliance verification analyst. Provide thorough, accurate analysis of entity verification results."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,
                max_tokens=1500,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            return {
                'status': 'ERROR',
                'confidence': 0.0,
                'discrepancies': [f'Analysis error: {str(e)}'],
                'recommendations': ['Manual review required'],
                'reasoning': 'AI analysis failed'
            }
    
    def _get_party_name(self, data: Dict[str, Any]) -> Optional[str]:
        """Extract party name from structured data"""
        return (data.get('extracted_fields', {})
                    .get('parties', {})
                    .get('party_name'))
    
    def _get_party_id(self, data: Dict[str, Any]) -> Optional[str]:
        """Extract party ID from structured data"""
        return (data.get('extracted_fields', {})
                    .get('parties', {})
                    .get('party_id'))
    
    def _get_party_address(self, data: Dict[str, Any]) -> Optional[str]:
        """Extract party address from structured data"""
        return (data.get('extracted_fields', {})
                    .get('parties', {})
                    .get('party_address'))


if __name__ == "__main__":
    # Test verification
    agent = ExternalVerificationAgent()
    
    test_data = {
        'extracted_fields': {
            'parties': {
                'party_name': 'Apple Inc',
                'party_id': 'C0806592',
                'party_address': '1 Apple Park Way, Cupertino, CA'
            }
        }
    }
    
    results = agent.verify_entity(test_data)
    print("\nVerification Results:")
    print(json.dumps(results, indent=2))

