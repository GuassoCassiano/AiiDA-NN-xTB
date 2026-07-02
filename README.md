# AiiDA-NN-xTB

A streamlined AiiDA plugin built to automate high-throughput computational chemistry workflows for machine learning. 

This repository provides a seamless pipeline that takes raw SMILES strings, generates 3D molecular structures, executes  quantum chemistry calculations via NN-xTB, and packages the resulting data into Zarr files ready for neural network training.

## Objective
The main goal of this project is to eliminate the manual bottleneck in building computational chemistry datasets. By leveraging AiiDA and WorkGraph, this pipeline ensures full data provenance and reproducibility while completely separating the data management from the heavy computations.

## Architecture
This workflow is designed for a distributed computing environment:
* Local Management: The PostgreSQL database and AiiDA profile run locally on a main lab machine. This handles the graphs, provenance tracking, and data storage.
* Remote Execution: The actual CPU/GPU intensive xTB calculations are offloaded to a remote compute server running Slurm. AiiDA daemon workers automatically handle job submission, queuing, and retrieval over SSH.

## Core Structure
The logic is broken down into modular tasks that are linked together using aiida-workgraph.

* aiida_nn_xtb/workgraph.py: The brain of the operation. This replaces traditional WorkChains and programmatically links all the tasks below while generating a visual graph of your workflow.
* aiida_nn_xtb/smiles2structure.py: Converts SMILES strings into AiiDA StructureData nodes.
* aiida_nn_xtb/structure2xyz.py: Formats the structures into XYZ files for the xTB executable.
* aiida_nn_xtb/xyz2dict.py: Parses the raw xTB outputs into structured Python dictionaries.
* aiida_nn_xtb/dict2zarr.py: Compiles the dictionaries into highly efficient Zarr arrays for machine learning.
* submit_batch.py: A utility script to fire off massive batches of SMILES strings to the remote server at once.

## Installation & Setup

1. Make sure you have AiiDA installed and your profile configured.
2. Install the required dependencies:
`pixi install`
3. Configure your remote Slurm server in AiiDA using `verdi computer setup` and set up passwordless SSH keys.
4. Configure your NN-xTB executable using `verdi code setup`.