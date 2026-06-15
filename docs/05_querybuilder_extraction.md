# The QueryBuilder & Extraction

The `dict2zarr.py` script is the final data extraction tool of our AiiDA pipeline. After the database has been populated with hundreds or thousands of isolated calculation nodes, we need a way to pull that data out efficiently for machine learning ingestion. This script uses AiiDA's `QueryBuilder` to hunt down flawless calculation runs, extracts the 3D molecular coordinates and their corresponding total energies, and packages everything into high-performance, memory-mapped `.zarr` arrays.

## 1. The QueryBuilder (Filtering the Noise)

Before we can interact with our AiiDA database, we have to wake up the profile itself using `load_profile()`. Once the profile is loaded, we can use the `QueryBuilder()` function to filter through the massive database and find exactly what we need. 

We start by "anchoring" our search to a specific batch of molecules by appending a Group filter to our query: `qb.append(Group, filters={'label': target_group}, tag='my_group')`. 

To ensure we do not crash our machine learning models downstream, we only want to extract successful calculations. We do this by looking within our `NNxTBWorkChain` and strictly grabbing results that have an attribute of a successful exit code using `filters={'attributes.exit_status': 0}`. 

Finally, we have to account for edge cases where a user searches for a typoed group name or a batch where every calculation failed. We use a simple `if` statement to count the total valid WorkChains and return a clean error message if there is no data to export.

## 2. Graph Traversal (Incoming & Outgoing)

A great way to understand how the `QueryBuilder` traverses data is to visualize the AiiDA database as a giant, directional flowchart. The database connects data points using strict arrows that represent where data came from and where it went. 

Because our WorkChain generates the 3D structure internally rather than taking it as a direct input, we have to teach the QueryBuilder to follow the process deeper into the graph to find our data.

* **The Outputs (with_incoming):** We want to find the final converged energy. We tell the QueryBuilder to find the `Dict` node that has an arrow pointing *into* itself coming directly from the WorkChain.
* **The CalcJob (with_incoming):** To find our atomic coordinates, we first have to locate the exact computational job the WorkChain triggered on the cluster. We append a `CalcJobNode` that has an arrow pointing *into* it from the WorkChain.
* **The Inputs (with_outgoing):** Now that we found the CalcJob, we can find the exact 3D coordinates it used. We tell the QueryBuilder to find the `StructureData` node that has an arrow pointing *out* of itself and into our CalcJob.

## 3. Zarr Export (The Final Package)

The last part of our function formats our NN-xTB data into a `.zarr` structure for high-speed machine learning ingestion. Luckily, AiiDA comes with a built-in Atomic Simulation Environment (ASE) method, which allows us to quickly strip the atomic positions and element numbers directly out of our `StructureData` nodes using `get_ase()`. 

We create empty Python lists for the positions, atomic numbers, and energies, and then use a `for` loop to step through our perfect `QueryBuilder` matches and append that extracted information into the lists. 

With the information safely stored in memory, turning it into a `.zarr` file simply requires opening a local store and creating three datasets with the correct labels. We use `root = zarr.open('dataset.zarr', mode='w')` to open the file and `root.create_dataset()` to physically write our arrays. The final `.zarr` output is now completely clean, standardized, and ready for the OpenQDC framework.