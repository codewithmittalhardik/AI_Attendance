#!/usr/bin/env python
import sys
import pkgutil
import os

# --- STEP 1: THE FIX (Must be before importing face_recognition) ---
if not hasattr(pkgutil, 'ImpImporter'):
    # We create a dummy class because the library expects an object, not just None
    class Dummy: pass
    pkgutil.ImpImporter = Dummy

# --- STEP 2: NOW IMPORT THE AI MODELS ---
try:
    import face_recognition_models
    os.environ['FACE_RECOGNITION_MODELS'] = os.path.dirname(face_recognition_models.__file__)
except ImportError:
    pass # Handle this inside your Django views if needed

def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()