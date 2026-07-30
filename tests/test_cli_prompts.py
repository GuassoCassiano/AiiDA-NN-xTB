import pytest
from unittest.mock import patch
from orchestrator import get_user_input

def test_get_user_input_default():
    """Test that the function correctly falls back to the default value."""
    with patch('builtins.input', return_value=''):
        assert get_user_input("Prompt", default_val="test_default") == "test_default"

def test_get_user_input_custom():
    """Test that user input overrides the default value."""
    with patch('builtins.input', return_value='my_custom_value'):
        assert get_user_input("Prompt", default_val="test_default") == "my_custom_value"

def test_get_user_input_cast_int():
    """Test that the function correctly casts inputs to integers."""
    with patch('builtins.input', return_value='42'):
        assert get_user_input("Prompt", cast_type=int) == 42