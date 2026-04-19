import os
import pkgutil
import sys
from django.core.wsgi import get_wsgi_application

# --- CRITICAL PYTHON 3.12 HACK FOR GUNICORN ---
if not hasattr(pkgutil, 'ImpImporter'):
    class Dummy: pass
    pkgutil.ImpImporter = Dummy

# Force the models path environment variable
try:
    import face_recognition_models
    os.environ['FACE_RECOGNITION_MODELS'] = os.path.dirname(face_recognition_models.__file__)
except ImportError:
    pass
# ----------------------------------------------

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

application = get_wsgi_application()