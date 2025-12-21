import sys
import os
from pathlib import Path
import pytest

from soe import soe

def test_main_function_exists():
    """Test that main function exists"""
    assert callable(soe.soe)

def test_import():
    """Test that the module can be imported"""
    assert soe is not None
    
@pytest.mark.slow
def test_soe():
	try:
		soe.soe(Path("downloads/numpy-8"),)
	except Exception as e:
		assert False, f"soe.soe raised an exception: {e}"
