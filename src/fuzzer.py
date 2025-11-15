from typing import List
from src.runner import Runner, RunnerResult
import time

class Fuzzer:
    def __init__(self, runner: Runner) -> None:
        self.runner = runner

    def fuzz(self, trails: int = 10, verbose: bool = True) -> List[RunnerResult]:
        results = []
        for i in range(trails):
            if verbose:
                print(f"Fuzzing trial {i + 1}/{trails}... ", end="", flush=True)
            result = self.runner.run()
            results.append(result)

            if verbose:
                print(f"{result.status.value.upper()}")

        return results