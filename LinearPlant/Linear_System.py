from pypdevs.DEVS import *
from pypdevs.infinity import INFINITY
from pypdevs.simulator import Simulator
import pypdevs.accurate_time as time
import random



source_inventory = {
    'main_source' : INFINITY
}

data = {
    #proc    working time  
    'station_1':     [3],
    'station_2':     [3],
    'station_3':     [3],
    'station_4':     [3],
    'station_5':     [3],
    'station_6':     [3],
    'station_7':     [3],
    'station_8':     [3],
    'station_9':     [3],
    'station_10':    [3],
    'station_11':    [3],
    'station_12':    [3],
    'station_13':    [3],
    'station_14':    [3],
    'turn_1':          [10],
    'turn_2':          [10],
    'turn_3':          [10],
    'turn_4':          [10],
    'turn_5':          [10],
    'turn_6':          [10],
    'turn_7':          [10],
    'turn_8':          [10],
    'turn_9':          [10],
    'turn_10':          [10],
    'turn_11':          [10],

}

class State:
    def __init__(self, current="ready"):
        self.set(current)

    def set(self, value):
        self.__state=value
        return self.__state

    def get(self):
        return self.__state
    
    def __str__(self):
        return self.get()
    
class Storage(AtomicDEVS):
    def __init__(self, name = 'storage'):
        AtomicDEVS.__init__(self, name)
        self.name = name
        self.state = State("pop")
        outport_name = name + '_outport'
        self.outport = self.addOutPort(outport_name)
        response_inport_name = name + '_response_inport'
        self.response_inport = self.addInPort(response_inport_name)

    def timeAdvance(self):
        state = self.state.get()

        if state == "load":
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
            self.state = State("load")
            return self.state
        else:
            raise DEVSException(\
                "unknown state <%s> in <%s> internal transition function"\
                % (state, self.name))

    def extTransition(self, inputs):
        state = self.state.get()
        response_port_in =inputs[self.response_inport]

        if response_port_in == "pop":
            if state == "load":
                self.state = State("pop")
                return self.state
            else:
                return self.state
        else:
            return self.state
            
    def outputFnc(self):
        state = self.state.get()

        if state == "pop":
            return {self.outport: "pop"}
        else:
            return {self.outport: "load"}
    
class Source(AtomicDEVS):
    '''
        state : load / pop / end
    '''
    def __init__(self, name = 'source'):
        AtomicDEVS.__init__(self, name)
        self.count = 0
        self.name = name
        self.state = State("pop")
        outport_name = name + '_outport'
        self.outport = self.addOutPort(outport_name)

        #init section
        if name in source_inventory:
            self.inventory = source_inventory[name]

    def timeAdvance(self):
        state = self.state.get()
        if state == "load":
            return 1.0
        elif state == "pop":
            return 0.0
        elif state == "end":
            return INFINITY
        else:
            raise DEVSException(\
                "unknown state <%s> in <%s> time advance transition function"\
                % (state, self.name))
        
    def intTransition(self):
        state = self.state.get()

        if state == "load":
            if self.inventory == INFINITY:
                self.state = State("pop")
                return self.state
            
            else:
                if self.inventory > 0:
                    self.inventory = self.inventory - 1
                    self.state = State("pop")
                    return self.state
                else:
                    self.state = State("end")
                    return self.state
                
        elif state == "pop":
            self.count += 1
            self.state = State("load")
            return self.state
        
        else:
            raise DEVSException(\
                "unknown state <%s> in <%s> internal transition function"\
                % (state, self.name))
    
    def outputFnc(self):
        state = self.state.get()

        if state == "pop":
            return {self.outport: "pop"}
        else:
            return {self.outport: state}
        
class Buffer(AtomicDEVS):
    def __init__(self, name = 'buffer'):
        AtomicDEVS.__init__(self, name)
        self.name = name
        self.inventory = 0
        self.state = State("empty")
        outport_name = name + '_outport'
        self.outport = self.addOutPort(outport_name)
        inport_name = name + '_inport'
        self.inport = self.addInPort(inport_name)
        response_inport_name = name + '_response_inport'
        self.response_inport = self.addInPort(response_inport_name)

        self.do_pop = True

    def timeAdvance(self):
        state = self.state.get()

        if state == "empty":
            return INFINITY
        elif state == "ready":
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
            if self.inventory == 0:
                self.state = State("empty")
                return self.state
            else:
                self.state = State("ready")
                return self.state
        else:
            raise DEVSException(\
                "unknown state <%s> in <%s> internal transition function"\
                % (state, self.name))

    def extTransition(self, inputs):
        state = self.state.get()
        print(type(inputs))
        try:    
            port_in =inputs[self.inport]
        except:
            port_in = None
        try:
            response_port_in =inputs[self.response_inport]
        except:
            response_port_in = None
        
        # inport
        if port_in != None:

            if port_in == "pop":
                self.inventory = self.inventory + 1
                if self.do_pop == False:
                    self.state = State("ready")
                    return self.state
                else:
                    self.do_pop = False
                    self.inventory = self.inventory - 1
                    self.state = State("pop")
                    return self.state
            else:
                return self.state
            
        if response_port_in != None:
            
            if response_port_in == "pop":
                self.do_pop = True
                if state == "empty":
                    return self.state
                else:
                    self.do_pop = False
                    self.inventory = self.inventory - 1
                    self.state = State("pop")
                    return self.state
            else:
                return self.state
            
    def outputFnc(self):
        state = self.state.get()

        if state == "pop":
            return {self.outport: "pop"}
        
class Station(AtomicDEVS):
    def __init__(self, name = 'station'):
        AtomicDEVS.__init__(self, name)
        self.name = name
        self.state = State("ready")
        outport_name = name + '_outport'
        self.outport = self.addOutPort(outport_name)
        inport_name = name + '_inport'
        self.inport = self.addInPort(inport_name)
        response_inport_name = name + '_response_inport'
        self.response_inport = self.addInPort(response_inport_name)
        
        self.state_memo = State("ready")
        self.elapsed = 0.0

        self.weird = False

        self.do_pop = True
        self.working_time = 11
        #init section
        if name in data:
            init = data[name]
            self.working_time = init[0]


    def timeAdvance(self):
        try:
            state = self.state.get()
        except:
            self.state = self.state_memo
            state = self.state.get()

        if state == "ready":
            return INFINITY
        elif state == "working":
            if self.weird == True:
                working_time = self.working_time - self.elapsed
                self.weird = False
            else:
                working_time = self.working_time
            return working_time
        
        elif state == "pop":
            self.weird = False
            return 0.0
        elif state == "waiting":
            self.weird = False
            return INFINITY
        else:
            raise DEVSException(\
                "unknown state <%s> in <%s> time advance transition function"\
                % (state, self.name))
    
    def intTransition(self):
        try:
            state = self.state.get()
        except:
            self.state = self.state_memo
            state = self.state.get()

        if state == "working":
            if self.do_pop == False:
                self.state = State("waiting")
                self.state_memo = State("waiting")
                return self.state
            else:
                self.do_pop = False
                self.state = State("pop")
                self.state_memo = State("pop")
                return self.state
            
        elif state == "pop":
            self.state = State("ready")
            self.state_memo = State("ready")
            return self.state
        elif state == "ready":
            self.state = State("ready")
            self.state_memo = State("ready")
            return self.state
        elif state == "waiting":
            self.state = State("waiting")
            self.state_memo = State("waiting")
            return self.state
        else:
            raise DEVSException(\
                "unknown state <%s> in <%s> internal transition function"\
                % (state, self.name))
        
    def extTransition(self, inputs):
        print(type(inputs))
        try:
            state = self.state.get()
        except:
            self.state = self.state_memo
            state = self.state.get()

        try:    
            port_in =inputs[self.inport]
        except:
            port_in = None
        try:
            response_port_in =inputs[self.response_inport]
        except:
            response_port_in = None

        

        if port_in != None:
            if port_in == "pop":
                if state == "ready":
                    self.check_point = True
                    self.state = State("working")
                    self.state_memo = State("working")
                    self.timeAdvance()
                    return self.state
            
        if response_port_in != None:
            if response_port_in == "pop" or response_port_in[0] == "T":
                self.do_pop = True
                if state == "waiting":
                    self.do_pop = False
                    self.state = State("pop")
                    self.state_memo = State("pop")
                    return self.state
                
        self.weird = True
                 
        
    def outputFnc(self):
        try:
            state = self.state.get()
        except:
            self.state = self.state_memo
            state = self.state.get()

        if state == "working":
            return {self.outport: "waiting"}
        if state == "pop":
            return {self.outport: "pop"}
        
RESULT = 0

result_dict = {
    "result1" : 0,
    "result2" : 0,
    "result3" : 0
}

class Drain(AtomicDEVS):
    def __init__(self, name = 'drain'):
        AtomicDEVS.__init__(self, name)
        self.elapsed = 0.0
        self.name = name
        self.state = State("ready")
        outport_name = name + '_outport'
        self.outport = self.addOutPort(outport_name)
        inport_name = name + '_inport'
        self.inport = self.addInPort(inport_name)

        self.count = 0

    def timeAdvance(self):
        state = self.state.get()

        if state == "ready":
            return INFINITY
        elif state == "get":
            return 0.0
        else:
            raise DEVSException(\
                "unknown state <%s> in <%s> time advance transition function"\
                % (state, self.name))
        
    def extTransition(self, inputs):
        port_in =inputs[self.inport]
        state = self.state.get()

        if port_in == "pop":
            self.count = self.count + 1
            self.state = State("get")
            return self.state
        else:
            return self.state
        
    def intTransition(self):
        state = self.state.get()

        if state == "get":
            self.state = State("ready")
            return self.state
        else:
            raise DEVSException(\
                "unknown state <%s> in <%s> internal transition function"\
                % (state, self.name))
    
    def outputFnc(self):
        state = self.state.get()

        if state == "get":
            text = "Total : %s" % (self.count)
            print(text)
            result_dict[self.name] = self.count
            return {self.outport: text}

        
'''
class Storage(CoupledDEVS):
    def __init__(self, name="main_storage"):
        CoupledDEVS.__init__(self, name)
        self.main_source = self.addSubModel(Source(name="main_source"))
        self.main_buffer = self.addSubModel(Buffer(name="main_buffer"))

        self.outport = self.addOutPort(name="Storage_outport")
        self.response_inport = self.addInPort(name="Storage_buffer_inport")

        #inside connect
        self.connectPorts(self.main_source.outport, self.main_buffer.inport)

        #outside connect
        self.connectPorts(self.main_buffer.outport, self.outport)
        self.connectPorts(self.response_inport, self.main_buffer.response_inport)

    def select(self, imm):
        if self.main_buffer in imm:
            return self.main_buffer
        else:
            return self.main_source
'''
class LinearLine(CoupledDEVS):
    def __init__(self, name="LinearLine"):
        CoupledDEVS.__init__(self, name)
        self.storage = self.addSubModel(Storage(name="storage"))        #outport, response_inport

        self.station_1 = self.addSubModel(Station(name="station_1"))    #outport, inport, response_inport
        self.station_2 = self.addSubModel(Station(name="turn_1"))
        self.station_3 = self.addSubModel(Station(name="station_3"))

        self.result = self.addSubModel(Drain(name="result"))            #inport,outport
        
        #connect outports >> inports
        self.connectPorts(self.storage.outport, self.station_1.inport)
        self.connectPorts(self.station_1.outport, self.station_2.inport)
        self.connectPorts(self.station_2.outport, self.station_3.inport)
        self.connectPorts(self.station_3.outport, self.result.inport)

        #connect outports >> response_inport
        self.connectPorts(self.result.outport, self.station_3.response_inport)
        self.connectPorts(self.station_3.outport, self.station_2.response_inport)
        self.connectPorts(self.station_2.outport, self.station_1.response_inport)
        self.connectPorts(self.station_1.outport, self.storage.response_inport)

    def select(self, imm):
        if self.result in imm:
            return self.result
        elif self.station_3 in imm:
            return self.station_3
        elif self.station_2 in imm:
            return self.station_2
        elif self.station_1 in imm:
            return self.station_1
        elif self.storage in imm:
            return self.storage


