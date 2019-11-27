# 为兼容python 2.7所做的措施
from __future__ import absolute_import
from __future__ import print_function

# 导入相关包
import os
import sys
import optparse
import subprocess
import random


# 本脚本文件所在的目录
THISDIR = os.path.dirname('Users/siyuanzheng/Downloads/DynamicTrafficLight-master')

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

# TraCI控制主循环过程
def run():   
    # 记录允许车辆通行的绿灯持续时间    
    greenTimeSoFar = 0

    # 行人过马路按钮是否按下
    activeRequest = False

    # 主循环。在每个仿真步骤中执行某些操作，直到场景中没有新的车辆加入或现有车辆行驶
    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()

        # 如果车辆的绿灯时间超过最短绿灯时间，则确定是否有等待过马路的行人，并切换信号灯状态
        if not activeRequest:
            activeRequest = checkWaitingPersons()
        if traci.trafficlight.getPhase(TLSID) == VEHICLE_GREEN_PHASE:
            greenTimeSoFar += 1
            if greenTimeSoFar > MIN_GREEN_TIME:

                # 检测行人是否按下了过马路按钮
                if activeRequest:
                    # 信号灯切换至另一个状态，即非绿灯状态
                    # VEHICLE_GREEN_PHASE + 1表明切换到黄灯转红灯状态
                    traci.trafficlight.setPhase(
                        TLSID, VEHICLE_GREEN_PHASE + 1)
                    # 复位相关变量
                    activeRequest = False
                    greenTimeSoFar = 0

    sys.stdout.flush()
    traci.close()

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

# 定义本脚本文件及从命令行中解析得到的参数
def get_options():

    optParser = optparse.OptionParser()
    # 增加一个"--nogui"选项，默认值为False，即默认使用图形化界面
    optParser.add_option("--nogui", action="store_true",
                         default=False, help="run the commandline version of sumo")
    options, args = optParser.parse_args()
    return options


# 本脚本文件主入口
if __name__ == "__main__":

    # 获取程序运行的参数
    options = get_options()

    # 确定是调用sumo还是sumo-gui
    if options.nogui:
        sumoBinary = checkBinary('sumo')
    else:
        sumoBinary = checkBinary('sumo-gui')

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
    traci.start([sumoBinary, '-c', os.path.join('data', ' cross.sumocfg')])
    # 调用TraCI控制主循环过程
    run()