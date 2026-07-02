"""
Pytest suite for AiiDA-NN-xTB: Local xTB execution and parsing.
"""

import pytest
from aiida import load_profile
from aiida.engine import run
from aiida.plugins import CalculationFactory
from aiida.orm import Str, load_code
from aiida_nn_xtb.smiles2structure import smiles2structure

# Load the AiiDA profile
load_profile()

def test_xtb_execution_and_parsing():
    """
    Test that the CalcJob correctly executes a local xTB run 
    and the Parser successfully extracts the data into a dictionary.
    """
    XtbCalculation = CalculationFactory('nnxtb_calc') 
    
    # 1. Generate the test structure
    smiles_string = Str("CCO")
    structure = smiles2structure(smiles_string)
    
    # 2. Setup the inputs dictionary
    inputs = {
        'code': load_code('xtb@localhost'),
        'structure': structure,
        'metadata': {
            'options': {
                'resources': {'num_machines': 1, 'num_mpiprocs_per_machine': 1}
            }
        }
    }
    
    # 3. Run the calculation
    calculation_outputs = run(XtbCalculation, **inputs)
    
    # 4. Assertions
    # Verify the parser actually passed a 'results' node back
    assert 'results' in calculation_outputs, "The parser failed to return a 'results' node."
    
    # Extract the dictionary
    parsed_node = calculation_outputs['results']
    parsed_dict = parsed_node.get_dict()
    
    # Verify the dictionary is valid and contains data
    assert isinstance(parsed_dict, dict), "The parsed results should be a dictionary."
    assert len(parsed_dict) > 0, "The parsed dictionary is empty."
    
    # Optional: Test for a specific key you know the parser should grab
    # assert 'total_energy' in parsed_dict, "Expected 'total_energy' in parsed results."