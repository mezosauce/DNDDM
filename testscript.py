"""
Test all Python scripts in the BackEnd/Classes directory and BackEnd direcotry.
This script attempts to import each module and reports success or failure.
"""

import os
import importlib.util
def test_imports_in_directory(directory):
    """Test importing all Python modules in the specified directory."""
    for filename in os.listdir(directory):
        if filename.endswith('.py') and filename != os.path.basename(__file__):
            module_name = filename[:-3]
            file_path = os.path.join(directory, filename)
            try:
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                print(f"✓ Successfully imported {module_name} from {file_path}")
            except Exception as e:
                print(f"✗ Failed to import {module_name} from {file_path}: {e}")
if __name__ == "__main__":
    # Test imports in BackEnd/Classes
    classes_dir = os.path.join(os.path.dirname(__file__), 'Classes')
    print(f"Testing imports in directory: {classes_dir}")
    test_imports_in_directory(classes_dir)
    
    # Test imports in BackEnd
    backend_dir = os.path.dirname(__file__)
    print(f"\nTesting imports in directory: {backend_dir}")
    test_imports_in_directory(backend_dir)
