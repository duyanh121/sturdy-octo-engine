import sys
import os
import inspect
import hashlib
import importlib.util
import builtins
import json
from soe._global import get_function_list, get_type_list, set_function_list, set_type_list
from collections import defaultdict


function_list = get_function_list()
type_list = get_type_list()


# A helper index to prevent duplicates:
#   _type_seen[type_key] = set of fingerprints (strings)
_type_seen = {}  # {"int": {"1","2"}, "numpy.ndarray": {"...hash..."}, ...}


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


def type_key(val) -> str:
    """
    Returns a stable string key for the runtime type of `val` without hard-coding.
    Examples:
      3                -> "int"
      "hi"             -> "str"
      [1,2]            -> "list"
      np.array([1,2])  -> "numpy.ndarray"
      pd.DataFrame(...) -> "pandas.core.frame.DataFrame"
      None             -> "NoneType"
    """
    cls = val.__class__
    mod = getattr(cls, "__module__", "") or ""
    qual = getattr(cls, "__qualname__", getattr(cls, "__name__", "unknown"))

    return qual if mod == "builtins" else f"{mod}.{qual}"


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


def _inc_param_type(func_name: str, param_name: str, val):
    k = type_key(val)
    params = function_list[func_name].setdefault("params", {})
    param_types = params.setdefault(param_name, {})
    param_types[k] = param_types.get(k, 0) + 1




def resolve_by_dotted_name(dotted: str):
    # dotted like "numpy.ma.extras.intersect1d"
    mod_path, func_name = dotted.rsplit(".", 1)

    try:
        mod = importlib.import_module(mod_path)
    except ModuleNotFoundError:
        try:
            mod = importlib.import_module(f"numpy.{mod_path}")
        except ModuleNotFoundError:
            raise

    fn = getattr(mod, func_name)
    if not callable(fn):
        raise TypeError(f"{dotted} is not callable")
    return fn


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


def dump_type_list_to_json(type_list, path="type_list.json"):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            {k: [json_safe(v) for v in vals] for k, vals in type_list.items()},
            f,
            indent=2
        )


def run(f_name, params=[]):
    '''
    Run function with given parameters and get type samples

    :param f_name: function name from function list
    :param params: parameters to run with

    :return: run result
    '''


    if params is None:
        params = []

    target_fn = resolve_by_dotted_name(f_name)

    # Track frames descended from this run call
    tracked_frames = set()
    locals_seen_keys = {}  # id(frame) -> set(keys)

    def tracer(frame, event, arg):
        if event == "call":
            code = frame.f_code
            callee_name = code.co_name

            # Start tracking once we enter target function; then include children
            is_target_entry = (callee_name == target_fn.__name__ and frame.f_code is target_fn.__code__)
            is_child_of_tracked = (frame.f_back in tracked_frames)

            if is_target_entry or is_child_of_tracked:
                tracked_frames.add(frame)
                locals_seen_keys[id(frame)] = set(frame.f_locals.keys())

                # Only update function_list for functions we care about
                if callee_name in function_list:
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

    old_trace = sys.gettrace()
    sys.settrace(tracer)
    try:
        return target_fn(*params)
    finally:
        sys.settrace(old_trace)

if __name__ == "__main__":
    for f_name in function_list:
        params = function_list[f_name].get("params", {}).keys()
        try:
            run(f_name, params)
        except Exception as e:
            print(f"Error running {f_name}: {e}")
        dump_type_list_to_json(type_list)