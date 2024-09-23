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
        self.max_length = length
        self.speed = speed

    def timeAdvance(self):
        state = self.state.get()
        #print("---------------------------------------------------------")
        #print(f"TA, current_time : {self.current_time}, state : {state}, remain_time : {self.remain_time}")

        if state == "block":
            return INFINITY
        
        elif state == "ready":
            return self.remain_time
        
        elif state == "empty":
            return self.remain_time
        
        elif state == "pop":
            self.__pop = self.conveyor.pop(0)
            return 0.0
        
        else:
            raise DEVSException(\
                "unknown state <%s> in <%s> time advance transition function"\
                % (state, self.name))
        
    def intTransition(self):
        state = self.state.get()
        if state == "ready" or state == "empty":
            self.current_time += self.remain_time
        #print("---------------------------------------------------------")
        #print(f"INT, current_time : {self.current_time}, state : {state}, remain_time : {self.remain_time}")

        #정보 업데이트
        for ent in self.conveyor:
            if ent.get("is_arrive") == False:
                if ent.get("event_time") == self.current_time:
                    if ent.get("possible_distance") == self.op_length:
                        ent["moving_distance"] = self.op_length
                        ent["is_arrive"] = True
                        ent["is_moving"] = False
                    else:
                        ent["moving_distance"] = ent.get("possible_distance") 
                        ent["is_moving"] = False
                else:
                    continue


        if state == "empty":
            if len(self.conveyor) == 0:
                return self.state

            else:
                #도착했다면?
                #print("part is arrive")
                #print(self.conveyor[0])
                if self.conveyor[0].get("is_arrive") == True:
                    #바로 pop 해야하는 지 체크
                    if self.do_pop == True:
                        #print("do_pop immediatly")
                        self.state = State_str("pop")
                        return self.state
                    
                    #아니면 ready로 상태천이
                    else:
                        self.state = State_str("ready")

                        for ent in self.conveyor:
                            if ent.get("event_time") <= self.current_time:
                                self.remain_time = INFINITY
                                continue
                            else:
                                tmp = self.op_length / self.speed
                                if tmp > (ent.get("event_time") - self.current_time):
                                    tmp = ent.get("event_time") - self.current_time
                                    self.remain_time = tmp
                        #print(f"set state : ready, remain_time : {self.remain_time}")
                        return self.state

        elif state == "ready":
                if self.is_full == True:
                    self.state = State_str("block")
                else:
                    self.state = State_str("ready")


                for ent in self.conveyor:
                    if ent.get("event_time") <= self.current_time:
                        self.remain_time = INFINITY
                        continue
                    else:
                        tmp = self.op_length / self.speed
                        if tmp > (ent.get("event_time") - self.current_time):
                            tmp = ent.get("event_time") - self.current_time
                            self.remain_time = tmp
                return self.state

        if state == "pop":
            self.max_length += self.__pop.get("part_len")
            plus_len = self.__pop.get("part_len")
            for ent in self.conveyor:
                if ent.get("is_arrive") == False:
                    ent["possible_distance"] += plus_len
                    if ent.get("is_moving") == False:
                        ent["event_time"] = self.current_time + (plus_len / self.speed)
                    else:
                        ent["event_time"] += (plus_len / self.speed)


            if len(self.conveyor) == 0 :
                self.remain_time = INFINITY
                self.state = State_str("empty")
                #print(f"set state : {self.state}, remain_time = {self.remain_time}")
                return self.state
            
            if self.conveyor[0].get("is_arrive") == True:
                self.state = State_str("ready")
            else:
                self.state = State_str("empty")

            tmp = self.op_length / self.speed
            for ent in self.conveyor:
                if ent.get("event_time") <= self.current_time:
                    continue
                else:
                    if tmp > (ent.get("event_time") - self.current_time):
                        tmp = ent.get("event_time") - self.current_time
                        self.remain_time = tmp

            #print(f"set state : {self.state}, remain_time = {self.remain_time}")
            return self.state
                        
        else:
            raise DEVSException(\
                "unknown state <%s> in <%s> internal transition function"\
                % (state, self.name))

    def extTransition(self, inputs):
        state = self.state.get()
        self.current_time += self.elapsed
        #print("---------------------------------------------------------")
        #print(f"EXT, current_time : {self.current_time}, state : {state}")

        port_in = inputs.get(self.inport, None)
        response_in = inputs.get(self.response_inport, None)

        #컨베이어 위에 객체 있으면 정보 업데이트
        if len(self.conveyor) != 0 and self.elapsed != 0:
            for ent in self.conveyor:
                elapsed_distance = self.speed * self.elapsed

                moving_distance = ent.get("moving_distance")
                possible_distance = ent.get("possible_distance")

                if possible_distance > (moving_distance + elapsed_distance):
                    #이동거리 업데이트
                    ent["moving_distance"] = moving_distance + elapsed_distance

                else:
                    #이동가능거리까지 이동했다는 뜻
                    ent["moving_distance"] = possible_distance
                    ent["is_moving"] = False
        
        # inport
        if port_in:
            if port_in.get("state") == "pop":
                #print("EXT port_in")

                #들어온 객체 저장
                part_length = port_in.get("part").get("length")
                self.conveyor.append({
                    "incoming"  : port_in,              #들어온 객체 저장
                    "get_time"  : self.current_time,    #들어온 시점
                    "part_len"  : part_length,          #파트 길이

                    "moving_distance"  : 0,                                             #현재 위치(앞부분 기준)
                    "possible_distance": self.max_length,                               #이동가능한 거리
                    "is_arrive" : False,                                                #도착 여부
                    "is_moving" : True,                                                 #움직이고 있는지 여부
                    "event_time": self.current_time + (self.max_length / self.speed)    #들어오고 이동가능위치에 도착했을 때 시간
                })

                #print(f"current_time : {self.current_time}, event_time : {self.current_time + (self.max_length / self.speed)}")
                self.max_length -= part_length
                #print("max_length = ", self.max_length)

                if self.max_length <= 0:
                    self.is_full = True


                #시간설정
                for ent in self.conveyor:
                    ev_time = ent.get("event_time")

                    tmp = self.op_length / self.speed
                    if ev_time < self.current_time:
                        self.remain_time = INFINITY
                        continue
                    else:
                        #바로 다음 이벤트 시간까지의 시간으로 설정
                        if tmp > (ev_time - self.current_time):
                            tmp = ev_time - self.current_time
                        self.remain_time = tmp
                #print(f"set state : {self.state}, remain_time = {self.remain_time}")
                return self.state
      
            
        if response_in:
            for ent in self.conveyor:
                ev_time = ent.get("event_time")

                tmp = self.op_length / self.speed
                if ev_time < self.current_time:
                    self.remain_time = INFINITY
                    continue
                else:
                    #바로 다음 이벤트 시간까지의 시간으로 설정
                    if tmp > (ev_time - self.current_time):
                        tmp = ev_time - self.current_time
                    self.remain_time = tmp

            if response_in.get("state") == "pop":
                #print("response_in : block해제 ")
                
                #Save this response
                self.do_pop = True
                self.is_full = False

                #If Buffer Can't pop entry
                if state == "empty":
                    #print("not ready")
                    self.state = State_str("empty")
                    #print(f"set state : {self.state}, remain_time : {self.remain_time}")
                    return self.state
                
                #Buffer can pop entry
                else:
                    #Set state "pop"
                    #print("do pop")
                    self.state = State_str("pop")
                    #Release do_pop
                    self.do_pop = False
                    #print(f"set state : {self.state}, remain_time : {self.remain_time}")
                    return self.state
                
            elif response_in.get("state") == "block":
                #print("next ent was blocked")
                self.do_pop = False
                #print(f"set state : {self.state}, remain_time : {self.remain_time}")
                return self.state
                
        for ent in self.conveyor:
            ev_time = ent.get("event_time")

            tmp = self.op_length / self.speed
            if ev_time < self.current_time:
                self.remain_time = INFINITY
                continue
            else:
                #바로 다음 이벤트 시간까지의 시간으로 설정
                if tmp > (ev_time - self.current_time):
                    tmp = ev_time - self.current_time
                self.remain_time = tmp
        #print(f"set state : {self.state}, remain_time : {self.remain_time}")
        return self.state
            
    def outputFnc(self):
        state = self.state.get()
        #print("---------------------------------------------------------")
        #print(f"OUT, current_time = {self.current_time}, state : {state}")
        
        ##print(state)
        __out = Out()

        if state == "pop":
            if self.is_full == False:
                #print("doing pop")
                __out = self.__pop.get("incoming")
                __out.set("state",state)
                
                elased_time = self.current_time - self.__pop.get("get_time")
                __out.set(self.name,elased_time)
                ##print("out")
                return {self.outport: __out}
            else:
                #print("block signal")
                __out.set("state","block")
                return {self.outport: __out}
            
        if state == "ready":
            if self.is_full == True:
                #print("block signal")
                __out.set("state","block")
                __out.set("msg", "conveyor is full")
                return {self.outport: __out}
            else:
                __out.set("state",state)
                return {self.outport: __out}
            
        if state == "empty":
            #print("not ready")
            if self.is_full:
                __out.set("state","block")
            else:
                __out.set("state","empty")
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
            return self.remain_time
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
                __out.set("msg","first block")
                return {self.outport: __out}
            
            else:
                if self.next_is_blocked == True:
                    __out.set("state","block")
                    __out.set("msg","next is block")
                    return {self.outport: __out}
                
                else:
                    ##print(self.name, self.current_time, "out")
                    ##print(self.name, " out")
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
            #print(f"total : {self.count}")
            self.state = State_arr(["get", self.count])
            return self.state
        else:
            self.state = State_arr(["get", self.count])
            return self.state
    
    

class Seperator(AtomicDEVS):
    def __init__(self, name = 'seperator', out_way = 3):
        AtomicDEVS.__init__(self, name)
        self.name = name
        self.state = State_str("ready")
        self.out_way = out_way
        self.num = 0

        __out = Out()
        __out.set("state","ready")
        self.incoming = __out

        inport_name = name + '_inport'
        self.inport = self.addInPort(inport_name)

        for num in range(out_way):
            outport_name = name + "_outport_" + str(num)
            val_name = "outport_" + str(num)
            setattr(self, val_name, self.addOutPort(outport_name))
            
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
        
        ##print(self.name,self.current_time,"int")

        if state == "pop":
            self.state = State_str("ready")

            return self.state
            
        else:
            raise DEVSException(\
                "unknown state <%s> in <%s> internal transition function"\
                % (state, self.name))
    
    def extTransition(self, inputs):
        port_in =inputs[self.inport]

        self.incoming = port_in
        if self.incoming.get("state") == "pop":
            self.state = State_str("pop")
        else:
            self.state = State_str("ready")

        return self.state
    
    def outputFnc(self):

        for out_num in range(self.out_way):
            if self.num == out_num:
                _outport_name = "outport_"+str(self.num)
                outport_value = getattr(self, _outport_name)
                self.incoming.set("seperator",_outport_name)
                if self.num < self.out_way-1:
                    self.num += 1
                else:
                    self.num = 0
                return {outport_value: self.incoming}



class Line_in_Cell(CoupledDEVS):
    def __init__(self, name="LinC", inputData= {}):
        CoupledDEVS.__init__(self, name)

        self.conveyor1 = self.addSubModel(Conveyor(name="conveyor1"))
        self.station1 = self.addSubModel(Station(name="station1"))
        self.station2 = self.addSubModel(Station(name="station2"))
        self.conveyor2 = self.addSubModel(Conveyor(name="conveyor2"))

        self.inport = self.addInPort(name="LC_in")
        self.outport = self.addOutPort(name="LC_out")
        self.response_inport = self.addInPort(name="LC_response")

        self.connectPorts(self.inport, self.conveyor1.inport)

        self.connectPorts(self.conveyor1.outport, self.station1.inport)
        self.connectPorts(self.station1.outport, self.station2.inport)
        self.connectPorts(self.station2.outport, self.conveyor2.inport)

        self.connectPorts(self.conveyor2.outport, self.station2.response_inport)
        self.connectPorts(self.station2.outport, self.station1.response_inport)
        self.connectPorts(self.station1.outport, self.conveyor1.response_inport)

        self.connectPorts(self.conveyor2.outport, self.outport)

    def select(self, imm):
        if self.conveyor2 in imm:
            return self.conveyor2
        elif self.station2 in imm:
            return self.station2
        elif self.station1 in imm:
            return self.station1
        elif self.conveyor1 in imm:
            return self.conveyor1

class Cell(CoupledDEVS):
    def __init__(self, name="cell"):
        CoupledDEVS.__init__(self, name)

        self.seperator = self.addSubModel(Seperator(name="seperator",out_way=3))

        self.line0 = self.addSubModel(Line_in_Cell(name="LinC0"))
        self.line1 = self.addSubModel(Line_in_Cell(name="LinC1"))
        self.line2 = self.addSubModel(Line_in_Cell(name="LinC2"))

        self.buffer = self.addSubModel(Buffer(name="buffer"))

        self.inport = self.addInPort(name="Cell_in")
        self.outport = self.addOutPort(name="Cell_out")
        self.response_inport = self.addInPort(name="Cell_response_inport")

        self.connectPorts(self.inport, self.seperator.inport)

        self.connectPorts(self.seperator.outport_0, self.line0.inport)
        self.connectPorts(self.seperator.outport_1, self.line1.inport)
        self.connectPorts(self.seperator.outport_2, self.line2.inport)

        self.connectPorts(self.line0.outport, self.buffer.inport)
        self.connectPorts(self.line1.outport, self.buffer.inport)
        self.connectPorts(self.line2.outport, self.buffer.inport)

        self.connectPorts(self.response_inport, self.buffer.response_inport)
        self.connectPorts(self.buffer.outport, self.outport)

    def select(self, imm):
        if self.buffer in imm:
            return self.buffer
        elif self.line2 in imm:
            return self.line2
        elif self.line1 in imm:
            return self.line1
        elif self.line0 in imm:
            return self.line0
        elif self.seperator in imm:
            return self.seperator

class Test(CoupledDEVS):
    def __init__(self, name="Test"):
        CoupledDEVS.__init__(self, name)

        self.source = self.addSubModel(Source(name="source",interval=2))
        self.buffer = self.addSubModel(Buffer(name="buffer"))

        self.station_first = self.addSubModel(Station(name="station_first"))

        self.cell = self.addSubModel(Cell(name="cell"))
        #self.line0 = self.addSubModel(Line_in_Cell(name="LinC0"))

        self.station_last = self.addSubModel(Station(name="station_last"))
        self.result = self.addSubModel(Drain(name="result"))

        self.connectPorts(self.source.outport, self.buffer.inport)
        self.connectPorts(self.buffer.outport, self.station_first.inport)
        self.connectPorts(self.station_first.outport, self.cell.inport)
        self.connectPorts(self.cell.outport, self.station_last.inport)
        self.connectPorts(self.station_last.outport, self.result.inport)

        self.connectPorts(self.station_last.outport, self.cell.response_inport)
        self.connectPorts(self.station_first.outport, self.buffer.response_inport)

    def select(self, imm):
        if self.result in imm:
            return self.result
        elif self.station_last in imm:
            return self.station_last
        elif self.cell in imm:
            return self.cell
        elif self.station_first in imm:
            return self.station_first
        elif self.buffer in imm:
            return self.buffer
        elif self.source in imm:
            return self.source

#setting
sim = Simulator(Test("Test"))

sim.setVerbose()
sim.setTerminationTime(100)

sim.setClassicDEVS()

sim.simulate()

        

class Gen_LINE(CoupledDEVS):
    def __init__(self, name="Gen_LINE", inputData= {}):
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

            elif type == "Cell":
                setattr(self,name,self.addSubModel(Cell(name=name)))
            

            elif type == "Station":
                setattr(self,name,self.addSubModel(Station(name=name,working_time=time)))

            else:
                setattr(self,name,self.addSubModel(Drain(name=name)))
            self.variable_name.append(name)
            self.variable_type.append(type)

        #print(self.variable_name)
        #print(self.variable_type)

        for i in range(len(self.variable_name)-1):
            val_now = getattr(self, self.variable_name[i])
            val_next = getattr(self, self.variable_name[i+1])
            val_outport = val_now.outport
            val_inport = val_next.inport
            self.connectPorts(val_outport,val_inport)

            now_type = self.variable_type[i]
            next_type = self.variable_type[i+1]
        
            if now_type == "Station" or now_type == "Buffer" or now_type == "Conveyor" or now_type == "Cell" :
                if next_type == "Station" or next_type == "Buffer" or next_type == "Conveyor":    
                    val_response_outport = val_next.outport
                    val_response_inport = val_now.response_inport
                    self.connectPorts(val_response_outport, val_response_inport)

    def select(self, imm):
        for var_name in reversed(self.variable_name):
            var_value = getattr(self, var_name)
            if var_value in imm:
                return var_value
        

