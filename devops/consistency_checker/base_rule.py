#!/usr/bin/env python3
"""
Base Rule Interface for Consistency Checker Framework

This module defines the standard interface that all consistency rules must implement.
It provides a consistent API for rule development, execution, and integration.
"""

import abc
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Set
import uuid


class Severity(Enum):
    """Violation severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"





@dataclass
class Violation:
    """Represents a single rule violation"""
    # Unique identifier for this violation instance
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Rule identification
    rule_name: str = ""
    rule_category: str = ""
    
    # Location information
    file_path: str = ""
    line_number: int = 0
    column: int = 0
    end_line: int = 0
    end_column: int = 0
    
    # Violation details
    message: str = ""
    description: str = ""
    severity: Severity = Severity.ERROR
    
    # Code context
    code_snippet: str = ""
    context_lines_before: List[str] = field(default_factory=list)
    context_lines_after: List[str] = field(default_factory=list)
    
    # Suggested fixes
    suggested_fix: Optional[str] = None
    
    # Additional metadata
    tags: Set[str] = field(default_factory=set)
    references: List[str] = field(default_factory=list)  # URLs, tickets, etc.
    custom_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_waiver_line(self) -> str:
        """Generate waiver line for this violation"""
        return f"{self.file_path}:{self.line_number}:{self.column}: {self.rule_name} {self.message}"
    
    def get_unique_key(self) -> str:
        """Get unique key for waiver matching"""
        return f"{self.rule_name}:{self.file_path}:{self.line_number}:{self.message[:100]}"





@dataclass
class RuleMetadata:
    """Metadata about a rule"""
    name: str = ""
    version: str = "1.0.0"
    description: str = ""
    category: str = "general"
    tags: Set[str] = field(default_factory=set)
    
    # Rule capabilities
    supports_incremental: bool = True
    supports_parallel: bool = True
    
    # Performance characteristics
    estimated_runtime: str = "fast"  # fast, medium, slow
    memory_usage: str = "low"  # low, medium, high
    
    # Configuration
    configurable_parameters: Dict[str, Any] = field(default_factory=dict)
    default_config: Dict[str, Any] = field(default_factory=dict)
    
    # Dependencies
    required_tools: List[str] = field(default_factory=list)
    python_dependencies: List[str] = field(default_factory=list)
    
    # Documentation
    documentation_url: Optional[str] = None
    examples: List[str] = field(default_factory=list)
    
    # Maintenance
    author: str = ""
    maintainer: str = ""
    last_updated: Optional[datetime] = None


@dataclass
class CheckResult:
    """Result of a rule execution"""
    rule_name: str = ""
    rule_metadata: Optional[RuleMetadata] = None
    
    # Execution status
    success: bool = True
    error_message: str = ""
    execution_time: float = 0.0
    
    # Results
    violations: List[Violation] = field(default_factory=list)
    warnings: List[Violation] = field(default_factory=list)
    info_messages: List[str] = field(default_factory=list)
    
    # Statistics
    files_checked: int = 0
    lines_checked: int = 0
    
    # Waiver information
    waived_violations: List[Violation] = field(default_factory=list)
    waiver_count: int = 0
    
    # Performance metrics
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def passed(self) -> bool:
        """Check if rule passed (no error-level violations)"""
        return self.success and len([v for v in self.violations if v.severity in [Severity.ERROR, Severity.CRITICAL]]) == 0
    
    @property
    def total_violations(self) -> int:
        """Total number of violations including warnings"""
        return len(self.violations) + len(self.warnings)
    
    def get_violations_by_severity(self, severity: Severity) -> List[Violation]:
        """Get violations filtered by severity"""
        return [v for v in self.violations if v.severity == severity]


class BaseRule(abc.ABC):
    """Base class for all consistency rules"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize rule with optional configuration"""
        self.config = config or {}
        self._metadata = self._create_metadata()
    
    @abc.abstractmethod
    def check(self, repo_root: Path, files: Optional[List[Path]] = None) -> CheckResult:
        """
        Execute the rule check
        
        Args:
            repo_root: Root directory of the repository
            files: Optional list of specific files to check (for incremental checking)
            
        Returns:
            CheckResult containing violations and metadata
        """
        pass
    
    @abc.abstractmethod
    def _create_metadata(self) -> RuleMetadata:
        """Create metadata for this rule"""
        pass
    
    def get_metadata(self) -> RuleMetadata:
        """Get rule metadata"""
        return self._metadata
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate rule configuration"""
        return True
    
    def get_file_patterns(self) -> List[str]:
        """Get file patterns this rule should check"""
        return ["**/*.py"]  # Default to Python files
    
    def should_check_file(self, file_path: Path, repo_root: Path) -> bool:
        """Determine if a file should be checked by this rule, ignoring venv directory"""
        import fnmatch
        relative_path = str(file_path.relative_to(repo_root))
        # Ignore any file under venv directory
        if "venv" in file_path.parts:
            return False
        # Check against file patterns
        for pattern in self.get_file_patterns():
            if fnmatch.fnmatch(relative_path, pattern):
                return True
        return False
    
    def create_violation(
        self,
        file_path: Path,
        line_number: int,
        message: str,
        severity: Severity = Severity.ERROR,
        **kwargs
    ) -> Violation:
        """Helper method to create a violation"""
        return Violation(
            rule_name=self._metadata.name,
            rule_category=self._metadata.category,
            file_path=str(file_path),
            line_number=line_number,
            message=message,
            severity=severity,
            **kwargs
        )
    
    def read_file_safely(self, file_path: Path) -> Optional[str]:
        """Safely read a file with encoding detection"""
        try:
            # Try UTF-8 first
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            try:
                # Fall back to latin-1
                with open(file_path, 'r', encoding='latin-1') as f:
                    return f.read()
            except Exception:
                return None
        except Exception:
            return None
    
    def get_code_context(self, file_path: Path, line_number: int, context_lines: int = 3) -> Dict[str, Any]:
        """Get code context around a line"""
        content = self.read_file_safely(file_path)
        if not content:
            return {}
        
        lines = content.splitlines()
        start_line = max(0, line_number - context_lines - 1)
        end_line = min(len(lines), line_number + context_lines)
        
        return {
            'code_snippet': lines[line_number - 1] if line_number <= len(lines) else "",
            'context_lines_before': lines[start_line:line_number - 1],
            'context_lines_after': lines[line_number:end_line]
        }


class ConfigurableRule(BaseRule):
    """Base class for rules that support extensive configuration"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._apply_config()
    
    def _apply_config(self):
        """Apply configuration to rule parameters"""
        # Override in subclasses to apply specific configuration
        pass
    
    @abc.abstractmethod
    def get_config_schema(self) -> Dict[str, Any]:
        """Return JSON schema for rule configuration"""
        pass


class IncrementalRule(BaseRule):
    """Base class for rules that support incremental checking"""
    
    def supports_incremental(self) -> bool:
        """Check if this rule supports incremental checking"""
        return True
    
    def get_file_dependencies(self, file_path: Path) -> List[Path]:
        """Get files that this file depends on for checking"""
        return []  # Override in subclasses that have file dependencies


class SecurityRule(BaseRule):
    """Base class for security-related rules"""
    
    def _create_metadata(self) -> RuleMetadata:
        metadata = super()._create_metadata()
        metadata.category = "security"
        metadata.tags.add("security")
        return metadata
    
    def create_security_violation(
        self,
        file_path: Path,
        line_number: int,
        message: str,
        cve_reference: Optional[str] = None,
        **kwargs
    ) -> Violation:
        """Create a security-specific violation"""
        violation = self.create_violation(
            file_path, line_number, message, 
            severity=Severity.CRITICAL, **kwargs
        )
        violation.tags.add("security")
        if cve_reference:
            violation.references.append(f"CVE: {cve_reference}")
        return violation


class PerformanceRule(BaseRule):
    """Base class for performance-related rules"""
    
    def _create_metadata(self) -> RuleMetadata:
        metadata = super()._create_metadata()
        metadata.category = "performance"
        metadata.tags.add("performance")
        return metadata


# Rule registry for dynamic rule discovery
class RuleRegistry:
    """Registry for managing available rules"""
    
    def __init__(self):
        self._rules: Dict[str, type] = {}
    
    def register(self, rule_class: type):
        """Register a rule class"""
        if not issubclass(rule_class, BaseRule):
            raise ValueError(f"Rule {rule_class} must inherit from BaseRule")
        
        # Get rule name from metadata
        dummy_instance = rule_class()
        rule_name = dummy_instance.get_metadata().name
        self._rules[rule_name] = rule_class
    
    def get_rule(self, rule_name: str) -> Optional[type]:
        """Get a rule class by name"""
        return self._rules.get(rule_name)
    
    def list_rules(self) -> List[str]:
        """List all registered rule names"""
        return list(self._rules.keys())
    
    def create_instance(self, rule_name: str, config: Optional[Dict[str, Any]] = None) -> Optional[BaseRule]:
        """Create an instance of a rule"""
        rule_class = self.get_rule(rule_name)
        if rule_class:
            return rule_class(config)
        return None


# Global rule registry instance
rule_registry = RuleRegistry()
