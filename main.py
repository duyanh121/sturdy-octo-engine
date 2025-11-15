from src.runner import Runner, FunctionRunner
from src.fuzzer import Fuzzer
from src.generator import StringGenerator

def test_function(s: str) -> int:
    if not s:
        raise ValueError("Empty string is not allowed")
    return len(s)

runner = Runner("run/test_parser.py", [StringGenerator])
# runner = FunctionRunner(test_function, [StringGenerator])

fuzzer = Fuzzer(runner)
results = fuzzer.fuzz()