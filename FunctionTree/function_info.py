from dataclasses import dataclass, field
from typing import List, Set

@dataclass
class FunctionInfo:
    # qualname: str
    # module: str
    # cls: str | None
    # name: str
    # params: List[str]
    # filename: str
    # lineno: int
    # calls: Set[str] = field(default_factory=set)
    all_functions = {}

    def __init__(self, qualname, module, cls, name, params, filename, lineno):
        self.qualname = qualname
        self.module = module
        self.cls = cls
        self.name = name
        self.params = params
        self.filename = filename
        self.lineno = lineno
        self.calls = set()   # MUST manually initialize!

        FunctionInfo.all_functions[qualname] = self
