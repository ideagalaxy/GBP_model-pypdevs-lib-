from pypdevs.DEVS import *
from pypdevs.infinity import INFINITY
import random


from MUs import *
from MaterialFlow import Source, Conveyor, Buffer, Drain, Station, Seperator


class Tasks_Cell(CoupledDEVS):
    def __init__(self, name="Tasks_Cell", task_num = 3):
        CoupledDEVS.__init__(self, name)
        self.task_num = task_num

        self.inport = self.addInPort(name="Tasks_Cell_in")
        self.outport = self.addOutPort(name="Tasks_Cell_out")

        for i in range(task_num):
            station_name = name + "_station_" + str(i+1)
            setattr(self,name,self.addSubModel(Station(name=station_name, interval=param)))






class Parallel_Cell(CoupledDEVS):
    def __init__(self, name="Parallel_Cell", line_num = 2, task_num = 3, cycle_time = 4):
        CoupledDEVS.__init__(self, name)


class Block_Cell(CoupledDEVS):
    def __init__(self, name="Block_Cell", line_num = 2, task_num = 3, cycle_time = 4):
        CoupledDEVS.__init__(self, name)




class Create_subLine(CoupledDEVS):
    def sub():
        return Create_subLine()

class Gen_Cell():
    def gen_cell(inputData = {}):
        size = inputData["size"]
        sublines = inputData["sublines"]
        inport = inputData["inport"]
        outport = inputData["outport"]



class Line_in_Cell(CoupledDEVS):
    def __init__(self, name="LinC"):
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