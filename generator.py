#!/usr/bin/env python3

import argparse
import pickle
import sys
import numpy as np
from itertools import count

nmos = "nch"
pmos = "pch"
Rmin = 10**4
Rmax = 10**6
Rf = (Rmax + Rmin) / 2


def getNetId(_netCount=count()):
    return "net" + str(next(_netCount))


def wei2res(w):
    Rpos = (w + 1 - np.sqrt(w**2 + 1)) * Rf / w
    Rpos = float("%.2g" % Rpos)
    Rneg = 2 * Rf - Rpos
    return (Rpos, Rneg)


# Defining the different lines/modules


def header(module_name):
    out.write(".subckt " + module_name + "\n")


def footer(module_name):
    out.write(".ends " + module_name + "\n")


def resistor(minus, plus, value, _id=count()):
    if type(value) != str:
        value = str(value)
    out.write("R" + str(next(_id)) + " " + minus + " " + plus + " " + value + "\n")


def MOSFET(tType, drain, gate, source, bulk, _id=count()):
    out.write(
        "M"
        + str(next(_id))
        + " "
        + drain
        + " "
        + gate
        + " "
        + source
        + " "
        + bulk
        + " "
        + tType
        + "\n"
    )


def sigmoid(Vin, Vout, _id=count()):
    tmpNet = getNetId()
    idc(tmpNet, "vdd!", dc="150u")
    out.write(
        "Xsig"
        + str(next(_id))
        + " V1 V2 V3s "
        + Vin
        + " "
        + Vout
        + " 0 "
        + tmpNet
        + " vdd! sigmoid\n"
    )


def tanh(Vin, Vout, _id=count()):
    tmpNet = getNetId()
    idc(tmpNet, "vdd!", dc="150u")
    out.write(
        "Xtanh"
        + str(next(_id))
        + " V1 V2 V3t "
        + Vin
        + " "
        + Vout
        + " 0 "
        + tmpNet
        + " vdd! tanh\n"
    )


def voltMult(in1, in2, outPin, _id=count()):
    out.write(
        "XvoltMult"
        + str(next(_id))
        + " "
        + in1
        + " "
        + in2
        + " "
        + outPin
        + " voltageMult\n"
    )


def opAmp(pin, nin, outPin, _id=count()):
    out.write(
        "XopAmp" + str(next(_id)) + " " + nin + " " + outPin + " " + pin + " opAmp\n"
    )


def voltInv(inPin, outPin, _id=count()):
    tmpNet = getNetId()
    res = 10**5
    resistor(inPin, tmpNet, res)
    resistor(tmpNet, outPin, res)
    out.write(
        "XvoltInv" + str(next(_id)) + " " + tmpNet + " " + outPin + " Vcm opAmp\n"
    )


def buffer(inPin, outPin, _id=count()):
    out.write(
        "Xbuffer"
        + str(next(_id))
        + " "
        + outPin
        + " "
        + outPin
        + " "
        + inPin
        + " opAmp\n"
    )


def inverter(inPin, outPin, _id=count()):
    out.write(
        "Xinverter" + str(next(_id)) + " 0 " + inPin + " " + outPin + " vdd! inverter\n"
    )


def memcell(inPin, outPin, enableIn, enableOut, _id=count()):
    out.write(
        "Xmemcell"
        + str(next(_id))
        + " "
        + enableIn
        + " "
        + enableOut
        + " 0 "
        + inPin
        + " "
        + outPin
        + " vdd! memcell\n"
    )


# Ideal sources
def vpulse(minus, plus, dc=0, val0=0, val1="vdd", per=0, pw=0, td=0, _id=count()):
    out.write(
        "Vpulse"
        + str(next(_id))
        + " "
        + plus
        + " "
        + minus
        + " DC="
        + str(dc)
        + " srcType=pulse val0="
        + str(val0)
        + " val1="
        + str(val1)
        + " per="
        + str(per)
        + " pw="
        + str(pw)
        + " td="
        + str(td)
        + "\n"
    )


def vdc(minus, plus, dc=0, _id=count()):
    out.write(
        "Vdc"
        + str(next(_id))
        + " "
        + plus
        + " "
        + minus
        + " DC="
        + str(dc)
        + " srcType=dc\n"
    )


# Real sources
def vpulseReal(minus, plus, dc=0, val0=0, val1="vdd", per=0, pw=0, td=0, _id=count()):
    tmpNet = getNetId()
    out.write(
        "Vpulse"
        + str(next(_id))
        + " "
        + tmpNet
        + " "
        + minus
        + " DC="
        + str(dc)
        + " srcType=pulse val0="
        + str(val0)
        + " val1="
        + str(val1)
        + " per="
        + str(per)
        + " pw="
        + str(pw)
        + " td="
        + str(td)
        + "\n"
    )
    resistor(tmpNet, plus, 10)


def vdcReal(minus, plus, dc=0, _id=count()):
    tmpNet = getNetId()
    out.write(
        "Vdc"
        + str(next(_id))
        + " "
        + tmpNet
        + " "
        + minus
        + " DC="
        + str(dc)
        + " srcType=dc\n"
    )
    resistor(tmpNet, plus, 10)


def idc(minus, plus, dc=0, _id=count()):
    out.write(
        "Idc"
        + str(next(_id))
        + " "
        + plus
        + " "
        + minus
        + " DC="
        + str(dc)
        + " srcType=dc\n"
    )


def genXBar(lIn, nbOutput, serialSize, weights=None):
    outNets = []
    if weights is not None:
        weights = iter(weights)
    for _ in range(nbOutput // serialSize):
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
                # TODO : be able to choose between one or two opAmp/Weights
                resistor(netIn, posWeight, Rp)
                resistor(netIn, negWeight, Rm)
            # Setting the bias weights
            Rp, Rm = (100, 100) if weights is None else wei2res(next(weights))
            resistor("netBias", posWeight, Rp)
            resistor("netBias", negWeight, Rm)
            if (
                serialSize > 1
            ):  # The CMOS switches are not necessary if the system is fully parallelized
                # Positive line CMOS Switch
                MOSFET(nmos, posWeight, "e" + str(i), posCurOut, posCurOut)
                MOSFET(pmos, posCurOut, "ne" + str(i), posWeight, posWeight)
                # Negative line CMOS Switch
                MOSFET(nmos, negWeight, "e" + str(i), negCurOut, negCurOut)
                MOSFET(pmos, negCurOut, "ne" + str(i), negWeight, negWeight)

        tmpOp1 = getNetId()
        # OpAmps to voltage again
        opAmp("Vcm", posCurOut, tmpOp1)
        resistor(posCurOut, tmpOp1, "R")
        resistor(tmpOp1, negCurOut, "R")
        netOut = getNetId()
        outNets.append(netOut)
        opAmp("Vcm", negCurOut, netOut)
        resistor(negCurOut, netOut, "Rf")
    return outNets


def genPointWise(outputNet, inputNet, cellStateNet, forgetNet, nbSerial, parNum):
    # Multiplication of C and input
    tmpNet = getNetId()
    voltMult(inputNet, cellStateNet, tmpNet)
    # Code for buffer #
    tmpNet2 = getNetId()
    voltInv(tmpNet, tmpNet2)
    tmpNet = tmpNet2
    ##################
    adderNet = getNetId()
    resistor(tmpNet, adderNet, "R1")

    # Multiplication with old cell state
    tmpNet = getNetId()
    oldCellState = "cellStateOld" + str(parNum)
    voltMult(forgetNet, oldCellState, tmpNet)
    # Code for buffer #
    tmpNet2 = getNetId()
    voltInv(tmpNet, tmpNet2)
    tmpNet = tmpNet2
    ##################
    resistor(tmpNet, adderNet, "R1")

    # opAmp adder
    postAddNet = "cellStateCur" + str(parNum)
    tmpNet = getNetId()
    opAmp("Vcm", adderNet, postAddNet)
    resistor(adderNet, postAddNet, "R2")
    # voltInv(tmpNet, postAddNet)

    # Memory of the cell state
    for i in range(nbSerial):
        tmpNet = getNetId()
        memcell(postAddNet, tmpNet, "m" + str(i) + "p2", "nextT")
        memcell(tmpNet, oldCellState, "nextT", "e" + str(i))
        # Old way, kept in case
        # memcell(postAddNet, oldCellState, "m" +str(i) + "p2", "m" + str(i) + "p1")

    # tanh activation function
    tmpNet = getNetId()
    tanh(postAddNet, tmpNet)
    # Code for buffer #
    tmpNet2 = getNetId()
    buffer(tmpNet, tmpNet2)
    tmpNet = tmpNet2
    ##################

    # Multiplication of last result and output gate
    tmpNet2 = getNetId()
    voltMult(outputNet, tmpNet, tmpNet2)
    # Code for buffer #
    tmpNet = getNetId()
    voltInv(tmpNet2, tmpNet)
    tmpNet2 = tmpNet
    ##################

    # Multiplication by 10
    tmpNet = getNetId()
    resistor(tmpNet2, tmpNet, "R3")
    hidNet = getNetId()
    opAmp("Vcm", tmpNet, hidNet)
    resistor(tmpNet, hidNet, "R4")
    # voltInv(tmpNet2, hidNet)
    return hidNet


def genPowerNSignals(
    nbInputs, timeSteps, serialSize
):  # NOTE : Find out if should be set here or in cadence
    vdc("0", "vdd!", dc="vdd")
    vdc("0", "Vcm", dc="vdd/2")
    # vdc("0", "V3t", dc=0.55)
    # vdc("0", "V3s", dc=0.8)
    # vdc("0", "V2", dc=0.635)
    # vdc("0", "V1", dc=1.1)
    vdc("0", "V3t", dc="V3t")
    vdc("0", "V3s", dc="V3s")
    vdc("0", "V2", dc="V2")
    vdc("0", "V1", dc="V1")
    # Sourcing on Vcm for the vdd/2 is it right?
    vdc("Vcm", "netBias", dc=0.1)
    # needs to be connected to each device (loi des noeuds debilos)
    # idc("idc", "vdd!", dc="150u")

    # TODO : Check whether T/20 is enough time for the data to move from one memcell to another
    vpulse(
        "0",
        "nextT",
        per="T*" + str(serialSize) + "+T/8",
        td="T*" + str(serialSize),
        pw="T/8",
    )
    vpulse(
        "0",
        "predEn",
        td='"(T*' + str(serialSize) + "+T/8)*" + str(timeSteps) + '"',
        pw="T/2",
    )  # TODO : probably change pulse width # TODO : Check if necessary to have a small break in between (might hurt other calcs)
    vpulse(
        "0", "xbarEn", per="T*" + str(serialSize) + "+T/8", pw="T*" + str(serialSize)
    )
    for i in range(serialSize):
        vpulse(
            "0",
            "m" + str(i) + "p1",
            per="T*" + str(serialSize) + "+T/8",
            td=str(i) + "*T",
            pw="T/2-T/16",
        )
        vpulse(
            "0",
            "m" + str(i) + "p2",
            per="T*" + str(serialSize) + "+T/8",
            td=str(i) + "*T+T/2",
            pw="T/2-T/16",
        )
        vpulse(
            "0",
            "e" + str(i),
            per="T*" + str(serialSize) + "+T/8",
            td=str(i) + "*T",
            pw="T",
        )
        inverter("e" + str(i), "ne" + str(i))
    # Inputs
    # trying to use Vcm as common
    # vdc("0", inNet, dc="vdd/2")
    for i in range(nbInputs):
        gndNet = "Vcm"  # Net on the ground side
        inNet = getNetId()  # Net on the input side
        for j in range(timeSteps):
            vpulse(
                gndNet,
                inNet,
                val1="in" + str(i) + "step" + str(j),
                td='"(T*' + str(serialSize) + "+T/2)*" + str(j) + '"',
                pw="T*" + str(serialSize),
            )
            gndNet = inNet
            # needs to be fixed, doesn't work for one time step
            inNet = "netIn" + str(i) if j == timeSteps - 2 else getNetId()
    # add small delay to set all memcells
    # Harder than I thought


def genLSTM(listIn, nbHidden, serialSize, typeLSTM="NP", weights=None):
    parSize = nbHidden // serialSize
    isFGR = typeLSTM == "FGR"
    isVanilla = typeLSTM == "Vanilla"

    for i in range(nbHidden):
        listIn.append("netHid" + str(i))
    if isFGR:
        listFGR = []
        listFGR.append(["o" + str(i) for i in range(nbHidden)])
        listFGR.append(["i" + str(i) for i in range(nbHidden)])
        listFGR.append(["f" + str(i) for i in range(nbHidden)])

    predIn = []
    hidIndex = iter(range(nbHidden))

    if isFGR:
        listIn.append("cellStateOld")
        for l in listFGR:
            listIn.extend(l)
    if isVanilla:
        listIn.append("cellStateOld")
    # Generate part of input gate
    inputNets = genXBar(listIn, nbHidden, serialSize, weights[0])
    # Generate part of forget gate
    forgetNets = genXBar(listIn, nbHidden, serialSize, weights[1])
    if isVanilla:
        listIn.pop()
    if isFGR:
        listIn = listIn[: -(3 * nbHidden + 1)]
    # Generate part of cell state gate
    cellStateNets = genXBar(listIn, nbHidden, serialSize, weights[2])
    # Generate part of output gate
    if isFGR:
        listIn.append("cellStateOld")
        for l in listFGR:
            listIn.extend(l)
    if isVanilla:
        listIn.append("cellStateCur")
    outputNets = genXBar(listIn, nbHidden, serialSize, weights[3])

    for i in range(parSize):  # Also equal to parSize
        outputNet = "outputG" + str(i)
        inputNet = "inputG" + str(i)
        cellStateNet = "cellStateG" + str(i)
        forgetNet = "forgetG" + str(i)
        tmpNet = getNetId()
        sigmoid(inputNets[i], tmpNet)
        buffer(tmpNet, inputNet)
        tmpNet = getNetId()
        sigmoid(forgetNets[i], tmpNet)
        buffer(tmpNet, forgetNet)
        tmpNet = getNetId()
        tanh(cellStateNets[i], tmpNet)
        buffer(tmpNet, cellStateNet)
        tmpNet = getNetId()
        sigmoid(outputNets[i], tmpNet)
        buffer(tmpNet, outputNet)

        hiddenStateNet = genPointWise(
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
                hiddenStateNet, tmpNet, "m" + str(i) + "p2", "predEn"
            )  # Prediction memcells
            tmpNet = getNetId()
            memcell(
                hiddenStateNet, tmpNet, "m" + str(i) + "p2", "nextT"
            )  # Feedback memcells
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

    return predIn


def genDense(lIn, nbOutputs, weights=None):
    return genXBar(lIn, nbOutputs, 1, weights)


def main():
    parser = argparse.ArgumentParser(
        prog="Analog LSTM Generator",
        description="This program is used to generate spice netlists to be used in Cadence's virtuoso. It sets all the memristors values from the weights.",
    )
    parser.add_argument(
        "-m",
        "--model",
        nargs=1,
        type=argparse.FileType("w"),
        default=None,
        help="Specify a file containing the model and its weights.",
    )
    parser.add_argument(
        "-o",
        "--output",
        nargs="?",
        type=argparse.FileType("w"),
        default=sys.stdout,
        help="Specify an output file. The name of the file before the extension will be the name of the netlist.",
    )
    parser.add_argument(  # Change to bool ?
        "type",
        default="NP",
        choices=["NP", "Vanilla", "GRU", "FGR"],
        help="Choose which LSTM architecture will be generated.",
    )
    parser.add_argument(
        "-ni",
        "--number_input",
        default=1,
        type=int,
        help="Choose the number of inputs for the LSTM. Default : 1",
    )
    parser.add_argument(
        "-no",
        "--number_output",
        default=1,
        type=int,
        help="Choose the number of outputs for the overall circuit. Default : 1",
    )
    parser.add_argument(
        "-ts",
        "--time_steps",
        default=1,
        type=int,
        help="Choose the number of time steps the input of the LSTM has. Default : 1",
    )
    parser.add_argument(
        "-ns",
        "--serial_size",
        default=4,
        type=int,
        help="Choose the amount of serial channel for the LSTM. An LSTM time step will become SERIAL_SIZE times longer. Default : 4 (This value has to divide the number of hidden states)",
    )

    args = parser.parse_args()

    global out
    out = args.output

    if args.weights is None:
        weights = [None for i in range(10)]
        # Placeholder until I figure out how to specify architecture
    else:
        with open("all.wei", "rb") as file:
            tmp = pickle.load(file)
            arch, weights = tmp[0], tmp[1::]

    tmpNet = ["netIn" + str(i) for i in range(args.number_input)]

    name = out.name.split(".")[0]
    # Start writing the file
    header(name)

    for i, layer in enumerate(arch):
        if "Dense" in layer:
            nbOut = int(layer.split("(")[1].split(")")[0])
            tmpNet = genDense(tmpNet, nbOut, weights[i])
        elif "LSTM" in layer:
            nbHid = int(layer.split("(")[1].split(")")[0])
            if nbHid % args.serial_size != 0:
                print(
                    "The number of hidden states has to be a multiple of SERIAL_SIZE."
                )
                exit()
            tmpNet = genLSTM(tmpNet, nbHid, args.serial_size, args.type, weights[i])

    genPowerNSignals(args.number_input, args.time_steps, args.serial_size)

    print("\nThe prediction are outputed on", tmpNet)

    footer(name)
    # End of the file
    out.close()


if __name__ == "__main__":
    main()
else:
    print(__name__)
