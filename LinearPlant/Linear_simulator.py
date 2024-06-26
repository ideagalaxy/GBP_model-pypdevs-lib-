### Experiment
from pypdevs.simulator import Simulator
from Linear_System import LinearLine

#setting
sim = Simulator(LinearLine("LinearLine"))

sim.setVerbose()
sim.setTerminationTime(600)
sim.setClassicDEVS()

sim.simulate()