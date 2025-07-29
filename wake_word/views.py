import json
import time
import logging
import threading
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
import azure.cognitiveservices.speech as speechsdk

logger = logging.getLogger(__name__)

# Global wake word detector instance
wake_word_detector = None
detection_active = False
detection_lock = threading.Lock()


class WakeWordDetectorAPI:
    """
    Wake word detection for API usage
    """
    
    def __init__(self):
        self.is_listening = False
        self.speech_config = None
        self.audio_config = None
        self.recognizer = None
        self.detection_results = []
        self.max_results = 10
        
        self._initialize_speech_config()
    
    def _initialize_speech_config(self):
        """Initialize Azure Speech SDK configuration"""
        try:
            self.speech_config = speechsdk.SpeechConfig(
                subscription=settings.AZURE_SPEECH_KEY,
                region=settings.AZURE_SPEECH_REGION
            )
            self.speech_config.speech_recognition_language = "en-US"
            self.audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
            
            logger.info("Wake word detector initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize wake word detector: {e}")
            raise
    
    def _on_recognition_result(self, evt):
        """Handle recognition results"""
        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
            recognized_text = evt.result.text.lower().strip()
            
            # Check for wake word "hey buddy"
            if "hey buddy" in recognized_text:
                logger.info(f"Wake word detected: {recognized_text}")
                
                # Extract command after wake word
                wake_word_index = recognized_text.find("hey buddy")
                command_text = recognized_text[wake_word_index + len("hey buddy"):].strip()
                
                # Store detection result
                detection_result = {
                    "timestamp": time.time(),
                    "wake_word_detected": True,
                    "full_text": evt.result.text,
                    "command_text": command_text,
                    "confidence": 0.95  # Azure doesn't provide confidence for continuous recognition
                }
                
                self.detection_results.append(detection_result)
                
                # Keep only last N results
                if len(self.detection_results) > self.max_results:
                    self.detection_results.pop(0)
    
    def start_detection(self):
        """Start wake word detection"""
        if self.is_listening:
            return False
        
        try:
            self.recognizer = speechsdk.SpeechRecognizer(
                speech_config=self.speech_config,
                audio_config=self.audio_config
            )
            
            # Connect event handler
            self.recognizer.recognized.connect(self._on_recognition_result)
            
            # Start continuous recognition
            self.recognizer.start_continuous_recognition()
            self.is_listening = True
            
            logger.info("Wake word detection started")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start wake word detection: {e}")
            return False
    
    def stop_detection(self):
        """Stop wake word detection"""
        if not self.is_listening:
            return False
        
        try:
            if self.recognizer:
                self.recognizer.stop_continuous_recognition()
                self.recognizer = None
            
            self.is_listening = False
            logger.info("Wake word detection stopped")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop wake word detection: {e}")
            return False
    
    def get_recent_detections(self, limit=5):
        """Get recent wake word detections"""
        return self.detection_results[-limit:] if self.detection_results else []
    
    def clear_detections(self):
        """Clear detection history"""
        self.detection_results.clear()


@csrf_exempt
@require_http_methods(["POST"])
def start_wake_word_detection(request):
    """Start wake word detection"""
    global wake_word_detector, detection_active
    
    try:
        # Check Azure credentials
        if not settings.AZURE_SPEECH_KEY or not settings.AZURE_SPEECH_REGION:
            return JsonResponse({
                'status': 'error',
                'message': 'Azure Speech credentials not configured'
            }, status=500)
        
        with detection_lock:
            if detection_active:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Wake word detection is already active'
                }, status=400)
            
            # Create detector if not exists
            if not wake_word_detector:
                wake_word_detector = WakeWordDetectorAPI()
            
            # Start detection
            if wake_word_detector.start_detection():
                detection_active = True
                return JsonResponse({
                    'status': 'success',
                    'message': 'Wake word detection started',
                    'wake_word': 'hey buddy',
                    'listening': True
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Failed to start wake word detection'
                }, status=500)
                
    except Exception as e:
        logger.error(f"Error starting wake word detection: {e}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def stop_wake_word_detection(request):
    """Stop wake word detection"""
    global wake_word_detector, detection_active
    
    try:
        with detection_lock:
            if not detection_active or not wake_word_detector:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Wake word detection is not active'
                }, status=400)
            
            if wake_word_detector.stop_detection():
                detection_active = False
                return JsonResponse({
                    'status': 'success',
                    'message': 'Wake word detection stopped',
                    'listening': False
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Failed to stop wake word detection'
                }, status=500)
                
    except Exception as e:
        logger.error(f"Error stopping wake word detection: {e}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def wake_word_status(request):
    """Get wake word detection status"""
    global wake_word_detector, detection_active
    
    try:
        status_data = {
            'status': 'success',
            'listening': detection_active,
            'wake_word': 'hey buddy'
        }
        
        if wake_word_detector and detection_active:
            # Get recent detections
            recent_detections = wake_word_detector.get_recent_detections(limit=5)
            status_data['recent_detections'] = recent_detections
            status_data['detection_count'] = len(wake_word_detector.detection_results)
        else:
            status_data['recent_detections'] = []
            status_data['detection_count'] = 0
        
        return JsonResponse(status_data)
        
    except Exception as e:
        logger.error(f"Error getting wake word status: {e}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def wake_word_stream(request):
    """Stream wake word detections using Server-Sent Events"""
    global wake_word_detector
    
    def event_stream():
        """Generator for SSE events"""
        last_check = time.time()
        
        while True:
            try:
                if wake_word_detector and detection_active:
                    # Check for new detections
                    recent_detections = wake_word_detector.get_recent_detections(limit=10)
                    new_detections = [
                        d for d in recent_detections 
                        if d['timestamp'] > last_check
                    ]
                    
                    if new_detections:
                        for detection in new_detections:
                            data = json.dumps(detection)
                            yield f"data: {data}\n\n"
                        
                        last_check = time.time()
                
                # Send heartbeat every 30 seconds
                yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': time.time()})}\n\n"
                
                time.sleep(1)  # Check every second
                
            except Exception as e:
                logger.error(f"Error in wake word stream: {e}")
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
                break
    
    response = StreamingHttpResponse(
        event_stream(),
        content_type='text/event-stream'
    )
    response['Cache-Control'] = 'no-cache'
    response['Connection'] = 'keep-alive'
    response['Access-Control-Allow-Origin'] = '*'
    
    return response


@csrf_exempt
@require_http_methods(["POST"])
def process_wake_word_command(request):
    """Process a wake word command through the complete pipeline"""
    try:
        data = json.loads(request.body)
        command_text = data.get('command_text', '').strip()
        
        if not command_text:
            return JsonResponse({
                'status': 'error',
                'message': 'Command text is required'
            }, status=400)
        
        # Import here to avoid circular imports
        from semantic_search.views import get_conversational_chain
        
        # Process through semantic search
        summary, relevant_chunks = get_conversational_chain(command_text)
        
        # Return result
        return JsonResponse({
            'status': 'success',
            'command_text': command_text,
            'summary': summary,
            'relevant_chunks': [
                {
                    'content': chunk['page_content'],
                    'metadata': chunk['metadata'],
                    'similarity_score': chunk['similarity_score']
                } for chunk in relevant_chunks
            ],
            'wake_word_triggered': True
        })
        
    except Exception as e:
        logger.error(f"Error processing wake word command: {e}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)