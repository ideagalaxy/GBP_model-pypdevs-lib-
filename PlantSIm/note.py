
from pypdevs.DEVS import *
from pypdevs.infinity import INFINITY
import random
from pypdevs.simulator import Simulator

from MUs import *

class Conveyor(AtomicDEVS):
    def __init__(self, name = 'conveyor', length = 2, speed = 1.0):
        AtomicDEVS.__init__(self, name)
        self.name = name
        self.state = State_arr(["empty",INFINITY])
        self.current_time = 0.0

        outport_name = name + '_outport'
        inport_name = name + '_inport'
        response_inport_name = name + '_response_inport'

        self.inport = self.addInPort(inport_name)
        self.outport = self.addOutPort(outport_name)
        self.response_inport = self.addInPort(response_inport_name)

        self.remain_time = INFINITY
        self.conveyor = []
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
                self.remain_time == INFINITY
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
            self.conveyor[0]["is_arrive"] = True

            if self.do_pop == True:
                self.state = State_arr(["pop",next_time])
            else:
                if self.is_full == True:
                    self.state = State_arr("block",next_time)
                else:
                    self.state = State_arr("ready",next_time)

        if state == "pop":
            self.max_length += self.__pop.get("part_len")
            plus_time = self.__pop.get("part_len") / self.speed

            if len(self.conveyor) == 0:
                self.state = State_arr(["empty",INFINITY])
                return self.state
            else:
                first = self.conveyor[0]
                self.remain_time

                self.state = State_arr(["empty",next_time])



    def extTransition(self, inputs):
        state_arr = self.state.get()
        state = state_arr[0]
        next_time =state_arr[1]
        self.current_time += self.elapsed

        port_in = inputs.get(self.inport, None)
        response_in = inputs.get(self.response_inport, None)

        if port_in:
            if state != "block":
                #empty나 ready일때만 append 진행
                if port_in.get("state") == "pop":
                    #part 들어올 때
                    part_length = port_in.get("part").get("length")

                    self.conveyor.append({
                        "incoming"  : port_in,              #들어온 객체 저장
                        "get_time"  : self.current_time,    #들어온 시점
                        "part_len"  : part_length,          #파트 길이

                        "is_arrive" : False,                                                #도착 여부
                        "event_time": self.current_time + (self.max_length / self.speed)    #들어오고 이동가능위치에 도착했을 때 시간
                    })

                    self.max_length -= part_length
                    if self.max_length <= 0:
                        self.is_full = True

                    #처음 들어오거나 아직 도착 안했을때
                    if state == "empty":
                        self.state = State_arr(["empty",next_time])
                        return self.state
                    
                    #끝에 도착한게 있을 때
                    elif state == "ready":
                        return self.state

        if response_in:
            if response_in.get("state") == "pop":
                self.do_pop = True
                self.is_full = False

                if state == "empty":
                    self.state = State_arr(["empty",next_time])
                    return self.state
                else:
                    self.state = State_arr(["pop",next_time])
                    return self.state
    
            elif response_in.get("state") == "block":
                self.do_pop = False

        return self.state


    def get_next_event_time(self,conveyor):
        first = conveyor[0]
        next_event_time = first["event_time"]
        
        return next_event_time
                
                
                


                
    def calculate_remain_time(self, conveyor):
        first_element = conveyor[0]
        get_time = first_element["get_time"]
        next_event_time = get_time + (self.op_length / self.speed)
        remain_time = self.current_time - next_event_time

        return remain_time
    
    def check_full(self, conveyor):
        check_length = 0
        for element in conveyor:
            check_length += element["part_len"]

        if check_length >= self.op_length:
            return True
        else:
            return False        

                        
                