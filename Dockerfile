FROM python:3.12-slim

# Install system dependencies for face_recognition
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
RUN pip install --no-cache-dir dlib-bin==20.0.1
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

# --- CRITICAL: MEDIA FOLDER PERMISSIONS ---
RUN mkdir -p /app/media/student_photos && chmod -R 777 /app/media
# ------------------------------------------

# Run migrations and collect static files
RUN python manage.py collectstatic --noinput

# HF Spaces use port 7860
CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:7860"]