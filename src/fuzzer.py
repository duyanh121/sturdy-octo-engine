from typing import List
from src.runner import Runner, RunnerResult, RunnerStatus
import time

class Fuzzer:
    def __init__(self, runner: Runner) -> None:
        self.runner = runner

    def fuzz(self, trails: int = 10, verbose: bool = True) -> List[RunnerResult]:
        results = []
        result_pass = 0
        result_fail = 0
        for i in range(trails):
            if verbose:
                print(f"Fuzzing trial {i + 1}/{trails}... ", end="", flush=True)
            result = self.runner.run()
            results.append(result)

            if verbose:
                print(f"{result.status.value.upper()}")

                if result.status == RunnerStatus.PASS:
                    result_pass += 1
                else:
                    result_fail += 1

        if verbose:
            print(f"Fuzzing complete: {trails} trials, {result_pass} passes, {result_fail} fails.")

        return results
    
def fuzz(function_list, function_parameter_types):
    pass