from pypdevs.DEVS import *
from pypdevs.infinity import INFINITY
import random
from pypdevs.simulator import Simulator

data = {
    #proc    working time  
    'station_1':     [2],
    'station_2':     [3],
    'station_3':     [1]

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
    
class BState:
    def __init__(self, current=["ready", "inventory: 0"]):
        self.set(current)

    def set(self, value):
        insert = "inventory: " + str(value[1])
        self.__state= [value[0],insert]
        return self.__state

    def get(self):
        return self.__state
    
    def __str__(self):
        data = self.get()
        text = data[0] + ", " + data[1]
        return text
    
class GState:
    def __init__(self, current=["ready", "Total: 0"]):
        self.set(current)

    def set(self, value):
        insert = "Total: " + str(value[1])
        self.__state= [value[0],insert]
        return self.__state

    def get(self):
        return self.__state
    
    def __str__(self):
        data = self.get()
        text = data[0] + ", " + data[1]
        return text
    
    
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

    def timeAdvance(self):
        state = self.state.get()
        if state == "pop":
            return 1.0
        else:
            raise DEVSException(\
                "unknown state <%s> in <%s> time advance transition function"\
                % (state, self.name))
        
    def intTransition(self):
        state = self.state.get()

        if state == "pop":
            self.state = State("pop")
            return self.state
        
        else:
            raise DEVSException(\
                "unknown state <%s> in <%s> internal transition function"\
                % (state, self.name))
    
    def outputFnc(self):
        state = self.state.get()
        if state == "pop":
            return {self.outport: "pop"}
        
class Buffer(AtomicDEVS):
    def __init__(self, name = 'buffer'):
        AtomicDEVS.__init__(self, name)
        self.name = name
        outport_name = name + '_outport'
        self.outport = self.addOutPort(outport_name)
        inport_name = name + '_inport'
        self.inport = self.addInPort(inport_name)
        response_inport_name = name + '_response_inport'
        self.response_inport = self.addInPort(response_inport_name)

        self.inventory = []
        self.do_pop = True
        self.state = BState(["empty",len(self.inventory)])

    def timeAdvance(self):
        state = self.state.get()

        if state[0] == "empty":
            return INFINITY
        elif state[0] == "ready":
            return INFINITY
        elif state[0] == "pop":
            return 0.0
        else:
            raise DEVSException(\
                "unknown state <%s> in <%s> time advance transition function"\
                % (state, self.name))
        
    def intTransition(self):
        state = self.state.get()

        if state[0] == "pop":
            if len(self.inventory) == 0:
                self.state = BState(["empty",len(self.inventory)])
                return self.state
            else:
                self.state = BState(["ready",len(self.inventory)])
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
                #1. save into inventory
                self.inventory.append(port_in)
                
                #2-1 if do_pop is True
                if self.do_pop == True:
                    #pop inventory's first entry
                    self.inventory.pop(0)

                    #Set state "pop"
                    self.state = BState(["pop",len(self.inventory)])
                    self.do_pop = False
                    return self.state
                
                #2-2 if do_pop is False
                else:
                    #Set state "ready"
                    self.state = BState(["ready",len(self.inventory)])
                    return self.state
            
        if response_port_in != None:
            
            if response_port_in == "pop":
                #Save this response
                self.do_pop = True

                #If Buffer Can't pop entry
                if state[0] == "empty":
                    self.state = BState(["empty",len(self.inventory)])
                    return self.state
                
                #Buffer can pop entry
                else:
                    self.inventory.pop(0)
                    #Set state "pop"
                    self.state = BState(["pop",len(self.inventory)])
                    #Release do_pop
                    self.do_pop = False
                    return self.state
            
        raise DEVSException(\
                "unknown state <%s> in <%s> internal transition function"\
                % (state, self.name))
            
    def outputFnc(self):
        state = self.state.get()

        if state[0] == "pop":
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

        #init section
        if name in data:
            init = data[name]
            self.working_time = init[0]

    def timeAdvance(self):
        state = self.state.get()

        if state == "ready":
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
            self.state = State("ready")
            return self.state
        else:
            raise DEVSException(\
                "unknown state <%s> in <%s> internal transition function"\
                % (state, self.name))
        
    def extTransition(self, inputs):
        state = self.state.get()

        if state == "ready":
            self.state = State("busy")
            return self.state
           
        else:
            raise DEVSException(\
                "unknown state <%s> in <%s> external transition function"\
                % (state, self.name))

    def outputFnc(self):
        state = self.state.get()

        if state == "busy":
            return {self.outport: "pop" }

class Drain(AtomicDEVS):
    def __init__(self, name = 'drain'):
        AtomicDEVS.__init__(self, name)
        self.name = name
        self.state = GState(["get", 0])
        inport_name = name + '_inport'
        self.inport = self.addInPort(inport_name)
        self.count = 0

    def timeAdvance(self):
        state = self.state.get()

        if state[0] == "get":
            return INFINITY
        else:
            raise DEVSException(\
                "unknown state <%s> in <%s> time advance transition function"\
                % (state, self.name))
        
    def extTransition(self, inputs):
        state = self.state.get()

        if state[0] == "get":
            self.count += 1
            self.state = GState(["get", self.count])
            return self.state
        else:
            raise DEVSException(\
                "unknown state <%s> in <%s> external transition function"\
                % (state, self.name))
        
class BS_model(CoupledDEVS):
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
        self.connectPorts(self.station.outport, self.buffer.response_inport)
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

        self.station_1 = self.addSubModel(BS_model(name="BS_1"))    #outport, inport, response_inport
        self.station_2 = self.addSubModel(BS_model(name="BS_2"))
        self.station_3 = self.addSubModel(BS_model(name="BS_3"))

        self.result = self.addSubModel(Drain(name="result"))            #inport,outport
        
        #connect outports >> inports
        self.connectPorts(self.storage.outport, self.station_1.inport)
        self.connectPorts(self.station_1.outport, self.station_2.inport)
        self.connectPorts(self.station_2.outport, self.station_3.inport)
        self.connectPorts(self.station_3.outport, self.result.inport)

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
sim.setTerminationTime(21600)
sim.setClassicDEVS()

sim.simulate()