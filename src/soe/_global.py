import threading

function_list = {}
type_list = {}

_f_lock = threading.Lock()
_t_lock = threading.Lock()

def init() -> None:
    global function_list
    global type_list
    function_list = {}
    type_list = {}


# function_list

def get_function_list() -> dict:
    with _f_lock:
        return function_list
    
def get_function(f_name: str) -> dict:
    with _f_lock:
        return function_list.get(f_name, {})

def set_function_list(f_list: dict) -> None:
    global function_list
    with _f_lock:
        function_list = f_list

def set_function(f_name: str, f_info: dict) -> None:
    global function_list
    with _f_lock:
        function_list[f_name] = f_info


# type_list
def get_type_list() -> dict:
    with _t_lock:
        return type_list
    
def get_type(t_name: str) -> dict:
    with _t_lock:
        return type_list.get(t_name, {})
    
def set_type_list(t_list: dict) -> None:
    global type_list
    with _t_lock:
        type_list = t_list

def set_type(t_name: str, t_info: dict) -> None:
    global type_list
    with _t_lock:
        type_list[t_name] = t_info