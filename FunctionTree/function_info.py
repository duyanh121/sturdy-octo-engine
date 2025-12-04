from dataclasses import dataclass, field
from typing import Dict, Set, Optional


@dataclass
class FunctionInfo:
    qualname: str                 # e.g. "numpy.linalg.linalg.det"
    module: str                   # e.g. "numpy.linalg.linalg"
    cls: Optional[str]            # class name if method, else None
    name: str                     # short function name, e.g. "det"
    params: Dict[str, str]        # {"obj": "int", "kind": "str", ...}
    filename: str                 # file path
    lineno: int                   # line number
    calls: Set[str] = field(default_factory=set)  # short names of called functions