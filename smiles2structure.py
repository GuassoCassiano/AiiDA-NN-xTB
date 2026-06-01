from rdkit import Chem
from rdkit.Chem import AllChem
from aiida.orm import StructureData

def smiles2structure(smiles_string):
    """
    Converts SMILES strings into an AiiDA StructureData Node
    """

    # generate internal molecule structure and then add H's
    mol = Chem.MolFromSmiles(smiles_string) 
    if mol is None: 
        raise ValueError(f"Invalid SMILES string provided: {smiles_string}")
    
    mol = Chem.AddHs(mol)

    # generate 3D structure and optimize its position for lowest energy states
    AllChem.EmbedMolecule(mol, AllChem.ETKDG())
    AllChem.MMFFOptimizeMolecule(mol)

    # save molecule conformer and extract atom positions for AiiDA StructureData
    conformer = mol.GetConformer()

    structure = StructureData()

    for i, atom in enumerate(mol.GetAtoms()):
        pos = conformer.GetAtomPosition(i)
        symbol = atom.GetSymbol()

        structure.append_atom(position=(pos.x, pos.y, pos.z), symbols=symbol)
    
    # Stick the original SMILES string into the StructureData for XYZ file comment
    structure.base.extras.set("original_smiles", smiles_string)

    return structure