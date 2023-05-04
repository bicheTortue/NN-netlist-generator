#!/usr/bin/env python3

import argparse
import sys

# Defining the different lines/modules
def header(module_name):
    out.write(".subckt " + module_name + "\n")

def footer(module_name):
    out.write(".ends " + module_name + "\n")

def resistor(name, minus, plus, value):
    out.write("R" + name + " " + minus + " " + plus + " " + value + "\n")

def MOSFET(name, tType, drain, gate, source, bulk):
    out.write("M" + name + " " + drain + " " + gate + " " + source + " " + bulk + " " + tType + "\n")

def sigmoid(name, Vin, Vout, V1, V2, V3, idc, gnd, vdd):
    out.write("X" + name + " " + V1 + " " + V2 + " " + V3 + " " + Vin + " " + Vout + " " + gnd +" " + idc +" " + vdd + "sigmoid\n")

def tanh(name, Vin, Vout, V1, V2, V3, idc, gnd, vdd):
    out.write("X" + name + " " + V1 + " " + V2 + " " + V3 + " " + Vin + " " + Vout + " " + gnd +" " + idc +" " + vdd + "tanh\n")

# def voltMult

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
    resistor("truc", "net1", "net2", "15000")

    # End of the file
    footer(name) 
    out.close()

if(__name__ == "__main__"):
    main()
