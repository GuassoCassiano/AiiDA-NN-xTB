"""
Pytest suite for AiiDA-NN-xTB: Interactive Batch Submission CLI.
"""

import pytest
import runpy
from aiida import load_profile

# Load the AiiDA profile
load_profile()

def test_interactive_submit_batch(monkeypatch, tmp_path):
    """
    Simulates a user typing inputs into the command line to test submit_batch.py.
    """
    # 1. Create a temporary text file with SMILES strings
    smiles_file = tmp_path / "test_smiles.txt"
    smiles_file.write_text("C\nCCO\n")
    
    # 2. Define the exact sequence of strings the "user" will type
    user_inputs = iter([
        "pytest_cli_group",         # target AiiDA Group name
        str(smiles_file),           # path to the text file
        "xtb@localhost",            # cluster code label
        "1",                        # machines
        "1",                        # processors
        "3600"                      # wallclock time
    ])
    
    # 3. Use monkeypatch to override the built-in input() function
    monkeypatch.setattr('builtins.input', lambda _: next(user_inputs))
    
    # 4. Execute the script as if we typed `python submit_batch.py` in the terminal
    # If the script crashes or fails to submit, this test will fail
    try:
        runpy.run_module('submit_batch', run_name='__main__')
    except StopIteration:
        pytest.fail("The script asked for more inputs than we provided!")
    except Exception as e:
        pytest.fail(f"The CLI script crashed with error: {e}")