from state import State, Logger
from pypdevs.DEVS import *
from pypdevs.infinity import INFINITY

class Buffer(AtomicDEVS):
    def __init__(self, name = 'buffer'):
        AtomicDEVS.__init__(self, name)
        self.name = name
        self.inventory = 0
        self.state = State("empty")
        outport_name = name + '_outport'
        self.outport = self.addOutPort(outport_name)
        inport_name = name + '_inport'
        self.inport = self.addInPort(inport_name)
        response_inport_name = name + '_response_inport'
        self.response_inport = self.addInPort(response_inport_name)

        self.do_pop = True

    def timeAdvance(self):
        state = self.state.get()

        if state == "empty":
            return INFINITY
        elif state == "ready":
            return INFINITY
        elif state == "pop":
            return 0.0
        else:
            raise DEVSException(\
                "unknown state <%s> in <%s> time advance transition function"\
                % (state, self.name))
        
    def intTransition(self):
        state = self.state.get()

        if state == "pop":
            if self.inventory == 0:
                self.state = State("empty")
                return self.state
            else:
                self.state = State("ready")
                return self.state
        else:
            raise DEVSException(\
                "unknown state <%s> in <%s> internal transition function"\
                % (state, self.name))

    def extTransition(self, inputs):
        state = self.state.get()
        try:    
            port_in =inputs[self.inport]
        except:
            port_in = None
        try:
            response_port_in =inputs[self.response_inport]
        except:
            response_port_in = None
        
        # inport
        if port_in != None:
            if port_in == "pop":
                self.inventory = self.inventory + 1
                if self.do_pop == False:
                    self.state = State("ready")
                    return self.state
                else:
                    self.do_pop = False
                    self.inventory = self.inventory - 1
                    self.state = State("pop")
                    return self.state
            else:
                return self.state
            
        if response_port_in != None:
            if response_port_in == "pop":
                self.do_pop = True
                if state == "empty":
                    return self.state
                else:
                    self.do_pop = False
                    self.inventory = self.inventory - 1
                    self.state = State("pop")
                    return self.state
            else:
                return self.state
            
    def outputFnc(self):
        state = self.state.get()

        if state == "pop":
            return {self.outport: "pop"}