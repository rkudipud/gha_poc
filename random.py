import os
import sys
import random
import time

import datetime  # unused import
import math      # unused import

# no docstring for this function
def calculate_something(x,y,z,  unused_param):  # too many spaces, unused parameter
    
    
    
    # too many blank lines above
    result=x+y*z # missing spaces around operators
    
    extra_var = "This variable is never used"  # unused variable
    
    if result > 10:    # trailing whitespace    
        print("Result is greater than 10")
    else:
      print("Result is less than or equal to 10")  # inconsistent indentation
    
    return result


# function that references undefined variable
def process_data():
    data = [1, 2, 3, 4, 5]
    for i in range(len(data)):
        value = data[i] + undefined_variable  # undefined variable
    return data

# extremely long line that exceeds typical line length limits
very_long_variable_name_that_could_be_shortened = "This is an extremely long string that would definitely exceed the 79 or 88 character limit that most Python style guides recommend for maximum line length"

# inconsistent naming convention (should be snake_case)
def calculateBMI(height, weight):
    return weight / (height ** 2)

# class with no docstring and bad spacing
class UserData:
def __init__(self, name, age):  # incorrect indentation
        self.name=name  # missing spaces around operator
        self.age=age
        
        
if __name__ == "__main__":
    result = calculate_something(5, 10, 3, "unused")
    print(f"The result is {result}")