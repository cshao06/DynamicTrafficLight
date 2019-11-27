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
import subprocess


# 本脚本文件所在的目录
THISDIR = os.path.dirname('Users/siyuanzheng/Downloads/DynamicTrafficLight-master2/cross')

# 需要从$SUMO_HOME/tools目录导入相关包，为此需要先设置环境变量SUMO_HOME，
# 若未设置，请设置之。
try:
    # tutorial in tests
    sys.path.append(os.path.join(THISDIR, '..', '..', '..', '..', "tools"))
    # tutorial in docs
    sys.path.append(os.path.join(os.environ.get("SUMO_HOME", os.path.join(
        THISDIR, "..", "..", "..")), "tools"))  
    import traci
    from sumolib import checkBinary  # noqa
    import randomTrips
except ImportError:
    sys.exit(
        "please declare environment variable 'SUMO_HOME' as the root directory of your sumo installation (it should contain folders 'bin', 'tools' and 'docs')")


# 车辆的最短绿灯时间
MIN_GREEN_TIME = 15
# 红绿灯仿真计划的初始状态，参见'pedcrossing.tll.xml'    
VEHICLE_GREEN_PHASE = 0
# 红绿灯的ID（仅包含一个），默认情况下它与受控交叉路口的ID相同。
TLSID = 'C'

# 受控交叉口的人行横道边界
WALKINGAREAS = [':C_w0', ':C_w1']
CROSSINGS = [':C_c0']


def generate_routefile():
    random.seed(42)  # make tests reproducible
    N = 3600  # number of time steps
    # demand per second from different directions
    pWE = 1. / 10
    pEW = 1. / 11
    # pNS = 1. / 30
    pNS = 1. / 12
    pSN = 1. / 13
    with open("cross.rou.xml", "w") as routes:
        print("""<routes>
        <vType id="typeWE" accel="0.8" decel="4.5" sigma="0.5" length="5" minGap="2.5" maxSpeed="16.67" \
guiShape="passenger"/>
        <vType id="typeNS" accel="0.8" decel="4.5" sigma="0.5" length="7" minGap="3" maxSpeed="25" guiShape="bus"/>

        <route id="right" edges="51o 1i 2o 52i" />
        <route id="left" edges="52o 2i 1o 51i" />
        <route id="down" edges="54o 4i 3o 53i" />
        <route id="up" edges="53o 3i 4o 54i" />""", file=routes)
        vehNr = 0
        for i in range(N):
            if random.uniform(0, 1) < pWE:
                print('    <vehicle id="right_%i" type="typeWE" route="right" depart="%i" />' % (
                    vehNr, i), file=routes)
                vehNr += 1
            if random.uniform(0, 1) < pEW:
                print('    <vehicle id="left_%i" type="typeWE" route="left" depart="%i" />' % (
                    vehNr, i), file=routes)
                vehNr += 1
            if random.uniform(0, 1) < pNS:
                print('    <vehicle id="down_%i" type="typeNS" route="down" depart="%i" color="1,0,0"/>' % (
                    vehNr, i), file=routes)
                vehNr += 1
            # if random.uniform(0, 1) < pSN:
            #     print('    <vehicle id="up_%i" type="typeNS" route="up" depart="%i" color="1,0,0"/>' % (
            #         vehNr, i), file=routes)
            #     vehNr += 1
        print("</routes>", file=routes)

# The program looks like this
#    <tlLogic id="0" type="static" programID="0" offset="0">
# the locations of the tls are      NESW
#        <phase duration="31" state="GrGr"/>
#        <phase duration="6"  state="yryr"/>
#        <phase duration="31" state="rGrG"/>
#        <phase duration="6"  state="ryry"/>
#    </tlLogic>


def run():
    # 记录允许车辆通行的绿灯持续时间    
    greenTimeSoFar = 0

    # 行人过马路按钮是否按下
    activeRequest = False

    """execute the TraCI control loop"""
    step = 0
    # we start with phase 2 where EW has green
    traci.trafficlight.setPhase("0", 2)
    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
#        # 如果车辆的绿灯时间超过最短绿灯时间，则确定是否有等待过马路的行人，并切换信号灯状态
#        if not activeRequest:
#            activeRequest = checkWaitingPersons()
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


# 检测是否有行人需要过马路
def checkWaitingPersons():

    # 检测路口两侧的行人
    for edge in WALKINGAREAS:
        peds = traci.edge.getLastStepPersonIDs(edge)

        # 检测是否有人在路口等待
        # 我们假设行人在等待1秒后，才按下过马路按钮
        for ped in peds:
            if (traci.person.getWaitingTime(ped) == 1 and
                    traci.person.getNextEdge(ped) in CROSSINGS):
                print("%s pushes the button" % ped)
                return True
    return False


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

    net = 'cross.net.xml'

    # 借助工具软件netconvert，从普通的xml输入构建多模态网络
    subprocess.call([checkBinary('netconvert'),
                     '-c', os.path.join('data', 'cross.netccfg'),
                     '--output-file', net],
                    stdout=sys.stdout, stderr=sys.stderr)
    # 随机生成仿真中的行人
    randomTrips.main(randomTrips.get_options([
        '--net-file', net,
        '--output-trip-file', 'pedestrians.trip.xml',
        '--seed', '42',  # make runs reproducible
        '--pedestrians',
        '--prefix', 'ped',
        # prevent trips that start and end on the same edge
        '--min-distance', '1',
        '--trip-attributes', 'departPos="random" arrivalPos="random"',
        '--binomial', '4',
        '--period', '35']))

    # 这是启动TraCI的一般方法。sumo作为子进程启动，然后使用本脚本文件连接该子进程  
    traci.start([sumoBinary, '-c', os.path.join('cross.sumocfg')])
    # 调用TraCI控制主循环过程
    run()
