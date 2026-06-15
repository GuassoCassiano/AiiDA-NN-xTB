# Structure Data

The `smiles2structure.py` script serves as the physical starting line for our computational chemistry pipeline. Its primary job is to bridge the gap between human-readable 1D SMILES strings and the strict 3D data formats required by the AiiDA engine. Using RDKit, the script generates a 3D molecular geometry, optimizes its initial energy state, and packages the coordinates into an AiiDA `StructureData` node. Because AiiDA's architecture was originally designed for solid-state crystals rather than gas-phase molecules floating in a vacuum, this script also executes a specialized workaround to safely integrate our molecules into the database without triggering spatial boundary errors.

## 1. RDKit Prep (Standard Chemistry)

Before feeding any data into the AiiDA engine, we must convert the user-input SMILES string into a 3D format that NN-xTB can physically process. 

To achieve this, the script first translates the 1D SMILES string into an internal RDKit Molecule Object using the `MolFromSmiles()` function. Crucially, we immediately follow this with `AddHs()`. SMILES strings typically omit hydrogen atoms, but quantum mechanics calculations require them to properly calculate total energy. 

Next, we use `EmbedMolecule()` to project the 2D molecule into a geometrically feasible 3D conformer. However, to ensure the conformer is resting in its lowest energy state and atoms aren't overlapping (which would crash the NN-xTB calculation), we further relax the molecule using the MMFF94 force-field optimizer. This relaxed conformer is then saved so its atomic coordinates can be extracted into AiiDA.

### 1.5 Extracting the Coordinates (The Enumerate Loop)
Once the 3D RDKit conformer is fully optimized, we must physically transfer the atoms into AiiDA. We achieve this by using Python's `enumerate()` function to loop through `mol.GetAtoms()`. For every single atom, the loop extracts its chemical symbol alongside its exact X, Y, and Z spatial coordinates from the RDKit conformer matrix. We then use the `structure.append_atom()` method to drop them one by one into our new AiiDA `StructureData` node.

## 2. The AiiDA Unit Cell Problem (The Bounding Box)

AiiDA's `StructureData` class was originally designed for solid-state materials and crystalline structures. Because of this, the database engine strictly requires every geometry to have a defined unit cell (a 3D bounding box) to run its processes. Since the Kim Group primarily calculates molecules in an isolated vacuum, we have to play by AiiDA's rulebook to prevent the database from crashing. To bypass this, the script dynamically calculates a custom bounding box for every unique molecule.

To build this box, the script initializes a `max_coord` variable at zero. It then loops through every atom in the generated RDKit molecule, comparing the absolute values of the X, Y, and Z coordinates to find the single atom sitting furthest from the origin. Once that maximum distance is found, we multiply it by two to span the full width and add a generous 10.0 Angstrom buffer to ensure the molecule has plenty of empty space. This gives us the dimensions for a perfect cubic unit cell.

Finally, we attach this new cell to our `StructureData` node and explicitly define the Periodic Boundary Conditions (`pbc`). The `pbc` parameter uses a boolean list to tell AiiDA whether an axis is infinite and repeating (`True`) or isolated and finite (`False`). Since our molecule is a completely isolated object in open space, we set all three spatial dimensions to `[False, False, False]`.

## 3. The Metadata Trick (Extras)

The final step of the `smiles2structure.py` script utilizes a built-in AiiDA feature to ensure our data remains traceable. Ultimately, we want the original SMILES string to appear in the comment line of our final `.xyz` files. However, AiiDA's `StructureData` node only cares about atomic coordinates and element symbols—it automatically strips away any other chemical information.

To smuggle this information into AiiDA's highly sanitized environment, we inject the string directly into the node's database metadata using the `structure.base.extras.set()` method. We assign the user-input SMILES string to a custom key named `original_smiles`. This is perfectly analogous to slapping a sticky note on the outside of a shipping crate before sending it into a factory; the AiiDA database engine doesn't care what the note says, but Script 2 can read it later to format the `.xyz` file.