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
#from GenerateCell import Cell




    
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
            __out.set("sender", self.name)

            self.count += 1
            name = "part_" + str(self.count)
            __out.set("part_name",name)
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
                            self.state = State_str("pop") #block된 신호를 내보내기 위해 pop 거침
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
                __out.set("sender", self.name)
                
                elased_time = self.current_time - self.__pop.get("get_time")
                __out.set(self.name,elased_time)
                
                return {self.outport: __out}
            else:
                __out.set("state","block")
                __out.set("sender", self.name)
                return {self.outport: __out}

class Conveyor(AtomicDEVS):
    def __init__(self, name = 'conveyor', length = 2, speed = 1.0):
        AtomicDEVS.__init__(self, name)
        self.conveyor = []
        self.name = name
        self.state = State_arr(["empty",INFINITY,len(self.conveyor)])
        self.current_time = 0.0

        print(f"{self.name} : set length={length}, set speed={speed}")

        outport_name = name + '_outport'
        inport_name = name + '_inport'
        response_inport_name = name + '_response_inport'

        self.inport = self.addInPort(inport_name)
        self.outport = self.addOutPort(outport_name)
        self.response_inport = self.addInPort(response_inport_name)

        self.remain_time = INFINITY
        
        self.is_full = False
        self.do_pop = True

        #setting
        self.op_length = length
        self.max_length = length
        self.speed = speed

    def timeAdvance(self):
        state_arr = self.state.get()
        state = state_arr[0]

        if state == "block":
            return INFINITY
        
        elif state == "ready":
            return INFINITY
        
        elif state == "empty":
            if len(self.conveyor) == 0:
                self.remain_time = INFINITY
                return self.remain_time
            else:
                first = self.conveyor[0]
                self.remain_time = first["event_time"] - self.current_time
                return self.remain_time
            
        
        elif state == "pop":
            self.__pop = self.conveyor.pop(0)
            return 0.0
        
        
        else:
            raise DEVSException(\
                "unknown state <%s> in <%s> time advance transition function"\
                % (state, self.name))    

    def intTransition(self):
        state_arr = self.state.get()
        state = state_arr[0]
        next_time = state_arr[1]

        if state == "empty": 
            #update current_time
            self.current_time += self.remain_time

            if self.do_pop == True:
                if len(self.conveyor) > 0:
                    self.state = State_arr(["pop",self.current_time,len(self.conveyor)])
                else:
                    self.state = State_arr(["empty",INFINITY,len(self.conveyor)])
            else:
                if self.is_full == True:
                    self.state = State_arr(["block",INFINITY,len(self.conveyor)])
                else:
                    self.state = State_arr(["ready",INFINITY,len(self.conveyor)])
            
            return self.state

        if state == "pop":
            #정보 업데이트
            self.max_length += self.__pop.get("part_len")
            plus_time = self.__pop.get("part_len") / self.speed

            if len(self.conveyor) == 0:
                self.state = State_arr(["empty",INFINITY,len(self.conveyor)])
                return self.state
            
            else:
                first = True
                for item in self.conveyor: #이미 pop은 되어 있는 상태
                    if item["event_time"] > self.current_time:
                        item["event_time"] += plus_time
                    else:
                        item["event_time"] = self.current_time + plus_time

                    if first == True:
                        next_time = item["event_time"]
                        first = False

                self.state = State_arr(["empty",next_time,len(self.conveyor)])
                return self.state

    def extTransition(self, inputs):
        state_arr = self.state.get()
        state = state_arr[0]
        next_time =state_arr[1]
        self.current_time += self.elapsed

        port_in = inputs.get(self.inport, None)
        response_in = inputs.get(self.response_inport, None)

        if port_in:
            if self.is_full == False:
                #empty나 ready일때만 append 진행
                if port_in.get("state") == "pop":
                    #part 들어올 때
                    part_length = port_in.get("part").get("length")

                    self.conveyor.append({
                        "incoming"  : port_in,              #들어온 객체 저장
                        "get_time"  : self.current_time,    #들어온 시점
                        "part_len"  : part_length,          #파트 길이
                        "event_time": self.current_time + (self.max_length / self.speed)    #들어오고 이동가능위치에 도착했을 때 시간
                    })

                    self.max_length -= part_length
                    if self.max_length < 0:
                        self.is_full = True

                    #처음 들어오거나 아직 도착 안했을때
                    if state == "empty":
                        next_time = self.conveyor[0]["event_time"]
                        self.state = State_arr(["empty",next_time,len(self.conveyor)])
                        return self.state
                    
                    #끝에 도착한게 있을 때
                    elif state == "ready":
                        state_arr[2] = len(self.conveyor)
                        self.state = State_arr(state_arr)
                        return self.state

        if response_in:
            if response_in.get("state") == "pop":
                self.do_pop = True
                self.is_full = False

                if state == "empty":
                    self.state = State_arr(["empty",next_time,len(self.conveyor)])
                    return self.state
                else:
                    self.state = State_arr(["pop",next_time,len(self.conveyor)])
                    return self.state
    
            elif response_in.get("state") == "block":
                self.do_pop = False

        state_arr[2] = len(self.conveyor)
        self.state = State_arr(state_arr)
        return self.state
    
    def outputFnc(self):
        state_arr = self.state.get()
        state = state_arr[0]
        next_time =state_arr[1]

        __out = Out()
        if state == "pop":
            __out = self.__pop.get("incoming")
            __out.set("state",state)
            __out.set("sender", self.name)
            elased_time = self.current_time - self.__pop.get("get_time")
            __out.set(self.name,elased_time)

            return {self.outport: __out}
        
        if state == "empty":
            if self.do_pop == False:
                if self.is_full:
                    __out.set("state","block")
                    __out.set("sender", self.name)
                else:
                    __out.set("state","empty")
                    __out.set("sender", self.name)
                return {self.outport: __out}
            
            else:
                __out.set("state","waiting for pop")
                __out.set("sender", self.name)
                return {self.outport: __out}

   
class Station(AtomicDEVS):
    '''
    working_time = [mu,sigma,lower,upper]
    if sigma = 0 , than working_time will set const mu
    '''
    def __init__(self, name = 'station', working_time = [10,0,0,0]):
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
        self.working_time_setting = working_time
        self.remain_time = 0

    def generate_normal(self,setting):
        import scipy.stats as stats
        mu = setting[0]
        sigma = setting[1]
        lower = setting[2]
        upper = setting[3]

        if sigma == 0:
            return mu
        
        low = (lower - mu) / sigma
        upp = (upper - mu) / sigma
        
        #make randnum
        samples = stats.truncnorm.rvs(low, upp, loc=mu, scale=sigma, size=1)
        working_time = int(samples[0])
        return working_time

    def timeAdvance(self):
        state = self.state.get()
        ##print(self.name, self.current_time,"TA",state)

        if state == "ready":
            return INFINITY
        elif state == "block":
            return INFINITY
        elif state == "busy":
            self.current_time += self.remain_time
            return int(self.remain_time * 10) / 10
        else:
            raise DEVSException(\
                "unknown state <%s> in <%s> time advance transition function"\
                % (state, self.name))
    
    def intTransition(self):
        state = self.state.get()
        
        ##print(self.name,self.current_time,"int")

        if state == "busy":
            if self.is_first_pulse == True:
                self.is_first_pulse = False
                self.is_in = True
                self.remain_time = self.generate_normal(self.working_time_setting)
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
        ##print(self.name, self.current_time, "ext")
        
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
                __out.set("sender", self.name)
                __out.set("msg","first block")
                return {self.outport: __out}
            
            else:
                if self.next_is_blocked == True:
                    __out.set("state","block")
                    __out.set("sender", self.name)
                    __out.set("msg","next is block")
                    return {self.outport: __out}
                
                else:
                    ##print(self.name, self.current_time, "out")
                    ##print(self.name, " out")
                    __out = self.__product.get("incoming")
                    __out.set("state","pop")
                    __out.set("sender", self.name)
                    
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
        outport_name = name + '_outport'
        self.outport = self.addOutPort(outport_name)
        self.count = 0
        self.result = []

        self.time = INFINITY
    
    def intTransition(self):
        state = self.state.get()

        if self.time == 0:
            self.time = INFINITY
            return self.state
        else:
            raise DEVSException(\
                "unknown state <%s> in <%s> internal transition function"\
                % (state, self.name))

    def timeAdvance(self):
        state = self.state.get()

        if state[0] == "get":
            return self.time
        else:
            raise DEVSException(\
                "unknown state <%s> in <%s> time advance transition function"\
                % (state, self.name))
        
    def extTransition(self, inputs):
        port_in =inputs[self.inport]

        if port_in.get("state") == "pop":
            self.count += 1
            print("Total : ", self.count)
            self.result.append(port_in)
            self.state = State_arr(["get", self.count])
            self.time = 0
            return self.state
        else:
            self.state = State_arr(["get", self.count])
            self.time = INFINITY
            return self.state
    
    def outputFnc(self):
        state = self.state.get()

        __out = Out()
        __out.set("state","pop")
        msg = " : "+ str(self.count)
        __out.set("get",msg)
        return {self.outport: __out}
    

class Seperator(AtomicDEVS):
    def __init__(self, name = 'seperator', out_way = 3):
        AtomicDEVS.__init__(self, name)
        self.name = name
        self.state = State_str("ready")
        self.out_way = out_way

        __out = Out()
        __out.set("state","ready")
        __out.set("sender", self.name)
        self.incoming = __out

        inport_name = name + '_inport'
        self.inport = self.addInPort(inport_name)

        self.buffer = []
        self.status = []
        self.reponse_inport_list = []

        for num in range(out_way):
            outport_name = name + "_outport_" + str(num)
            val_name = "outport_" + str(num)
            setattr(self, val_name, self.addOutPort(outport_name))

            response_inport_name = name + "_response_inport_" + str(num)
            val_name = "response_inport_" + str(num)
            setattr(self, val_name, self.addInPort(response_inport_name))
            self.reponse_inport_list.append(val_name)

            self.status.append(["ready",num])
            
    def timeAdvance(self):
        state = self.state.get()

        if state == "ready":
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
            self.state = State_str("ready")
            return self.state
            
        else:
            raise DEVSException(\
                "unknown state <%s> in <%s> internal transition function"\
                % (state, self.name))
    
    def extTransition(self, inputs):
        port_in = inputs.get(self.inport, None)

        port_num = None
        i = 0
        for inport in self.reponse_inport_list:
            value = getattr(self, inport)
            response = inputs.get(value, None)
            if response != None:
                port_num = i
                break
            i += 1

        if port_in:
            if port_in.get("state") == "pop":
                self.buffer.append(port_in)

                self.state = State_str("ready")
                for flag in self.status:
                    if flag[0] == "ready":
                        self.state = State_str("pop")
                        break
                return self.state
        
        if response:
            for res_port in self.status:
                if res_port[1] == port_num:
                    if response.get("state") == "block":
                        #print(self.status)
                        #print(f"{self.name} : port{port_num} = BLOCK")
                        res_port[0] = "block"

                    if response.get("state") == "pop":

                        '''if res_port[0] == "block":
                            print(f"{self.name} : port{port_num} = BLOCK RELEASE")'''
                        
                        res_port[0] = "ready"
                    break

        self.state = State_str("ready")
        return self.state
    
    def outputFnc(self):
        for flag in self.status:
            if flag[0] == "ready":
                out_num = flag[1]
                break
        self.status = self.status[1:] + self.status[:1]

        _outport_name = "outport_"+str(out_num)
        outport_value = getattr(self, _outport_name)
        self.incoming.set("seperator",_outport_name)

        return {outport_value: self.buffer.pop(0)}




        

