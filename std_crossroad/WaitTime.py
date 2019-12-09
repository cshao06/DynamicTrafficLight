import os
import sys
import optparse
import subprocess
import torch
import numpy as np
import xml.dom.minidom as xmldom


#解析tripinfo获取车辆等待时间
def extractVeh():
    vehWait=[]
    pedWait=[]
    xml_filepath = os.path.abspath("./tripinfo.xml")
    dom_obj = xmldom.parse(xml_filepath)
    element_obj = dom_obj.documentElement
    #车辆平均等待时间
    sub_element_obj = element_obj.getElementsByTagName("tripinfo")
    for i in range(len(sub_element_obj)):
        vehWait.append(float(sub_element_obj[i].getAttribute("waitingTime")))
    veh_mean=np.mean(vehWait)
    # 车辆等待时间标准差
    veh_std=np.std(vehWait,ddof=1)

    #行人平均等待时间
    sub_element_obj_1 = element_obj.getElementsByTagName("walk")
    for i in range(len(sub_element_obj_1)):
        pedWait.append(float(sub_element_obj_1[i].getAttribute("timeLoss")))
    ped_mean=np.mean(pedWait)
    # 行人等待时间标准差
    ped_std=np.std(pedWait,ddof=1)

    return veh_mean,veh_std,ped_mean,ped_std


if __name__ == "__main__":
    veh_mean,veh_std,ped_mean,ped_std=extractVeh()
    print("车辆平均等待时间:"+str(veh_mean))
    print("车辆等待时间标准差:" + str(veh_std))

    print("行人平均等待时间"+str(ped_mean))
    print("行人等待时间标准差" + str(ped_std))
