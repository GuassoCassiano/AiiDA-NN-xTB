# Architecture Overview
This repository contains an automated AiiDA pipeline developed for the Seonah Kim Group. It is designed to take raw SMILES strings, generate 3D molecular structures using RDKit, optimize them, and run them through NN-xTB to extract converged energies.

## What is AiiDA?
Within this project, AiiDA is a workflow manager used to make the downstream of our NN-xTB calculations easier to track and manage. 

This project was designed with a couple bigger goals in mind:
* Automating the transition from SMILES strings to NN-xTB calculations
* Creating a system to queue & distribute calculations to different computing clusters 
* Ease of tracking errors and calculation progress
* Creating a hub for easier tracking & querying of results

## Structure
This project follows a relatively streamlined process. We take raw SMILES strings as an input and push them through a highly modular, six-part Python architecture. 

*(Note: Please excuse the graphic design skills below. I am an engineer, not an artist, but this maps out the general data flow!)*

![A highly professional, totally not cobbled together architecture diagram](assets/aiida_nn_xtb_diagram.svg)

The pipeline is physically broken down into the following files, which are executed in this general chronological order:

1. **The Launcher (`submit_batch.py`):** The user-facing ignition switch. It sits completely outside the AiiDA engine, takes our target molecules, organizes an AiiDA Group, and feeds the inputs to the daemon.
2. **The WorkChain (`workchain.py`):** The automated AiiDA recipe. It receives the SMILES string and asynchronously orchestrates the next three steps while tracking the data provenance. 
3. **The 3D Generator (`smiles2structure.py`):** Converts the 1D string into an optimized 3D geometry with a dynamic bounding box to satisfy AiiDA's StructureData requirements.
4. **The Wrapper (`structure2xyz.py`):** Translates the AiiDA node into a strictly formatted XYZ file and sends the execution commands to the remote cluster.
5. **The Parser (`xyz2dict.py`):** Hunts through the raw text output from the cluster using Regex and securely saves the final total energy to the database.
6. **The Exporter (`dict2zarr.py`):** The final extraction tool. It queries the database for successful WorkChains and packages the 3D coordinates and energies into high-performance OpenQDC Zarr arrays.