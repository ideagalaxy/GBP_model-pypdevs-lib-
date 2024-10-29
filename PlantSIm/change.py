class Conveyor(AtomicDEVS):

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