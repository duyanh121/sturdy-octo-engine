# ast_function_visitor.py
from __future__ import annotations
import ast
from typing import Dict, Optional
from .function_info import FunctionInfo


def annotation_to_str(node: ast.AST | None) -> str:
    """Convert a type annotation AST node to a readable string."""
    if node is None:
        return "Any"

    # Python 3.10+: int | None
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        return f"{annotation_to_str(node.left)} | {annotation_to_str(node.right)}"

    if isinstance(node, ast.Name):
        return node.id

    if isinstance(node, ast.Attribute):
        # e.g. typing.List, np.ndarray
        return f"{annotation_to_str(node.value)}.{node.attr}"

    if isinstance(node, ast.Subscript):
        # e.g. list[int], Dict[str, int]
        base = annotation_to_str(node.value)
        # slice shapes differ across versions; normalize
        sub = node.slice
        if isinstance(sub, ast.Tuple):
            inner = ", ".join(annotation_to_str(elt) for elt in sub.elts)
        else:
            inner = annotation_to_str(sub)
        return f"{base}[{inner}]"

    if isinstance(node, ast.Constant):
        # e.g. "MyClass" forward-ref, or None
        if node.value is None:
            return "None"
        if isinstance(node.value, str):
            return node.value
        return repr(node.value)

    if isinstance(node, ast.Tuple):
        return ", ".join(annotation_to_str(elt) for elt in node.elts)

    # fallback
    try:
        return ast.unparse(node)  # py3.9+
    except Exception:
        return "Any"


class FunctionCollector(ast.NodeVisitor):
    def __init__(self, module_name: str, filename: str):
        self.module_name = module_name
        self.filename = filename

        self.current_class: Optional[str] = None
        self.current_function_qualname: Optional[str] = None
        self.functions: dict[str, FunctionInfo] = {}

    def _make_qualname(self, func_name: str) -> str:
        if self.current_class:
            return f"{self.module_name}.{self.current_class}.{func_name}"
        return f"{self.module_name}.{func_name}"

    def _extract_call_name(self, node: ast.expr) -> str | None:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            parts = []
            cur: ast.AST = node
            while isinstance(cur, ast.Attribute):
                parts.append(cur.attr)
                cur = cur.value
            if isinstance(cur, ast.Name):
                parts.append(cur.id)
            parts.reverse()
            return ".".join(parts)
        return None

    def visit_ClassDef(self, node: ast.ClassDef):
        prev = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = prev

    def _collect_params_with_types(self, node: ast.arguments) -> Dict[str, str]:
        params: Dict[str, str] = {}

        # positional args
        for a in node.args:
            params[a.arg] = annotation_to_str(a.annotation)

        # vararg
        if node.vararg:
            params["*" + node.vararg.arg] = annotation_to_str(node.vararg.annotation)

        # kwonly
        for a in node.kwonlyargs:
            params[a.arg] = annotation_to_str(a.annotation)

        # kwarg
        if node.kwarg:
            params["**" + node.kwarg.arg] = annotation_to_str(node.kwarg.annotation)

        return params

    def _handle_function(self, node: ast.AST, name: str, args: ast.arguments, lineno: int):
        qualname = self._make_qualname(name)
        params = self._collect_params_with_types(args)

        info = FunctionInfo(
            qualname=qualname,
            module=self.module_name,
            cls=self.current_class,
            name=name,
            params=params,
            filename=self.filename,
            lineno=lineno,
        )
        self.functions[qualname] = info

        prev = self.current_function_qualname
        self.current_function_qualname = qualname
        self.generic_visit(node)
        self.current_function_qualname = prev

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._handle_function(node, node.name, node.args, node.lineno)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._handle_function(node, node.name, node.args, node.lineno)

    def visit_Call(self, node: ast.Call):
        if self.current_function_qualname is not None:
            callee_name = self._extract_call_name(node.func)
            if callee_name is not None:
                self.functions[self.current_function_qualname].calls.add(callee_name)
        self.generic_visit(node)
