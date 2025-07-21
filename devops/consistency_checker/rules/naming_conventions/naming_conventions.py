#!/usr/bin/env python3
"""
Naming Conventions Rule

This rule enforces consistent naming conventions across Python code:
- Function names: snake_case
- Class names: PascalCase
- Constants: UPPER_SNAKE_CASE
- Variable names: snake_case
- File names: snake_case.py
- Private members: _leading_underscore
"""

import ast
import re
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add the base directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from base_rule import BaseRule, Violation, Severity, CheckResult, RuleMetadata


class NamingConventionsRule(BaseRule):
    """Rule to enforce Python naming conventions"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        
        # Default configuration
        self.default_config = {
            'function_naming': 'snake_case',
            'class_naming': 'pascal_case',
            'constant_naming': 'upper_snake_case',
            'variable_naming': 'snake_case',
            'file_naming': 'snake_case',
            'check_private_members': True,
            'allow_single_char_vars': True,
            'exclude_files': ['__init__.py'],
            'exclude_patterns': ['test_*', '*_test.py']
        }
        
        # Apply configuration
        self.rule_config = self.default_config.copy()
        if config:
            self.rule_config.update(config)
    
    def _create_metadata(self) -> RuleMetadata:
        """Create rule metadata"""
        return RuleMetadata(
            name="naming_conventions",
            version="2.0.0",
            description="Enforces consistent Python naming conventions for functions, classes, variables, and files",
            category="code_style",
            supports_incremental=True,
            supports_parallel=True
        )
    
    def check(self, repo_root: Path, files: Optional[List[Path]] = None) -> CheckResult:
        """Check naming conventions in Python files"""
        violations = []
        warnings = []
        files_checked = 0
        lines_checked = 0
        
        try:
            target_files = self._discover_files(repo_root, files)
            
            for file_path in target_files:
                try:
                    file_violations, file_warnings, file_lines = self._check_file(file_path)
                    violations.extend(file_violations)
                    warnings.extend(file_warnings)
                    files_checked += 1
                    lines_checked += file_lines
                except Exception as e:
                    warnings.append(Violation(
                        rule_name=self.get_metadata().name,
                        file_path=str(file_path),
                        line_number=0,
                        message=f"Error checking naming conventions: {e}",
                        severity=Severity.WARNING
                    ))
                    files_checked += 1
            
            return CheckResult(
                rule_name=self.get_metadata().name,
                rule_metadata=self.get_metadata(),
                success=True,
                violations=violations,
                warnings=warnings,
                files_checked=files_checked,
                lines_checked=lines_checked
            )
            
        except Exception as e:
            return CheckResult(
                rule_name=self.get_metadata().name,
                rule_metadata=self.get_metadata(),
                success=False,
                error_message=str(e),
                violations=[],
                warnings=[]
            )
    
    def _discover_files(self, repo_root: Path, files: Optional[List[Path]] = None) -> List[Path]:
        """Discover Python files to check, skipping venv directory"""
        if files:
            # Filter to only Python files, skip venv
            return [f for f in files if f.suffix == '.py' and "venv" not in f.parts and self._should_check_file(f)]
        # Discover all Python files in the repository, skip venv
        python_files = []
        for py_file in repo_root.rglob("*.py"):
            if "venv" not in py_file.parts and self._should_check_file(py_file):
                python_files.append(py_file)
        return python_files
    
    def _should_check_file(self, file_path: Path) -> bool:
        """Check if a file should be analyzed, ignoring venv directory"""
        # Ignore any file under venv directory
        if "venv" in file_path.parts:
            return False
        # Skip excluded files
        if file_path.name in self.rule_config['exclude_files']:
            return False
        # Skip excluded patterns
        for pattern in self.rule_config['exclude_patterns']:
            if file_path.match(pattern):
                return False
        # Skip hidden files and directories
        if any(part.startswith('.') for part in file_path.parts):
            return False
        # Skip __pycache__ directories
        if '__pycache__' in file_path.parts:
            return False
        
        return True
    
    def _check_file(self, file_path: Path) -> tuple[List[Violation], List[Violation], int]:
        """Check naming conventions in a single file"""
        violations = []
        warnings = []
        
        # Check file naming convention
        file_violations = self._check_file_naming(file_path)
        violations.extend(file_violations)
        
        # Parse and check code naming
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines_checked = len(content.splitlines())
            
            # Parse AST for code analysis
            tree = ast.parse(content, filename=str(file_path))
            visitor = NamingVisitor(file_path, self.rule_config)
            visitor.visit(tree)
            
            violations.extend(visitor.violations)
            warnings.extend(visitor.warnings)
            
            return violations, warnings, lines_checked
            
        except SyntaxError as e:
            warnings.append(Violation(
                rule_name=self.get_metadata().name,
                file_path=str(file_path),
                line_number=e.lineno or 0,
                message=f"Syntax error in file: {e}",
                severity=Severity.WARNING
            ))
            return violations, warnings, 0
        except Exception as e:
            warnings.append(Violation(
                rule_name=self.get_metadata().name,
                file_path=str(file_path),
                line_number=0,
                message=f"Error parsing file: {e}",
                severity=Severity.WARNING
            ))
            return violations, warnings, 0
    
    def _check_file_naming(self, file_path: Path) -> List[Violation]:
        """Check if file name follows naming conventions"""
        violations = []
        
        file_name = file_path.stem  # Name without extension
        
        # Skip special files
        if file_name.startswith('__') and file_name.endswith('__'):
            return violations
        
        # Check file naming convention
        if self.rule_config['file_naming'] == 'snake_case':
            if not self._is_snake_case(file_name):
                suggested_name = self._to_snake_case(file_name)
                violations.append(Violation(
                    rule_name=self.get_metadata().name,
                    file_path=str(file_path),
                    line_number=0,
                    message=f"File name '{file_name}' should use snake_case (e.g., '{suggested_name}')",
                    severity=Severity.WARNING,
                    suggested_fix=f"{suggested_name}.py"
                ))
        
        return violations


class NamingVisitor(ast.NodeVisitor):
    """AST visitor to check naming conventions"""
    
    def __init__(self, file_path: Path, config: Dict[str, Any]):
        self.file_path = file_path
        self.config = config
        self.violations = []
        self.warnings = []
        self.rule_name = "naming_conventions"
    
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Check class naming"""
        if self.config['class_naming'] == 'pascal_case':
            if not self._is_pascal_case(node.name):
                suggested_name = self._to_pascal_case(node.name)
                self.violations.append(Violation(
                    rule_name=self.rule_name,
                    file_path=str(self.file_path),
                    line_number=node.lineno,
                    message=f"Class name '{node.name}' should use PascalCase (e.g., '{suggested_name}')",
                    severity=Severity.WARNING,
                    suggested_fix=suggested_name
                ))
        
        self.generic_visit(node)
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Check function naming"""
        if self.config['function_naming'] == 'snake_case':
            if not self._is_snake_case(node.name) and not node.name.startswith('__'):
                suggested_name = self._to_snake_case(node.name)
                self.violations.append(Violation(
                    rule_name=self.rule_name,
                    file_path=str(self.file_path),
                    line_number=node.lineno,
                    message=f"Function name '{node.name}' should use snake_case (e.g., '{suggested_name}')",
                    severity=Severity.WARNING,
                    suggested_fix=suggested_name
                ))
        
        self.generic_visit(node)
    
    def visit_Assign(self, node: ast.Assign) -> None:
        """Check variable naming"""
        for target in node.targets:
            if isinstance(target, ast.Name):
                name = target.id
                
                # Check if it's a constant (all uppercase with underscores)
                if self._is_constant(name):
                    if self.config['constant_naming'] == 'upper_snake_case':
                        if not self._is_upper_snake_case(name):
                            suggested_name = self._to_upper_snake_case(name)
                            self.violations.append(Violation(
                                rule_name=self.rule_name,
                                file_path=str(self.file_path),
                                line_number=node.lineno,
                                message=f"Constant '{name}' should use UPPER_SNAKE_CASE (e.g., '{suggested_name}')",
                                severity=Severity.WARNING,
                                suggested_fix=suggested_name
                            ))
                else:
                    # Regular variable
                    if self.config['variable_naming'] == 'snake_case':
                        if not self._is_snake_case(name) and len(name) > 1:  # Allow single char vars
                            suggested_name = self._to_snake_case(name)
                            self.violations.append(Violation(
                                rule_name=self.rule_name,
                                file_path=str(self.file_path),
                                line_number=node.lineno,
                                message=f"Variable '{name}' should use snake_case (e.g., '{suggested_name}')",
                                severity=Severity.WARNING,
                                suggested_fix=suggested_name
                            ))
        
        self.generic_visit(node)
    
    def _is_snake_case(self, name: str) -> bool:
        """Check if name follows snake_case convention"""
        if not name:
            return False
        return re.match(r'^[a-z_][a-z0-9_]*$', name) is not None
    
    def _is_pascal_case(self, name: str) -> bool:
        """Check if name follows PascalCase convention"""
        if not name:
            return False
        return re.match(r'^[A-Z][a-zA-Z0-9]*$', name) is not None
    
    def _is_upper_snake_case(self, name: str) -> bool:
        """Check if name follows UPPER_SNAKE_CASE convention"""
        if not name:
            return False
        return re.match(r'^[A-Z_][A-Z0-9_]*$', name) is not None
    
    def _is_constant(self, name: str) -> bool:
        """Check if name appears to be a constant"""
        return name.isupper() and '_' in name
    
    def _to_snake_case(self, name: str) -> str:
        """Convert name to snake_case"""
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    
    def _to_pascal_case(self, name: str) -> str:
        """Convert name to PascalCase"""
        components = name.split('_')
        return ''.join(word.capitalize() for word in components)
    
    def _to_upper_snake_case(self, name: str) -> str:
        """Convert name to UPPER_SNAKE_CASE"""
        return self._to_snake_case(name).upper()
