"""
Pytest suite for AiiDA-NN-xTB: Structure to XYZ (CalcJob Dry Run).
"""

import os
import pytest
from aiida import load_profile
from aiida.engine import run
from aiida.plugins import CalculationFactory
from aiida.orm import Str, load_code
from aiida_nn_xtb.smiles2structure import smiles2structure
import shutil

# Load the AiiDA profile so the database is accessible
load_profile()

def test_xtb_calcjob_dry_run():
    """
    Test that the CalcJob correctly prepares the input files for xTB
    without executing the heavy calculation.
    """
    XtbCalculation = CalculationFactory('nnxtb_calc')
    
    # 1. Generate the test structure
    structure = smiles2structure(Str("CCO"))
    
    # 2. Set up the dry run parameters
    inputs = {
        'code': load_code('xtb@localhost'),
        'structure': structure,
        'metadata': {
            'dry_run': True,
            'store_provenance': False,
            'options': {
                'resources': {'num_machines': 1, 'num_mpiprocs_per_machine': 1}
            }
        }
    }
    
    # 3. Execute the dry run
    # If the CalcJob logic is broken, this will immediately throw an error and fail the test
    run(XtbCalculation, **inputs)
    
    # 4. Assertions
    # A successful dry run creates a 'submit_test' folder in your working directory
    assert os.path.isdir("submit_test"), "The 'submit_test' folder was not created."
    
    # Verify that the plugin actually wrote files inside that folder
    generated_files = os.listdir("submit_test")
    assert len(generated_files) > 0, "The submit_test folder is empty. The plugin failed to write the input files."

    # 5. Teardown (Clean up the test folder)
    shutil.rmtree("submit_test")