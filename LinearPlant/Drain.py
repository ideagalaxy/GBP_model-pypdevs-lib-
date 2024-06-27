from state import State , Logger
from pypdevs.DEVS import *
from pypdevs.infinity import INFINITY

class Drain(AtomicDEVS):
    def __init__(self, name = 'drain'):
        AtomicDEVS.__init__(self, name)
        self.name = name
        self.state = State("ready")
        outport_name = name + '_outport'
        self.outport = self.addOutPort(outport_name)
        inport_name = name + '_inport'
        self.inport = self.addInPort(inport_name)

        self.count = 0

    def timeAdvance(self):
        state = self.state.get()

        if state == "ready":
            return INFINITY
        elif state == "get":
            return 0.0
        else:
            raise DEVSException(\
                "unknown state <%s> in <%s> time advance transition function"\
                % (state, self.name))
        
    def extTransition(self, inputs):
        port_in =inputs[self.inport]
        state = self.state.get()

        if port_in == "pop":
            self.count = self.count + 1
            self.state = State("get")
            return self.state
        else:
            return self.state
        
    def intTransition(self):
        state = self.state.get()
        print "int Transition",self.name, state

        if state == "get":
            self.state = State("ready")
            return self.state
        else:
            raise DEVSException(\
                "unknown state <%s> in <%s> internal transition function"\
                % (state, self.name))
    
    def outputFnc(self):
        state = self.state.get()

        if state == "get":
            text = "Total : %s" % (self.count)
            return {self.outport: text}