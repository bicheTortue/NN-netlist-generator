#!/usr/bin/env python3

import argparse
import sys
import numpy as np
from itertools import count
nmos="nch"
pmos="pch"

def getNetId(_netCount=count()):
    return "net"+ str(next(_netCount))

# Defining the different lines/modules
def header(module_name):
    out.write(".subckt " + module_name + "\n")

def footer(module_name):
    out.write(".ends " + module_name + "\n")

def resistor(minus, plus, value, _id=count()):
    if(type(value) == int):
        value=str(value)
    out.write("R" + str(next(_id)) + " " + minus + " " + plus + " " + value + "\n")

def MOSFET(tType, drain, gate, source, bulk, _id=count()):
    out.write("M" + str(next(_id)) + " " + drain + " " + gate + " " + source + " " + bulk + " " + tType + "\n")

def sigmoid(Vin, Vout, _id=count()):
    out.write("Xsig" + str(next(_id)) + " V1 V2 V3s " + Vin + " " + Vout + " 0 idc vdd! sigmoid\n")

def tanh(Vin, Vout, _id=count()):
    out.write("Xtanh" + str(next(_id)) + " V1 V2 V3t " + Vin + " " + Vout + " 0 idc vdd! tanh\n")

def voltMult(in1, in2, outPin, _id=count()):
    out.write("XvoltMult"+ str(next(_id)) + " " + in1 + " " + in2 + " " + outPin + " voltageMult\n")

def opAmp(pin, nin, outPin, _id=count()):
    out.write("XopAmp"+ str(next(_id)) + " " + nin + " " + outPin + " " + pin + " opAmp\n")

def memcell(inPin, outPin, enableIn, enableOut, _id=count()):
    out.write("Xmemcell"+ str(next(_id)) + " " + enableIn + " "  + enableOut + " " + inPin + " " + outPin + " memcell\n")


def genXBar(lIn, serialSize):
    posCurOut = getNetId() # Because common, bring in to make parallel
    negCurOut = getNetId() 
    for i in range(serialSize):
        if(serialSize==1):
            posWeight=posCurOut
            negWeight=negCurOut
        else:
            posWeight = getNetId()
            negWeight = getNetId()
        # Setting the input weights
        for netIn in lIn:
            resistor(netIn, posWeight, 100) # TODO : be able to choose between one or two opAmp/Weights
            resistor(netIn, negWeight,100) # TODO : Add weights calculations
        # Setting the bias weights
        resistor("netBias", posWeight,1000)
        resistor("netBias", negWeight,1000)
        if(serialSize>1): # The CMOS switches are not necessary if the system is fully parallelized
            # Positive line CMOS Switch
            MOSFET(nmos,posWeight, "e"+str(i), posCurOut, posCurOut)
            MOSFET(pmos,posWeight, "ne"+str(i), posCurOut, posWeight)
            # Negative line CMOS Switch
            MOSFET(nmos,negWeight, "e"+str(i), negCurOut, negCurOut)
            MOSFET(pmos,negWeight, "ne"+str(i), negCurOut, negWeight)

    tmpOp1 = getNetId()
    # OpAmps to voltage again
    opAmp("Vcm", posCurOut, tmpOp1)
    resistor(posCurOut, tmpOp1, "R")
    resistor(tmpOp1, negCurOut, "R")
    netOut = getNetId()
    opAmp("Vcm", negCurOut, netOut)
    resistor(negCurOut, netOut, "Rf") # TODO : Figure out how to fix Rf
    return netOut

def genPointWiseVanilla(outputNet, inputNet, cellStateNet, forgetNet, nbSerial):
    # Multiplication of C and input
    tmpNet = getNetId()
    voltMult(inputNet,cellStateNet,tmpNet)
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
        memcell(postAddNet, oldCellState, "m" + str(i)+ "p2", "m" + str(i)+ "p1")

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

def genPointWiseNP(outputNet, inputNet, cellStateNet, forgetNet, nbSerial):
    # Multiplication of C and input
    tmpNet = getNetId()
    voltMult(inputNet,cellStateNet,tmpNet)
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

    # Memory of the cell state
    for i in range(nbSerial):
        memcell(postAddNet, oldCellState, "m" + str(i)+ "p2", "m" + str(i)+ "p1")

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
    
def main():

    parser = argparse.ArgumentParser(prog = 'Analog LSTM Generator', description = 'This program is used to generate spice netlists to be used in Cadence\'s virtuoso. It sets all the memristors values from the weights.')
    parser.add_argument("-o", "--output", nargs='?', type=argparse.FileType("w"), default=sys.stdout, help="Specify an output file. The name of the file before '.' will be the name of the netlist.")

    #tmp # will be set by parameters
    isVanilla =True 
    nbInput=1
    nbHidden=4
    nbPred=1
    serialSize=4
    parSize=int(np.ceil(nbHidden/serialSize)) # TODO : Add check to see if serialSize divides nbHidden
    #tmp

    args = parser.parse_args()
    
    global out
    out = args.output

    name = (out.name.split('.')[0]) 
    # Start writing the file
    header(name) 

    listIn = ["netIn"+str(i) for i in range(nbInput)]
    for i in range(nbHidden):
        listIn.append("netHid"+str(i))

    # listOut = [getNetId() for _ in range(parSize)]
    # genXBar(listIn, listOut, serialSize)
    predIn = []
    hidIndex = iter(range(nbHidden))
    for i in range(parSize):
        outputNet = "outputG" + str(i)
        inputNet = "inputG" + str(i)
        cellStateNet = "cellStateG" + str(i)
        forgetNet = "forgetG" + str(i)
        # Generate part of output gate
        if isVanilla : listIn.append("cellStateCur")
        tmpNet = genXBar(listIn, serialSize)
        sigmoid(tmpNet, outputNet)
        if isVanilla : listIn.pop()
        # Generate part of input gate
        if isVanilla : listIn.append("cellStateOld")
        tmpNet = genXBar(listIn, serialSize)
        sigmoid(tmpNet, inputNet)
        if isVanilla : listIn.pop()
        # Generate part of cell state gate
        tmpNet = genXBar(listIn, serialSize)
        tanh(tmpNet, cellStateNet)
        # Generate part of forget gate
        if isVanilla : listIn.append("cellStateOld")
        tmpNet = genXBar(listIn, serialSize)
        sigmoid(tmpNet, forgetNet)
        if isVanilla : listIn.pop()

        hiddenStateNet = genPointWiseVanilla(outputNet, inputNet, cellStateNet, forgetNet, serialSize)

        # Memory cells for prediction NN
        # Memory cells for feedback
        for i in range(serialSize):
            tmpNet = getNetId()
            predIn.append(tmpNet)
            memcell(hiddenStateNet, tmpNet, "m" + str(i)+ "p2", "predEn") # Prediction memcells
            tmpNet = getNetId()
            memcell(hiddenStateNet, tmpNet, "m" + str(i)+ "p2", "nextT") # Feedback memcells
            memcell(tmpNet, "netHid" + str(next(hidIndex)), "nextT", "xbarEn") # There are 2 of them not to override the values with-in a single LSTM step

    predNet = genXBar(predIn, nbPred)
    print("The prediction are outputed on ", predNet) 

    # End of the file
    footer(name) 
    out.close()

if(__name__ == "__main__"):
    main()
