import os
import cv2
import numpy as np
import face_recognition
from datetime import date
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache

from .models import Student, Attendance

# ==========================================
# 1. THE DASHBOARD VIEW
# ==========================================
# In attendance_app/views.py

def dashboard(request):
    # 1. Check if the user selected a date in the calendar
    date_str = request.GET.get('date')
    
    if date_str:
        try:
            # Convert the string (YYYY-MM-DD) back into a real Python date
            selected_date = date.fromisoformat(date_str)
        except ValueError:
            selected_date = date.today()
    else:
        # Default to today if no date is selected
        selected_date = date.today()

    # 2. Filter the database by the EXACT date chosen
    attendance_records = Attendance.objects.filter(date=selected_date).select_related('student').order_by('-time_marked')
    
    total_students = Student.objects.count()
    present_count = attendance_records.count()
    
    context = {
        'records': attendance_records,
        'total_students': total_students,
        'present_count': present_count,
        'display_date': selected_date.strftime("%B %d, %Y"),   # For beautiful text
        'input_date': selected_date.strftime("%Y-%m-%d"),      # For the HTML calendar
        'is_today': selected_date == date.today()              # To know if we are looking at the past
    }
    return render(request, 'dashboard.html', context)

# ==========================================
# 2. ADD STUDENT VIEW (SINGLE & BULK)
# ==========================================
def add_student(request):
    context = {'active_tab': 'single'}

    if request.method == 'POST':
        action_type = request.POST.get('action_type')
        context['active_tab'] = action_type 

        # --- SINGLE UPLOAD ---
        if action_type == 'single':
            name = request.POST.get('name', '')
            roll_number = request.POST.get('roll_number', '')
            photo = request.FILES.get('photo')

            context['name'] = name
            context['roll_number'] = roll_number

            if name and roll_number and photo:
                try:
                    student = Student.objects.create(name=name, roll_number=roll_number, photo=photo)
                    if student.face_encoding:
                        messages.success(request, f"Successfully registered {name}!")
                        return redirect('dashboard')
                    else:
                        student.delete()
                        messages.error(request, "Error: No face detected. Please upload a clearer picture.")
                except Exception as e:
                    messages.error(request, f"Error saving student: {str(e)}")
            else:
                messages.error(request, "Please fill all fields and select a valid photo.")

            return render(request, 'add_student.html', context)

        # --- BULK UPLOAD ---
        elif action_type == 'bulk':
            photos = request.FILES.getlist('bulk_photos')
            
            if not photos or (len(photos) == 1 and photos[0].name == ''):
                messages.error(request, "No photos selected for bulk upload.")
                return render(request, 'add_student.html', context)

            success_count, skip_count, fail_count = 0, 0, 0

            for photo in photos:
                filename = photo.name
                if not filename: continue 
                
                name_part = os.path.splitext(filename)[0]

                try:
                    roll_number, student_name = name_part.split('_', 1)
                    student_name = student_name.replace('-', ' ').strip()
                    roll_number = roll_number.strip()
                except ValueError:
                    fail_count += 1
                    messages.error(request, f"❌ Failed '{filename}': Invalid format. Use 'RollNumber_Name.jpg'")
                    continue

                if Student.objects.filter(roll_number=roll_number).exists():
                    skip_count += 1
                    messages.warning(request, f"⏩ Skipped '{filename}': Roll number {roll_number} already exists.")
                    continue

                try:
                    student = Student.objects.create(name=student_name, roll_number=roll_number, photo=photo)
                    
                    if student.face_encoding:
                        success_count += 1
                        messages.success(request, f"✅ Added '{filename}': {student_name} registered successfully.")
                    else:
                        student.delete()
                        fail_count += 1
                        messages.error(request, f"❌ Failed '{filename}': No face detected in photo.")
                except Exception as e:
                    fail_count += 1
                    messages.error(request, f"❌ System error on '{filename}': {str(e)}")

            # --- SMART ROUTING LOGIC ---
            # --- SMART ROUTING LOGIC ---
            if fail_count > 0 or skip_count > 0:
                # Dynamically build the summary message so it only shows numbers > 0
                summary_parts = []
                if success_count > 0:
                    summary_parts.append(f"{success_count} Added")
                if skip_count > 0:
                    summary_parts.append(f"{skip_count} Skipped")
                if fail_count > 0:
                    summary_parts.append(f"{fail_count} Failed")
                
                # Joins the list together with " | " 
                summary_text = " | ".join(summary_parts)
                
                messages.info(request, f"Bulk Upload Finished: {summary_text}. Please review the details below.")
                return render(request, 'add_student.html', context) 
            else:
                # If 100% flawless
                if success_count > 0:
                    messages.success(request, f"Perfect Bulk Upload! All {success_count} students added successfully.")
                    return redirect('dashboard')
                else:
                    messages.error(request, "No valid photos were processed.")
                    return render(request, 'add_student.html', context)

    return render(request, 'add_student.html', context)


# ==========================================
# 3. HARDWARE API VIEW 
# ==========================================
@csrf_exempt
def hardware_scan(request):
    if request.method == 'POST':
        try:
            image_bytes = request.body
            nparr = np.frombuffer(image_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if frame is None:
                return JsonResponse({'error': 'Failed to decode image'}, status=400)

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            live_face_locations = face_recognition.face_locations(rgb_frame)
            live_face_encodings = face_recognition.face_encodings(rgb_frame, live_face_locations)

            all_students = Student.objects.all()
            valid_students = [s for s in all_students if s.face_encoding]
            known_encodings = [np.array(s.face_encoding) for s in valid_students]

            marked_today = []

            for face_encoding in live_face_encodings:
                matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=0.5) #Euclidean Distance
                
                if True in matches:
                    first_match_index = matches.index(True)
                    matched_student = valid_students[first_match_index]

                    attendance, created = Attendance.objects.get_or_create(
                        student=matched_student,
                        date=date.today()
                    )
                    if created:
                        marked_today.append(matched_student.name)

            return JsonResponse({'status': 'success', 'marked_present': marked_today})

        except Exception as e:
            print(f"Hardware API Error: {e}")
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid Request'}, status=400)

# --- NEW HEARTBEAT API ---
def hardware_heartbeat(request):
    # Set a flag in memory saying the hardware is online.
    # It automatically deletes itself after 10 seconds!
    cache.set('hardware_connected', True, timeout=10)
    return JsonResponse({'status': 'alive'})

# --- UPDATED LIVE LISTENER ---
def get_present_count(request):
    date_str = request.GET.get('date')
    if date_str:
        try:
            selected_date = date.fromisoformat(date_str)
        except ValueError:
            selected_date = date.today()
    else:
        selected_date = date.today()
        
    count = Attendance.objects.filter(date=selected_date).count()
    
    # Check if the hardware has pinged us in the last 10 seconds
    is_connected = cache.get('hardware_connected', False)
    
    # Send BOTH the count and the hardware status to the dashboard
    return JsonResponse({
        'count': count,
        'hardware_active': is_connected
    })