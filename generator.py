#!/usr/bin/env python3

import argparse
import sys
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
    out.write("Xsig" + str(next(_id)) + " V1 V2 V3s " + Vin + " " + Vout + " 0 idc vdd sigmoid\n")

def tanh(Vin, Vout):
    out.write("Xtanh" + str(next(_id)) + " V1 V2 V3t " + Vin + " " + Vout + " 0 idc vdd tanh\n")

def voltMult(in1, in2, outPin, _id=count()):
    out.write("XvoltMult"+ str(next(_id)) + " " + in1 + " " + in2 + " " + outPin + " voltageMult\n")

def opAmp(pin, nin, outPin, _id=count()):
    out.write("XopAmp"+ str(next(_id)) + " " + nin + " " + outPin + " " + pin + " opAmp\n")

def memcell(inVal, enableIn, enableOut, out, _id=count()):
    out.write("Xmemcell"+ str(next(_id)) + " " + enableIn + " "  + enableOut + " " + inVal + " " + out + " memcell\n")

def genInputXBar(nbIn,nbHid,outNet):
    posCurOut = getNetId() # Because common, bring in to make parallel
    negCurOut = getNetId() 
    for i in range(nbHid): # Add another inner loop for both serial and parallel
        posWeight = getNetId()
        negWeight = getNetId()
        # Setting the input weights
        for j in range(nbIn):
            resistor("netIn"+str(j), posWeight, 100) # TODO : be able to choose between one or two opAmp
            resistor("netIn"+str(j), negWeight,100) # TODO : Add weights calculations
        # Setting the hidden weights
        for j in range(nbHid):
            resistor("netHid"+str(j), posWeight,10)
            resistor("netHid"+str(j), negWeight,10)
        # Setting the bias weights
        resistor("netBias", posWeight,1000)
        resistor("netBias", negWeight,1000)
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
    opOut = getNetId()
    opAmp("Vcm", negCurOut, opOut)
    resistor(negCurOut, opOut, "Rf") # TODO : Figure out how to fix Rf
    sigmoid(opOut, outNet) # Add id numbers if parallel

    

def main():

    parser = argparse.ArgumentParser(prog = 'Analog LSTM Generator', description = 'This program is used to generate spice netlists to be used in Cadence\'s virtuoso. It sets all the memristors values from the weights.')
    parser.add_argument("-o", "--output", nargs='?', type=argparse.FileType("w"), default=sys.stdout, help="Specify an output file. The name of the file before '.' will be the name of the netlist.")


    args = parser.parse_args()
    
    global out
    out = args.output

    name = (out.name.split('.')[0]) 
    # Start writing the file
    header(name) 

    genInputXBar(1,4,"outputG")
    genInputXBar(1,4,"inputG")
    genInputXBar(1,4,"cellStateG")
    genInputXBar(1,4,"forgetG")

    # End of the file
    footer(name) 
    out.close()

if(__name__ == "__main__"):
    main()
