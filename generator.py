#!/usr/bin/env python3

import argparse
import pickle
import sys
import numpy as np
from itertools import count
from components import *

nmos = "nch"
pmos = "pch"
Rmin = 10**4
Rmax = 10**6
Rf = (Rmax + Rmin) / 2


def wei2res(w):
    Rpos = (w + 1 - np.sqrt(w**2 + 1)) * Rf / w
    Rpos = float("%.3g" % Rpos)
    Rneg = 2 * Rf - Rpos
    return (Rpos, Rneg)


def header(module_name):
    out.write(".subckt " + module_name + "\n")


def footer(module_name):
    out.write(".ends " + module_name + "\n")


def genXBar(lIn, nbOutput, serialSize, weights=None, peephole=False, isOld=True):
    outNets = []
    if weights is not None:
        weights = iter(weights)
    for j in range(nbOutput // serialSize):
        posCurOut = getNetId()
        negCurOut = getNetId()
        for i in range(serialSize):
            if serialSize == 1:
                posWeight = posCurOut
                negWeight = negCurOut
            else:
                posWeight = getNetId()
                negWeight = getNetId()
            # Setting the input weights
            for netIn in lIn:
                Rp, Rm = (100, 100) if weights is None else wei2res(next(weights))
                resistor(out, netIn, posWeight, Rp)
                resistor(out, netIn, negWeight, Rm)
            # Setting the bias weights
            Rp, Rm = (100, 100) if weights is None else wei2res(next(weights))
            resistor(out, "netBias", posWeight, Rp)
            resistor(out, "netBias", negWeight, Rm)
            if peephole:
                Rp, Rm = (100, 100) if weights is None else wei2res(next(weights))
                if isOld:
                    resistor(out, "cellStateOld" + str(j), posWeight, Rp)
                    resistor(out, "cellStateOld" + str(j), negWeight, Rm)
                else:
                    resistor(out, "cellStateCur" + str(j), posWeight, Rp)
                    resistor(out, "cellStateCur" + str(j), negWeight, Rm)
            if (
                    serialSize > 1
                    ):  # The CMOS switches are not necessary if the system is fully parallelized
                # Positive line CMOS Switch
                MOSFET(out, nmos, posWeight, "e" + str(i), posCurOut, posCurOut)
                MOSFET(out, pmos, posCurOut, "ne" + str(i), posWeight, posWeight)
                # Negative line CMOS Switch
                MOSFET(out, nmos, negWeight, "e" + str(i), negCurOut, negCurOut)
                MOSFET(out, pmos, negCurOut, "ne" + str(i), negWeight, negWeight)

        tmpOp1 = getNetId()
        # OpAmps to voltage again
        opAmp(out, "Vcm", posCurOut, tmpOp1)
        resistor(out, posCurOut, tmpOp1, "R")
        resistor(out, tmpOp1, negCurOut, "R")
        netOut = getNetId()
        outNets.append(netOut)
        opAmp(out, "Vcm", negCurOut, netOut)
        resistor(out, negCurOut, netOut, "Rf")
    return outNets


def genLSTMPointWise(outputNet, inputNet, cellStateNet, forgetNet, nbSerial, parNum):
    # Multiplication of C and input
    tmpNet = getNetId()
    voltMult(out, inputNet, cellStateNet, tmpNet)
    adderNet = getNetId()
    resistor(out, tmpNet, adderNet, "Ramp0")

    # Multiplication forget with old cell state
    tmpNet = getNetId()
    oldCellState = "cellStateOld" + str(parNum)
    voltMult(out, forgetNet, oldCellState, tmpNet)
    resistor(out, tmpNet, adderNet, "Ramp0")

    # opAmp adder
    postAddNet = "cellStateCur" + str(parNum)
    opAmp(out, "Vcm", adderNet, postAddNet)
    resistor(out, adderNet, postAddNet, "Ramp1")

    # Memory of the cell state
    tmpNet = getNetId()
    for i in range(nbSerial):
        memcell(out, postAddNet, tmpNet, "m" + str(i) + "p2", "m" + str(i) + "p1")
        # memcell(out,postAddNet, tmpNet, "e" + str(i), "nextT")
        # memcell(out,tmpNet, oldCellState, "nextT", "e" + str(i))
    capacitor(out, "0", tmpNet, "1P")
    buffer(out, tmpNet, oldCellState)

    # Old way, kept in case
    # memcell(out,postAddNet, oldCellState, "m" + str(i) + "p2", "m" + str(i) + "p1")

    # tanh activation function
    tmpNet = getNetId()
    tanh(out, postAddNet, tmpNet)
    # Code for buffer #
    tmpNet2 = getNetId()
    buffer(out, tmpNet, tmpNet2)
    tmpNet = tmpNet2
    ##################

    # Multiplication of last result and output gate
    tmpNet2 = getNetId()
    voltMult(out, outputNet, tmpNet, tmpNet2)

    # Multiplication by 10
    tmpNet = getNetId()
    resistor(out, tmpNet2, tmpNet, "Ramp0")
    hidNet = getNetId()
    opAmp(out, "Vcm", tmpNet, hidNet)
    resistor(out, tmpNet, hidNet, "Ramp1")
    return hidNet


def genPowerNSignals(nbInputs, timeSteps, serialSize, timeDib):
    vdc(out, "0", "vdd!", dc="vdd")
    vdc(out, "0", "Vcm", dc="vdd/2")
    vdc(out, "0", "V3t", dc=0.55)
    vdc(out, "0", "V3s", dc=0.8)
    vdc(out, "0", "V2", dc=0.635)
    vdc(out, "0", "V1", dc=1.1)
    vdc(out, "Vcm", "netBias", dc=0.1)

    vpulse(
            out,
            "0",
            "nextT",
            per="T*" + str(serialSize) + "+T/8",
            td="T*" + str(serialSize),
            pw="T/8",
            )
    if timeDib:
        perPred = '"(T*' + str(serialSize) + '+T/8)"'
    else:
        perPred = '"(T*' + str(serialSize) + "+T/8)*" + str(timeSteps) + '"'
    vpulse(
            out,
            "0",
            "predEn",
            td=perPred,
            per=perPred,
            pw="T/2",
            )
    vpulse(
            out,
            "0",
            "xbarEn",
            per="T*" + str(serialSize) + "+T/8",
            pw="T*" + str(serialSize),
            )
    for i in range(serialSize):
        vpulse(
                out,
                "0",
                "m" + str(i) + "p1",
                per="T*" + str(serialSize) + "+T/8",
                td=str(i) + "*T",
                pw="T/2-T/16",
                )
        vpulse(
                out,
                "0",
                "m" + str(i) + "p2",
                per="T*" + str(serialSize) + "+T/8",
                td=str(i) + "*T+T/2+T/16",
                pw="T/2-T/16",
                )
        vpulse(
                out,
                "0",
                "e" + str(i),
                per="T*" + str(serialSize) + "+T/8",
                td=str(i) + "*T",
                pw="T",
                )
        inverter(out, "e" + str(i), "ne" + str(i))
    for i in range(nbInputs):
        gndNet = "Vcm"  # Net on the ground side
        if timeSteps > 1:
            inNet = getNetId()  # Net on the input side
            for j in range(timeSteps):
                vpulse(
                        out,
                        gndNet,
                        inNet,
                        val1="in" + str(i) + "step" + str(j),
                        td='"(T*' + str(serialSize) + "+T/2)*" + str(j) + '"',
                        pw="T*" + str(serialSize),
                        )
                gndNet = inNet
                inNet = "netIn" + str(i) if j == timeSteps - 2 else getNetId()
        else:
            inNet = "netIn0"  # Net on the input side
            vpulse(
                    out,
                    gndNet,
                    inNet,
                    val1="in" + str(i) + "step" + str(j),
                    td='"(T*' + str(serialSize) + "+T/2)*" + str(j) + '"',
                    pw="T*" + str(serialSize),
                    )


def genGRU(listIn, nbHidden, weights=None):
    nbIn = len(listIn)
    vdc(out, "Vcm", "netInv", dc=0.05)

    for i in range(nbHidden):
        listIn.append("netHid" + str(i))

    predIn = []
    hidIndex = iter(range(nbHidden))

    updateNets = genXBar(listIn, nbHidden, 1, weights[0])
    resetNets = genXBar(listIn, nbHidden, 1, weights[1])
    listIn = listIn[:nbIn]
    for i in range(nbHidden):
        resetNet = "resetG" + str(i)
        tmpNet = getNetId()
        sigmoid(out, resetNets[i], tmpNet)
        buffer(out, tmpNet, resetNet)
        tmpNet = getNetId()
        voltMult(out, resetNet, "netHid" + str(i), tmpNet)
        tmpNet2 = getNetId()
        resistor(out, tmpNet, tmpNet2, "Ramp0")
        listIn.append(getNetId())
        opAmp(out, "Vcm", tmpNet2, listIn[nbIn + i])
        resistor(out, tmpNet2, listIn[nbIn + i], "Ramp1")
    cellNets = genXBar(listIn, nbHidden, 1, weights[2])

    for i in range(nbHidden):  # Also equal to parSize
        updateNet = "updateG" + str(i)
        tmpNet = getNetId()
        sigmoid(out, updateNets[i], tmpNet)
        buffer(out, tmpNet, updateNet)

        tmpNet = getNetId()
        nUpdateNet = "nUpdateG" + str(i)
        resistor(out, updateNet, tmpNet, "Ramp1")
        opAmp(out, "netInv", tmpNet, nUpdateNet)
        resistor(out, tmpNet, nUpdateNet, "Ramp1")

        cellNet = "cellG" + str(i)
        tmpNet = getNetId()
        tanh(out, cellNets[i], tmpNet)
        buffer(out, tmpNet, cellNet)

        tmpNet = getNetId()
        voltMult(out, "netHid" + str(i), nUpdateNet, tmpNet)
        adderNet = getNetId()
        resistor(out, tmpNet, adderNet, "Ramp0")

        tmpNet = getNetId()
        voltMult(out, cellNet, updateNet, tmpNet)
        resistor(out, tmpNet, adderNet, "Ramp0")

        # opAmp adder
        postAddNet = getNetId()
        opAmp(out, "Vcm", adderNet, postAddNet)
        resistor(out, adderNet, postAddNet, "Ramp1")

        # Memory cells for prediction NN
        # Memory cells for feedback
        curIndex = str(next(hidIndex))
        tmpNet = getNetId()
        predIn.append(tmpNet)
        memcell(
                out, postAddNet, tmpNet, "m" + str(i) + "p2", "predEn"
                )  # Prediction memcells
        # There are 2 of them not to override the values with-in a single LSTM step
        tmpNet = getNetId()
        memcell(out, postAddNet, tmpNet, "e" + str(i), "nextT")  # Feedback memcells
        memcell(out, tmpNet, "netHid" + curIndex, "nextT", "xbarEn")

    return predIn


def genLSTM(listIn, nbHidden, serialSize, weights=None):
    parSize = nbHidden // serialSize

    for i in range(nbHidden):
        listIn.append("netHid" + str(i))

    predIn = []
    hidIndex = iter(range(nbHidden))

    # Generate part of cell state gate
    cellStateNets = genXBar(listIn, nbHidden, serialSize, weights[2])
    # Generate part of input gate
    inputNets = genXBar(listIn, nbHidden, serialSize, weights[0])
    # Generate part of forget gate
    forgetNets = genXBar(listIn, nbHidden, serialSize, weights[1])
    # Generate part of output gate
    outputNets = genXBar(
            listIn,
            nbHidden,
            serialSize,
            weights[3],
            )

    for i in range(parSize):  # Also equal to parSize
        outputNet = "outputG" + str(i)
        inputNet = "inputG" + str(i)
        cellStateNet = "cellStateG" + str(i)
        forgetNet = "forgetG" + str(i)
        tmpNet = getNetId()
        sigmoid(out, inputNets[i], tmpNet)
        buffer(out, tmpNet, inputNet)
        tmpNet = getNetId()
        sigmoid(out, forgetNets[i], tmpNet)
        buffer(out, tmpNet, forgetNet)
        tmpNet = getNetId()
        tanh(out, cellStateNets[i], tmpNet)
        buffer(out, tmpNet, cellStateNet)
        tmpNet = getNetId()
        sigmoid(out, outputNets[i], tmpNet)
        buffer(out, tmpNet, outputNet)

        hiddenStateNet = genLSTMPointWise(
                outputNet, inputNet, cellStateNet, forgetNet, serialSize, i
                )

        # Memory cells for prediction NN
        # Memory cells for feedback
        for i in range(serialSize):
            # for _ in range(parSize):
            curIndex = str(next(hidIndex))
            tmpNet = getNetId()
            predIn.append(tmpNet)
            memcell(
                    out, hiddenStateNet, tmpNet, "m" + str(i) + "p2", "predEn"
                    )  # Prediction memcells
            # There are 2 of them not to override the values with-in a single LSTM step
            tmpNet = getNetId()
            memcell(
                    out, hiddenStateNet, tmpNet, "e" + str(i), "nextT"
                    )  # Feedback memcells
            memcell(out, tmpNet, "netHid" + curIndex, "nextT", "xbarEn")

    return predIn


def genDense(lIn, nbOutputs, weights=None):
    return genXBar(lIn, nbOutputs, 1, weights)


def main():
    parser = argparse.ArgumentParser(
            prog="Analog LSTM Generator",
            description="This python script that generates a SPICE netlist to be imported in Cadence's Virtuoso.",
            )
    parser.add_argument(
            "-m",
            "--model",
            nargs=1,
            type=str,
            default=None,
            help="Specify the file containing the model and its weights.",
            )
    parser.add_argument(
            "-o",
            "--output",
            nargs="?",
            type=argparse.FileType("w"),
            default=sys.stdout,
            help="Specify the output file. The name of the file before the extension will be the name of the netlist. (default : stdout)",
            )
    parser.add_argument(
            "-ni",
            "--number-input",
            default=1,
            type=int,
            help="Sets the number of inputs for the Neural Network. (default : %(default)s)",
            )
    parser.add_argument(
            "-ts",
            "--time-steps",
            default=1,
            type=int,
            help="Sets the number of time steps the input of the Recurrent Neural Network has. Only relevant if using Recurrent Neural Network. (default : %(default)s)",
            )
    parser.add_argument(
            "-ns",
            "--serial-size",
            default=1,
            type=int,
            help="Sets the amount of serial channel for the Neural Network. (default : %(default)s)",
            )
    parser.add_argument(
            default=1,
            type=int,
            )

    args = parser.parse_args()

    global out
    out = args.output

    with open(args.model[0], "rb") as file:
        tmp = pickle.load(file)
    arch, weights = tmp[0], tmp[1::]

    tmpNet = ["netIn" + str(i) for i in range(args.number_input)]

    name = out.name.split(".")[0]
    # Start writing the file
    header(name)

    for i, layer in enumerate(arch):
        if "Dense" in layer:
            timeDib = layer[0] == "t"
            nbOut = int(layer.split("(")[1].split(")")[0])
            tmpNet = genDense(tmpNet, nbOut, weights[i])
        elif "LSTM" in layer:
            nbHid = int(layer.split("(")[1].split(")")[0])
            if nbHid % args.serial_size != 0:
                print(
                        "The number of hidden states has to be a multiple of SERIAL_SIZE."
                        )
                exit()
            tmpNet = genLSTM(tmpNet, nbHid, args.serial_size, weights[i])
        elif "GRU" in layer:
            nbHid = int(layer.split("(")[1].split(")")[0])
            if args.serial_size != 1:
                print(
                        "The GRU architecture can only work in parallel mode, it cannot be serialized"
                        )
                exit()
            tmpNet = genGRU(tmpNet, nbHid, weights[i])

    genPowerNSignals(args.number_input, args.time_steps, args.serial_size, timeDib)

    print("\nThe prediction are outputed on", tmpNet)
    time = 8
    if timeDib:
        print(
                "They are",
                args.time_steps,
                "predictions outputed every",
                time * args.serial_size + time / 8,
                "micro seconds, starting at",
                (time * args.serial_size + time / 8) + time / 4,
                "micro seconds. Ending at",
                (time * args.serial_size + time / 8) * args.time_steps + time / 4,
                )
    else:
        print(
                "\nThe prediction are outputed at",
                (time * args.serial_size + time / 8) * args.time_steps + time / 4,
                "micro seconds",
                )

    footer(name)
    # End of the file
    out.close()


if __name__ == "__main__":
    main()
else:
    print(__name__)
