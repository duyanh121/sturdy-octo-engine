from src.generator import Generator
from typing import List, Type, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
import subprocess

class RunnerStatus(Enum):
    PASS = "pass"
    FAIL = "fail"
    UNRESOLVED = "unresolved"


@dataclass
class RunnerResult:
    status: RunnerStatus
    out: str
    error: str
    value: Any = None


class Runner:
    def __init__(self, filename: str, arguments: Optional[List[Type[Generator]]] = None) -> None:
        self.filename = filename
        self.arguments = arguments or ()

        self.instantiate()

    def instantiate(self) -> None:
        self.generators = []
        for argument in self.arguments:
            self.generators.append(argument())

    def run(self) -> RunnerResult: 
        result = subprocess.run(["python", self.filename] + [generator.generate() for generator in self.generators],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True)
        
        status = RunnerStatus.PASS if result.returncode == 0 else RunnerStatus.FAIL
        return RunnerResult(status, result.stdout, result.stderr, result)
    

class FunctionRunner(Runner):
    def __init__(self, function: Callable, arguments: Optional[List[Type[Generator]]] = None) -> None:
        self.function = function
        self.arguments = arguments or ()

        self.instantiate()

    def run(self) -> RunnerResult: 
        args = [generator.generate() for generator in self.generators]
        try:
            value = self.function(*args)
            status = RunnerStatus.PASS
            out = ""
            error = ""
        except Exception as e:
            value = None
            status = RunnerStatus.FAIL
            out = ""
            error = str(e)

        return RunnerResult(status, out, error, value)
