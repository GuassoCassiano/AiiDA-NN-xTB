# Batch Submission (The Launcher)

The `submit_batch.py` script is the user-facing ignition switch for our entire computational pipeline. Unlike the previous scripts, which are deeply embedded as plugins inside the AiiDA database, this script acts as an external controller. It allows a researcher to take a simple text file of target molecules, automatically launch parallel asynchronous WorkChains for each one, and neatly organize the calculation nodes into designated database folders for easy retrieval later.

## 1. The Terminal Interface (argparse)

Because this script acts as the main steering wheel, researchers interact with it directly through the terminal. We use Python's built-in `argparse` library to set up three required command-line flags. A user must provide a target group name (`-g`), the specific supercomputer code they want to run (`-c`), and a text file containing their target molecules (`-f`). 

Once the user hits enter, the script opens that text file and uses a quick list comprehension command (`line.strip()`) to automatically clean the data, stripping out any accidental blank lines or hidden spaces before the pipeline even starts.

## 2. Organizing with Groups

If we blindly drop hundreds of automated calculations into AiiDA, the database will quickly turn into a massive, unsearchable junk drawer. To prevent this, the script uses `Group.collection.get_or_create` at the very beginning of the run. 

This command looks at the group name the user provided and either opens that existing batch or creates a brand new one. You can think of an AiiDA Group like a labeled manila folder. It neatly corrals all related calculations together, which is exactly what allows the QueryBuilder (from Script 5) to locate and extract them easily later.

## 3. The Submission Loop

The final piece of the script is the execution loop itself. The code loops through every cleaned SMILES string in our list and uses AiiDA's built-in `submit()` function. This command takes our target string and our cluster code, packages them together, and hands the whole job over to the AiiDA background daemon to process asynchronously. 

AiiDA creates a tracking node the exact millisecond a job is submitted. To make sure that tracking node does not get lost in the void, the script takes the `running_node` output and immediately drops it straight into our manila folder using `batch_group.add_nodes([running_node])`.