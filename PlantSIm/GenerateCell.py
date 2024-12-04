from pypdevs.DEVS import *
from pypdevs.infinity import INFINITY


from MUs import *
from MaterialFlow import Source, Conveyor, Buffer, Drain, Station, Seperator

class One_sided_Wingbody_Seperator(AtomicDEVS):
    def __init__(self, name = 'One_sided_Wingbody_Seperator', out_way = 3):
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
                        print(self.status)
                        print(f"{self.name} : port{port_num} = BLOCK")
                        res_port[0] = "block"

                    if response.get("state") == "pop":
                        if res_port[0] == "block":
                            print(f"{self.name} : port{port_num} = BLOCK RELEASE")
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

        return {outport_value: self.buffer[0]}

class One_sided_Wingbody_Module(CoupledDEVS):
    def __init__(self, name="One_sided_Wingbody_Module",line_num = 2, cycle_time = 6, add_conv = False):
        CoupledDEVS.__init__(self, name)

        self.inport = self.addInPort(name="One_sided_Wingbody_Module_in")
        self.outport = self.addOutPort(name="One_sided_Wingbody_Module_out")

        self.seperator = self.addSubModel(One_sided_Wingbody_Seperator(name="seperator",out_way=line_num))

        tmp = ["seperator"]

        self.connectPorts(self.inport, self.seperator.inport)
        if add_conv == True:
            add_length = 2
        else:
            add_length = 0 
        conv_length = 2*line_num + add_length

        for line in range(line_num):
            line_name = "conveyor_" + str(line)
            setattr(self,line_name,self.addSubModel(Conveyor(name=line_name, length=conv_length)))
            tmp.append(line_name)
            task_name = "task_" + str(line)
            setattr(self,task_name,self.addSubModel(Station(name=task_name, working_time=[cycle_time,0,0,0])))
            tmp.append(task_name)

            conv_var = getattr(self, line_name)
            task_var = getattr(self, task_name)

            self.connectPorts(task_var.outport, conv_var.inport)
            self.connectPorts(conv_var.outport, task_var.response_inport)
            self.connectPorts(conv_var.outport, self.outport) 

            sep_outport_name = "outport_"+str(line)
            sep_res_in_name = "response_inport_"+str(line)

            sep_outport = getattr(self.seperator, sep_outport_name)
            sep_res_in = getattr(self.seperator, sep_res_in_name)

            self.connectPorts(sep_outport,task_var.inport)
            self.connectPorts(task_var.outport, sep_res_in)

        self.variable = tmp

    def select(self, imm):
        for var_name in reversed(self.variable):
            var_value = getattr(self, var_name)
            if var_value in imm:
                return var_value 

class One_sided_Wingbody_Cell(CoupledDEVS):
    
    def __init__(self, name="One_sided_Wingbody_Cell", line_num = 2, task_num = 3, cycle_time = 6):
        '''
        inport / outport / response_inport
        '''
        CoupledDEVS.__init__(self, name)

        if line_num < 2:
            raise ValueError("2개 이상부터 Cell 제작 가능")


        self.inport = self.addInPort(name="One_sided_Wingbody_Cell_in")
        self.outport = self.addOutPort(name="One_sided_Wingbody_Cell_out")
        self.response_inport = self.addInPort(name="One_sided_Wingbody_Cell_response_inport")

        tmp = []
        
        i=0
        for task in range(task_num):
            print("Module : ",task)

            module_name = "module_" + str(task)
            set_add_conv = True
            if task == (task_num-1):
                set_add_conv = False
            setattr(self,module_name,self.addSubModel(One_sided_Wingbody_Module(name=module_name, cycle_time=cycle_time, add_conv=set_add_conv)))
            tmp.append(module_name)
            module_var = getattr(self, module_name) 

            #첫번째 inport 연결 작업
            if task == 0:
                self.connectPorts(self.inport, module_var.inport)
            #앞 컨베이어와 연결 작업
            else:
                prev_module = "module_"+str(task-1)
                prev_module_var = getattr(self, prev_module) 
                self.connectPorts(prev_module_var.outport, module_var.inport)


            #마지막 module 처리 작업
            if task == (task_num-1):
                self.buffer = self.addSubModel(Buffer(name="buffer"))
                tmp.append("buffer")
                self.connectPorts(module_var.outport, self.buffer.inport)
                self.connectPorts(self.response_inport, self.buffer.response_inport)
                self.connectPorts(self.buffer.outport, self.outport)
                
        self.variable = tmp

    def select(self, imm):
        for var_name in reversed(self.variable):
            var_value = getattr(self, var_name)
            if var_value in imm:
                return var_value 

class Two_sided_Wingbody_Module(CoupledDEVS):
    '''
    Conveyor + Seperator + Station/Station(무조건 2개로 설정) + Conveyor
    inport / outport / response_inport / response_outport
    '''
    def __init__(self, name="Two_sided_Wingbody_Module", cycle_time = 6):
        CoupledDEVS.__init__(self, name)

        
        self.conveyor_in = self.addSubModel(Conveyor(name="conveyor_in",length=1))
        self.seperator = self.addSubModel(Seperator(name="seperator",out_way=2))
        self.station1 =  self.addSubModel(Station(name="sub station1",working_time=[cycle_time,0,0,0]))
        self.station2 =  self.addSubModel(Station(name="sub station2",working_time=[cycle_time,0,0,0]))
        self.conveyor_out = self.addSubModel(Conveyor(name="conveyor_out",length=1))

        self.inport = self.addInPort(name="Two_sided_Wingbody_Module_in")
        self.outport = self.addOutPort(name="Two_sided_Wingbody_Module_out")
        self.response_inport = self.addInPort(name="Two_sided_Wingbody_Module_response_inport")
        self.response_outport = self.addOutPort(name="Two_sided_Wingbody_Module_response_outport")


        self.connectPorts(self.inport,self.conveyor_in.inport)
        self.connectPorts(self.conveyor_in.outport, self.seperator.inport)
        self.connectPorts(self.conveyor_in.outport, self.response_outport)

        self.connectPorts(self.seperator.outport_0, self.station1.inport)
        self.connectPorts(self.station1.outport, self.seperator.response_inport_0)
        self.connectPorts(self.station1.outport, self.conveyor_out.inport)

        self.connectPorts(self.seperator.outport_1, self.station2.inport)
        self.connectPorts(self.station2.outport, self.seperator.response_inport_1)
        self.connectPorts(self.station2.outport, self.conveyor_out.inport)

        self.connectPorts(self.conveyor_out.outport, self.station1.response_inport)
        self.connectPorts(self.conveyor_out.outport, self.station2.response_inport)

        self.connectPorts(self.conveyor_out.outport, self.outport)
        self.connectPorts(self.response_inport, self.conveyor_out.response_inport)

    def select(self, imm):
        if self.conveyor_out in imm:
            return self.conveyor_out
        elif self.station2 in imm:
            return self.station2
        elif self.station1 in imm:
            return self.station1
        elif self.seperator in imm:
            return self.seperator
        elif self.conveyor_in in imm:
            return self.conveyor_in
        





class Two_sided_Wingbody_Cell(CoupledDEVS):
    
    def __init__(self, name="Two_sided_Wingbody_Cell", line_num = 2, task_num = 3, cycle_time = 6):
        '''
        inport / outport / response_inport / response_outport
        '''
        CoupledDEVS.__init__(self, name)

        if line_num < 2:
            raise ValueError("2개 이상부터 Cell 제작 가능")


        self.inport = self.addInPort(name="Two_sided_Wingbody_Cell_in")
        self.outport = self.addOutPort(name="Two_sided_Wingbody_Cell_out")
        self.response_inport = self.addInPort(name="Two_sided_Wingbody_Cell_response_inport")
        self.response_outport = self.addOutPort(name="Two_sided_Wingbody_Cell_response_outport")

        tmp = []
        
        i=0
        for task in range(task_num):
            print("task : ",task)

            task_name = "task_" + str(task)
            setattr(self,task_name,self.addSubModel(Two_sided_Wingbody_Module(name=task_name, cycle_time=cycle_time)))
            tmp.append(task_name)
            task_var = getattr(self, task_name) 

            #첫번째 inport 연결 작업
            if task == 0:
                self.connectPorts(self.inport, task_var.inport)
                self.connectPorts(task_var.response_outport, self.response_outport)
            #앞 컨베이어와 연결 작업
            else:
                conveyor_name = "conveyor_"+str(task-1)
                conv_var = getattr(self, conveyor_name) 
                self.connectPorts(conv_var.outport, task_var.inport)
                self.connectPorts(task_var.response_outport, conv_var.response_inport)


            #마지막 task 처리 작업
            if task == (task_num-1):
                self.connectPorts(self.response_inport, task_var.response_inport)
                self.connectPorts(task_var.outport, self.outport)
            #뒤에 컨베이어 연결작업
            else:
                conveyor_name = "conveyor_"+str(task)
                setattr(self,conveyor_name,self.addSubModel(Conveyor(name=conveyor_name, length=2)))
                tmp.append(conveyor_name)
                conv_var = getattr(self, conveyor_name) 

                self.connectPorts(task_var.outport, conv_var.inport)
                self.connectPorts(conv_var.outport, task_var.response_inport)
                
        self.variable = tmp

    def select(self, imm):
        for var_name in reversed(self.variable):
            var_value = getattr(self, var_name)
            if var_value in imm:
                return var_value 


class Tasks_Cell(CoupledDEVS):
    def __init__(self, name="Tasks_Cell", task_num = 3, param = 12):
        CoupledDEVS.__init__(self, name)
        self.task_num = task_num

        self.inport = self.addInPort(name="Tasks_Cell_in")
        self.outport = self.addOutPort(name="Tasks_Cell_out")
        self.response_outport = self.addOutPort(name="Tasks_Cell_respose_out")
            
        self.variable_name = []
        for i in range(task_num):
            station_name = name + "_" + str(i)
            setattr(self,station_name,self.addSubModel(Station(name=station_name, working_time=[param,0,0,0])))
            self.variable_name.append(station_name)
        
        for i in range(len(self.variable_name)-1):
            cur_station = getattr(self,self.variable_name[i])
            nex_station = getattr(self,self.variable_name[i+1])

            if i == 0:
                self.connectPorts(self.inport,cur_station.inport)
                self.connectPorts(cur_station.outport, self.response_outport)

            self.connectPorts(cur_station.outport,nex_station.inport)
            self.connectPorts(nex_station.outport,cur_station.response_inport)
            last_station = nex_station
            
        self.connectPorts(last_station.outport, self.outport)
        
    def select(self, imm):
        for var_name in reversed(self.variable_name):
            var_value = getattr(self, var_name)
            if var_value in imm:
                return var_value

def is_odd(number): #홀수확인
    if number % 2 == 0:
        return False
    else:
        return True

def parrallel_generate_odd(number, include_one = False): #홀수 생성기
    odd = []
    loop = int(number / 2)
    for i in range(loop+1):
        tmp = 1 + i
        if include_one == False:
            if tmp == 1:
                continue
        odd.append(tmp*2)
        odd.append(tmp*2)
    return odd

class Parallel_Cell(CoupledDEVS):
    def __init__(self, name="Parallel_Cell", line_num = 2, task_num = 3, cycle_time = 6):
        CoupledDEVS.__init__(self, name)

        if line_num < 2:
            raise ValueError("2개 이상부터 Cell 제작 가능")

        self.seperator = self.addSubModel(Seperator(name="seperator",out_way=line_num))
        self.buffer = self.addSubModel(Buffer(name="buffer"))

        self.inport = self.addInPort(name="Parallel_Cell_in")
        self.outport = self.addOutPort(name="Parallel_Cell_out")
        self.response_inport = self.addInPort(name="Parallel_Cell_response_inport")

        self.connectPorts(self.inport, self.seperator.inport)
        self.connectPorts(self.response_inport, self.buffer.response_inport)
        self.connectPorts(self.buffer.outport, self.outport)
    
        tmp1 = ["seperator"]
        tmp2 = []
        tmp3 = []

        if is_odd(line_num):
            print("line : ", 0)
            length = 2

            conveyor_in_name = "line0_conveyor_in"
            setattr(self,conveyor_in_name,self.addSubModel(Conveyor(name=conveyor_in_name, length=length)))
            tmp1.append(conveyor_in_name)
            #print(f"{self.name} : {conveyor_in_name} : setting {length} m")

            task_name = "line0_task"
            setattr(self,task_name,self.addSubModel(Tasks_Cell(name=task_name, task_num=task_num, param=cycle_time)))
            tmp2.append(task_name)
            #print(f"{self.name} : {task_name} : setting {cycle_time} sec")

            conveyor_out_name = "line0_conveyor_out"
            setattr(self,conveyor_out_name,self.addSubModel(Conveyor(name=conveyor_out_name, length=length)))
            tmp3.append(conveyor_out_name)
            #print(f"{self.name} : {conveyor_out_name} : setting {length} m")

            print(f"{self.name} : conveyor_in : {length}m | task X {task_num} | conveyor_out : {length}m")

            conv_in = getattr(self, conveyor_in_name)
            task = getattr(self, task_name)   
            conv_out = getattr(self, conveyor_out_name)

            self.connectPorts(self.seperator.outport_0, conv_in.inport)
            self.connectPorts(conv_in.outport, self.seperator.response_inport_0)
            self.connectPorts(conv_in.outport, task.inport)
            self.connectPorts(task.response_outport, conv_in.response_inport)
            self.connectPorts(task.outport, conv_out.inport)
            self.connectPorts(conv_out.outport, self.buffer.inport)
        
        conv_lengths = parrallel_generate_odd(line_num)
        i=0
        for line in range(line_num):
            if is_odd(line_num):
                if line == 0:
                    continue
            print("line : ",line)
            
            conveyor_in_name = "line"+str(line)+"_conveyor_in"
            setattr(self,conveyor_in_name,self.addSubModel(Conveyor(name=conveyor_in_name, length=conv_lengths[i])))
            tmp1.append(conveyor_in_name)
            #print(f"{self.name} : {conveyor_in_name} : setting {conv_lengths[i]} m")
            
            task_name = "line"+str(line)+"_task"
            setattr(self,task_name,self.addSubModel(Tasks_Cell(name=task_name, task_num=task_num, param=cycle_time)))
            tmp2.append(task_name)
            #print(f"{self.name} : line{line}_station X {task_num} : setting {cycle_time} sec")

            conveyor_out_name = "line"+str(line)+"_conveyor_out"
            setattr(self,conveyor_out_name,self.addSubModel(Conveyor(name=conveyor_out_name, length=conv_lengths[i])))
            tmp3.append(conveyor_out_name)
            #print(f"{self.name} : {conveyor_out_name}: setting {conv_lengths[i]} m")

            print(f"{self.name} : conveyor_in : {conv_lengths[i]}m | task X {task_num} | conveyor_out : {conv_lengths[i]}m")

            conv_in = getattr(self, conveyor_in_name)
            task = getattr(self, task_name)   
            conv_out = getattr(self, conveyor_out_name)

            outport_num = "outport_"+str(line)
            seperator_outport = getattr(self.seperator, outport_num)
            self.connectPorts(seperator_outport, conv_in.inport)

            response_port_num = "response_inport_"+str(line)
            seperator_response_inport = getattr(self.seperator, response_port_num)
            self.connectPorts(conv_in.outport, seperator_response_inport)

            self.connectPorts(conv_in.outport, task.inport)
            self.connectPorts(task.response_outport, conv_in.response_inport)
            self.connectPorts(task.outport, conv_out.inport)
            self.connectPorts(conv_out.outport, self.buffer.inport)

            i += 1
        tmp3.append("buffer")

        self.variable = tmp1 + tmp2 + tmp3

    def select(self, imm):
        for var_name in reversed(self.variable):
            var_value = getattr(self, var_name)
            if var_value in imm:
                return var_value 


def block_generate_odd(number): #홀수 생성기
    odd = []
    for i in range(number):
        tmp = i+1
        odd.append(tmp*2)
    return odd


class Block_Cell(CoupledDEVS):
    def __init__(self, name="Block_Cell", line_num = 3 , task_num = 2, cycle_time = 1):
        CoupledDEVS.__init__(self, name)

        self.seperator = self.addSubModel(Seperator(name="seperator",out_way=(line_num)))
        self.buffer = self.addSubModel(Buffer(name="buffer"))
        self.inport = self.addInPort(name="Block_Cell_in")
        self.outport = self.addOutPort(name="Block_Cell_out")
        self.response_inport = self.addInPort(name="Block_Cell_response_inport")

        self.connectPorts(self.inport, self.seperator.inport)
        self.connectPorts(self.response_inport, self.buffer.response_inport)
        self.connectPorts(self.buffer.outport, self.outport)
        
        tmp1 = ["seperator"]
        tmp2 = []
        tmp3 = []
        
        conv_lengths = block_generate_odd(line_num)
        
        last = len(conv_lengths) - 1
        for line in range(line_num):
            print("line : ",line)
            conveyor_in_name = "line"+str(line)+"_conveyor_in"
            setattr(self,conveyor_in_name,self.addSubModel(Conveyor(name=conveyor_in_name, length=conv_lengths[line])))
            tmp1.append(conveyor_in_name)
            #print(f"{self.name} : {conveyor_in_name} : setting {conv_lengths[line]} m")
            
            task_name = "line"+str(line)+"_task"
            setattr(self,task_name,self.addSubModel(Tasks_Cell(name=task_name, task_num=task_num, param=cycle_time)))
            tmp2.append(task_name)
            #print(f"{self.name} : line{line}_station X {task_num} : setting {cycle_time} sec")

            conveyor_out_name = "line"+str(line)+"_conveyor_out"
            setattr(self,conveyor_out_name,self.addSubModel(Conveyor(name=conveyor_out_name, length=conv_lengths[last - line])))
            tmp3.append(conveyor_out_name)
            #print(f"{self.name} : {conveyor_out_name}: setting {conv_lengths[last - line]} m")

            print(f"{self.name} : conveyor_in : {conv_lengths[line]}m | task X {task_num} | conveyor_out : {conv_lengths[last - line]}m")

            conv_in = getattr(self, conveyor_in_name)
            task = getattr(self, task_name)   
            conv_out = getattr(self, conveyor_out_name)

            outport_num = "outport_"+str(line)
            seperator_outport = getattr(self.seperator, outport_num)
            self.connectPorts(seperator_outport, conv_in.inport)

            response_port_num = "response_inport_"+str(line)
            seperator_response_inport = getattr(self.seperator, response_port_num)
            self.connectPorts(conv_in.outport, seperator_response_inport)

            self.connectPorts(conv_in.outport, task.inport)
            self.connectPorts(task.response_outport, conv_in.response_inport)
            self.connectPorts(task.outport, conv_out.inport)
            self.connectPorts(conv_out.outport, self.buffer.inport)

        tmp3.append("buffer")

        self.variable = tmp1 + tmp2 + tmp3

    def select(self, imm):
        for var_name in reversed(self.variable):
            var_value = getattr(self, var_name)
            if var_value in imm:
                return var_value 
        
