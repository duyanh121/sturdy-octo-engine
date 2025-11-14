from src.generator import Generator
from typing import List, Type, Optional, Union
import subprocess


class Runner():
    def __init__(self, filename: str, arguments: Optional[List[Type[Generator]]] = None) -> None:
        self.filename = filename
        self.arguments = arguments or []
        self.generators: List[Generator] = []

    def instantiate(self) -> None:
        self.generators = []
        for argument in self.arguments:
            self.generators.append(argument())

    def run(self) -> subprocess.CompletedProcess[str]: 
        if self.generators == [] and len(self.arguments) != 0:
            self.instantiate()

        return subprocess.run(["python", self.filename] + [generator.generate() for generator in self.generators],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True)
