from django.urls import path
from . import views

urlpatterns = [
    path('start', views.start_wake_word_detection, name='start_wake_word'),
    path('stop', views.stop_wake_word_detection, name='stop_wake_word'),
    path('status', views.wake_word_status, name='wake_word_status'),
    path('stream', views.wake_word_stream, name='wake_word_stream'),
    path('process', views.process_wake_word_command, name='process_wake_word_command'),
]