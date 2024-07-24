from pypdevs.DEVS import *
from pypdevs.infinity import INFINITY
import random
from pypdevs.simulator import Simulator

from MUs import *
    
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
    def __init__(self, name = 'buffer', capacity = INFINITY, buffer_type = "Queue"):
        AtomicDEVS.__init__(self, name)
        self.name = name
        outport_name = name + '_outport'
        self.outport = self.addOutPort(outport_name)
        inport_name = name + '_inport'
        self.inport = self.addInPort(inport_name)
        response_inport_name = name + '_response_inport'
        self.response_inport = self.addInPort(response_inport_name)
        
        self.do_pop = True
        self.state = State_str("empty")
        self.is_full = False
        self.init_msg = "msg : "

        if buffer_type == "Queue":
            self.inventory = Queue()

        #setting
        if capacity == INFINITY:
            self.capacity = -1
        else:
            self.capacity = capacity

    def timeAdvance(self):
        state = self.state.get()

        if state == "empty":
            return INFINITY
        elif state == "ready":
            return INFINITY
        elif state == "block":
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
                if self.is_full == False:
                    self.state = State_str("ready")
                else:
                    self.state = State_str("block")
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
                    #Set state "ready" or "block"
                    if self.capacity <= self.inventory.len():
                        if self.capacity != -1:
                            self.is_full = True
                            self.state = State_str("pop")
                            return self.state
                        else:
                            self.state = State_str("ready")
                            return self.state
                    else:
                        self.state = State_str("ready")
                        return self.state
            
        if response_port_in != None:
            if response_port_in[0] == "pop":
                
                #Save this response
                self.do_pop = True
                self.is_full = False

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
            
        return self.state
            
    def outputFnc(self):
        state = self.state.get()
        msg = self.init_msg + "inventory length : " + str(self.inventory.len())
        if state == "pop":
            if self.is_full == False:
                return {self.outport: ["pop",self.__pop, msg]}
            else:
                msg = msg + ", State : block, inventory was full"
                return {self.outport: ["block", msg]}

        
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
        
class Station(AtomicDEVS):
    def __init__(self, name = 'station', working_time = 10):
        AtomicDEVS.__init__(self, name)
        self.name = name
        self.state = State_str("ready")

        outport_name = name + '_outport'
        self.outport = self.addOutPort(outport_name)

        inport_name = name + '_inport'
        self.inport = self.addInPort(inport_name)

        response_inport_name = name + '_response_inport'
        self.response_inport = self.addInPort(response_inport_name)
        self.next_was_blocked = False

        #setting
        self.working_time = working_time
        self.remain_time = working_time

    def timeAdvance(self):
        state = self.state.get()

        if state == "ready":
            return INFINITY
        elif state == "block":
            return INFINITY
        elif state == "busy":
            return self.remain_time
        else:
            raise DEVSException(\
                "unknown state <%s> in <%s> time advance transition function"\
                % (state, self.name))
    
    def intTransition(self):
        state = self.state.get()

        if state == "busy":
            if self.is_first_pulse == True:
                self.is_first_pulse = False
                self.remain_time = self.working_time
                self.state = State_str("busy")
                return self.state
            else:
                if self.next_was_blocked == True:
                    self.state = State_str("block")
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

        if port_in != None:
            if port_in[0] == "pop":
                if state == "ready":
                    self.__product = port_in[1]
                    self.state = State_str("busy")
                    self.is_first_pulse = True
                    self.remain_time = 0
                    return self.state
                
        if response_port_in != None:
            if response_port_in[0] == "pop":
                self.next_was_blocked = False

                if state == "block":
                    self.state = State_str("busy")
                    self.remain_time = 0
                    return self.state
                
                elif state == "busy":
                    self.remain_time = self.remain_time - self.elapsed
                    self.state = State_str("busy")
                    return self.state
                
            elif response_port_in[0] == "block":
                self.next_was_blocked = True

                if state == "busy":
                    self.remain_time = self.remain_time - self.elapsed
                    self.state = State_str("busy")
                    return self.state
        self.remain_time = self.remain_time - self.elapsed
        return self.state    
        

    def outputFnc(self):
        
        state = self.state.get()

        if state == "busy":
            if self.is_first_pulse == True:
                return {self.outport: ["block","fisrt_pulse"] }
            else:
                if self.next_was_blocked == True:
                    return {self.outport: ["block","next is block"] }
                else:
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
        
class BStation(CoupledDEVS):
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

# class Conveyor

inputData = {
    "name"  :["source","source_buffer","station_1", "buffer_1","station_2","station_3","result"],
    "type"  :["Source", "Buffer", "Station", "Buffer", "Station", "Station", "Drain"],
    "time"  :[2,None,6,4,10,15,None]
}

class LinearLine(CoupledDEVS):
    def __init__(self, name="LinearLine", inputData= {}):
        CoupledDEVS.__init__(self, name)
        self.variable_name = []
        self.variable_type = []
        for i in range(len(inputData["name"])):
            name = inputData["name"][i]
            type = inputData["type"][i]
            time = inputData["time"][i]
            if type == "Source":
                setattr(self,name,self.addSubModel(Source(name=name, interval=time)))
            
            elif type == "Buffer":
                if time == None:
                    setattr(self,name,self.addSubModel(Buffer(name=name)))
                else:
                    setattr(self,name,self.addSubModel(Buffer(name=name, capacity= time)))

            elif type == "Station":
                setattr(self,name,self.addSubModel(Station(name=name,working_time=time)))

            else:
                setattr(self,name,self.addSubModel(Drain(name=name)))
            self.variable_name.append(name)
            self.variable_type.append(type)

        print(self.variable_name)
        print(self.variable_type)

        for i in range(len(self.variable_name)-1):
            val_now = getattr(self, self.variable_name[i])
            val_next = getattr(self, self.variable_name[i+1])
            val_outport = val_now.outport
            val_inport = val_next.inport
            self.connectPorts(val_outport,val_inport)

            now_type = self.variable_type[i]
            next_type = self.variable_type[i+1]
        
            if now_type == "Station" or now_type == "Buffer":
                if next_type == "Station" or next_type == "Buffer":
                    val_response_outport = val_next.outport
                    val_response_inport = val_now.response_inport
                    self.connectPorts(val_response_outport, val_response_inport)
            

    def select(self, imm):
        for var_name in reversed(self.variable_name):
            var_value = getattr(self, var_name)
            if var_value in imm:
                return var_value
        





sim = Simulator(LinearLine("LinearLine",inputData=inputData))

sim.setVerbose()
sim.setTerminationTime(120)
sim.setClassicDEVS()

sim.simulate()