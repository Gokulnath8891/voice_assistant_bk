import json
import io
import os
import tempfile
import pyttsx3
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

@csrf_exempt
@require_http_methods(["POST"])
def synthesize_speech(request):
    try:
        data = json.loads(request.body)
        text = data.get('text')
        voice_settings = data.get('voice_settings', {})
        
        if not text:
            return JsonResponse({
                'status': 'error',
                'message': 'Text is required'
            }, status=400)
        
        rate = voice_settings.get('rate', 150)
        volume = voice_settings.get('volume', 0.8)
        voice = voice_settings.get('voice', 'default')
        
        # Create a temporary file for audio output
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            temp_path = temp_file.name
        
        try:
            # Initialize TTS engine
            engine = pyttsx3.init()
            engine.setProperty('rate', rate)
            engine.setProperty('volume', volume)
            
            # Set voice if specified
            voices = engine.getProperty('voices')
            if voice != 'default' and voices:
                for v in voices:
                    if voice.lower() in v.name.lower():
                        engine.setProperty('voice', v.id)
                        break
            
            # Save audio to temporary file
            engine.save_to_file(text, temp_path)
            engine.runAndWait()
            
            # Read the generated audio file
            with open(temp_path, 'rb') as audio_file:
                audio_data = audio_file.read()
            
            # Create HTTP response with audio data
            response = HttpResponse(
                audio_data,
                content_type='audio/wav'
            )
            response['Content-Disposition'] = 'inline; filename="speech.wav"'
            response['Content-Length'] = len(audio_data)
            
            return response
            
        finally:
            # Clean up temporary file
            try:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            except Exception:
                pass  # Ignore cleanup errors
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)