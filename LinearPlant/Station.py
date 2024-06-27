from state import State, Logger
from pypdevs.DEVS import *
from pypdevs.infinity import INFINITY

class Station(AtomicDEVS):
    def __init__(self, name = 'station'):
        AtomicDEVS.__init__(self, name)
        self.name = name
        self.state = State("ready")
        outport_name = name + '_outport'
        self.outport = self.addOutPort(outport_name)
        inport_name = name + '_inport'
        self.inport = self.addInPort(inport_name)
        response_inport_name = name + '_response_inport'
        self.response_inport = self.addInPort(response_inport_name)

        self.do_pop = True
        self.working_time = 11
        #init section
        if name in data:
            init = data[name]
            self.working_time = init[0]


    def timeAdvance(self):
        state = self.state.get()

        if state == "ready":
            return INFINITY
        elif state == "working":
            return self.working_time
        elif state == "pop":
            return 0.0
        elif state == "waiting":
            return INFINITY
        else:
            raise DEVSException(\
                "unknown state <%s> in <%s> time advance transition function"\
                % (state, self.name))
    
    def intTransition(self):
        state = self.state.get()

        if state == "working":
            if self.do_pop == False:
                self.state = State("waiting")
                return self.state
            else:
                self.do_pop = False
                self.state = State("pop")
                return self.state
            
        elif state == "pop":
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

        if port_in != None:
            print "extTransition port_in",self.name, port_in

            if port_in == "pop":
                if state == "ready":
                    self.state = State("working")
                    return self.state
                else:
                    return self.state
            else:
                return self.state
            
        if response_port_in != None:
            print "extTransition response_port_in",self.name, response_port_in

            if response_port_in == "pop" or response_port_in[0] == "T":
                self.do_pop = True
                if state == "waiting":
                    self.do_pop = False
                    self.state = State("pop")
                    return self.state
                elif state == "ready":
                    return self.state
                elif state == "working":
                    return self.state
            else:
                return self.state

        
    def outputFnc(self):
        state = self.state.get()
        print "outputFnc", self.name, state

        if state == "working":
            return {self.outport: "waiting"}
        elif state == "pop":
            return {self.outport: "pop"}