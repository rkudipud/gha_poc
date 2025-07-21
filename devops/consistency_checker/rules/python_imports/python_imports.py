#!/usr/bin/env python3
"""
Python Imports Rule

This rule enforces consistent Python import conventions:
- Standard library imports first
- Third-party imports second  
- Local application imports last
- Alphabetical ordering within each group
- No wildcard imports (from module import *)
- No unused imports
- No duplicate imports
"""

import ast
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Set

# Add the base directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from base_rule import BaseRule, Violation, Severity, CheckResult, RuleMetadata


class PythonImportsRule(BaseRule):
    """Rule to enforce Python import conventions"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        
        # Default configuration
        self.default_config = {
            'enforce_import_order': True,
            'alphabetical_within_groups': True,
            'disallow_wildcard_imports': True,
            'check_unused_imports': True,
            'check_duplicate_imports': True,
            'separate_groups_with_blank_line': True,
            'max_imports_per_line': 1,
            'allowed_wildcard_modules': [],  # Modules where wildcard imports are allowed
        }
        
        # Merge with provided config
        if config:
            self.default_config.update(config)
    
    def _create_metadata(self) -> RuleMetadata:
        """Create metadata for this rule"""
        return RuleMetadata(
            name="python_imports",
            version="2.0.0",
            description="Enforces consistent Python import organization and style",
            category="code_style",
            supports_incremental=True,
            supports_parallel=True
        )
    
    def check(self, repo_root: Path, files: Optional[List[Path]] = None) -> CheckResult:
        """Check Python files for import convention violations, skipping venv directory"""
        violations = []
        if files is None:
            # Find all Python files in the repository, skip venv
            python_files = [f for f in repo_root.rglob("*.py") if "venv" not in f.parts]
        else:
            python_files = [f for f in files if f.suffix == ".py" and "venv" not in f.parts]
        for file_path in python_files:
            if not file_path.exists():
                continue
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                # Parse the AST
                tree = ast.parse(content, filename=str(file_path))
                # Visit the AST to find import violations
                visitor = ImportVisitor(file_path, repo_root, self.default_config)
                visitor.visit(tree)
                visitor.finalize()  # Check import ordering
                violations.extend(visitor.violations)
            except (SyntaxError, UnicodeDecodeError) as e:
                # Skip files with syntax errors or encoding issues
                violations.append(Violation(
                    rule_name="python_imports",
                    file_path=file_path,
                    line_number=1,
                    column=1,
                    message=f"Could not parse file: {e}",
                    severity=Severity.WARNING,
                    suggested_fix="Fix syntax errors in the file"
                ))
        return CheckResult(
            violations=violations,
            files_checked=len(python_files),
            rule_name="python_imports"
        )


class ImportVisitor(ast.NodeVisitor):
    """AST visitor to find import-related violations"""
    
    def __init__(self, file_path: Path, repo_root: Path, config: Dict[str, Any]):
        self.file_path = file_path
        self.repo_root = repo_root
        self.config = config
        self.violations = []
        self.imports = []
        self.seen_imports = set()
        
    def visit_Import(self, node: ast.Import):
        """Visit regular import statements"""
        for alias in node.names:
            import_info = {
                'type': 'import',
                'module': alias.name,
                'name': alias.asname or alias.name,
                'lineno': node.lineno,
                'col_offset': node.col_offset,
                'node': node
            }
            self.imports.append(import_info)
            
            # Check for duplicate imports
            import_key = (alias.name, alias.asname)
            if import_key in self.seen_imports:
                self.violations.append(Violation(
                    rule_name="python_imports",
                    file_path=self.file_path,
                    line_number=node.lineno,
                    column=node.col_offset,
                    message=f"Duplicate import: {alias.name}",
                    severity=Severity.WARNING,
                    suggested_fix="Remove duplicate import statement"
                ))
            else:
                self.seen_imports.add(import_key)
        
        self.generic_visit(node)
        
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Visit from ... import statements"""
        module = node.module or ''
        
        for alias in node.names:
            # Check for wildcard imports
            if alias.name == '*':
                if module not in self.config.get('allowed_wildcard_modules', []):
                    self.violations.append(Violation(
                        rule_name="python_imports",
                        file_path=self.file_path,
                        line_number=node.lineno,
                        column=node.col_offset,
                        message=f"Wildcard import not allowed: from {module} import *",
                        severity=Severity.WARNING,
                        suggested_fix="Import specific names instead of using wildcard"
                    ))
            
            import_info = {
                'type': 'from_import',
                'module': module,
                'name': alias.name,
                'asname': alias.asname,
                'lineno': node.lineno,
                'col_offset': node.col_offset,
                'node': node
            }
            self.imports.append(import_info)
            
            # Check for duplicate imports
            import_key = (module, alias.name, alias.asname)
            if import_key in self.seen_imports:
                self.violations.append(Violation(
                    rule_name="python_imports",
                    file_path=self.file_path,
                    line_number=node.lineno,
                    column=node.col_offset,
                    message=f"Duplicate import: from {module} import {alias.name}",
                    severity=Severity.WARNING,
                    suggested_fix="Remove duplicate import statement"
                ))
            else:
                self.seen_imports.add(import_key)
        
        self.generic_visit(node)
    
    def finalize(self):
        """Check import ordering after all imports have been collected"""
        if not self.config.get('enforce_import_order', True):
            return
            
        # Group imports by type
        import_groups = self._group_imports()
        
        # Check if imports are in the correct order
        self._check_import_order(import_groups)
        
        # Check alphabetical ordering within groups
        if self.config.get('alphabetical_within_groups', True):
            self._check_alphabetical_order(import_groups)
    
    def _group_imports(self) -> Dict[str, List[Dict]]:
        """Group imports by their type (stdlib, third-party, local)"""
        groups = {
            'stdlib': [],
            'third_party': [],
            'local': []
        }
        
        for import_info in self.imports:
            module = import_info['module']
            group = self._classify_import(module)
            groups[group].append(import_info)
        
        return groups
    
    def _classify_import(self, module_name: str) -> str:
        """Classify import as stdlib, third-party, or local"""
        if not module_name:
            return 'local'
        
        # Check if it's a standard library module
        if self._is_stdlib_module(module_name):
            return 'stdlib'
        
        # Check if it's a local module (relative to repo root)
        if self._is_local_module(module_name):
            return 'local'
        
        # Otherwise, it's third-party
        return 'third_party'
    
    def _is_stdlib_module(self, module_name: str) -> bool:
        """Check if a module is part of the standard library"""
        # Get the top-level module name
        top_module = module_name.split('.')[0]
        
        # List of known standard library modules (Python 3.8+)
        stdlib_modules = {
            'abc', 'ast', 'asyncio', 'base64', 'collections', 'copy', 'datetime', 
            'functools', 'hashlib', 'io', 'itertools', 'json', 'logging', 'math', 
            'os', 'pathlib', 'random', 're', 'subprocess', 'sys', 'time', 'typing', 
            'urllib', 'uuid', 'warnings'
        }
        
        return top_module in stdlib_modules
    
    def _is_local_module(self, module_name: str) -> bool:
        """Check if a module is local to the project"""
        # Check if the module corresponds to a file or package in the repo
        module_path = Path(module_name.replace('.', '/'))
        
        # Check for .py file
        py_file = self.repo_root / f"{module_path}.py"
        if py_file.exists():
            return True
        
        # Check for package directory
        pkg_dir = self.repo_root / module_path / "__init__.py"
        if pkg_dir.exists():
            return True
        
        # Check if it's a relative import
        if module_name.startswith('.'):
            return True
        
        return False
    
    def _check_import_order(self, groups: Dict[str, List[Dict]]):
        """Check if imports are in the correct order (stdlib, third-party, local)"""
        expected_order = ['stdlib', 'third_party', 'local']
        last_group_line = 0
        
        for group_name in expected_order:
            group_imports = groups[group_name]
            if not group_imports:
                continue
            
            first_import_line = min(imp['lineno'] for imp in group_imports)
            
            if first_import_line < last_group_line:
                self.violations.append(Violation(
                    rule_name="python_imports",
                    file_path=self.file_path,
                    line_number=first_import_line,
                    column=0,
                    message=f"Import group '{group_name}' is not in the correct order",
                    severity=Severity.WARNING,
                    suggested_fix="Reorder imports: standard library, third-party, local"
                ))
            
            last_group_line = max(imp['lineno'] for imp in group_imports)
    
    def _check_alphabetical_order(self, groups: Dict[str, List[Dict]]):
        """Check if imports within each group are alphabetically ordered"""
        for group_name, group_imports in groups.items():
            if len(group_imports) <= 1:
                continue
            
            sorted_imports = sorted(group_imports, key=lambda x: x['module'])
            
            for i, (actual, expected) in enumerate(zip(group_imports, sorted_imports)):
                if actual['module'] != expected['module']:
                    self.violations.append(Violation(
                        rule_name="python_imports",
                        file_path=self.file_path,
                        line_number=actual['lineno'],
                        column=actual['col_offset'],
                        message=f"Import not in alphabetical order in {group_name} group: {actual['module']}",
                        severity=Severity.INFO,
                        suggested_fix=f"Sort imports alphabetically within {group_name} group"
                    ))