# The WorkGraph Pipeline

The `orchestrator.py` script is the new central nervous system of our entire pipeline. We completely transitioned away from AiiDA's traditional, rigid WorkChains in favor of the dynamic `aiida-workgraph` plugin. This script handles user inputs, builds massive parallel execution tracks for every molecule, and submits the entire visual graph to the daemon at once.

## 1. Interactive Terminal Prompts
Instead of hardcoding variables, the orchestrator acts as a user-friendly terminal interface. We use a custom `get_user_input` helper function to ask the researcher exactly how they want to run their batch. It handles setting defaults (like assuming 1 processor or 86400 seconds) and automatically sanitizes the inputs before the pipeline even starts building.

## 2. Building the Parallel Tracks
The core power of this script is the `launch_batch` function. After creating a clean AiiDA Group to hold the data, it initializes an empty `WorkGraph`. 

It then loops through every SMILES string in your text file and creates a parallel track. For every molecule, it:
* Adds a `smiles2structure` task.
* Adds an `NNxTBCalculation` task.
* Programmatically links the output of the 3D generator straight into the input of the calculation wrapper.

By looping this process, a single WorkGraph can orchestrate hundreds of independent molecules simultaneously without the local machine breaking a sweat.

## 3. The Gather Node
To keep track of massive batches, we built a custom `@task def gather_results` node. This task sits at the very end of the WorkGraph. We save the final output dictionary from every single xTB calculation and plug them all into this gather node. 

Once the remote cluster finishes churning through the entire batch, this final node wakes up, counts exactly how many calculations succeeded versus how many were attempted, and saves a clean summary dictionary straight to the AiiDA database. 

## 4. Submission
Once the entire graph is built, we simply call `wg.submit()`. This hands the blueprint over to AiiDA's background daemon to process asynchronously. We then drop the main WorkGraph tracking node into our designated AiiDA Group so the QueryBuilder can easily find it later during the Zarr extraction step.