# EGGS_labrad

The EGGS LabRAD repository is the main repository for control of the EGGS experiment at UCLA.
Our experiment uses LabRAD to interface our devices, schedule experimental sequences, and manage data.

In essence, EGGS_LabRAD is a kind of wrapper for pylabrad that adds a lot of convenient
and useful tools and functionality.

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

A LabRAD system is composed of one or more computers on a shared network with a single LabRAD master
running on one of the computers.

Command line tools are included to simplify the process of initializing a LabRAD system;
these can be found in our binaries folder.

### LabRAD Master

A LabRAD master manages the connections between servers, clients, and nodes.

Only one LabRAD master can run at a time on the entire system.

To run a LabRAD master, go to the command line and enter

```commandline
    labrad_master
```

This starts up the LabRAD manager, a LabRAD node, and the LabRAD Chromium GUI.

### LabRAD node

A LabRAD node manages the connection to the LabRAD master, other nodes, and facilitates
the launching of local servers.

Only one LabRAD node can be run at a time on an individual computer.

To run a LabRAD node, go to the command line and enter

```commandline
    labrad_node
```

This starts up a LabRAD node and the LabRAD Chromium GUI.

## ARTIQ

Since our experiment uses ARTIQ (mainly to handle all of our pulse sequencing), EGGS_labrad contains
a "bridge" between ARTIQ and LabRAD which basically just makes essential ARTIQ stuff accessible via LabRAD.
We also have an ARTIQ Server which breaks out control over individual devices, similar to MonInj in ARTIQ.

