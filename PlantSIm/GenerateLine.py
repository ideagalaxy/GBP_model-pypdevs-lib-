from pypdevs.DEVS import *
from MaterialFlow import *
from GenerateCell import *
from pypdevs.simulator import Simulator
import pandas as pd

class DEVS:
    def __init__(self,sourceAmount = -1, interval = 2, default_length = 2, default_speed = 1):
        #Source Setting
        self.source_amount = sourceAmount
        self.source_interval = interval

        #Conveyor Setting
        self.default_length = default_length
        self.default_speed = default_speed

    def getType(self,input):
        el_type = input['Type'].tolist()
        return el_type
    
    def getName(self,typeList):
        el_type = typeList
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
    
    def preprocessing(self,input):
        el_type = []
        el_param = []

        #About Source
        el_type.append("Source")
        el_param.append({"amount" : self.source_amount,
                         "interval" : self.source_interval})
        
        length = 1
        for index, row in input.iterrows():
            type = row["Type"]
            tmp = {}
            if type == "Station":
                el_type.append(type)
                
                tmp["working_time"] = [row["cycletime"],0,0,0]
                el_param.append(tmp)

            elif type == "Conveyor":

                if self.getType(input)[index+1] == "Conveyor":
                    length += 1

                else:
                    el_type.append(type) 
                    tmp["length"] = length * self.default_length
                    tmp["speed"]  = self.default_speed 
                    el_param.append(tmp)

                    length = 1

            elif type == "Block Cell" or type == "Parallel Cell":
                el_type.append(type) 
                tmp["line_num"]   = row["line_num"]
                tmp["task_num"]   = row["task_num"]
                tmp["cycle_time"] = row["cycletime"]
                el_param.append(tmp)
        
        #About Drain
        el_type.append("Drain")
        el_param.append(None)

        el_name = self.getName(el_type)

        inputData = {
            "name" : el_name,
            "type" : el_type,
            "param": el_param
        }
        return inputData
    
    def getModel(self,input):
        inputData = self.preprocessing(input)
        model = Gen_LINE(inputData=inputData)
        return model

    def simulate(self, model, settime = 100, setVerbose = True):
        sim = Simulator(model)
        if setVerbose == True:
            sim.setVerbose()
        sim.setTerminationTime(settime)
        sim.setClassicDEVS()

        sim.simulate()


class Gen_LINE(CoupledDEVS):
    def __init__(self, name="Gen_LINE", inputData= {}):
        CoupledDEVS.__init__(self, name)
        self.variable_name = []
        self.variable_type = []
        for i in range(len(inputData["type"])):
            name    = inputData["name"][i]
            type    = inputData["type"][i]
            param   = inputData["param"][i]
            print(name,type,param)
            if type == "Source":
                setattr(self,name,self.addSubModel(Source(name=name,amount=param["amount"], interval=param["interval"])))
            
            elif type == "Buffer":
                setattr(self,name,self.addSubModel(Buffer(name=name, capacity=param["capacity"])))

            elif type == "Conveyor":
                setattr(self,name,self.addSubModel(Conveyor(name=name,length=param["length"],speed=param["speed"])))

            elif type == "Block Cell":
                setattr(self,name,self.addSubModel(Block_Cell(name=name, line_num=param["line_num"], task_num = param["task_num"], cycle_time=param["cycle_time"])))
            
            elif type == "Parallel Cell":
                setattr(self,name,self.addSubModel(Parallel_Cell(name=name, line_num=param["line_num"], task_num = param["task_num"], cycle_time=param["cycle_time"])))

            elif type == "Station":
                setattr(self,name,self.addSubModel(Station(name=name,working_time=param["working_time"])))

            elif type == "Drain":
                setattr(self,name,self.addSubModel(Drain(name=name)))
            self.variable_name.append(name)
            self.variable_type.append(type)

        for i in range(len(self.variable_name)-1):
            val_now = getattr(self, self.variable_name[i])
            val_next = getattr(self, self.variable_name[i+1])

            val_outport = val_now.outport
            val_inport = val_next.inport
            self.connectPorts(val_outport,val_inport)

            now_type = self.variable_type[i]
            next_type = self.variable_type[i+1]

            if now_type == "Source" or now_type == "Drain":
                continue
            val_response_outport = val_next.outport
            val_response_inport = val_now.response_inport
            self.connectPorts(val_response_outport, val_response_inport)

    def select(self, imm):
        for var_name in reversed(self.variable_name):
            var_value = getattr(self, var_name)
            if var_value in imm:
                return var_value