# Netlist generator for memristor-based Neural Networks

This is a python script that generates a SPICE netlist to be imported in Cadence's Virtuoso. The netlist describes the circuit of an analog computer capable of running Neural Networks. This repo is a companion of my [master thesis](https://github.com/bicheTortue/MSc-thesis/releases/download/Final/thesis.pdf).


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

| Short | Long | Default | Description |
|:-----:|:----------:|:--------:|-------------------------------------------------------------------------------------------------------------------------------|
|`-h`|`--help`||Show help message and exit.|
|`-m`|`--model`||Specify the file containing the model and its weights.|
|`-o`|`--output`|<stdout>|Specify the output file. The name of the file before the extension will be the name of the netlist.|
|`-ni`|`--number-input`|1|Sets the number of inputs for the Neural Network.|
|`-ts`|`--time-steps`|1|Sets the number of time steps the input of the Recurrent Neural Network has. Only relevant if using Recurrent Neural Network.|
|`-ns`|`--serial-size`|1|Sets the amount of serial channel for the Neural Network.|

## Features

It generates the netlist based on a file (generated using the scripts available [here](../../../weights-generator)) containing the Neural Network configuration and the weights associated as described in the [thesis](https://github.com/bicheTortue/MSc-thesis/releases/download/Final/thesis.pdf).

The script supports the following Neural Network layers :

- Dense layers
- Time distributed dense layers
- LSTM layers
- GRU layers (WIP)


## Importing

Importing the netlist in Cadence's Virtuoso requires the following steps :

- From the console window, select `File` in the toolbar.
- Then select `Import`, then `Spice...`.
- From the `Spice In` window select `load` from the bottom of the window.
- Select the [`spiceIn.params`](../../../cadence-files/blob/main/spiceIn.params) file from the [Cadence files](../../../cadence-files) repo and select `open`.
- Choose your netlist from the `Netlist File` file picker.
- From the `Output` tab, select the `Output Library` which the schematic will be part of.
- Then select `OK` at the bottom of the window.

## License

This project is licensed under the General Public License, version 3.0 or later - see the [COPYING](./COPYING) file for details.
