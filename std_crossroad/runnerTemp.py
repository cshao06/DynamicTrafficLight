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
import xml.dom.minidom as xmldom

priority = None

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

DETECTORS = ["e2det_SC_3", "e2det_SC_2", "e2det_SC_1", "e2det_EC_3", "e2det_EC_2", "e2det_EC_1", "e2det_NC_3", "e2det_NC_2", "e2det_NC_1", "e2det_WC_3", "e2det_WC_2", "e2det_WC_1"]


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

TLS_ID = '0'
GIDX = [1, 4, 7, 10, 12, 13, 14, 15]

def setTrafficlight(schedule):
    light_str = ''
    for idx, light in enumerate(schedule):
        if light == 0:
            light_str += 'r'
        elif light == 1:
            if idx in GIDX:
                light_str += 'G'
            else:
                light_str += 'g'
        else:
            light_str += 'G'
    print('light state: ', light_str)
    traci.trafficlight.setRedYellowGreenState(TLS_ID, light_str)

def run():
    """execute the TraCI control loop"""
    global priority
    step = 0
    # we start with phase 2 where EW has green
    #traci.trafficlight.setPhase("0", 2)
    penalty = torch.zeros(16)
    priority = torch.zeros(16)
    while traci.simulation.getMinExpectedNumber() > 0:
        # if step % 10 != 0:
        #     step += 1
        #     continue
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
        light = torch.zeros(16)
        #获取等待行人
        peoWaitTime,pedest=checkWaitingPersons()
        print('pedest:', pedest.int().data)
        #获取等待车辆
        vehicle=torch.zeros(12)
        for idx, det in enumerate(DETECTORS):
            vehicle[idx] = (traci.lanearea.getLastStepHaltingNumber(det) > 0)
        #vehicle *= 100
        print('vehicle:', vehicle.int().data)
        traffic = torch.cat((vehicle, pedest*1), 0)
        index_t = [0, 1, 2, 12, 3, 4, 5, 13, 6, 7, 8, 14, 9, 10, 11, 15]
        traffic = traffic[index_t]
        print('traffic:', traffic.int().data)
        penalty = traffic * penalty + traffic
        penal_lift = [penalty[light < 1] * 2, penalty[light < 1] ** 2, torch.exp(penalty)]
        penalty_shift = penal_lift[0]
        #生成调度
        print('penalty:', penalty.int().data)

        schedule, light = geneSchedule(penalty_shift)

        #if step % 10 == 0:
        #    schedule = torch.LongTensor([0,0,0,1,2,1,0,0,0,1,2,1,2,0,2,0])
        #elif step % 10 == 5:
        #    schedule = torch.LongTensor([1,2,1,0,0,0,1,2,1,0,0,0,0,2,0,2])

        setTrafficlight(schedule)

        step += 1
    traci.close()
    sys.stdout.flush()




def checkWaitingPersons():
    """check whether a person has requested to cross the street"""
# pedestrian edges at the controlled intersection
#ALKINGAREAS = [':C_w3', ':C_w2', ':C_w1', ':C_w0']
# :C_c0 north, ':E_w0', ':N_w0', 'S_w0', 'W_w0'
#CROSSINGS = [':C_c2', ':C_c1', ':C_c0', ':C_c3']


    # 统计行人等待时间
    peopleWaitingTime = 0

    persons = torch.zeros(4)

    # check both sides of the crossing

    for edge in WALKINGAREAS:
        index = 0
        peds = traci.edge.getLastStepPersonIDs(edge)
        # print(peds)
        # check who is waiting at the crossing
        # we assume that pedestrians push the button upon
        # standing still for 1s
        for ped in peds:
            peopleWaitingTime+=traci.person.getWaitingTime(ped)
            # traci.person.getWaitingTime(ped)

            # if (traci.person.getWaitingTime(ped) == 1 and
            #         traci.person.getNextEdge(ped) == CROSSINGS[index]):
            #         persons[index] = 1
            # elif(traci.person.getWaitingTime(ped) == 1 and
            #         traci.person.getNextEdge(ped) == CROSSINGS[index + 1]):
            #         persons[index+1] = 1

            if (traci.person.getNextEdge(ped) in CROSSINGS):
                    persons[CROSSINGS.index(traci.person.getNextEdge(ped))] = 1

                # numWaiting = traci.trafficlight.getServedPersonCount(TLSID, PEDESTRIAN_GREEN_PHASE)
                # print("%s: pedestrian %s pushes the button (waiting: %s)" %
                #       (traci.simulation.getTime(), ped, numWaiting))
                #print("%s pushes the button" % ped)
                #return True
        index+=1

    return peopleWaitingTime,persons


# 计算时间片内平均等待车辆和行人，行人权重为车辆的1.2倍，计算车辆的平均通过速度
def averageWaiting(DETECTORS, people):
    veh_num=0
    speed=0
    for dec in DETECTORS:
        veh_num+=traci.lanearea.getLastStepHaltingNumber(dec)
        #getJamLengthVehicle
        # 计算车辆通过速度
        speed+=traci.lanearea.getLastStepMeanSpeed(dec)

    ped_num=torch.mean(people)*len(people.numpy().tolist())
    averageWait=veh_num+1.5*ped_num
    averageSpeed=speed/len(DETECTORS)

    return averageWait,averageSpeed,ped_num


#计算10s内行人和车辆的总等待时间
def totalWaiting():
    peo_time,_=checkWaitingPersons()
    veh_time=extractVeh()
    return peo_time+veh_time


#解析tripinfo获取车辆等待时间
def extractVeh():
    vehWaitSum=0
    xml_filepath = os.path.abspath("./tripinfo.xml")
    dom_obj = xmldom.parse(xml_filepath)
    element_obj = dom_obj.documentElement
    sub_element_obj = element_obj.getElementsByTagName("tripinfo")

    for i in range(len(sub_element_obj)):
        vehWaitSum += float(sub_element_obj[i].getAttribute("waitingTime"))

    return vehWaitSum



def get_options():
    """define options for this script and interpret the command line"""
    optParser = optparse.OptionParser()
    optParser.add_option("--nogui", action="store_true",
                         default=False, help="run the commandline version of sumo")
    optParser.add_option("-d", "--default", action="store_true",
                         default=False, help="Run the default fixed length traffic light")
    optParser.add_option("-c", "--sumocfg", action="store",
                         type="string", default="std_crossroad.sumocfg", dest="sumocfg", help="The sumocfg file")
    options, args = optParser.parse_args()
    return options


# 生成调度face
def geneSchedule(penalty):
    global priority
  # 初始化，可行置1，不可行置0，本身置1
    line0 = [-1, 1, 1, 0, 0, 1, 1, 1, 1, 0, 1, 1, 0, 0, 1, 0]
    line1 = [1, -1, 1, 0, 0, 0, 1, 1, 0, 1, 1, 0, 1, 0, 1, 1]
    line2 = [1, 1, -1, 0, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1]
    line3 = [0, 0, 0, -1, 0, 1, 1, 1, 1, 0, 1, 1, 1, 1, 0, 1]
    state_temp = torch.FloatTensor([line0, line1, line2, line3])
    state = torch.zeros(16, 16)

    for i in range(16):
        for j in range(16):
            bias = i // 4
            line = i % 4
            state[i][j] = state_temp[line][(j + 12 * bias) % 16]
  #0冲突， 1不冲突， -1本身
    state_prob = state.clone()
    state_prob[state_prob < 0] = 0
  #0冲突+本身， 1不冲突， 
    state = state + 1
  #1冲突， 2不冲突， 0本身
    state_copy = state.clone()
    state_copy[state_copy != 1] = 0
  #1冲突， 0不冲突+本身
    state_nol = 1 - state_copy
  #0冲突， 1不冲突+本身

    light = torch.zeros(16)
  #print('state_copy',state_copy.size())



  #获取当前loss最低对象
    penalty_tensor = penalty.reshape(1, -1).repeat(16, 1)
    loss = penalty_tensor * state_copy
    print('lossb: ', loss)
    loss_sum = loss.sum(1)
    print('lossa: ', loss_sum)
    # index_loss = [0, 1, 2, 4, 5, 6, 8, 9, 10, 12, 13, 14]
    index_loss = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
    loss_line = loss_sum[index_loss]
    min_mum  = min(loss_line)
    # min_p = 9999
    max_p = 0
    index = -1
    prob = torch.ones(16)
    for i in range(loss_line.shape[0]):
        if loss_line[i] == min_mum:
            if priority[i] > max_p:
                # min_p = priority[i]
                max_p = priority[i]
                index = i
    light[index] = 1
    priority[index] = 0

    prob = prob * state_prob[index]  # 求prob空间
    nol = state_nol[index]
    # print(index)
    # print(prob)
    # 调度可行域
    print('light',light)
    print('prob',prob)
    print()
    while (prob.sum() != 0):
        # min_p = 9999
        max_p = 0
        min_loss = 9999
        index = -1

    #获取可行域下一个执行对象index
        for i in range(16):
            if prob[i] > 0:
                nol_temp = nol * state_nol[i]
        #0冲突， 1不冲突+本身
                noloss = 1-nol_temp
        #1冲突， 0不冲突+本身
                loss = (noloss * penalty).sum()
                print((i, loss))
                if loss < min_loss:
                    min_loss = loss
                    index = i
                    # min_p = priority[i]
                    max_p = priority[i]
                elif loss == min_loss:
                    if priority[i] > max_p:
                        min_loss = loss
                        index = i
                        # min_p = priority[i]
                        max_p = priority[i]
        light[index] = 1
        priority[index] = 0
        # state_temp = state_prob[index]
        # state_temp -= 1
        # state_temp[state_temp < 0] = 0
        prob = prob * state_prob[index]#更新prob空间
        nol = nol * state_nol[index]
        # print(index)
        # print(prob)
        print('light',light)
        print('prob',prob)
        print()

    vlight = torch.zeros(12)
    plight = torch.zeros(4)
    j = 0
    k = 0
    for i in range(16):
        if i != 3 and i != 7 and i != 11 and i != 15:
            vlight[j] = light[i]
            j += 1
        else:
            plight[k] = light[i]
            k += 1
    #print(vlight)
    #print(plight)
    index_v = [8,7,6,5,4,3,2,1,0,11,10,9]
    index_p = [2,1,0,3]
    vlight = vlight[index_v]
    plight = plight[index_p]

    traflight = torch.cat((vlight, plight),0)
    print('priority before increment: ', priority)
    priority += 1  # 时间片结束，所有状态优先级均上升
    return traflight, light

def run_default():
    """execute the TraCI control loop"""
    step = 0
    # we start with phase 2 where EW has green
    traci.trafficlight.setPhase("0", 2)
    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
        step += 1
    traci.close()
    sys.stdout.flush()


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

    if options.sumocfg is None:
        cfg_file = 'std_crossroad.sumocfg'
    else:
        cfg_file = options.sumocfg
    # if len(sys.argv) == 2:
    #     cfg_file = sys.argv[1]
    # else:
    #     cfg_file = 'std_crossroad.sumocfg'

    net = 'std_crossroad.net.xml'
    # build the multi-modal network from plain xml inputs
    # subprocess.call([checkBinary('netconvert'),
    #                  '-c', os.path.join('data', 'pedcrossing.netccfg'),
    #                  '--output-file', net],
    #                 stdout=sys.stdout, stderr=sys.stderr)

    # generate the vehicles for this simulation
    randomTrips.main(randomTrips.get_options([
        '--net-file', net,
        '--output-trip-file', 'std_crossroad.rou.xml',
        # '--seed', '42',  # make runs reproducible
        '--end', '60',
        # '--prefix', 'ped',
        # prevent trips that start and end on the same edge
        '--min-distance', '1',
        '--trip-attributes', 'departPos="random" arrivalPos="random"',
        '--binomial', '3',
        '--period', '0.8']))

    # generate the pedestrians for this simulation
    randomTrips.main(randomTrips.get_options([
        '--net-file', net,
        '--output-trip-file', 'std_crossroad.ped.xml',
        # '--seed', '42',  # make runs reproducible
        '--pedestrians',
        '--end', '60',
        '--prefix', 'ped',
        # prevent trips that start and end on the same edge
        '--min-distance', '1',
        '--trip-attributes', 'departPos="random" arrivalPos="random"',
        '--binomial', '1',
        '--period', '5']))

    # this is the normal way of using traci. sumo is started as a
    # subprocess and then the python script connects and runs
    # traci.start([sumoBinary, '-c', os.path.join('data', 'std_crossroad.sumocfg')])
    # traci.start([sumoBinary, '-c', os.path.join('std_crossroad.sumocfg'), '--tripinfo-output', 'tripinfo.xml'])
    traci.start([sumoBinary, '-c', os.path.join(cfg_file), '--tripinfo-output', 'tripinfo.xml'])
    if options.default:
        run_default()
    else:
        run()
    # TotalWaitingTime=0
    # TotalWaitingTime=totalWaiting()
