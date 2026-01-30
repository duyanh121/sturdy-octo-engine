import sys
import os
from pathlib import Path
import pytest

from soe import soe
from soe import _global

def test_main_function_exists():
    """Test that main function exists"""
    assert callable(soe.soe)

def test_import():
    """Test that the module can be imported"""
    assert soe is not None


@pytest.mark.unit
def test_global():
	_global.init_global()
	_global.set_function_list({"a": {"test": 1}, "b": {"test": 2}, "c": {"test": 3}})
	_global.set_function("d", {"test": 4})
	_global.set_function("a", {"test": 5})
	_global.set_type_list({int: [1], str: ["a"]})
	_global.set_type(float, [1.0])
	_global.set_type(int, [2, 3])

	assert _global.get_function_list() == {"a": {"test": 5}, "b": {"test": 2}, "c": {"test": 3}, "d": {"test": 4}}
	assert _global.get_function("a") == {"test": 5}
	assert _global.get_function("d") == {"test": 4}
	assert _global.get_type_list() == {int: [2, 3], str: ["a"], float: [1.0]}
	assert _global.get_type(int) == [2, 3]
	assert _global.get_type(float) == [1.0]


@pytest.mark.unit
def test_function_list_generation():
		from tests.test_repo.test_src_2.main import SampleClass

		try:
				soe.soe(Path("tests/test_repo"), no_fuzz=True, no_log=True, no_save=True)
		except Exception as e:
				assert False, f"soe.soe raised an exception: {e}"

		function_list = _global.get_function_list()["functions"]
		assert "test_src_1.main.param_func" in function_list
		assert "test_src_1.main.param_func_2" in function_list
		assert "test_src_1.main.nested_func" in function_list
		assert "test_src_1.main.inner_func" not in function_list # inner_func is nested, should not be included
		assert "test_src_2.main.SampleClass.method_one" in function_list
		assert "test_src_2.main.SampleClass.method_two" in function_list
		assert function_list["test_src_2.main.SampleClass.method_one"]["is_class_method"] is True
		assert function_list["test_src_2.main.SampleClass.method_two"]["is_class_method"] is True
		assert function_list["test_src_2.main.SampleClass.method_one"]["class"] == "SampleClass"
		assert function_list["test_src_2.main.SampleClass.method_two"]["class"] == "SampleClass"
		assert function_list["test_src_1.main.param_func"]["is_class_method"] is False

		# Test param type updating
		from soe.run import f_run
		result = f_run("test_src_1.main.param_func", [1])
		function_list = _global.get_function_list()
		assert function_list["functions"]["test_src_1.main.param_func"]["params"]["a"] == {"int": 1}


def test_soe():
		try:
				soe.soe(Path("tests/test_repo"), no_log=True, no_save=True)
		except Exception as e:
				assert False, f"soe.soe raised an exception: {e}"


@pytest.mark.slow
def test_soe_numpy():
		try:
				soe.soe(Path("downloads/numpy-8"), no_log=True, no_save=True)
		except Exception as e:
				assert False, f"soe.soe raised an exception: {e}"

@pytest.mark.slow
def test_soe_pandas():
		try:
				soe.soe(Path("downloads/pandas-49"), no_log=True, no_save=True)
		except Exception as e:
				assert False, f"soe.soe raised an exception: {e}"

@pytest.mark.slow
def test_soe_scipy():
		try:
				soe.soe(Path("downloads/scipy-5"), no_log=True, no_save=True)
		except Exception as e:
				assert False, f"soe.soe raised an exception: {e}"
