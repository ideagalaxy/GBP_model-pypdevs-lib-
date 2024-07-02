### Experiment
from pypdevs.simulator import Simulator
from Linear_System import Storage, Station, Drain
from pypdevs.DEVS import *
        
class OptimalPath1(CoupledDEVS):
    def __init__(self, name="OptimalPath1"):
        CoupledDEVS.__init__(self, name)
        self.storage = self.addSubModel(Storage(name="storage"))        #outport, response_inport

        self.station_1 = self.addSubModel(Station(name="station_1"))    #outport, inport, response_inport
        self.station_2 = self.addSubModel(Station(name="station_2"))
        self.station_3 = self.addSubModel(Station(name="station_3"))
        self.station_4 = self.addSubModel(Station(name="station_4"))
        self.station_5 = self.addSubModel(Station(name="station_5"))
        self.station_6 = self.addSubModel(Station(name="station_6"))
        self.station_7 = self.addSubModel(Station(name="station_7"))
        self.station_8 = self.addSubModel(Station(name="station_8"))
        self.station_9 = self.addSubModel(Station(name="station_9"))
        self.station_10 = self.addSubModel(Station(name="station_10"))
        self.station_11 = self.addSubModel(Station(name="station_11"))

        self.turn_1 = self.addSubModel(Station(name="turn_1"))
        
        self.station_12 = self.addSubModel(Station(name="station_12"))
        self.station_13 = self.addSubModel(Station(name="station_13"))
        self.station_14 = self.addSubModel(Station(name="station_14"))

        self.result = self.addSubModel(Drain(name="result1"))            #inport,outport
        
        #connect outports >> inports
        self.connectPorts(self.storage.outport, self.station_1.inport)
        self.connectPorts(self.station_1.outport, self.station_2.inport)
        self.connectPorts(self.station_2.outport, self.station_3.inport)
        self.connectPorts(self.station_3.outport, self.station_4.inport)
        self.connectPorts(self.station_4.outport, self.station_5.inport)
        self.connectPorts(self.station_5.outport, self.station_6.inport)
        self.connectPorts(self.station_6.outport, self.station_7.inport)
        self.connectPorts(self.station_7.outport, self.station_8.inport)
        self.connectPorts(self.station_8.outport, self.station_9.inport)
        self.connectPorts(self.station_9.outport, self.station_10.inport)
        self.connectPorts(self.station_10.outport, self.station_11.inport)

        self.connectPorts(self.station_11.outport, self.turn_1.inport)

        self.connectPorts(self.turn_1.outport, self.station_12.inport)
        self.connectPorts(self.station_12.outport, self.station_13.inport)
        self.connectPorts(self.station_13.outport, self.station_14.inport)
        self.connectPorts(self.station_14.outport, self.result.inport)

        #connect outports >> response_inport
        self.connectPorts(self.result.outport, self.station_14.response_inport)
        self.connectPorts(self.station_14.outport, self.station_13.response_inport)
        self.connectPorts(self.station_13.outport, self.station_12.response_inport)
        self.connectPorts(self.station_12.outport, self.turn_1.response_inport)
        self.connectPorts(self.turn_1.outport, self.station_11.response_inport)
        self.connectPorts(self.station_11.outport, self.station_10.response_inport)
        self.connectPorts(self.station_10.outport, self.station_9.response_inport)
        self.connectPorts(self.station_9.outport, self.station_8.response_inport)
        self.connectPorts(self.station_8.outport, self.station_7.response_inport)
        self.connectPorts(self.station_7.outport, self.station_6.response_inport)
        self.connectPorts(self.station_6.outport, self.station_5.response_inport)
        self.connectPorts(self.station_5.outport, self.station_4.response_inport)
        self.connectPorts(self.station_4.outport, self.station_3.response_inport)
        self.connectPorts(self.station_3.outport, self.station_2.response_inport)
        self.connectPorts(self.station_2.outport, self.station_1.response_inport)
        self.connectPorts(self.station_1.outport, self.storage.response_inport)

    def select(self, imm):
        if self.result in imm:
            return self.result
        elif self.station_14 in imm:
            return self.station_14
        elif self.station_13 in imm:
            return self.station_13
        elif self.station_12 in imm:
            return self.station_12
        elif self.turn_1 in imm:
            return self.turn_1
        elif self.station_11 in imm:
            return self.station_11
        elif self.station_10 in imm:
            return self.station_10
        elif self.station_9 in imm:
            return self.station_9
        elif self.station_8 in imm:
            return self.station_8
        elif self.station_7 in imm:
            return self.station_7
        elif self.station_6 in imm:
            return self.station_6
        elif self.station_5 in imm:
            return self.station_5
        elif self.station_4 in imm:
            return self.station_4
        elif self.station_3 in imm:
            return self.station_3
        elif self.station_2 in imm:
            return self.station_2
        elif self.station_1 in imm:
            return self.station_1
        elif self.storage in imm:
            return self.storage


#setting
sim = Simulator(OptimalPath1("OptimalPath1"))

#sim.setVerbose()
sim.setTerminationTime(15552000)
sim.setClassicDEVS()

sim.simulate()


from Linear_System import result_dict



print "*** Finsish Simulator ***\n \
        Result = ", result_dict['result1']