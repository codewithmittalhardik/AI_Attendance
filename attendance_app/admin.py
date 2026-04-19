# In attendance_app/admin.py
from django.contrib import admin
from .models import Student, Attendance

admin.site.register(Student)
admin.site.register(Attendance)