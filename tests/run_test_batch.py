from aiida import load_profile
# Load your default AiiDA profile to connect to the database
load_profile()

from orchestrator import launch_batch

def main():
    # Methane, Ethane, and Propane - they will compute in seconds
    test_smiles = ["C", "CC", "CCC"]
    
    print(f"Building WorkGraph for {len(test_smiles)} test molecules...")
    
    # Fire off the batch
    launch_batch(
        group_name="xtb_test_run_01",
        smiles_list=test_smiles,
        cluster_code_string="xtb@localhost", # Change this if your xTB code has a different label on Loki
        num_machines=1,
        num_mpiprocs_per_machine=1,
        wallclock=1800 # 30 minutes is plenty for these small runs
    )
    
    print("Graph submitted! The daemon is taking over.")

if __name__ == "__main__":
    main()