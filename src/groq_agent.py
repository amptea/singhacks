"""
Groq AI Agent for Intelligent Fraud Detection Analysis
Uses Groq's LLM API to provide AI-powered document analysis and reporting
"""

import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from groq import Groq


class FraudDetectionAgent:
    """
    AI Agent powered by Groq for intelligent fraud detection analysis
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "llama-3.3-70b-versatile"):
        """
        Initialize the Groq AI agent
        
        Args:
            api_key: Groq API key (or set GROQ_API_KEY env variable)
            model: Groq model to use (default: llama-3.3-70b-versatile)
        """
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Groq API key required. Set GROQ_API_KEY environment variable or pass api_key parameter.\n"
                "Get your API key at: https://console.groq.com/keys"
            )
        
        self.client = Groq(api_key=self.api_key)
        self.model = model
        self.conversation_history = []
    
    def analyze_document_fraud(
        self,
        document_data: Dict[str, Any],
        format_validation: Dict[str, Any],
        image_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Use AI to analyze all fraud detection data and provide intelligent insights
        
        Args:
            document_data: Processed document data
            format_validation: Format validation results
            image_analysis: Image analysis results
        
        Returns:
            AI-powered analysis with insights and recommendations
        """
        print("\n🤖 Groq AI Agent analyzing fraud indicators...")
        
        # Prepare analysis context for the AI
        context = self._prepare_analysis_context(
            document_data, format_validation, image_analysis
        )
        
        # Get AI analysis
        analysis = self._get_ai_analysis(context)
        
        # Get risk assessment from AI
        risk_assessment = self._get_ai_risk_assessment(context, analysis)
        
        # Get detailed recommendations from AI
        recommendations = self._get_ai_recommendations(context, analysis, risk_assessment)
        
        # Compile results
        ai_results = {
            'agent_timestamp': datetime.now().isoformat(),
            'model_used': self.model,
            'document_name': document_data.get('file_name'),
            'ai_analysis': analysis,
            'ai_risk_assessment': risk_assessment,
            'ai_recommendations': recommendations,
            'confidence_score': self._calculate_ai_confidence(analysis)
        }
        
        return ai_results
    
    def generate_executive_report(
        self,
        document_data: Dict[str, Any],
        format_validation: Dict[str, Any],
        image_analysis: Dict[str, Any],
        ai_analysis: Dict[str, Any]
    ) -> str:
        """
        Generate an executive-level report using AI
        
        Args:
            document_data: Processed document data
            format_validation: Format validation results
            image_analysis: Image analysis results
            ai_analysis: AI analysis results
        
        Returns:
            Formatted executive report
        """
        print("\n📝 Generating AI-powered executive report...")
        
        prompt = self._create_report_prompt(
            document_data, format_validation, image_analysis, ai_analysis
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert fraud detection analyst creating executive reports. 
                        Generate a clear, professional report that:
                        1. Summarizes key findings concisely
                        2. Highlights critical fraud indicators
                        3. Provides clear risk assessment
                        4. Gives actionable recommendations
                        5. Uses professional language suitable for compliance officers
                        
                        Format the report in a structured, easy-to-read manner."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Lower temperature for consistent, factual output
                max_tokens=2000
            )
            
            report = response.choices[0].message.content
            return report
            
        except Exception as e:
            return f"Error generating executive report: {str(e)}"
    
    def generate_detailed_narrative(
        self,
        document_data: Dict[str, Any],
        format_validation: Dict[str, Any],
        image_analysis: Dict[str, Any],
        ai_analysis: Dict[str, Any]
    ) -> str:
        """
        Generate a detailed narrative analysis using AI
        
        Args:
            document_data: Processed document data
            format_validation: Format validation results
            image_analysis: Image analysis results
            ai_analysis: AI analysis results
        
        Returns:
            Detailed narrative analysis
        """
        print("\n📖 Generating detailed AI narrative analysis...")
        
        prompt = f"""Based on the fraud detection analysis below, provide a detailed narrative explanation 
        of the findings. Explain each issue in context and what it might indicate about document authenticity.

        Document: {document_data.get('file_name')}
        
        Format Issues Found: {len(format_validation.get('issues_found', []))}
        Image Fraud Indicators: {len(image_analysis.get('fraud_indicators', []))}
        
        Format Validation Details:
        {json.dumps(format_validation.get('issues_found', [])[:5], indent=2)}
        
        Image Analysis Details:
        {json.dumps(image_analysis.get('fraud_indicators', []), indent=2)}
        
        AI Risk Assessment:
        {json.dumps(ai_analysis.get('ai_risk_assessment', {}), indent=2)}
        
        Provide a thorough, expert-level narrative analysis."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """You are a forensic document analyst providing detailed narrative analysis. 
                        Explain findings in clear, professional language. Connect individual indicators to 
                        broader patterns. Provide context for why certain findings are significant."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.4,
                max_tokens=3000
            )
            
            narrative = response.choices[0].message.content
            return narrative
            
        except Exception as e:
            return f"Error generating narrative analysis: {str(e)}"
    
    def _prepare_analysis_context(
        self,
        document_data: Dict[str, Any],
        format_validation: Dict[str, Any],
        image_analysis: Dict[str, Any]
    ) -> str:
        """Prepare context for AI analysis"""
        
        # Extract key information
        doc_name = document_data.get('file_name', 'Unknown')
        total_pages = document_data.get('content', {}).get('total_pages', 0)
        text_length = len(document_data.get('content', {}).get('text', ''))
        
        format_risk = format_validation.get('overall_risk', 0)
        format_issues = format_validation.get('issues_found', [])
        format_warnings = format_validation.get('warnings', [])
        
        image_risk = image_analysis.get('overall_image_risk', 0)
        fraud_indicators = image_analysis.get('fraud_indicators', [])
        
        # Create comprehensive context
        context = f"""
DOCUMENT FRAUD DETECTION ANALYSIS

Document Information:
- File Name: {doc_name}
- Total Pages: {total_pages}
- Text Extracted: {text_length} characters
- Total Images: {image_analysis.get('total_images', 0)}

FORMAT VALIDATION RESULTS:
- Overall Risk Score: {format_risk}/10
- Issues Found: {len(format_issues)}
- Warnings: {len(format_warnings)}

Critical Format Issues:
{json.dumps([i for i in format_issues if i.get('severity', 0) >= 6], indent=2)}

IMAGE ANALYSIS RESULTS:
- Overall Image Risk: {image_risk}/10
- Fraud Indicators Detected: {len(fraud_indicators)}

Fraud Indicators:
{json.dumps(fraud_indicators, indent=2)}

Quality Metrics:
{json.dumps(document_data.get('quality_metrics', {}), indent=2)}
"""
        return context
    
    def _get_ai_analysis(self, context: str) -> Dict[str, Any]:
        """Get AI-powered analysis of the fraud indicators"""
        
        prompt = f"""Analyze this document fraud detection data and provide expert insights:

{context}

Provide your analysis as a JSON object with the following structure:
{{
    "overall_assessment": "Brief overall assessment of document authenticity",
    "key_findings": ["List of most significant findings"],
    "fraud_likelihood": "LOW/MEDIUM/HIGH/CRITICAL",
    "reasoning": "Detailed reasoning for the assessment",
    "patterns_detected": ["List any patterns that suggest fraud or manipulation"],
    "authenticity_indicators": ["List indicators that suggest authenticity"],
    "concerns": ["List specific concerns that need attention"]
}}"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert fraud detection analyst. Analyze document fraud 
                        indicators and provide professional insights. Be thorough but concise. Focus on 
                        the most significant indicators. Output valid JSON only."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=1500,
                response_format={"type": "json_object"}
            )
            
            analysis_text = response.choices[0].message.content
            analysis = json.loads(analysis_text)
            
            return analysis
            
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return {
                "overall_assessment": "Analysis completed with parsing issues",
                "key_findings": ["AI analysis available but formatting error occurred"],
                "fraud_likelihood": "UNKNOWN",
                "reasoning": analysis_text if 'analysis_text' in locals() else "Error in analysis"
            }
        except Exception as e:
            return {
                "overall_assessment": f"Error during AI analysis: {str(e)}",
                "key_findings": [],
                "fraud_likelihood": "UNKNOWN",
                "reasoning": str(e)
            }
    
    def _get_ai_risk_assessment(
        self,
        context: str,
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get detailed risk assessment from AI"""
        
        prompt = f"""Based on this fraud detection analysis, provide a detailed risk assessment:

{context}

Previous Analysis:
{json.dumps(analysis, indent=2)}

Provide risk assessment as JSON:
{{
    "risk_score": <number 0-10>,
    "risk_level": "MINIMAL/LOW/MEDIUM/HIGH/CRITICAL",
    "confidence": <number 0-1>,
    "primary_concerns": ["List of main concerns"],
    "risk_factors": {{
        "format_manipulation": <0-10>,
        "image_authenticity": <0-10>,
        "metadata_consistency": <0-10>,
        "content_integrity": <0-10>
    }},
    "action_required": true/false,
    "severity_justification": "Explain the risk level determination"
}}"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """You are a risk assessment specialist. Provide accurate, data-driven 
                        risk assessments for document fraud. Be conservative in your assessments - it's 
                        better to flag a legitimate document for review than miss fraud. Output valid JSON only."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,  # Very low temperature for consistent risk assessment
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            
            risk_text = response.choices[0].message.content
            risk_assessment = json.loads(risk_text)
            
            return risk_assessment
            
        except Exception as e:
            # Fallback risk assessment
            return {
                "risk_score": 5.0,
                "risk_level": "MEDIUM",
                "confidence": 0.5,
                "primary_concerns": [f"AI risk assessment error: {str(e)}"],
                "action_required": True,
                "severity_justification": "Unable to complete AI risk assessment"
            }
    
    def _get_ai_recommendations(
        self,
        context: str,
        analysis: Dict[str, Any],
        risk_assessment: Dict[str, Any]
    ) -> List[str]:
        """Get actionable recommendations from AI"""
        
        prompt = f"""Based on this fraud detection analysis, provide specific, actionable recommendations:

Risk Level: {risk_assessment.get('risk_level', 'UNKNOWN')}
Risk Score: {risk_assessment.get('risk_score', 0)}/10

Analysis Summary:
{json.dumps(analysis, indent=2)}

Primary Concerns:
{json.dumps(risk_assessment.get('primary_concerns', []), indent=2)}

Provide 5-7 specific, actionable recommendations as a JSON array of strings.
Focus on practical next steps for compliance officers."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """You are a compliance advisor. Provide clear, actionable recommendations 
                        for handling potentially fraudulent documents. Be specific and practical. Output a 
                        JSON array of recommendation strings."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.4,
                max_tokens=800,
                response_format={"type": "json_object"}
            )
            
            rec_text = response.choices[0].message.content
            rec_data = json.loads(rec_text)
            
            # Handle different possible response structures
            if isinstance(rec_data, list):
                return rec_data
            elif isinstance(rec_data, dict):
                # Try to extract recommendations from dict
                for key in ['recommendations', 'actions', 'steps', 'advice']:
                    if key in rec_data and isinstance(rec_data[key], list):
                        return rec_data[key]
                # If dict but no list found, convert values to list
                return [str(v) for v in rec_data.values() if v]
            
            return ["Review AI-generated recommendations in raw format"]
            
        except Exception as e:
            return [
                "Manual review required due to AI processing error",
                "Verify document authenticity through alternative means",
                f"AI recommendation error: {str(e)}"
            ]
    
    def _calculate_ai_confidence(self, analysis: Dict[str, Any]) -> float:
        """Calculate confidence in AI analysis"""
        # Base confidence on completeness of analysis
        confidence = 0.7  # Base confidence
        
        if analysis.get('key_findings'):
            confidence += 0.1
        if analysis.get('reasoning'):
            confidence += 0.1
        if analysis.get('patterns_detected'):
            confidence += 0.05
        if analysis.get('authenticity_indicators'):
            confidence += 0.05
        
        return min(confidence, 1.0)
    
    def _create_report_prompt(
        self,
        document_data: Dict[str, Any],
        format_validation: Dict[str, Any],
        image_analysis: Dict[str, Any],
        ai_analysis: Dict[str, Any]
    ) -> str:
        """Create prompt for executive report generation"""
        
        return f"""Generate an executive fraud detection report for the following analysis:

DOCUMENT: {document_data.get('file_name')}

AI ANALYSIS SUMMARY:
{json.dumps(ai_analysis.get('ai_analysis', {}), indent=2)}

RISK ASSESSMENT:
{json.dumps(ai_analysis.get('ai_risk_assessment', {}), indent=2)}

FORMAT VALIDATION:
- Overall Risk: {format_validation.get('overall_risk', 0)}/10
- Issues: {len(format_validation.get('issues_found', []))}
- Critical Issues: {len([i for i in format_validation.get('issues_found', []) if i.get('severity', 0) >= 7])}

IMAGE ANALYSIS:
- Overall Risk: {image_analysis.get('overall_image_risk', 0)}/10
- Fraud Indicators: {len(image_analysis.get('fraud_indicators', []))}

Create a professional executive report with:
1. Executive Summary (2-3 sentences)
2. Risk Level and Score
3. Key Findings (bullet points)
4. Critical Issues (if any)
5. Recommended Actions

Keep it concise but comprehensive. Use clear, professional language."""
    
    def chat_about_document(self, question: str, context: Dict[str, Any]) -> str:
        """
        Interactive chat about the document analysis
        
        Args:
            question: User's question
            context: Analysis context
        
        Returns:
            AI response
        """
        # Add to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": question
        })
        
        # Create system message with context
        system_message = f"""You are an expert fraud detection analyst. Answer questions about this document analysis:

Context: {json.dumps(context, indent=2)[:2000]}  # Limit context size

Provide clear, accurate answers based on the analysis data."""
        
        messages = [{"role": "system", "content": system_message}] + self.conversation_history
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.5,
                max_tokens=500
            )
            
            answer = response.choices[0].message.content
            
            # Add to conversation history
            self.conversation_history.append({
                "role": "assistant",
                "content": answer
            })
            
            return answer
            
        except Exception as e:
            return f"Error in chat: {str(e)}"


# Convenience function for quick analysis
def analyze_with_ai(
    document_data: Dict[str, Any],
    format_validation: Dict[str, Any],
    image_analysis: Dict[str, Any],
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Quick analysis with AI agent
    
    Args:
        document_data: Processed document data
        format_validation: Format validation results
        image_analysis: Image analysis results
        api_key: Optional Groq API key
    
    Returns:
        AI analysis results
    """
    agent = FraudDetectionAgent(api_key=api_key)
    return agent.analyze_document_fraud(document_data, format_validation, image_analysis)


if __name__ == "__main__":
    # Example usage
    print("="*80)
    print("GROQ AI FRAUD DETECTION AGENT")
    print("="*80)
    print("\nThis agent requires a Groq API key.")
    print("Get your free API key at: https://console.groq.com/keys")
    print("\nSet the GROQ_API_KEY environment variable or pass it to the agent.")
    print("\nExample usage:")
    print("""
    from groq_agent import FraudDetectionAgent
    
    agent = FraudDetectionAgent(api_key="your-api-key")
    ai_results = agent.analyze_document_fraud(
        document_data, 
        format_validation, 
        image_analysis
    )
    
    report = agent.generate_executive_report(
        document_data,
        format_validation,
        image_analysis,
        ai_results
    )
    """)

