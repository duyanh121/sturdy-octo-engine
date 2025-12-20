import inspect
import random
import sys
import os
import json
import importlib
import multiprocessing
import ast
import textwrap
from collections import defaultdict
if len(sys.argv) > 1:
    potential_path = sys.argv[1]
    if os.path.exists(potential_path) and os.path.isdir(potential_path):
        sys.path.insert(0, os.path.abspath(potential_path))
        #print(f"[*] Pre-loaded path: {sys.path[0]}")
import numpy as np

# --- 1. Top-Level Definitions (Must be picklable) ---

class FuzzGenerator:
    def __init__(self):
        self.universe = [int, float, str, bool, type(None), list, tuple, dict, np.int32, np.float64, np.complex128, np.ndarray]

    def get_random_type(self): 
        return random.choice(self.universe)

    def generate_value(self, t):
        try:
            if t is int: return random.randint(-10, 10)
            if t is float: return random.uniform(-10, 10)
            if t is str: return "fuzz"
            if t is bool: return True
            if t is list: return [1, 2]
            if t is tuple: return (1, 2)
            if t is dict: return {"k": 1}
            if t is np.int32: return np.int32(5)
            if t is np.float64: return np.float64(0.5)
            if t is np.ndarray: return np.array([1, 2])
            return None
        except: return 0

def make_concrete(abstract_cls):
    if not inspect.isabstract(abstract_cls): return abstract_cls
    def dummy_method(self, *args, **kwargs): return [1] 
    def dummy_property(self): return np.array([0, 1])
    impl_methods = {}
    for name in abstract_cls.__abstractmethods__:
        base_attr = getattr(abstract_cls, name, None)
        if isinstance(base_attr, property): impl_methods[name] = property(dummy_property)
        else: impl_methods[name] = dummy_method
    return type(f"Concrete_{abstract_cls.__name__}", (abstract_cls,), impl_methods)

# --- 2. AST Analysis (Static) ---

class CallVisitor(ast.NodeVisitor):
    def __init__(self):
        self.calls = []

    def visit_Call(self, node):
        # Extract the name of the function being called
        func_name = ""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            # Handles obj.method() or module.func()
            parts = []
            curr = node.func
            while isinstance(curr, ast.Attribute):
                parts.append(curr.attr)
                curr = curr.value
            if isinstance(curr, ast.Name):
                parts.append(curr.id)
            func_name = ".".join(reversed(parts))
        
        if func_name:
            self.calls.append(func_name)
        self.generic_visit(node)

def analyze_static(func_obj):
    """
    Returns (lineno, list_of_calls)
    """
    try:
        lines, start_lineno = inspect.getsourcelines(func_obj)
        source_code = "".join(lines)
        
        # Parse the source code of the function
        # We wrap in dedent to handle indented methods inside classes
        tree = ast.parse(textwrap.dedent(source_code))
        
        visitor = CallVisitor()
        visitor.visit(tree)
        
        return start_lineno, visitor.calls
    except Exception:
        # If source is not available (e.g. C-extension or dynamic), return defaults
        return -1, []

# --- 3. The Worker Task (Runs inside the Sandbox) ---
def worker_fuzz_task(repo_root, module_name, class_name, func_name, iterations, result_queue):
    sys.path.insert(0, repo_root)
    sys.stdout = open(os.devnull, 'w')
    sys.stderr = open(os.devnull, 'w')

    local_success_log = []

    try:
        mod = importlib.import_module(module_name)
        target_func = None
        instance = None
        
        if class_name:
            cls = getattr(mod, class_name)
            ConcreteCls = make_concrete(cls)
            try:
                instance = ConcreteCls()
            except:
                try: instance = ConcreteCls(np.array([1,2]))
                except: return 
            
            target_func = getattr(instance, func_name)
        else:
            target_func = getattr(mod, func_name)

        gen = FuzzGenerator()
        sig = inspect.signature(target_func)
        params = list(sig.parameters.values())
        
        for _ in range(iterations):
            args = []
            current_types = {}
            
            for p in params:
                if p.name in ['self', 'cls']: continue
                t = gen.get_random_type()
                if p.kind == p.VAR_POSITIONAL or p.kind == p.VAR_KEYWORD: continue

                val = gen.generate_value(t)
                args.append(val)
                current_types[p.name] = t.__name__
            
            try:
                target_func(*args)
                local_success_log.append(current_types)
            except Exception:
                pass

        result_queue.put(local_success_log)

    except Exception:
        pass

# --- 4. The Safe Runner ---
def run_safely(repo_root, module_name, class_name, func_name, iterations=10):
    queue = multiprocessing.Queue()
    p = multiprocessing.Process(
        target=worker_fuzz_task, 
        args=(repo_root, module_name, class_name, func_name, iterations, queue)
    )
    p.start()
    p.join(timeout=1.0) 
    
    if p.is_alive():
        p.terminate()
        p.join()
        return "TIMEOUT", []
    
    if p.exitcode != 0:
        return "CRASH", [] 
    
    try:
        if not queue.empty():
            return "SUCCESS", queue.get()
        else:
            return "SUCCESS", [] 
    except:
        return "ERROR", []

def update_stats(final_results, module_name, class_name, func_name, static_info, success_list):
    """
    Updates the nested dictionary structure requested:
    root -> functions -> module.func_name -> {params, lineno, calls}
    root -> class_methods -> module.ClassName -> method_name -> {params, lineno, calls}
    """
    target_block = None

    if class_name:
        # Structure: class_methods -> module.ClassName -> method_name -> block
        full_class_name = f"{module_name}.{class_name}"
        if full_class_name not in final_results["class_methods"]:
            final_results["class_methods"][full_class_name] = {}
        
        if func_name not in final_results["class_methods"][full_class_name]:
            final_results["class_methods"][full_class_name][func_name] = {
                "params": {},
                "lineno": static_info['lineno'],
                "calls": static_info['calls']
            }
        target_block = final_results["class_methods"][full_class_name][func_name]

    else:
        # Structure: functions -> module.func_name -> block
        full_func_name = f"{module_name}.{func_name}"
        if full_func_name not in final_results["functions"]:
            final_results["functions"][full_func_name] = {
                "params": {},
                "lineno": static_info['lineno'],
                "calls": static_info['calls']
            }
        target_block = final_results["functions"][full_func_name]

    # Populate the "params" dictionary inside the target block
    param_stats = target_block["params"]
    for run in success_list:
        for param, type_name in run.items():
            if param not in param_stats:
                param_stats[param] = defaultdict(int)
            param_stats[param][type_name] += 1

def generate_function_list(repo_root, iterations=20):
    repo_root = os.path.abspath(repo_root)
    if repo_root not in sys.path: 
        sys.path.insert(0, repo_root)
    
    print(f"[*] Root: {repo_root}")
    print(f"[*] Mode: Nested Structure (functions/class_methods) with Full Paths")

    # --- RESTORED ROOT STRUCTURE ---
    final_results = {
        "functions": {},
        "class_methods": {}
    }

    IGNORE_DIRS = {'tests', 'testing', 'benchmarks', 'examples', '_examples', 'conftest', 
                   'cython', 'include', 'distutils', 'f2py', '.git', '__pycache__', 'venv', 'env'}

    modules_processed = 0
    crashes_detected = 0

    class DefaultEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, defaultdict): return dict(obj)
            return super().default(obj)

    for root, dirs, files in os.walk(repo_root):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        for file in files:
            if file.endswith(".py") and not file.startswith("test") and not file.startswith("setup"):
                rel_path = os.path.relpath(os.path.join(root, file), repo_root)
                module_string = rel_path.replace(os.path.sep, ".")[:-3]
                
                if any(x in module_string.split(".") for x in IGNORE_DIRS): continue

                print(f"\r[>] Scanning: {module_string:<60}", end="")
                
                try:
                    save_stdout = sys.stdout
                    sys.stdout = open(os.devnull, 'w')
                    mod = importlib.import_module(module_string)
                    sys.stdout = save_stdout
                except: 
                    sys.stdout = save_stdout
                    continue

                targets = []
                
                # Get Classes
                try:
                    classes = [m for name, m in inspect.getmembers(mod, inspect.isclass) if m.__module__ == mod.__name__]
                    for cls in classes:
                        methods = inspect.getmembers(cls, predicate=lambda x: inspect.isfunction(x) or inspect.ismethod(x))
                        for name, func_obj in methods:
                            if not name.startswith("__") or name == '__call__':
                                targets.append((cls.__name__, name, func_obj))
                except: pass
                
                # Get Functions
                try:
                    funcs = [f for name, f in inspect.getmembers(mod, inspect.isfunction) if f.__module__ == mod.__name__]
                    for f in funcs:
                        targets.append((None, f.__name__, f))
                except: pass

                # Fuzz Targets
                for cls_name, func_name, func_obj in targets:
                    # 1. Static Analysis
                    lineno, calls = analyze_static(func_obj)
                    static_info = {"lineno": lineno, "calls": calls}

                    # 2. Dynamic Fuzzing
                    status, results = run_safely(repo_root, module_string, cls_name, func_name, iterations)
                    
                    if status == "SUCCESS":
                        update_stats(final_results, module_string, cls_name, func_name, static_info, results)
                    elif status == "CRASH":
                        crashes_detected += 1
                
                modules_processed += 1
                if modules_processed % 5 == 0:
                    with open("fuzz_results.json", 'w') as f:
                        json.dump(final_results, f, indent=4, cls=DefaultEncoder)

    print(f"\n\n[*] Fuzzing complete.")
    print(f"[*] Total Crashes survived: {crashes_detected}")
    
    with open("fuzz_results.json", 'w') as f:
         json.dump(final_results, f, indent=4, cls=DefaultEncoder)

    return final_results

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fuzzer9.py <repo_root>")
    else:
        results_dict = generate_function_list(sys.argv[1])