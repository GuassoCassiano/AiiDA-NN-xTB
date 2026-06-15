from rdkit import Chem
from rdkit.Chem import AllChem
from aiida.orm import StructureData
from aiida.engine import calcfunction

@calcfunction
def smiles2structure(smiles_node):
    """
    Converts SMILES strings into an AiiDA StructureData Node
    """

    # unwrap the AiiDA node to get python string for RDKit
    smiles_string = smiles.node.value

    # generate internal molecule structure and then add H's
    mol = Chem.MolFromSmiles(smiles_string) 
    if mol is None: 
        raise ValueError(f"Invalid SMILES string provided: {smiles_string}")
    
    mol = Chem.AddHs(mol)

    # adding a safety check to the code to ensure that only successful structures are ran
    if AllChem.EmbedMolecule(mol, AllChem.ETKDG()) == -1:
        raise ValueError("RDKit failed to generate 3D coordinates for this molecule.")

    # generate 3D structure and optimize its position for lowest energy states
    AllChem.EmbedMolecule(mol, AllChem.ETKDG())
    AllChem.MMFFOptimizeMolecule(mol)

    # save molecule conformer and extract atom positions for AiiDA StructureData
    conformer = mol.GetConformer()

    # AiiDA require a unit cell or boundary to run its StructureData class so we need to make a
    # dynamic boundary to make sure it encapsolates the structure regardless of size
    max_coord = 0.0
    for i in range(mol.GetNumAtoms()):
        pos = conformer.GetAtomPosition(i)
        max_coord = max(max_coord, abs(pos.x), abs(pos.y), abs(pos.z))
    
    # builds a new box that fits the widest atom and adds a 10 angstrum buffer region in all directions
    box_size = (max_coord * 2) + 10.0
    dynamic_cell = [[box_size, 0.0, 0.0], [0.0, box_size, 0.0], [0.0, 0.0, box_size]]

    # update the structure with the dynamic box
    structure = StructureData(cell=dynamic_cell, pbc=[False, False, False])

    for i, atom in enumerate(mol.GetAtoms()):
        pos = conformer.GetAtomPosition(i)
        symbol = atom.GetSymbol()

        structure.append_atom(position=(pos.x, pos.y, pos.z), symbols=symbol)
    
    # Stick the original SMILES string into the StructureData for XYZ file comment
    structure.base.extras.set("original_smiles", smiles_string)

    return structure