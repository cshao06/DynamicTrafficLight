#!/usr/bin/env python

"""
Tutorial for traffic light control via the TraCI interface.
This scenario models a pedestrian crossing which switches on demand.
"""
from __future__ import absolute_import
from __future__ import print_function

import os
import sys
import optparse
import subprocess


# the directory in which this script resides
THISDIR = os.path.dirname(__file__)


# we need to import python modules from the $SUMO_HOME/tools directory
# If the the environment variable SUMO_HOME is not set, try to locate the python
# modules relative to this script
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")

import traci  # noqa
from sumolib import checkBinary  # noqa
import randomTrips  # noqa

# minimum green time for the vehicles
MIN_GREEN_TIME = 15
# the first phase in tls plan. see 'pedcrossing.tll.xml'
VEHICLE_GREEN_PHASE = 0
PEDESTRIAN_GREEN_PHASE = 2
# the id of the traffic light (there is only one). This is identical to the
# id of the controlled intersection (by default)
TLSID = 'C'

# pedestrian edges at the controlled intersection
WALKINGAREAS = [':C_w0', ':C_w1']
CROSSINGS = [':C_c0']


# def run():
#     """execute the TraCI control loop"""
#     # track the duration for which the green phase of the vehicles has been
#     # active
#     greenTimeSoFar = 0

#     # whether the pedestrian button has been pressed
#     activeRequest = False

#     # main loop. do something every simulation step until no more vehicles are
#     # loaded or running
#     while traci.simulation.getMinExpectedNumber() > 0:
#         traci.simulationStep()

#         # decide wether there is a waiting pedestrian and switch if the green
#         # phase for the vehicles exceeds its minimum duration
#         if not activeRequest:
#             activeRequest = checkWaitingPersons()
#         if traci.trafficlight.getPhase(TLSID) == VEHICLE_GREEN_PHASE:
#             greenTimeSoFar += 1
#             if greenTimeSoFar > MIN_GREEN_TIME:
#                 # check whether someone has pushed the button

#                 if activeRequest:
#                     # switch to the next phase
#                     traci.trafficlight.setPhase(
#                         TLSID, VEHICLE_GREEN_PHASE + 1)
#                     # reset state
#                     activeRequest = False
#                     greenTimeSoFar = 0

#     sys.stdout.flush()
#     traci.close()

def run():
    """execute the TraCI control loop"""
    step = 0
    # we start with phase 2 where EW has green
    traci.trafficlight.setPhase("0", 2)
    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
        if traci.trafficlight.getPhase("0") == 2:
            # we are not already switching
            # if traci.inductionloop.getLastStepVehicleNumber("0") > 0:
            if traci.lanearea.getLastStepVehicleNumber("TLS0_my_program_E2CollectorOn_2i_0") > 0:
                # there is a vehicle from the north, switch
                traci.trafficlight.setPhase("0", 3)
            else:
                # otherwise try to keep green for EW
                traci.trafficlight.setPhase("0", 2)
        step += 1
    traci.close()
    sys.stdout.flush()



def checkWaitingPersons():
    """check whether a person has requested to cross the street"""

    # check both sides of the crossing
    for edge in WALKINGAREAS:
        peds = traci.edge.getLastStepPersonIDs(edge)
        # check who is waiting at the crossing
        # we assume that pedestrians push the button upon
        # standing still for 1s
        for ped in peds:
            if (traci.person.getWaitingTime(ped) == 1 and
                    traci.person.getNextEdge(ped) in CROSSINGS):
                # numWaiting = traci.trafficlight.getServedPersonCount(TLSID, PEDESTRIAN_GREEN_PHASE)
                # print("%s: pedestrian %s pushes the button (waiting: %s)" %
                #       (traci.simulation.getTime(), ped, numWaiting))
                print("%s pushes the button" % ped)
                return True
    return False


def get_options():
    """define options for this script and interpret the command line"""
    optParser = optparse.OptionParser()
    optParser.add_option("--nogui", action="store_true",
                         default=False, help="run the commandline version of sumo")
    options, args = optParser.parse_args()
    return options


# this is the main entry point of this script
if __name__ == "__main__":
    # load whether to run with or without GUI
    options = get_options()

    # this script has been called from the command line. It will start sumo as a
    # server, then connect and run
    if options.nogui:
        sumoBinary = checkBinary('sumo')
    else:
        sumoBinary = checkBinary('sumo-gui')

    net = 'std_crossroad.net.xml'
    # build the multi-modal network from plain xml inputs
    # subprocess.call([checkBinary('netconvert'),
    #                  '-c', os.path.join('data', 'pedcrossing.netccfg'),
    #                  '--output-file', net],
    #                 stdout=sys.stdout, stderr=sys.stderr)

    # generate the pedestrians for this simulation
    randomTrips.main(randomTrips.get_options([
        '--net-file', net,
        '--output-trip-file', 'std_crossroad.ped.xml',
        '--seed', '42',  # make runs reproducible
        '--pedestrians',
        '--prefix', 'ped',
        # prevent trips that start and end on the same edge
        '--min-distance', '1',
        '--trip-attributes', 'departPos="random" arrivalPos="random"',
        '--binomial', '4',
        '--period', '35']))

    # this is the normal way of using traci. sumo is started as a
    # subprocess and then the python script connects and runs
    # traci.start([sumoBinary, '-c', os.path.join('data', 'std_crossroad.sumocfg')])
    traci.start([sumoBinary, '-c', os.path.join('std_crossroad.sumocfg')])
    run()
