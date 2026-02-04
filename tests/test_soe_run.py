from operator import ge
import sys
import os
from pathlib import Path
import pytest

from soe import run


def test_main_function_exists():
    """Test that main function exists"""
    assert callable(run.run)
    assert callable(run.f_run)


def test_import():
    """Test that the module can be imported"""
    assert run is not None
    

@pytest.mark.unit
def test_run():
    def inner_function(a):
        pass
    
    def sample_function():
        inner_function(42)
        inner_function("test")
        
    type_list = run.run(sample_function, params=[])[1]
    assert int in type_list
    assert str in type_list
    assert 42 in type_list[int]
    assert "test" in type_list[str]


@pytest.mark.unit
def test_run_1():
    def add(a, b):
        return a + b
    
    type_list = run.run(add, params=[1, 2])[1]
    print(type_list)
    assert int in type_list
    assert 1 in type_list[int]
    assert 2 in type_list[int]
    assert 3 in type_list[int]

@pytest.mark.unit
def test_run_2():
    def add(a, b):
        return a + b
    
    type_list = run.run(add, params=[1, 2])[1]
    print(type_list)
    assert int in type_list
    assert 1 in type_list[int]
    assert 2 in type_list[int]
    assert 3 in type_list[int]

@pytest.mark.unit
def test_run_3():
    class SampleClass:
        def __init__(self, a=0):
            self.a = a

        def method(self, x):
            return x * 2
        
    def use_method():
        obj = SampleClass(5)
        obj.method(5)
        obj.method(10)

    type_list = run.run(use_method, params=[])[1]
    print(type_list)
    assert int in type_list
    assert 5 in type_list[int]
    assert 10 in type_list[int]
    assert any(obj.a == 5 for obj in type_list[SampleClass])

def _multiply(a, b):
    return a * b

@pytest.mark.unit
def test_f_run_1():
    type_list = run.f_run('tests.test_soe_run._multiply', params=[3, 4])[1]
    print(type_list)
    assert int in type_list
    assert 3 in type_list[int]
    assert 4 in type_list[int]
    assert 12 in type_list[int]

def _concat_strings(s1, s2):
    return s1 + s2

@pytest.mark.unit
def test_f_run_2():
    type_list = run.f_run('tests.test_soe_run._concat_strings', params=["hello, ", "world!"])[1]
    print(type_list)
    assert str in type_list
    assert "hello, " in type_list[str]
    assert "world!" in type_list[str]
    assert "hello, world!" in type_list[str]

class _Calculator:
    def __init__(self, name):
        self.name = name

    def add(self, x, y):
        return x + y
    
def _calculate(a, b):
    calc = _Calculator("test")
    return calc.add(a, b)
        
@pytest.mark.unit
def test_f_run_3():
    type_list = run.f_run('tests.test_soe_run._calculate', params=[10, 20])[1]
    print(type_list)
    assert int in type_list
    assert 10 in type_list[int]
    assert 20 in type_list[int]
    assert 30 in type_list[int]
    assert _Calculator in type_list
    assert any(obj.name == "test" for obj in type_list[_Calculator])
