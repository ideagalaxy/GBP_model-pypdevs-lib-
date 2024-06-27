from pypdevs.DEVS import *
from pypdevs.infinity import INFINITY

class GMode:
    def __init__(self, current="block"):
        self.set(current)

    def set(self, value="block"):
        self.__state=value

    def get(self):
        return self.__state

    def __str__(self):
        return self.get()

class Generator(AtomicDEVS):
    #   Default state : block
    #   IntTransition : block -> generate (every 5 sec)
    #   outputFnc : "new_person"

    def __init__(self, name =None):
        AtomicDEVS.__init__(self, name)
        self.state = GMode("block")
        self.gen_outport = self.addOutPort("gen_outport")
    
    def timeAdvance(self):
        print "Enter G_timeAdvance"
        state = self.state.get()
        if state == 'block':
            return 5
        elif state == 'generate':
            return 0.0
        else:
            raise DEVSException(\
                "unknown state <%s> in Generator time advance transition function"\
                % state)
    
    def intTransition(self):
        print "Enter G_inTransition"
        state = self.state.get()
        
        if state == "block":
            print "G state : block -> generate"
            return self.state.set("generate")
        elif state == "generate":
            print "G state : block -> generate"
            return self.state.set("block")
        else:
            raise DEVSException(\
                "unknown state <%s> in Generator internal transition function"\
                % state)
    
    def outputFnc(self):
        print "Enter G_outputFnc"
        state = self.state.get()
        if state == "generate":
            return {self.gen_outport: "new_person"}
        else:
            return {self.gen_outport: "None"}

    

# Buffer
class Buffer_storage:
    # If Generator make object, data will store in this Array
    def __init__(self, current=[]):
        self.set(current)

    def set(self, value=[]):
        self.__drive=value

    def append(self, value="new_person"):
        self.__drive.append(value)
        return self.__drive
    
    def pop(self):
        self.__value = self.__drive.pop()
        return self.__value

    def get(self):
        return self.__drive

class BMode:
    def __init__(self, current="empty"):
        self.set(current)

    def set(self, value="empty"):
        self.__state=value

    def get(self):
        return self.__state
    
    def __str__(self):
        return self.get()

class Buffer(AtomicDEVS):
    #   Default state : empty
    #   ExtTransition from Generator : empty -> possible
    #   ExtTransition from Processor : possilbe -> pop
    #   InTransition : pop -> possible or empty

    def __init__(self, name =None):
        AtomicDEVS.__init__(self, name)
        self.buffer = Buffer_storage([])
        self.state = BMode("empty")
        self.elapsed = 0.0
        self.buffer_out = self.addOutPort("buffer_out")
        self.buffer_in = self.addInPort("buffer_in")
        self.state_in = self.addInPort("state_in")

    def timeAdvance(self):
        print "Enter B_timeAdvance"
        state = self.state.get()

        if state == 'empty':
            return INFINITY
        elif state == 'possible':
            return INFINITY
        elif state == 'pop':
            return 0.0
        else:
            raise DEVSException(\
                "unknown state <%s> in Buffer time advance transition function"\
                % state)
        
    def intTransition(self):
        print "Enter B_intTransition"
        state = self.state.get()
        buffer = self.buffer
        
        #After outputFnc
        if state == "pop":
            if len(buffer.get()) == 0:
                print "Buffer state : pop -> empty"
                return self.state.set("empty")
            else:
                print "Buffer state : pop -> possible"
                return self.state.set("possible")
            
        elif state == "empty":
            return self.state.set("empty")
        elif state == "possible":
            return self.state.set("possible")
        else:
            raise DEVSException(\
                "unknown state <%s> in Buffer internal transition function"\
                % state)
            
    def outputFnc(self):
        print "Enter B_outputFnc"
        state = self.state.get()
        buffer = self.buffer

        if state == "empty":
            return {self.buffer_out: "None"}
        
        elif state == "possible":
            return {self.buffer_out: "None"}
        
        elif state == "pop":
            out = buffer.pop()
            return {self.buffer_out: out}
        
        else:
            raise DEVSException(\
                "unknown state <%s> in Buffer outputFnc transition function"\
                % state)
        

    def extTransition(self, inputs):
        print "Enter B_extTransition"
        state = self.state.get()
        buffer = self.buffer

        try:
            buffer_in = inputs[self.buffer_in]
            print "port[buffer_in] input : ", buffer_in
            if buffer_in != "None":
                buffer.append(buffer_in)
                if state == 'empty':
                    print "Buffer state : empty -> possible"
                    return self.state.set("possible")
                else:
                    return self.state.set(state)
            else:
                return self.state.set(state)
            
        except:
            print "port[state_in] Event!!"


        try:
            state_in = inputs[self.state_in]
            print "port[state_in] input : ", state_in

            if state == 'possible':
                state_in = inputs[self.state_in]
                if state_in == 'ready':
                    print "Buffer state : possible -> pop"
                    return self.state.set("pop")
                else:
                    return self.state.set(state)
            else:
                return self.state.set(state)
            
        except:
            print "port[buffer_in] Event!!"
            
class PMode:
    def __init__(self, current="ready"):
        self.set(current)

    def set(self, value="ready"):
        self.__state=value

    def get(self):
        return self.__state

    def __str__(self):
        return self.get()

class Processor(AtomicDEVS):
    #   Default state : ready
    #   ExtTransition : ready -> busy
    #   IntTransition : (after 11 sec) busy -> ready
    #   If state = ready : outputFnc work every 1sec (>> Buffer check Processor outport)
     
    def __init__(self, name =None):
        AtomicDEVS.__init__(self, name)
        self.proc_in = self.addInPort("proc_in")
        self.proc_out = self.addOutPort("proc_out")
        self.state = PMode("ready")
    
    def timeAdvance(self):
        print "Enter P_timeAdvance"
        state = self.state.get()
        if state == "busy":
            return 12
        if state == "ready": 
            return 1

    def intTransition(self):
        print "Enter P_intTransition"
        state = self.state.get()
        if state == "busy":
            print "processor state : busy -> ready"
            return self.state.set("ready")
        else:
            return self.state.set("ready")
        
    def extTransition(self, inputs):
        print "Enter P_extTransition"
        proc_in =inputs[self.proc_in]
        print "port[porc_in] input : ", proc_in
        state = self.state.get()
      
        if proc_in != "None":
            if state == 'ready':
                print "processor state : ready -> busy"
                return self.state.set("busy")
            else:
                return self.state.set(state)
        else:
            return self.state.set(state)

    def outputFnc(self):
        print "Enter P_outputFnc"
        state = self.state.get()

        if state == "ready":
            print "Processor outputFnc : ", state
            return {self.proc_out: "ready"}
        elif state == "busy":
            print "Processor outputFnc : ", state
            return {self.proc_out: "busy"}



class B_Pmodel(CoupledDEVS):
    def __init__(self, name=None):
        CoupledDEVS.__init__(self, name)
        print "Enter B_Pmodel"
        self.processor = self.addSubModel(Processor(name="Processor"))
        self.buffer = self.addSubModel(Buffer(name="Buffer"))

        self.bp_model_in = self.addInPort(name="bp_model_in")
        self.connectPorts(self.bp_model_in, self.buffer.buffer_in)
        print "succes to connect [bp_model_in] -> [buffer_in]"
        self.connectPorts(self.buffer.buffer_out, self.processor.proc_in)
        print "succes to connect [buffer_out] -> [proc_in]"
        self.connectPorts(self.processor.proc_out, self.buffer.state_in)
        print "succes to connect [proc_out] -> [state_in]"
        
    #IDK what it is
    def select(self, imm):
        if self.processor in imm:
            return self.processor
        elif self.buffer in imm:
            return self.buffer

class G_BPmodel(CoupledDEVS):
    def __init__(self, name=None):
        CoupledDEVS.__init__(self, name)
        print "Enter G_BPmodel"
        self.generator = self.addSubModel(Generator(name="Generator"))
        self.b_pmodel = self.addSubModel(B_Pmodel(name="B_Pmodel"))

        self.connectPorts(self.generator.gen_outport, self.b_pmodel.bp_model_in)
        print "succes to connect [gen_outport] -> [bp_model_in]"

    def select(self, imm):
        if self.generator in imm:
            return self.generator
        elif self.b_pmodel in imm:
            return self.b_pmodel

