from django.urls import path
from . import views

app_name = 'chatbot'

urlpatterns = [
    path('', views.chat_view, name='chatbot'),
    path('send/', views.send_message, name='send_message'),
    path('get-messages/', views.get_messages, name='get_messages'),
]