#!/usr/bin/env python3
"""
Code Complexity Consistency Rule

This rule checks for code complexity issues including:
- Cyclomatic complexity of functions
- Nesting depth limits
- Function length limits
- Class complexity metrics
"""

import ast
from pathlib import Path
from typing import Dict, List, Any, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))
from base_rule import BaseRule, CheckResult, Violation, RuleMetadata, Severity


class CodeComplexity(BaseRule):
    """
    Checks code complexity metrics to ensure maintainable code
    
    Violations include:
    - Functions with high cyclomatic complexity
    - Deeply nested code blocks
    - Overly long functions
    - Classes with too many methods
    
    Configuration:
    - max_cyclomatic_complexity: Maximum allowed cyclomatic complexity (default: 10)
    - max_nesting_depth: Maximum allowed nesting depth (default: 4)
    - max_function_length: Maximum lines per function (default: 50)
    - max_class_methods: Maximum methods per class (default: 20)
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
        # Configuration parameters
        self.max_cyclomatic_complexity = self.config.get('max_cyclomatic_complexity', 10)
        self.max_nesting_depth = self.config.get('max_nesting_depth', 4)
        self.max_function_length = self.config.get('max_function_length', 50)
        self.max_class_methods = self.config.get('max_class_methods', 20)
        self.ignore_test_files = self.config.get('ignore_test_files', True)
    
    def _create_metadata(self) -> RuleMetadata:
        """Create metadata for this rule"""
        return RuleMetadata(
            name="code_complexity",
            version="1.0.0",
            description="Checks code complexity metrics including cyclomatic complexity and nesting depth",
            category="code_quality",
            tags={"complexity", "maintainability", "quality"},
            
            supports_auto_fix=False,  # Complexity fixes require human intervention
            supports_incremental=True,
            supports_parallel=True,
            
            estimated_runtime="medium",
            memory_usage="low",
            
            configurable_parameters={
                "max_cyclomatic_complexity": {
                    "type": "integer",
                    "description": "Maximum allowed cyclomatic complexity",
                    "default": 10,
                    "minimum": 1
                },
                "max_nesting_depth": {
                    "type": "integer", 
                    "description": "Maximum allowed nesting depth",
                    "default": 4,
                    "minimum": 1
                },
                "max_function_length": {
                    "type": "integer",
                    "description": "Maximum lines per function",
                    "default": 50,
                    "minimum": 5
                },
                "max_class_methods": {
                    "type": "integer",
                    "description": "Maximum methods per class",
                    "default": 20,
                    "minimum": 1
                }
            },
            
            author="Consistency Team",
            maintainer="consistency@company.com",
            examples=[
                "# High complexity function (bad)",
                "def complex_function(x):",
                "    if x > 0:",
                "        if x > 10:",
                "            if x > 100:",
                "                return 'high'",
                "",
                "# Better approach (good)",
                "def simple_function(x):",
                "    if x <= 0: return 'zero'",
                "    if x <= 10: return 'low'",
                "    return 'high'"
            ]
        )
    
    def get_file_patterns(self) -> List[str]:
        """Define which files this rule should check"""
        return ["**/*.py"]
    
    def should_check_file(self, file_path: Path, repo_root: Path) -> bool:
        """Determine if a file should be checked"""
        if not super().should_check_file(file_path, repo_root):
            return False
        
        # Skip test files if configured
        if self.ignore_test_files:
            file_name = file_path.name.lower()
            if (file_name.startswith('test_') or 
                file_name.endswith('_test.py') or
                'test' in file_path.parts):
                return False
        
        return True
    
    def check(self, repo_root: Path, files: Optional[List[Path]] = None) -> CheckResult:
        """Execute the complexity check"""
        violations = []
        warnings = []
        files_checked = 0
        lines_checked = 0
        
        # Discover files to check
        if files:
            files_to_check = [f for f in files if self.should_check_file(f, repo_root)]
        else:
            files_to_check = self._discover_files(repo_root)
        
        # Process each file
        for file_path in files_to_check:
            try:
                file_violations, file_warnings, file_lines = self._check_file(file_path, repo_root)
                violations.extend(file_violations)
                warnings.extend(file_warnings)
                files_checked += 1
                lines_checked += file_lines
                
            except Exception as e:
                warning = self.create_violation(
                    file_path=file_path,
                    line_number=0,
                    message=f"Error analyzing file: {e}",
                    severity=Severity.WARNING
                )
                warnings.append(warning)
        
        return CheckResult(
            rule_name=self.get_metadata().name,
            rule_metadata=self.get_metadata(),
            success=True,
            violations=violations,
            warnings=warnings,
            files_checked=files_checked,
            lines_checked=lines_checked
        )
    
    def _discover_files(self, repo_root: Path) -> List[Path]:
        """Discover Python files to check"""
        files = []
        for pattern in self.get_file_patterns():
            files.extend(repo_root.glob(pattern))
        
        return [f for f in files if f.is_file() and self.should_check_file(f, repo_root)]
    
    def _check_file(self, file_path: Path, repo_root: Path) -> tuple[List[Violation], List[Violation], int]:
        """Check complexity in a single file"""
        violations = []
        warnings = []
        
        # Read file content
        content = self.read_file_safely(file_path)
        if content is None:
            return [], [], 0
        
        lines = content.splitlines()
        line_count = len(lines)
        
        try:
            # Parse as AST
            tree = ast.parse(content, filename=str(file_path))
            
            # Analyze complexity
            complexity_analyzer = ComplexityAnalyzer(
                file_path, 
                self.max_cyclomatic_complexity,
                self.max_nesting_depth,
                self.max_function_length,
                self.max_class_methods
            )
            
            complexity_analyzer.visit(tree)
            
            # Convert analysis results to violations
            for issue in complexity_analyzer.issues:
                context = self.get_code_context(file_path, issue['line'], 2)
                
                violation = self.create_violation(
                    file_path=file_path,
                    line_number=issue['line'],
                    message=issue['message'],
                    severity=issue['severity'],
                    **context
                )
                
                if issue['severity'] == Severity.ERROR:
                    violations.append(violation)
                else:
                    warnings.append(violation)
            
        except SyntaxError as e:
            # Handle syntax errors gracefully
            warning = self.create_violation(
                file_path=file_path,
                line_number=getattr(e, 'lineno', 0),
                message=f"Syntax error prevents complexity analysis: {e}",
                severity=Severity.WARNING
            )
            warnings.append(warning)
        
        return violations, warnings, line_count


class ComplexityAnalyzer(ast.NodeVisitor):
    """AST visitor to analyze code complexity"""
    
    def __init__(self, file_path: Path, max_complexity: int, max_nesting: int, 
                 max_function_length: int, max_class_methods: int):
        self.file_path = file_path
        self.max_complexity = max_complexity
        self.max_nesting = max_nesting
        self.max_function_length = max_function_length
        self.max_class_methods = max_class_methods
        
        self.issues = []
        self.current_nesting = 0
        self.class_methods = {}
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Analyze function complexity"""
        # Calculate cyclomatic complexity
        complexity = self._calculate_cyclomatic_complexity(node)
        
        if complexity > self.max_complexity:
            self.issues.append({
                'line': node.lineno,
                'message': f"Function '{node.name}' has high cyclomatic complexity ({complexity} > {self.max_complexity})",
                'severity': Severity.ERROR if complexity > self.max_complexity * 1.5 else Severity.WARNING
            })
        
        # Check function length
        function_lines = (node.end_lineno or node.lineno) - node.lineno + 1
        if function_lines > self.max_function_length:
            self.issues.append({
                'line': node.lineno,
                'message': f"Function '{node.name}' is too long ({function_lines} > {self.max_function_length} lines)",
                'severity': Severity.WARNING
            })
        
        # Check nesting depth within function
        self._check_nesting_depth(node, node.name)
        
        # Continue visiting child nodes
        self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Analyze async function complexity"""
        self.visit_FunctionDef(node)  # Same analysis as regular functions
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Analyze class complexity"""
        # Count methods in class
        method_count = 0
        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                method_count += 1
        
        if method_count > self.max_class_methods:
            self.issues.append({
                'line': node.lineno,
                'message': f"Class '{node.name}' has too many methods ({method_count} > {self.max_class_methods})",
                'severity': Severity.WARNING
            })
        
        # Continue visiting child nodes
        self.generic_visit(node)
    
    def _calculate_cyclomatic_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity for a function"""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            # Decision points that increase complexity
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, (ast.ExceptHandler, ast.Try)):
                complexity += 1
            elif isinstance(child, ast.With):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                # Each additional condition in boolean operations
                complexity += len(child.values) - 1
            elif isinstance(child, ast.ListComp):
                # List comprehensions with conditions
                complexity += sum(1 for gen in child.generators if gen.ifs)
            elif isinstance(child, (ast.DictComp, ast.SetComp, ast.GeneratorExp)):
                # Other comprehensions with conditions
                complexity += sum(1 for gen in child.generators if gen.ifs)
        
        return complexity
    
    def _check_nesting_depth(self, node: ast.FunctionDef, function_name: str):
        """Check nesting depth within a function"""
        max_depth_found = self._get_max_nesting_depth(node)
        
        if max_depth_found > self.max_nesting:
            self.issues.append({
                'line': node.lineno,
                'message': f"Function '{function_name}' has excessive nesting depth ({max_depth_found} > {self.max_nesting})",
                'severity': Severity.WARNING
            })
    
    def _get_max_nesting_depth(self, node: ast.AST, current_depth: int = 0) -> int:
        """Recursively calculate maximum nesting depth"""
        max_depth = current_depth
        
        for child in ast.iter_child_nodes(node):
            # Nodes that increase nesting depth
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor, 
                                ast.With, ast.AsyncWith, ast.Try)):
                child_depth = self._get_max_nesting_depth(child, current_depth + 1)
                max_depth = max(max_depth, child_depth)
            else:
                child_depth = self._get_max_nesting_depth(child, current_depth)
                max_depth = max(max_depth, child_depth)
        
        return max_depth
