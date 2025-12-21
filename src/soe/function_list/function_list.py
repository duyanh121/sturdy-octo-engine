# function_list.py
import os
import ast
import json
from pathlib import Path
from collections import defaultdict
from .function_info import FunctionInfo
from .ast_function_visitor import FunctionCollector


def module_name_from_path(root_dir: str, file_path: str) -> str:
    rel = os.path.relpath(file_path, root_dir)
    no_ext = os.path.splitext(rel)[0]
    parts = no_ext.split(os.sep)
    return ".".join(parts)

def collect_functions_in_repo(root_dir: str) -> dict[str, FunctionInfo]:
    all_functions: dict[str, FunctionInfo] = {}

    for dirpath, _, filenames in os.walk(root_dir):
        for fname in filenames:
            if not fname.endswith(".py"):
                continue
            fullpath = os.path.join(dirpath, fname)

            try:
                with open(fullpath, "r", encoding="utf-8") as f:
                    src = f.read()
            except (UnicodeDecodeError, OSError):
                continue

            try:
                tree = ast.parse(src, filename=fullpath)
            except SyntaxError:
                continue

            modname = module_name_from_path(root_dir, fullpath)
            collector = FunctionCollector(modname, fullpath)
            collector.visit(tree)
            all_functions.update(collector.functions)

    return all_functions

def build_dependency_graph(all_functions: dict[str, FunctionInfo]) -> dict[str, set[str]]:
    graph: dict[str, set[str]] = defaultdict(set)

    name_index: dict[str, list[str]] = defaultdict(list)
    for qname, finfo in all_functions.items():
        name_index[finfo.name].append(qname)

    for caller_qname, finfo in all_functions.items():
        for call in finfo.calls:
            short = call.split(".")[-1]
            if short in name_index:
                for callee_qname in name_index[short]:
                    graph[caller_qname].add(callee_qname)
        graph.setdefault(caller_qname, set())

    return graph

def is_public_function(finfo: FunctionInfo) -> bool:
    if finfo.name.startswith("_"):
        return False
    if ". _" in finfo.module.replace("_", " _"):
        return False
    return True


def generate_function_list(path: Path) -> dict[str, dict]:
    PROJECT_ROOT = Path(__file__).resolve().parents[3]
    root = os.path.abspath(PROJECT_ROOT / path)
    public_only = True

    all_funcs = collect_functions_in_repo(root)
    funcs = {q: f for q, f in all_funcs.items() if is_public_function(f)} if public_only else all_funcs
    dep_graph = build_dependency_graph(all_funcs)

    out = {
        "functions": {
            q: {
                "params": f.params,                     # ✅ param -> {type: count}
                "filename": f.filename,
                "lineno": f.lineno,
                "calls": sorted(dep_graph.get(q, set())),# ✅ list for JSON
            }
            for q, f in funcs.items()
        }
    }

    curr_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(curr_dir, "function_list.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print("Saved to:", output_path)

    return out["functions"]
