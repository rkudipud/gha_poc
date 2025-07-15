#!/usr/bin/env python3
"""
Test script to verify basic functionality before GitHub Actions runs.
This helps ensure the workflow will work correctly.
"""

import os
import sys
import subprocess
from pathlib import Path

def test_python_syntax():
    """Test Python syntax for all Python files in the repo."""
    print("🔍 Testing Python syntax...")
    
    # Find all Python files, excluding venv directory
    python_files = []
    for file_path in Path('.').rglob('*.py'):
        # Skip virtual environment and __pycache__ directories
        if 'venv' not in str(file_path) and '__pycache__' not in str(file_path):
            python_files.append(file_path)
    
    if not python_files:
        print("ℹ️ No Python files found")
        return True
    
    success = True
    for file_path in python_files:
        try:
            print(f"   Checking: {file_path}")
            subprocess.run([sys.executable, '-m', 'py_compile', str(file_path)], 
                         check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            print(f"❌ Syntax error in {file_path}")
            print(f"   Error: {e.stderr.decode()}")
            success = False
    
    if success:
        print("✅ All Python files have valid syntax")
    
    return success

def check_workflow_syntax():
    """Basic check for workflow file existence and basic structure."""
    print("🔍 Checking workflow file...")
    
    workflow_path = Path('.github/workflows/pr-validation.yml')
    if not workflow_path.exists():
        print("❌ Workflow file not found")
        return False
    
    content = workflow_path.read_text()
    
    # Basic checks
    required_sections = ['name:', 'on:', 'jobs:', 'validate_pr:', 'auto_merge:']
    missing = []
    
    for section in required_sections:
        if section not in content:
            missing.append(section)
    
    if missing:
        print(f"❌ Missing sections in workflow: {missing}")
        return False
    
    print("✅ Workflow file structure looks good")
    return True

def main():
    """Run all tests."""
    print("🚀 Running pre-workflow validation tests...\n")
    
    tests = [
        ("Python Syntax", test_python_syntax),
        ("Workflow Structure", check_workflow_syntax),
    ]
    
    all_passed = True
    
    for test_name, test_func in tests:
        print(f"Running {test_name} test:")
        result = test_func()
        print()
        
        if not result:
            all_passed = False
    
    if all_passed:
        print("🎉 All tests passed! Workflow should work correctly.")
        return 0
    else:
        print("❌ Some tests failed. Fix issues before creating PR.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
