import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_main_function_exists():
    """Test that main function exists"""
    from src.downloader.downloader import downloader
    assert callable(downloader)

def test_import():
    """Test that the module can be imported"""
    from src.downloader import downloader
    assert downloader is not None