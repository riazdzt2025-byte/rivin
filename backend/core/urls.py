from django.urls import path
from .views import geo_language_debug, set_language_api

urlpatterns = [
    path('language/', geo_language_debug, name='geo-language-debug'),
    path('language/set/', set_language_api, name='set-language-api'),
]
