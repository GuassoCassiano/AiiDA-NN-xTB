import sys
from aiida import load_profile
from aiida.engine import submit
from aiida.orm import Str, Group, load_code, Int
from aiida_nn_xtb.workchain import NNxTBWorkChain

# Boot up the database before loading AiiDA modules
load_profile()

def get_user_input(prompt_text, default_val=None, cast_type=str):
    """
    Helper function to ask the user questions and handle default questions
    """

    if default_val is not None:
        user_input = input(f"{prompt_text} [Default: {default_val}]").strip()
        if not user_input:
            return default_val
    
    else:
        user_input = input(f"{prompt_text}: ").strip()
        while not user_input:
            print("This field is required. Try again.")
            user_input = input(f"{prompt_text}: ").strip()
    
    try:
        return cast_type(user_input)
    except ValueError:
        print(f"Invalid input. Please enter a valid {cast_type.__name__}.")
        sys.exit(1)

def launch_batch(group_name, smiles_list, cluster_code_string, num_machines, num_mpiprocs_per_machine, wallclock):
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
            code=cluster_code,
            num_machines=Int(num_machines),
            num_mpiprocs_per_machine=Int(num_mpiprocs_per_machine),
            max_wallclock_seconds=Int(wallclock)
        )
        
        # immediately drop the tracking node into your AiiDA group
        batch_group.add_nodes([running_node])

    print(f"Successfully submitted {len(smiles_list)} molecules to the '{group_name}' group!")

if __name__ == "__main__":
    print("*** AiiDA NN-xTB Batch Submitter ***")
    print("------------------------------------")
    # ask the user for their inputs line by line
    group_name = get_user_input("Enter the target AiiDA Group name")
    file_name = get_user_input("Enter the text file containing your SMILES strings")
    cluster_code = get_user_input("Enter the cluster code label", default_val="xtb@localhost")
    num_machines = get_user_input("How many machines per job?", default_val=1, cast_type=int)
    processors = get_user_input("How many processors per machine?", default_val=1, cast_type=int)
    wallclock = get_user_input("Max wallclock time in seconds?", default_val=86400, cast_type=int)
    
    # open the file and read the strings into a list
    try:
        with open(file_name, 'r') as file:
            imported_smiles = [line.strip() for line in file if line.strip()]
        if not imported_smiles:
            print("Error: No valid SMILES strings found in file")
            sys.exit(1)
    except FileNotFoundError:
        print(f"Error: File '{file_name}' not found")
        sys.exit(1)
    except IOError as e:
        print(f"Error reading file: {e}")
        sys.exit(1)
    
    print("\nStarting submission process...")

    launch_batch(
        group_name=group_name, 
        smiles_list=imported_smiles, 
        cluster_code_string=cluster_code,
        num_machines=num_machines,
        num_mpiprocs_per_machine=processors,
        wallclock=wallclock
    )