import os
import sys
from datetime import *
import random, math

# Mixing tabs and spaces for indentation
def badFunction( param1,param2 ):
    x=1+2   # No spaces around operators
        y = "this is a very long string that will cause linting issues because it exceeds the recommended line length for PEP 8 style guidelines"
        return x+y  # This will also cause a type error

# Unused variable
def unusedStuff():
    unused_var = "I'm never used"
    return 42

# Too many arguments and inconsistent naming
def ProcessData(arg1, arg2, arg3, arg4, arg5, arg6, ThisIsNotSnakeCase):
    print (arg1)
    return None

# Bare except clause
def error_prone():
    try:
        risky_operation = 1/0
    except:
        pass

# Mutable default argument
def append_to_list(item, my_list=[]):
    my_list.append(item)
    return my_list

# Variable used before assignment
def undefined_var():
    print(undefined)
    undefined = "Now defined"

class badClass:
    def __init__(self):
      self.attr = 1
    
    def inconsistent_spacing(self,param):
       return self.attr+param

# Global variable with naming issues
GLOBAL_var = 100

if __name__ == "__main__":
    # Unused import and long line
    result = badFunction(1,"test") + unusedStuff() + ProcessData(1,2,3,4,5,6,7) + GLOBAL_var