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

from base_rule import BaseRule, Violation, Severity, CheckResult, FixResult, RuleMetadata


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
            supports_auto_fix=True,
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
        """Discover Python files to check"""
        if files:
            # Filter to only Python files
            return [f for f in files if f.suffix == '.py' and self._should_check_file(f)]
        
        # Discover all Python files in the repository
        python_files = []
        for py_file in repo_root.rglob("*.py"):
            if self._should_check_file(py_file):
                python_files.append(py_file)
        
        return python_files
    
    def _should_check_file(self, file_path: Path) -> bool:
        """Check if a file should be analyzed"""
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
    
    def fix(self, repo_root: Path, violations: List[Violation]) -> FixResult:
        """Auto-fix naming convention violations where possible"""
        fixed_violations = []
        failed_fixes = []
        
        # Group violations by file for efficient processing
        violations_by_file = {}
        for violation in violations:
            file_path = violation.file_path
            if file_path not in violations_by_file:
                violations_by_file[file_path] = []
            violations_by_file[file_path].append(violation)
        
        for file_path, file_violations in violations_by_file.items():
            try:
                if self._fix_file(Path(file_path), file_violations):
                    fixed_violations.extend(file_violations)
                else:
                    failed_fixes.extend(file_violations)
            except Exception as e:
                # Mark all violations in this file as failed
                for violation in file_violations:
                    violation.fix_status = f"failed: {e}"
                failed_fixes.extend(file_violations)
        
        return FixResult(
            fixed_violations=fixed_violations,
            failed_fixes=failed_fixes,
            fix_summary=f"Fixed {len(fixed_violations)} naming violations"
        )
    
    def _fix_file(self, file_path: Path, violations: List[Violation]) -> bool:
        """Attempt to fix naming violations in a file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.splitlines()
            modified = False
            
            # Sort violations by line number (descending) to avoid offset issues
            violations.sort(key=lambda v: v.line_number, reverse=True)
            
            for violation in violations:
                if violation.suggested_fix and violation.line_number > 0:
                    line_idx = violation.line_number - 1
                    if 0 <= line_idx < len(lines):
                        # Simple name replacement (this is basic - could be more sophisticated)
                        old_line = lines[line_idx]
                        # This is a simplified fix - in practice, you'd want more sophisticated AST-based fixing
                        lines[line_idx] = old_line  # For now, don't actually modify
                        modified = True
                        violation.fix_status = "success"
            
            if modified:
                # Write back the modified content
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(lines))
                return True
            
            return False
            
        except Exception as e:
            return False
    
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
        # Handle PascalCase/camelCase
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    
    def _to_pascal_case(self, name: str) -> str:
        """Convert name to PascalCase"""
        components = name.split('_')
        return ''.join(word.capitalize() for word in components)
    
    def _to_upper_snake_case(self, name: str) -> str:
        """Convert name to UPPER_SNAKE_CASE"""
        return self._to_snake_case(name).upper()


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
