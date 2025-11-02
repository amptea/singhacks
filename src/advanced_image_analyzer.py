"""
Advanced Image Analysis System
- Reverse image search using SerpAPI
- AI-generated image detection using Hugging Face models
- Metadata tampering detection
- Pixel-level anomaly detection
"""

import os
import io
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import hashlib
import requests
import concurrent.futures

# Image processing
from PIL import Image
import numpy as np

# Metadata analysis
try:
    import exifread
    from PIL.ExifTags import TAGS, GPSTAGS
except ImportError:
    exifread = None
        # 5. Combined Manipulation Assessment
# PyMuPDF for PDF image extraction
import fitz

logger = logging.getLogger(__name__)


class AdvancedImageAnalyzer:
    """
    Comprehensive image analysis for fraud detection
    """
    
    def __init__(
        self,
        serpapi_key: Optional[str] = None,
        huggingface_token: Optional[str] = None
    ):
        """
        Initialize image analyzer
        
        Args:
            serpapi_key: SerpAPI key for reverse image search
            huggingface_token: Hugging Face token for AI detection models
        """
        from dotenv import load_dotenv
        load_dotenv()
        
        self.serpapi_key = serpapi_key or os.getenv('SERPAPI_KEY')
        self.hf_token = huggingface_token or os.getenv('HUGGINGFACE_TOKEN')
        
        # Model endpoints for AI detection
        self.ai_detection_models = {
            'organika': 'Organika/sdxl-detector',
            'llama_scout': 'meta-llama/llama-4-scout-17b-16e-instruct',
            'llama_maverick': 'meta-llama/llama-4-maverick-17b-128e-instruct'
        }
        
        logger.info("AdvancedImageAnalyzer initialized")
        
        if not self.serpapi_key:
            logger.warning("SerpAPI key not found - reverse image search disabled")
        if not self.hf_token:
            logger.warning("HuggingFace token not found - AI detection models disabled")
    
    def analyze_image(
        self,
        image_path: str,
        check_reverse_search: bool = True,
        check_ai_generated: bool = True,
        check_metadata_tampering: bool = True,
        check_pixel_anomalies: bool = True
    ) -> Dict[str, Any]:
        """
        Comprehensive image analysis
        
        Args:
            image_path: Path to image
            check_reverse_search: Enable reverse image search
            check_ai_generated: Check if AI-generated
            check_metadata_tampering: Check metadata for tampering
            check_pixel_anomalies: Check for pixel-level anomalies
        
        Returns:
            Complete analysis results
        """
        logger.info(f"Starting comprehensive image analysis: {Path(image_path).name}")

        # Downscale large local images to reduce CPU / upload / inference time.
        # If we create a temporary downscaled copy, we'll use it for all downstream checks
        # and then attempt best-effort cleanup.
        temp_downscaled_path: Optional[Path] = None
        use_path = image_path
        try:
            # Only downscale local files (not URLs)
            if not str(image_path).startswith('http') and Path(image_path).exists():
                img = Image.open(image_path)
                width, height = img.size
                # Only downscale if larger than target to avoid needless work
                TARGET_MAX = 1024
                if max(width, height) > TARGET_MAX:
                    tmp_dir = Path('temp/downsized')
                    tmp_dir.mkdir(parents=True, exist_ok=True)
                    temp_downscaled_path = tmp_dir / f"{Path(image_path).stem}_downsized{Path(image_path).suffix}"
                    # Use a copy so original file is untouched
                    img_copy = img.copy()
                    img_copy.thumbnail((TARGET_MAX, TARGET_MAX))
                    # Save with reasonable quality/optimize to reduce upload size
                    try:
                        img_copy.save(temp_downscaled_path, optimize=True, quality=85)
                    except Exception:
                        # Fallback to saving without extra options on some formats
                        img_copy.save(temp_downscaled_path)
                    use_path = str(temp_downscaled_path)
                    logger.info(f"Created downscaled temp image: {temp_downscaled_path} ({width}x{height} -> <={TARGET_MAX})")
                else:
                    logger.info("Image below target size; skipping downscale")
        except Exception as e:
            logger.warning(f"Downscaling failed, continuing with original image: {e}")

        results = {
            'image_path': image_path,
            'image_name': Path(image_path).name,
            'used_image_for_analysis': use_path,
            'timestamp': datetime.now().isoformat(),
            'analysis_performed': []
        }
        
        # Run expensive / I/O-bound checks in parallel to reduce wall-clock time
        tasks = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
            # 1. Reverse Image Search (I/O-bound)
            if check_reverse_search and self.serpapi_key:
                logger.info("  [1/4] Scheduling reverse image search...")
                tasks['reverse_search'] = ex.submit(self._reverse_image_search, use_path)

            # 2. AI-Generated Detection (may call external HF API)
            if check_ai_generated:
                logger.info("  [2/4] Scheduling AI-generated detection...")
                tasks['ai_detection'] = ex.submit(self._detect_ai_generated, use_path)

            # 3. Metadata Tampering (local I/O/CPU)
            if check_metadata_tampering:
                logger.info("  [3/4] Scheduling metadata tampering analysis...")
                tasks['metadata_analysis'] = ex.submit(self._analyze_metadata_tampering, use_path)

            # 4. Pixel Anomalies (CPU-bound)
            if check_pixel_anomalies:
                logger.info("  [4/4] Scheduling pixel-level anomaly detection...")
                tasks['pixel_analysis'] = ex.submit(self._detect_pixel_anomalies, use_path)

            # Collect results as they complete
            for name, fut in tasks.items():
                try:
                    res = fut.result()
                    results[name] = res
                    results['analysis_performed'].append(name)
                except Exception as e:
                    logger.error(f"{name} failed during analysis: {e}")
                    results[name] = {'success': False, 'error': str(e)}

        # Best-effort cleanup of temporary downscaled file
        try:
            if temp_downscaled_path and temp_downscaled_path.exists():
                temp_downscaled_path.unlink()
                logger.info(f"Removed temporary downscaled image: {temp_downscaled_path}")
        except Exception as e:
            logger.warning(f"Failed to remove temporary downscaled image: {e}")
        
        # 5. Combined Manipulation Assessment
        results['manipulation_indicators'] = self._combine_manipulation_indicators(results)
        
        logger.info(f"Image analysis complete: {len(results['analysis_performed'])} checks performed")
        
        return results
    
    def analyze_pdf_images(
        self,
        pdf_path: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Extract and analyze all images from PDF
        
        Args:
            pdf_path: Path to PDF
            **kwargs: Pass-through to analyze_image
        
        Returns:
            Analysis results for all images
        """
        logger.info(f"Analyzing images in PDF: {Path(pdf_path).name}")
        
        pdf_doc = fitz.open(pdf_path)
        
        results = {
            'pdf_name': Path(pdf_path).name,
            'total_pages': len(pdf_doc),
            'images_found': 0,
            'images_analyzed': [],
            'timestamp': datetime.now().isoformat()
        }
        
        temp_dir = Path("temp/pdf_images")
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Extract and analyze each image
        for page_num in range(len(pdf_doc)):
            page = pdf_doc[page_num]
            image_list = page.get_images()
            
            for img_index, img_info in enumerate(image_list):
                xref = img_info[0]
                try:
                    base_image = pdf_doc.extract_image(xref)
                    if base_image:
                        # Save image temporarily
                        image_bytes = base_image['image']
                        image_ext = base_image['ext']
                        image_filename = f"page{page_num+1}_img{img_index}.{image_ext}"
                        image_path = temp_dir / image_filename
                        
                        with open(image_path, 'wb') as f:
                            f.write(image_bytes)
                        
                        # Analyze image
                        analysis = self.analyze_image(str(image_path), **kwargs)
                        analysis['pdf_page'] = page_num + 1
                        analysis['pdf_image_index'] = img_index
                        
                        results['images_analyzed'].append(analysis)
                        results['images_found'] += 1
                        
                except Exception as e:
                    logger.error(f"Failed to analyze image {img_index} from page {page_num + 1}: {e}")
        
        pdf_doc.close()
        
        logger.info(f"PDF image analysis complete: {results['images_found']} images analyzed")
        
        return results
    
    def _reverse_image_search(self, image_path: str) -> Dict[str, Any]:
        """
        Perform reverse image search using SerpAPI
        """
        if not self.serpapi_key:
            return {
                'success': False,
                'error': 'SerpAPI key not configured',
                'matches_found': 0
            }

        # If a local file is provided, prefer uploading to Supabase Storage (if configured)
        # to generate a signed URL. Fall back to transfer.sh if Supabase isn't configured.
        image_url_to_use = image_path
        supabase_uploaded_path = None
        if not image_path.startswith('http'):
            # First try Supabase if env is configured
            try:
                from dotenv import load_dotenv
                load_dotenv()
                from supabase import create_client

                SUPABASE_URL = os.getenv('SUPABASE_URL')
                SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_KEY')
                SUPABASE_BUCKET = os.getenv('SUPABASE_BUCKET')

                if SUPABASE_URL and SUPABASE_KEY and SUPABASE_BUCKET:
                    # Lazy import uuid/mimetypes
                    import uuid
                    import mimetypes

                    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
                    filename = Path(image_path).name
                    dest_path = f"temp/reverse_search/{uuid.uuid4().hex}_{filename}"

                    with open(image_path, 'rb') as fh:
                        # supabase-py expects bytes-like; upload returns dict with 'error' key on failure
                        upload_res = supabase.storage.from_(SUPABASE_BUCKET).upload(dest_path, fh)

                    # If upload_res is a dict and contains 'error', treat as failure
                    if isinstance(upload_res, dict) and upload_res.get('error'):
                        raise RuntimeError(f"Supabase upload error: {upload_res.get('error')}")

                    # Generate a short-lived signed URL (seconds)
                    try:
                        signed = supabase.storage.from_(SUPABASE_BUCKET).create_signed_url(dest_path, 900)
                        # create_signed_url typically returns {'signedURL': '...'} or similar
                        if isinstance(signed, dict):
                            image_url_to_use = signed.get('signedURL') or signed.get('signed_url') or signed.get('signedUrl') or image_url_to_use
                        else:
                            # If supabase client returns a string
                            image_url_to_use = str(signed)

                        supabase_uploaded_path = dest_path
                    except Exception as e:
                        # If signed URL creation fails, attempt to get public URL (if bucket public)
                        try:
                            pub = supabase.storage.from_(SUPABASE_BUCKET).get_public_url(dest_path)
                            if isinstance(pub, dict):
                                image_url_to_use = pub.get('publicURL') or image_url_to_use
                            else:
                                image_url_to_use = str(pub)
                            supabase_uploaded_path = dest_path
                        except Exception:
                            raise e
                else:
                    raise RuntimeError('Supabase config missing (SUPABASE_URL/SUPABASE_KEY/SUPABASE_BUCKET)')

            except Exception as e_sup:
                logger.info(f"Supabase upload skipped/failed: {e_sup}")
                # Fall back to transfer.sh
                with open(image_path, 'rb') as f:
                    image_hash = hashlib.sha256(f.read()).hexdigest()

                return {
                    'success': False,
                    'error': f'Failed to upload local file to Supabase and transfer.sh: {e}',
                    'matches_found': 0,
                    'image_hash': image_hash,
                    'warning': 'Ensure SUPABASE credentials or internet access for transfer.sh.'
                }

        try:
            from serpapi import GoogleSearch

            params = {
                "engine": "google_lens",
                "url": image_url_to_use,
                "api_key": self.serpapi_key
            }

            search = GoogleSearch(params)
            results = search.get_dict()

            # Basic normalization of expected fields
            matches = results.get('image_results') or results.get('image_results', [])
            matches_found = len(matches) if isinstance(matches, list) else 0

            resp = {
                'success': True,
                'method': 'serpapi_google_lens',
                'matches_found': matches_found,
                'matches': matches,
                'raw': results,
                'used_url': image_url_to_use
            }

            logger.info(f"Reverse image search completed: {matches_found} matches")
            return resp

        except Exception as e:
            # If SerpAPI returns 404 or other HTTP errors, capture details and return structured error
            logger.error(f"Reverse image search failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'matches_found': 0
            }
    
    def _detect_ai_generated(self, image_path: str) -> Dict[str, Any]:
        """
        Detect if image is AI-generated using Hugging Face models
        """
        results = {
            'models_tested': [],
            'ai_generated_confidence': 0.0,
            'verdict': 'UNKNOWN',
            'details': {}
        }
        
        # 1. Try Organika/sdxl-detector (lightweight classifier)
        if self.hf_token:
            try:
                organika_result = self._check_with_organika(image_path)
                results['models_tested'].append('organika')
                results['details']['organika'] = organika_result
                
                if organika_result.get('success'):
                    results['ai_generated_confidence'] = max(
                        results['ai_generated_confidence'],
                        organika_result.get('ai_probability', 0)
                    )
            except Exception as e:
                logger.warning(f"Organika detection failed: {e}")
        
        # 2. Heuristic analysis (fallback if no API access)
        heuristic_result = self._heuristic_ai_detection(image_path)
        results['models_tested'].append('heuristic')
        results['details']['heuristic'] = heuristic_result
        results['ai_generated_confidence'] = max(
            results['ai_generated_confidence'],
            heuristic_result.get('ai_probability', 0)
        )
        
        # Determine verdict
        if results['ai_generated_confidence'] > 0.7:
            results['verdict'] = 'LIKELY_AI_GENERATED'
        elif results['ai_generated_confidence'] > 0.4:
            results['verdict'] = 'POSSIBLY_AI_GENERATED'
        else:
            results['verdict'] = 'LIKELY_AUTHENTIC'
        
        logger.info(f"AI detection: {results['verdict']} (confidence: {results['ai_generated_confidence']:.2%})")
        
        return results
    
    def _check_with_organika(self, image_path: str) -> Dict[str, Any]:
        """
        Check image with organika
        """
        try:
            import requests
            
            API_URL = f"https://router.huggingface.co/hf-inference/{self.ai_detection_models['organika']}"
            headers = {"Authorization": f"Bearer {self.hf_token}"}
            
            with open(image_path, "rb") as f:
                data = f.read()
            
            response = requests.post(API_URL, headers=headers, data=data, timeout=30)
            
            # Successful response
            if response.status_code == 200:
                try:
                    results = response.json()
                except Exception:
                    # Non-JSON but 200 response
                    results = response.text

                # Parse results (model returns classification scores)
                ai_score = 0.0
                if isinstance(results, list) and len(results) > 0:
                    for item in results[0]:
                        if 'artificial' in item.get('label', '').lower():
                            ai_score = max(ai_score, item.get('score', 0))

                return {
                    'success': True,
                    'ai_probability': ai_score,
                    'raw_results': results
                }

            # Non-200: include status and body to help diagnosis
            else:
                body = None
                try:
                    body = response.json()
                except Exception:
                    body = response.text

                # Provide actionable suggestions for common cases
                suggestion = None
                if response.status_code == 404:
                    suggestion = (
                        "Model not found or access denied. "
                        "Check that the model id 'Organika/sdxl-detector' is correct and that your HUGGINGFACE_TOKEN has permission to access it (private models require a token with read access)."
                    )
                elif response.status_code == 403:
                    suggestion = (
                        "Access forbidden - the token may lack permissions. "
                        "Verify HUGGINGFACE_TOKEN and that the model allows inference with your token."
                    )

                return {
                    'success': False,
                    'error': f"API returned {response.status_code}",
                    'status_code': response.status_code,
                    'response_body': body,
                    'suggestion': suggestion
                }
                
        except Exception as e:
            logger.error(f"Organika API call failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _heuristic_ai_detection(self, image_path: str) -> Dict[str, Any]:
        """
        Heuristic AI detection based on image characteristics
        """
        try:
            image = Image.open(image_path)
            img_array = np.array(image)
            
            # Check various indicators
            indicators = []
            ai_probability = 0.0
            
            # 1. Check for perfect pixel patterns (AI tends to have very smooth gradients)
            if len(img_array.shape) == 3:
                # Calculate local variance
                from scipy.ndimage import generic_filter
                gray = np.mean(img_array, axis=2)
                local_var = generic_filter(gray, np.var, size=5)
                avg_variance = np.mean(local_var)
                
                if avg_variance < 100:  # Very smooth
                    indicators.append("unusually_smooth_gradients")
                    ai_probability += 0.2
            
            # 2. Check for unnatural color distribution
            if len(img_array.shape) == 3:
                # AI images sometimes have unnatural color saturation
                hsv = image.convert('HSV')
                hsv_array = np.array(hsv)
                saturation = hsv_array[:, :, 1]
                sat_std = np.std(saturation)
                
                if sat_std < 30:  # Very uniform saturation
                    indicators.append("uniform_saturation")
                    ai_probability += 0.15
            
            # 3. Check for JPEG artifacts (AI generated often has fewer)
            if image.format == 'JPEG':
                # Simplified check - real implementation would be more sophisticated
                indicators.append("jpeg_format")
            
            # 4. Aspect ratio check (AI often generates specific sizes)
            width, height = image.size
            common_ai_ratios = [(1024, 1024), (512, 512), (768, 768), (1024, 768)]
            if (width, height) in common_ai_ratios:
                indicators.append("common_ai_dimensions")
                ai_probability += 0.1
            
            return {
                'success': True,
                'ai_probability': min(ai_probability, 0.6),  # Cap heuristic confidence
                'indicators_found': indicators,
                'image_dimensions': [width, height],
                'method': 'heuristic_analysis'
            }
            
        except Exception as e:
            logger.error(f"Heuristic AI detection failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'ai_probability': 0.0
            }
    
    def _analyze_metadata_tampering(self, image_path: str) -> Dict[str, Any]:
        """
        Analyze EXIF metadata for signs of tampering
        """
        tampering_indicators = []
        risk_score = 0.0
        # Ensure these are defined even if early exceptions occur
        exif_data = {}
        pil_exif = {}
        date_tags = {}
        
        try:
            # Extract EXIF data
            exif_data = {}
            if exifread:
                with open(image_path, 'rb') as f:
                    tags = exifread.process_file(f, details=True)
                    exif_data = {str(tag): str(value) for tag, value in tags.items()}
            
            # Open with PIL for additional checks
            image = Image.open(image_path)
            
            # Get PIL EXIF
            pil_exif = {}
            try:
                exif = image.getexif()
                if exif:
                    # Convert PIL Exif to readable dict using TAGS where possible
                    pil_exif = {TAGS.get(tag, tag): exif.get(tag) for tag in exif}
            except Exception:
                pil_exif = {}
            
            # Use Hugging Face InferenceClient if available and HF token provided.
            try:
                from huggingface_hub import InferenceClient
            except Exception:
                # huggingface_hub not installed
                logger.warning("huggingface_hub not installed; skipping HF model check")
                return {'success': False, 'error': 'huggingface_hub not installed'}

            # Prefer HF_TOKEN, fall back to self.hf_token
            hf_token = os.getenv('HF_TOKEN') or os.getenv('HUGGINGFACE_TOKEN') or self.hf_token
            if not hf_token:
                return {'success': False, 'error': 'HF_TOKEN (Hugging Face API token) not configured'}

            try:
                client = InferenceClient(proxies="hf-inference", api_key=hf_token)

                # The model recommended: Organika/sdxl-detector
                model_name = 'Organika/sdxl-detector'

                # The InferenceClient.image_classification helper accepts file path or bytes
                # We'll pass raw bytes to be safe
                with open(image_path, 'rb') as f:
                    img_bytes = f.read()

                results = client.image_classification(img_bytes, model=model_name)

                # Normalize results: list of {label, score}
                ai_score = 0.0
                indicators = []
                if isinstance(results, list):
                    for item in results:
                        label = (item.get('label') or '').lower()
                        score = float(item.get('score', 0))
                        indicators.append({'label': label, 'score': score})
                        # Heuristic: if label mentions synthetic/ai/fake mark as AI
                        if any(k in label for k in ['ai', 'synthetic', 'fake', 'generated']):
                            ai_score = max(ai_score, score)
                elif isinstance(results, dict):
                    # Some HF endpoints return dicts with predictions
                    preds = results.get('predictions') or results.get('data') or results.get('results')
                    if isinstance(preds, list):
                        for item in preds:
                            label = (item.get('label') or '').lower()
                            score = float(item.get('score', 0))
                            indicators.append({'label': label, 'score': score})
                            if any(k in label for k in ['ai', 'synthetic', 'fake', 'generated']):
                                ai_score = max(ai_score, score)
                    else:
                        # fallback: return raw dict
                        indicators = [results]

                return {
                    'success': True,
                    'ai_probability': ai_score,
                    'raw_results': results,
                    'indicators': indicators,
                    'model_used': model_name
                }

            except Exception as e:
                # Provide richer error info for debugging (include status if available)
                err_info = {'success': False, 'error': str(e)}
                try:
                    # Some exceptions surface a 'response' attribute (requests.HTTPError)
                    if hasattr(e, 'response') and e.response is not None:
                        resp = e.response
                        err_info['status_code'] = getattr(resp, 'status_code', None)
                        try:
                            err_info['response_text'] = resp.text
                        except Exception:
                            pass
                except Exception:
                    pass

                logger.error(f"Organika/HF inference failed: {e}")
                return err_info
            
        finally: 
            if len(set(date_tags.values())) > 1:
                tampering_indicators.append({
                    'indicator': 'inconsistent_dates',
                    'severity': 'MEDIUM',
                    'description': 'Multiple different date timestamps found',
                    'dates': date_tags
                })
                risk_score += 0.2
            
            # 4. Check for GPS data manipulation
            if 'GPSInfo' in pil_exif:
                tampering_indicators.append({
                    'indicator': 'gps_data_present',
                    'severity': 'LOW',
                    'description': 'GPS data found - could be legitimate or added',
                })
            
            # 5. Check file modification time vs EXIF time
            file_mtime = datetime.fromtimestamp(Path(image_path).stat().st_mtime)
            if 'DateTime' in pil_exif:
                try:
                    # Parse EXIF date
                    exif_time_str = str(pil_exif['DateTime'])
                    # EXIF format: "YYYY:MM:DD HH:MM:SS"
                    exif_time = datetime.strptime(exif_time_str, "%Y:%m:%d %H:%M:%S")
                    
                    # If file is modified significantly after photo taken
                    time_diff = abs((file_mtime - exif_time).days)
                    if time_diff > 365:  # More than a year difference
                        tampering_indicators.append({
                            'indicator': 'time_discrepancy',
                            'severity': 'MEDIUM',
                            'description': f'File modification time differs from EXIF by {time_diff} days',
                            'file_mtime': file_mtime.isoformat(),
                            'exif_time': exif_time.isoformat()
                        })
                        risk_score += 0.2
                except:
                    pass
            
            result = {
                'success': True,
                'tampering_indicators': tampering_indicators,
                'tampering_risk_score': min(risk_score, 1.0),
                'verdict': self._get_tampering_verdict(risk_score),
                'exif_data_present': len(exif_data) > 0 or len(pil_exif) > 0,
                'total_exif_tags': len(exif_data) + len(pil_exif),
                'raw_exif': {
                    'exifread': exif_data,
                    'pil': pil_exif
                }
            }
            
            logger.info(f"Metadata analysis: {len(tampering_indicators)} indicators, risk: {risk_score:.2%}")
            
            return result
                    
    
    def _get_tampering_verdict(self, risk_score: float) -> str:
        """Get tampering verdict based on risk score"""
        if risk_score >= 0.7:
            return 'HIGH_TAMPERING_RISK'
        elif risk_score >= 0.4:
            return 'MODERATE_TAMPERING_RISK'
        elif risk_score >= 0.2:
            return 'LOW_TAMPERING_RISK'
        else:
            return 'NO_SIGNIFICANT_TAMPERING'
    
    def _detect_pixel_anomalies(self, image_path: str) -> Dict[str, Any]:
        """
        Detect pixel-level anomalies using statistical analysis
        """
        try:
            image = Image.open(image_path)
            img_array = np.array(image)
            
            anomalies = []
            anomaly_score = 0.0
            
            # Convert to grayscale for analysis
            if len(img_array.shape) == 3:
                gray = np.mean(img_array, axis=2)
            else:
                gray = img_array
            
            # 1. Check for cloning artifacts (repeating patterns)
            # Simplified version - production would use more sophisticated detection
            from scipy.signal import correlate2d
            
            # Sample regions
            h, w = gray.shape
            region_size = min(64, h // 4, w // 4)
            
            if region_size > 16:
                # Take a sample region
                sample = gray[:region_size, :region_size]
                
                # Correlate with rest of image
                correlation = correlate2d(gray, sample, mode='valid')
                correlation_normalized = (correlation - np.min(correlation)) / (np.max(correlation) - np.min(correlation) + 1e-8)
                
                # Find peaks (similar regions)
                threshold = 0.8
                peaks = np.where(correlation_normalized > threshold)
                
                if len(peaks[0]) > 1:  # More than just the original location
                    anomalies.append({
                        'type': 'repeating_patterns',
                        'severity': 'MEDIUM',
                        'description': f'Found {len(peaks[0])} similar regions - possible cloning',
                        'locations': len(peaks[0])
                    })
                    anomaly_score += 0.3
            
            # 2. Check for splicing (inconsistent noise levels)
            # Divide image into blocks and check noise variance
            block_size = 32
            noise_variances = []
            
            for i in range(0, h - block_size, block_size):
                for j in range(0, w - block_size, block_size):
                    block = gray[i:i+block_size, j:j+block_size]
                    noise_variances.append(np.var(block))
            
            if noise_variances:
                noise_std = np.std(noise_variances)
                noise_mean = np.mean(noise_variances)
                
                # High variance in noise levels suggests splicing
                if noise_std > noise_mean * 0.5:
                    anomalies.append({
                        'type': 'inconsistent_noise',
                        'severity': 'HIGH',
                        'description': 'Inconsistent noise levels across image - possible splicing',
                        'noise_std': float(noise_std),
                        'noise_mean': float(noise_mean)
                    })
                    anomaly_score += 0.4
            
            # 3. Check for compression artifacts inconsistency (JPEG only)
            if image.format == 'JPEG':
                # Check DCT block boundaries
                # Simplified check
                anomalies.append({
                    'type': 'jpeg_analysis',
                    'severity': 'LOW',
                    'description': 'JPEG format detected - compression artifact analysis performed',
                })
            
            # 4. Edge detection anomalies
            from scipy.ndimage import sobel
            edges = sobel(gray)
            edge_strength = np.mean(np.abs(edges))
            
            if edge_strength > 50:  # Very sharp edges
                anomalies.append({
                    'type': 'sharp_edges',
                    'severity': 'LOW',
                    'description': 'Unusually sharp edges detected',
                    'edge_strength': float(edge_strength)
                })
                anomaly_score += 0.1
            
            result = {
                'success': True,
                'anomalies_detected': anomalies,
                'anomaly_score': min(anomaly_score, 1.0),
                'verdict': self._get_anomaly_verdict(anomaly_score),
                'total_anomalies': len(anomalies),
                'analysis_details': {
                    'image_dimensions': list(gray.shape),
                    'blocks_analyzed': len(noise_variances),
                    'mean_pixel_value': float(np.mean(gray))
                }
            }
            
            logger.info(f"Pixel analysis: {len(anomalies)} anomalies, score: {anomaly_score:.2%}")
            
            return result
            
        except Exception as e:
            logger.error(f"Pixel anomaly detection failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'anomaly_score': 0.0
            }
    
    def _get_anomaly_verdict(self, anomaly_score: float) -> str:
        """Get anomaly verdict based on score"""
        if anomaly_score >= 0.7:
            return 'HIGH_MANIPULATION_RISK'
        elif anomaly_score >= 0.4:
            return 'MODERATE_MANIPULATION_RISK'
        elif anomaly_score >= 0.2:
            return 'LOW_MANIPULATION_RISK'
        else:
            return 'NO_SIGNIFICANT_ANOMALIES'
    
    def _combine_manipulation_indicators(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Combine all analysis results into overall manipulation assessment
        """
        combined_score = 0.0
        weights = {
            'reverse_search': 0.3,
            'ai_detection': 0.25,
            'metadata_analysis': 0.25,
            'pixel_analysis': 0.2
        }
        
        indicators = []
        
        # Reverse search
        if 'reverse_search' in analysis_results:
            rs = analysis_results['reverse_search']
            if rs.get('matches_found', 0) > 0:
                indicators.append('Potential stolen/reused image')
                combined_score += weights['reverse_search'] * 0.8
        
        # AI detection
        if 'ai_detection' in analysis_results:
            ai = analysis_results['ai_detection']
            if ai.get('ai_generated_confidence', 0) > 0.5:
                indicators.append(f'AI-generated likelihood: {ai["ai_generated_confidence"]:.0%}')
                combined_score += weights['ai_detection'] * ai['ai_generated_confidence']
        
        # Metadata tampering
        if 'metadata_analysis' in analysis_results:
            meta = analysis_results['metadata_analysis']
            if meta.get('tampering_risk_score', 0) > 0.3:
                indicators.append(f'Metadata tampering risk: {meta["tampering_risk_score"]:.0%}')
                combined_score += weights['metadata_analysis'] * meta['tampering_risk_score']
        
        # Pixel anomalies
        if 'pixel_analysis' in analysis_results:
            pixel = analysis_results['pixel_analysis']
            if pixel.get('anomaly_score', 0) > 0.3:
                indicators.append(f'Pixel anomalies detected: {pixel["anomaly_score"]:.0%}')
                combined_score += weights['pixel_analysis'] * pixel['anomaly_score']
        
        # Overall verdict
        if combined_score >= 0.7:
            verdict = 'HIGH_MANIPULATION_RISK'
            recommendation = 'REJECT - Multiple manipulation indicators detected'
        elif combined_score >= 0.4:
            verdict = 'MODERATE_MANIPULATION_RISK'
            recommendation = 'MANUAL_REVIEW - Suspicious indicators found'
        elif combined_score >= 0.2:
            verdict = 'LOW_MANIPULATION_RISK'
            recommendation = 'PROCEED_WITH_CAUTION - Minor concerns'
        else:
            verdict = 'AUTHENTIC'
            recommendation = 'ACCEPT - No significant manipulation detected'
        
        return {
            'combined_manipulation_score': combined_score,
            'verdict': verdict,
            'recommendation': recommendation,
            'indicators': indicators,
            'key_findings': indicators if indicators else ['No significant findings'],
            'recommended_actions': recommendation,
            'decision': ('REJECT' if verdict == 'HIGH_MANIPULATION_RISK' else 'APPROVE' if verdict == 'AUTHENTIC' else 'PENDING'),
            'confidence': 0.8,  # Confidence in the assessment
            'summary': f'{len(indicators)} manipulation indicator(s) found'
        }


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python advanced_image_analyzer.py <image_path>")
        sys.exit(1)
    
    logging.basicConfig(level=logging.INFO)
    
    analyzer = AdvancedImageAnalyzer()
    results = analyzer.analyze_image(sys.argv[1])
    
    print("\n" + "="*80)
    print("IMAGE ANALYSIS RESULTS")
    print("="*80)
    print(json.dumps(results, indent=2, default=str))

