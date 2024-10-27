from pypdevs.DEVS import *
from MaterialFlow import *
from GenerateCell import *
from pypdevs.simulator import Simulator
import pandas as pd

class Data_preprocessing:
    def __init__(self):
        pass

    def getType(self,input):
        el_type = input['Type'].tolist()

        return el_type

    def getName(self,input):
        el_type = self.getType(input)
        el_name = []

        station_num = 1
        cell_num = 1
        
        for type in el_type:
            
            if "Cell" in type:
                _name = "Cell_" + str(cell_num)
                cell_num += 1
                el_name.append(_name)
            elif type == "Station":
                _name = "Station_" + str(station_num)
                station_num += 1
                el_name.append(_name)
            else:
                el_name.append(type)
        
        return el_name
    
    def getParam(self,input):
        el_type = self.getType(input)
        el_param = []

        return el_param




        




class Gen_LINE(CoupledDEVS):
    def __init__(self, name="Gen_LINE", inputData= {}):
        CoupledDEVS.__init__(self, name)
        self.variable_name = []
        self.variable_type = []
        for i in range(len(inputData["name"])):
            name = inputData["name"][i]
            type = inputData["type"][i]
            param = inputData["param"][i]
            if type == "Source":
                setattr(self,name,self.addSubModel(Source(name=name, interval=param)))
            
            elif type == "Buffer":
                if param == None:
                    setattr(self,name,self.addSubModel(Buffer(name=name)))
                else:
                    setattr(self,name,self.addSubModel(Buffer(name=name, capacity= param)))

            elif type == "Conveyor":
                setattr(self,name,self.addSubModel(Conveyor(name=name,length=param)))

            elif type == "Cell":
                setattr(self,name,self.addSubModel(Cell(name=name)))

            elif type == "Station":
                setattr(self,name,self.addSubModel(Station(name=name,working_time=param)))

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
                    print(now_type,"response")
                    self.connectPorts(val_response_outport, val_response_inport)

    def select(self, imm):
        for var_name in reversed(self.variable_name):
            var_value = getattr(self, var_name)
            if var_value in imm:
                return var_value