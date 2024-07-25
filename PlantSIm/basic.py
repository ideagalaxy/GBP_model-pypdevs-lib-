class State_str:
    def __init__(self, current="State_str"):
        self.set(current)

    def set(self, value):
        self.__state=value
        return self.__state

    def get(self):
        return self.__state
    
    def __str__(self):
        return self.get()
    
class State_arr:
    def __init__(self, current=["State_arr"]):
        self.set(current)

    def set(self, value_list):
        self.__state = value_list
        return self.__state

    def get(self):
        return self.__state
    
    def __str__(self):
        data = self.get()
        for i in range(len(data)):
            if i == 0:
                text = data[0]
            else:
                text = text + ", " + data[i]
        return text