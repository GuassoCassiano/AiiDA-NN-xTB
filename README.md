# AiiDA-NN-xTB Pipeline

## Overview
This repository contains an automated AiiDA pipeline developed for the Seonah Kim Group. It is designed to take raw SMILES strings, generate 3D molecular structures using RDKit, optimize them, and run them through NN-xTB to extract converged energies. 

## Pipeline Architecture
1. **SMILES to Structure:** Converts SMILES strings to 3D optimized AiiDA StructureData.
2. **CalcJob Wrapper:** Translates AiiDA structures into strictly formatted XYZ files.
3. **Execution:** Submits the calculation to the remote cluster via AiiDA.
4. **Parser:** Extracts total energy from the NN-xTB output.
5. **OpenQDC Exporter:** Packages the final arrays into high-performance `.zarr` files for machine learning ingestion.

## Installation
This project uses [Pixi](https://pixi.sh) for environment management. 
To install the required dependencies, run:
`pixi install`
