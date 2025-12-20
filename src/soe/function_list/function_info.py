# function_info.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Set, Optional

@dataclass
class FunctionInfo:
    qualname: str
    module: str
    cls: Optional[str]
    name: str
    # param_name -> {type_name -> count}
    params: Dict[str, Dict[str, int]] = field(default_factory=dict)

    filename: str = ""
    lineno: int = 0

    # short names of called functions (store as set for dedup)
    calls: Set[str] = field(default_factory=set)

    def ensure_param(self, param_name: str) -> None:
        """Make sure param exists in params dict."""
        if param_name not in self.params:
            self.params[param_name] = {}

    def bump_param_type(self, param_name: str, type_name: str, delta: int = 1) -> None:
        """Increment count for a param receiving a certain type."""
        self.ensure_param(param_name)
        self.params[param_name][type_name] = self.params[param_name].get(type_name, 0) + delta

    def to_json_dict(self, dep_graph: dict[str, set[str]] | None = None) -> dict:
        return {
            "params": self.params,
            "filename": self.filename,
            "lineno": self.lineno,
            "calls": sorted((dep_graph.get(self.qualname, set()) if dep_graph else set())),
        }
