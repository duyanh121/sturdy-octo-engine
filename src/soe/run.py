import sys
import inspect
import importlib
import json
from pathlib import Path

from soe._global import get_function_list, get_type_list, set_function_list, set_type_list, get_dir_path
from soe._types import RunUnableToResolve, RunTimeout, RunStatus, RunResult
import logging

from soe.function_list.function_list import dump_function_list



logger = logging.getLogger('run')
type_list = get_type_list()
function_list = get_function_list()


# A helper index to prevent duplicates:
#   _type_seen[type_class] = set of fingerprints (strings)
_type_seen = {}  # {<class 'int'>: {"1","2"}, <class 'numpy.ndarray'>: {"...hash..."}, ...}


MAX_SAMPLES_PER_TYPE = 50

# ----------------------------
# Duplicate-safe fingerprinting
# ----------------------------
def _fingerprint(val) -> str:
    """
    Return a stable-ish fingerprint for a value so we can prevent duplicates.
    - Primitives: exact value
    - Lists/tuples/dicts: structural fingerprint
    - numpy.ndarray: dtype+shape+bytes hash (fallback to repr if needed)
    - Other objects: module.qualname + repr()
    """
    if val is None or isinstance(val, (int, float, str, bool)):
        return f"{type(val).__name__}:{val!r}"

    if isinstance(val, (list, tuple)):
        inner = ",".join(_fingerprint(x) for x in val)
        return f"{type(val).__name__}:[{inner}]"

    if isinstance(val, dict):
        # sort by key string to make deterministic
        items = sorted(val.items(), key=lambda kv: str(kv[0]))
        inner = ",".join(f"{str(k)!r}:{_fingerprint(v)}" for k, v in items)
        return f"dict:{{{inner}}}"

    cls = val.__class__

    # fallback
    return f"{cls.__module__}.{cls.__qualname__}:{repr(val)}"


def type_key(val):
    """
    Returns the actual class type of `val` as the key.
    Examples:
      3                -> <class 'int'>
      "hi"             -> <class 'str'>
      [1,2]            -> <class 'list'>
      np.array([1,2])  -> <class 'numpy.ndarray'>
      pd.DataFrame(...) -> <class 'pandas.core.frame.DataFrame'>
      None             -> <class 'NoneType'>
    """
    return val.__class__


def _add_type_sample(val):
    k = type_key(val)
    bucket = type_list.setdefault(k, [])
    if len(bucket) >= MAX_SAMPLES_PER_TYPE:
        return

    seen = _type_seen.setdefault(k, set())
    fp = _fingerprint(val)

    if fp in seen:
        return  # duplicate, skip

    bucket.append(val)
    seen.add(fp)


def resolve_by_dotted_name(dotted: str):
    """
    Resolve a callable from a dotted name.
    Works for:
      - functions: test_src_1.main.param_func
      - class methods: test_src_2.main.SampleClass.method_one
    """
    # Add path to sys.path
    fuzz_dir_str = str(get_dir_path().resolve())
    if fuzz_dir_str not in sys.path:
        sys.path.insert(0, fuzz_dir_str)

    parts = dotted.split(".")

    last_mod_exc = None
    # Find the longest importable module prefix.
    # Example:
    #   tests.test_repo.test_src_2.main.SampleClass.method_one
    # module prefix is:
    #   tests.test_repo.test_src_2.main
    for i in range(len(parts), 0, -1):
        mod_name = ".".join(parts[:i])
        try:
            mod = importlib.import_module(mod_name)
            attr_parts = parts[i:]  # remaining attributes
            obj = mod
            for a in attr_parts:
                obj = getattr(obj, a)

            if not callable(obj):
                raise RunUnableToResolve(f"{dotted} resolved to non-callable: {type(obj)}")

            # If it's an unbound function pulled from a class, return it as a function object
            # (accessing via class gives you a function; via instance gives a bound method).
            # Here, we always traverse from module -> class -> function, so this is already "function".
            return obj

        except ModuleNotFoundError as e:
            last_mod_exc = e
            continue
        except AttributeError as e:
            # Module imported, but attribute chain failed: that's a real resolve failure.
            raise RunUnableToResolve(f"Attribute not found while resolving {dotted}: {e}") from e
        except Exception as e:
            raise RunUnableToResolve(f"Failed to resolve {dotted}: {e}") from e

    # No module prefix could be imported
    if last_mod_exc:
        raise RunUnableToResolve(f"Cannot import any module prefix of {dotted}: {last_mod_exc}") from last_mod_exc
    raise RunUnableToResolve(f"Cannot resolve: {dotted}")


# remove
def json_safe(obj):
    if obj is None or isinstance(obj, (int, float, str, bool)):
        return obj

    if isinstance(obj, list):
        return [json_safe(x) for x in obj]

    if isinstance(obj, dict):
        return {str(k): json_safe(v) for k, v in obj.items()}

    cls = obj.__class__

    # Fallback for non-serializable objects
    return {
        "__type__": f"{cls.__module__}.{cls.__qualname__}",
        "repr": repr(obj)
    }

# remove
def dump_type_list_to_json(type_list, path="type_list.json"):
    with open(path, "w", encoding="utf-8") as f:
        # Convert class type keys to string representation for JSON serialization
        json_dict = {}
        for cls_type, vals in type_list.items():
            type_key_str = f"{cls_type.__module__}.{cls_type.__qualname__}" if hasattr(cls_type, "__module__") else str(cls_type)
            json_dict[type_key_str] = [json_safe(v) for v in vals]
        json.dump(json_dict, f, indent=2)


def f_run(f_name, params=[]) -> tuple[RunResult, dict]:
    '''
    Wrapper for run function to match other module style

    :param f_name: function name from function list
    :param params: parameters to run with

    :return: type list
    '''
    if params is None:
        params = []

    target_fn = resolve_by_dotted_name(f_name)

    result = run(target_fn, params)
    result[0].f_name = f_name
    return result


def type_name(val) -> str:
    """Return the string key used in function_list/type_list."""

    t = type(val)

    # Common builtins: "int", "str", "list", ...
    if t.__module__ == "builtins":
        return t.__name__

    # Fallback: class name only (you can change to module-qualified if you want)
    return t.__name__


def _inc_param_type(func_name: str, param_name: str, val):
    """
    function_list["functions"][func_name]["params"][param_name][type_str] += 1
    Add new type keys dynamically if needed.
    """
    try:
        type_k = type_name(val)
        function_list = get_function_list()
        params = function_list["functions"][func_name].setdefault("params", {})
        param_types = params.setdefault(param_name, {})
        param_types[type_k] = param_types.get(type_k, 0) + 1
    except Exception as e:
        print(f"Error in _inc_param_type: {e}")
        import traceback
        traceback.print_exc()



def merge_type_dicts_unique(d1, d2):
    merged = {}

    for key in set(d1) | set(d2):
        combined = d1.get(key, []) + d2.get(key, [])

        seen = set()
        unique_items = []

        for item in combined:
            # Make unhashable items hashable by converting to a tuple of sorted items
            if isinstance(item, dict):
                marker = tuple(sorted(item.items()))
            else:
                marker = item

            if marker not in seen:
                seen.add(marker)
                unique_items.append(item)

        merged[key] = unique_items

    return merged


def run(target_fn, params=[]) -> tuple[RunResult, dict]:
    '''
    Run function with given parameters and get type samples

    :param target_fn: function
    :param params: parameters to run with

    :return: type list
    '''

    if params is None:
        params = []

    # Track frames descended from this run call
    tracked_frames = set()
    locals_seen_keys = {}  # id(frame) -> set(keys)

    def tracer(frame, event, arg):
        if event == "call":
            code = frame.f_code
            module_name = frame.f_globals.get('__name__', '')
            qualname = code.co_qualname
            callee_name = f"{module_name}.{qualname}" if module_name else qualname

            # Start tracking once we enter target function; then include children
            is_target_entry = (code.co_name == target_fn.__name__ and frame.f_code is target_fn.__code__)
            is_child_of_tracked = (frame.f_back in tracked_frames)

            if is_target_entry or is_child_of_tracked:
                tracked_frames.add(frame)
                locals_seen_keys[id(frame)] = set(frame.f_locals.keys())
                function_list = get_function_list()
                # Only update function_list for functions we care about
                funcs = function_list.get("functions", {})
                if callee_name in funcs:
                    # Record params with inspect signature binding
                    try:
                        sig = inspect.signature(frame.f_globals.get(callee_name, None) or target_fn)
                    except Exception:
                        sig = None

                    try:
                        # Build call args mapping from frame locals using inspect.getargvalues
                        args_info = inspect.getargvalues(frame)
                        argmap = {}

                        for p in args_info.args:
                            if p in args_info.locals:
                                argmap[p] = args_info.locals[p]
                        if args_info.varargs and args_info.varargs in args_info.locals:
                            argmap[args_info.varargs] = args_info.locals[args_info.varargs]
                        if args_info.keywords and args_info.keywords in args_info.locals:
                            argmap[args_info.keywords] = args_info.locals[args_info.keywords]

                        # Update counters + samples
                        for p, v in argmap.items():
                            _inc_param_type(callee_name, p, v) 
                            _add_type_sample(v)

                    except Exception:
                        # If anything fails, still keep tracing
                        pass

            return tracer

        if frame in tracked_frames:
            if event == "line":
                # Best-effort: detect newly created locals
                cur_keys = set(frame.f_locals.keys())
                prev_keys = locals_seen_keys.get(id(frame), set())
                new_keys = cur_keys - prev_keys
                locals_seen_keys[id(frame)] = cur_keys

                for k in new_keys:
                    try:
                        _add_type_sample(frame.f_locals[k])
                    except Exception:
                        pass

            elif event == "return":
                # Sample return value + final locals snapshot
                try:
                    _add_type_sample(arg)
                except Exception:
                    pass

                try:
                    for _, v in frame.f_locals.items():
                        _add_type_sample(v)
                except Exception:
                    pass

                tracked_frames.discard(frame)

        return tracer


    exception = None

    old_trace = sys.gettrace()
    sys.settrace(tracer)
    try:
        target_fn(*params)
    except RunTimeout as e:
        sys.settrace(old_trace)
        exception = e
    except Exception as e:
        sys.settrace(old_trace)
        exception = e
    finally:
        sys.settrace(old_trace)

    status = RunStatus.SUCCESS
    if exception is not None:
        if isinstance(exception, RunUnableToResolve):
            status = RunStatus.ERROR
        elif isinstance(exception, RunTimeout):
            status = RunStatus.TIMEOUT
        else:
            status = RunStatus.ERROR
    else:
        # TODO: merge (not replace) with global type list
        # set_type_list(...)
        set_type_list(merge_type_dicts_unique(type_list, get_type_list()))
        print("Updated type list with samples.")
        dump_type_list_to_json(get_type_list())
        dump_function_list(get_function_list())
        

    return RunResult(f=target_fn, params=params, status=status), type_list



