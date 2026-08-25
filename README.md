# AiiDA-NN-xTB
A streamlined AiiDA plugin built to automate high-throughput computational chemistry workflows for machine learning. This repository provides a seamless pipeline that takes raw SMILES strings, generates 3D molecular structures, executes quantum chemistry calculations via NN-xTB, and packages the resulting data into Zarr files ready for neural network training.

## Objective
The main goal of this project is to eliminate the manual bottleneck in building computational chemistry datasets. By leveraging AiiDA and WorkGraph, this pipeline ensures full data provenance and reproducibility while completely separating the data management from the heavy computations.

## Architecture
This workflow is designed for a distributed computing environment:
* **Local Management:** The PostgreSQL database and AiiDA profile run locally on a main lab machine. This handles the graphs, provenance tracking, and data storage.
* **Remote Execution:** The actual CPU/GPU intensive xTB calculations are offloaded to a remote compute server running Slurm. AiiDA daemon workers automatically handle job submission, queuing, and retrieval over SSH.

## Core Structure
The logic is broken down into modular tasks that are linked together using aiida-workgraph.
* `orchestrator.py`: The user-facing interactive launcher. It replaces traditional WorkChains, handles all user inputs via terminal prompts, and programmatically links all tasks into a massive parallel WorkGraph.
* `aiida_nn_xtb/smiles2structure.py`: Converts SMILES strings into AiiDA StructureData nodes.
* `aiida_nn_xtb/structure2xyz.py`: Formats the structures into XYZ files for the xTB executable.
* `aiida_nn_xtb/xyz2dict.py`: Parses the raw xTB outputs into structured Python dictionaries.
* `aiida_nn_xtb/dict2zarr.py`: Compiles the dictionaries into highly efficient Zarr arrays for machine learning.

## Installation & Setup
1. Make sure you have AiiDA installed and your profile configured.
2. Install the required dependencies: `pixi install`
3. Configure your remote Slurm server in AiiDA using `verdi computer setup` and set up passwordless SSH keys.
4. Configure your NN-xTB executable using `verdi code setup`.

## Usage
To launch a batch, simply run the orchestrator script:
`python orchestrator.py`

The script features interactive terminal prompts that will guide you through setting up the run. You will be asked for:
* Target AiiDA Group name
* Text file containing your SMILES strings
* Cluster code label (Default: xtb@localhost)
* Number of machines and processors per job
* Max wallclock time

### Tracking with the GUI
Because this pipeline leverages WorkGraph, you can easily track your batch progress and visualize your calculation nodes directly in your browser. Just ensure you are inside your pixi shell, and then start the web interface:

```bash
# Enter the environment if you haven't already
pixi shell

# Start the AiiDA web GUI
aiida-gui start