import sys
from aiida import load_profile
from aiida.orm import Str, Int, load_code, Group, Dict

# added monkey patch for older redundant aiida specifics
import aiida.engine.processes.functions as aiida_funcs
if not hasattr(aiida_funcs, 'get_stack_size'):
    aiida_funcs.get_stack_size = lambda *args, **kwargs: 1

from aiida_workgraph import WorkGraph, task

from aiida_nn_xtb.smiles2structure import smiles2structure, calcfunction
from aiida_nn_xtb.structure2xyz import NNxTBCalculation

load_profile()

# create a simple global gather task to count successes
@task
def gather_results(**results):
    # results only contains the outputs of the xTB tasks that didn't crash
    success_count = len(results)

    total_attempted = results.pop("total_attempted")

    summary_data = {
        "summary_message": f"{success_count}/{total_attempted} calculations were successful!",
        "tasks_succeeded": success_count,
        "total_attempted": total_attempted,
        "successful_molecules": list(results.keys())
    }
    
    # return it as an AiiDA Dict so it gets permanently saved to database
    return Dict(dict=summary_data)

def get_user_input(prompt_text, default_val=None, cast_type=str):
    """Helper function to ask the user questions and handle default questions"""
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
    """Builds and submits a massive parallel WorkGraph for a list of SMILES."""
    
    # create the bucket (or load it if it already exists)
    batch_group, created = Group.collection.get_or_create(label=group_name)
    if created:
        print(f"Created new AiiDA Group: {group_name}")
    
    wg = WorkGraph(name="NN_xTB_Batch_Pipeline")
    cluster_code = load_code(cluster_code_string)
    
    final_outputs = {}

    # loop through your SMILES list and build the parallel tracks
    for i, smiles_string in enumerate(smiles_list):
        
        smiles_task_name = f"smiles_node_{i}"
        xtb_task_name = f"xtb_node_{i}"
        
        # add the SMILES to Structure task and feed it the string
        smiles_task = wg.add_task(
            smiles2structure, 
            name=smiles_task_name,
            smiles_node=Str(smiles_string),
            metadata={"label": f"SMILES String: {smiles_string}"}
        )

        # add the xTB CalcJob task
        xtb_task = wg.add_task(
            NNxTBCalculation, 
            name=xtb_task_name,
            code=cluster_code,
            metadata={
                "label": f"SMILES String: {smiles_string}",
                "options": {
                    "resources": {
                        "num_machines": num_machines,
                        "num_mpiprocs_per_machine": num_mpiprocs_per_machine
                    },
                    "max_wallclock_seconds": wallclock
                }
            }
        )

        wg.add_link(smiles_task.outputs["result"], xtb_task.inputs["structure"])
        
        # save the final parsed output node to plug into the gather node
        final_outputs[f"mol_{i}"] = xtb_task.outputs["results"]
        
    # add the gather node at the very end of the loop
    gather_node = wg.add_task(
        gather_results, 
        name="final_tally", 
        total_attempted=Int(len(smiles_list)), 
        **final_outputs
    )

    # submit the whole graph to the AiiDA daemon
    wg.submit()
    print(f"Successfully submitted WorkGraph with {len(smiles_list)} parallel tracks!")
    
    # drop the main WorkGraph tracking node into the group
    batch_group.add_nodes([wg.process])
    print(f"WorkGraph added to group: {group_name}. Check the AiiDA GUI to track progress!")

if __name__ == "__main__":
    print("*** AiiDA NN-xTB Batch Submitter ***")
    print("------------------------------------")
    
    group_name = get_user_input("Enter the target AiiDA Group name")
    file_name = get_user_input("Enter the text file containing your SMILES strings")
    cluster_code = get_user_input("Enter the cluster code label", default_val="xtb@localhost")
    num_machines = get_user_input("How many machines per job?", default_val=1, cast_type=int)
    processors = get_user_input("How many processors per machine?", default_val=1, cast_type=int)
    wallclock = get_user_input("Max wallclock time in seconds?", default_val=86400, cast_type=int)
    
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