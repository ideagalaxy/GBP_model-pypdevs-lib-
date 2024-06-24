from pypdevs.DEVS import *
from pypdevs.infinity import INFINITY
import random

source_inventory = {
    'main_source' : 100,
    'sub1_source' : 100,
    'sub2_source' : 100,
    'sub3_source' : 100 
}

data = {
    #proc    setup  cycle   inven   safety  faliure mttr
    'a101': [600.0, 1200.0, 100.0,  10.0,   0.0,    600],
    'a201': [300.0, 900.0,  0.0,    0.0,    0.05,   600],
    'a202': [300.0, 600.0,  0.0,    0.0,    0.05,   600],
    'a301': [180.0, 1200.0, 100.0,  10.0,   0.10,   900],
    'a302': [180.0, 900.0,  0.0,    0.0,    0.10,   900],
    'a303': [300.0, 1500.0, 0.0,    0.0,    0.05,   300],
    'a203': [300.0, 1800.0, 0.0,    0.0,    0.05,   300],
    'a204': [300.0, 1500.0, 0.0,    0.0,    0.05,   900],
    'a401': [600.0, 1800.0, 0.0,    10.0,   0.05,   600],
    'a403': [600.0, 1800.0, 0.0,    0.0,    0.15,   600]
}

class Station_state:
    def __init__(self, current="ready"):
        self.set(current)

    def set(self, value):
        self.__state=value

    def get(self):
        return self.__state
    def __str__(self):
        return self.get()

class Source_state:
    def __init__(self, current="load"):
        self.set(current)

    def set(self, value):
        self.__state=value

    def get(self):
        return self.__state
    def __str__(self):
        return self.get()
    
class Buffer_state:
    def __init__(self, current="empty"):
        self.set(current)

    def set(self, value):
        self.__state=value

    def get(self):
        return self.__state[0]
    def __str__(self):
        return self.get()
    


class Source(AtomicDEVS):
    '''소스 제공'''
    def __init__(self, name = 'source'):
        AtomicDEVS.__init__(self, name)
        self.name = name
        self.state = Station_state("load")
        outport_name = name + '_outport'
        self.outport = self.addOutPort(outport_name)

        #init section
        if name in data:
            self.inventory = data[name]

    def timeAdvance(self):
        state = self.state.get()

        if state == 'load':
            return 5
        elif state == 'pop':
            return 0
        else:
            raise DEVSException(\
                "unknown state <%s> in <%s> time advance transition function"\
                % state , self.name)
        
    def intTransition(self):
        state = self.state.get()

        if state == "load":
            if self.inventory > 0:
                self.inventory = self.inventory - 1
                return self.state.set("pop")
            else:
                return self.state.set("load")
        elif state == "pop":
            return self.state.set("load")
        else:
            raise DEVSException(\
                "unknown state <%s> in <%s> internal transition function"\
                % state , self.name)
    
    def outputFnc(self):
        state = self.state.get()

        if state == "pop":
            return {self.outport: "pop"}
        
class Buffer(AtomicDEVS):
    '''일반공정'''
    def __init__(self, name = 'buffer'):
        AtomicDEVS.__init__(self, name)
        self.name = name
        self.inventory = 0
        self.state = Buffer_state("empty")
        outport_name = name + '_outport'
        self.outport = self.addOutPort(outport_name)
        inport_name = name + '_inport'
        self.inport = self.addInPort(inport_name)
    
    def timeAdvance(self):
        state = self.state.get()

        if state == 'empty':
            return INFINITY
        elif state == 'possible':
            return INFINITY
        elif state == 'pop':
            return INFINITY
        else:
            raise DEVSException(\
                "unknown state <%s> in <%s> time advance transition function"\
                % state , self.name)

    def extTransition(self, inputs):
        port_in =inputs[self.inport]
        state = self.state.get()

        if port_in == "pop":
            self.inventory = self.inventory + 1
            return self.state.set("possible")
        
        elif port_in == "ready"
                
            
        else:
            return self.state.set(state)
        

class Station(AtomicDEVS):
    '''일반공정'''
    def __init__(self, name = 'station'):
        AtomicDEVS.__init__(self, name)
        self.name = name
        self.state = Station_state("ready")
        outport_name = name + '_outport'
        self.outport = self.addOutPort(outport_name)
        inport_name = name + '_inport'
        self.inport = self.addInPort(inport_name)

        #init section
        if name in data:
            init = data[name]
            self.setup_time = init[0]
            self.cycle_time = init[1]
            self.inventory = init[2]
            self.safety = init[3]
            self.failure = init[4]
            self.mttr = init[5]

    def timeAdvance(self):
        state = self.state.get()

        if state == 'ready':
            return INFINITY
        elif state == 'setup':
            return self.setup_time
        elif state == 'cycle':
            return self.cycle_time
        elif state == 'fix':
            return self.mttr
        else:
            raise DEVSException(\
                "unknown state <%s> in <%s> time advance transition function"\
                % state , self.name)
    
    def intTransition(self):
        state = self.state.get()

        if state == "setup":
            failure_num = random.random()
            if self.failure > failure_num:
                return self.state.set("fix")
            else:
                return self.state.set("cycle")
        elif state == "fix":
            return self.state.set("cycle")
        else:
            raise DEVSException(\
                "unknown state <%s> in <%s> internal transition function"\
                % state , self.name)
        
    def extTransition(self, inputs):
        port_in =inputs[self.inport]
        state = self.state.get()

        if port_in == "ready" or port_in == "pop":

            if state == 'ready':
                return self.state.set("setup")
            else:
                return self.state.set(state)
        else:
            return self.state.set(state)
        
    def outputFnc(self):
        state = self.state.get()

        if state == "ready":
            return {self.outport: "ready"}
        elif state == "setup":
            return {self.outport: "setup"}
        elif state == "cycle":
            return {self.outport: "cycle"}
        elif state == "fix":
            return {self.outport: "fix"}
        elif state == "wait":
            return {self.outport: "wait"}