# ast_function_visitor.py
from __future__ import annotations
import ast
from .function_info import FunctionInfo

class FunctionCollector(ast.NodeVisitor):
    def __init__(self, module_name: str, filename: str):
        self.module_name = module_name
        self.filename = filename
        self.current_class: str | None = None
        self.current_function_qualname: str | None = None
        self.functions: dict[str, FunctionInfo] = {}

    def _make_qualname(self, func_name: str) -> str:
        if self.current_class:
            return f"{self.module_name}.{self.current_class}.{func_name}"
        return f"{self.module_name}.{func_name}"

    def _extract_call_name(self, node: ast.expr) -> str | None:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            parts = []
            cur = node
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

    def _collect_param_names(self, args: ast.arguments) -> list[str]:
        names = [a.arg for a in args.posonlyargs]
        names += [a.arg for a in args.args]
        if args.vararg:
            names.append("*" + args.vararg.arg)
        names += [a.arg for a in args.kwonlyargs]
        if args.kwarg:
            names.append("**" + args.kwarg.arg)
        return names

    def visit_FunctionDef(self, node: ast.FunctionDef):
        qualname = self._make_qualname(node.name)
        param_names = self._collect_param_names(node.args)

        # init params as param_name -> {}
        params_dict = {p: {} for p in param_names}

        info = FunctionInfo(
            qualname=qualname,
            module=self.module_name,
            cls=self.current_class,
            name=node.name,
            params=params_dict,
            filename=self.filename,
            lineno=node.lineno,
        )
        self.functions[qualname] = info

        prev_func = self.current_function_qualname
        self.current_function_qualname = qualname
        self.generic_visit(node)
        self.current_function_qualname = prev_func

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        # same logic
        qualname = self._make_qualname(node.name)
        param_names = self._collect_param_names(node.args)

        # init params as param_name -> {}
        params_dict = {p: {} for p in param_names}

        info = FunctionInfo(
            qualname=qualname,
            module=self.module_name,
            cls=self.current_class,
            name=node.name,
            params=params_dict,
            filename=self.filename,
            lineno=node.lineno,
        )
        self.functions[qualname] = info

        prev_func = self.current_function_qualname
        self.current_function_qualname = qualname
        self.generic_visit(node)
        self.current_function_qualname = prev_func

    def visit_Call(self, node: ast.Call):
        if self.current_function_qualname is not None:
            callee_name = self._extract_call_name(node.func)
            if callee_name is not None:
                # FunctionInfo.calls is a set, OK
                self.functions[self.current_function_qualname].calls.add(callee_name)
        self.generic_visit(node)
