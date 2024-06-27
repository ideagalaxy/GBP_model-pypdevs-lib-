from pypdevs.DEVS import *
from pypdevs.infinity import INFINITY

class State:
    def __init__(self, current="ready"):
        self.set(current)

    def set(self, value):
        self.__state=value
        return self.__state

    def get(self):
        return self.__state
    
    def __str__(self):
        return self.get()
    
class Logger:
    def __init__(self, current=[]):
        self.set(current)

    def set(self, value):
        self.__state=value
        return self.__state
    
    def getall(self):
        return self.__state

    def get(self):
        return self.__state[0]
    
    def __str__(self):
        return self.get()
    
