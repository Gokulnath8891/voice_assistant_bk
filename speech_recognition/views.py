import json
import time
import logging
import tempfile
import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import azure.cognitiveservices.speech as speechsdk
from django.conf import settings

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
def recognize_speech(request):
    start_time = time.time()
    temp_file_path = None
    
    try:
        logger.info("Speech recognition request received")
        
        # Check for Azure credentials
        if not settings.AZURE_SPEECH_KEY or not settings.AZURE_SPEECH_REGION:
            logger.error("Azure Speech credentials not configured")
            return JsonResponse({
                'status': 'error',
                'message': 'Azure Speech Service not configured'
            }, status=500)
        
        if 'audio' not in request.FILES:
            logger.warning("No audio file in request")
            return JsonResponse({
                'status': 'error',
                'message': 'No audio file provided'
            }, status=400)
        
        audio_file = request.FILES['audio']
        logger.info(f"Processing audio file: {audio_file.name}, size: {audio_file.size} bytes")
        
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            for chunk in audio_file.chunks():
                temp_file.write(chunk)
            temp_file_path = temp_file.name
        
        logger.info(f"Audio saved to temporary file: {temp_file_path}")
        
        # Configure Azure Speech
        speech_config = speechsdk.SpeechConfig(
            subscription=settings.AZURE_SPEECH_KEY,
            region=settings.AZURE_SPEECH_REGION
        )
        speech_config.speech_recognition_language = "en-US"
        
        # Configure audio input
        audio_config = speechsdk.audio.AudioConfig(filename=temp_file_path)
        speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config, 
            audio_config=audio_config
        )
        
        logger.info("Starting speech recognition")
        result = speech_recognizer.recognize_once_async().get()
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            logger.info(f"Speech recognized: {result.text}")
            return JsonResponse({
                'status': 'success',
                'recognized_text': result.text,
                'confidence_score': 0.95,
                'processing_time_ms': processing_time_ms
            })
        elif result.reason == speechsdk.ResultReason.NoMatch:
            logger.warning("No speech could be recognized")
            return JsonResponse({
                'status': 'error',
                'message': 'No speech could be recognized'
            }, status=400)
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            error_msg = f'Speech recognition canceled: {cancellation_details.reason}'
            if cancellation_details.error_details:
                error_msg += f' - {cancellation_details.error_details}'
            logger.error(error_msg)
            return JsonResponse({
                'status': 'error',
                'message': error_msg
            }, status=500)
            
    except Exception as e:
        logger.error(f"Speech recognition error: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
    
    finally:
        # Clean up temporary file with improved retry logic
        if temp_file_path and os.path.exists(temp_file_path):
            import gc
            gc.collect()  # Force garbage collection to release handles
            max_retries = 5
            for attempt in range(max_retries):
                try:
                    time.sleep(0.1 * (attempt + 1))  # Increasing delay
                    os.unlink(temp_file_path)
                    logger.info("Temporary file cleaned up")
                    break
                except PermissionError:
                    if attempt == max_retries - 1:
                        # Schedule for cleanup on next request
                        logger.warning(f"Failed to cleanup temp file after {max_retries} attempts, file may be locked by Azure SDK")
                        # Try to mark it for deletion when possible
                        try:
                            import stat
                            os.chmod(temp_file_path, stat.S_IWRITE)
                        except:
                            pass
                    else:
                        time.sleep(0.2 * (attempt + 1))
                except Exception as e:
                    if attempt == max_retries - 1:
                        logger.warning(f"Failed to cleanup temp file: {e}")
                    else:
                        time.sleep(0.2)