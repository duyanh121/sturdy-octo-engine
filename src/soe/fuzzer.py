from pathlib import Path
import logging
import sys
import soe._global as _global
from soe.run import f_run
from soe._types import RunStatus, RunUnableToResolve

logger = logging.getLogger('fuzzer')

def simple_fuzzer(fuzz_dir: Path) -> None:
    func_list = _global.get_function_list()
    
    # Handle if function_list has a "functions" wrapper key
    if "functions" in func_list and isinstance(func_list["functions"], dict):
        func_list = func_list["functions"]
    
    for f_name in func_list:
        logger.debug(f"Fuzzing function {f_name}")

        if "SampleClass" in f_name:
            # add class method implementation later
            continue 

        if len(func_list[f_name]["params"]) >= 1:
            params = [1]
        else:
            params = []
        
        try:
            result = f_run(f_name, params)
            logger.info(repr(result[0]))
        except RunUnableToResolve as e:
            raise e

        if result[0].status != RunStatus.SUCCESS:
            _global.add_error(result[0])

    logger.info("Fuzzing completed. Errors:")
    for i in _global.get_error_list():
        logger.info(repr(i))


def blackbox_fuzzer(fuzz_dir: Path) -> None:
    pass
