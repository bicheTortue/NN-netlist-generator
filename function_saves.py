def genXBar(lIn, lOut, serialSize): # NOTE : Might just have to change nbHid=1 to parallelize
    posCurOut = getNetId() # Because common, bring in to make parallel
    negCurOut = getNetId() 
    for netOut in lOut:
        for i in range(serialSize):
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

# Generate the whole neural network with activation function
def genInputXBar(nbIn,nbHid,outNet): # NOTE : Might just have to change nbHid=1 to parallelize
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
