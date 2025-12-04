import os
from FunctionTree.function_info import FunctionInfo
import ast
from FunctionTree.ast_function_visitor import FunctionCollector
from collections import defaultdict
import json


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


def generate_function_tree(path: str) -> None: 
    '''
    Generate a new function tree
    
    :param path: path to the repo
    :type path: str
    '''

    curr_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join("..", path)   # go up one folder and into ExampleRepos
    root = os.path.abspath(os.path.join(curr_dir, path))     
    public_only = True            # or False

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

    output_path = os.path.join(curr_dir, "function_tree.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print("Saved to:", output_path)



def get_function_tree() -> dict[str, dict]:  # Load existing function tree from JSON
    with open("FunctionTree\\function_tree.json", 'r') as file:
        function_list = json.load(file)["functions"]
    
    # Output format: dict{str, dict[str, Any]}
    # {'_pyinstaller.tests.test_pyinstaller.test_pyinstaller': 
    # {'params': ['mode', 'tmp_path'], 
    # 'filename': 'd:\\All Python Project\\UROP\\repos\\numpy\\_pyinstaller\\tests\\test_pyinstaller.py', 
    # 'lineno': 13, 
    # 'calls': ['_core.defchararray.chararray.strip', '_core.strings.strip', 'f2py.diagnose.run']
    #,...}
    return function_list


