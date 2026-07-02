"""
Pytest suite for AiiDA-NN-xTB: End-to-End Batch Processing and Zarr Compilation.
"""

import os
import shutil
import pytest
import zarr
from aiida import load_profile
from aiida.engine import run
from aiida.orm import Str, load_code, Group, Int

# Import MVP WorkChain and the Zarr compiler
from aiida_nn_xtb.workchain import NNxTBWorkChain
from aiida_nn_xtb.dict2zarr import build_openqdc_zarr

load_profile()

def test_full_pipeline_compilation():
    """
    Test the full pipeline:
    1. Runs a batch of 5 varying SMILES strings synchronously.
    2. Groups the results.
    3. Compiles them into a Zarr file.
    4. Verifies the Zarr arrays contain exactly 5 entries.
    """
    # 1. Define the test batch (increasing complexity)
    smiles_list = [
        "C",                      # Methane
        "CCO",                    # Ethanol
        "c1ccccc1",               # Benzene
        "CC(=O)Oc1ccccc1C(=O)O",  # Aspirin
        "CN1C=NC2=C1C(=O)N(C(=O)N2C)C" # Caffeine
    ]
    
    test_group_name = "pytest_e2e_run"
    
    # Create a fresh group for this test
    group, created = Group.objects.get_or_create(label=test_group_name)

    # Empty out any calculations from previous test runs so we start fresh
    group.clear()
    
    # 2. Run the batch synchronously
    for smiles in smiles_list:
        inputs = {
            'smiles': Str(smiles),
            'code': load_code('xtb@localhost'),
            'num_machines': Int(1),
            'num_mpiprocs_per_machine': Int(1),
            'max_wallclock_seconds': Int(86400)
        }
        
        # Use 'run' so Pytest waits for the calculation to finish
        _, workchain_node = run.get_node(NNxTBWorkChain, **inputs)

        assert workchain_node.is_finished_ok, f"Workchain failed for {smiles} with exit status {workchain_node.exit_status}"
        
        # Add the completed WorkChain to our test group
        group.add_nodes(workchain_node)
        
    # 3. Run the Zarr extraction script targeting our test group
    build_openqdc_zarr(target_group=test_group_name)
    
    # 4. Assertions on the generated dataset.zarr
    assert os.path.isdir("dataset.zarr"), "The dataset.zarr folder was not created."
    
    # Open the compiled Zarr store to verify the data
    root = zarr.open('dataset.zarr', mode='r')
    
# Verify the arrays exist
    assert 'positions' in root, "Positions array missing from Zarr."
    assert 'energies' in root, "Energies array missing from Zarr."
    assert 'atomic_numbers' in root, "Atomic numbers array missing from Zarr."
    assert 'num_atoms' in root, "num_atoms array missing from Zarr."
    
    # Check the length using .shape[0]
    num_energies = root['energies'].shape[0]
    num_atoms_entries = root['num_atoms'].shape[0]
    
    assert num_energies == 5, f"Expected 5 energies, but the Zarr array shape is {root['energies'].shape}"
    assert num_atoms_entries == 5, f"Expected 5 num_atoms entries, but the Zarr array shape is {root['num_atoms'].shape}"
    
    # 5. Teardown (Clean up the test file so it doesn't clutter your workspace)
    shutil.rmtree("dataset.zarr")