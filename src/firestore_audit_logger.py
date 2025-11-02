"""
Firestore Audit Trail Logger
Comprehensive logging system for tracking all actions, analyses, and decisions
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import traceback
from functools import wraps

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    print("Warning: firebase-admin not installed. Install with: pip install firebase-admin")

from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class FirestoreAuditLogger:
    """
    Comprehensive audit trail logger using Firestore
    Tracks all actions, agents, inputs, outputs, and errors
    """
    
    def __init__(
        self,
        credentials_path: Optional[str] = None,
        fallback_to_local: bool = True
    ):
        """
        Initialize Firestore audit logger
        
        Args:
            credentials_path: Path to Firebase credentials JSON
            fallback_to_local: If True, falls back to local JSON logging if Firebase unavailable
        """
        load_dotenv()
        
        self.credentials_path = credentials_path or os.getenv('FIREBASE_CREDENTIALS_PATH')
        self.fallback_to_local = fallback_to_local
        self.db = None
        self.firebase_enabled = False
        
        # Local fallback
        self.local_log_dir = Path("data/logs/audit_trail")
        self.local_log_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize Firebase if available
        if FIREBASE_AVAILABLE and self.credentials_path:
            try:
                self._initialize_firebase()
                self.firebase_enabled = True
                logger.info("Firestore audit logger initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Firebase: {e}")
                if fallback_to_local:
                    logger.info("Falling back to local JSON logging")
        else:
            if not FIREBASE_AVAILABLE:
                logger.warning("Firebase SDK not available - using local logging only")
            elif not self.credentials_path:
                logger.warning("Firebase credentials not provided - using local logging only")
        
        # Session tracking
        self.session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK"""
        if not firebase_admin._apps:
            cred = credentials.Certificate(self.credentials_path)
            firebase_admin.initialize_app(cred)
        
        self.db = firestore.client()
        logger.info("Firebase initialized successfully")
    
    def log_action(
        self,
        action_type: str,
        agent: str,
        input_data: Any,
        output_data: Any,
        status: str = "success",
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        document_id: Optional[str] = None
    ) -> str:
        """
        Log an action to audit trail
        
        Args:
            action_type: Type of action (e.g., 'document_parse', 'image_analysis', 'validation')
            agent: Agent/component performing action (e.g., 'ai_fraud_detector', 'image_analyzer')
            input_data: Input parameters and data
            output_data: Output results and decisions
            status: Action status ('success', 'error', 'warning')
            error: Error message if applicable
            metadata: Additional metadata
            document_id: Optional document identifier
        
        Returns:
            Log entry ID
        """
        timestamp = datetime.now()
        
        log_entry = {
            'session_id': self.session_id,
            'timestamp': timestamp.isoformat(),
            'timestamp_unix': timestamp.timestamp(),
            'action_type': action_type,
            'agent': agent,
            'status': status,
            'input': self._sanitize_data(input_data),
            'output': self._sanitize_data(output_data),
            'error': error,
            'metadata': metadata or {},
            'document_id': document_id
        }
        
        # Generate entry ID
        entry_id = f"{self.session_id}_{action_type}_{timestamp.strftime('%H%M%S%f')}"
        
        # Log to Firestore
        if self.firebase_enabled:
            try:
                self._log_to_firestore(entry_id, log_entry)
            except Exception as e:
                logger.error(f"Failed to log to Firestore: {e}")
                if self.fallback_to_local:
                    self._log_to_local(entry_id, log_entry)
        else:
            # Fallback to local logging
            if self.fallback_to_local:
                self._log_to_local(entry_id, log_entry)
        
        return entry_id
    
    def _log_to_firestore(self, entry_id: str, log_entry: Dict[str, Any]):
        """Log entry to Firestore"""
        doc_ref = self.db.collection('audit_trail').document(entry_id)
        doc_ref.set(log_entry)
        logger.debug(f"Logged to Firestore: {entry_id}")
    
    def _log_to_local(self, entry_id: str, log_entry: Dict[str, Any]):
        """Log entry to local JSON file"""
        log_file = self.local_log_dir / f"{self.session_id}.jsonl"
        
        with open(log_file, 'a', encoding='utf-8') as f:
            json.dump({**log_entry, 'entry_id': entry_id}, f)
            f.write('\n')
        
        logger.debug(f"Logged to local file: {log_file.name}")
    
    def log_document_analysis_start(
        self,
        document_path: str,
        document_type: str,
        analysis_config: Dict[str, Any]
    ) -> str:
        """Log start of document analysis"""
        return self.log_action(
            action_type='document_analysis_start',
            agent='system',
            input_data={
                'document_path': document_path,
                'document_type': document_type,
                'config': analysis_config
            },
            output_data={},
            status='started',
            metadata={
                'file_name': Path(document_path).name,
                'file_size': Path(document_path).stat().st_size
            }
        )
    
    def log_document_analysis_complete(
        self,
        document_path: str,
        analysis_results: Dict[str, Any],
        duration_seconds: float
    ) -> str:
        """Log completion of document analysis"""
        return self.log_action(
            action_type='document_analysis_complete',
            agent='system',
            input_data={'document_path': document_path},
            output_data=analysis_results,
            status='success',
            metadata={
                'duration_seconds': duration_seconds,
                'file_name': Path(document_path).name
            }
        )
    
    def log_parsing(
        self,
        parser_name: str,
        file_path: str,
        text_extracted: str,
        metadata_extracted: Dict[str, Any],
        success: bool = True,
        error: Optional[str] = None
    ) -> str:
        """Log document parsing"""
        return self.log_action(
            action_type='document_parsing',
            agent=parser_name,
            input_data={
                'file_path': file_path,
                'file_name': Path(file_path).name
            },
            output_data={
                'text_length': len(text_extracted),
                'text_preview': text_extracted[:500] if text_extracted else '',
                'metadata': metadata_extracted,
                'success': success
            },
            status='success' if success else 'error',
            error=error
        )
    
    def log_image_analysis(
        self,
        analyzer_name: str,
        image_path: str,
        analysis_results: Dict[str, Any],
        checks_performed: List[str]
    ) -> str:
        """Log image analysis"""
        return self.log_action(
            action_type='image_analysis',
            agent=analyzer_name,
            input_data={
                'image_path': image_path,
                'checks_performed': checks_performed
            },
            output_data=analysis_results,
            status='success',
            metadata={
                'image_name': Path(image_path).name,
                'total_checks': len(checks_performed)
            }
        )
    
    def log_validation(
        self,
        validator_name: str,
        document_text: str,
        validation_results: Dict[str, Any]
    ) -> str:
        """Log document validation"""
        return self.log_action(
            action_type='document_validation',
            agent=validator_name,
            input_data={
                'text_length': len(document_text),
                'text_preview': document_text[:300]
            },
            output_data=validation_results,
            status='success',
            metadata={
                'total_issues': sum([
                    len(validation_results.get('formatting_issues', [])),
                    len(validation_results.get('content_issues', [])),
                    len(validation_results.get('structure_issues', []))
                ]),
                'completeness_score': validation_results.get('completeness_score', 0),
                'accuracy_score': validation_results.get('accuracy_score', 0)
            }
        )
    
    def log_ai_analysis(
        self,
        model_name: str,
        input_prompt: str,
        output_analysis: Dict[str, Any],
        tokens_used: Optional[int] = None
    ) -> str:
        """Log AI model analysis"""
        return self.log_action(
            action_type='ai_analysis',
            agent=f'ai_model:{model_name}',
            input_data={
                'prompt_length': len(input_prompt),
                'prompt_preview': input_prompt[:500]
            },
            output_data=output_analysis,
            status='success',
            metadata={
                'model': model_name,
                'tokens_used': tokens_used,
                'risk_score': output_analysis.get('risk_score'),
                'risk_level': output_analysis.get('risk_level')
            }
        )
    
    def log_external_verification(
        self,
        verification_type: str,
        query_data: Dict[str, Any],
        verification_results: Dict[str, Any]
    ) -> str:
        """Log external verification (e.g., company registers, sanctions)"""
        return self.log_action(
            action_type='external_verification',
            agent=f'external_api:{verification_type}',
            input_data=query_data,
            output_data=verification_results,
            status='success',
            metadata={
                'verification_type': verification_type
            }
        )
    
    def log_error(
        self,
        component: str,
        error_message: str,
        error_traceback: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log error"""
        return self.log_action(
            action_type='error',
            agent=component,
            input_data=context or {},
            output_data={},
            status='error',
            error=error_message,
            metadata={
                'traceback': error_traceback,
                'error_type': type(error_message).__name__
            }
        )
    
    def log_decision(
        self,
        decision_type: str,
        decision_maker: str,
        decision: str,
        reasoning: str,
        confidence: float,
        factors: List[str]
    ) -> str:
        """Log decision made by system"""
        return self.log_action(
            action_type='decision',
            agent=decision_maker,
            input_data={
                'factors': factors
            },
            output_data={
                'decision': decision,
                'reasoning': reasoning,
                'confidence': confidence
            },
            status='success',
            metadata={
                'decision_type': decision_type,
                'total_factors': len(factors)
            }
        )
    
    def _sanitize_data(self, data: Any) -> Any:
        """
        Sanitize data for logging (handle non-serializable types)
        """
        if data is None:
            return None
        
        if isinstance(data, (str, int, float, bool)):
            return data
        
        if isinstance(data, dict):
            return {k: self._sanitize_data(v) for k, v in data.items()}
        
        if isinstance(data, (list, tuple)):
            return [self._sanitize_data(item) for item in data]
        
        if isinstance(data, datetime):
            return data.isoformat()
        
        if isinstance(data, Path):
            return str(data)
        
        # Convert other types to string
        try:
            return str(data)
        except:
            return f"<{type(data).__name__}>"
    
    def get_session_logs(self, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve logs for a session
        
        Args:
            session_id: Session ID (defaults to current session)
        
        Returns:
            List of log entries
        """
        session_id = session_id or self.session_id
        
        if self.firebase_enabled:
            try:
                docs = self.db.collection('audit_trail')\
                    .where('session_id', '==', session_id)\
                    .order_by('timestamp_unix')\
                    .stream()
                
                return [doc.to_dict() for doc in docs]
            except Exception as e:
                logger.error(f"Failed to retrieve from Firestore: {e}")
        
        # Fallback to local
        return self._get_local_session_logs(session_id)
    
    def _get_local_session_logs(self, session_id: str) -> List[Dict[str, Any]]:
        """Retrieve logs from local file"""
        log_file = self.local_log_dir / f"{session_id}.jsonl"
        
        if not log_file.exists():
            return []
        
        logs = []
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    logs.append(json.loads(line))
                except:
                    pass
        
        return logs
    
    def generate_audit_report(
        self,
        session_id: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> str:
        """
        Generate human-readable audit report
        
        Args:
            session_id: Session ID (defaults to current session)
            output_path: Optional path to save report
        
        Returns:
            Report as string
        """
        logs = self.get_session_logs(session_id)
        
        if not logs:
            return "No logs found for session"
        
        lines = []
        lines.append("="*80)
        lines.append("AUDIT TRAIL REPORT")
        lines.append("="*80)
        lines.append(f"Session ID: {session_id or self.session_id}")
        lines.append(f"Total Actions: {len(logs)}")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        # Group by action type
        action_types = {}
        for log in logs:
            action_type = log.get('action_type', 'unknown')
            if action_type not in action_types:
                action_types[action_type] = []
            action_types[action_type].append(log)
        
        lines.append("ACTION SUMMARY")
        lines.append("-"*80)
        for action_type, entries in action_types.items():
            lines.append(f"  {action_type}: {len(entries)} action(s)")
        lines.append("")
        
        # Detailed log
        lines.append("DETAILED LOG")
        lines.append("-"*80)
        
        for i, log in enumerate(logs, 1):
            lines.append(f"\n[{i}] {log.get('timestamp', 'unknown')}")
            lines.append(f"    Action: {log.get('action_type', 'unknown')}")
            lines.append(f"    Agent: {log.get('agent', 'unknown')}")
            lines.append(f"    Status: {log.get('status', 'unknown')}")
            
            if log.get('error'):
                lines.append(f"    Error: {log['error']}")
            
            if log.get('metadata'):
                lines.append(f"    Metadata: {json.dumps(log['metadata'], indent=6)}")
        
        lines.append("\n" + "="*80)
        
        report = "\n".join(lines)
        
        # Save if output path provided
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"Audit report saved to: {output_path}")
        
        return report


def audit_trail(action_type: str, agent: str):
    """
    Decorator for automatic audit trail logging
    
    Usage:
        @audit_trail('document_parsing', 'pdf_parser')
        def parse_document(file_path):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get logger instance (assumes global audit_logger exists)
            try:
                from src.firestore_audit_logger import audit_logger
            except:
                audit_logger = None
            
            if not audit_logger:
                # No logger available, just run function
                return func(*args, **kwargs)
            
            start_time = datetime.now()
            
            try:
                # Execute function
                result = func(*args, **kwargs)
                
                # Log success
                duration = (datetime.now() - start_time).total_seconds()
                audit_logger.log_action(
                    action_type=action_type,
                    agent=agent,
                    input_data={'args': args, 'kwargs': kwargs},
                    output_data={'result': result},
                    status='success',
                    metadata={'duration_seconds': duration}
                )
                
                return result
                
            except Exception as e:
                # Log error
                duration = (datetime.now() - start_time).total_seconds()
                audit_logger.log_error(
                    component=agent,
                    error_message=str(e),
                    error_traceback=traceback.format_exc(),
                    context={
                        'action_type': action_type,
                        'args': str(args),
                        'kwargs': str(kwargs),
                        'duration_seconds': duration
                    }
                )
                raise
        
        return wrapper
    return decorator


# Global audit logger instance (initialized when needed)
audit_logger = None

def get_audit_logger() -> FirestoreAuditLogger:
    """Get global audit logger instance"""
    global audit_logger
    if audit_logger is None:
        audit_logger = FirestoreAuditLogger()
    return audit_logger


if __name__ == "__main__":
    # Test the audit logger
    logging.basicConfig(level=logging.INFO)
    
    logger = FirestoreAuditLogger(fallback_to_local=True)
    
    # Test logging various actions
    logger.log_action(
        action_type='test_action',
        agent='test_agent',
        input_data={'test': 'input'},
        output_data={'test': 'output'},
        status='success'
    )
    
    logger.log_error(
        component='test_component',
        error_message='Test error',
        error_traceback='Test traceback'
    )
    
    # Generate report
    report = logger.generate_audit_report()
    print(report)

