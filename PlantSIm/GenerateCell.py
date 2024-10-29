from pypdevs.DEVS import *
from pypdevs.infinity import INFINITY
import random


from MUs import *
from MaterialFlow import Source, Conveyor, Buffer, Drain, Station, Seperator


class Tasks_Cell(CoupledDEVS):
    def __init__(self, name="Tasks_Cell", task_num = 3, param = 12):
        CoupledDEVS.__init__(self, name)
        self.task_num = task_num

        self.inport = self.addInPort(name="Tasks_Cell_in")
        self.outport = self.addOutPort(name="Tasks_Cell_out")
        self.response_outport = self.addOutPort(name="Tasks_Cell_respose_out")

        self.variable_name = []
        for i in range(task_num):
            station_name = name + "_station_" + str(i+1)
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

class Parallel_Cell(CoupledDEVS):
    def __init__(self, name="Parallel_Cell", conveyor_length = [6,6], task_num = 3, cycle_time = 6):
        CoupledDEVS.__init__(self, name)

        self.seperator = self.addSubModel(Seperator(name="seperator",out_way=len(conveyor_length)))
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

        line = 1
        for length in conveyor_length:
            conveyor_in_name = "line"+str(line)+"_conveyor_in"
            setattr(self,conveyor_in_name,self.addSubModel(Conveyor(name=conveyor_in_name, length=conveyor_length[line-1])))
            tmp1.append(conveyor_in_name)
            
            task_name = "line"+str(line)+"_station"
            setattr(self,task_name,self.addSubModel(Tasks_Cell(name=task_name, task_num=task_num, param=cycle_time)))
            tmp2.append(task_name)

            conveyor_out_name = "line"+str(line)+"_conveyor_out"
            setattr(self,conveyor_out_name,self.addSubModel(Conveyor(name=conveyor_in_name, length=conveyor_length[line-1])))
            tmp3.append(conveyor_out_name)

            conv_in = getattr(self, conveyor_in_name)
            task = getattr(self, task_name)   
            conv_out = getattr(self, conveyor_out_name)

            self.connectPorts(self.seperator.outport, conv_in.inport)
            self.connectPorts(conv_in.outport, task.inport)
            self.connectPorts(task.response_outport, conv_in.response_inport)
            self.connectPorts(task.outport, conv_out.inport)
            self.connectPorts(conv_out.outport, self.buffer.inport)

            line += 1
        
        tmp3.append("buffer")

        self.variable = tmp1 + tmp2 + tmp3

    def select(self, imm):
        for var_name in reversed(self.variable):
            var_value = getattr(self, var_name)
            if var_value in imm:
                return var_value 


class Block_Cell(CoupledDEVS):
    def __init__(self, name="Block_Cell", conveyor_length = [2,6], task_num = 2, cycle_time = 1):
        CoupledDEVS.__init__(self, name)

        self.seperator = self.addSubModel(Seperator(name="seperator",out_way=len(conveyor_length)))
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
        line = 1
        for length in conveyor_length:
            conveyor_in_name = "line"+str(line)+"_conveyor_in"
            setattr(self,conveyor_in_name,self.addSubModel(Conveyor(name=conveyor_in_name, length=conveyor_length[line-1])))
            tmp1.append(conveyor_in_name)

            task_name = "line"+str(line)+"_station"
            setattr(self,task_name,self.addSubModel(Tasks_Cell(name=task_name, task_num=task_num, param=cycle_time)))
            tmp2.append(task_name)
            
            conveyor_out_name = "line"+str(line)+"_conveyor_out"
            setattr(self,conveyor_out_name,self.addSubModel(Conveyor(name=conveyor_out_name, length=conveyor_length[len(conveyor_length) - (line-1)])))
            tmp3.append(conveyor_out_name)

            conv_in = getattr(self, conveyor_in_name)
            task = getattr(self, task_name)   
            conv_out = getattr(self, conveyor_out_name)

            self.connectPorts(self.seperator.outport, conv_in.inport)
            self.connectPorts(conv_in.outport, task.inport)
            self.connectPorts(task.response_outport, conv_in.response_inport)
            self.connectPorts(task.outport, conv_out.inport)
            self.connectPorts(conv_out.outport, self.buffer.inport)

            line += 1

        tmp3.append("buffer")

        self.variable = tmp1 + tmp2 + tmp3

    def select(self, imm):
        for var_name in reversed(self.variable):
            var_value = getattr(self, var_name)
            if var_value in imm:
                return var_value

'''

class Cell(CoupledDEVS):
    def __init__(self, name="cell"):
        CoupledDEVS.__init__(self, name)

        self.seperator = self.addSubModel(Seperator(name="seperator",out_way=3))

        self.line0 = self.addSubModel(Tasks_Cell(name="line0", param=4))
        self.line1 = self.addSubModel(Tasks_Cell(name="line1", param=4))
        self.line2 = self.addSubModel(Tasks_Cell(name="line2", param=4))

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
            
'''