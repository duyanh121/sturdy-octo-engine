# ast_function_visitor.py
import ast
from typing import Dict, Optional
from FunctionTree.function_info import FunctionInfo


class FunctionCollector(ast.NodeVisitor):
    def __init__(self, module_name: str, filename: str):
        self.module_name = module_name
        self.filename = filename

        self.current_class: Optional[str] = None
        self.current_function_qualname: Optional[str] = None

        self.functions: Dict[str, FunctionInfo] = {}

    # --- Helpers ---

    def _make_qualname(self, func_name: str) -> str:
        if self.current_class:
            return f"{self.module_name}.{self.current_class}.{func_name}"
        else:
            return f"{self.module_name}.{func_name}"

    def _annotation_to_str(self, ann: Optional[ast.expr]) -> str:
        """Convert a parameter annotation AST node to a string."""
        if ann is None:
            return "Any"
        # Python 3.9+ has ast.unparse
        try:
            return ast.unparse(ann)
        except AttributeError:
            # Fallback: handle a few simple cases if you're on <3.9
            if isinstance(ann, ast.Name):
                return ann.id
            elif isinstance(ann, ast.Attribute):
                parts = []
                cur = ann
                while isinstance(cur, ast.Attribute):
                    parts.append(cur.attr)
                    cur = cur.value
                if isinstance(cur, ast.Name):
                    parts.append(cur.id)
                parts.reverse()
                return ".".join(parts)
            else:
                return "Any"

    def _extract_call_name(self, node: ast.expr) -> Optional[str]:
        """
        Get a *short* name from a Call node's .func.
        We don't fully resolve imports here, just grab a reasonable string.
        """
        if isinstance(node, ast.Name):
            return node.id                       # foo(...)
        elif isinstance(node, ast.Attribute):
            # e.g. np.sin -> "np.sin", self.foo -> "self.foo"
            parts = []
            cur = node
            while isinstance(cur, ast.Attribute):
                parts.append(cur.attr)
                cur = cur.value
            if isinstance(cur, ast.Name):
                parts.append(cur.id)
            parts.reverse()
            return ".".join(parts)
        else:
            return None

    # --- Visitors ---

    def visit_ClassDef(self, node: ast.ClassDef):
        prev_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = prev_class

    def _collect_params(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> Dict[str, str]:
        """
        Build a mapping {param_name: type_string} from function arguments.
        Handles posonlyargs, args, kwonlyargs, *args, **kwargs.
        """
        params: Dict[str, str] = {}

        def handle_arg(arg: ast.arg):
            params[arg.arg] = self._annotation_to_str(arg.annotation)

        # posonlyargs (Python 3.8+)
        for a in getattr(node.args, "posonlyargs", []):
            handle_arg(a)

        # normal args
        for a in node.args.args:
            handle_arg(a)

        # keyword-only args
        for a in node.args.kwonlyargs:
            handle_arg(a)

        # *args / **kwargs
        if node.args.vararg:
            name = "*" + node.args.vararg.arg
            params[name] = self._annotation_to_str(node.args.vararg.annotation)
        if node.args.kwarg:
            name = "**" + node.args.kwarg.arg
            params[name] = self._annotation_to_str(node.args.kwarg.annotation)

        return params

    def visit_FunctionDef(self, node: ast.FunctionDef):
        qualname = self._make_qualname(node.name)
        params = self._collect_params(node)

        info = FunctionInfo(
            qualname=qualname,
            module=self.module_name,
            cls=self.current_class,
            name=node.name,
            params=params,
            filename=self.filename,
            lineno=node.lineno,
        )
        self.functions[qualname] = info

        prev_func = self.current_function_qualname
        self.current_function_qualname = qualname
        self.generic_visit(node)
        self.current_function_qualname = prev_func

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        # Treat async functions the same way, reusing _collect_params
        qualname = self._make_qualname(node.name)
        params = self._collect_params(node)

        info = FunctionInfo(
            qualname=qualname,
            module=self.module_name,
            cls=self.current_class,
            name=node.name,
            params=params,
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
                self.functions[self.current_function_qualname].calls.add(callee_name)
        self.generic_visit(node)
