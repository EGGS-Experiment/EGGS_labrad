# EGGS_labrad

The EGGS LabRAD repository is the main repository for control of the EGGS experiment at UCLA.
Our experiment uses LabRAD to interface our devices, schedule experimental sequences, and manage data.

This repository contains all the servers, clients, and experimental sequences that are part of the EGGS experiment,
as well as a simplified programming environment for creating LabRAD tools.

## Installation

Use of the code in this repository requires a LabRAD manager/system to already be installed.
For instructions and resources on installing LabRAD, see our [wiki](https://github.com/EGGS-Experiment/EGGS_labrad/wiki/Resources).

To deal with all the required packages (of which there are many) and their concomitant dependencies,
a package manager is needed. Since we are beta males who use Windows, we use Conda.

A .yml file containing all of the packages we use can be found in the env folder.
The required conda environment for our code can be created from this .yml file using the following command:

```commandline
    conda env create --file labart_MONGKOK.yml
```

## Use

Command line tools are included to simplify the process of initializing a LabRAD system;
these can be found in our binaries folder.

For example, running

```commandline
    labrad_master -s
```

starts up the LabRAD manager, a LabRAD node, core device servers,
all experimental control servers, and all device servers.

## ARTIQ

Since our experiment uses ARTIQ (mainly to handle all of our pulse sequencing), EGGS_labrad contains
a "bridge" between ARTIQ and LabRAD which basically just makes essential ARTIQ stuff accessible via LabRAD.
We also have an ARTIQ Server which breaks out control over individual devices, similar to MonInj in ARTIQ.

