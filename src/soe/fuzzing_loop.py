from pathlib import Path
from typing import Any
import logging

from dotenv import get_key
from ._helpers import merge_list_dicts_stable
from .fuzzer import fuzz
from soe.function_list import function_list
import soe._global as _global
import soe.run as run

logger = logging.getLogger('fuzzing_loop')

def fuzzing_loop(repo_path: Path):
    """
    Main loop for fuzzing a repository.
    :param repoPath: Path to the repository to be fuzzed.
    """
    if not repo_path.exists():
        logger.critical(f"Repository path does not exist: {repo_path}")
        raise FileNotFoundError(f"Repository path {repo_path} does not exist.")
    if not repo_path.is_dir():
        logger.critical(f"Provided path is not a directory: {repo_path}")
        raise NotADirectoryError(f"Provided path {repo_path} must be a directory.")

    # Generate function list
    logger.info(f"Generating function list from {repo_path}...")
    _global.set_function_list(function_list.generate_function_list(str(repo_path)))


    # Generate default parameter types
    logger.info("Generating default parameter types...")
    default_parameter_types = {}
    for f_name in _global.get_function_list():
        default_parameter_types[f_name] = [Any for _ in _global.get_function_list()[f_name]["params"]]


    # Generate parameter types from type hints
    logger.info("Generating parameter types from type hints...")
    type_hint_parameter_types = {}
    # ...


    # Generate parameter types from static analysis
    logger.info("Generating parameter types from static analysis...")
    static_analysis_parameter_types = {}
    # ...

    function_parameter_types = merge_list_dicts_stable(default_parameter_types, type_hint_parameter_types, static_analysis_parameter_types)
    # function_parameter_types["abc"] = [[any, any]]

    while True:
        func_list = _global.get_function_list()
        for f_name in func_list:
            params = func_list[f_name].get("params", {}).keys()
            try:
                result = fuzz(f_name, params)
            except Exception as e:
                print(f"Error running {f_name}: {e}")
            else:
                if result is not None:
                    _global.set_type_list(result)
                    
        break
    


if __name__ == "__main__":
    repo_path = Path("downloads/numpy")
    fuzzing_loop(repo_path)
    
