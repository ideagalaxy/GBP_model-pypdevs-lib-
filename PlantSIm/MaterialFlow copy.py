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
    #       front move
    #

    def __init__(self, name = 'conveyor', length = 2, speed = 1.0):
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
        self.remain_time = INFINITY

        #setting
        self.op_length = length
        self.length = length
        self.speed = speed

    def timeAdvance(self):
        state = self.state.get()
        print(self.name ,"ta", state, self.current_time)

        if state == "block":
            return self.remain_time
        elif state == "ready":
            if self.remain_time != INFINITY:
                self.current_time += self.remain_time
            return self.remain_time
        elif state == "empty":
            if self.remain_time != INFINITY:
                self.current_time += self.remain_time
            return self.remain_time
        elif state == "pop":
            self.__pop = self.conveyor.pop(0)
            self.length += self.__pop.get("part_len")
            return 0.0
        else:
            raise DEVSException(\
                "unknown state <%s> in <%s> time advance transition function"\
                % (state, self.name))
        
    def intTransition(self):
        state = self.state.get()
        print(self.name ,"int", state)

        if state == "empty":
            if len(self.conveyor) == 0:
                return self.state

            #intT의 empty에 왔다는 뜻 = 첫번째 객체가 끝에 도달했다는 뜻
            for ent in self.conveyor:
                if ent.get("is_arrive") == False:
                    end_ent = ent
                    break
            #도착 정보 표기하기
            end_ent["is_arrive"] = True 
            end_ent["arr_time"] = None

            #바로 pop 해야하는 지 체크
            if self.do_pop == True:
                self.state = State_str("pop")
                return self.state
            
            #아니면 ready로 상태천이
            else:
                self.state = State_str("ready")
                
                #뒤에 따라오는 객체 없으면 INFINITY로 설정
                self.remain_time = INFINITY
                #뒤에 따라오는 객체 있으면 다음 remain_time 설정
                for ent in self.conveyor:
                    if ent.get("arr_time") != None:
                        self.remain_time = ent.get("arr_time")
                        break
                return self.state

        elif state == "ready":
            #intT ready에 왔다는 뜻은 따라오던 객체가 도착 했다는 뜻
            for ent in self.conveyor:
                if ent.get("is_arrive") == False:
                    end_ent = ent
                    break
            #도착 정보 표기하기
            end_ent["is_arrive"] = True 
            end_ent["arr_time"] = None

            #뒤에 따라오는 객체 있는지 확인하기
            for ent in self.conveyor:
                #따라오는 객체 있을 때
                if ent.get("arr_time") != None:
                    self.remain_time = ent.get("arr_time")
                    break
                #따라오는 객체 없을 때
                if ent == self.conveyor[-1]:
                    self.remain_time = INFINITY
                    if self.is_full == True:
                        self.state = State_str("block")

            return self.state          

        if state == "pop":
            if len(self.conveyor) == 0 :
                self.remain_time = INFINITY
                self.state = State_str("empty")
                return self.state
            
            if self.conveyor[0].get("is_arrive") == True:
                self.remain_time = INFINITY
                self.state = State_str("ready")
                return self.state
            else:
                self.state = State_str("empty")
                self.remain_time =  self.conveyor[0].get("arr_time")
                return self.state
            
            
        else:
            raise DEVSException(\
                "unknown state <%s> in <%s> internal transition function"\
                % (state, self.name))

    def extTransition(self, inputs):
        state = self.state.get()
        print(self.name ,"ext", self.current_time,state)

        if len(self.conveyor) != 0:
            if self.conveyor[-1].get("is_arrive") == False:
                self.current_time -= self.remain_time
        self.current_time += self.elapsed

        port_in = inputs.get(self.inport, None)
        response_in = inputs.get(self.response_inport, None)

        
        # inport
        if port_in:
            if port_in.get("state") == "pop":
                
                if len(self.conveyor) != 0 and self.elapsed != 0:
                    for ent in self.conveyor:
                        elapsed_distance = self.speed * self.elapsed

                #들어온 객체 저장
                part_length = port_in.get("part").get("length")
                self.conveyor.append({
                    "incoming"  : port_in,              #들어온 객체 저장
                    "get_time"  : self.current_time,    #들어온 시점
                    "distance"  : 0,                    #현재 위치(앞부분 기준)
                    "part_len"  : part_length,          #파트 길이
                    "is_arrive" : False                 #도착 여부
                })
                
                


                

                self.length - part_length

                if self.length < 0:
                    self.is_full = True

                #다음 이벤트 시간 설정
                if self.remain_time == INFINITY:
                    front_ent = self.conveyor[0]
                    if front_ent.get("arr_time") == None:
                        self.remain_time = INFINITY
                    else:
                        self.remain_time = front_ent.get("arr_time")
                else:
                    self.remain_time -= self.elapsed

                return self.state              
            
        if response_in:
            if response_in.get("state") == "pop":
                if self.remain_time != INFINITY:
                    self.remain_time -= self.elapsed
                
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
                
            elif response_in.get("state") == "block":
                if self.remain_time != INFINITY:
                    self.remain_time -= self.elapsed
                self.do_pop = False
                return self.state
                
        if self.remain_time != INFINITY:
            self.remain_time -= self.elapsed
        return self.state
            
    def outputFnc(self):
        state = self.state.get()
        
        #print(state)
        __out = Out()

        if state == "pop":
            if self.is_full == False:
                __out = self.__pop.get("incoming")
                __out.set("state",state)
                
                elased_time = self.current_time - self.__pop.get("get_time")
                __out.set(self.name,elased_time)
                #print("out")
                return {self.outport: __out}
            else:
                __out.set("state","block")
                return {self.outport: __out}
        if state == "ready":
            if self.is_full == True:
                __out.set("state","block")
                __out.set("msg", "conveyor is full")
                return {self.outport: __out}
            else:
                __out.set("state",state)
                return {self.outport: __out}
            
        if state == "empty":
            __out.set("state","empty")
            return {self.outport: __out}

        
        
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
    "name"  :["source","source_buffer", "station_1",    "conveyor_1",   "station_2",    "result"],
    "type"  :["Source", "Buffer",       "Station",      "Conveyor",     "Station",      "Drain"],
    "time"  :[2,        None,           2,              2,              10,             None]
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

            elif type == "Conveyor":
                setattr(self,name,self.addSubModel(Conveyor(name=name,length=time)))

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
        
            if now_type == "Station" or now_type == "Buffer" or now_type == "Conveyor" :
                if next_type == "Station" or next_type == "Buffer" or next_type == "Conveyor":
                    val_response_outport = val_next.outport
                    val_response_inport = val_now.response_inport
                    self.connectPorts(val_response_outport, val_response_inport)

    def select(self, imm):
        for var_name in reversed(self.variable_name):
            var_value = getattr(self, var_name)
            if var_value in imm:
                return var_value
        





sim = Simulator(LinearLine("LinearLine",inputData=inputData))

#sim.setVerbose()
sim.setTerminationTime(60)
sim.setClassicDEVS()

sim.simulate()