#!/usr/bin/env python

"""
Tutorial for traffic light control via the TraCI interface.
This scenario models a pedestrian crossing which switches on demand.
"""
from __future__ import absolute_import
from __future__ import print_function

import operator
import os
import sys
import optparse
import subprocess
import torch
import numpy as np

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
WALKINGAREAS = [':C_w3', ':C_w2', ':C_w1', ':C_w0']
# :C_c0 north, ':E_w0', ':N_w0', 'S_w0', 'W_w0'
CROSSINGS = [':C_c2', ':C_c1', ':C_c0', ':C_c3']


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
        #if traci.trafficlight.getPhase("0") == 2:
            # we are not already switching
            # if traci.inductionloop.getLastStepVehicleNumber("0") > 0:
            #if #traci.lanearea.getLastStepVehicleNumber("TLS0_my_program_E2CollectorOn_2i_0") > 0:
                # there is a vehicle from the north, switch
                #traci.trafficlight.setPhase("0", 3)
            #else:
                # otherwise try to keep green for EW
                #traci.trafficlight.setPhase("0", 2)

        #获取等待行人
        pedest=checkWaitingPersons()
        #获取等待车辆
        vehicle=torch.zeros(16)
        i=0
        vehicle[i] =traci.lanearea.getLastStepVehicleNumber("e2det_SC_3")
        i+=1
        vehicle[i] = traci.lanearea.getLastStepVehicleNumber("e2det_SC_2")
        i += 1
        vehicle[i] = traci.lanearea.getLastStepVehicleNumber("e2det_SC_1")
        i += 1
        vehicle[i] = pedest[0]
        i += 1
        vehicle[i] = traci.lanearea.getLastStepVehicleNumber("e2det_EC_3")
        i += 1
        vehicle[i] = traci.lanearea.getLastStepVehicleNumber("e2det_EC_2")
        i += 1
        vehicle[i] = traci.lanearea.getLastStepVehicleNumber("e2det_EC_1")
        i += 1
        vehicle[i]=pedest[1]
        i += 1
        vehicle[i] = traci.lanearea.getLastStepVehicleNumber("e2det_NC_3")
        i += 1
        vehicle[i] = traci.lanearea.getLastStepVehicleNumber("e2det_NC_2")
        i += 1
        vehicle[i] = traci.lanearea.getLastStepVehicleNumber("e2det_NC_1")
        i += 1
        vehicle[i] = pedest[2]
        i+=1
        vehicle[i] = traci.lanearea.getLastStepVehicleNumber("e2det_WC_3")
        i += 1
        vehicle[i] = traci.lanearea.getLastStepVehicleNumber("e2det_WC_2")
        i += 1
        vehicle[i] = traci.lanearea.getLastStepVehicleNumber("e2det_WC_1")
        i += 1
        vehicle[i] = pedest[3]


        #生成调度
        schedule=geneSchedule(step,pedest,vehicle)

        step += 1
    traci.close()
    sys.stdout.flush()



def checkWaitingPersons():
    """check whether a person has requested to cross the street"""
# pedestrian edges at the controlled intersection
#ALKINGAREAS = [':C_w3', ':C_w2', ':C_w1', ':C_w0']
# :C_c0 north, ':E_w0', ':N_w0', 'S_w0', 'W_w0'
#CROSSINGS = [':C_c2', ':C_c1', ':C_c0', ':C_c3']
    persons = torch.zeros(4)

    # check both sides of the crossing

    for edge in WALKINGAREAS:
        index = 0
        peds = traci.edge.getLastStepPersonIDs(edge)
        # check who is waiting at the crossing
        # we assume that pedestrians push the button upon
        # standing still for 1s
        for ped in peds:
            if (traci.person.getWaitingTime(ped) == 1 and
                    traci.person.getNextEdge(ped) == CROSSINGS[index]):
                    persons[index] = 1
            elif(traci.person.getWaitingTime(ped) == 1 and
                    traci.person.getNextEdge(ped) == CROSSINGS[index + 1]):
                    persons[index+1] = 1
                # numWaiting = traci.trafficlight.getServedPersonCount(TLSID, PEDESTRIAN_GREEN_PHASE)
                # print("%s: pedestrian %s pushes the button (waiting: %s)" %
                #       (traci.simulation.getTime(), ped, numWaiting))
                #print("%s pushes the button" % ped)
                #return True
        index+=1


    return persons


def get_options():
    """define options for this script and interpret the command line"""
    optParser = optparse.OptionParser()
    optParser.add_option("--nogui", action="store_true",
                         default=False, help="run the commandline version of sumo")
    options, args = optParser.parse_args()
    return options


# 生成调度face
def geneSchedule(time, people, vehicle):
    # 初始化，可行置1，不可行置0，本身置1
    line0 = [-1, 1, 1, 0, 0, 1, 1, 1, 1, 0, 1, 1, 0, 0, 1, 1]
    line1 = [1, -1, 1, 0, 0, 0, 1, 1, 0, 1, 1, 1, 1, 0, 1, 1]
    line2 = [1, 1, -1, 0, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1]
    line3 = [0, 0, 0, -1, 0, 1, 1, 1, 1, 0, 1, 1, 1, 1, 0, 1]
    state_temp = torch.FloatTensor([line0, line1, line2, line3])
    state = torch.zeros(16, 16)
    privilege = torch.zeros(16)
    for i in range(16):
        for j in range(16):
            bias = i // 4
            line = i % 4
            state[i][j] = state_temp[line][(j + 12 * bias) % 16]
    state = state + 1
    # print(state)

    # 获取每个状态的代价损失
    # veh=torch.Tensor(vehicle)
    veh = vehicle
    peo=people
    loss_arr = torch.zeros(16)
    for k in range(16):
        s = state[k]
        s = s.numpy().tolist()
        loss = 0
        for p in range(16):
            loss =loss+ s[p] * veh[p]+s[p] * peo[p]
        loss_arr[k] = loss

    # 获取当前loss最低对象
    # min_mum=min(enumerate(loss_arr))
    _, min_mum = min(enumerate(loss_arr), key=operator.itemgetter(1))

    list_temp = []
    min_p = 9999
    index = -1
    prob = torch.ones(16)
    light = np.zeros(16)
    for i in range(loss_arr.shape[0]):
        if loss_arr[i] == min_mum:
            if privilege[i] < min_p:
                min_p = privilege[i]
                index = i
    light[index] = 1
    privilege[index] = 0
    state_temp = state[index]
    state_temp -= 1
    state_temp[state_temp < 0] = 0
    prob = prob * state_temp  # 求prob空间
    # print(index)
    # print(prob)
    # 调度可行域
    while (prob.sum() != 0):
        loss_arr[index] = 9999
        list_temp = []
        min_p = 9999
        min_loss = 9999
        index = -1

        # 获取可行域下一个执行对象index
        for i in range(16):
            if prob[i] > 0:
                if loss_arr[i] < min_loss:
                    min_loss == loss_arr[i]
                    index = i
                    min_p = privilege[i]
                elif loss_arr[i] == min_loss:
                    if privilege[i] < min_p:
                        min_loss = loss_arr[i]
                        index = i
                        min_p = privilege[i]
        light[index] = 1
        privilege[index] = 0
        state_temp = state[index]
        state_temp -= 1
        state_temp[state_temp < 0] = 0
        prob = prob * state_temp  # 更新prob空间
        # print(index)
        # print(prob)

    traflight = torch.zeros(12)
    j = 0
    for i in range(16):
        if i != 3 and i != 7 and i != 11 and i != 15:
            traflight[j] = light[i]
            j += 1
    traflight = traflight.permute(9,8,7,6,5,4,3,2,1,12,11,10)
    privilege += 1  # 时间片结束，所有状态优先级均上升
    return traflight



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
