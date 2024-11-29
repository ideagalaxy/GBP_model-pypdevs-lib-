from pypdevs.DEVS import *
from pypdevs.infinity import INFINITY


from MUs import *
from MaterialFlow import Source, Conveyor, Buffer, Drain, Station, Seperator




class Two_sided_Wingbody_Cell(CoupledDEVS):
    def __init__(self, name="Parallel_Cell", line_num = 2, task_num = 3, cycle_time = 6):
        CoupledDEVS.__init__(self, name)

        if line_num < 2:
            raise ValueError("2개 이상부터 Cell 제작 가능")

        self.seperator = self.addSubModel(Seperator(name="seperator",out_way=line_num))
        self.buffer = self.addSubModel(Buffer(name="buffer"))

        self.inport = self.addInPort(name="Two_sided_Wingbody_Cell_in")
        self.outport = self.addOutPort(name="Two_sided_Wingbody_Cell_out")
        self.response_inport = self.addInPort(name="Two_sided_Wingbody_Cell_response_inport")

        self.connectPorts(self.inport, self.seperator.inport)
        self.connectPorts(self.response_inport, self.buffer.response_inport)
        self.connectPorts(self.buffer.outport, self.outport)
    
        tmp1 = ["seperator"]
        tmp2 = []
        tmp3 = []
        
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
            setattr(self,task_name,self.addSubModel(Station(name=task_name, working_time=cycle_time)))
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
        
