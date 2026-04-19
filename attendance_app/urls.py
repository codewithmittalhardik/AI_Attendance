# In attendance_app/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('add-student/', views.add_student, name='add_student'),
    path('hardware_scan/', views.hardware_scan, name='hardware_scan'),
    path('api/present_count/', views.get_present_count, name='present_count'),
    path('api/heartbeat/', views.hardware_heartbeat, name='heartbeat'),
]