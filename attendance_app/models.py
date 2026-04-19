from django.db import models
import face_recognition
import numpy as np
import os

class Student(models.Model):
    name = models.CharField(max_length=100)
    roll_number = models.CharField(max_length=20, unique=True)
    photo = models.ImageField(upload_to='student_photos/')
    face_encoding = models.JSONField(blank=True, null=True)

    def save(self, *args, **kwargs):
        # 1. Save the model first to ensure the file is on the disk
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # 2. Only run AI logic if there is a photo and no encoding yet
        if self.photo and not self.face_encoding:
            try:
                # Ensure the path is absolute and clean
                image_path = self.photo.path
                if os.path.exists(image_path):
                    image = face_recognition.load_image_file(image_path)
                    encodings = face_recognition.face_encodings(image)
                    
                    if encodings:
                        # Convert numpy array to list for JSON storage
                        self.face_encoding = encodings[0].tolist()
                        # Use update_fields to save ONLY the encoding, preventing loops
                        super().save(update_fields=['face_encoding'])
                    else:
                        print(f"⚠️ No face found for {self.name}")
            except Exception as e:
                print(f"❌ AI Processing Error: {e}")

    def __str__(self):
        return f"{self.name} ({self.roll_number})"

class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    time_marked = models.TimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'date')

    def __str__(self):
        return f"{self.student.name} marked present on {self.date}"