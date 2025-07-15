import random
import os
from datetime import datetime
import time as t

# A Python script with various consistency issues


# snake_case function
def calculate_average(numbers):
    return sum(numbers) / len(numbers)

# camelCase function
def findMaxValue(numberList):
    return max(numberList)

# PascalCase function
def PrintResults(value):
    print(f"The result is: {value}")

# inconsistent spacing
x=10
y = 20
z=x+y

# inconsistent string quotes
name = 'John'
greeting = "Hello"
message = '''Welcome
to my program'''

# inconsistent variable naming
UserAge = 30
user_name = "Alice"
userSCORE = 95

class dataProcessor:
    def __init__(self, data):
        self.Data = data
    
    # inconsistent indentation
    def process(self):
      return [x * 2 for x in self.Data]
    
    def filter_data(self, threshold):
            return [x for x in self.Data if x > threshold]

# inconsistent list creation
list1 = [1, 2, 3, 4, 5]
list2=[6,7,8,9,10]

# inconsistent error handling
try:
    result = 10 / 0
except ZeroDivisionError:
    print("Cannot divide by zero")
except:
    print("An error occurred")

if __name__ == "__main__":
    numbers = [random.randint(1, 100) for _ in range(10)]
    avg = calculate_average(numbers)
    maxVal=findMaxValue(numbers)
    PrintResults(avg)
    PrintResults(maxVal)
    
    # inconsistent if formatting
    if avg > 50:
        print("Above average")
    if maxVal>75:
      print("High maximum")