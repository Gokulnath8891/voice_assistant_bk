from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/speech/', include('speech_recognition.urls')),
    path('api/v1/search/', include('semantic_search.urls')),
    path('api/v1/tts/', include('text_to_speech.urls')),
    path('api/v1/wakeword/', include('wake_word.urls')),
]