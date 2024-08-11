#
#
#       Basically, all materials are significantly affected only by the pop or block state
#       You must return the 'State' object(or self.state) in every step
#       Output
#        
#       
#


from pypdevs.DEVS import *
from pypdevs.infinity import INFINITY
import random
from pypdevs.simulator import Simulator

from MUs import *


    
class Source(AtomicDEVS):               #Source will create 'Part' object

    def __init__(self, name = 'source', amount = -1, interval = 1, part_lwh = [1,1,1]):
        AtomicDEVS.__init__(self, name)
        self.name = name
        self.state = State_str("pop")
        outport_name = name + '_outport'
        self.outport = self.addOutPort(outport_name)
        self.count = 0

        #setting
        self.amount = amount            #Set how many to create
        self.interval = interval        #Generate term
        self.part_lwh = part_lwh        #Information of the Part object to be created (length, width, height)

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
                self.state = State_str("pop")           #Resetting the new "pop" state will reset the TimeAdvance 
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
            __out = Out()
            __out.set("state","pop")

            self.count += 1
            name = "part_" + str(self.count)
            part = Part(name, self.part_lwh[0], self.part_lwh[1], self.part_lwh[2])
            __out.set("part",part)
            
            return {self.outport: __out}
        
class Buffer(AtomicDEVS): 
    def __init__(self, name = 'buffer', capacity = INFINITY, buffer_type = "Queue"):
        AtomicDEVS.__init__(self, name)
        self.name = name
        self.state = State_str("empty")

        outport_name = name + '_outport'
        inport_name = name + '_inport'
        response_inport_name = name + '_response_inport'

        self.outport = self.addOutPort(outport_name)
        self.inport = self.addInPort(inport_name)
        self.response_inport = self.addInPort(response_inport_name)
        
    

        self.do_pop = True
        self.is_full = False
        self.init_msg = "msg : "
        self.current_time = 0.0

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
        self.current_time += self.elapsed

        incoming = inputs.get(self.inport, None)
        response = inputs.get(self.response_inport, None)
        
        # inport
        if incoming:   
            if incoming.get('state') == 'pop':
                #1. save into inventory
                self.inventory.append({
                    "incoming" : incoming, 
                    "get_time" : self.current_time
                })

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
            
        if response:
            if response.get("state") == "pop":
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

        __out = Out()

        if state == "pop":
            if self.is_full == False:
                __out = self.__pop.get("incoming")
                __out.set("state",state)
                
                elased_time = self.current_time - self.__pop.get("get_time")
                __out.set(self.name,elased_time)
                
                return {self.outport: __out}
            else:
                __out.set("state","block")
                return {self.outport: __out}

class Conveyor(AtomicDEVS): 
    #
    #       center move
    #

    def __init__(self, name = 'conveyor', length = 8, speed = 1.0):
        AtomicDEVS.__init__(self, name)
        self.name = name
        self.state = State_str("empty")
        self.current_time = 0.0

        outport_name = name + '_outport'
        inport_name = name + '_inport'
        response_inport_name = name + '_response_inport'

        self.inport = self.addInPort(inport_name)
        self.outport = self.addOutPort(outport_name)
        self.response_inport = self.addInPort(response_inport_name)
        
        self.do_pop = True
        self.is_full = False
        self.conveyor = []
        self.remain_time = 0


        #setting
        self.op_length = length
        self.length = length
        self.speed = speed

    def timeAdvance(self):
        state = self.state.get()

        if state == "block":
            return INFINITY
        elif state == "ready":
            self.current_time += self.remain_time
            return self.remain_time
        elif state == "empty":
            self.current_time += self.remain_time
            return self.remain_time
        elif state == "pop":
            return 0.0
        else:
            raise DEVSException(\
                "unknown state <%s> in <%s> time advance transition function"\
                % (state, self.name))
        
    def intTransition(self):
        state = self.state.get()

        if state == "empty":
            for ent in self.conveyor:
                if ent.get("is_arrive") == False:
                    end_ent = ent
                    break
            end_ent["is_arrive"] = True 
            end_ent["arr_time"] = None

            if self.do_pop == True:
                self.state = State_str("pop")
                return self.state
            else:
                self.state = State_str("ready")
                
                self.remain_time = INFINITY
                for ent in self.conveyor:
                    if ent.get("arr_time") != None:
                        self.remain_time = ent.get("arr_time")
                        break
                
                return self.state

        elif state == "ready":
            end = self.conveyor[0]
            end["is_arrive"] = True

            if self.do_pop == True:
                self.state = State_str("pop")
                return self.state
            else:
                self.state = State_str("ready")
                self.remain_time = INFINITY
                return self.state          

        if state == "pop":
            self.__pop = self.conveyor[0]

            if self.conveyor.is_empty():
                self.remain_time = INFINITY
                self.state = State_str("empty")
                return self.state
            
            else:
                next = self.conveyor[0]
                remain_distance = self.op_length - next.get("distance")
                self.remain_time = (remain_distance) / self.speed
                for item in self.conveyor:
                    item["distance"] += remain_distance 
                self.state = State_str("empty")
                return self.state
        else:
            raise DEVSException(\
                "unknown state <%s> in <%s> internal transition function"\
                % (state, self.name))

    def extTransition(self, inputs):
        state = self.state.get()
        if len(self.conveyor) != 0:
            if self.conveyor[-1].get("is_arrive") == False:
                self.current_time -= self.remain_time
        self.current_time += self.elapsed

        port_in = inputs.get(self.inport, None)
        response_in = inputs.get(self.response_inport, None)
        
        # inport
        if port_in:
            if port_in.get("state") == "pop":
                
                part_length = port_in.get("part").get("length")
                

                
                if len(self.conveyor) != 0:
                    forward_ent = self.conveyor[-1]
                    if forward_ent.get("is_arrive") == False:
                        length = self.speed * self.elapsed  - forward_ent("part_len")
                        next_time = forward_ent.get("arr_time") + length / self.speed
                        
                    else:
                        length = self.length
                        next_time = length / self.speed
                else:
                    self.length = self.op_length
                    length = self.op_length
                    next_time = length / self.speed

                self.conveyor.append({
                    "incoming"  : port_in,
                    "get_time"  : self.current_time,
                    "arr_time"  : next_time,
                    "part_len"  : part_length,
                    "distance"  : length,          #distance of forward entity
                    "is_arrive" : False
                })

                self.length - part_length
                if self.length <= 0:
                    self.is_full = True

                front_ent = self.conveyor[0]
                self.remain_time = self.current_time - front_ent.get("arr_time")

                return self.state              
            
        if response_in:
            if response_in.get("state") == "pop":
                
                #Save this response
                self.do_pop = True
                self.is_full = False

                #If Buffer Can't pop entry
                if state == "empty":
                    self.state = State_str("empty")
                    return self.state
                
                #Buffer can pop entry
                else:
                    #Set state "pop"
                    self.state = State_str("pop")
                    #Release do_pop
                    self.do_pop = False
                    return self.state
                
        self.remain_time -= self.elapsed
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
        
class Station(AtomicDEVS):
    def __init__(self, name = 'station', working_time = 10):
        AtomicDEVS.__init__(self, name)
        self.name = name
        self.state = State_str("ready")
        self.current_time = 0.0

        outport_name = name + '_outport'
        inport_name = name + '_inport'
        response_inport_name = name + '_response_inport'

        self.outport = self.addOutPort(outport_name)
        self.inport = self.addInPort(inport_name)
        self.response_inport = self.addInPort(response_inport_name)

        self.next_is_blocked = False
        self.is_first_pulse = True
        self.is_in = False

        #setting
        self.working_time = working_time
        self.remain_time = 0


    def timeAdvance(self):
        state = self.state.get()
        #print(self.name, self.current_time,"TA",state)

        if state == "ready":
            return INFINITY
        elif state == "block":
            return INFINITY
        elif state == "busy":
            self.current_time += self.remain_time
            return self.remain_time
        else:
            raise DEVSException(\
                "unknown state <%s> in <%s> time advance transition function"\
                % (state, self.name))
    
    def intTransition(self):
        state = self.state.get()
        
        
        #print(self.name,self.current_time,"int")

        if state == "busy":
            if self.is_first_pulse == True:
                self.is_first_pulse = False
                self.is_in = True
                self.remain_time = self.working_time
                self.state = State_str("busy")
                return self.state
            else:
                if self.next_is_blocked == True:
                    self.state = State_str("block")
                else:
                    self.is_in = False
                    self.state = State_str("ready")
                return self.state
        else:
            raise DEVSException(\
                "unknown state <%s> in <%s> internal transition function"\
                % (state, self.name))
        
    def extTransition(self, inputs):
        state = self.state.get()
        if self.is_in == True and self.next_is_blocked == False:
            self.current_time -= self.remain_time
        self.current_time += self.elapsed
        #print(self.name, self.current_time, "ext")
        
        incoming = inputs.get(self.inport, None)
        response = inputs.get(self.response_inport, None)

        if incoming:
            if incoming.get("state") == "pop":
                if state == "ready":
                    
                    self.__product = {
                        "incoming" : incoming, 
                        "get_time" : self.current_time
                    }

                    self.state = State_str("busy")
                    self.is_first_pulse = True
                    self.remain_time = 0.0
                    return self.state
                
        if response:
            if response.get("state") == "pop":
                self.next_is_blocked = False

                if state == "block":
                    self.state = State_str("busy")
                    self.remain_time = 0
                    return self.state
                
                elif state == "busy":
                    self.remain_time = self.remain_time - self.elapsed
                    self.state = State_str("busy")
                    return self.state
                
            elif response.get("state") == "block":
                self.next_is_blocked = True

                if state == "busy":
                    self.remain_time = self.remain_time - self.elapsed
                    self.state = State_str("busy")
                    return self.state
                
        self.remain_time = self.remain_time - self.elapsed
        return self.state    
        

    def outputFnc(self):
        state = self.state.get()

        __out = Out()
        if state == "busy":
            if self.is_first_pulse == True:
                __out.set("state","block")
                __out.set("msg","first block")
                return {self.outport: __out}
            
            else:
                if self.next_is_blocked == True:
                    __out.set("state","block")
                    __out.set("msg","next is block")
                    return {self.outport: __out}
                
                else:
                    #print(self.name, self.current_time, "out")
                    #print(self.name, " out")
                    __out = self.__product.get("incoming")
                    __out.set("state","pop")
                    
                    elapsed_time = self.current_time - self.__product.get("get_time")
                    __out.set(self.name,elapsed_time)

                    return {self.outport: __out}


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

        if port_in.get("state") == "pop":
            self.count += 1
            self.result.append(port_in)
            self.state = State_arr(["get", self.count])
            return self.state
        else:
            self.state = State_arr(["get", self.count])
            return self.state
        


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
sim.setTerminationTime(50)
sim.setClassicDEVS()

sim.simulate()