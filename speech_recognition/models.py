from django.db import models

class SpeechRecognitionRequest(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    audio_duration = models.FloatField()
    recognized_text = models.TextField()
    confidence_score = models.FloatField()
    processing_time_ms = models.IntegerField()
    
    class Meta:
        ordering = ['-timestamp']