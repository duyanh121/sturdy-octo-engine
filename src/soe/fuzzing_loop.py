import sys
from pathlib import Path
from typing import Any
import logging
import json
from .helpers import merge_list_dicts_stable
from .fuzzer import fuzz

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] [%(name)s/%(levelname)s]: %(message)s',
    # Send output to a file and the console (sys.stderr is default for console)
    handlers=[
        logging.FileHandler("runtime.log"), 
        logging.StreamHandler(sys.stdout)
    ]
)

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

    # Generate function tree function tree
    logger.info(f"Generating function tree from {repo_path}...")
    function_list = {}
    with open("src\\soe\\function_tree\\function_tree.json", 'r') as file:
        function_list = json.load(file)["functions"]

    # Generate default parameter types
    logger.info("Generating default parameter types...")
    default_parameter_types = {}
    for func in function_list:
        default_parameter_types[func] = [Any for _ in function_list[func]["params"]]


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
        for func in function_list:
            fuzz(function_list[func], function_parameter_types[func])
            # function_parameter_types = merge_list_dicts_stable(function_parameter_types, parameter)

        break
    


if __name__ == "__main__":
    repo_path = Path("repos/numpy")
    fuzzing_loop(repo_path)
