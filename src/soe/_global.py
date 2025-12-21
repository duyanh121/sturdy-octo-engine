import threading
import logging

logger = logging.getLogger('_global')

type_list, function_list = {}, {}
_f_lock = threading.Lock()
_t_lock = threading.Lock()


def init_global() -> None:
    logger.debug("Initializing global state")
    set_function_list({})
    set_type_list({})

# function_list
def get_function_list() -> dict:
    with _f_lock:
        logger.debug("Getting function list")
        return function_list
    
def get_function(f_name: str) -> dict:
    with _f_lock:
        logger.debug(f"Getting function {f_name}")
        return function_list.get(f_name, {})

def set_function_list(f_list: dict) -> None:
    with _f_lock:
        logger.debug(f"Setting function list {f_list}")
        function_list = f_list

def set_function(f_name: str, f_info: dict) -> None:
    with _f_lock:
        logger.debug(f"Setting function {f_name} with {f_info}")
        function_list[f_name] = f_info


# type_list
def get_type_list() -> dict:
    with _t_lock:
        logger.debug("Getting type list")
        return type_list
    
def get_type(t_name: str) -> dict:
    with _t_lock:
        logger.debug(f"Getting type {t_name}")
        return type_list.get(t_name, {})
    
def set_type_list(t_list: dict) -> None:
    with _t_lock:
        logger.debug(f"Setting type list {t_list}")
        type_list = t_list

def set_type(t_name: str, t_info: dict) -> None:
    with _t_lock:
        logger.debug(f"Setting type {t_name} with {t_info}")
        type_list[t_name] = t_info


if __name__ == "__main__":
    init_global()
