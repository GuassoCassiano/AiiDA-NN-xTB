import pytest
from aiida import load_profile
from aiida_workgraph import WorkGraph
from unittest.mock import patch, MagicMock
from orchestrator import launch_batch

# Boot up the database for the test
load_profile()

@patch('orchestrator.WorkGraph.submit')
@patch('orchestrator.Group.collection.get_or_create')
@patch('orchestrator.load_code')
def test_launch_batch_graph_creation(mock_load_code, mock_get_group, mock_submit):
    """
    Tests that the orchestrator successfully builds the WorkGraph and 
    organizes the AiiDA group without actually submitting to the daemon.
    """
    # 1. Setup our "intercepted" dummy responses
    mock_group_instance = MagicMock()
    mock_get_group.return_value = (mock_group_instance, True)
    mock_load_code.return_value = MagicMock()
    
    # 2. Provide a mini test batch
    smiles_list = ["C", "CC", "CCC"]
    
    # 3. Run the orchestrator
    launch_batch(
        group_name="test_group",
        smiles_list=smiles_list,
        cluster_code_string="dummy_code@localhost",
        num_machines=1,
        num_mpiprocs_per_machine=1,
        wallclock=3600
    )
    
    # 4. Verify the orchestrator did exactly what we expect
    mock_load_code.assert_called_once_with("dummy_code@localhost")
    mock_get_group.assert_called_once_with(label="test_group")
    
    # Ensure it actually tried to hit the submit button!
    mock_submit.assert_called_once()
    
    # Ensure it added the tracking node to the group
    mock_group_instance.add_nodes.assert_called_once()