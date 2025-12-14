import os
from .function_info import FunctionInfo
import ast
from .ast_function_visitor import FunctionCollector
from .ast_type_samples import collect_type_samples_for_repo
from collections import defaultdict
import json
from pathlib import Path

def module_name_from_path(root_dir: str, file_path: str) -> str:
    """
    Convert a file path under root_dir to a Python module name.
    e.g. root_dir="/path/to/numpy", file_path="/path/to/numpy/linalg/linalg.py"
         -> "numpy.linalg.linalg"
    """
    rel = os.path.relpath(file_path, root_dir)
    no_ext = os.path.splitext(rel)[0]
    parts = no_ext.split(os.sep)
    return ".".join(parts)

def collect_functions_in_repo(root_dir: str) -> dict[str, FunctionInfo]:
    all_functions: dict[str, FunctionInfo] = {}

    for dirpath, dirnames, filenames in os.walk(root_dir):
        
        for fname in filenames:
            if not fname.endswith(".py"):
                continue
            fullpath = os.path.join(dirpath, fname)
            try:
                with open(fullpath, "r", encoding="utf-8") as f:
                    src = f.read()
            except (UnicodeDecodeError, OSError):
                continue  # skip weird files

            try:
                tree = ast.parse(src, filename=fullpath)
            except SyntaxError:
                continue  # skip files that don't parse

            modname = module_name_from_path(root_dir, fullpath)
            collector = FunctionCollector(modname, fullpath)
            collector.visit(tree)

            all_functions.update(collector.functions)

    return all_functions


def build_dependency_graph(all_functions: dict[str, FunctionInfo]) -> dict[str, set[str]]:
    # Graph: caller_qualname -> set of callee_qualnames
    graph: dict[str, set[str]] = defaultdict(set)

    # Map short name -> list of fully qualified names
    name_index: dict[str, list[str]] = defaultdict(list)
    for qname, finfo in all_functions.items():
        name_index[finfo.name].append(qname)

    for caller_qname, finfo in all_functions.items():
        for call in finfo.calls:
            # call might look like "foo" or "np.sin" or "self.bar"
            short = call.split(".")[-1]  # use last part as short name

            if short in name_index:
                # Naive: link to all functions with that short name
                for callee_qname in name_index[short]:
                    graph[caller_qname].add(callee_qname)
        # ensure caller exists in graph
        graph.setdefault(caller_qname, set())

    return graph


def is_public_function(finfo: FunctionInfo) -> bool:
    # Basic heuristic: no leading underscore
    if finfo.name.startswith("_"):
        return False
    # You may also filter internal modules, e.g. "numpy._core"
    if ". _" in finfo.module.replace("_", " _"):  # crude, adjust as needed
        return False
    return True


def generate_function_list(path: str) -> dict[str, dict]: 
    '''
    Generate a new function tree
    
    :param path: path to the repo
    :type path: str
    '''

    curr_dir = os.path.dirname(os.path.abspath(__file__)) 
    PROJECT_ROOT = Path(__file__).resolve().parents[3]
    root = os.path.abspath(os.path.join(PROJECT_ROOT, path))   
    public_only = True            # or False
    print(root)
    all_funcs = collect_functions_in_repo(root)


    if public_only:
        funcs = {q: f for q, f in all_funcs.items() if is_public_function(f)}
    else:
        funcs = all_funcs

    dep_graph = build_dependency_graph(all_funcs)  # can also restrict to funcs

    # Example: dump minimal info for fuzzing
    out = {
        "functions": {
            q: {
                "params": f.params,
                "filename": f.filename,
                "lineno": f.lineno,
                "calls": sorted(dep_graph.get(q, [])),
            }
            for q, f in funcs.items()
        }
    }

    output_path = os.path.join(curr_dir, "function_list.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print("Saved to:", output_path)

    return out["functions"]


def generate_type_sample(path: str) -> dict[str, list]:
    '''
    Generate a new type sample tree
    
    :param path: path to the repo
    :type path: str
    '''

    curr_dir = os.path.dirname(os.path.abspath(__file__)) 
    PROJECT_ROOT = Path(__file__).resolve().parents[3]
    root = os.path.abspath(os.path.join(PROJECT_ROOT, path))   


    type_samples = collect_type_samples_for_repo(root)

    def json_safe(obj):
        # Primitive-safe
        if obj is None or isinstance(obj, (int, float, str, bool)):
            return obj

        # set → list
        if isinstance(obj, set):
            return list(obj)

        # bytes → hex or utf-8
        if isinstance(obj, bytes):
            try:
                return obj.decode("utf-8")
            except UnicodeDecodeError:
                return obj.hex()

        # complex → structured dict
        if isinstance(obj, complex):
            return {
                "__type__": "complex",
                "real": obj.real,
                "imag": obj.imag,
            }

        # list / tuple
        if isinstance(obj, (list, tuple)):
            return [json_safe(x) for x in obj]

        # dict
        if isinstance(obj, dict):
            return {str(k): json_safe(v) for k, v in obj.items()}

        # fallback
        return str(obj)
        
    print(type_samples)
    output_path = os.path.join(curr_dir, "type_samples.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(json_safe(type_samples), f, indent=2)
    print("Saved to:", output_path)

    return type_samples



def get_function_list_from_json() -> dict[str, dict]:  # Load existing function tree from JSON
    with open("src\\soe\\function_list\\function_list.json", 'r') as file:
        function_list = json.load(file)["functions"]
    
    # Output format: dict{str, dict[str, Any]}
    # {'_pyinstaller.tests.test_pyinstaller.test_pyinstaller': 
    # {'params': ['mode', 'tmp_path'], 
    # 'filename': 'd:\\All Python Project\\UROP\\repos\\numpy\\_pyinstaller\\tests\\test_pyinstaller.py', 
    # 'lineno': 13, 
    # 'calls': ['_core.defchararray.chararray.strip', '_core.strings.strip', 'f2py.diagnose.run']
    #,...}
    return function_list


