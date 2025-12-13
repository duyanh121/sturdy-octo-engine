from math import log
import threading
import logging

function_list = {}
# {int: [1, 2, 3]}
# type: [sample1, sample2]
type_list = {}

_f_lock = threading.Lock()
_t_lock = threading.Lock()

logger = logging.getLogger('_global')

def init() -> None:
    logging.debug("Initializing global state")
    global function_list
    global type_list
    function_list = {}
    type_list = {}


# function_list
def get_function_list() -> dict:
    with _f_lock:
        logging.debug("Getting function list")
        return function_list
    
def get_function(f_name: str) -> dict:
    with _f_lock:
        logging.debug(f"Getting function ${f_name}")
        return function_list.get(f_name, {})

def set_function_list(f_list: dict) -> None:
    global function_list
    with _f_lock:
        logging.debug(f"Setting function list ${f_list}")
        function_list = f_list

def set_function(f_name: str, f_info: dict) -> None:
    global function_list
    with _f_lock:
        logging.debug(f"Setting function ${f_name} with ${f_info}")
        function_list[f_name] = f_info


# type_list
def get_type_list() -> dict:
    with _t_lock:
        logging.debug("Getting type list")
        return type_list
    
def get_type(t_name: str) -> dict:
    with _t_lock:
        logging.debug(f"Getting type ${t_name}")
        return type_list.get(t_name, {})
    
def set_type_list(t_list: dict) -> None:
    global type_list
    with _t_lock:
        logging.debug(f"Setting type list ${t_list}")
        type_list = t_list

def set_type(t_name: str, t_info: dict) -> None:
    global type_list
    with _t_lock:
        logging.debug(f"Setting type ${t_name} with ${t_info}")
        type_list[t_name] = t_info


if __name__ == "__main__":
    init()
