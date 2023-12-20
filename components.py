from itertools import count


# Generate a new wire
def getNetId(_netCount=count()):
    return "net" + str(next(_netCount))


# This file contains all the components used by the netlist generator
def resistor(out, minus, plus, value, _id=count()):
    if type(value) != str:
        value = str(value)
    out.write("R" + str(next(_id)) + " " + plus + " " + minus + " " + value + "\n")


def capacitor(out, minus, plus, value, _id=count()):
    if type(value) != str:
        value = str(value)
    out.write("C" + str(next(_id)) + " " + plus + " " + minus + " " + value + "\n")


def MOSFET(out, tType, drain, gate, source, bulk, _id=count()):
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


def sigmoid(out, Vin, Vout, _id=count()):
    tmpNet = getNetId()
    idc(out, tmpNet, "vdd!", dc="150u")
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


def tanh(out, Vin, Vout, _id=count()):
    tmpNet = getNetId()
    idc(out, tmpNet, "vdd!", dc="150u")
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


def voltMult(out, in1, in2, outPin, _id=count()):
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


def opAmp(out, pin, nin, outPin, _id=count()):
    out.write(
        "XopAmp" + str(next(_id)) + " " + nin + " " + outPin + " " + pin + " opAmp\n"
    )


def buffer(out, inPin, outPin, _id=count()):
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


def inverter(out, inPin, outPin, _id=count()):
    out.write(
        "Xinverter" + str(next(_id)) + " 0 " + inPin + " " + outPin + " vdd! inverter\n"
    )


def memcell(out, inPin, outPin, enableIn, enableOut, _id=count()):
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
def vpulse(out, minus, plus, dc=0, val0=0, val1="vdd", per=0, pw=0, td=0, _id=count()):
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


def vdc(out, minus, plus, dc=0, _id=count()):
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


def idc(out, minus, plus, dc=0, _id=count()):
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
