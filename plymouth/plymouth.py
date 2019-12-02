#!/usr/bin/env python
# Eclipse SUMO, Simulation of Urban MObility; see https://eclipse.org/sumo
# Copyright (C) 2009-2019 German Aerospace Center (DLR) and others.
# This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v2.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v20.html
# SPDX-License-Identifier: EPL-2.0

# @file    runner.py
# @author  Lena Kalleske
# @author  Daniel Krajzewicz
# @author  Michael Behrisch
# @author  Jakob Erdmann
# @date    2009-03-26
# @version $Id$

from __future__ import absolute_import
from __future__ import print_function

import os
import sys
import optparse
import random

# we need to import python modules from the $SUMO_HOME/tools directory
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")

from sumolib import checkBinary  # noqa
import traci  # noqa
# import randomTrips  # noqa

# minimum green time for the vehicles
MIN_GREEN_TIME = 15
# the first phase in tls plan. see 'pedcrossing.tll.xml'
VEHICLE_GREEN_PHASE = 0
PEDESTRIAN_GREEN_PHASE = 2
# the id of the traffic light (there is only one). This is identical to the
# id of the controlled intersection (by default)
TLSID = 'cluster_5366535756_5366535757_5545639495_5545639496_767530322'

# pedestrian edges at the controlled intersection
WALKINGAREAS = [':4200368775_w0', ':5233121811_w0', ':5233656401_w0', ':5237009838_w0']
CROSSINGS = [':cluster_5366535756_5366535757_5545639495_5545639496_767530322_c0',
             ':cluster_5366535756_5366535757_5545639495_5545639496_767530322_c1',
             ':cluster_5366535756_5366535757_5545639495_5545639496_767530322_c2',
             ':cluster_5366535756_5366535757_5545639495_5545639496_767530322_c3']


# def generate_routefile():
#     random.seed(42)  # make tests reproducible
#     N = 3600  # number of time steps
#     # demand per second from different directions
#     pWE = 1. / 10
#     pEW = 1. / 11
#     # pNS = 1. / 30
#     pNS = 1. / 12
#     pSN = 1. / 13
#     with open("data/cross.rou.xml", "w") as routes:
#         print("""<routes>
#         <vType id="typeWE" accel="0.8" decel="4.5" sigma="0.5" length="5" minGap="2.5" maxSpeed="16.67" \
# guiShape="passenger"/>
#         <vType id="typeNS" accel="0.8" decel="4.5" sigma="0.5" length="7" minGap="3" maxSpeed="25" guiShape="bus"/>

#         <route id="right" edges="51o 1i 2o 52i" />
#         <route id="left" edges="52o 2i 1o 51i" />
#         <route id="down" edges="54o 4i 3o 53i" />
#         <route id="up" edges="53o 3i 4o 54i" />""", file=routes)
#         vehNr = 0
#         for i in range(N):
#             if random.uniform(0, 1) < pWE:
#                 print('    <vehicle id="right_%i" type="typeWE" route="right" depart="%i" />' % (
#                     vehNr, i), file=routes)
#                 vehNr += 1
#             if random.uniform(0, 1) < pEW:
#                 print('    <vehicle id="left_%i" type="typeWE" route="left" depart="%i" />' % (
#                     vehNr, i), file=routes)
#                 vehNr += 1
#             if random.uniform(0, 1) < pNS:
#                 print('    <vehicle id="down_%i" type="typeNS" route="down" depart="%i" color="1,0,0"/>' % (
#                     vehNr, i), file=routes)
#                 vehNr += 1
#             # if random.uniform(0, 1) < pSN:
#             #     print('    <vehicle id="up_%i" type="typeNS" route="up" depart="%i" color="1,0,0"/>' % (
#             #         vehNr, i), file=routes)
#             #     vehNr += 1
#         print("</routes>", file=routes)

# The program looks like this
#    <tlLogic id="0" type="static" programID="0" offset="0">
# the locations of the tls are      NESW
#        <phase duration="31" state="GrGr"/>
#        <phase duration="6"  state="yryr"/>
#        <phase duration="31" state="rGrG"/>
#        <phase duration="6"  state="ryry"/>
#    </tlLogic>

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
                numWaiting = traci.trafficlight.getServedPersonCount(TLSID, PEDESTRIAN_GREEN_PHASE)
                print("%s: pedestrian %s pushes the button (waiting: %s)" %
                      (traci.simulation.getTime(), ped, numWaiting))
                return True
    return False


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
#         # if not activeRequest:
#         #     activeRequest = checkWaitingPersons()
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


def get_options():
    optParser = optparse.OptionParser()
    optParser.add_option("--nogui", action="store_true",
                         default=False, help="run the commandline version of sumo")
    options, args = optParser.parse_args()
    return options


# this is the main entry point of this script
if __name__ == "__main__":
    options = get_options()

    # this script has been called from the command line. It will start sumo as a
    # server, then connect and run
    if options.nogui:
        sumoBinary = checkBinary('sumo')
    else:
        sumoBinary = checkBinary('sumo-gui')

    # first, generate the route file for this simulation
    # generate_routefile()

    # net = 'plymouth.net.xml'
    # net = 'plymouth_new.net.xml'
    # build the multi-modal network from plain xml inputs
    # subprocess.call([checkBinary('netconvert'),
    #                  '-c', os.path.join('cross.netccfg'),
    #                  '--output-file', net],
    #                 stdout=sys.stdout, stderr=sys.stderr)

    # generate the pedestrians for this simulation
    # randomTrips.main(randomTrips.get_options([
    #     '--net-file', net,
    #     '--output-trip-file', 'pedestrians.trip.xml',
    #     '--seed', '42',  # make runs reproducible
    #     '--pedestrians',
    #     '--prefix', 'ped',
    #     # prevent trips that start and end on the same edge
    #     '--min-distance', '1',
    #     '--trip-attributes', 'departPos="random" arrivalPos="random"',
    #     '--binomial', '4',
    #     '--period', '35']))
    # # this is the normal way of using traci. sumo is started as a
    # # subprocess and then the python script connects and runs
    # traci.start([sumoBinary, "-c", "plymouth.sumocfg",
    #                          "--tripinfo-output", "tripinfo.xml"])
    run()
