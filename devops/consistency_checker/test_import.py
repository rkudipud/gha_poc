#!/usr/bin/env python3
import sys
sys.path.insert(0, 'rules/python_imports')
try:
    import python_imports
    print('Module imported successfully')
    print('Module dir:', [x for x in dir(python_imports) if not x.startswith('_')])
    if hasattr(python_imports, 'PythonImportsRule'):
        print('PythonImportsRule found')
        rule_class = python_imports.PythonImportsRule
        print('Rule class:', rule_class)
        print('Is BaseRule subclass:', issubclass(rule_class, python_imports.BaseRule))
    else:
        print('PythonImportsRule NOT found')
except Exception as e:
    print('Import error:', e)
    import traceback
    traceback.print_exc()
