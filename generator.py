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

def tanh(Vin, Vout):
    out.write("Xtanh" + str(next(_id)) + " V1 V2 V3t " + Vin + " " + Vout + " 0 idc vdd! tanh\n")

def voltMult(in1, in2, outPin, _id=count()):
    out.write("XvoltMult"+ str(next(_id)) + " " + in1 + " " + in2 + " " + outPin + " voltageMult\n")

def opAmp(pin, nin, outPin, _id=count()):
    out.write("XopAmp"+ str(next(_id)) + " " + nin + " " + outPin + " " + pin + " opAmp\n")

def memcell(inPin, outPin, enableIn, enableOut, _id=count()):
    out.write("Xmemcell"+ str(next(_id)) + " " + enableIn + " "  + enableOut + " " + inPin + " " + outPin + " memcell\n")


def genXBar(lIn, netOut, serialSize):
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
    opAmp("Vcm", negCurOut, netOut)
    resistor(negCurOut, netOut, "Rf") # TODO : Figure out how to fix Rf

def genPointWise(outputNet, inputNet, cellStateNet, forgetNet, nbSerial):
    # Multiplication of C and input
    tmpNet = getNetId()
    voltMult(inputNet,cellStateNet,tmpNet)
    adderNet = getNetId()
    resistor(tmpNet, adderNet, "R1")
    
    # Multiplication with old cell state
    tmpNet = getNetId()
    oldCellState = getNetId()
    voltMult(forgetG, oldCellState, tmpNet)
    resistor(tmpNet, adderNet, "R1")

    # opAmp adder
    postAddNet = getNetId()
    opAmp("Vcm", adderNet, postAddNet)
    resistor(adderNet, postAddNet, "R2")

    # Memory of the cell state
    for i in range(nbSerial):
        memcell(postAddNet, oldCellState,) # finish this
    
def main():

    parser = argparse.ArgumentParser(prog = 'Analog LSTM Generator', description = 'This program is used to generate spice netlists to be used in Cadence\'s virtuoso. It sets all the memristors values from the weights.')
    parser.add_argument("-o", "--output", nargs='?', type=argparse.FileType("w"), default=sys.stdout, help="Specify an output file. The name of the file before '.' will be the name of the netlist.")

    #tmp # will be set by parameters
    nbInput=1
    nbHidden=4
    serialSize=4
    parSize=int(np.ceil(nbHidden/serialSize))
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
    genXBar(listIn, listOut, serialSize)
    for i in range(parSize):
        # Generate part of output gate
        tmpNet = getNetId()
        genXBar(listInput, tmpNet, serialSize)
        sigmoid(tmpNet, "outputG"+str(i))
        # Generate part of input gate
        tmpNet = getNetId()
        genXBar(listInput, tmpNet, serialSize)
        sigmoid(tmpNet, "inputG"+str(i))
        # Generate part of cell state gate
        tmpNet = getNetId()
        genXBar(listInput, tmpNet, serialSize)
        tanh(tmpNet, "cellStateG"+str(i))
        # Generate part of forget gate
        tmpNet = getNetId()
        genXBar(listInput, tmpNet, serialSize)
        sigmoid(tmpNet, "forgetG"+str(i))





    genInputXBar(1,4,"outputG")
    genInputXBar(1,4,"inputG")
    genInputXBar(1,4,"cellStateG")
    genInputXBar(1,4,"forgetG")

    # End of the file
    footer(name) 
    out.close()

if(__name__ == "__main__"):
    main()
