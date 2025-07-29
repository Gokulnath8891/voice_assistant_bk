from django.urls import path
from . import views

urlpatterns = [
    path('recognize', views.recognize_speech, name='recognize_speech'),
]