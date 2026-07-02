"""
Pytest suite for AiiDA-NN-xTB: SMILES to 3D Structure.
"""

import pytest
from aiida import load_profile
from aiida.orm import Str
from aiida_nn_xtb.smiles2structure import smiles2structure

# Load the AiiDA profile so the database is accessible during the test
load_profile()

def test_ethanol_conversion():
    """
    Test that a basic SMILES string (Ethanol) is correctly converted 
    into a 3D AiiDA StructureData node with explicit hydrogens and metadata.
    """
    # 1. Setup input
    smiles_node = Str("CCO")
    
    # 2. Execute the function
    structure_node = smiles2structure(smiles_node)
    
    # 3. Unpack into an ASE object for easy geometry assertions
    ase_mol = structure_node.get_ase()
    
    # 4. Assertions
    # Ethanol (C2H6O) should have exactly 9 atoms
    assert len(ase_mol) == 9, f"Expected 9 atoms for CCO, but got {len(ase_mol)}"
    
    # Verify the exact element counts (2 Carbons, 6 Hydrogens, 1 Oxygen)
    symbols = ase_mol.get_chemical_symbols()
    assert symbols.count('C') == 2, "Carbon count is incorrect"
    assert symbols.count('H') == 6, "Hydrogen count is incorrect (implicit hydrogens might be missing)"
    assert symbols.count('O') == 1, "Oxygen count is incorrect"
    
    # Verify the bounding box actually generated dimensions (should not be perfectly zero)
    assert sum(structure_node.cell_lengths) > 0, "Cell lengths are zero, structure generation failed"
    
    # Verify the custom metadata is attached correctly
    smiles_extra = structure_node.base.extras.get('original_smiles')
    assert smiles_extra == "CCO", f"Expected metadata 'CCO', found {smiles_extra}"