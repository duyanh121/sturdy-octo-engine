from pathlib import Path
import logging
import soe._global as _global
import soe.run as run
from soe.run import run

logger = logging.getLogger('fuzzer')

def fuzz(fuzz_dir: Path) -> None:
    while True:
        func_list = _global.get_function_list()
        for f_name in func_list:
            params = func_list[f_name].get("params", {}).keys()
            try:
                result = run(f_name, params)
            except Exception as e:
                print(f"Error running {f_name}: {e}")
            else:
                if result is not None:
                    _global.set_type_list(result)
                    
        break
    return 

