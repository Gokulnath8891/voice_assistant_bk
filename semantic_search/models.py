from django.db import models

class SearchQuery(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    query = models.TextField()
    summary = models.TextField()
    processing_time_ms = models.IntegerField()
    num_chunks_returned = models.IntegerField()
    
    class Meta:
        ordering = ['-timestamp']