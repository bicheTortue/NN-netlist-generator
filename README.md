# Netlist generator for memristor-based Neural Networks

This is a python script that generates a SPICE netlist to be imported in Cadence's Virtuoso. The netlist describes the circuit of an analog computer capable of running Neural Networks. This repo is a companion of my [master thesis](todo).


## Table of Contents

- [Usage](#usage)

- [Features](#features)

- [Importing](#importing)

- [License](#license)


## Usage



## Features

    It generates the netlist based on a file (generated using [the other repo](../LSTM-weights-generator)) containing the Neural Network configuration and the weights associated as described in the [thesis](todo).

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
