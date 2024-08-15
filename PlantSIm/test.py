from pypdevs.simulator import Simulator
from MaterialFlow import Gen_LINE

inputData = {
    "name"  :["source","source_buffer", "station_1",    "conveyor_1",   "station_2",    "result"],
    "type"  :["Source", "Buffer",       "Station",      "Conveyor",     "Station",      "Drain"],
    "time"  :[2,        None,           2,              2,              10,             None]
}
'''
sim = Simulator(Gen_LINE("LinearLine",inputData=inputData))

#sim.setVerbose()
sim.setTerminationTime(200)
sim.setClassicDEVS()

sim.simulate()

print("-------------------------------")
print(sim.model.result.count)
'''


import itertools

model_dict = {
    "station_1" : 38.57,
    "station_2" : 34.44,
    "station_3" : 9.91,
    "station_4" : 33.48,
    "station_5" : 33.48,
    "station_6" : 10.84
}


arr = ["Station","Station","Station","Station","Conveyor"]
# 모든 순열을 구한 후, 중복을 제거
unique_permutations = set(itertools.permutations(arr))



best_comb = None
best_result = None
# 결과 출력
for perm in unique_permutations:



    inputData = {}
    name = ["source","source_buffer","station_1"]
    atomic = ["Source","Buffer","Station"]
    time = [2,None,model_dict["station_1"]]

    station_cnt = 1
    conveyor_cnt = 1
    for tp in perm:
        if tp == "Station":
            tmp_name = "station_" + str(station_cnt)
            station_cnt += 1
            name.append(tmp_name)
            atomic.append(tp)
            time.append(model_dict[tmp_name])
        
        elif tp == "Conveyor":
            
            tmp_name = "conveyor_" + str(conveyor_cnt)
            conveyor_cnt += 1
            name.append(tmp_name)
            atomic.append(tp)
            time.append(2)
    
    name.append("station_6")
    atomic.append("Station")
    time.append(model_dict["station_6"])

    name.append("result")
    atomic.append("Drain")
    time.append(None)

    inputData["name"] = name
    inputData["type"] = atomic
    inputData["time"] = time

    print(inputData)
    print("------------------------------------------")

    sim = Simulator(Gen_LINE("LinearLine",inputData=inputData))

    #sim.setVerbose()
    sim.setTerminationTime(21600)
    sim.setClassicDEVS()

    sim.simulate()

    print("-------------------------------")
    print(sim.model.result.count)

    if best_comb == None:
        best_comb = inputData
        best_result = sim.model.result.count
    else:
        if best_result < sim.model.result.count:
            best_result = sim.model.result.count
            best_comb = inputData

print(best_comb)
print(best_result)

