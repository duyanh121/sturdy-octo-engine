from __future__ import annotations

import ast
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, DefaultDict


# --- Helpers: map "type name" -> example values you want to store ---
DEFAULT_SAMPLES: dict[str, Any] = {
    "int": 0,
    "float": 0.0,
    "bool": False,
    "str": "",
    "bytes": b"",
    "none": None,
    "list": [],
    "tuple": (),
    "set": set(),
    "dict": {},
}


def safe_add_sample(type_list: DefaultDict[str, list[Any]], type_name: str, sample: Any, limit: int = 100) -> None:
    """Add up to `limit` samples per type_name, avoid duplicates by repr."""
    if type_name is None:
        return
    bucket = type_list[type_name]
    if len(bucket) >= limit:
        return
    # Deduplicate cheaply
    srepr = repr(sample)
    if any(repr(x) == srepr for x in bucket):
        return
    bucket.append(sample)


def annotation_to_str(node: ast.AST) -> str | None:
    """Convert a type annotation AST to a readable string (best-effort)."""
    try:
        # Python 3.9+: ast.unparse exists
        return ast.unparse(node)  # type: ignore[attr-defined]
    except Exception:
        # Minimal fallback
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return node.attr
        return None


class LocalTypeSampleCollector(ast.NodeVisitor):
    """
    Collects type samples from local variable assignments inside functions.
    Stores results in `type_list`: dict[str, list[Any]] mapping type_name -> sample values.
    """

    def __init__(self) -> None:
        self.type_list: DefaultDict[str, list[Any]] = defaultdict(list)
        self._in_function: bool = False

    # ------------------------
    # Visiting boundaries
    # ------------------------
    def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:
        prev = self._in_function
        self._in_function = True
        self.generic_visit(node)
        self._in_function = prev

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> Any:
        prev = self._in_function
        self._in_function = True
        self.generic_visit(node)
        self._in_function = prev

    # ------------------------
    # Assignments / annotated assignments
    # ------------------------
    def visit_Assign(self, node: ast.Assign) -> Any:
        if not self._in_function:
            return  # only local vars in functions (change if you want module-level too)

        inferred = self._infer_type_and_sample(node.value)
        if inferred:
            type_name, sample = inferred
            safe_add_sample(self.type_list, type_name, sample)

        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> Any:
        if not self._in_function:
            return

        # Use annotation as type hint label
        ann = annotation_to_str(node.annotation)
        if ann:
            # Add a default sample for that annotation if we have one, else store annotation string itself
            key = ann.split(".")[-1].lower()
            if key in DEFAULT_SAMPLES:
                safe_add_sample(self.type_list, key, DEFAULT_SAMPLES[key])
            else:
                # We can’t construct arbitrary types safely; store the annotation string as “sample”
                safe_add_sample(self.type_list, ann, ann)

        # Also try to infer from value if present
        if node.value is not None:
            inferred = self._infer_type_and_sample(node.value)
            if inferred:
                type_name, sample = inferred
                safe_add_sample(self.type_list, type_name, sample)

        self.generic_visit(node)

    # ------------------------
    # Core inference
    # ------------------------
    def _infer_type_and_sample(self, value: ast.AST) -> tuple[str, Any] | None:
        # Literal constants
        if isinstance(value, ast.Constant):
            v = value.value
            if v is None:
                return ("none", None)
            if isinstance(v, bool):
                return ("bool", v)
            if isinstance(v, int):
                return ("int", v)
            if isinstance(v, float):
                return ("float", v)
            if isinstance(v, str):
                return ("str", v)
            if isinstance(v, bytes):
                return ("bytes", v)
            return (type(v).__name__, v)

        # Containers: list/tuple/set/dict
        if isinstance(value, ast.List):
            # sample empty or a 1-element sample
            if value.elts:
                return ("list", [self._sample_from_expr(value.elts[0])])
            return ("list", [])
        if isinstance(value, ast.Tuple):
            if value.elts:
                return ("tuple", (self._sample_from_expr(value.elts[0]),))
            return ("tuple", ())
        if isinstance(value, ast.Set):
            if value.elts:
                return ("set", {self._sample_from_expr(value.elts[0])})
            return ("set", set())
        if isinstance(value, ast.Dict):
            if value.keys and value.values and value.keys[0] is not None:
                return ("dict", {self._sample_from_expr(value.keys[0]): self._sample_from_expr(value.values[0])})
            return ("dict", {})

        # Unary minus etc. (e.g. -1)
        if isinstance(value, ast.UnaryOp) and isinstance(value.op, (ast.USub, ast.UAdd)):
            inner = self._infer_type_and_sample(value.operand)
            if inner and inner[0] in ("int", "float"):
                t, s = inner
                try:
                    return (t, -s if isinstance(value.op, ast.USub) else +s)
                except Exception:
                    return inner

        # Simple constructor calls: int(...), list(...), dict(...)
        if isinstance(value, ast.Call):
            fn_name = self._call_name(value.func)
            if fn_name:
                short = fn_name.split(".")[-1].lower()
                if short in DEFAULT_SAMPLES:
                    # For list(tuple/set/dict) you could attempt to sample argument too, but keep it safe:
                    return (short, DEFAULT_SAMPLES[short])

        return None

    def _call_name(self, node: ast.AST) -> str | None:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            # e.g. builtins.int or something.attr
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

    def _sample_from_expr(self, node: ast.AST) -> Any:
        # Best-effort sample for container elements
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name):
            # unknown; return a placeholder
            return f"<{node.id}>"
        if isinstance(node, ast.Call):
            fn = self._call_name(node.func) or "call"
            return f"<{fn}()>"
        return "<expr>"


def collect_type_samples_for_repo(root_dir: str | Path) -> dict[str, list[Any]]:
    """
    Walk all .py files under root_dir, parse AST, collect local variable type samples.
    """
    root = Path(root_dir)
    collector = LocalTypeSampleCollector()

    for pyfile in root.rglob("*.py"):
        try:
            src = pyfile.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        try:
            tree = ast.parse(src, filename=str(pyfile))
        except SyntaxError:
            continue
        collector.visit(tree)

    # Convert defaultdict to plain dict
    return {k: v for k, v in collector.type_list.items()}
