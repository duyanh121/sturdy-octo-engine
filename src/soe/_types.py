from enum import Enum
from typing import Optional
from collections.abc import Callable

class RunUnableToResolve(Exception):
    pass

class RunTimeout(Exception):
    pass

class RunStatus(Enum):
    SUCCESS = 0
    ERROR = 1
    TIMEOUT = 2

class RunResult:
    def __init__(
            self,
            f: Optional[Callable] = None,
            f_name: str = "",
            params: list = [],
            status: RunStatus = RunStatus.SUCCESS
        ):
        self.f = f
        self.f_name = f_name
        self.params = params
        self.status = status
        self.dotted = True if isinstance(f_name, str) else False

    def __repr__(self) -> str:
        return f"RunResult(f={self.f}, f_name='{self.f_name}', params={self.params}, status={self.status})"