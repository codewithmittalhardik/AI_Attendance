from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve # Add this import
import re

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('attendance_app.urls')),
    path('media/<path:path>', serve, {'document_root': settings.MEDIA_ROOT}),# Your app folder name
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)