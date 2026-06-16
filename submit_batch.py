import argparse
import sys
from aiida import load_profile
from aiida.engine import submit
from aiida.orm import Str, Group, load_code
from aiida_nn_xtb.workchain import NNxTBWorkChain

# Boot up the database before loading AiiDA modules
load_profile()

def launch_batch(group_name, smiles_list, cluster_code_string):
    """Submits a list of SMILES strings to the AiiDA daemon and organizes them into a Group."""
    
    # create the bucket (or load it if it already exists)
    batch_group, created = Group.collection.get_or_create(label=group_name)
    if created:
        print(f"Created new AiiDA Group: {group_name}")
    
    # dynamically load the cluster software configuration
    cluster_code = load_code(cluster_code_string)

    # loop through the molecules and submit them
    for smiles_string in smiles_list:
        print(f"Submitting WorkChain for SMILES: {smiles_string}")
        
        # submit the WorkChain to the AiiDA background daemon
        running_node = submit(
            NNxTBWorkChain, 
            smiles=Str(smiles_string), 
            code=cluster_code
        )
        
        # immediately drop the tracking node into your AiiDA group
        batch_group.add_nodes([running_node])

    print(f"Successfully submitted {len(smiles_list)} molecules to the '{group_name}' group!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Launch a batch of SMILES strings.")
    parser.add_argument('-g', '--group', type=str, required=True)
    parser.add_argument('-c', '--code', type=str, required=True)
    
    # add a new argument for a text file
    parser.add_argument('-f', '--file', type=str, required=True, help="Text file containing SMILES strings")
    args = parser.parse_args()
    
    # open the file and read the strings into a list
  try:
        with open(args.file, 'r') as file:
            imported_smiles = [line.strip() for line in file if line.strip()]
        if not imported_smiles:
            print("Error: No valid SMILES strings found in file")
            sys.exit(1)
    except FileNotFoundError:
        print(f"Error: File '{args.file}' not found")
        sys.exit(1)
    except IOError as e:
        print(f"Error reading file: {e}")
        sys.exit(1)
    
    launch_batch(
        group_name=args.group, 
        smiles_list=imported_smiles, 
        cluster_code_string=args.code
    )