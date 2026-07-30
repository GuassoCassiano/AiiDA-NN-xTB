# tests/conftest.py
import aiida.engine.processes.functions as aiida_funcs

if not hasattr(aiida_funcs, 'get_stack_size'):
    aiida_funcs.get_stack_size = lambda *args, **kwargs: 1