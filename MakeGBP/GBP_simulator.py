### Experiment
from pypdevs.simulator import Simulator
from GBP_System import G_BPmodel

#setting
sim = Simulator(G_BPmodel("G_BPmodel"))

sim.setVerbose()
sim.setTerminationTime(600)
sim.setClassicDEVS()

sim.simulate()