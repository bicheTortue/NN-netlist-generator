#!/usr/bin/env python3

import argparse
import sys
from itertools import count

def getResId(_resCount=count()):
    return next(_resCount)

def getNetId(_netCount=count()):
    return next(_netCount)

# Defining the different lines/modules
def header(module_name):
    out.write(".subckt " + module_name + "\n")

def footer(module_name):
    out.write(".ends " + module_name + "\n")

def resistor(name, minus, plus, value):
    if(type(value) == int):
        value=str(value)
    out.write("R" + name + " " + minus + " " + plus + " " + value + "\n")

def MOSFET(name, tType, drain, gate, source, bulk):
    out.write("M" + name + " " + drain + " " + gate + " " + source + " " + bulk + " " + tType + "\n")

def sigmoid(name, Vin, Vout, V1, V2, V3, idc, gnd, vdd):
    out.write("X" + name + " " + V1 + " " + V2 + " " + V3 + " " + Vin + " " + Vout + " " + gnd +" " + idc +" " + vdd + "sigmoid\n")

def tanh(name, Vin, Vout, V1, V2, V3, idc, gnd, vdd):
    out.write("X" + name + " " + V1 + " " + V2 + " " + V3 + " " + Vin + " " + Vout + " " + gnd +" " + idc +" " + vdd + "tanh\n")

def voltMult(name, in1, in2, out):
    out.write("X"+ name + " " + in1 + " " + in2 + " " + out + "voltageMult\n")

def opAmp(name, pin, nin, out):
    out.write("X"+ name + " " + nin + " " + out + " " + pin + "opAmp\n")

def memcell(name, inVal, enableIn, enableOut, out):
    out.write("X"+ name + " " + enableIn + " "  + enableOut + " " + inVal + " " + out + "opAmp\n")

def genMainXBar(nbIn,nbHid,nbOut):
    for i in range(nbOut):
        posWeight = str(getNetId())
        negWeight = str(getNetId())
        # Setting the input weights
        for j in range(nbIn):
            resistor(str(getResId()),"netIn"+str(j), posWeight, 100) # TODO : be able to choose between one or two opAmp
            resistor(str(getResId()),"netIn"+str(j), negWeight,100)
        # Setting the hidden weights
        for j in range(nbHid):
            resistor(str(getResId()),"netHid"+str(j), posWeight,10)
            resistor(str(getResId()),"netHid"+str(j), negWeight,10)
        # Setting the bias weights
        resistor(str(getResId()),"netBias", posWeight,10)
        resistor(str(getResId()),"netBias", negWeight,10)

def main():

    parser = argparse.ArgumentParser(prog = 'Analog LSTM Generator', description = 'This program is used to generate spice netlists to be used in Cadence\'s virtuoso. It sets all the memristors values from the weights.')
    parser.add_argument("-o", "--output", nargs='?', type=argparse.FileType("w"), default=sys.stdout, help="Specify an output file. The name of the file before '.' will be the name of the netlist.")


    args = parser.parse_args()
    
    global out
    out = args.output

    name = (out.name.split('.')[0]) 
    # Start writing the file
    header(name) 

    MOSFET("test","nch","1","2", "3","4")
    MOSFET("test","pch","1","2", "3","4")
    resistor("truc", "1", "2", "15000")

    genMainXBar(1,4,1)
    genMainXBar(1,4,1)
    genMainXBar(1,4,1)
    genMainXBar(1,4,1)

    # End of the file
    footer(name) 
    out.close()

if(__name__ == "__main__"):
    main()
