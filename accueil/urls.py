from django.urls import path
from .views import bonjour
urlpatterns = [
    path('', bonjour),
]