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
                text = text + ", " + data[i]
        return text
    
class Part:
    def __init__(self, name = "part", length = 1, width = 1, height = 1):
        self.name = name
        self.lwd = [length,width,height]        #This is Information about LDW(length,width,height)
        self.state = State_arr([self.name])

    def getstate(self):
        state = self.state.get()
        return state
    
    def setstate(self, value):
        setstate = self.state
        sef

    def getname(self):
        return self.name
    
    def getlwd(self):
        return self.lwd

    def __str__(self):
        return self.lwd
    

    