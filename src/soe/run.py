

def run(f_name, params=[]):
    '''
    Run function with given parameters and get type samples

    :param f_name: function name from function list
    :param params: parameters to run with

    :return: run result
    '''
    pass


'''
def function1(a, b):
    pass
    
def print_formatted(input):
    pass

def test_function():
    a = 3
    b = "hello"

    function1(a, b)"


def abcdef(input):
    string = str(input)
    print_formatted(string)    

    
run("test_function")
expected updates to global state:
function list --> function_list["function1"]["params"]["a"][int]++
                  function_list["function1"]["params"]["b"][str]++
type list     --> add new type samples
                  type_list[int].append(3)
                  type_list[str].append("hello")

run("abcdef", [123])
expected updates to global state:
function list --> function_list["print_formatted"]["params"]["input"][str]++
type list     --> add new type samples
                  type_list[str].append("123")


'''