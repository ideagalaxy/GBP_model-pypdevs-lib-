from pypdevs.DEVS import *
from pypdevs.infinity import INFINITY
import random
from pypdevs.simulator import Simulator

source_inventory = {
    'Source' : INFINITY
}

data = {
    #proc    working time  
    'station_1':     [3],
    'station_2':     [3],
    'station_3':     [3]

}

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
    
class Source(AtomicDEVS):
    '''
        state : load / pop / end
    '''
    def __init__(self, name = 'source'):
        AtomicDEVS.__init__(self, name)
        self.name = name
        self.state = State("pop")
        outport_name = name + '_outport'
        self.outport = self.addOutPort(outport_name)
        self.count = 0

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
            self.state = State("load")
            return self.state
        
        else:
            raise DEVSException(\
                "unknown state <%s> in <%s> internal transition function"\
                % (state, self.name))
    
    def outputFnc(self):
        state = self.state.get()

        if state == "pop":
            self.count = self.count + 1
            return {self.outport: ["pop",self.count]}
        else:
            return {self.outport: [state]}
        
class Buffer(AtomicDEVS):
    def __init__(self, name = 'buffer'):
        AtomicDEVS.__init__(self, name)
        self.name = name
        self.inventory = 0
        self.pop = []
        self.state = State("empty")
        outport_name = name + '_outport'
        self.outport = self.addOutPort(outport_name)
        inport_name = name + '_inport'
        self.inport = self.addInPort(inport_name)
        response_inport_name = name + '_response_inport'
        self.response_inport = self.addInPort(response_inport_name)

        self.inventory = []

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
            if len(self.inventory) == 0:
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

            if port_in[0] == "pop":
                if self.do_pop == True:
                    self.inventory.append(port_in[1])
                    pop = self.inventory.pop(0)
                    self.pop = ['pop',pop]
                    self.state = State("pop")
                    self.do_pop = False
                    return self.state
                else:
                    self.inventory.append(port_in[1])
                    self.state = State("ready")
                    return self.state
            else:
                return self.state
            
        if response_port_in != None:
            
            if response_port_in[0] == "pop":
                self.do_pop = True
                if state == "empty":
                    return self.state
                else:
                    pop = self.inventory.pop(0)
                    self.pop = ['pop',pop]
                    self.state = State("pop")
                    self.do_pop = False
                    return self.state
            else:
                return self.state
            
    def outputFnc(self):
        state = self.state.get()

        if state == "pop":
            return {self.outport: self.pop}
        
class Station(AtomicDEVS):
    def __init__(self, name = 'station'):
        AtomicDEVS.__init__(self, name)
        self.name = name
        self.state = State("free")
        outport_name = name + '_outport'
        self.outport = self.addOutPort(outport_name)
        inport_name = name + '_inport'
        self.inport = self.addInPort(inport_name)

        #init section
        if name in data:
            init = data[name]
            self.working_time = init[0]

    def timeAdvance(self):
        state = self.state.get()

        if state == "free":
            return INFINITY
        elif state == "busy":
            return self.working_time
        else:
            raise DEVSException(\
                "unknown state <%s> in <%s> time advance transition function"\
                % (state, self.name))
    
    def intTransition(self):
        state = self.state.get()

        if state == "busy":
            self.state = State("free")
            return self.state
        else:
            raise DEVSException(\
                "unknown state <%s> in <%s> internal transition function"\
                % (state, self.name))
        
    def extTransition(self, inputs):
        state = self.state.get()

        if state == "free":
            self.state = State("busy")
            return self.state
           
        else:
            raise DEVSException(\
                "unknown state <%s> in <%s> external transition function"\
                % (state, self.name))

    def outputFnc(self):
        state = self.state.get()

        if state == "busy":
            return {self.outport: "free"}

class Drain(AtomicDEVS):
    def __init__(self, name = 'drain'):
        AtomicDEVS.__init__(self, name)
        self.name = name
        self.state = State("ready")
        outport_name = name + '_outport'
        self.outport = self.addOutPort(outport_name)
        inport_name = name + '_inport'
        self.inport = self.addInPort(inport_name)
        self.pop = []

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

        if port_in[0] == "pop":
            self.pop = port_in
            self.state = State("get")
            return self.state
        else:
            return self.state
        
    def intTransition(self):
        state = self.state.get()

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
            print text
            return {self.outport: self.pop}
        
class BS_coupled(CoupledDEVS):
    def __init__(self, name="BS"):
        CoupledDEVS.__init__(self, name)
        self.name = name

        num = self.name[-1]
        station_name = "station_" + num
        buffer_name = "buffer_" + num
        self.buffer = self.addSubModel(Buffer(name=buffer_name))  
        self.station = self.addSubModel(Station(name=station_name))  

        inport_name = self.name + "_inport"
        outport_name = self.name + "_outport"
        response_inport_name = self.name + "_response_inport"
        self.inport = self.addInPort(inport_name)
        self.outport = self.addOutPort(outport_name)
        self.response_inport = self.addInPort(response_inport_name)

        self.connectPorts(self.inport, self.buffer.inport)
        self.connectPorts(self.response_inport, self.buffer.response_inport)
        self.connectPorts(self.buffer.outport, self.station.inport)
        self.connectPorts(self.station.outport, self.outport)
    
    def select(self, imm):
        if self.station in imm:
            return self.station
        elif self.buffer in imm:
            return self.buffer
        

        
class LinearLine(CoupledDEVS):
    def __init__(self, name="LinearLine"):
        CoupledDEVS.__init__(self, name)
        self.storage = self.addSubModel(Source(name="Source"))        #outport, response_inport

        self.station_1 = self.addSubModel(BS_coupled(name="BS_1"))    #outport, inport, response_inport
        self.station_2 = self.addSubModel(BS_coupled(name="BS_2"))
        self.station_3 = self.addSubModel(BS_coupled(name="BS_3"))

        self.result = self.addSubModel(Drain(name="result"))            #inport,outport
        
        #connect outports >> inports
        self.connectPorts(self.storage.outport, self.station_1.inport)
        self.connectPorts(self.station_1.outport, self.station_2.inport)
        self.connectPorts(self.station_2.outport, self.station_3.inport)
        self.connectPorts(self.station_3.outport, self.result.inport)

        #connect outports >> response_inport
        self.connectPorts(self.result.outport, self.station_3.response_inport)
        self.connectPorts(self.station_3.outport, self.station_2.response_inport)
        self.connectPorts(self.station_2.outport, self.station_1.response_inport)

    def select(self, imm):
        if self.result in imm:
            return self.result
        elif self.station_3 in imm:
            return self.station_3
        elif self.station_2 in imm:
            return self.station_2
        elif self.station_1 in imm:
            return self.station_1
        elif self.storage in imm:
            return self.storage

sim = Simulator(LinearLine("LinearLine"))

sim.setVerbose()
sim.setTerminationTime(60)
sim.setClassicDEVS()

sim.simulate()