#!/usr/bin/env python3
"""
Naming Conventions Consistency Rule

This rule enforces consistent naming conventions across Python code:
- Function names: snake_case
- Class names: PascalCase
- Constants: UPPER_SNAKE_CASE
- Variable names: snake_case
- File names: snake_case.py
- Private members: _leading_underscore

Can automatically suggest fixes for some naming violations.
"""

import ast
import os
import re
from pathlib import Path
from typing import Dict, List, Any


DESCRIPTION = "Enforces consistent naming conventions for Python code"


def check(repo_root: Path) -> Dict[str, Any]:
    """
    Check naming conventions across the repository
    
    Args:
        repo_root: Root directory of the repository
        
    Returns:
        Dictionary with violations and warnings
    """
    violations = []
    warnings = []
    
    # Find all Python files
    python_files = []
    for root, dirs, files in os.walk(repo_root):
        # Skip common non-source directories
        dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', '.pytest_cache', 'venv', '.venv', 'node_modules'}]
        
        for file in files:
            if file.endswith('.py'):
                file_path = Path(root) / file
                python_files.append(file_path)
                
                # Check file naming
                file_violations = _check_file_naming(file_path, repo_root)
                violations.extend(file_violations)
    
    # Check code naming conventions
    for file_path in python_files:
        try:
            file_violations, file_warnings = _check_code_naming(file_path, repo_root)
            violations.extend(file_violations)
            warnings.extend(file_warnings)
        except Exception as e:
            warnings.append({
                'file': str(file_path.relative_to(repo_root)),
                'line': 0,
                'message': f"Could not parse file: {e}",
                'severity': 'warning'
            })
    
    return {
        'violations': violations,
        'warnings': warnings
    }


def _check_file_naming(file_path: Path, repo_root: Path) -> List[Dict[str, Any]]:
    """Check file naming conventions"""
    violations = []
    
    filename = file_path.name
    if filename == '__init__.py':
        return violations  # __init__.py is always valid
    
    # Remove .py extension
    name_part = filename[:-3] if filename.endswith('.py') else filename
    
    # Check if filename follows snake_case
    if not _is_snake_case(name_part):
        violations.append({
            'file': str(file_path.relative_to(repo_root)),
            'line': 0,
            'message': f"File name '{filename}' should use snake_case (e.g., '{_to_snake_case(name_part)}.py')",
            'severity': 'warning',
            'rule': 'file_naming',
            'suggested_fix': f"{_to_snake_case(name_part)}.py"
        })
    
    return violations


def _check_code_naming(file_path: Path, repo_root: Path) -> tuple:
    """Check naming conventions in Python code"""
    violations = []
    warnings = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content, filename=str(file_path))
        
        class NamingVisitor(ast.NodeVisitor):
            def visit_FunctionDef(self, node):
                # Check function naming
                if not node.name.startswith('_') and not _is_snake_case(node.name):
                    # Special cases
                    if not (node.name.startswith('test') or 
                           node.name in {'setUp', 'tearDown', 'setUpClass', 'tearDownClass'}):
                        violations.append({
                            'file': str(file_path.relative_to(repo_root)),
                            'line': node.lineno,
                            'message': f"Function '{node.name}' should use snake_case (e.g., '{_to_snake_case(node.name)}')",
                            'severity': 'warning',
                            'rule': 'function_naming',
                            'suggested_fix': _to_snake_case(node.name)
                        })
                
                self.generic_visit(node)
            
            def visit_AsyncFunctionDef(self, node):
                # Same rules as regular functions
                self.visit_FunctionDef(node)
            
            def visit_ClassDef(self, node):
                # Check class naming
                if not _is_pascal_case(node.name):
                    violations.append({
                        'file': str(file_path.relative_to(repo_root)),
                        'line': node.lineno,
                        'message': f"Class '{node.name}' should use PascalCase (e.g., '{_to_pascal_case(node.name)}')",
                        'severity': 'warning',
                        'rule': 'class_naming',
                        'suggested_fix': _to_pascal_case(node.name)
                    })
                
                self.generic_visit(node)
            
            def visit_Assign(self, node):
                # Check variable/constant naming
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        name = target.id
                        
                        # Skip special variables
                        if name.startswith('__') and name.endswith('__'):
                            continue
                        
                        # Check if it's a constant (all uppercase)
                        if name.isupper():
                            if not _is_constant_case(name):
                                violations.append({
                                    'file': str(file_path.relative_to(repo_root)),
                                    'line': node.lineno,
                                    'message': f"Constant '{name}' should use UPPER_SNAKE_CASE",
                                    'severity': 'info',
                                    'rule': 'constant_naming'
                                })
                        else:
                            # Regular variable
                            if not name.startswith('_') and not _is_snake_case(name):
                                warnings.append({
                                    'file': str(file_path.relative_to(repo_root)),
                                    'line': node.lineno,
                                    'message': f"Variable '{name}' should use snake_case (e.g., '{_to_snake_case(name)}')",
                                    'severity': 'info',
                                    'rule': 'variable_naming',
                                    'suggested_fix': _to_snake_case(name)
                                })
                
                self.generic_visit(node)
        
        visitor = NamingVisitor()
        visitor.visit(tree)
        
    except SyntaxError as e:
        warnings.append({
            'file': str(file_path.relative_to(repo_root)),
            'line': e.lineno or 0,
            'message': f"Syntax error: {e.msg}",
            'severity': 'error'
        })
    except Exception as e:
        warnings.append({
            'file': str(file_path.relative_to(repo_root)),
            'line': 0,
            'message': f"Error checking naming: {e}",
            'severity': 'warning'
        })
    
    return violations, warnings


def _is_snake_case(name: str) -> bool:
    """Check if name follows snake_case convention"""
    if not name:
        return True
    
    # Allow single character names
    if len(name) == 1:
        return name.islower()
    
    # Check pattern: lowercase with underscores, no consecutive underscores
    pattern = r'^[a-z]+(_[a-z0-9]+)*$'
    return bool(re.match(pattern, name))


def _is_pascal_case(name: str) -> bool:
    """Check if name follows PascalCase convention"""
    if not name:
        return True
    
    # Check pattern: starts with uppercase, then camelCase
    pattern = r'^[A-Z][a-zA-Z0-9]*$'
    return bool(re.match(pattern, name))


def _is_constant_case(name: str) -> bool:
    """Check if name follows CONSTANT_CASE convention"""
    if not name:
        return True
    
    # Check pattern: uppercase with underscores
    pattern = r'^[A-Z]+(_[A-Z0-9]+)*$'
    return bool(re.match(pattern, name))


def _to_snake_case(name: str) -> str:
    """Convert name to snake_case"""
    if not name:
        return name
    
    # Handle PascalCase/camelCase
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
    
    # Handle spaces and other separators
    s3 = re.sub(r'[\s\-\.]+', '_', s2)
    
    # Clean up multiple underscores
    s4 = re.sub(r'_+', '_', s3)
    
    # Remove leading/trailing underscores
    s5 = s4.strip('_')
    
    return s5.lower()


def _to_pascal_case(name: str) -> str:
    """Convert name to PascalCase"""
    if not name:
        return name
    
    # Split on underscores and spaces
    parts = re.split(r'[_\s\-\.]+', name.lower())
    
    # Capitalize each part
    return ''.join(word.capitalize() for word in parts if word)


def fix(repo_root: Path, violations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Suggest fixes for naming violations (manual review required)
    
    Args:
        repo_root: Root directory of the repository
        violations: List of violations to fix
        
    Returns:
        Dictionary with suggested fixes
    """
    suggestions = []
    
    for violation in violations:
        if 'suggested_fix' in violation:
            suggestions.append({
                'file': violation['file'],
                'line': violation['line'],
                'rule': violation['rule'],
                'current': violation['message'],
                'suggested': violation['suggested_fix'],
                'action': 'manual_review_required'
            })
    
    return {
        'fixed': [],  # No automatic fixes for naming (too risky)
        'suggestions': suggestions,
        'failed': []
    }


if __name__ == '__main__':
    # Allow running rule directly for testing
    import sys
    
    repo_root = Path.cwd()
    if len(sys.argv) > 1:
        repo_root = Path(sys.argv[1])
    
    result = check(repo_root)
    
    print(f"Found {len(result['violations'])} violations and {len(result['warnings'])} warnings")
    
    for violation in result['violations']:
        print(f"VIOLATION: {violation['file']}:{violation['line']} - {violation['message']}")
    
    for warning in result['warnings']:
        print(f"WARNING: {warning['file']}:{warning['line']} - {warning['message']}")
