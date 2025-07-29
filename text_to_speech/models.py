from django.db import models

class TextToSpeechRequest(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    text = models.TextField()
    voice_rate = models.IntegerField(default=150)
    voice_volume = models.FloatField(default=0.8)
    audio_duration = models.FloatField()
    
    class Meta:
        ordering = ['-timestamp']