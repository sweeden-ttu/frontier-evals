import sys
from unittest.mock import patch, MagicMock
import pytest

def pytest_configure(config):
    """Mock skip conditions before test collection"""
    # Store original module or create mock
    import swelancer.utils.general as general_module
    
    # Mock the functions in the module
    general_module.is_linux_machine = lambda: True
    general_module.is_docker_running = lambda timeout=10.0: True
    general_module.is_docker_image = lambda image_name: True

@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(config, items):
    """Remove skip marks for integration tests"""
    for item in items:
        # Remove all skipif marks
        marks = list(item.iter_markers('skipif'))
        for mark in marks:
            try:
                # Try to remove the mark
                if hasattr(item, 'own_markers'):
                    item.own_markers = [m for m in item.own_markers if m.name != 'skipif']
            except:
                pass
