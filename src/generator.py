from typing import Any
import random


class Generator:
    def __init__(self) -> None:
        pass

    def generate(self) -> Any:
        return None


class StringGenerator(Generator):
    def __init__(self, max_length: int = 128, char_start: int = ord("a"), char_range: int = 26):
        self.max_length = max_length
        self.char_start = char_start
        self.char_range = char_range

    def generate(self):
        string_length = random.randrange(0, self.max_length + 1)
        out = ""
        for i in range(0, string_length):
            out += chr(random.randrange(self.char_start, self.char_start + self.char_range))
        return out

class IntegerGenerator(Generator):
    def __init__(self, min_value: int = 0, max_value: int = 100):
        self.min_value = min_value
        self.max_value = max_value

    def generate(self):
        return random.randint(self.min_value, self.max_value)
    