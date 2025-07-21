#!/usr/bin/env python3
"""
Template for Creating New Consistency Rules

Copy this template to create new rules. Replace 'rule_template' with your rule name
and implement the required methods.

Rule Development Checklist:
1. Choose a descriptive rule name (e.g., 'line_length', 'function_complexity')
2. Define file patterns that your rule should check
3. Implement check() method with your rule logic
4. Test your rule thoroughly
5. Add configuration to rule_template_config.yml
7. Document the rule in _create_metadata()
"""

import ast
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass

# Add the consistency_checker directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from base_rule import BaseRule, CheckResult, Violation, RuleMetadata, Severity


class RuleTemplate(BaseRule):
    """
    Template Rule - Replace with your rule description
    
    This rule template provides a starting point for creating new consistency rules.
    Replace this docstring with a description of what your rule checks.
    
    Example violations:
    - Describe what conditions trigger violations
    - Provide examples of problematic code
    
    Configuration:
    - List any configuration parameters
    - Explain their effects
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
        # Rule-specific configuration with defaults
        self.max_threshold = self.config.get('max_threshold', 10)
        self.ignore_patterns = self.config.get('ignore_patterns', [])
        self.strict_mode = self.config.get('strict_mode', False)
        
        # Internal state
        self.processed_files = 0
        self.processed_lines = 0
    
    def _create_metadata(self) -> RuleMetadata:
        """Create metadata for this rule"""
        return RuleMetadata(
            name="rule_template",
            version="1.0.0",
            description="Template for creating new consistency rules",
            category="template",
            supports_incremental=True,
            supports_parallel=True
        )
    
    def get_file_patterns(self) -> List[str]:
        """Define which files this rule should check"""
        return [
            "**/*.py",  # Python files
            "**/*.pyx",  # Cython files
            # Add other patterns as needed
        ]
    
    def should_check_file(self, file_path: Path, repo_root: Path) -> bool:
        """Determine if a file should be checked by this rule, ignoring venv directory"""
        if "venv" in file_path.parts:
            return False
        # Call parent implementation first
        if not super().should_check_file(file_path, repo_root):
            return False
        # Additional file filtering logic
        relative_path = str(file_path.relative_to(repo_root))
        # Skip files matching ignore patterns
        import fnmatch
        for pattern in self.ignore_patterns:
            if fnmatch.fnmatch(relative_path, pattern):
                return False
        # Skip test files in strict mode (example logic)
        if self.strict_mode and "test" in file_path.name.lower():
            return False
        return True
    
    def check(self, repo_root: Path, files: Optional[List[Path]] = None) -> CheckResult:
        """
        Execute the rule check
        
        Args:
            repo_root: Root directory of the repository
            files: Optional list of specific files to check
            
        Returns:
            CheckResult containing violations and metadata
        """
        violations = []
        warnings = []
        
        # Determine files to check
        if files:
            files_to_check = [f for f in files if self.should_check_file(f, repo_root)]
        else:
            files_to_check = self._discover_files(repo_root)
        
        # Process each file
        for file_path in files_to_check:
            try:
                file_violations, file_warnings = self._check_file(file_path, repo_root)
                violations.extend(file_violations)
                warnings.extend(file_warnings)
                self.processed_files += 1
                
            except Exception as e:
                # Handle file processing errors gracefully
                warning = self.create_violation(
                    file_path=file_path,
                    line_number=0,
                    message=f"Error processing file: {e}",
                    severity=Severity.WARNING
                )
                warnings.append(warning)
        
        return CheckResult(
            rule_name=self.get_metadata().name,
            rule_metadata=self.get_metadata(),
            success=True,  # Set to False if rule execution failed
            violations=violations,
            warnings=warnings,
            files_checked=self.processed_files,
            lines_checked=self.processed_lines,
            waiver_count=0  # This will be updated by the framework
        )
    
    def _discover_files(self, repo_root: Path) -> List[Path]:
        """Discover files that match this rule's patterns, skipping venv directory"""
        files = []
        for pattern in self.get_file_patterns():
            files.extend(repo_root.glob(pattern))
        # Filter and deduplicate, skip venv
        unique_files = []
        seen = set()
        for file_path in files:
            if file_path.is_file() and file_path not in seen:
                if "venv" not in file_path.parts and self.should_check_file(file_path, repo_root):
                    unique_files.append(file_path)
                    seen.add(file_path)
        return sorted(unique_files)
    
    def _check_file(self, file_path: Path, repo_root: Path) -> tuple[List[Violation], List[Violation]]:
        """
        Check a single file for violations
        
        Returns:
            Tuple of (violations, warnings)
        """
        violations = []
        warnings = []
        
        # Read file content safely
        content = self.read_file_safely(file_path)
        if content is None:
            warning = self.create_violation(
                file_path=file_path,
                line_number=0,
                message="Could not read file (encoding issue)",
                severity=Severity.WARNING
            )
            return [], [warning]
        
        lines = content.splitlines()
        self.processed_lines += len(lines)
        
        # Example: Check each line for violations
        for line_num, line in enumerate(lines, 1):
            line_violations = self._check_line(file_path, line_num, line, content)
            violations.extend(line_violations)
        
        # Example: Check file-level violations
        file_violations = self._check_file_level(file_path, content, lines)
        violations.extend(file_violations)
        
        return violations, warnings
    
    def _check_line(self, file_path: Path, line_num: int, line: str, full_content: str) -> List[Violation]:
        """
        Check a single line for violations
        
        Replace this with your actual line-checking logic
        """
        violations = []
        
        # Example: Check line length
        if len(line) > self.max_threshold:
            context = self.get_code_context(file_path, line_num)
            
            violation = self.create_violation(
                file_path=file_path,
                line_number=line_num,
                message=f"Line too long ({len(line)} > {self.max_threshold} characters)",
                severity=Severity.ERROR,
                **context
            )
            violations.append(violation)
        
        # Example: Check for specific patterns
        if "TODO" in line and self.strict_mode:
            violation = self.create_violation(
                file_path=file_path,
                line_number=line_num,
                message="TODO comments not allowed in strict mode",
                severity=Severity.WARNING,
                code_snippet=line.strip()
            )
            violations.append(violation)
        
        return violations
    
    def _check_file_level(self, file_path: Path, content: str, lines: List[str]) -> List[Violation]:
        """
        Check file-level violations
        
        Replace this with your actual file-level checking logic
        """
        violations = []
        
        # Example: Check file size
        if len(lines) > 1000:
            violation = self.create_violation(
                file_path=file_path,
                line_number=0,
                message=f"File too long ({len(lines)} lines)",
                severity=Severity.WARNING
            )
            violations.append(violation)
        
        # Example: Parse as Python AST for structural checks
        try:
            tree = ast.parse(content)
            ast_violations = self._check_ast(file_path, tree)
            violations.extend(ast_violations)
        except SyntaxError:
            # Not a valid Python file, skip AST checks
            pass
        
        return violations
    
    def _check_ast(self, file_path: Path, tree: ast.AST) -> List[Violation]:
        """
        Check Python AST for structural violations
        
        Replace this with your actual AST checking logic
        """
        violations = []
        
        # Example: Check function complexity
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Count complexity (simplified example)
                complexity = self._calculate_complexity(node)
                
                if complexity > self.max_threshold:
                    violation = self.create_violation(
                        file_path=file_path,
                        line_number=node.lineno,
                        message=f"Function '{node.name}' too complex (complexity: {complexity})",
                        severity=Severity.WARNING
                    )
                    violations.append(violation)
        
        return violations
    
    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity (simplified example)"""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.Try, ast.With)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate rule configuration"""
        # Check required parameters
        if 'max_threshold' in config:
            if not isinstance(config['max_threshold'], int) or config['max_threshold'] < 1:
                return False
        
        if 'ignore_patterns' in config:
            if not isinstance(config['ignore_patterns'], list):
                return False
        
        if 'strict_mode' in config:
            if not isinstance(config['strict_mode'], bool):
                return False
        
        return True


# Register the rule (this would be done by the framework)
# from ...base_rule import rule_registry
# rule_registry.register(RuleTemplate)
