import ast
from function_info import FunctionInfo

class FunctionCollector(ast.NodeVisitor):
    def __init__(self, module_name: str, filename: str):
        self.module_name = module_name
        self.filename = filename

        self.current_class: str | None = None
        self.current_function_qualname: str | None = None

        self.functions: dict[str, FunctionInfo] = {}

    # --- Helpers ---

    def _make_qualname(self, func_name: str) -> str:
        if self.current_class:
            return f"{self.module_name}.{self.current_class}.{func_name}"
        else:
            return f"{self.module_name}.{func_name}"

    def _extract_call_name(self, node: ast.expr) -> str | None:
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

    def visit_FunctionDef(self, node: ast.FunctionDef):
        qualname = self._make_qualname(node.name)

        # Collect parameter names
        params = [arg.arg for arg in node.args.args]
        # You can also include vararg, kwonlyargs, kwarg if you want:
        if node.args.vararg:
            params.append("*" + node.args.vararg.arg)
        if node.args.kwarg:
            params.append("**" + node.args.kwarg.arg)

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
        # Treat async functions the same way
        qualname = self._make_qualname(node.name)

        # Collect parameter names
        params = [arg.arg for arg in node.args.args]
        # You can also include vararg, kwonlyargs, kwarg if you want:
        if node.args.vararg:
            params.append("*" + node.args.vararg.arg)
        if node.args.kwarg:
            params.append("**" + node.args.kwarg.arg)

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
