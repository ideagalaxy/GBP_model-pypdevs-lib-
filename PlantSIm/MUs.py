from pypdevs.DEVS import *
from pypdevs.infinity import INFINITY
import random
from pypdevs.simulator import Simulator

class State_str:
    def __init__(self, current="State_str"):
        self.set(current)

    def set(self, value):
        self.__state=value
        return self.__state

    def get(self):
        return self.__state
    
    def __str__(self):
        return self.get()
    
class State_arr:
    def __init__(self, current=["State_arr"]):
        self.set(current)

    def set(self, value_list):
        self.__state = value_list
        return self.__state

    def get(self):
        return self.__state
    
    def __str__(self):
        data = self.get()
        for i in range(len(data)):
            if i == 0:
                text = data[0]
            else:
                text = text + ", " + str(data[i])
        return text
    
class Part:
    def __init__(self, name = "part", length = 1, width = 1, height = 1):
        self.set_name(name)
        self.set_length(length)
        self.set_width(width)
        self.set_height(height)
        self.set_elapsed(0)
        self.__log = []

    def set_name(self, name):
        self.__name = name
        return self.__name
    
    def set_length(self, length):
        self.__length = length
        return self.__length
    
    def set_width(self, width):
        self.__width = width
        return self.__width
    
    def set_height(self, height):
        self.__height = height
        return self.__height
    
    def set_elapsed(self,elapsed):
        self.__elpased = elapsed

    def get_elapsed(self):
        return self.__dict["elapsed"]

    def set_log(self,log):
        self.__log.append(log)
    
    def get(self):
        self.__dict = {
             "name" : self.__name,
             "length" : self.__length,
             "width" : self.__width,
             "height" : self.__height,
             "elapsed" : self.__elpased,
             "log" : self.__log
            }
        return self.__dict

    def __str__(self):
        return self.__name
    
class Queue:
    def __init__(self):
        self.__queue = []

    def append(self,value):
        self.__queue.append(value)
        return self.__queue
    
    def pop(self):
        self.__pop = self.__queue.pop(0)
        return self.__pop
    
    def get(self):
        return self.__queue
    
    def len(self):
        return len(self.__queue)
    
    def is_empty(self):
        if len(self.__queue) == 0:
            return True
        
        else:
            return False

class Stack:
    def __init__(self):
        self.__stack = []

    def append(self,value):
        self.__stack.append(value)
        return self.__stack
    
    def pop(self):
        self.__pop = self.__stack.pop()
        return self.__pop
    
    def get(self):
        return self.__stack
    
    def len(self):
        return len(self.__stack)
    
    def is_empty(self):
        if len(self.__stack) == 0:
            return True
        else:
            return False

    