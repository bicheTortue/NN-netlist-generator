#!/usr/bin/env python3

import argparse
import sys
import numpy as np
from itertools import count
nmos = "nch"
pmos = "pch"
Rmin = 10**4
Rmax = 10**6
Rf = (Rmax+Rmin)/2


def getNetId(_netCount=count()):
    return "net" + str(next(_netCount))


def getResVal(w):
    Rpos = (w-1+np.sqrt(w**2+1))*Rf/w
    Rneg = 2*Rf - Rpos
    return (Rpos, Rneg)

    # Defining the different lines/modules


def header(module_name):
    out.write(".subckt " + module_name + "\n")


def footer(module_name):
    out.write(".ends " + module_name + "\n")


def resistor(minus, plus, value, _id=count()):
    if (type(value) == int):
        value = str(value)
    out.write("R" + str(next(_id)) + " " + minus +
              " " + plus + " " + value + "\n")


def MOSFET(tType, drain, gate, source, bulk, _id=count()):
    out.write("M" + str(next(_id)) + " " + drain + " " + gate +
              " " + source + " " + bulk + " " + tType + "\n")


def sigmoid(Vin, Vout, _id=count()):
    out.write("Xsig" + str(next(_id)) + " V1 V2 V3s " +
              Vin + " " + Vout + " 0 idc vdd! sigmoid\n")
    # tmpNet = getNetId()
    # buffer(tmpNet, Vout)


def tanh(Vin, Vout, _id=count()):
    out.write("Xtanh" + str(next(_id)) + " V1 V2 V3t " +
              Vin + " " + Vout + " 0 idc vdd! tanh\n")


def voltMult(in1, in2, outPin, _id=count()):
    out.write("XvoltMult" + str(next(_id)) + " " + in1 +
              " " + in2 + " " + outPin + " voltageMult\n")


def opAmp(pin, nin, outPin, _id=count()):
    out.write("XopAmp" + str(next(_id)) + " " + nin +
              " " + outPin + " " + pin + " opAmp\n")


def buffer(inPin, outPin, _id=count()):
    out.write("Xbuffer" + str(next(_id)) + " " + outPin +
              " " + outPin + " " + inPin + " opAmp\n")


def inverter(inPin, outPin, _id=count()):
    out.write("Xinverter" + str(next(_id)) + " " + inPin +
              " " + outPin + " inverter\n")


def memcell(inPin, outPin, enableIn, enableOut, _id=count()):
    out.write("Xmemcell" + str(next(_id)) + " " + enableIn + " " +
              enableOut + " " + inPin + " " + outPin + " memcell\n")


def vpulse(plus, minus, dc=0, val0=0, val1="vdd", per=0, pw=0, td=0, _id=count()):
    out.write("Vpulse"+str(next(_id)) + " " + plus + " " + minus + " DC=" + str(dc) + " srcType=pulse val0=" +
              str(val0) + " val1=" + str(val1) + " per=" + str(per) + " pw=" + str(pw) + " td=" + str(td) + "\n")


def vdc(plus, minus, dc=0, _id=count()):
    out.write("Vdc"+str(next(_id)) + " " + plus + " " +
              minus + " DC=" + str(dc) + " srcType=dc\n")


def idc(plus, minus, dc=0, _id=count()):
    out.write("Idc"+str(next(_id)) + " " + plus + " " +
              minus + " DC=" + str(dc) + " srcType=dc\n")


def genXBar(lIn, serialSize):
    posCurOut = getNetId()  # Because common, bring in to make parallel
    negCurOut = getNetId()
    for i in range(serialSize):
        if (serialSize == 1):
            posWeight = posCurOut
            negWeight = negCurOut
        else:
            posWeight = getNetId()
            negWeight = getNetId()
        # Setting the input weights
        for netIn in lIn:
            # TODO : be able to choose between one or two opAmp/Weights
            resistor(netIn, posWeight, 100)
            resistor(netIn, negWeight, 100)  # TODO : Add weights calculations
        # Setting the bias weights
        resistor("netBias", posWeight, 1000)
        resistor("netBias", negWeight, 1000)
        if (serialSize > 1):  # The CMOS switches are not necessary if the system is fully parallelized
            # Positive line CMOS Switch
            MOSFET(nmos, posWeight, "e"+str(i), posCurOut, posCurOut)
            MOSFET(pmos, posWeight, "ne"+str(i), posCurOut, posWeight)
            # Negative line CMOS Switch
            MOSFET(nmos, negWeight, "e"+str(i), negCurOut, negCurOut)
            MOSFET(pmos, negWeight, "ne"+str(i), negCurOut, negWeight)

    tmpOp1 = getNetId()
    # OpAmps to voltage again
    opAmp("Vcm", posCurOut, tmpOp1)
    resistor(posCurOut, tmpOp1, "R")
    resistor(tmpOp1, negCurOut, "R")
    netOut = getNetId()
    opAmp("Vcm", negCurOut, netOut)
    resistor(negCurOut, netOut, "Rf")
    return netOut

# Not usable yet, have to figure out the index thingy


def genPointWiseGRU(outputNet, inputNet, cellStateNet, forgetNet, nbSerial):
    # Multiplication of C and forget
    tmpNet = getNetId()
    voltMult(forgetG, cellStateNet, tmpNet)
    adderNet = getNetId()
    resistor(tmpNet, adderNet, "R1")

    # Multiplication with old cell state
    tmpNet = getNetId()
    oldCellState = getNetId()
    voltMult(forgetNet, oldCellState, tmpNet)
    resistor(tmpNet, adderNet, "R1")

    # opAmp adder
    postAddNet = getNetId()
    opAmp("Vcm", adderNet, postAddNet)
    resistor(adderNet, postAddNet, "R2")

    # Memory of the cell state/hidden state
    for i in range(nbSerial):
        memcell(postAddNet, oldCellState, "m" +
                str(i) + "p2", "m" + str(i) + "p1")

        # voltMult( # TODO : Finish

    return postAddNet


def genPointWise(outputNet, inputNet, cellStateNet, forgetNet, nbSerial):
    # Multiplication of C and input
    tmpNet = getNetId()
    voltMult(inputNet, cellStateNet, tmpNet)
    adderNet = getNetId()
    resistor(tmpNet, adderNet, "R1")

    # Multiplication with old cell state
    tmpNet = getNetId()
    oldCellState = "cellStateOld"
    voltMult(forgetNet, oldCellState, tmpNet)
    resistor(tmpNet, adderNet, "R1")

    # opAmp adder
    postAddNet = "cellStateCur"
    opAmp("Vcm", adderNet, postAddNet)
    resistor(adderNet, postAddNet, "R2")

    # Memory of the cell state
    for i in range(nbSerial):
        memcell(postAddNet, oldCellState, "m" +
                str(i) + "p2", "m" + str(i) + "p1")

    # tanh activation function
    tmpNet = getNetId()
    tanh(adderNet, tmpNet)

    # Multiplication of last result and output gate
    tmpNet2 = getNetId()
    voltMult(outputNet, tmpNet, tmpNet2)

    # Multiplication by 10
    tmpNet = getNetId()
    resistor(tmpNet2, tmpNet, "R3")
    hidNet = getNetId()
    opAmp("Vcm", tmpNet, hidNet)
    resistor(tmpNet, hidNet, "R4")
    return hidNet


def genPowerNSignals(serialSize):  # NOTE : Find out if should be set here or in cadence
    vdc("gnd!", "vdd!", dc="vdd")
    vdc("gnd!", "Vcm", dc="vdd/2")
    vdc("gnd!", "V3t", dc="V3t")
    vdc("gnd!", "V3s", dc="V3s")
    vdc("gnd!", "V2", dc="V2")
    vdc("gnd!", "V1", dc="V1")
    idc("gnd!", "idc", dc="150u")

    # TODO : Check whether T/20 is enough time for the data to move from one memcell to another
    vpulse("gnd!", "nextT", per="T+T/20", td="T", pw="T/20")
    vpulse("gnd!", "predEn", per="2*(T+T/20)", td="2*(T+T/20)",
           pw="3*T/40")  # TODO : probably change pulse width
    vpulse("gnd!", "xbarEn", per="2*(T+T/20)", td="(T+T/20)", pw="T")
    for i in range(serialSize):
        vpulse("gnd!", "m" + str(i) + "p1", per="(T+T/20)", td=str(i) +
               "*T/" + str(serialSize), pw="T/"+str(2*serialSize))
        vpulse("gnd!", "m" + str(i) + "p2", per="(T+T/20)", td="T/"+str(2*serialSize) +
               "+" + str(i) + "*T/" + str(serialSize), pw="T/"+str(2*serialSize))
        vpulse("gnd!", "e" + str(i), per="(T+T/20)", td=str(i) +
               "*T/" + str(serialSize), pw="T/"+str(serialSize))
        inverter("e" + str(i), "ne" + str(i))


def main():

    parser = argparse.ArgumentParser(
        prog='Analog LSTM Generator', description='This program is used to generate spice netlists to be used in Cadence\'s virtuoso. It sets all the memristors values from the weights.')
    parser.add_argument("-o", "--output", nargs='?', type=argparse.FileType("w"), default=sys.stdout,
                        help="Specify an output file. The name of the file before '.' will be the name of the netlist.")

    # tmp # will be set by parameters
    isVanilla = True
    isFGR = False
    nbInput = 1
    nbHidden = 4
    nbPred = 1
    serialSize = 2
    # TODO : Add check to see if serialSize divides nbHidden
    parSize = int(np.ceil(nbHidden/serialSize))
    # tmp

    args = parser.parse_args()

    global out
    out = args.output

    name = (out.name.split('.')[0])
    # Start writing the file
    header(name)

    listIn = ["netIn"+str(i) for i in range(nbInput)]
    for i in range(nbHidden):
        listIn.append("netHid"+str(i))
    if isFGR:
        listFGR = []
        listFGR.append(["o"+str(i) for i in range(nbHidden)])
        listFGR.append(["i"+str(i) for i in range(nbHidden)])
        listFGR.append(["f"+str(i) for i in range(nbHidden)])

    predIn = []
    hidIndex = iter(range(nbHidden))
    for i in range(parSize):
        outputNet = "outputG" + str(i)
        inputNet = "inputG" + str(i)
        cellStateNet = "cellStateG" + str(i)
        forgetNet = "forgetG" + str(i)
        # Generate part of cell state gate
        tmpNet = genXBar(listIn, serialSize)
        tanh(tmpNet, cellStateNet)
        # Generate part of output gate
        if isVanilla:
            listIn.append("cellStateCur")
        if isFGR:
            listIn.append("cellStateOld")
            for l in listFGR:
                listIn.extend(l)
        tmpNet = genXBar(listIn, serialSize)
        sigmoid(tmpNet, outputNet)
        if isVanilla:
            listIn.pop()
        # Generate part of input gate
        if isVanilla:
            listIn.append("cellStateOld")
        tmpNet = genXBar(listIn, serialSize)
        sigmoid(tmpNet, inputNet)
        # Generate part of forget gate
        tmpNet = genXBar(listIn, serialSize)
        sigmoid(tmpNet, forgetNet)
        # It is not mandatory to clean the list
        # if isVanilla : listIn.pop()
        # if isFGR : listIn.pop()

        hiddenStateNet = genPointWise(
            outputNet, inputNet, cellStateNet, forgetNet, serialSize)

        # Memory cells for prediction NN
        # Memory cells for feedback
        for i in range(serialSize):
            curIndex = str(next(hidIndex))
            tmpNet = getNetId()
            predIn.append(tmpNet)
            memcell(hiddenStateNet, tmpNet, "m" + str(i) +
                    "p2", "predEn")  # Prediction memcells
            tmpNet = getNetId()
            memcell(hiddenStateNet, tmpNet, "m" + str(i) +
                    "p2", "nextT")  # Feedback memcells
            # There are 2 of them not to override the values with-in a single LSTM step
            memcell(tmpNet, "netHid" + curIndex, "nextT", "xbarEn")
            if isFGR:
                # For the output gate recurrence
                tmpNet = getNetId()
                memcell(hiddenStateNet, tmpNet, "m" + str(i) + "p2", "nextT")
                memcell(tmpNet, "o" + curIndex, "nextT", "xbarEn")
                # For the input gate recurrence
                tmpNet = getNetId()
                memcell(hiddenStateNet, tmpNet, "m" + str(i) + "p2", "nextT")
                memcell(tmpNet, "i" + curIndex, "nextT", "xbarEn")
                # For the forget gate recurrence
                tmpNet = getNetId()
                memcell(hiddenStateNet, tmpNet, "m" + str(i) + "p2", "nextT")
                memcell(tmpNet, "f" + curIndex, "nextT", "xbarEn")

    predNet = genXBar(predIn, nbPred)

    genPowerNSignals(serialSize)

    print("\nThe prediction are outputed on", predNet)

    # End of the file
    footer(name)
    out.close()


if (__name__ == "__main__"):
    main()
