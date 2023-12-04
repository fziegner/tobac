# bad_code.py
import os, sys

# Example of bad practices for Pylint
class myClass:
    def __init__(self,value=2):
        self.value=value
    
    def BADMethodNaming(self, aValue):
        try:
            self.value/=aValue
        except Exception, e:
            print "Error detected:",e
            exit(1)
        return self.value

     def anothermethod(self): # Indentation inconsistency
    pass

def global_func():
    global some_global
    some_global = 1
    some_global+=1

# Unused variable and wildcard import
from math import *

# Unused argument
def unused_arg_function(unused_arg):
    return "Nothing"

# Redefinition of a built-in
list = ['a', 'b', 'c']

class AnotherClass(object):
  def not_used_method(self):
      pass

# usage of myClass that will increase the Pylint issues count
instance = myClass()
instance.BADMethodNaming(42)
print(instance.BADMethodNaming('1'))
