# Netlist generator for memristor-based Neural Networks

This is a python script that generates a SPICE netlist to be imported in Cadence's Virtuoso. The netlist describes the circuit of an analog computer capable of running Neural Networks. This repo is a companion of my [master thesis](todo).


## Table of Contents

- [Usage](#usage)

- [Features](#features)

- [Importing](#importing)

- [License](#license)


## Usage

```bash
usage: Analog LSTM Generator [-h] [-m MODEL] [-o [OUTPUT]] [-ni NUMBER_INPUT] [-ts TIME_STEPS] [-ns SERIAL_SIZE]
```

### Arguments

| Short | Long       | Default  | Description                                                                                                                   |
|:-----:|:----------:|:--------:|-------------------------------------------------------------------------------------------------------------------------------|
|`-h`|`--help`||Show help message and exit.|
|`-m`|`--model`||Specify the file containing the model and its weights.|
|`-o`|`--output`|<stdout>|Specify the output file. The name of the file before the extension will be the name of the netlist.|
|`-ni`|`--number-input`|1|Sets the number of inputs for the Neural Network.|
|`-ts`|`--time-steps`|1|Sets the number of time steps the input of the Recurrent Neural Network has. Only relevant if using Recurrent Neural Network.|
|`-ns`|`--serial-size`|1|Sets the amount of serial channel for the Neural Network.|

## Features

It generates the netlist based on a file (generated using [the other repo](../../../LSTM-weights-generator)) containing the Neural Network configuration and the weights associated as described in the [thesis](todo).

The script supports the following Neural Network layers :

- Dense layers

- Time distributed dense layers

- LSTM layers

- GRU layers (WIP)


## Importing

Importing the netlist in Cadence's Virtuoso requires the following steps :

- File

TODO : check

## License

This project is licensed under the General Public License, version 3.0 or later - see the [COPYING](./COPYING) file for details.
