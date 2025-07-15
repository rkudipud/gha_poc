import sys
sys.path.insert(0, 'rules/python_imports')
try:
    import python_imports
    print('Import successful')
    if hasattr(python_imports, 'PythonImportsRule'):
        print('PythonImportsRule found')
        rule = python_imports.PythonImportsRule()
        print('Rule instantiated successfully')
    else:
        print('PythonImportsRule not found')
except Exception as e:
    print('Error:', e)
    import traceback
    traceback.print_exc()
