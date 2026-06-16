from aiida import load_profile
from aiida_nn_xtb.workchain import NNxTBWorkChain
from aiida.orm import QueryBuilder, Dict, Group, StructureData, CalcJobNode
import zarr
import numpy as np
import argparse

# imports aiida database 
load_profile()

def build_openqdc_zarr(target_group="rough_draft_testing"):
    """Extracts SUCCESSFUL calculations from a specific AiiDA Group into a Zarr store."""
    
    qb = QueryBuilder()

    # anchor the search to a specific batch
    qb.append(Group, filters={'label': target_group}, tag='my_group')

    # find the WorkChain, only if it is in that Group and it finished perfectly
    qb.append(
        NNxTBWorkChain, 
        with_group='my_group',
        filters={'attributes.exit_status': 0},
        tag='my_workchain'
    )
    # find the Output Dictionary
    qb.append(
        Dict,
        with_incoming='my_workchain',
        project='*',
        tag='results'
    )

    # find the CalcJob that was executed in the WorkChain
    qb.append(
        CalcJobNode,
        with_incoming='my_workchain',
        tag='my_calcjob'
    )

    # find the Input Structure
    qb.append(
        StructureData,
        with_outgoing='my_calcjob',
        project='*',
        tag='structure'
    )



    total_calcs = qb.count()
    print(f"Found {total_calcs} perfect calculations in the '{target_group}' batch.")
    
    if total_calcs == 0:
        print("No valid data to export. Check if the WorkChains failed or if the group is empty.")
        return

    # set up empty Python lists
    all_positions = []
    all_atomic_numbers = []
    all_energies = []
    num_atoms_per_mol =[]

    # loop and extract
    for structure_node, dict_node in qb.all():
        ase_molecule = structure_node.get_ase()
        
        all_positions.append(ase_molecule.positions)
        all_atomic_numbers.append(ase_molecule.numbers)
        
        energy_val = dict_node.get_dict()['total_energy']
        all_energies.append(energy_val)

        num_atoms_per_mol.append(len(ase_molecule.numbers))

    # flatten the list so that zarr does error out
    flat_positions = np.concatenate(all_positions, axis=0)
    flat_atomic_numbers = np.concatenate(all_atomic_numbers, axis=0)

    # export to Zarr
    print("Writing data to dataset.zarr...")
    root = zarr.open('dataset.zarr', mode='w')
    
    root.create_dataset('positions', data=flat_positions, dtype=np.float32)
    root.create_dataset('atomic_numbers', data=flat_atomic_numbers, dtype=np.int32)
    root.create_dataset('energies', data=np.array(all_energies, dtype=np.float32))
    root.create_dataset('num_atoms', data=np.array(num_atoms_per_mol, dtype=np.int32))

    print("Export complete! Zarr store is clean and ready.")

if __name__ == "__main__":
    # set up the argument parser
    parser = argparse.ArgumentParser(description="Extracts AiiDA NN-xTB data to a Zarr file.")
    
    # add a required flag for the group name
    parser.add_argument(
        '-g', '--group', 
        type=str, 
        required=True, 
        help="The name of the AiiDA Group you want to extract"
    )
    
    # Parse the terminal command and pass it to your function
    args = parser.parse_args()
    build_openqdc_zarr(target_group=args.group)