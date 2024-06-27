from state import State
from pypdevs.DEVS import *
from pypdevs.infinity import INFINITY

source_inventory = {
    'main_source' : INFINITY
}
    
class Source(AtomicDEVS):
    '''
        state : load / pop / end
    '''
    def __init__(self, name = 'source'):
        AtomicDEVS.__init__(self, name)
        self.count = 0
        self.name = name
        self.state = State("pop")
        outport_name = name + '_outport'
        self.outport = self.addOutPort(outport_name)

        #init section
        if name in source_inventory:
            self.inventory = source_inventory[name]

    def timeAdvance(self):
        state = self.state.get()
        if state == "load":
            return 1.0
        elif state == "pop":
            return 0.0
        elif state == "end":
            return INFINITY
        else:
            raise DEVSException(\
                "unknown state <%s> in <%s> time advance transition function"\
                % (state, self.name))
        
    def intTransition(self):
        state = self.state.get()

        if state == "load":
            if self.inventory == INFINITY:
                self.state = State("pop")
                return self.state
            
            else:
                if self.inventory > 0:
                    self.inventory = self.inventory - 1
                    self.state = State("pop")
                    return self.state
                else:
                    self.state = State("end")
                    return self.state
                
        elif state == "pop":
            self.count += 1
            self.state = State("load")
            return self.state
        
        else:
            raise DEVSException(\
                "unknown state <%s> in <%s> internal transition function"\
                % (state, self.name))
    
    def outputFnc(self):
        state = self.state.get()

        if state == "pop":
            return {self.outport: "pop"}
        else:
            return {self.outport: " "}