import importlib.util
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def test_backend_app_imports_without_broken_model_artifacts():
    import app

    assert hasattr(app, 'app')
