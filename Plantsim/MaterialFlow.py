from pypdevs.DEVS import *
from pypdevs.infinity import INFINITY
import random
from pypdevs.simulator import Simulator

from MUs import State_arr, State_str, Part, Queue
    
class Source(AtomicDEVS):
    '''
        state : load / pop / end
    '''
    def __init__(self, name = 'source', amount = -1, interval = 1, part_lwh = [1,1,1]):
        AtomicDEVS.__init__(self, name)
        self.name = name
        self.state = State_str("pop")
        outport_name = name + '_outport'
        self.outport = self.addOutPort(outport_name)
        self.count = 0

        #setting
        self.amount = amount
        self.interval = interval
        self.part_lwh = part_lwh

    def timeAdvance(self):
        state = self.state.get()
        if state == "pop":
            return self.interval
        elif state == "empty":
            return INFINITY
        else:
            raise DEVSException(\
                "unknown state <%s> in <%s> time advance transition function"\
                % (state, self.name))
        
    def intTransition(self):
        state = self.state.get()

        if state == "pop":
            if self.amount == -1:
                self.state = State_str("pop")
            else:
                self.count += 1 
                if self.count >= self.amount:
                    self.state = State_str("empty")
                else:
                    self.state = State_str("pop")
            return self.state
        
        else:
            raise DEVSException(\
                "unknown state <%s> in <%s> internal transition function"\
                % (state, self.name))
    
    def outputFnc(self):
        state = self.state.get()
        
        if state == "pop":
            self.count += 1
            name = "part_" + str(self.count)
            return {self.outport: [state,Part(name, self.part_lwh[0], self.part_lwh[1], self.part_lwh[2])]}
        
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

        self.inventory = Queue()
        self.do_pop = True
        self.state = State_str("empty")

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
            if self.inventory.is_empty():
                self.state = State_str("empty")
                return self.state
            else:
                self.state = State_str("ready")
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
                #1. save into inventory
                self.inventory.append(port_in[1])

                
                #2-1 if do_pop is True
                if self.do_pop == True:
                    #pop inventory's first entry
                    self.__pop = self.inventory.pop()

                    #Set state "pop"
                    self.state = State_str("pop")
                    self.do_pop = False
                    return self.state
                
                #2-2 if do_pop is False
                else:
                    #Set state "ready"
                    self.state = State_str("ready")
                    return self.state
            
        if response_port_in != None:
            if response_port_in[0] == "pop":
                
                #Save this response
                self.do_pop = True

                #If Buffer Can't pop entry
                if state == "empty":
                    self.state = State_str("empty")
                    return self.state
                
                #Buffer can pop entry
                else:
                    self.__pop = self.inventory.pop()
                    #Set state "pop"
                    self.state = State_str("pop")
                    #Release do_pop
                    self.do_pop = False
                    return self.state
            
        raise DEVSException(\
                "unknown state <%s> in <%s> internal transition function"\
                % (state, self.name))
            
    def outputFnc(self):
        state = self.state.get()

        if state == "pop":
            return {self.outport: [state,self.__pop]}
        
class Processor(AtomicDEVS):
    def __init__(self, name = 'processor', working_time = 10):
        AtomicDEVS.__init__(self, name)
        self.name = name
        self.state = State_str("ready")
        outport_name = name + '_outport'
        self.outport = self.addOutPort(outport_name)
        inport_name = name + '_inport'
        self.inport = self.addInPort(inport_name)

        #setting
        self.working_time = working_time

    def timeAdvance(self):
        state = self.state.get()

        if state == "ready":
            return INFINITY
        elif state == "block":
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
            self.state = State_str("ready")
            return self.state
        else:
            raise DEVSException(\
                "unknown state <%s> in <%s> internal transition function"\
                % (state, self.name))
        
    def extTransition(self, inputs):
        state = self.state.get()
        port_in =inputs[self.inport]

        if state == "ready":
            self.__product = port_in[1]
            self.state = State_str("busy")
            return self.state
           
        else:
            raise DEVSException(\
                "unknown state <%s> in <%s> external transition function"\
                % (state, self.name))

    def outputFnc(self):
        state = self.state.get()

        if state == "busy":
            return {self.outport: ["pop",self.__product] }

class Drain(AtomicDEVS):
    def __init__(self, name = 'drain'):
        AtomicDEVS.__init__(self, name)
        self.name = name
        self.state = State_arr(["get", 0])
        inport_name = name + '_inport'
        self.inport = self.addInPort(inport_name)
        self.count = 0
        self.result = []

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

        port_in =inputs[self.inport]

        if state[0] == "get":
            self.count += 1
            self.result.append(port_in[1])
            self.state = State_arr(["get", self.count])
            return self.state
        else:
            raise DEVSException(\
                "unknown state <%s> in <%s> external transition function"\
                % (state, self.name))
        
class Station(CoupledDEVS):
    def __init__(self, name="station",processor_working_time = 10):
        CoupledDEVS.__init__(self, name)
        self.name = name

        num = self.name[-1]
        processor_name = "processor_" + num
        buffer_name = "buffer_" + num
        self.buffer = self.addSubModel(Buffer(name=buffer_name))  

        self.working_time = processor_working_time
        self.station = self.addSubModel(Processor(name=processor_name,working_time=self.working_time))  

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

        self.station_1 = self.addSubModel(Station(name="BS_1"))    #outport, inport, response_inport
        self.station_2 = self.addSubModel(Station(name="BS_2"))
        self.station_3 = self.addSubModel(Station(name="BS_3"))

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
sim.setTerminationTime(120)
sim.setClassicDEVS()

sim.simulate()