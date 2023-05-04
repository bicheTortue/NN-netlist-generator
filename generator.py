#!/usr/bin/env python3

import argparse
import sys



def header(module_name):
    print(".subckt " + module_name)
    out.write(".subckt " + module_name+ "\n")

def footer(module_name):
    print(".ends " + module_name)

def main():

    parser = argparse.ArgumentParser(prog = 'Analog LSTM Generator', description = 'This program is used to generate spice netlists to be used in Cadence\'s virtuoso. It sets all the memristors values from the weights.')
    parser.add_argument("-o", "--output", nargs='?', type=argparse.FileType("w"), default=sys.stdout, help="Specify an output file.")


    args = parser.parse_args()
    
    global out
    out = args.output

    header("testouille") 

if(__name__ == "__main__"):
    main()
