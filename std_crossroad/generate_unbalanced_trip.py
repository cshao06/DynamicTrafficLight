#!/usr/bin/env python
import random

def generate_routefile():
    # random.seed(42)  # make tests reproducible
    N = 360  # number of time steps
    # demand per second from different directions
    # pWE = 1. / 10
    # pEW = 1. / 11
    # pNS = 1. / 30
    # pSN = 1. / 30
    pWE = 1. / 1
    pEW = 1. / 1
    pNS = 1. / 150
    pSN = 1. / 150
    with open("unbalanced.rou.xml", "w") as routes:
        print("<routes>", file=routes)
        # print("""<routes>
        # <vType id="typeWE" accel="0.8" decel="4.5" sigma="0.5" length="5" minGap="2.5" maxSpeed="16.67" \
# guiShape="passenger"/>
        # <vType id="typeNS" accel="0.8" decel="4.5" sigma="0.5" length="7" minGap="3" maxSpeed="25" guiShape="bus"/>

        # <route id="right" edges="51o 1i 2o 52i" />
        # <route id="left" edges="52o 2i 1o 51i" />
        # <route id="down" edges="54o 4i 3o 53i" />""", file=routes)
        vehNr = 0
        for i in range(N):
            if random.uniform(0, 1) < pWE:
                print('    <trip id="right_%i" from="WC" to="CE" depart="%i" departPos="random" arrivalPos="random" />' % (
                    vehNr, i), file=routes)
                vehNr += 1
            if random.uniform(0, 1) < pEW:
                print('    <trip id="left_%i" from="EC" to="CW" depart="%i" departPos="random" arrivalPos="random" />' % (
                    vehNr, i), file=routes)
                vehNr += 1
            if random.uniform(0, 1) < pNS:
                print('    <trip id="down_%i" from="NC" to="CS" depart="%i" color="1,0,0" departPos="random" arrivalPos="random"/>' % (
                    vehNr, i), file=routes)
                vehNr += 1
            if random.uniform(0, 1) < pSN:
                print('    <trip id="up_%i" from="SC" to="CN" depart="%i" color="1,0,0" departPos="random" arrivalPos="random"/>' % (
                    vehNr, i), file=routes)
                vehNr += 1
        print("</routes>", file=routes)

if __name__ == "__main__":
    generate_routefile()


