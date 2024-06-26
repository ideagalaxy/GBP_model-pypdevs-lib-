from pypdevs.DEVS import *
from pypdevs.infinity import INFINITY
import random

source_inventory = {
    'main_source' : INFINITY
}

data = {
    #proc    working time  
    'station1':     [60],
    'station2':     [30],
    'station3':     [30],
    'station4':     [18],
    'station5':     [18],
}

class State:
    def __init__(self, current="ready"):
        self.set(current)

    def set(self, value):
        self.__state=value

    def get(self):
        return self.__state
    
    def __str__(self):
        return self.get()
    
class Source(AtomicDEVS):
    def __init__(self, name = 'source'):
        AtomicDEVS.__init__(self, name)
        self.name = name
        self.state = State("load")
        outport_name = name + '_outport'
        self.outport = self.addOutPort(outport_name)

        #init section
        if name in source_inventory:
            self.inventory = source_inventory[name]

    def timeAdvance(self):
        print "timeAdvance",self.name
        state = self.state.get()
        print self.name, state

        if state == "load":
            return 5.0
        elif state == "pop":
            return 0.0
        elif state == "end":
            return INFINITY
        else:
            raise DEVSException(\
                "unknown state <%s> in <%s> time advance transition function"\
                % (state, self.name))
        
    def intTransition(self):
        print "intTransition",self.name
        state = self.state.get()
        print self.name, state

        if state == "load":
            if self.inventory == INFINITY:
                print "Inventory = Inf"
                return self.state.set("pop")
            else:
                if self.inventory > 0:
                    self.inventory = self.inventory - 1
                    return self.state.set("pop")
                else:
                    return self.state.set("end")
                
        elif state == "pop":
            return self.state.set("load")
        
        elif state == "end":
            return self.state
        
        else:
            raise DEVSException(\
                "unknown state <%s> in <%s> internal transition function"\
                % (state, self.name))
    
    def outputFnc(self):
        print "output",self.name
        state = self.state.get()
        print self.name, state

        if state == "pop":
            return {self.outport: "pop"}
        else:
            return {self.outport: state}
        
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

        self.do_pop = False

    def timeAdvance(self):
        print "time advance",self.name
        state = self.state.get()
        print self.name, state

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
        print "int Transition",self.name
        state = self.state.get()
        print self.name, state

        if state == "pop":
            if self.inventory == 0:
                return self.state.set("empty")
            else:
                return self.state.set("ready")
        else:
            raise DEVSException(\
                "unknown state <%s> in <%s> internal transition function"\
                % (state, self.name))

    def extTransition(self, inputs):
        port_in =inputs[self.inport]
        print "ext transition", self.name , port_in
        state = self.state.get()
        print self.name, state

        if port_in == "pop":
            self.inventory = self.inventory + 1
            if self.do_pop == False:
                return self.state.set("ready")
            else:
                self.do_pop == False
                return self.state.set("pop")
        
        elif port_in == "ready":
            self.do_pop = True
            if state == "empty":
                return self.state
            else:
                self.do_pop = False
                self.inventory = self.inventory - 1
                return self.state.set("pop")
        else:
            return self.state
            
    def outputFnc(self):
        print "output", self.name
        state = self.state.get()
        print "output", state

        if state == "ready":
            return {self.outport: "ready"}
        elif state == "empty":
            return {self.outport: "empty"}
        elif state == "pop":
            return {self.outport: "pop"}
        
class Station(AtomicDEVS):
    def __init__(self, name = 'station'):
        AtomicDEVS.__init__(self, name)
        self.name = name
        self.state = State("ready")
        outport_name = name + '_outport'
        self.outport = self.addOutPort(outport_name)
        inport_name = name + '_inport'
        self.inport = self.addInPort(inport_name)

        self.do_pop = False
        self.working_time = 11
        #init section
        if name in data:
            init = data[name]
            self.working_time = init[0]


    def timeAdvance(self):
        print "time advance",self.name
        state = self.state.get()
        print "time advance",self.state

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
        print "int Transition",self.name
        state = self.state.get()
        print "int Transition",state

        if state == "working":
            if self.do_pop == False:
                return self.state.set("waiting")
            else:
                self.do_pop = False
                return self.state.set("pop")
            
        elif state == "pop":
            return self.state.set("ready")
        else:
            raise DEVSException(\
                "unknown state <%s> in <%s> internal transition function"\
                % (state, self.name))
        
    def extTransition(self, inputs):
        port_in =inputs[self.inport]
        print "extTransition",self.name, port_in
        state = self.state.get()
        print "extTransition",state

        if port_in == "pop":
            if state == "ready":
                return self.state.set("working")
            
        if port_in == "ready" or port_in == "empty":
            self.do_pop = True
            if state == "waiting":
                self.do_pop = False
                return self.state.set("pop")
            elif state == "ready":
                self.do_pop = False
                return self.state.set("ready")
            elif state == "working":
                return self.state.set(state)
        else:
            return self.state
        
    def outputFnc(self):
        print "output",self.name
        state = self.state.get()
        print "output",state

        if state == "ready":
            return {self.outport: "ready"}
        elif state == "working":
            return {self.outport: "working"}
        elif state == "waiting":
            return {self.outport: "waiting"}
        elif state == "pop":
            return {self.outport: "pop"}

class Drain(AtomicDEVS):
    def __init__(self, name = 'drain'):
        AtomicDEVS.__init__(self, name)
        self.name = name
        self.state = State("ready")
        outport_name = name + '_outport'
        self.outport = self.addOutPort(outport_name)
        inport_name = name + '_inport'
        self.inport = self.addInPort(inport_name)

    def timeAdvance(self):
        state = self.state.get()
        print "time advance",self.name

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
            return self.state.set("get")
        
    def intTransition(self):
        state = self.state.get()

        print "int Transition",self.name

        if state == "get":
            return self.state.set("ready")
        else:
            raise DEVSException(\
                "unknown state <%s> in <%s> internal transition function"\
                % (state, self.name))
    
    def outputFnc(self):
        state = self.state.get()

        if state == "get":
            text = "Total : "
            return {self.outport: self.count}
        else:
            return {self.outport: state}

        
        
class Storage(CoupledDEVS):
    def __init__(self, name="main_storage"):
        CoupledDEVS.__init__(self, name)
        self.main_source = self.addSubModel(Source(name="main_source"))
        self.main_buffer = self.addSubModel(Buffer(name="main_buffer"))

        self.outport = self.addOutPort(name="Storage_outport")
        self.inport = self.addInPort(name="Storage_buffer_inport")

        self.connectPorts(self.main_source.outport, self.main_buffer.inport)

        self.connectPorts(self.main_buffer.outport, self.outport)
        self.connectPorts(self.inport, self.main_buffer.inport)

    def select(self, imm):
        if self.main_source in imm:
            return self.main_source
        
class Stem(CoupledDEVS):
    def __init__(self, name="main_stem"):
        CoupledDEVS.__init__(self, name)
        self.station_1 = self.addSubModel(Station(name="station_1"))
        self.station_2 = self.addSubModel(Station(name="station_2"))
        self.station_3 = self.addSubModel(Station(name="station_3"))
        self.buffer_1 = self.addSubModel(Buffer(name="buffer_1"))
        self.station_4 = self.addSubModel(Station(name="station_4"))
        self.station_5 = self.addSubModel(Station(name="station_5"))

        self.outport = self.addOutPort(name= "main_stem_outport")
        self.inport = self.addInPort(name= "main_stem_inport")

        self.first_outport = self.addOutPort(name= "first_outport")
        self.last_inport = self.addInPort(name= "last_inport")
        

        self.connectPorts(self.inport, self.station_1.inport)

        self.connectPorts(self.station_1.outport, self.station_2.inport)
        self.connectPorts(self.station_1.outport, self.first_outport)

        self.connectPorts(self.station_2.outport, self.station_1.inport)
        self.connectPorts(self.station_2.outport, self.station_3.inport)

        self.connectPorts(self.station_3.outport, self.station_2.inport)
        self.connectPorts(self.station_3.outport, self.buffer_1.inport)

        self.connectPorts(self.buffer_1.outport, self.station_4.inport)

        self.connectPorts(self.station_4.outport, self.buffer_1.inport)
        self.connectPorts(self.station_4.outport, self.station_5.inport)

        self.connectPorts(self.last_inport, self.station_5.inport)
        self.connectPorts(self.station_5.outport, self.station_4.inport)
        
        self.connectPorts(self.station_5.outport, self.outport)
        print "connect all"

    def select(self, imm):
        if self.station_5 in imm:
            return self.station_5
        elif self.station_4 in imm:
            return self.station_4
        elif self.buffer_1 in imm:
            return self.buffer_1
        elif self.buffer_1 in imm:
            return self.buffer_1
        elif self.station_3 in imm:
            return self.station_3
        elif self.station_2 in imm:
            return self.station_2
        elif self.station_1 in imm:
            return self.station_1

class LinearLine(CoupledDEVS):
    def __init__(self, name="LinearLine"):
        CoupledDEVS.__init__(self, name)
        self.main_storage = self.addSubModel(Storage(name="main_storage"))
        self.main_stem = self.addSubModel(Stem(name="main_stem"))
        self.result = self.addSubModel(Drain(name="result"))

        self.connectPorts(self.main_storage.outport, self.main_stem.inport)
        self.connectPorts(self.main_stem.first_outport, self.main_storage.inport)

        self.connectPorts(self.main_stem.outport, self.result.inport)
        self.connectPorts(self.result.outport, self.main_stem.last_inport)

    def select(self, imm):
        if self.main_storage in imm:
            return self.main_storage


from pypdevs.simulator import Simulator 
sim = Simulator(LinearLine("LinearLine"))

sim.setVerbose()
sim.setTerminationTime(600)
sim.setClassicDEVS()

sim.simulate()