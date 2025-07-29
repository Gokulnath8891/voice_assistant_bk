from django.urls import path
from . import views

urlpatterns = [
    path('query', views.search_query, name='search_query'),
    path('conversation/clear', views.clear_conversation, name='clear_conversation'),
    path('conversation/history', views.get_conversation_history, name='get_conversation_history'),
    path('conversation/sessions', views.list_active_sessions, name='list_active_sessions'),
    path('conversation/new', views.create_new_session, name='create_new_session'),
    path('conversation/reset', views.reset_session, name='reset_session'),
]