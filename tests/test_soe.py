import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from soe.soe import soe

def test_main_function_exists():
    """Test that main function exists"""
    assert callable(soe)

def test_import():
    """Test that the module can be imported"""
    from soe import soe
    assert soe is not None