# from src.runner import Runner, FunctionRunner
# from src.fuzzer import Fuzzer
# from src.generator import StringGenerator
# from FunctionTree.function_info import FunctionInfo 

# def test_function(s: str) -> int:
#     if not s:
#         raise ValueError("Empty string is not allowed")
#     return len(s)

# runner = Runner("run/test_parser.py", [StringGenerator])
# # runner = FunctionRunner(test_function, [StringGenerator])

# fuzzer = Fuzzer(runner)
# results = fuzzer.fuzz()

from src import fuzzing_loop
from pathlib import Path


fuzzing_loop.fuzzing_loop(Path("repos/numpy"))