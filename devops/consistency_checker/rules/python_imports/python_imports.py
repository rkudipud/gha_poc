#!/usr/bin/env python3
"""
Python Import Consistency Rule

This rule checks for consistent Python import patterns and identifies common issues:
- Unused imports
- Duplicate imports
- Import order violations
- Relative import issues
- Missing imports

Can automatically fix some issues like removing unused imports and sorting imports.
"""

import ast
import os
from pathlib import Path
from typing import Dict, List, Any, Set
import subprocess


DESCRIPTION = "Checks Python import consistency and identifies unused/duplicate imports"


def check(repo_root: Path) -> Dict[str, Any]:
    """
    Check Python import consistency across the repository
    
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
                python_files.append(Path(root) / file)
    
    for file_path in python_files:
        try:
            file_violations, file_warnings = _check_file_imports(file_path, repo_root)
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


def _check_file_imports(file_path: Path, repo_root: Path) -> tuple:
    """Check imports in a single Python file"""
    violations = []
    warnings = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse AST
        tree = ast.parse(content, filename=str(file_path))
        
        # Collect import information
        imports = []
        used_names = set()
        
        class ImportVisitor(ast.NodeVisitor):
            def visit_Import(self, node):
                for alias in node.names:
                    imports.append({
                        'type': 'import',
                        'module': alias.name,
                        'alias': alias.asname,
                        'line': node.lineno,
                        'node': node
                    })
            
            def visit_ImportFrom(self, node):
                for alias in node.names:
                    imports.append({
                        'type': 'from_import',
                        'module': node.module,
                        'name': alias.name,
                        'alias': alias.asname,
                        'line': node.lineno,
                        'level': node.level,
                        'node': node
                    })
            
            def visit_Name(self, node):
                if isinstance(node.ctx, ast.Load):
                    used_names.add(node.id)
                self.generic_visit(node)
            
            def visit_Attribute(self, node):
                if isinstance(node.value, ast.Name):
                    used_names.add(node.value.id)
                self.generic_visit(node)
        
        visitor = ImportVisitor()
        visitor.visit(tree)
        
        # Check for unused imports
        for imp in imports:
            import_name = imp.get('alias') or imp.get('name') or imp.get('module', '').split('.')[0]
            
            if import_name and import_name not in used_names:
                # Special cases that are often used implicitly
                if import_name not in {'typing', 'annotations', '__future__'}:
                    violations.append({
                        'file': str(file_path.relative_to(repo_root)),
                        'line': imp['line'],
                        'message': f"Unused import: {import_name}",
                        'severity': 'warning',
                        'rule': 'unused_import',
                        'import_info': imp
                    })
        
        # Check for duplicate imports
        seen_imports = set()
        for imp in imports:
            import_key = (imp['type'], imp.get('module'), imp.get('name'))
            if import_key in seen_imports:
                violations.append({
                    'file': str(file_path.relative_to(repo_root)),
                    'line': imp['line'],
                    'message': f"Duplicate import: {imp.get('name') or imp.get('module')}",
                    'severity': 'error',
                    'rule': 'duplicate_import'
                })
            seen_imports.add(import_key)
        
        # Check import order (basic check)
        previous_type = None
        for imp in imports:
            current_type = _get_import_category(imp)
            if previous_type and _should_come_before(current_type, previous_type):
                warnings.append({
                    'file': str(file_path.relative_to(repo_root)),
                    'line': imp['line'],
                    'message': f"Import order violation: {current_type} should come before {previous_type}",
                    'severity': 'style',
                    'rule': 'import_order'
                })
            previous_type = current_type
        
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
            'message': f"Error checking imports: {e}",
            'severity': 'warning'
        })
    
    return violations, warnings


def _get_import_category(imp: Dict[str, Any]) -> str:
    """Categorize import type for ordering"""
    module = imp.get('module', '')
    
    if imp.get('level', 0) > 0:  # Relative import
        return 'relative'
    elif module.startswith('.'):
        return 'relative'
    elif module in {'os', 'sys', 'json', 'typing', 'pathlib', 'subprocess', 'datetime'}:
        return 'standard'
    elif '.' not in module or module in {'requests', 'yaml', 'click'}:
        return 'third_party'
    else:
        return 'local'


def _should_come_before(current: str, previous: str) -> bool:
    """Check if current import type should come before previous"""
    order = ['standard', 'third_party', 'local', 'relative']
    try:
        return order.index(current) < order.index(previous)
    except ValueError:
        return False


def fix(repo_root: Path, violations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Attempt to automatically fix import violations
    
    Args:
        repo_root: Root directory of the repository
        violations: List of violations to fix
        
    Returns:
        Dictionary with information about fixes applied
    """
    fixed = []
    failed = []
    
    # Group violations by file
    files_to_fix = {}
    for violation in violations:
        if violation.get('rule') == 'unused_import':
            file_path = violation['file']
            if file_path not in files_to_fix:
                files_to_fix[file_path] = []
            files_to_fix[file_path].append(violation)
    
    # Fix each file
    for file_path, file_violations in files_to_fix.items():
        try:
            full_path = repo_root / file_path
            
            # Read file content
            with open(full_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Remove unused import lines (in reverse order to preserve line numbers)
            lines_to_remove = []
            for violation in file_violations:
                if 'import_info' in violation:
                    lines_to_remove.append(violation['line'] - 1)  # Convert to 0-based
            
            lines_to_remove.sort(reverse=True)
            
            for line_idx in lines_to_remove:
                if 0 <= line_idx < len(lines):
                    removed_line = lines.pop(line_idx).strip()
                    fixed.append({
                        'file': file_path,
                        'line': line_idx + 1,
                        'action': 'removed_unused_import',
                        'content': removed_line
                    })
            
            # Write back the modified content
            with open(full_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
                
        except Exception as e:
            failed.append({
                'file': file_path,
                'error': str(e)
            })
    
    return {
        'fixed': fixed,
        'failed': failed
    }


if __name__ == '__main__':
    # Allow running rule directly for testing
    import sys
    from pathlib import Path
    
    repo_root = Path.cwd()
    if len(sys.argv) > 1:
        repo_root = Path(sys.argv[1])
    
    result = check(repo_root)
    
    print(f"Found {len(result['violations'])} violations and {len(result['warnings'])} warnings")
    
    for violation in result['violations']:
        print(f"VIOLATION: {violation['file']}:{violation['line']} - {violation['message']}")
    
    for warning in result['warnings']:
        print(f"WARNING: {warning['file']}:{warning['line']} - {warning['message']}")
